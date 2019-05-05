import io
import pandas as pd
from lxml import html
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.db.models import Q
from rest_framework.status import HTTP_200_OK
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.decorators import APIView
from rest_framework import serializers
from api.tasks import create_transaction
from api.decorators import handle_error_json
from api.models import Wallet, WalletHistory, ExchangeRate
from api.serializers import ExchangeRateSerializer, WalletSerializer, ClientReportSerializer
from payment_system.pagination import ResultsSetPagination


class ClientView(mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    """
    retrieve:
    Возвращает данного пользователя.

    list:
    Возвращает список всех существующих пользователей.

    create:
    Регистрация клиента с указанием его имени, страны, города регистрации, валюты создаваемого кошелька.
    """
    serializer_class = WalletSerializer
    queryset = Wallet.objects.all()
    pagination_class = ResultsSetPagination


class ExchangeRateView(mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    serializer_class = ExchangeRateSerializer
    queryset = ExchangeRate.objects.all()
    pagination_class = ResultsSetPagination


class WalletRefillByNameView(APIView):
    """
    post:
    Пополнения баланса кошелька по wallet name
    """

    def _validate(self, data):
        """валидация входных данных"""
        if 'amount' not in data:
            raise serializers.ValidationError({'amount': ["This field is required."]})
        elif not data['amount'].isdigit():
            raise serializers.ValidationError({'amount': ["Must be float."]})

    @method_decorator(handle_error_json())
    def post(self, request, *args, **kwargs):
        self._validate(request.POST)
        try:
            wallet = Wallet.objects.get(name=kwargs.get('name'))
            # Создаем транзакция пополнения кошелька.
            transaction_data = dict(wallet_to_id=wallet.pk,
                                    currency_id=wallet.currency.pk,
                                    amount=request.POST.get('amount'),
                                    operation='REFILL')
            create_transaction.delay(transaction_data)
        except Wallet.DoesNotExist:
            raise serializers.ValidationError({'non_field_errors': ["Wallet not exists"]})

        return Response(data=dict(result="success", message="Transaction REFILL created"), status=HTTP_200_OK)


class WalletToWalletByNameView(APIView):
    """
    post:
    Денежный перевод от клиента > клиенту по имени.
    """

    def _validate(self, data):
        """валидация входных данных"""
        if 'amount' not in data:
            raise serializers.ValidationError({'amount': ["This field is required."]})
        elif not data['amount'].isdigit():
            raise serializers.ValidationError({'amount': ["Must be float."]})

        # Тут мы ожидаем, что 'from_name' и 'to_name' в любом случае есть. Проверка была на уровне роутинга.
        if data['from_name'] == data['to_name']:
            # Нельзя переводить самому себе.
            raise serializers.ValidationError({'non_field_errors': ["Can't translate to yourself"]})

        # currency_use - обязательное поле. может быть "FROM", "TO"
        if not data.get('currency_use') in ["FROM", "TO"]:
            raise serializers.ValidationError({'currency_use': ["Set currency_use 'FROM' or 'TO'"]})

    @method_decorator(handle_error_json())
    def post(self, request, *args, **kwargs):
        data = kwargs.copy()
        data['currency_use'] = request.POST.get('currency_use')
        data['amount'] = request.POST.get('amount')
        self._validate(data)

        try:
            wallet_from = Wallet.objects.get(name=data['from_name'])
        except Wallet.DoesNotExist:
            raise serializers.ValidationError({'from_name': ["Wallet not exists"]})

        try:
            wallet_to = Wallet.objects.get(name=data['to_name'])
        except Wallet.DoesNotExist:
            raise serializers.ValidationError({'non_field_errors': ["Wallet not exists"]})

        # Создаем транзакцию перевода от клиента > клиенту
        transaction_data = dict(
            operation='TRANSFER',
            wallet_from_id=wallet_from.pk,
            wallet_to_id=wallet_to.pk,
            currency_id=wallet_from.currency.pk if data['currency_use'] == 'FROM' else wallet_to.currency.pk,
            amount=data['amount'])
        create_transaction.delay(transaction_data)

        return Response(data=dict(result="success", message="Transaction TRANSFER created"), status=HTTP_200_OK)


class ClientReportView(APIView):
    def get(self, request):
        data = request.GET.copy()
        serializer = ClientReportSerializer(data=data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)

        try:
            wallet = Wallet.objects.get(name=serializer.validated_data['name'])
        except Wallet.DoesNotExist:
            raise serializers.ValidationError({'non_field_errors': ["Wallet not exists"]})

        args = Q()
        args &= Q(wallet=wallet)
        if 'start_date' in serializer.validated_data:
            args &= Q(oper_date__gte=serializer.validated_data['start_date'])
        if 'end_date' in serializer.validated_data:
            args &= Q(oper_date__lte=serializer.validated_data['end_date'])

        values = [
            'oper',
            'type',
            'wallet_partner',
            'wallet_partner_name',
            'oper_date',
            'amount',
            'oper__usd_amount',
        ]
        values_trans = [
            'ID операции',
            'Тип',
            'ID клиента',
            'Имя клиента',
            'Время',
            'Cумма в валюте',
            'Сумма в USD'
        ]
        wallet_history = WalletHistory.objects.filter(args).prefetch_related('oper').values_list(*values)
        if not wallet_history.exists():
            raise serializers.ValidationError({'non_field_errors': ["There are no transactions for this wallet."]})

        df = pd.DataFrame(list(wallet_history))
        df.columns = values_trans

        # Задаем формат отображения даты.
        df['Время'] = pd.to_datetime(df['Время']).dt.strftime('%Y-%m-%d %H:%M:%S')

        # Причесываем Nan/None, корректируем вывод.
        df['ID клиента'] = df['ID клиента'].astype(pd.np.str).replace('nan', 'Пополнение баланса')
        df['Имя клиента'] = df['Имя клиента'].astype(pd.np.str).replace('None', '')
        html_string = df.to_html(index=False)

        # Собираем файл отчета, если требуется.
        file_type = data.get('export_file_type')
        if file_type == 'xml':
            output = io.BytesIO()
            root = html.fromstring(html_string)
            tree = root.getroottree()
            tree.write(output, encoding='unicode')
            response = HttpResponse(output.getvalue(), content_type='text/xml')
            response['Content-Disposition'] = 'attachment; filename="Report for {}.xml"'.format(wallet.name)
            return response
        elif file_type == 'csv':
            output = io.StringIO()
            df.to_csv(output, index=False, compression='gzip')
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="Report for {}.csv"'.format(wallet.name)
            return response

        # Добавляем ссылки для скачивания CSV и XML
        fixed_html = """
        <html>
        <body>
             <ul>
                 <li><a href="{path}?{params}&export_file_type=csv">Download CSV report</a></li>
                 <li><a href="{path}?{params}&export_file_type=xml">Download XML report</a></li>
            </ul>
            {body}
        <body>
        """.format(path=request.META.get('PATH_INFO'),
                   body=html_string,
                   params="&".join(["{}={}".format(k, v) for k, v in data.items()]))

        return HttpResponse(fixed_html, content_type='text/html; charset=utf-8', status=HTTP_200_OK)

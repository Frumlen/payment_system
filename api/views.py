import csv
from django.utils.encoding import smart_str
from django.core import serializers as core_serializers
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
from api.serializers import ExchangeRateSerializer, WalletSerializer, ClientReportSerializer, \
    WalletRefillByNameSerializer, WalletToWalletByNameSerializer
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

    @method_decorator(handle_error_json())
    def post(self, request, *args, **kwargs):
        data = kwargs.copy()
        data['amount'] = request.POST.get('amount')

        serializer = WalletRefillByNameSerializer(data=data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)

        wallet = serializer.validated_data['name']
        # Создаем транзакция пополнения кошелька.
        transaction_data = dict(wallet_to_id=wallet.pk,
                                currency_id=wallet.currency.pk,
                                amount=request.POST.get('amount'),
                                operation='REFILL')
        create_transaction.delay(transaction_data)
        return Response(data=dict(result="success", message="Transaction REFILL created"), status=HTTP_200_OK)


class WalletToWalletByNameView(APIView):
    """
    post:
    Денежный перевод от клиента > клиенту по имени.
    """

    @method_decorator(handle_error_json())
    def post(self, request, *args, **kwargs):
        data = kwargs.copy()
        data['currency_use'] = request.POST.get('currency_use')
        data['amount'] = request.POST.get('amount')
        serializer = WalletToWalletByNameSerializer(data=data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)

        # Создаем транзакцию перевода от клиента > клиенту
        wallet_from= serializer.validated_data['wallet_from']
        wallet_to = serializer.validated_data['wallet_to']
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

        wallet = serializer.validated_data['name']
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
        wallet_history = WalletHistory.objects.filter(args).prefetch_related('oper')
        queryset = wallet_history.values(*values)
        if not queryset.exists():
            raise serializers.ValidationError({'non_field_errors': ["There are no transactions for this wallet."]})

        # Конструктор TD элементов для HTML версии страницы.
        html_tr = ""
        for obj in queryset.iterator():
            tr = "<tr>\n"
            for val in values:
                tr += "<td>{%s}</td>\n" % val
            tr += '</tr>\n'
            html_tr += tr.format(**obj)

        # Конструктор TR элемента
        html_header = '<tr style="text-align: right;">\n'
        for val in values_trans:
            html_header += '<th>{}</th>\n'.format(val)
        html_header += '</tr>\n'

        # Собираем основном HTML
        html = """
               <html>
               <body>
                    <ul>
                        <li><a href="{path}?{params}&export_file_type=csv">Download CSV report</a></li>
                        <li><a href="{path}?{params}&export_file_type=xml">Download XML report</a></li>
                   </ul>
                   <table border="1" class="dataframe">
                        <thead>{html_header}</thead>
                        <tbody>{html_tr}</tbody>
                    </table>
               <body>
               </html>
               """.format(path=request.META.get('PATH_INFO'),
                          html_header=html_header,
                          html_tr=html_tr,
                          params="&".join(["{}={}".format(k, v) for k, v in data.items()]))

        # Собираем файл отчета, если требуется.
        file_type = data.get('export_file_type')
        if file_type == 'xml':
            XMLSerializer = core_serializers.get_serializer("xml")
            xml_serializer = XMLSerializer()
            xml_serializer.serialize(wallet_history)
            response = HttpResponse(xml_serializer.getvalue(), content_type='text/xml')
            response['Content-Disposition'] = 'attachment; filename="Report for {}.xml"'.format(wallet.name)
            return response
        elif file_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=Report for {}.csv"'.format(wallet.name)
            writer = csv.writer(response, csv.excel)
            response.write(u'\ufeff'.encode('utf8'))  # BOM (optional...Excel needs it to open UTF-8 file properly)
            writer.writerow([smart_str(val) for val in values_trans])
            for obj in queryset:
                writer.writerow([smart_str(obj[smart_str(val)]) for val in values])
            return response
        return HttpResponse(html, content_type='text/html; charset=utf-8', status=HTTP_200_OK)

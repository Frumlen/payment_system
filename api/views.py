import csv
from django.utils.encoding import smart_str
from django.core.serializers.xml_serializer import Serializer as XMLSerializer
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.db.models import Q
from rest_framework.status import HTTP_200_OK
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.decorators import APIView
from rest_framework import serializers
from .tasks import create_transaction
from .decorators import handle_error_json
from .models import Wallet, WalletHistory, ExchangeRate
from .serializers import ExchangeRateSerializer, WalletSerializer, ClientReportSerializer, \
    WalletRefillByNameSerializer, WalletToWalletByNameSerializer, WalletHistorySerializer
from payment_system.pagination import ResultsSetPagination


class ClientView(mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    """
    retrieve:
    Returns the current user.

    list:
    Returns a list of all existing users.

    create:
    Registration of the client with his name, country, city of registration, currency of the wallet being created.
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
    Top up wallet balance by wallet name
    """

    @method_decorator(handle_error_json())
    def post(self, request, *args, **kwargs):
        data = kwargs.copy()
        data['amount'] = request.POST.get('amount')

        serializer = WalletRefillByNameSerializer(data=data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)

        wallet = serializer.validated_data['name']
        # Create a purse replenishment transaction.
        transaction_data = dict(wallet_to_id=wallet.pk,
                                currency_id=wallet.currency.pk,
                                amount=request.POST.get('amount'),
                                operation='REFILL')
        #TODO: Mb remove Celery + rabbitmq? Need Ddos test.
        create_transaction.delay(transaction_data)
        return Response(data=dict(result="success", message="Transaction REFILL created"), status=HTTP_200_OK)


class WalletToWalletByNameView(APIView):
    """
    Money transfer from client> client by name.
    """

    @method_decorator(handle_error_json())
    def post(self, request, *args, **kwargs):
        data = kwargs.copy()
        data['currency_use'] = request.POST.get('currency_use')
        data['amount'] = request.POST.get('amount')
        serializer = WalletToWalletByNameSerializer(data=data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)

        # Create a transfer transaction from client> client
        wallet_from = serializer.validated_data['wallet_from']
        wallet_to = serializer.validated_data['wallet_to']
        transaction_data = dict(
            operation='TRANSFER',
            wallet_from_id=wallet_from.pk,
            wallet_to_id=wallet_to.pk,
            currency_id=wallet_from.currency.pk if data['currency_use'] == 'FROM' else wallet_to.currency.pk,
            amount=data['amount'])
        #TODO: Mb remove Celery + rabbitmq? Need Ddos test.
        create_transaction.delay(transaction_data)
        return Response(data=dict(result="success", message="Transaction TRANSFER created"), status=HTTP_200_OK)


class ClientReportView(APIView):

    @method_decorator(handle_error_json())
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

        wallet_history = WalletHistory.objects.filter(args).prefetch_related('oper', 'oper__currency')
        if not wallet_history.exists():
            raise serializers.ValidationError({'non_field_errors': ["There are no transactions for this wallet."]})

        # Report file generation.
        export_file_type = data.get('export_file_type')
        if export_file_type == 'xml':
            xml_serializer = XMLSerializer()
            xml_serializer.serialize(wallet_history)
            response = HttpResponse(xml_serializer.getvalue(), content_type='text/xml', status=HTTP_200_OK)
            response['Content-Disposition'] = 'attachment; filename="Report for {}.xml"'.format(wallet.name)
            return response
        elif export_file_type == 'csv':
            response = HttpResponse(content_type='text/csv', status=HTTP_200_OK)
            response['Content-Disposition'] = 'attachment; filename="Report for {}.csv"'.format(wallet.name)
            values = [
                'oper',
                'type',
                'wallet_partner',
                'wallet_partner_name',
                'oper_date',
                'amount',
                'oper__currency__currency',
                'oper__usd_amount',
            ]
            values_trans = [
                'Operation ID',
                'Type of',
                'Customer ID',
                'Customer Name',
                'Time',
                'Amount of operation',
                'Transaction Currency',
                'USD amount'
            ]
            writer = csv.writer(response, csv.excel)
            response.write(u'\ufeff'.encode('utf8'))  # BOM (optional...Excel needs it to open UTF-8 file properly)
            writer.writerow([smart_str(val) for val in values_trans])
            queryset = wallet_history.values(*values)
            for obj in queryset.iterator():
                writer.writerow([smart_str(obj[smart_str(val)]) for val in values])
            return response

        return Response(WalletHistorySerializer(wallet_history, many=True).data, status=HTTP_200_OK)

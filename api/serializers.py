from django.conf import settings
from rest_framework import serializers
from api.models import Wallet, ExchangeRate, Currency, WalletHistory


class WalletSerializer(serializers.ModelSerializer):
    """Serializer to create, display wallet"""
    balance = serializers.IntegerField(read_only=True)
    created = serializers.DateTimeField(read_only=True, format=settings.DATE_OUTPUT_FORMAT)
    currency = serializers.CharField()

    def validate_currency(self, data):
        if not data:
            raise serializers.ValidationError("This field is required.")

        if data.isdigit():
            try:
                return Currency.objects.get(pk=data)
            except Currency.DoesNotExist:
                raise serializers.ValidationError("No currency with such Pk.")
        try:
            return Currency.objects.get(currency=data)
        except Currency.DoesNotExist:
            raise serializers.ValidationError("No currency with such ISO code.")

    class Meta:
        model = Wallet
        fields = ('id', 'name', 'city', 'country', 'created', 'currency', 'balance')


class ExchangeRateSerializer(serializers.ModelSerializer):
    """Serializer for creating, displaying currency quotes"""
    currency_name = serializers.CharField(source='currency.currency_name', read_only=True)
    currency = serializers.CharField()
    rate = serializers.FloatField()
    created = serializers.DateTimeField(input_formats=settings.DATE_INPUT_FORMATS, format=settings.DATE_OUTPUT_FORMAT)

    def validate_currency(self, data):
        if not data:
            raise serializers.ValidationError("This field is required.")

        if data.isdigit():
            try:
                return Currency.objects.get(pk=data)
            except Currency.DoesNotExist:
                raise serializers.ValidationError("No currency with such Pk.")
        try:
            return Currency.objects.get(currency=data)
        except Currency.DoesNotExist:
            raise serializers.ValidationError("No currency with such ISO code.")

    class Meta:
        model = ExchangeRate
        fields = ('id', 'currency_id', 'currency', 'currency_name', 'rate', 'created')


class ClientReportSerializer(serializers.Serializer):
    """Serializer to create report"""
    name = serializers.CharField(required=True)
    start_date = serializers.DateTimeField(input_formats=settings.DATE_INPUT_FORMATS, required=False)
    end_date = serializers.DateTimeField(input_formats=settings.DATE_INPUT_FORMATS, required=False)

    def validate_name(self, data):
        if not data:
            raise serializers.ValidationError("This field is required.")

        try:
            return Wallet.objects.get(name=data)
        except Wallet.DoesNotExist:
            raise serializers.ValidationError("Wallet not exists.")


class WalletRefillByNameSerializer(serializers.Serializer):
    """Serializer to replenish the wallet"""
    amount = serializers.FloatField(required=True)
    name = serializers.CharField(required=True)

    def validate_name(self, data):
        if not data:
            raise serializers.ValidationError("This field is required.")

        try:
            return Wallet.objects.get(name=data)
        except Wallet.DoesNotExist:
            raise serializers.ValidationError("Wallet not exists.")


class WalletToWalletByNameSerializer(serializers.Serializer):
    """Serializer to replenish the wallet"""
    amount = serializers.FloatField(required=True)
    from_name = serializers.CharField(required=True)
    to_name = serializers.CharField(required=True)
    currency_use = serializers.ChoiceField(required=True, choices=['FROM', 'TO'])

    def validate(self, data):
        if data['from_name'] == data['to_name']:
            raise serializers.ValidationError("Can't translate to yourself")

        try:
            data['wallet_from'] = Wallet.objects.get(name=data['from_name'])
        except Wallet.DoesNotExist:
            raise serializers.ValidationError("Wallet not exists")

        try:
            data['wallet_to'] = Wallet.objects.get(name=data['to_name'])
        except Wallet.DoesNotExist:
            raise serializers.ValidationError("Wallet not exists")

        return data


class WalletHistorySerializer(serializers.ModelSerializer):
    """Serializer for displaying operation history, for report"""
    usd_amount = serializers.FloatField(source='oper.usd_amount')
    oper_date = serializers.DateTimeField(format=settings.DATE_OUTPUT_FORMAT)
    oper_currency = serializers.CharField(source='oper.currency')

    class Meta:
        model = WalletHistory
        fields = ('id', 'oper', 'wallet_partner', 'wallet_partner_name', 'oper_date', 'amount', 'oper_currency',
                  'usd_amount')

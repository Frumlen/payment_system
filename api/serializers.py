from django.conf import settings
from rest_framework import serializers
from api.models import Wallet, ExchangeRate, Currency


class WalletSerializer(serializers.ModelSerializer):
    """Сериализатор для создания, отображения кошелька"""
    balance = serializers.IntegerField(read_only=True)
    created = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
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
    """Сериализатор для создания, отображения котировок валют"""
    currency_name = serializers.CharField(source='currency.currency_name', read_only=True)
    currency = serializers.CharField()
    rate = serializers.FloatField()
    created = serializers.DateTimeField(input_formats=settings.DATE_INPUT_FORMATS, format='%Y-%m-%d %H:%M:%S')

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
    name = serializers.CharField(required=True)
    start_date = serializers.DateTimeField(input_formats=settings.DATE_INPUT_FORMATS, required=False)
    end_date = serializers.DateTimeField(input_formats=settings.DATE_INPUT_FORMATS, required=False)

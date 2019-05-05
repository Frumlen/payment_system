from __future__ import unicode_literals
from django.utils.crypto import random
import factory
from api.models import Wallet, Currency, ExchangeRate, WalletHistory, Transaction, Operation


class CurrencyFactory(factory.DjangoModelFactory):
    class Meta:
        model = Currency

    currency_name = 'USD'
    currency = 'USD'
    fractional = 100


class WalletFactory(factory.DjangoModelFactory):
    class Meta:
        model = Wallet

    name = 'Тестовый объект'
    city = 'Страна'
    country = 'Город проживания'
    # currency = CurrencyFactory.create()

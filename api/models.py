import datetime
from django.db import models


class Currency(models.Model):
    currency_name = models.CharField(max_length=60, verbose_name='Название валюты')
    currency = models.CharField(max_length=10, db_index=True, verbose_name='ISO')  # FIXME: add ISO4217 validator
    fractional = models.SmallIntegerField(verbose_name='Дробная часть')

    class Meta:
        ordering = ('pk',)
        verbose_name = 'Валюта'
        verbose_name_plural = 'Валюты'

    def __str__(self):
        return self.currency


class Wallet(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True, verbose_name='Имя клиента')
    city = models.CharField(max_length=60, verbose_name='Страна')
    country = models.CharField(max_length=180, verbose_name='Город проживания')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')
    balance = models.BigIntegerField(default=0, verbose_name='Баланс')
    currency = models.ForeignKey('api.Currency', on_delete=models.DO_NOTHING, verbose_name='Валюта кошелька')

    class Meta:
        ordering = ('pk',)
        verbose_name = 'Кошелек'
        verbose_name_plural = 'Кошельки'

    def __str__(self):
        return self.name


class ExchangeRate(models.Model):
    currency = models.ForeignKey('api.Currency', db_index=True, on_delete=models.DO_NOTHING, verbose_name='Валюта')
    rate = models.FloatField(verbose_name='Курс валюты к USD')
    created = models.DateTimeField(verbose_name='Дата добавления')

    class Meta:
        ordering = ('pk',)
        verbose_name = 'Курс валюты'
        verbose_name_plural = 'Курсы валют'
        unique_together = ("currency", "created")

    def __str__(self):
        return '{} {}'.format(self.currency, self.rate)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.created:
            self.created = datetime.datetime.now()
            self.save()
        super().save(force_insert, force_update, using, update_fields)


class Operation(models.Model):
    currency = models.ForeignKey('api.Currency', on_delete=models.DO_NOTHING,
                                 verbose_name='Идентификатор валюты операции')
    operation = models.CharField(max_length=20,
                                 verbose_name='Название операции')  # REFILL– replenishment, TRANSFER - transfer
    oper_amount = models.BigIntegerField(verbose_name='Cумма операции в валюте операции')
    usd_amount = models.BigIntegerField(verbose_name='Cумма операции в USD')
    created = models.DateTimeField(verbose_name='Дата операции')

    class Meta:
        ordering = ('pk',)
        verbose_name = 'Операция'
        verbose_name_plural = 'Операции'


class WalletHistory(models.Model):
    wallet = models.ForeignKey('api.Wallet', on_delete=models.DO_NOTHING, related_name='histories',
                               verbose_name='Кошелек')
    wallet_partner = models.ForeignKey('api.Wallet', null=True, on_delete=models.DO_NOTHING,
                                       related_name='partner_histories',
                                       verbose_name='Кошелек, с которым проводилась операция')
    wallet_partner_name = models.CharField(max_length=255, null=True,
                                           verbose_name='Имя клиента, с которым проводилась операция')
    oper = models.ForeignKey('api.Operation', on_delete=models.DO_NOTHING, verbose_name='Операция')
    oper_date = models.DateTimeField(db_index=True, verbose_name='Дата операции')
    type = models.CharField(max_length=3, verbose_name='Тип операции (списание, пополнение)')  # IN / OUT
    amount = models.BigIntegerField(verbose_name='Cумма операции в валюте кошелька')

    class Meta:
        ordering = ('pk',)
        verbose_name = 'История операции по кошельку'
        verbose_name_plural = 'История операций по кошелькам'


class Transaction(models.Model):
    wallet_from = models.ForeignKey('api.Wallet', null=True, db_index=True, related_name='in_transactions',
                                    on_delete=models.DO_NOTHING,
                                    verbose_name='Кошелек, с которого снимают деньги')
    wallet_to = models.ForeignKey('api.Wallet', on_delete=models.DO_NOTHING, related_name='out_transactions',
                                  verbose_name='Кошелек, на который поступают деньги')
    operation = models.CharField(max_length=20,
                                 verbose_name='Название операции')  # REFILL– replenishment, TRANSFER - transfer
    currency = models.ForeignKey('api.Currency', on_delete=models.DO_NOTHING, verbose_name='Валюта транзакции')
    status = models.CharField(max_length=6, db_index=True, verbose_name='Статус транзакции')
    amount = models.FloatField(verbose_name='Сумма операции')
    created = models.DateTimeField(auto_now_add=True, editable=False, verbose_name='Дата транзакции')

    class Meta:
        ordering = ('pk',)
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'

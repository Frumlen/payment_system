import math
import logging
from celery import shared_task
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from api.models import Transaction, ExchangeRate, Operation, WalletHistory


@shared_task
def create_transaction(data):
    with transaction.atomic():
        tran = Transaction.objects.create(**data)
        # Получаем последний курс на момент совершения транзакции
        rate = ExchangeRate.objects.filter(currency=tran.currency, created__lte=tran.created).order_by('-created')\
            .first()
        if not rate:
            raise ObjectDoesNotExist('Exchange rate not exists')

    return True


def get_wallet_amount(tran, wallet, usd, tran_amount):
    if tran.currency == wallet.currency:
        return tran_amount
    rate = ExchangeRate.objects.filter(currency=wallet.currency, created__lte=tran.created).order_by(
        '-created').first()
    if rate:
        return math.floor(usd * rate.rate * wallet.currency.fractional)


def create_operation(tran, usd, tran_amount):
    operation = Operation.objects.create(
        currency=tran.currency,
        operation=tran.operation,
        created=tran.created,
        oper_amount=tran_amount,
        usd_amount=usd)
    return operation


def create_wallet_hist(tran, wallet, wallet_partner, oper, amount):
    wallet_history = WalletHistory.objects.create(
        wallet=wallet,
        oper=oper,
        oper_date=tran.created,
        type='IN' if amount > 0 else 'OUT',
        amount=abs(amount)
    )
    if wallet_partner:
        wallet_history.wallet_partner = wallet_partner
        wallet_history.wallet_partner_name = wallet_partner.name
        wallet_history.save()


def inc_wallet_balance(wallet, amount):
    # Если денег на счету недостаточно, вызываем исключение, чтобы не создавать данных в базе.
    if wallet.balance + amount < 0:
        raise Exception('Wrong amount')

    wallet.balance += amount
    wallet.save()


@shared_task
def processing_transactions():
    """Метод процессинга транзакций. В нем происходит вся логика перевода денег, сохранения истории"""
    transacitons = Transaction.objects.exclude(status__in=['start', 'done']).order_by('created')
    counter = 0

    for tran in transacitons.iterator():
        try:
            with transaction.atomic():
                rate = ExchangeRate.objects.filter(currency=tran.currency, created__lte=tran.created)\
                    .order_by('-created').first()
                if not rate:
                    continue
    
                usd = math.floor(100 * tran.amount / rate.rate)
                tran_amount = math.floor(tran.amount * tran.currency.fractional)
                oper = create_operation(tran, usd, tran_amount)
    
                wallet_to = tran.wallet_to
                wallet_from = None
    
                if tran.operation == 'TRANSFER':
                    wallet_from = tran.wallet_from
                    wallet_from_amount = -1 * get_wallet_amount(tran, wallet_from, usd, tran_amount)
                    create_wallet_hist(tran, wallet_from, wallet_to, oper, wallet_from_amount)
                    inc_wallet_balance(wallet_from, wallet_from_amount)
    
                wallet_to_amount = get_wallet_amount(tran, wallet_to, usd, tran_amount)
                create_wallet_hist(tran, wallet_to, wallet_from, oper, wallet_to_amount)
                inc_wallet_balance(wallet_to, wallet_to_amount)
    
                tran.status = 'done'
                tran.save()
                counter += 1
        except Exception as err:
            logging.warning(err)
    return '{} transactions processed'.format(counter)

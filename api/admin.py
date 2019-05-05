from django.contrib import admin
from api.models import Wallet, Currency, Transaction, WalletHistory, ExchangeRate, Operation

admin.site.register(Wallet)
admin.site.register(Currency)
admin.site.register(Transaction)
admin.site.register(WalletHistory)
admin.site.register(ExchangeRate)
admin.site.register(Operation)

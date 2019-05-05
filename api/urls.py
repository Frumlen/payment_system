from django.conf.urls import url
from rest_framework.routers import SimpleRouter
from .views import ClientView, ExchangeRateView, WalletRefillByNameView, WalletToWalletByNameView, ClientReportView

router = SimpleRouter(trailing_slash=False)
router.register('client', ClientView, base_name='client')
router.register('exchange_rate', ExchangeRateView, base_name='exchange_rate')

urlpatterns = router.urls + [
    url(r'^client_report$', ClientReportView.as_view(), name='client_report'),
    url(r'^wallet_refill_by_name/(?P<name>[A-z0-9-_]+)$', WalletRefillByNameView.as_view(),
        name='wallet_refill_by_name'),
    url(r'^wallet2wallet_by_name/(?P<from_name>[A-z0-9-_]+)/(?P<to_name>[A-z0-9-_]+)$',
        WalletToWalletByNameView.as_view(), name='wallet2wallet_by_name')
]

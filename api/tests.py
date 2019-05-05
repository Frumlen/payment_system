from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from api.models import Wallet
from api.factories import WalletFactory, CurrencyFactory


class TestCreateWalletView(APITestCase):
    url = reverse('client-list')
    base_url = 'client'

    def setUp(self):
        super().setUp()
        self.wallet = WalletFactory.create()
        self.basename = 'client'


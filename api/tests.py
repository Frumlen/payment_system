from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Wallet, WalletHistory


class TestApiView(APITestCase):
    fixtures = ['test.json']

    def test_create_wallet(self):
        url = '/api/client'

        # test main client(wallet) api url
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # create user via api without parameters
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # create wallet through api
        params = {
            "name": "Name",
            "city": "City",
            "country": "Country",
            "currency": "USD",
        }
        response = self.client.post(url, data=params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_balance(self):
        wallet = Wallet.objects.all().first()
        if wallet:
            url = '/api/wallet_refill_by_name/{}'.format(wallet.name)

            # update ballance via api without parameters
            response = self.client.post(url, data={})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            # if not running, celery can give out 500
            response = self.client.post(url, data={'amount': 100})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_wallet2wallet(self):
        # Get 2 purses with a balance of bolans more than 1 unit for the test.
        wallets = Wallet.objects.filter(balance__gte=1).order_by('balance')
        if wallets.count() > 2:
            url = "/api/wallet2wallet_by_name/{}/{}".format(wallets[0].name, wallets[1].name)
            response = self.client.post(url, data={'amount': 1, 'currency_use': 'FROM'})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Making a request for translation with the wrong parameters
            response = self.client.post(url, data={'amount': 1, 'currency_use': 'BAD PARAM'})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_exchange_rate(self):
        url = '/api/exchange_rate'

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Create currency quotes
        params = {
            "currency": "USD",
            "created": "2019-05-04 10:17:33",
            "rate": 10.1
        }
        response = self.client.post(url, data=params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # create exchange_rate via api without parameters
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_client_report(self):
        url = '/api/client_report'

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        wallet_history = WalletHistory.objects.all().first()
        if wallet_history:
            url = '{}?name={}'.format(url, wallet_history.wallet.name)

            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response = self.client.get(url + '&export_file_type=xml')
            xml_filename = 'attachment; filename="Report for {}.xml"'.format(wallet_history.wallet.name)
            self.assertEqual(response['content-disposition'], xml_filename)

            response = self.client.get(url + '&export_file_type=csv')
            csv_filename = 'attachment; filename="Report for {}.csv"'.format(wallet_history.wallet.name)
            self.assertEqual(response['content-disposition'], csv_filename)

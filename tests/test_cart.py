from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from .test_customer_register import CustomerRegisterTest

class CartTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        customer_registration_test = CustomerRegisterTest()
        customer_registration_test.client = self.client
        customer_registration_test.test_customer_registration()

        data = {
            'username': 'tony',
            'password': 'password123',
        }
        url = reverse('token_obtain_pair')
        response = self.client.post(url, data)
        self.token = response.data['access']

    def test_get_cart(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        url = reverse('cart-list')
        response = self.client.get(url, headers=headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

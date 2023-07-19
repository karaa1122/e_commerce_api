from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from .test_customer_register import CustomerRegisterTest

class CardTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer_register_test = CustomerRegisterTest()

    def perform_authentication(self):
        
        self.customer_register_test.client = self.client
        self.customer_register_test.test_customer_registration()


        data = {
            'username': 'tony',
            'password': 'password123',
        }
        url = reverse('token_obtain_pair')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.data['access']
        return access_token

    def test_get_cards(self):
        access_token = self.perform_authentication()
        headers = {'Authorization': f'Bearer {access_token}'}

        url = reverse('cards-list')
        response = self.client.get(url, headers=headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

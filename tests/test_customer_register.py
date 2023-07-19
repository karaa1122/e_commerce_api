from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse

class CustomerRegisterTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_customer_registration(self):
        data = {
            'first_name': 'tony',
            'last_name': 'soprano',
            'email': 'soprano@example.com',
            'username': 'tony',
            'password': 'password123',
        }
        url = reverse('customer-signup')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Account is created')

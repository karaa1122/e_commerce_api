from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from .test_staff_register import StaffRegisterTest


class ItemTest(TestCase):
    fixtures = ['categories']
    def setUp(self):
        self.client = APIClient()

        staff_registration_test = StaffRegisterTest()
        staff_registration_test.client = self.client
        staff_registration_test.test_staff_registration()
        
        data = {
            'username': 'white',
            'password': 'password123',
        }
        url = reverse('token_obtain_pair')
        response = self.client.post(url, data)
        self.token = response.data['access']

    def test_get_items(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        url = reverse('product_item-list')  
        response = self.client.get(url, headers=headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_item(self):
        data = {
            'item_name': 'Smartphone',
            'price': 999.99,
            'Category': 1,
            'stock': 10,
            'description': 'Good condition.',
        }
        headers = {'Authorization': f'Bearer {self.token}'}
        url = reverse('product_item-list')
        response = self.client.post(url, data, headers=headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

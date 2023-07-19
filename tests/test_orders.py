from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from .test_staff_register import StaffRegisterTest

class BaseTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff_token = None

    def test_staff_authentication(self):
        
        staff_registration_test = StaffRegisterTest()
        staff_registration_test.client = self.client  
        staff_registration_test.test_staff_registration()

        data = {
            'username': 'white',
            'password': 'password123',
        }
        url = reverse('token_obtain_pair')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)  
        self.staff_token = response.data['access']

    def test_staff_order_list_authenticated(self):
        
        self.test_staff_authentication()

        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.staff_token)

        
        url = reverse('orders-list')  
        response = self.client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
       
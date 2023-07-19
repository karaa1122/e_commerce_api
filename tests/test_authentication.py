from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from .test_staff_register import StaffRegisterTest
from .test_customer_register import CustomerRegisterTest

class BaseTest(TestCase):
    def setUp(self):
        self.client = APIClient()

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
        self.assertIsNotNone(response.data['access'])  

    def test_customer_authentication(self):
        # Register customer user
        customer_registration_test = CustomerRegisterTest()
        customer_registration_test.client = self.client  
        customer_registration_test.test_customer_registration()

        
        data = {
            'username': 'tony',
            'password': 'password123',
        }
        url = reverse('token_obtain_pair')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)  
        self.assertIsNotNone(response.data['access'])  

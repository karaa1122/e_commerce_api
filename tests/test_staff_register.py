from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse

class StaffRegisterTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_staff_registration(self):
        data = {
            'first_name': 'walter',
            'last_name': 'white',
            'username': 'white',
            'email': 'white@example.com',
            'password': 'password123',
        }
        url = reverse('staff-signup')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Account is created')

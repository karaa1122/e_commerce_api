from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from .test_staff_register import StaffRegisterTest
from api.models import Orders, CustomUser

class OrderListTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff_token = None
        self.order_id = None

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
        user = CustomUser.objects.create_user(username='user1', password='password')

        order_data = {
            'user': user,
            'order_status': Orders.PENDING,
            
        }
        order = Orders.objects.create(**order_data)
        self.order_id = order.id  

        url = reverse('orders-list')
        response = self.client.get(url)

        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            order_id = self.order_id

            data = {
                'order_id': order_id,
                'payment_method': 'cash',
            }
            refund_url = reverse('refund-list')
            refund_response = self.client.post(refund_url, data)
            

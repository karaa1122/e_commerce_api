from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch
from api.auth import User
from api.models import Category, Item, OrderItem, Orders

class CheckoutTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('checkout-list')

    def test_create_checkout(self):
        
        user = User.objects.create(username='testuser')
        category = Category.objects.create(name='Electronics')
        item = Item.objects.create(item_name='xbox', stock=10, Category=category)
        order = Orders.objects.create(user=user, order_status=Orders.PENDING)
        order_item = OrderItem.objects.create(order=order, item=item, quantity=5)

        
        with patch('api.views.send_mail') as mock_send_mail:
            
            data = {
                'order_id': order.id,
                'payment_method': 'cash',
            }

            
            self.client.force_authenticate(user=user)
            response = self.client.post(self.url, data)

            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['detail'], 'Checkout successful')

            
            order.refresh_from_db()
            self.assertEqual(order.order_status, 'ordered')

            
            item.refresh_from_db()
            self.assertEqual(item.stock, 5)

            
            mock_send_mail.assert_called_once_with(
                subject='Order Confirmation',
                message='Your order has been confirmed and processed successfully.',
                from_email='admin@admin.com',
                recipient_list=[user.email],
                fail_silently=True
            )

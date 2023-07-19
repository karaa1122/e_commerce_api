from django.urls import path
from rest_framework import routers

from api.views import *
from .views import CustomerRegisterView, CustomerCategoryViewSet

router = routers.DefaultRouter()
router.register(r'category_product', CategoryViewSet, basename='category_product')
router.register(r'product_item', ItemViewSet, basename='product_item')
router.register(r'orders', StaffOrderViewset, basename='orders')
router.register(r'cart-items', CartItemViewSet, basename='cart')
router.register(r'checkout', CheckoutViewSet, basename='checkout')
router.register(r'refund', RefundViewSet, basename='refund')
router.register(r'user-orders', CustomerOrdersViewSet, basename='user-orders')
router.register(r'cards', CardViewSet, basename='cards')
router.register(r'transactions', TransactionViewSet, basename='transactions')
router.register(prefix='product_item_customers', viewset=CustomerItemsViewSet, basename='customer-items')
router.register(prefix='category_product_customers', viewset=CustomerCategoryViewSet, basename='customer-category')

urlpatterns = [
  path('staff-signup/', StaffRegisterView.as_view(), name='staff-signup'),
  path('customer-signup/', CustomerRegisterView.as_view(), name='customer-signup'),
] + router.urls

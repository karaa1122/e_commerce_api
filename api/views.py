from rest_framework.views import APIView
from django.core.mail import send_mail
from rest_framework import status
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from django.db import transaction
from api.auth import CustomerAuthentication
from .auth import StaffAuthentication
from .serializers import *




class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class StaffBaseView(viewsets.ModelViewSet):
    authentication_classes = (StaffAuthentication,)


class StaffRegisterView(APIView):
    def post(self, request):
        data = request.data
        serializer = StaffRegisterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'data': {},
            'message': 'Account is created'
        }, status=status.HTTP_201_CREATED)


# end of staff register


# customer_view
class CustomerBaseView(ModelViewSet):
    authentication_classes = (CustomerAuthentication,)


class CustomerCategoryViewSet(CustomerBaseView):
    http_method_names = ['get']
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CustomerItemsViewSet(CustomerBaseView):
    http_method_names = ['get']
    queryset = Item.objects.with_final_price()
    serializer_class = ItemSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['item_name', 'category__name']
    ordering_fields = ['price']
    pagination_class = Pagination


class CustomerRegisterView(APIView):

    def post(self, request):
        data = request.data
        serializer = CustomerRegisterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'data': {},
            'message': 'Account is created'
        }, status=status.HTTP_201_CREATED)


# end of customer register


class CategoryViewSet(StaffBaseView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ItemViewSet(StaffBaseView):
    queryset = Item.objects.with_final_price()
    serializer_class = ItemSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['item_name', 'category__name']
    ordering_fields = ['price']
    pagination_class = Pagination


class CustomerOrdersViewSet(CustomerBaseView):
    http_method_names = ['get', 'post']

    def get_queryset(self):
        return Orders.objects.exclude(order_status=Orders.PENDING).filter(user=self.request.user)

    serializer_class = CustomerOrdersSerializer

    @action(methods=['post'], detail=False)
    def add_to_cart(self, request, *args, **kwargs):
        serializer = AddToCartSerializer(data=request.data, context=dict(request=request))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class StaffOrderViewset(StaffBaseView):
    queryset = Orders.objects.exclude(order_status=Orders.PENDING)
    serializer_class = StaffOrdersSerializer


class TransactionViewSet(StaffBaseView):
    http_method_names = ['get']
    queryset = Transaction.objects.all().select_related('order')
    serializer_class = TransactionSerializer



class CardViewSet(ModelViewSet):
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:

            return Card.objects.filter(customer=user)
        else:

            return Card.objects.none()

    def perform_create(self, serializer):
        
        serializer.save(customer=self.request.user)




class CartItemViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        cart = Orders.get_customer_cart(self.request.user)
        return cart.order_items.all()

    serializer_class = CartItemSerializer


class CheckoutViewSet(viewsets.ViewSet):
    authentication_classes = (CustomerAuthentication,)

    def create(self, request):
        serializer = CheckoutSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        payment_method = serializer.validated_data['payment_method']
        card_id = serializer.validated_data.get('card_id')

        try:
            order = Orders.get_customer_cart(request.user)
        except Orders.DoesNotExist:
            return Response({'detail': 'Invalid cart'}, status=status.HTTP_400_BAD_REQUEST)

   
        if not order.order_items.exists():
            return Response({'detail': 'Order has already been processed'}, status=status.HTTP_400_BAD_REQUEST)

        for order_item in order.order_items.all():
            if order_item.quantity > order_item.item.stock:
                return Response({'detail': 'Insufficient stock quantity'}, status=status.HTTP_400_BAD_REQUEST)

        if payment_method == 'credit_card' and not card_id:
            return Response({'detail': 'Card ID is required for credit card payment'}, status=status.HTTP_400_BAD_REQUEST)



        if payment_method == 'credit_card':
            try:
                card = Card.objects.get(id=card_id, customer=request.user)
            except Card.DoesNotExist:
                return Response({'detail': 'Invalid card ID'}, status=status.HTTP_400_BAD_REQUEST)

        for order_item in order.order_items.all():
            order_item.item.stock -= order_item.quantity
            order_item.item.save()

        order.order_status = 'ordered'
        order.payment_method = payment_method
        order.save()

        transaction_data = {
            'customer': request.user,
            'order': order,
            'amount': order.total_amount,
            'payment_method': payment_method,
            'transaction_type': 'payment',
        }

        if payment_method == 'credit_card':
            transaction_data['card'] = card

        Transaction.objects.create(**transaction_data)

        send_mail(
            subject='Order Confirmation',
            message='Your order has been confirmed and processed successfully.',
            from_email='admin@admin.com',
            recipient_list=[request.user.email],
            fail_silently=True,
        )

        return Response({'detail': 'Checkout successful'}, status=status.HTTP_200_OK)


 
class RefundViewSet(viewsets.ViewSet):
    authentication_classes = (StaffAuthentication,)

    def create(self, request):
        serializer = RefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data['order_id']

        try:
            order = Orders.objects.get(id=order_id)
        except Orders.DoesNotExist:
            return Response({'detail': 'Invalid order ID'}, status=status.HTTP_400_BAD_REQUEST)

        order_items = order.order_items.all()

        with transaction.atomic():
            for order_item in order_items:
                item = order_item.item
                quantity = order_item.quantity

                item.stock += quantity  
                item.save()

            
            order.order_status = 'rejected'
            order.save()

            Transaction.objects.create(
                customer=order.user,
                order=order,
                amount=0,
                payment_method='refund',
                transaction_type='refund'
            )

        send_mail(
            subject='Refund Processed',
            message='Your refund has been processed successfully.',
            from_email='admin@admin.com',
            recipient_list=[order.user.email],
            fail_silently=True,
        )

        return Response({'detail': 'Refund processed successfully'}, status=status.HTTP_200_OK)

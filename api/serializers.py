from rest_framework import serializers
from .models import *
from django.core.mail import send_mail
from rest_framework.response import Response
from rest_framework import status


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class ItemSerializer(serializers.ModelSerializer):
    final_price = serializers.FloatField(read_only=True)

    class Meta:
        model = Item
        fields = "__all__"


class StaffRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        if CustomUser.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username is taken")
        return super(StaffRegisterSerializer, self).validate(data)

    def create(self, validated_data):
        user = CustomUser.objects.create(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            username=validated_data['username'].lower(),
            is_staff=True
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class CustomerRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        if CustomUser.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username is taken")
        return data

    def create(self, validated_data):
        user = CustomUser.objects.create(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            username=validated_data['username'].lower()
        )
        user.set_password(validated_data['password'])
        user.save()
        return user




class StaffOrdersSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Orders
        fields = ['id', 'user', 'created_at', 'total_amount', 'order_status', 'payment_method', 'items']

    def get_total_amount(self, obj):
        total_amount = 0
        for order_item in obj.order_items.all():
            item = order_item.item
            if item.on_discount:
                total_amount += (item.price - item.discount_price) * order_item.quantity
            else:
                total_amount += item.price * order_item.quantity
        return total_amount

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['total_amount'] = self.get_total_amount(instance)


        items_data = []
        for order_item in instance.order_items.all():
            item_data = {
                'id': order_item.item.id,
                'item_name': order_item.item.item_name,
                'price': order_item.item.price,
                'on_discount': order_item.item.on_discount,
                'discount_price': order_item.item.discount_price,
                'stock': order_item.item.stock,
                'description': order_item.item.description,
                'Category': order_item.item.Category.id,
                'quantity': order_item.quantity,
            }
            items_data.append(item_data)

        representation['items'] = items_data
        return representation
    


class CustomerOrdersSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField(read_only=True)
    total_amount = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Orders
        fields = ['id', 'user', 'items', 'created_at', 'total_amount', 'order_status', 'payment_method']

    def get_items(self, obj):
        items_data = []
        order_items = obj.order_items.all()
        for order_item in order_items:
            item_data = ItemSerializer(order_item.item).data
            item_data['quantity'] = order_item.quantity
            items_data.append(item_data)
        return items_data

    def get_total_amount(self, obj):
        total_amount = 0
        for order_item in obj.order_items.all():
            item = order_item.item
            if item.on_discount:
                total_amount += (item.price - item.discount_price) * order_item.quantity
            else:
                total_amount += item.price * order_item.quantity
        return total_amount



class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            fields.pop('customer', None)

        return fields
 

class TransactionSerializer(serializers.ModelSerializer):
    order = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['id', 'payment_method', 'transaction_type', 'order_id', 'order']

    def get_order(self, obj):
        order_data = StaffOrdersSerializer(obj.order).data
        order_items_data = []
        final_price = 0
        for order_item in obj.order.order_items.all():
            item_data = ItemSerializer(order_item.item).data
            item_data['quantity'] = order_item.quantity
            order_items_data.append(item_data)
            item_price = order_item.item.price
            if order_item.item.on_discount:
                item_price = order_item.item.discount_price
            final_price += item_price * order_item.quantity
        order_data['items'] = order_items_data
        order_data['total_amount'] = self.get_total_amount(obj.order)  
        return order_data

    def get_total_amount(self, order):
        total_amount = 0
        for order_item in order.order_items.all():
            item = order_item.item
            if item.on_discount:
                total_amount += (item.price - item.discount_price) * order_item.quantity
            else:
                total_amount += item.price * order_item.quantity
        return total_amount
    
    

class AddToCartSerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())

    class Meta:
        model = OrderItem
        fields = ['id', 'item', 'quantity']

    def create(self, validated_data):
        user = self.context.get('request').user
        existing_cart = Orders.objects.filter(user=user, order_status=Orders.PENDING)

        if existing_cart.exists():
            order = existing_cart.latest('pk')
        else:
            order = Orders.objects.create(user=user)

        validated_data.update({'order': order})
        return super().create(validated_data)


class CartItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer()
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'item', 'quantity', 'total_amount']

    def get_total_amount(self, obj):
        item = obj.item
        if item.on_discount:
            total_price = (item.price - item.discount_price) * obj.quantity
        else:
            total_price = item.price * obj.quantity
        return total_price


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.FloatField(source='get_total_amount')

    class Meta:
        model = Orders
        fields = ['id', 'items', 'total_amount']

    def get_total_amount(self, obj):
        return obj.total_amount



class CheckoutSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=Orders.PAYMENT_METHOD_CHOICES)
    card_id = serializers.IntegerField(required=False)

    def validate(self, data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError({'detail': 'Missing request context'})

        payment_method = data['payment_method']
        card_id = data.get('card_id')

        try:
            order = Orders.get_customer_cart(request.user)
        except Orders.DoesNotExist:
            raise serializers.ValidationError({'detail': 'Invalid cart'})

        if order.order_status != Orders.PENDING:
            raise serializers.ValidationError({'detail': 'Order has already been processed'})

        if payment_method == 'credit_card' and not card_id:
            raise serializers.ValidationError({'detail': 'Card ID is required for credit card payment'})

        if payment_method == 'credit_card':
            try:
                Card.objects.get(id=card_id, customer=order.user)
            except Card.DoesNotExist:
                raise serializers.ValidationError({'detail': 'Invalid card ID'})

        return data

    def create_checkout(self, request):
        serializer = self
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


class RefundSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()

    def validate(self, data):
        order_id = data['order_id']

        try:
            order = Orders.objects.get(id=order_id)
        except Orders.DoesNotExist:
            raise serializers.ValidationError("Invalid order ID")



        if not OrderItem.objects.filter(order=order).exists():
            raise serializers.ValidationError("No items found for the order")

        return data

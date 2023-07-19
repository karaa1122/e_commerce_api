from rest_framework import serializers

from .models import *


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


class CustomerOrdersSerializer(serializers.ModelSerializer):
    items = ItemSerializer(many=True, read_only=True)
    discount = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Orders
        fields = ['id', 'user', 'items', 'created_at', 'total_amount', 'order_status', 'discount', 'payment_method']

    def get_discount(self, obj):
        items = obj.items.all()
        total_discount = 0
        for item in items:
            if item.on_discount:
                total_discount += item.discount_price * item.orderitem_set.get(order=obj).quantity
        return total_discount


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = '__all__'

    def get_fields(self):
        fields = super().get_fields()

        user = self.context['request'].user
        if user.is_staff:
            fields = {'id': fields['id']}

        return fields


        
class TransactionSerializer(serializers.ModelSerializer):
    order = StaffOrdersSerializer()
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['id', 'payment_method', 'transaction_type', 'order_id', 'order', 'final_price']

    def get_final_price(self, obj):
        order = obj.order
        items = order.items.all()
        final_price = sum(self.calculate_item_price(item) for item in items)
        return final_price

    def calculate_item_price(self, item):
        if item.on_discount:
            return item.discount_price
        return item.price


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
    order_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=Orders.PAYMENT_METHOD_CHOICES)
    card_id = serializers.IntegerField(required=False)

    def validate(self, data):
        order_id = data['order_id']
        payment_method = data['payment_method']
        card_id = data.get('card_id')

        try:
            order = Orders.objects.get(id=order_id)
        except Orders.DoesNotExist:
            raise serializers.ValidationError("Invalid order ID")

        if order.order_status != Orders.PENDING:
            raise serializers.ValidationError("Order has already been processed")

        if payment_method == 'credit_card' and not card_id:
            raise serializers.ValidationError("Card ID is required for credit card payment")

        if payment_method == 'credit_card':
            try:
                Card.objects.get(id=card_id, customer=order.user)
            except Card.DoesNotExist:
                raise serializers.ValidationError("Invalid card ID")

        return super().validate(data)





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

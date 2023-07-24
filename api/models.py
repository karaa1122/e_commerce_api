from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F


class CustomUser(AbstractUser):
    pass


class Card(models.Model):
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True) #making the customer field not required   
    card_number = models.CharField(max_length=16)
    cvv = models.CharField(max_length=3)
    expire_date = models.DateField()

    def __str__(self):  
        return self.card_number


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Item(models.Model):
    item_name = models.CharField(max_length=100)
    price = models.FloatField(default=0)
    on_discount = models.BooleanField(default=False)
    discount_price = models.FloatField(blank=True, null=True)
    Category = models.ForeignKey(Category, on_delete=models.CASCADE)
    stock = models.IntegerField(default=0)
    description = models.TextField()

    class ItemManager(models.Manager):

        def with_final_price(self):
            return self.get_queryset().annotate(
                final_price=models.Case(
                    models.When(
                        on_discount=True,
                        then=models.ExpressionWrapper(
                            models.F('price') - models.F('discount_price'), output_field=models.FloatField()
                        )
                    ),
                    default=models.F('price')
                )
            ).order_by('-id')

    objects = ItemManager()


class OrderItem(models.Model):
    order = models.ForeignKey('Orders', related_name='order_items', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


class Orders(models.Model):
    PENDING = 'pending'
    ORDER_STATUS_CHOICES = (
        (PENDING, 'Pending'),
        ('rejected', 'Rejected'),
        ('ordered', 'ordered'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    items = models.ManyToManyField(Item, through=OrderItem)
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.FloatField(default=0)
    order_status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES, default='cash')

    def __str__(self):
        return f"Order #{self.pk} by {self.user.username}"

    @classmethod
    def get_customer_cart(cls, user):
        instance, _ = Orders.objects.get_or_create(
            user=user, order_status=cls.PENDING,
            defaults=dict(user=user)
        )
        return instance

    def decrement_stock(self):
        for item in self.items.all():
            order_item = OrderItem.objects.get(order=self, item=item)
            item.stock = F('stock') - order_item.quantity
            item.save()

    

class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ('payment', 'Payment'),
        ('refund', 'Refund'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
    )

    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    amount = models.FloatField()
    
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES, default='cash')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Transaction #{self.pk} - {self.transaction_type}"

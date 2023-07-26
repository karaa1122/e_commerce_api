from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']

    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'groups']

    
    search_fields = ['username', 'email', 'first_name', 'last_name']

    
    ordering = ['username']

    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['customer', 'masked_card_number', 'cvv', 'expire_date']
    search_fields = ['customer__username', 'customer__email', 'card_number']

    def masked_card_number(self, obj):
        return f"**** **** **** {obj.card_number[-4:]}"
    masked_card_number.short_description = 'Card Number'




@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['item_name', 'price', 'on_discount', 'discount_price', 'Category', 'stock']
    list_filter = ['on_discount', 'Category']
    search_fields = ['item_name', 'Category__name']
    ordering = ['item_name']

class OrderItemInline(admin.TabularInline):
    model = OrderItem

@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'user', 'created_at', 'total_amount', 'order_status', 'payment_method']
    list_filter = ['order_status', 'payment_method']
    search_fields = ['user__username']
    ordering = ['-created_at']
    inlines = [OrderItemInline]

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'customer', 'order', 'amount', 'transaction_type', 'payment_method', 'card']
    list_filter = ['transaction_type', 'payment_method']
    search_fields = ['customer__username', 'order__user__username']
    ordering = ['-id']
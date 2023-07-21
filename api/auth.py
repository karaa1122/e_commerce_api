from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission
from api.models import Orders
User = get_user_model()


class StaffAuthentication(JWTAuthentication):
    CHECK_IS_STAFF = True

    def authenticate(self, request):
        user, token = super().authenticate(request)
        if user and user.is_staff == self.CHECK_IS_STAFF:
            return user, token
        else:
            raise AuthenticationFailed(detail='User is not a staff member.')


class CustomerAuthentication(StaffAuthentication):
    CHECK_IS_STAFF = False


class CanCheckout(BasePermission):
    message = 'Cannot checkout. An order has already been processed.'

    def has_permission(self, request, view):
        user = request.user
        try:
            order = Orders.get_customer_cart(user)
            return order.order_status == Orders.PENDING
        except Orders.DoesNotExist:
            return False
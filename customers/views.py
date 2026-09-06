"""Customer API views.

Public may register (throttled). A logged-in customer may read their own profile
and order history. Admin may browse the customer list with derived order stats.
"""

from django.db.models import Count, Max, Min
from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from customers.models import Customer
from customers.serializers import (
    CustomerAdminSerializer,
    CustomerOrderSerializer,
    CustomerProfileSerializer,
    RegisterSerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MeView(APIView):
    """The authenticated customer's own profile and order history."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        customer = getattr(request.user, "customer", None)
        if customer is None:
            return Response({"detail": "No customer profile for this account."}, status=404)
        orders = (
            customer.bookings.select_related("product").order_by("-created_at")
        )
        return Response(
            {
                "profile": CustomerProfileSerializer(customer).data,
                "orders": CustomerOrderSerializer(orders, many=True).data,
            }
        )


class CustomerAdminViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = CustomerAdminSerializer
    permission_classes = [IsAdminUser]
    queryset = Customer.objects.annotate(
        total_orders=Count("bookings"),
        first_order_date=Min("bookings__created_at"),
        last_order_date=Max("bookings__created_at"),
    ).order_by("-created_at")

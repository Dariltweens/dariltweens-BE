"""Customer API views.

Public may register (throttled). A logged-in customer may read their own profile
and order history. Admin may browse the customer list with derived order stats.
"""

from django.db.models import Count, Max, Min
from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer

from customers.models import Customer
from customers.serializers import (
    CustomerAdminSerializer,
    CustomerOrderSerializer,
    CustomerProfileSerializer,
    RegisterSerializer,
)


@extend_schema(
    summary="Register a new customer account",
    description="Public endpoint to create a new user account and associated customer profile.",
    request=RegisterSerializer,
    responses={201: RegisterSerializer},
    tags=["Public - Customers"],
)
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MeView(APIView):
    """The authenticated customer's own profile and order history."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve authenticated profile and bookings",
        description="Retrieve the currently logged-in customer's profile details and booking reservation history.",
        responses={
            200: inline_serializer(
                name="MeProfileResponse",
                fields={
                    "profile": CustomerProfileSerializer(),
                    "orders": CustomerOrderSerializer(many=True),
                },
            )
        },
        tags=["Public - Customers"],
    )
    def get(self, request):
        customer = getattr(request.user, "customer", None)
        if customer is None:
            return Response(
                {"detail": "No customer profile for this account."}, status=404
            )
        orders = customer.bookings.select_related("product").order_by("-created_at")
        return Response(
            {
                "profile": CustomerProfileSerializer(customer).data,
                "orders": CustomerOrderSerializer(orders, many=True).data,
            }
        )


@extend_schema_view(
    list=extend_schema(
        summary="List all customers",
        description="Retrieve a list of all customers, complete with aggregate statistics (total bookings count, first and last booking dates). (Admin-only)",
        responses={200: CustomerAdminSerializer(many=True)},
        tags=["Admin - Customers"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a customer profile",
        description="Retrieve a specific customer's detailed profile and booking summary by ID. (Admin-only)",
        responses={200: CustomerAdminSerializer},
        tags=["Admin - Customers"],
    ),
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

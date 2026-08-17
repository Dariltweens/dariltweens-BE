"""Admin for bookings.

Status changes are routed through bookings.services.transition_booking so the
state machine is enforced and cancellations release reserved stock — the admin
must not bypass that logic with a raw save.
"""

from django.contrib import admin
from django.core.exceptions import ValidationError

from bookings.models import Booking
from bookings.exceptions import InvalidTransition
from bookings.services import transition_booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "quantity", "pickup_date", "status", "created_at"]
    list_filter = ["status", "pickup_date"]
    search_fields = ["product__name"]
    autocomplete_fields = ["product"]
    list_select_related = ["product"]
    readonly_fields = ["created_at", "updated_at"]

    def save_model(self, request, obj, form, change):
        # New bookings created via admin reserve stock through the service.
        if not change:
            super().save_model(request, obj, form, change)
            return

        # Existing booking: if status changed, run it through the state machine.
        if "status" in form.changed_data:
            try:
                transition_booking(booking_id=obj.pk, new_status=obj.status)
            except InvalidTransition as exc:
                raise ValidationError(str(exc)) from exc
        else:
            super().save_model(request, obj, form, change)

"""Price list API routes."""

from rest_framework.routers import DefaultRouter

from pricelist.views import PriceListViewSet

router = DefaultRouter()
router.register("price-list", PriceListViewSet, basename="price-list")

urlpatterns = router.urls

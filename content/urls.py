"""Content API routes."""

from rest_framework.routers import DefaultRouter

from content.views import ArticleViewSet

router = DefaultRouter()
router.register("articles", ArticleViewSet, basename="article")

urlpatterns = router.urls

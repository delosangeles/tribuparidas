from rest_framework.routers import DefaultRouter

from .views import FestejoViewSet

router = DefaultRouter()
router.register("festejos", FestejoViewSet, basename="festejo")

urlpatterns = router.urls

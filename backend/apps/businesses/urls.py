from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from .views import AdminBusinessViewSet, BusinessPublicViewSet, MyBusinessImageViewSet, MyBusinessViewSet

router = DefaultRouter()
router.register("businesses", BusinessPublicViewSet, basename="business")
router.register("my/businesses", MyBusinessViewSet, basename="my-business")

admin_router = DefaultRouter()
admin_router.register("admin/businesses", AdminBusinessViewSet, basename="admin-business")

images_router = NestedDefaultRouter(router, "my/businesses", lookup="business")
images_router.register("images", MyBusinessImageViewSet, basename="my-business-images")

urlpatterns = [*router.urls, *images_router.urls, *admin_router.urls]

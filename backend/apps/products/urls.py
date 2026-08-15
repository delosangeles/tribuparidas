from django.urls import path
from rest_framework_nested.routers import NestedDefaultRouter

from apps.businesses.urls import router as businesses_router

from .views import BusinessProductsPublicView, MyBusinessProductsViewSet, MyProductDetailView

products_router = NestedDefaultRouter(businesses_router, "my/businesses", lookup="business")
products_router.register("products", MyBusinessProductsViewSet, basename="my-business-products")

urlpatterns = [
    path("businesses/<slug:slug>/products/", BusinessProductsPublicView.as_view(), name="business-products"),
    path("my/products/<int:pk>/", MyProductDetailView.as_view(), name="my-product-detail"),
    *products_router.urls,
]

from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AdminUserViewSet,
    ChangePasswordView,
    CustomTokenObtainPairView,
    LogoutView,
    MeView,
    NotificationViewSet,
    PasswordResetRequestView,
    RegisterView,
)

admin_router = DefaultRouter()
admin_router.register("admin/users", AdminUserViewSet, basename="admin-user")
admin_router.register("admin/notifications", NotificationViewSet, basename="admin-notification")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", CustomTokenObtainPairView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/password-reset-request/", PasswordResetRequestView.as_view(), name="auth-password-reset-request"),
    path("me/", MeView.as_view(), name="me"),
    path("me/change-password/", ChangePasswordView.as_view(), name="me-change-password"),
    *admin_router.urls,
]

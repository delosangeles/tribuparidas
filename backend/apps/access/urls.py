from django.urls import path

from .views import MadrinaDetailView, MadrinaListView

urlpatterns = [
    path("admin/madrinas/", MadrinaListView.as_view(), name="admin-madrinas"),
    path("admin/madrinas/<int:user_id>/", MadrinaDetailView.as_view(), name="admin-madrina-detail"),
]

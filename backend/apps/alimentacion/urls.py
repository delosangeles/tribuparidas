from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

public = DefaultRouter()
public.register("guias", views.GuideViewSet, basename="alimentacion-guide")
public.register("recetas", views.RecipeViewSet, basename="alimentacion-recipe")
public.register("alimentos", views.FoodViewSet, basename="alimentacion-food")

admin = DefaultRouter()
admin.register("recetas", views.RecipeAdminViewSet, basename="alimentacion-admin-recipe")
admin.register("guias", views.GuideAdminViewSet, basename="alimentacion-admin-guide")
admin.register("alimentos", views.FoodAdminViewSet, basename="alimentacion-admin-food")
admin.register("edades", views.AgeAdminViewSet, basename="alimentacion-admin-age")
admin.register("alergenos", views.AllergenAdminViewSet, basename="alimentacion-admin-allergen")
admin.register("tipos", views.MealTypeAdminViewSet, basename="alimentacion-admin-mealtype")

urlpatterns = [
    path("alimentacion/seguridad/", views.SafetyView.as_view(), name="alimentacion-safety"),
    path("alimentacion/catalogos/", views.CatalogsView.as_view(), name="alimentacion-catalogs"),
    path("alimentacion/favoritos/", views.FavoriteListView.as_view(), name="alimentacion-favorites"),
    path("alimentacion/recetas/<slug:slug>/favorito/", views.FavoriteToggleView.as_view(), name="alimentacion-favorite"),
    path("alimentacion/admin/seguridad/", views.SafetyAdminView.as_view(), name="alimentacion-admin-safety"),
    path("alimentacion/admin/", include(admin.urls)),
    path("alimentacion/", include(public.urls)),
]

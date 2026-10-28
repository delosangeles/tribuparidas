from django.db.models import Q
from django_filters import rest_framework as filters

from django.contrib.auth import get_user_model

User = get_user_model()

# Solo la importación del Excel llena `form_submitted_at`: es la marca de
# "esta usuaria tiene datos que vinieron del formulario de inscripción".
FROM_EXCEL = Q(member_profile__form_submitted_at__isnull=False)


class AdminUserFilter(filters.FilterSet):
    has_excel_data = filters.BooleanFilter(method="filter_excel")

    class Meta:
        model = User
        fields = ["is_active", "is_approved", "is_staff", "registration_status"]

    def filter_excel(self, queryset, name, value):
        return queryset.filter(FROM_EXCEL) if value else queryset.exclude(FROM_EXCEL)

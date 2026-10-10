from rest_framework import serializers

from .models import Festejo


def mother_display_name(user):
    profile = getattr(user, "member_profile", None)
    return (profile.preferred_name if profile else "") or user.get_full_name()


class FestejoSerializer(serializers.ModelSerializer):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    mother_name = serializers.SerializerMethodField()
    child_name = serializers.CharField(source="child.name", read_only=True, default=None)
    headline = serializers.SerializerMethodField()

    class Meta:
        model = Festejo
        fields = [
            "id", "kind", "kind_label", "event_date", "user", "child", "number",
            "title", "note", "status", "is_manual", "mother_name", "child_name", "headline",
        ]
        read_only_fields = ["id", "is_manual", "kind_label", "mother_name", "child_name", "headline"]
        validators = []  # el duplicado se valida a mano (child puede ser nulo)

    def get_mother_name(self, obj):
        return mother_display_name(obj.user)

    def get_headline(self, obj):
        # Texto listo para la tarjeta; no incluye fecha de nacimiento (privacidad).
        who = obj.child.name if obj.child_id else mother_display_name(obj.user)
        if obj.kind == Festejo.Kind.MONTHIVERSARY:
            return f"{who} cumple {obj.number} {'mes' if obj.number == 1 else 'meses'}"
        if obj.kind in (Festejo.Kind.CHILD_BIRTHDAY, Festejo.Kind.MOTHER_BIRTHDAY):
            return f"{who} cumple {obj.number} {'año' if obj.number == 1 else 'años'}"
        return obj.title or who

    def validate(self, attrs):
        child = attrs.get("child")
        user = attrs.get("user") or getattr(self.instance, "user", None)
        if child and user and child.user_id != user.id:
            raise serializers.ValidationError({"child": "El hijo/a no pertenece a esa usuaria."})
        kind = attrs.get("kind") or getattr(self.instance, "kind", None)
        if kind == Festejo.Kind.MANUAL and not (attrs.get("title") or getattr(self.instance, "title", "")):
            raise serializers.ValidationError({"title": "El festejo manual necesita un título."})
        event_date = attrs.get("event_date") or getattr(self.instance, "event_date", None)
        duplicates = Festejo.objects.filter(kind=kind, user=user, child=attrs.get("child", getattr(self.instance, "child", None)), event_date=event_date)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("Ya existe un festejo igual para esa persona y fecha.")
        return attrs

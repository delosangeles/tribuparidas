from rest_framework import serializers

from apps.core.validators import validate_image_file

from .models import Festejo


def mother_display_name(user):
    profile = getattr(user, "member_profile", None)
    return (profile.preferred_name if profile else "") or user.get_full_name()


class FestejoSerializer(serializers.ModelSerializer):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    mother_name = serializers.SerializerMethodField()
    child_name = serializers.CharField(source="child.name", read_only=True, default=None)
    headline = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()
    # Subida de imagen propia (multipart). La URL final se lee en `photo`.
    image = serializers.ImageField(source="photo", write_only=True, required=False, allow_null=True, validators=[validate_image_file])

    class Meta:
        model = Festejo
        fields = [
            "id", "kind", "kind_label", "event_date", "user", "child", "number",
            "title", "note", "status", "is_manual", "mother_name", "child_name", "headline", "photo", "image",
        ]
        read_only_fields = ["id", "is_manual", "kind_label", "mother_name", "child_name", "headline", "photo"]
        validators = []  # el duplicado se valida a mano (child puede ser nulo)

    def get_photo(self, obj):
        # Primero la imagen propia del festejo; si no, la del hijo/a o la foto de perfil de la mamá.
        image = obj.photo or (obj.child.photo if obj.child_id else obj.user.photo)
        if not image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(image.url) if request else image.url

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

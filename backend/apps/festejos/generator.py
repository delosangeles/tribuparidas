from django.contrib.auth import get_user_model

from apps.users.models import Child

from .logic import birthdays, monthiversaries
from .models import Festejo


def generate(start, end):
    """Crea (idempotente) los festejos con fecha en [start, end] a partir del
    perfil. Devuelve cuántos nuevos creó. Solo usuarias activas."""
    User = get_user_model()
    created = 0

    def make(**kwargs):
        nonlocal created
        _, was_created = Festejo.objects.get_or_create(**kwargs)
        created += int(was_created)

    for child in Child.objects.filter(user__is_active=True, birth_date__isnull=False).exclude(name="").select_related("user"):
        for when, n in monthiversaries(child.birth_date, start, end):
            make(kind=Festejo.Kind.MONTHIVERSARY, user=child.user, child=child, event_date=when, defaults={"number": n})
        for when, age in birthdays(child.birth_date, start, end):
            make(kind=Festejo.Kind.CHILD_BIRTHDAY, user=child.user, child=child, event_date=when, defaults={"number": age})

    for mother in User.objects.filter(is_active=True, birth_date__isnull=False):
        for when, age in birthdays(mother.birth_date, start, end):
            make(kind=Festejo.Kind.MOTHER_BIRTHDAY, user=mother, child=None, event_date=when, defaults={"number": age})

    return created

from django.db.models import Avg
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Review


def _recalculate_average_rating(business):
    result = business.reviews.filter(is_active=True).aggregate(avg=Avg("rating"))
    business.average_rating = round(result["avg"] or 0, 2)
    business.save(update_fields=["average_rating", "updated_at"])


@receiver(post_save, sender=Review)
def on_review_saved(sender, instance, **kwargs):
    _recalculate_average_rating(instance.business)


@receiver(post_delete, sender=Review)
def on_review_deleted(sender, instance, **kwargs):
    _recalculate_average_rating(instance.business)

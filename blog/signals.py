from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from .models import Post


@receiver(post_save, sender=Post)
def refresh_vector_on_save(sender, instance, **kwargs):
    instance.update_search_vector()


@receiver(m2m_changed, sender=Post.tags.through)
def refresh_vector_on_tags(sender, instance, action, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"} and isinstance(instance, Post):
        instance.update_search_vector()
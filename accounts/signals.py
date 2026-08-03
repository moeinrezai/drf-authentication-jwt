from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
   
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
  
    if hasattr(instance, "profile"):
        instance.profile.save()


@receiver(post_save, sender=User)
def blacklist_tokens_on_password_change(sender, instance, **kwargs):
    update_fields = kwargs.get("update_fields")
    if update_fields and "password" in update_fields:
        from .api.v1.utils import blacklist_all_user_tokens

        blacklist_all_user_tokens(instance)

# backend/signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


@receiver(user_logged_in)
def ensure_superuser_profile(sender, request, user, **kwargs):
    """Auto-create a UserProfile with SuperAdmin role for superusers that lack one."""
    if not user.is_superuser:
        return
    from .models import UserProfile, Role
    if not UserProfile.objects.filter(user=user).exists():
        role = Role.objects.filter(name='SuperAdmin').first()
        UserProfile.objects.create(user=user, role=role)

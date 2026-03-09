# backend/rbac.py

def get_user_permissions(user):
    """Return a set of permission codenames for the user's role."""
    if not user.is_authenticated:
        return set()
    # Superusers always get full access, even without a UserProfile
    if user.is_superuser:
        return {'*'}
    try:
        role = user.profile.role
        if role is None:
            return set()
        return set(role.permissions.values_list('codename', flat=True))
    except Exception:
        return set()


def has_permission(user, codename):
    """Check if user has a specific permission codename."""
    perms = get_user_permissions(user)
    return '*' in perms or codename in perms


def get_user_menus(user):
    """Return Menu objects the user has READ permission for, for sidebar rendering."""
    from .models import Menu, Permission
    if not user.is_authenticated:
        return Menu.objects.none()
    # Superusers see all active top-level menus
    if user.is_superuser:
        return Menu.objects.filter(is_active=True, parent=None).prefetch_related('menu_set')
    try:
        role = user.profile.role
        if role is None:
            return Menu.objects.none()
        readable_menu_ids = Permission.objects.filter(
            roles=role, action='READ'
        ).values_list('menu_id', flat=True)
        return Menu.objects.filter(id__in=readable_menu_ids, is_active=True, parent=None).prefetch_related('menu_set')
    except Exception:
        return Menu.objects.none()

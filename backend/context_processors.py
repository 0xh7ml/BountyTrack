# backend/context_processors.py
from .rbac import get_user_menus, get_user_permissions


def rbac_context(request):
    return {
        'sidebar_menus': get_user_menus(request.user),
        'user_permissions': get_user_permissions(request.user),
    }

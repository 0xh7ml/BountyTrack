# backend/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .rbac import has_permission


def permission_required(codename):
    """Decorator for views requiring a specific RBAC permission."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if not has_permission(request.user, codename):
                messages.error(request, "You don't have permission to access this page.")
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# backend/views_rbac.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse

from .decorators import permission_required
from .models import Menu, Permission, Role


# ─── Menu Management ─────────────────────────────────────────────────────────

@permission_required('manage_menus.read')
def MenuListView(request):
    menus = Menu.objects.select_related('parent').order_by('order')
    return render(request, 'manage/menus.html', {'menus': menus})


@permission_required('manage_menus.create')
def MenuCreateView(request):
    parent_menus = Menu.objects.filter(parent=None, is_active=True)
    if request.method == 'POST':
        menu = Menu(
            name     = request.POST.get('name', '').strip(),
            url_name = request.POST.get('url_name', '').strip(),
            icon     = request.POST.get('icon', '').strip(),
            order    = int(request.POST.get('order', 0)),
            is_active= request.POST.get('is_active') == 'on',
        )
        parent_id = request.POST.get('parent')
        if parent_id:
            menu.parent_id = parent_id
        menu.save()
        messages.success(request, 'Menu created.')
        return redirect('manage_menus')
    return render(request, 'manage/menu-form.html', {'parent_menus': parent_menus, 'action': 'Create'})


@permission_required('manage_menus.update')
def MenuEditView(request, id):
    menu         = get_object_or_404(Menu, pk=id)
    parent_menus = Menu.objects.filter(parent=None, is_active=True).exclude(pk=id)
    if request.method == 'POST':
        menu.name     = request.POST.get('name', menu.name).strip()
        menu.url_name = request.POST.get('url_name', menu.url_name).strip()
        menu.icon     = request.POST.get('icon', menu.icon).strip()
        menu.order    = int(request.POST.get('order', menu.order))
        menu.is_active= request.POST.get('is_active') == 'on'
        parent_id     = request.POST.get('parent')
        menu.parent   = Menu.objects.filter(pk=parent_id).first() if parent_id else None
        menu.save()
        messages.success(request, 'Menu updated.')
        return redirect('manage_menus')
    return render(request, 'manage/menu-form.html', {'menu': menu, 'parent_menus': parent_menus, 'action': 'Edit'})


@permission_required('manage_menus.delete')
def MenuDeleteView(request, id):
    menu = get_object_or_404(Menu, pk=id)
    if request.method == 'POST':
        menu.delete()
        return JsonResponse({'message': 'Menu deleted.', 'status': 'success'})
    return JsonResponse({'error': 'Invalid'}, status=400)


# ─── Role Management ─────────────────────────────────────────────────────────

@permission_required('manage_roles.read')
def RoleListView(request):
    roles = Role.objects.prefetch_related('permissions').order_by('name')
    return render(request, 'manage/roles.html', {'roles': roles})


@permission_required('manage_roles.create')
def RoleCreateView(request):
    menus       = Menu.objects.filter(is_active=True).prefetch_related('permissions')
    all_actions = ['CREATE', 'READ', 'UPDATE', 'DELETE']
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if Role.objects.filter(name=name).exists():
            messages.error(request, 'A role with this name already exists.')
        else:
            role = Role.objects.create(name=name)
            selected_perm_ids = request.POST.getlist('permissions')
            role.permissions.set(Permission.objects.filter(pk__in=selected_perm_ids))
            messages.success(request, f'Role "{name}" created.')
            return redirect('manage_roles')
    return render(request, 'manage/role-permissions.html', {
        'menus': menus, 'all_actions': all_actions, 'action': 'Create'
    })


@permission_required('manage_roles.update')
def RoleEditView(request, id):
    role        = get_object_or_404(Role, pk=id)
    menus       = Menu.objects.filter(is_active=True).prefetch_related('permissions')
    all_actions = ['CREATE', 'READ', 'UPDATE', 'DELETE']
    assigned    = set(role.permissions.values_list('id', flat=True))

    if request.method == 'POST':
        if role.is_system and not request.user.is_superuser:
            messages.error(request, 'System roles can only be modified by superusers.')
            return redirect('manage_roles')
        selected_perm_ids = request.POST.getlist('permissions')
        role.permissions.set(Permission.objects.filter(pk__in=selected_perm_ids))
        messages.success(request, f'Role "{role.name}" updated.')
        return redirect('manage_roles')

    return render(request, 'manage/role-permissions.html', {
        'role': role, 'menus': menus, 'all_actions': all_actions,
        'assigned': assigned, 'action': 'Edit'
    })


@permission_required('manage_roles.delete')
def RoleDeleteView(request, id):
    role = get_object_or_404(Role, pk=id)
    if request.method == 'POST':
        if role.is_system:
            return JsonResponse({'message': 'System roles cannot be deleted.', 'status': 'error'}, status=400)
        role.delete()
        return JsonResponse({'message': 'Role deleted.', 'status': 'success'})
    return JsonResponse({'error': 'Invalid'}, status=400)


# ─── Permission List ─────────────────────────────────────────────────────────

@permission_required('manage_permissions.read')
def PermissionListView(request):
    permissions = Permission.objects.select_related('menu').order_by('menu__order', 'action')
    return render(request, 'manage/permissions.html', {'permissions': permissions})

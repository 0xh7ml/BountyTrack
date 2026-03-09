from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from backend.models import Menu, Permission, Role, UserProfile


MENUS = [
    {'name': 'Dashboard',    'url_name': 'home',              'icon': 'fas fa-tachometer-alt', 'order': 1},
    {'name': 'Bug Reports',  'url_name': 'reports',           'icon': 'fa-solid fa-bug',        'order': 2},
    {'name': 'Programs',     'url_name': 'programs',          'icon': 'fa-solid fa-folder',     'order': 3},
    {'name': 'Platforms',    'url_name': 'platforms',         'icon': 'fa-solid fa-server',     'order': 4},
    {'name': 'Analytics',    'url_name': 'analytics.program', 'icon': 'fa-solid fa-chart-line', 'order': 5},
    {'name': 'Users',        'url_name': 'users',             'icon': 'fa-solid fa-users',      'order': 6},
    {'name': 'Manage Menus', 'url_name': 'manage_menus',      'icon': 'fa-solid fa-list',       'order': 7},
    {'name': 'Manage Roles', 'url_name': 'manage_roles',      'icon': 'fa-solid fa-shield',     'order': 8},
]


class Command(BaseCommand):
    help = 'Seeds the initial RBAC data (Menus, Permissions, Roles) and assigns SuperAdmin to superuser.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding RBAC data...')

        # 1. Create Menus
        menu_objects = {}
        for m in MENUS:
            menu, created = Menu.objects.get_or_create(
                url_name=m['url_name'],
                defaults={
                    'name':      m['name'],
                    'icon':      m['icon'],
                    'order':     m['order'],
                    'is_active': True,
                }
            )
            menu_objects[m['url_name']] = menu
            status = 'Created' if created else 'Exists'
            self.stdout.write(f"  Menu [{status}]: {menu.name}")

        # 2. Create Permissions (4 per menu)
        all_permissions = []
        for menu in menu_objects.values():
            for action, _ in Permission.ACTION_CHOICES:
                codename = f"{menu.url_name}.{action.lower()}"
                perm, created = Permission.objects.get_or_create(
                    menu=menu,
                    action=action,
                    defaults={'codename': codename}
                )
                all_permissions.append(perm)
                status = 'Created' if created else 'Exists'
                self.stdout.write(f"  Permission [{status}]: {codename}")

        # 3. Create system Roles
        super_admin_role, _ = Role.objects.get_or_create(
            name='SuperAdmin',
            defaults={'is_system': True}
        )
        super_admin_role.permissions.set(all_permissions)
        super_admin_role.save()
        self.stdout.write(f"  Role: SuperAdmin (all permissions)")

        reporter_role, _ = Role.objects.get_or_create(
            name='Reporter',
            defaults={'is_system': True}
        )
        reporter_perms = list(Permission.objects.filter(
            menu__url_name__in=['home', 'programs', 'platforms', 'analytics.program'],
            action='READ'
        )) + list(Permission.objects.filter(
            menu__url_name='reports'
        ))
        reporter_role.permissions.set(reporter_perms)
        reporter_role.save()
        self.stdout.write(f"  Role: Reporter")

        project_owner_role, _ = Role.objects.get_or_create(
            name='ProjectOwner',
            defaults={'is_system': True}
        )
        po_perms = Permission.objects.filter(
            menu__url_name__in=['home', 'reports', 'programs', 'platforms', 'analytics.program'],
            action='READ'
        )
        project_owner_role.permissions.set(po_perms)
        project_owner_role.save()
        self.stdout.write(f"  Role: ProjectOwner")

        # 4. Assign SuperAdmin to existing superusers
        superusers = User.objects.filter(is_superuser=True)
        for su in superusers:
            profile, created = UserProfile.objects.get_or_create(
                user=su,
                defaults={'role': super_admin_role}
            )
            if not created and profile.role != super_admin_role:
                profile.role = super_admin_role
                profile.save()
            self.stdout.write(f"  UserProfile for superuser '{su.username}' assigned SuperAdmin role.")

        self.stdout.write(self.style.SUCCESS('RBAC seeding complete!'))

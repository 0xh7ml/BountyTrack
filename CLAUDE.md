# CLAUDE.md — Bounty Track Enhancement Plan

> **Stack:** Django · SQLite (dev) / MySQL (prod) · AdminLTE 3 · Bootstrap 5 · Vanilla JS  
> **Rule:** No stack changes. No complex new frameworks. Extend what exists.

---

## Overview

This document is a step-by-step implementation guide to evolve **Bounty Track** from a simple CRUD tracker into a collaborative bug-bounty management platform with:

- Rich report editor (description, impact, remediation + image paste)
- Detailed report view (3-column layout)
- User management (creation, invitation, program following)
- Dynamic RBAC: Menus → Permissions → Roles → Sidebar

Work is split into **6 phases**. Complete each phase fully before moving to the next.

---

## Phase 1 — Database & Model Layer

### 1.1 — New Models in `backend/models.py`

Add the following models **without removing any existing ones**.

---

#### `Menu`
Represents a navigational item that maps to a URL/view.

```python
class Menu(models.Model):
    name        = models.CharField(max_length=100)           # Display name, e.g. "Reports"
    url_name    = models.CharField(max_length=100, unique=True)  # Django URL name, e.g. "reports"
    icon        = models.CharField(max_length=50, blank=True)    # FontAwesome class, e.g. "fa-bug"
    parent      = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    order       = models.PositiveIntegerField(default=0)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        db_table = 'tb_menus'
```

---

#### `Permission`
One permission per action per menu (CREATE, READ, UPDATE, DELETE).

```python
class Permission(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('READ',   'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]
    menu    = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='permissions')
    action  = models.CharField(max_length=10, choices=ACTION_CHOICES)
    codename = models.CharField(max_length=150, unique=True)  # auto-generated: "reports.create"

    class Meta:
        unique_together = ('menu', 'action')
        db_table = 'tb_permissions'

    def save(self, *args, **kwargs):
        if not self.codename:
            self.codename = f"{self.menu.url_name}.{self.action.lower()}"
        super().save(*args, **kwargs)
```

---

#### `Role`
A named collection of permissions.

```python
class Role(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles')
    is_system   = models.BooleanField(default=False)  # True = cannot be deleted (SuperAdmin, Reporter, ProjectOwner)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tb_roles'
```

---

#### `UserProfile`
Extends Django's built-in `User`.

```python
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role        = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    avatar      = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio         = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tb_user_profiles'
```

---

#### `Invitation`
Tracks pending user invitations.

```python
import uuid

class Invitation(models.Model):
    STATUS_CHOICES = [('Pending', 'Pending'), ('Accepted', 'Accepted'), ('Expired', 'Expired')]

    email       = models.EmailField()
    token       = models.UUIDField(default=uuid.uuid4, unique=True)
    role        = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    invited_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_invitations')
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    expires_at  = models.DateTimeField()
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tb_invitations'
```

---

#### `ProgramFollower`
Tracks which users follow which programs.

```python
class ProgramFollower(models.Model):
    program     = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='followers')
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followed_programs')
    joined_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('program', 'user')
        db_table = 'tb_program_followers'
```

---

#### Update `Report` model — add rich-text fields + participants

Add to the existing `Report` model:

```python
# Rich text fields (stored as HTML, sanitized on input)
description  = models.TextField(blank=True)
impact       = models.TextField(blank=True)
remediation  = models.TextField(blank=True)

# Participants
reporter        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_reports')
coordinator     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='coordinated_reports')
developer       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_reports')
collaborators   = models.ManyToManyField(User, blank=True, related_name='collaborated_reports')
```

---

#### `ReportComment`

```python
class ReportComment(models.Model):
    report      = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='comments')
    author      = models.ForeignKey(User, on_delete=models.CASCADE)
    body        = models.TextField()
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        db_table = 'tb_report_comments'
```

---

#### `UploadedImage`
Stores pasted/uploaded images for rich-text fields.

```python
class UploadedImage(models.Model):
    image       = models.ImageField(upload_to='report_images/%Y/%m/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tb_uploaded_images'
```

---

### 1.2 — Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 1.3 — Data Seeder (`backend/management/commands/seed_rbac.py`)

Create a management command that seeds the initial RBAC data automatically on first deploy.

**What it does:**
1. Creates all `Menu` entries matching `backend/urls.py` URL names.
2. Auto-generates all 4 `Permission` records per menu (CREATE, READ, UPDATE, DELETE).
3. Creates 3 system `Role` records:
   - **SuperAdmin** — all permissions
   - **Reporter** — READ on programs/platforms; CREATE/READ/UPDATE/DELETE own reports & comments
   - **ProjectOwner** — READ on reports filtered by their programs
4. Creates `UserProfile` for the existing superuser, assigns SuperAdmin role.

```bash
python manage.py seed_rbac
```

---

## Phase 2 — Settings & Infrastructure Updates

### 2.1 — `core/settings.py` additions

```python
import os

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# For image uploads
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Email (for invitations) — configure via .env
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST     = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT     = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS  = True
EMAIL_HOST_USER     = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@bountytrack.io')

INVITATION_EXPIRY_DAYS = 7
```

### 2.2 — `core/urls.py` additions

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('backend.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 2.3 — `.env.example` additions

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=yourpassword
DEFAULT_FROM_EMAIL=noreply@bountytrack.io
```

---

## Phase 3 — RBAC Middleware & Permission Helpers

### 3.1 — `backend/rbac.py` (new file)

This file provides the core RBAC utilities used across views and templates.

```python
# backend/rbac.py

def get_user_permissions(user):
    """Return a set of permission codenames for the user's role."""
    if not user.is_authenticated:
        return set()
    if user.is_superuser:
        return {'*'}  # wildcard — all permissions
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
    if user.is_superuser:
        return Menu.objects.filter(is_active=True, parent=None).prefetch_related('menu_set')
    try:
        role = user.profile.role
        readable_menu_ids = Permission.objects.filter(
            roles=role, action='READ'
        ).values_list('menu_id', flat=True)
        return Menu.objects.filter(id__in=readable_menu_ids, is_active=True, parent=None)
    except Exception:
        return Menu.objects.none()
```

### 3.2 — `backend/decorators.py` (new file)

```python
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
```

### 3.3 — `backend/context_processors.py` (new file)

Injects sidebar menus and user permissions into every template context.

```python
# backend/context_processors.py
from .rbac import get_user_menus, get_user_permissions

def rbac_context(request):
    return {
        'sidebar_menus': get_user_menus(request.user),
        'user_permissions': get_user_permissions(request.user),
    }
```

Add to `core/settings.py` under `TEMPLATES → OPTIONS → context_processors`:

```python
'backend.context_processors.rbac_context',
```

---

## Phase 4 — New & Updated Views

### 4.1 — Image Upload Endpoint

Add to `backend/views.py`:

```python
@login_required
def UploadImage(request):
    """AJAX endpoint for pasting/uploading images in the rich text editor."""
    if request.method == 'POST' and request.FILES.get('image'):
        from .models import UploadedImage
        img = UploadedImage(image=request.FILES['image'], uploaded_by=request.user)
        img.save()
        return JsonResponse({'url': img.image.url})
    return JsonResponse({'error': 'No image provided'}, status=400)
```

Add URL in `backend/urls.py`:
```python
path('upload/image/', view=UploadImage, name='upload.image'),
```

---

### 4.2 — Report Detail View (3-column layout)

```python
@login_required
def ReportDetail(request, id):
    report = get_object_or_404(Report, pk=id)

    # Permission check: SuperAdmin sees all; Reporter sees own/collaborated; ProjectOwner sees by program
    # (implement using has_permission + object-level check)

    comments = report.comments.select_related('author').all()
    programs = Program.objects.all()

    if request.method == 'POST':
        # Handle comment submission
        body = request.POST.get('body', '').strip()
        if body:
            ReportComment.objects.create(report=report, author=request.user, body=body)
            messages.success(request, 'Comment added.')
        return redirect('report-detail', id=id)

    return render(request, 'reports/report-detail.html', {
        'report': report,
        'comments': comments,
        'programs': programs,
    })
```

Add URL:
```python
path('reports/<int:id>/', view=ReportDetail, name='report-detail'),
```

---

### 4.3 — User Management Views

Create a new file `backend/views_users.py` (keep views.py clean):

**Views to implement:**

| View Function        | URL Pattern                        | Permission Required   |
|----------------------|------------------------------------|-----------------------|
| `UserListView`       | `users/`                           | `users.read`          |
| `UserCreateView`     | `users/create/`                    | `users.create`        |
| `UserEditView`       | `users/edit/<int:id>/`             | `users.update`        |
| `UserDeleteView`     | `users/delete/<int:id>/`           | `users.delete`        |
| `InviteUserView`     | `users/invite/`                    | `users.create`        |
| `AcceptInviteView`   | `invite/accept/<uuid:token>/`      | *(public)*            |

**`InviteUserView` logic:**
1. Validate email is not already registered.
2. Create `Invitation` with expiry = `now + INVITATION_EXPIRY_DAYS`.
3. Send email with link: `<base_url>/invite/accept/<token>/`.

**`AcceptInviteView` logic:**
1. Look up `Invitation` by token.
2. Check status == 'Pending' and `expires_at > now`.
3. If user with that email exists → assign role, redirect login.
4. If new user → show registration form, create `User` + `UserProfile`, mark invitation Accepted.

---

### 4.4 — Role & Permission Management Views

Create `backend/views_rbac.py`:

| View Function          | URL Pattern                         | Permission Required       |
|------------------------|-------------------------------------|---------------------------|
| `MenuListView`         | `manage/menus/`                     | `manage_menus.read`       |
| `MenuCreateView`       | `manage/menus/create/`              | `manage_menus.create`     |
| `MenuEditView`         | `manage/menus/edit/<int:id>/`       | `manage_menus.update`     |
| `MenuDeleteView`       | `manage/menus/delete/<int:id>/`     | `manage_menus.delete`     |
| `RoleListView`         | `manage/roles/`                     | `manage_roles.read`       |
| `RoleCreateView`       | `manage/roles/create/`              | `manage_roles.create`     |
| `RoleEditView`         | `manage/roles/edit/<int:id>/`       | `manage_roles.update`     |
| `RoleDeleteView`       | `manage/roles/delete/<int:id>/`     | `manage_roles.delete`     |
| `PermissionListView`   | `manage/permissions/`               | `manage_permissions.read` |

**`RoleEditView`** renders a matrix of checkboxes: rows = Menus, columns = CREATE/READ/UPDATE/DELETE. On POST, replaces the role's permissions with the checked set.

---

### 4.5 — Program Follow/Unfollow

```python
@login_required
def ProgramFollow(request, id):
    program = get_object_or_404(Program, pk=id)
    obj, created = ProgramFollower.objects.get_or_create(program=program, user=request.user)
    if not created:
        obj.delete()
        return JsonResponse({'status': 'unfollowed'})
    return JsonResponse({'status': 'followed'})
```

URL: `path('programs/<int:id>/follow/', view=ProgramFollow, name='program-follow')`

---

### 4.6 — Comment Edit & Delete

```python
@login_required
def CommentEdit(request, id):
    comment = get_object_or_404(ReportComment, pk=id, author=request.user)
    if request.method == 'POST':
        comment.body = request.POST.get('body', comment.body)
        comment.save()
        return JsonResponse({'status': 'updated', 'body': comment.body})
    return JsonResponse({'error': 'Invalid'}, status=400)

@login_required
def CommentDelete(request, id):
    comment = get_object_or_404(ReportComment, pk=id, author=request.user)
    if request.method == 'POST':
        comment.delete()
        return JsonResponse({'status': 'deleted'})
    return JsonResponse({'error': 'Invalid'}, status=400)
```

URLs:
```python
path('comments/edit/<int:id>/',   view=CommentEdit,   name='comment-edit'),
path('comments/delete/<int:id>/', view=CommentDelete, name='comment-delete'),
```

---

## Phase 5 — Templates

### 5.1 — Rich Text Editor Setup (Quill.js)

Use **Quill.js** (CDN, no install needed). Add to `base.html` before `</body>`:

```html
<!-- Quill.js -->
<link href="https://cdn.quilljs.com/1.3.7/quill.snow.css" rel="stylesheet">
<script src="https://cdn.quilljs.com/1.3.7/quill.min.js"></script>
```

**Reusable editor macro** — create `templates/misc/rich_editor.html`:

```html
<!-- Usage: {% include "misc/rich_editor.html" with field_name="description" label="Description" value=report.description %} -->
<div class="mb-3">
    <label class="form-label">{{ label }}</label>
    <div id="editor-{{ field_name }}" style="height: 200px;">{{ value|safe }}</div>
    <input type="hidden" name="{{ field_name }}" id="input-{{ field_name }}">
</div>
<script>
(function() {
    const quill = new Quill('#editor-{{ field_name }}', {
        theme: 'snow',
        modules: {
            toolbar: [
                ['bold', 'italic', 'underline', 'strike'],
                ['blockquote', 'code-block'],
                [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                ['link', 'image'],
                ['clean']
            ]
        }
    });

    // Image paste support
    quill.getModule('toolbar').addHandler('image', () => {
        const input = document.createElement('input');
        input.setAttribute('type', 'file');
        input.setAttribute('accept', 'image/*');
        input.click();
        input.onchange = () => uploadImage(input.files[0], quill);
    });

    quill.root.addEventListener('paste', (e) => {
        const items = (e.clipboardData || e.originalEvent.clipboardData).items;
        for (const item of items) {
            if (item.type.startsWith('image/')) {
                e.preventDefault();
                uploadImage(item.getAsFile(), quill);
            }
        }
    });

    function uploadImage(file, editor) {
        const formData = new FormData();
        formData.append('image', file);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        fetch('/upload/image/', { method: 'POST', body: formData })
            .then(r => r.json())
            .then(data => {
                if (data.url) {
                    const range = editor.getSelection(true);
                    editor.insertEmbed(range.index, 'image', data.url);
                }
            });
    }

    // Sync hidden input before form submit
    const form = document.getElementById('editor-{{ field_name }}').closest('form');
    if (form) {
        form.addEventListener('submit', () => {
            document.getElementById('input-{{ field_name }}').value = quill.root.innerHTML;
        });
    }
})();
</script>
```

---

### 5.2 — Updated Report Create Modal (`templates/reports/report-add.html`)

Add the 3 Quill editors after the existing fields:

```html
{% include "misc/rich_editor.html" with field_name="description" label="Description" value="" %}
{% include "misc/rich_editor.html" with field_name="impact"      label="Impact"      value="" %}
{% include "misc/rich_editor.html" with field_name="remediation" label="Remediation / Fix" value="" %}
```

---

### 5.3 — Report Detail Template (`templates/reports/report-detail.html`)

**3-column layout using AdminLTE/Bootstrap grid:**

```
┌──────────────────────────────────────────────────────────┐
│  Left Sidebar (col-2)  │  Main Content (col-7)  │  Right Sidebar (col-3) │
│                        │                        │                         │
│  Report Navigation     │  Title + Metadata bar  │  Reporter               │
│  ─ Description         │  Description (HTML)    │  Coordinator            │
│  ─ Impact              │  Impact (HTML)         │  Developer              │
│  ─ Remediation         │  Remediation (HTML)    │  Collaborators          │
│  ─ Comments            │  ── Comments ──        │  Program                │
│                        │  Comment input         │  Platform               │
│                        │                        │  Severity badge         │
│                        │                        │  Status badge           │
│                        │                        │  Reward                 │
│                        │                        │  Follow/Unfollow btn    │
└──────────────────────────────────────────────────────────┘
```

**Key template blocks:**

```html
{% extends "base.html" %}
{% block content %}
<div class="col-12">
  <div class="row">

    <!-- LEFT SIDEBAR: section navigation -->
    <div class="col-md-2">
      <div class="card sticky-top" style="top: 70px;">
        <div class="card-body p-2">
          <nav class="nav flex-column nav-pills">
            <a class="nav-link" href="#description">Description</a>
            <a class="nav-link" href="#impact">Impact</a>
            <a class="nav-link" href="#remediation">Remediation</a>
            <a class="nav-link" href="#comments">Comments</a>
          </nav>
        </div>
      </div>
    </div>

    <!-- MAIN CONTENT -->
    <div class="col-md-7">
      <!-- Report title + badges bar -->
      <div class="card">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h4>{{ report.title }}</h4>
          <div>
            <span class="badge badge-...">{{ report.severity }}</span>
            <span class="badge badge-...">{{ report.status }}</span>
          </div>
        </div>
      </div>

      <!-- Description section -->
      <div class="card" id="description">
        <div class="card-header"><h5>Description</h5></div>
        <div class="card-body">{{ report.description|safe }}</div>
      </div>

      <!-- Impact section -->
      <div class="card" id="impact">
        <div class="card-header"><h5>Impact</h5></div>
        <div class="card-body">{{ report.impact|safe }}</div>
      </div>

      <!-- Remediation section -->
      <div class="card" id="remediation">
        <div class="card-header"><h5>Remediation / Fix</h5></div>
        <div class="card-body">{{ report.remediation|safe }}</div>
      </div>

      <!-- Comments section -->
      <div class="card" id="comments">
        <div class="card-header"><h5>Comments ({{ comments.count }})</h5></div>
        <div class="card-body">
          {% for comment in comments %}
            <!-- Comment card with avatar, author, timestamp, edit/delete (own only) -->
          {% endfor %}

          <!-- New comment form (Quill editor) -->
          {% if can_comment %}
            <form method="POST">
              {% csrf_token %}
              {% include "misc/rich_editor.html" with field_name="body" label="Add Comment" value="" %}
              <button class="btn btn-primary btn-sm">Post Comment</button>
            </form>
          {% endif %}
        </div>
      </div>
    </div>

    <!-- RIGHT SIDEBAR: metadata + participants -->
    <div class="col-md-3">
      <!-- Participants card -->
      <div class="card">
        <div class="card-header"><h6>Participants</h6></div>
        <div class="card-body p-2">
          <p><strong>Reporter:</strong> {{ report.reporter.username|default:"—" }}</p>
          <p><strong>Coordinator:</strong> {{ report.coordinator.username|default:"—" }}</p>
          <p><strong>Developer:</strong> {{ report.developer.username|default:"—" }}</p>
          {% if report.collaborators.exists %}
            <p><strong>Collaborators:</strong></p>
            {% for user in report.collaborators.all %}
              <span class="badge badge-secondary">{{ user.username }}</span>
            {% endfor %}
          {% endif %}
        </div>
      </div>

      <!-- Report metadata card -->
      <div class="card mt-2">
        <div class="card-header"><h6>Details</h6></div>
        <div class="card-body p-2">
          <p><strong>Program:</strong> {{ report.program.name }}</p>
          <p><strong>Platform:</strong> {{ report.program.platform.name }}</p>
          <p><strong>Reward:</strong> {{ report.reward }}</p>
          <p><strong>Submitted:</strong> {{ report.created_at|date:"d M Y" }}</p>
          <p><strong>Updated:</strong> {{ report.updated_at|date:"d M Y" }}</p>
        </div>
      </div>

      <!-- Follow button (for programs) -->
      <button class="btn btn-outline-primary btn-block mt-2" id="followBtn"
              data-url="{% url 'program-follow' report.program.id %}">
        {% if is_following %}Unfollow{% else %}Follow{% endif %} Program
      </button>
    </div>

  </div>
</div>
{% endblock %}
```

---

### 5.4 — Dynamic Sidebar (`templates/misc/sidebar.html`)

Replace the static sidebar with a dynamic one driven by `sidebar_menus` from the context processor:

```html
<ul class="nav nav-pills nav-sidebar flex-column" data-widget="treeview" role="menu">
  {% for menu in sidebar_menus %}
    {% if menu.menu_set.exists %}
      <!-- Parent with children -->
      <li class="nav-item has-treeview">
        <a href="#" class="nav-link">
          <i class="nav-icon {{ menu.icon }}"></i>
          <p>{{ menu.name }} <i class="right fas fa-angle-left"></i></p>
        </a>
        <ul class="nav nav-treeview">
          {% for child in menu.menu_set.all %}
            <li class="nav-item">
              <a href="{% url child.url_name %}" class="nav-link {% if request.resolver_match.url_name == child.url_name %}active{% endif %}">
                <i class="far fa-circle nav-icon"></i>
                <p>{{ child.name }}</p>
              </a>
            </li>
          {% endfor %}
        </ul>
      </li>
    {% else %}
      <!-- Leaf menu -->
      <li class="nav-item">
        <a href="{% url menu.url_name %}" class="nav-link {% if request.resolver_match.url_name == menu.url_name %}active{% endif %}">
          <i class="nav-icon {{ menu.icon }}"></i>
          <p>{{ menu.name }}</p>
        </a>
      </li>
    {% endif %}
  {% endfor %}
</ul>
```

---

### 5.5 — User Management Templates

Create the following templates under `templates/users/`:

- `users.html` — paginated user table (name, email, role, status, actions)
- `user-invite.html` — modal with email + role selector
- `invite-accept.html` — public page: "You've been invited. Set your password."

### 5.6 — RBAC Management Templates

Create under `templates/manage/`:

- `menus.html` — table of menus with parent/child display, add/edit/delete
- `roles.html` — table of roles with permission count badge
- `role-permissions.html` — permission matrix (Menu rows × Action columns = checkboxes)

---

## Phase 6 — Report List View & Permission Enforcement

### 6.1 — Update `ReportView` in `views.py`

Apply object-level filtering based on role:

```python
@login_required
def ReportView(request):
    user = request.user
    if user.is_superuser or (hasattr(user, 'profile') and user.profile.role and user.profile.role.name == 'SuperAdmin'):
        reports = Report.objects.all()
    elif hasattr(user, 'profile') and user.profile.role and user.profile.role.name == 'Reporter':
        reports = Report.objects.filter(
            Q(reporter=user) | Q(collaborators=user)
        ).distinct()
    elif hasattr(user, 'profile') and user.profile.role and user.profile.role.name == 'ProjectOwner':
        followed_programs = user.followed_programs.values_list('program_id', flat=True)
        reports = Report.objects.filter(program_id__in=followed_programs)
    else:
        reports = Report.objects.none()

    # ... rest of filtering & pagination unchanged
```

### 6.2 — Apply `@permission_required` to all existing views

Replace `@login_required` with `@permission_required('resource.action')` on each view. Examples:

```python
@permission_required('reports.read')
def ReportView(request): ...

@permission_required('reports.create')
def ReportCreate(request): ...

@permission_required('reports.update')
def ReportEdit(request, id): ...

@permission_required('reports.delete')
def ReportDelete(request, id): ...

@permission_required('programs.read')
def ProgramView(request): ...
# etc.
```

The `permission_required` decorator already handles redirect for unauthenticated users.

---

## Phase 7 — Static JS (`static/js/custom.js`)

Ensure `custom.js` includes:

1. `handleAction(url)` — existing SweetAlert confirm-then-DELETE-request (keep)
2. `resetForm()` — clears the report filter form (keep)
3. Follow/Unfollow button AJAX toggle
4. Comment inline edit (click Edit → replace `<p>` with `<textarea>` → PATCH → restore)
5. Comment delete (SweetAlert confirm → POST to delete endpoint → remove DOM node)

---

## Summary: File Change Manifest

| File | Action |
|------|--------|
| `backend/models.py` | Add Menu, Permission, Role, UserProfile, Invitation, ProgramFollower, ReportComment, UploadedImage; update Report |
| `backend/views.py` | Add UploadImage, ReportDetail, ProgramFollow, CommentEdit, CommentDelete; update ReportView |
| `backend/views_users.py` | New — UserList/Create/Edit/Delete, InviteUser, AcceptInvite |
| `backend/views_rbac.py` | New — MenuList/Create/Edit/Delete, RoleList/Create/Edit/Delete, PermissionList |
| `backend/urls.py` | Add all new URL patterns |
| `backend/rbac.py` | New — get_user_permissions, has_permission, get_user_menus |
| `backend/decorators.py` | New — permission_required decorator |
| `backend/context_processors.py` | New — rbac_context |
| `backend/resources.py` | No change needed |
| `backend/management/commands/seed_rbac.py` | New — seeds Menus, Permissions, Roles |
| `core/settings.py` | Add MEDIA_URL/ROOT, email config, context_processors entry |
| `core/urls.py` | Add static(MEDIA_URL) |
| `templates/base.html` | Add Quill.js CDN links |
| `templates/misc/sidebar.html` | Replace with dynamic version |
| `templates/misc/rich_editor.html` | New — reusable Quill editor include |
| `templates/reports/report-add.html` | Add 3 rich editors |
| `templates/reports/report-detail.html` | New — 3-column detail view |
| `templates/users/` | New directory — users.html, user-invite.html, invite-accept.html |
| `templates/manage/` | New directory — menus.html, roles.html, role-permissions.html |
| `static/js/custom.js` | Add follow toggle, comment edit/delete AJAX |
| `.env.example` | Add email vars |

---

## Implementation Order Checklist

- [ ] **Phase 1** — Models + migrations + seed command
- [ ] **Phase 2** — Settings (MEDIA, email, context_processors)
- [ ] **Phase 3** — rbac.py + decorators.py + context_processors.py
- [ ] **Phase 4** — New views (image upload, report detail, users, RBAC mgmt)
- [ ] **Phase 5** — All new/updated templates
- [ ] **Phase 6** — Permission enforcement on all existing views
- [ ] **Phase 7** — custom.js AJAX updates
- [ ] **Final** — Run `seed_rbac`, smoke test all 3 roles

---

*End of CLAUDE.md*
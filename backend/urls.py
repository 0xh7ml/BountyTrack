from django.contrib import admin
from django.urls import path
from .views import *
from .views_users import (
    UserListView, UserCreateView, UserEditView, UserDeleteView,
    InviteUserView, AcceptInviteView,
)
from .views_rbac import (
    MenuListView, MenuCreateView, MenuEditView, MenuDeleteView,
    RoleListView, RoleCreateView, RoleEditView, RoleDeleteView,
    PermissionListView,
)

urlpatterns = [
    path('', view=CustomLoginView, name='login'),
    path('dashboard/', view=home, name='home'),
    path('logout/', view=CustomLogoutView, name='logout'),

    # Reports
    path('reports/', view=ReportView, name='reports'),
    path('reports/create/', view=ReportCreate, name='report-create'),
    path('reports/<int:id>/', view=ReportDetail, name='report-detail'),
    path('reports/edit/<int:id>/', view=ReportEdit, name='report-edit'),
    path('reports/delete/<int:id>/', view=ReportDelete, name='report-delete'),
    path('reports/<int:id>/pdf/', view=ReportExportPDF, name='report-pdf'),

    # Programs
    path('programs/', view=ProgramView, name='programs'),
    path('programs/create/', view=ProgramCreate, name='program-create'),
    path('programs/edit/<int:id>/', view=ProgramEdit, name='program-edit'),
    path('programs/delete/<int:id>/', view=ProgramDelete, name='program-delete'),
    path('programs/<int:id>/follow/', view=ProgramFollow, name='program-follow'),

    # Platforms
    path('platforms/', view=PlatformView, name='platforms'),
    path('platforms/create/', view=PlatformCreate, name='platform-create'),
    path('platforms/edit/<int:id>/', view=PlatformEdit, name='platform-edit'),
    path('platforms/delete/<int:id>/', view=PlatformDelete, name='platform-delete'),

    # Analytics
    path('analytics/program', view=ProgramWiseAnalytics, name='analytics.program'),

    # Import/Export
    path('import/program/', view=ImportProgram, name='import.program'),
    path('import/report/', view=ImportReport, name='import.report'),

    # Image Upload
    path('upload/image/', view=UploadImage, name='upload.image'),

    # Comments
    path('comments/edit/<int:id>/',   view=CommentEdit,   name='comment-edit'),
    path('comments/delete/<int:id>/', view=CommentDelete, name='comment-delete'),

    # User Management
    path('users/',                       view=UserListView,    name='users'),
    path('users/create/',                view=UserCreateView,  name='user-create'),
    path('users/edit/<int:id>/',         view=UserEditView,    name='user-edit'),
    path('users/delete/<int:id>/',       view=UserDeleteView,  name='user-delete'),
    path('users/invite/',                view=InviteUserView,  name='user-invite'),
    path('invite/accept/<uuid:token>/',  view=AcceptInviteView, name='invite-accept'),

    # RBAC Management
    path('manage/menus/',                     view=MenuListView,       name='manage_menus'),
    path('manage/menus/create/',              view=MenuCreateView,     name='manage_menus.create'),
    path('manage/menus/edit/<int:id>/',       view=MenuEditView,       name='manage_menus.edit'),
    path('manage/menus/delete/<int:id>/',     view=MenuDeleteView,     name='manage_menus.delete'),
    path('manage/roles/',                     view=RoleListView,       name='manage_roles'),
    path('manage/roles/create/',              view=RoleCreateView,     name='manage_roles.create'),
    path('manage/roles/edit/<int:id>/',       view=RoleEditView,       name='manage_roles.edit'),
    path('manage/roles/delete/<int:id>/',     view=RoleDeleteView,     name='manage_roles.delete'),
    path('manage/permissions/',               view=PermissionListView, name='manage_permissions'),
]

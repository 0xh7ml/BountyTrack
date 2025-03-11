from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('', view=CustomLoginView, name='login'),
    path('dashboard/', view=home, name='home'),
    path('logout/', view=CustomLogoutView, name='logout'),

    # Reports
    path('reports/', view=ReportView, name='reports'),
    path('reports/create/', view=ReportCreate, name='report-create'),
    path('reports/edit/<int:id>/', view=ReportEdit, name='report-edit'),
    path('reports/delete/<int:id>/', view=ReportDelete, name='report-delete'),

    path('programs/', view=ProgramView, name='programs'),
    path('programs/create/', view=ProgramCreate, name='program-create'),
    path('programs/edit/<int:id>/', view=ProgramEdit, name='program-edit'),
    path('programs/delete/<int:id>/', view=ProgramDelete, name='program-delete'),

    path('platforms/', view=PlatformView, name='platforms'),
    path('platforms/create/', view=PlatformCreate, name='platform-create'),
    path('platforms/edit/<int:id>/', view=PlatformEdit, name='platform-edit'),
    path('platforms/delete/<int:id>/', view=PlatformDelete, name='platform-delete'),
]

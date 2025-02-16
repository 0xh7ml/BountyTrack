from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('', view=home, name='home'),
    path('reports/', view=reports, name='reports'),
]

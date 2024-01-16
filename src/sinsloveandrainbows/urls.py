"""
URL configuration for sinsloveandrainbows project.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from api.api import api
from slrportal.views import custom_404

handler404 = custom_404

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("slrportal.urls")),
    path("api/", api.urls),
]

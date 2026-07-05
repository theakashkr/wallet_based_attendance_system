"""
URL configuration for wallet_attendance project.
Routes all attendance-related URLs to the attendance app.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("attendance.urls")),
]

"""
URL patterns for the attendance app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # Attendance actions (AJAX)
    path("check-in/", views.check_in, name="check_in"),
    path("check-out/", views.check_out, name="check_out"),
    path("recharge/", views.recharge, name="recharge"),

    # QR Code (Admin-only)
    path("qr-display/", views.qr_display, name="qr_display"),
    path("qr-image/", views.qr_image, name="qr_image"),

    # Authentication
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
]

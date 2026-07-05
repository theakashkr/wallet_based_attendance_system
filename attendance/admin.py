"""
Admin registration for the attendance app models.
"""

from django.contrib import admin
from .models import UserProfile, Attendance, Transaction


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "wallet_balance")
    search_fields = ("user__username", "user__email")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("user", "entry_time", "exit_time", "duration_minutes", "credits_deducted")
    list_filter = ("user", "entry_time")
    search_fields = ("user__username",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "timestamp", "description")
    list_filter = ("user", "timestamp")
    search_fields = ("user__username", "description")

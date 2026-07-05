"""
Models for the Wallet-Based Attendance & Access Control System.

Three models:
  - UserProfile: Extends Django User with a wallet_balance field.
  - Attendance:  Tracks check-in / check-out times and credit deductions.
  - Transaction: Logs wallet recharge events.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


# ---------------------------------------------------------------------------
# UserProfile — wallet extension for the built-in User model
# ---------------------------------------------------------------------------

class UserProfile(models.Model):
    """
    One-to-one extension of Django's User model.
    Stores the virtual wallet balance used for attendance access control.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    wallet_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("100.00"),
        help_text="Current wallet balance in credits.",
    )

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username} — ₹{self.wallet_balance}"


# Auto-create a UserProfile whenever a new User is saved
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile for every newly registered User."""
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Ensure the profile is saved when the user is updated
        if hasattr(instance, "profile"):
            instance.profile.save()


# ---------------------------------------------------------------------------
# Attendance — tracks entry/exit and credit deductions
# ---------------------------------------------------------------------------

class Attendance(models.Model):
    """
    Each record represents one office visit.
    - entry_time is set on check-in.
    - exit_time, duration_minutes, and credits_deducted are populated on check-out.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendances",
    )
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(
        default=0,
        help_text="Total stay duration in minutes.",
    )
    credits_deducted = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Credits deducted for this visit (0.1 per minute).",
    )

    class Meta:
        ordering = ["-entry_time"]
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"

    def __str__(self):
        status = "Inside" if self.exit_time is None else "Checked Out"
        return f"{self.user.username} | {self.entry_time:%Y-%m-%d %H:%M} | {status}"

    @property
    def is_active(self):
        """True if the user is currently inside (hasn't checked out yet)."""
        return self.exit_time is None


# ---------------------------------------------------------------------------
# Transaction — wallet recharge log
# ---------------------------------------------------------------------------

class Transaction(models.Model):
    """
    Immutable log of every wallet top-up / recharge event.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Credits added to the wallet.",
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(
        max_length=255,
        default="Wallet Recharge",
    )

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

    def __str__(self):
        return f"{self.user.username} | +{self.amount} | {self.timestamp:%Y-%m-%d %H:%M}"

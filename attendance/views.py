"""
Views for the Wallet-Based Attendance & Access Control System.

Endpoints:
  GET  /                → Dashboard (renders HTML)
  POST /check-in/       → AJAX check-in  (returns JSON) — requires QR token
  POST /check-out/      → AJAX check-out (returns JSON) — requires QR token
  POST /recharge/       → AJAX recharge  (returns JSON)
  GET  /qr-display/     → Admin-only QR code display page
  GET  /qr-image/       → QR code PNG image (rotates every 30s)
  GET  /login/          → Login page
  POST /login/          → Authenticate user
  GET  /register/       → Registration page
  POST /register/       → Create new user
  POST /logout/         → Log out
"""

import json
from decimal import Decimal

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import RegisterForm, RechargeForm
from .models import Attendance, Transaction
from .qr_utils import generate_qr_token, validate_qr_token, generate_qr_image_bytes


# ───────────────────────────────────────────────────────────────────────────
# Constants
# ───────────────────────────────────────────────────────────────────────────

CREDIT_RATE_PER_MINUTE = Decimal("0.10")  # 10 paisa per minute


# ───────────────────────────────────────────────────────────────────────────
# Dashboard
# ───────────────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    """
    Main dashboard view.
    Shows wallet balance, current status, attendance history, and transactions.
    """
    user = request.user
    profile = user.profile

    # Check if the user is currently inside (has an open attendance record)
    active_record = Attendance.objects.filter(user=user, exit_time__isnull=True).first()
    is_inside = active_record is not None

    # Fetch attendance history (last 50 records)
    attendance_history = Attendance.objects.filter(user=user)[:50]

    # Fetch recent transactions
    transactions = Transaction.objects.filter(user=user)[:20]

    context = {
        "profile": profile,
        "is_inside": is_inside,
        "active_record": active_record,
        "attendance_history": attendance_history,
        "transactions": transactions,
    }
    return render(request, "attendance/dashboard.html", context)


# ───────────────────────────────────────────────────────────────────────────
# Check-In (AJAX) — QR Token Required
# ───────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def check_in(request):
    """
    Check-in endpoint.
    1. Validate the QR token.
    2. Verify the user isn't already inside.
    3. Check wallet_balance > 0.
    4. Create a new Attendance record.
    """
    # Parse QR token from request body
    try:
        body = json.loads(request.body)
        qr_token = body.get("qr_token", "")
    except (json.JSONDecodeError, TypeError):
        qr_token = ""

    # Validate QR token
    if not validate_qr_token(qr_token):
        return JsonResponse(
            {"success": False, "message": "Invalid or expired QR code. Please scan the latest code."},
            status=403,
        )

    user = request.user
    profile = user.profile

    # Prevent double check-in
    if Attendance.objects.filter(user=user, exit_time__isnull=True).exists():
        return JsonResponse(
            {"success": False, "message": "You are already checked in."},
            status=400,
        )

    # Check wallet balance
    if profile.wallet_balance <= 0:
        return JsonResponse(
            {
                "success": False,
                "message": "Access Denied: Insufficient Credits. Please recharge.",
            },
            status=403,
        )

    # Create attendance record
    record = Attendance.objects.create(user=user)

    return JsonResponse({
        "success": True,
        "message": "Checked in successfully!",
        "entry_time": record.entry_time.strftime("%Y-%m-%d %H:%M:%S"),
        "wallet_balance": str(profile.wallet_balance),
    })


# ───────────────────────────────────────────────────────────────────────────
# Check-Out (AJAX) — QR Token Required
# ───────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def check_out(request):
    """
    Check-out endpoint.
    1. Validate the QR token.
    2. Find the active attendance record.
    3. Calculate duration and credit deduction (0.1 credits/minute).
    4. Update the attendance record and subtract from the wallet.
    """
    # Parse QR token from request body
    try:
        body = json.loads(request.body)
        qr_token = body.get("qr_token", "")
    except (json.JSONDecodeError, TypeError):
        qr_token = ""

    # Validate QR token
    if not validate_qr_token(qr_token):
        return JsonResponse(
            {"success": False, "message": "Invalid or expired QR code. Please scan the latest code."},
            status=403,
        )

    user = request.user
    profile = user.profile

    # Find the open attendance record
    record = Attendance.objects.filter(user=user, exit_time__isnull=True).first()
    if record is None:
        return JsonResponse(
            {"success": False, "message": "You are not currently checked in."},
            status=400,
        )

    # Record exit time and calculate duration
    now = timezone.now()
    record.exit_time = now

    delta = now - record.entry_time
    duration_minutes = int(delta.total_seconds() / 60)
    # Minimum 1 minute charge if they were inside at all
    if duration_minutes < 1:
        duration_minutes = 1

    record.duration_minutes = duration_minutes

    # Calculate credits to deduct: 0.1 credits per minute
    credits_to_deduct = Decimal(str(duration_minutes)) * CREDIT_RATE_PER_MINUTE
    record.credits_deducted = credits_to_deduct
    record.save()

    # Deduct from wallet
    profile.wallet_balance -= credits_to_deduct
    # Allow balance to go negative on check-out (they were already inside)
    profile.save()

    return JsonResponse({
        "success": True,
        "message": "Checked out successfully!",
        "exit_time": record.exit_time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_minutes": duration_minutes,
        "credits_deducted": str(credits_to_deduct),
        "wallet_balance": str(profile.wallet_balance),
    })


# ───────────────────────────────────────────────────────────────────────────
# Recharge (AJAX)
# ───────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def recharge(request):
    """
    Wallet recharge endpoint.
    Accepts a JSON body with {"amount": <number>} and adds it to the wallet.
    """
    try:
        body = json.loads(request.body)
        amount = Decimal(str(body.get("amount", 0)))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse(
            {"success": False, "message": "Invalid request data."},
            status=400,
        )

    if amount <= 0:
        return JsonResponse(
            {"success": False, "message": "Amount must be greater than zero."},
            status=400,
        )

    profile = request.user.profile

    # Add credits to wallet
    profile.wallet_balance += amount
    profile.save()

    # Log the transaction
    Transaction.objects.create(
        user=request.user,
        amount=amount,
        description=f"Wallet Recharge — +{amount} credits",
    )

    return JsonResponse({
        "success": True,
        "message": f"Successfully recharged {amount} credits!",
        "wallet_balance": str(profile.wallet_balance),
    })


# ───────────────────────────────────────────────────────────────────────────
# QR Code Display & Image (Admin-Only)
# ───────────────────────────────────────────────────────────────────────────

@staff_member_required
def qr_display(request):
    """
    Admin-only page that displays the current QR code.
    Designed to be shown on a monitor at the office entrance.
    Auto-refreshes every 30 seconds via JavaScript.
    """
    return render(request, "attendance/qr_display.html")


@staff_member_required
def qr_image(request):
    """
    Returns the current QR code as a PNG image.
    The QR code encodes the current HMAC token (rotates every 30s).
    """
    token = generate_qr_token()
    image_bytes = generate_qr_image_bytes(token)

    response = HttpResponse(image_bytes, content_type="image/png")
    # Prevent caching so the browser always fetches the latest QR
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    return response


# ───────────────────────────────────────────────────────────────────────────
# Authentication Views
# ───────────────────────────────────────────────────────────────────────────

def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            error = "Invalid username or password."

    return render(request, "attendance/login.html", {"error": error})


def register_view(request):
    """Handle new user registration."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegisterForm()

    return render(request, "attendance/register.html", {"form": form})


@require_POST
def logout_view(request):
    """Log the user out and redirect to login."""
    logout(request)
    return redirect("login")

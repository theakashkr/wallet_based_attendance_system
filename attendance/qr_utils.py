"""
QR Code Utilities for Attendance Verification.

Uses HMAC-based time-rotating tokens (30-second windows).
No database model needed — fully stateless.

Token = HMAC-SHA256(SECRET_KEY, floor(timestamp / WINDOW_SECONDS))
Validation accepts the current window and the previous window
to handle scans at the boundary.
"""

import hashlib
import hmac
import io
import time

import qrcode
from django.conf import settings


# ───────────────────────────────────────────────────────────────────────────
# Configuration
# ───────────────────────────────────────────────────────────────────────────

WINDOW_SECONDS = 30  # Token rotates every 30 seconds


# ───────────────────────────────────────────────────────────────────────────
# Token Generation
# ───────────────────────────────────────────────────────────────────────────

def _get_time_window(offset=0):
    """
    Return the current (or offset) time window index.
    offset=0  → current window
    offset=-1 → previous window
    """
    return int(time.time() // WINDOW_SECONDS) + offset


def _make_hmac(window_index):
    """Generate an HMAC-SHA256 hex digest for a given time window index."""
    key = settings.SECRET_KEY.encode("utf-8")
    message = str(window_index).encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def generate_qr_token():
    """
    Generate the QR token for the current time window.
    Returns a 64-character hex string.
    """
    return _make_hmac(_get_time_window(0))


def validate_qr_token(token):
    """
    Validate a QR token against the current and previous time window.
    Returns True if the token matches either window (handles boundary scans).
    """
    if not token or not isinstance(token, str):
        return False

    current_token = _make_hmac(_get_time_window(0))
    previous_token = _make_hmac(_get_time_window(-1))

    return hmac.compare_digest(token, current_token) or \
           hmac.compare_digest(token, previous_token)


# ───────────────────────────────────────────────────────────────────────────
# QR Image Generation
# ───────────────────────────────────────────────────────────────────────────

def generate_qr_image_bytes(data):
    """
    Generate a QR code PNG image from the given data string.
    Returns raw PNG bytes.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1e293b", back_color="#ffffff")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

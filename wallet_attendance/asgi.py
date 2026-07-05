"""
ASGI config for wallet_attendance project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wallet_attendance.settings")
application = get_asgi_application()

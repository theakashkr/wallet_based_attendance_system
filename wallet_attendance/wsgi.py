"""
WSGI config for wallet_attendance project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wallet_attendance.settings")
application = get_wsgi_application()

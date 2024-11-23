"""
WSGI config for speech_to_text_api project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'speech_to_text_api.settings')

application = get_wsgi_application()

"""
WSGI config for speech_to_text_api project.
"""

import os
from dotenv import load_dotenv

# Load environment variables before application starts
load_dotenv()

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'speech_to_text_api.settings')

application = get_wsgi_application()

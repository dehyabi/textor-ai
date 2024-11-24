import os
import sys

# Add your project directory to the sys.path
path = '/home/your_username/textor-ai'
if path not in sys.path:
    sys.path.append(path)

# Load environment variables from .env file
from dotenv import load_dotenv
project_folder = os.path.expanduser(path)
load_dotenv(os.path.join(project_folder, '.env'))

# Set environment variable for Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'speech_to_text_api.settings'

# Create application for WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

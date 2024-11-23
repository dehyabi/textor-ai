from django.contrib.auth.models import User
from django.core.management import BaseCommand

DJANGO_SUPERUSER_USERNAME = "admin"
DJANGO_SUPERUSER_EMAIL = "admin@example.com"
DJANGO_SUPERUSER_PASSWORD = "admin123!"

try:
    superuser = User.objects.create_superuser(
        username=DJANGO_SUPERUSER_USERNAME,
        email=DJANGO_SUPERUSER_EMAIL,
        password=DJANGO_SUPERUSER_PASSWORD)
    superuser.save()
    print(f"Superuser {DJANGO_SUPERUSER_USERNAME} created successfully!")
except Exception as e:
    print(e)

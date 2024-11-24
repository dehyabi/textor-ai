release: python manage.py migrate
web: gunicorn speech_to_text_api.wsgi:application --workers 4 --threads 2 --timeout 60 --max-requests 1200 --log-file -

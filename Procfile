release: python manage.py collectstatic --noinput
web: gunicorn backend_cigem.wsgi --log-file - --workers 1 --threads 4 --timeout 180 --max-requests 1000 --max-requests-jitter 100

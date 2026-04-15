#!/bin/sh
set -e

MAX_RETRIES=30
RETRY_DELAY=2

echo "Applying migrations (with retry)..."
attempt=1
while [ "$attempt" -le "$MAX_RETRIES" ]; do
  if python manage.py migrate; then
    break
  fi

  if [ "$attempt" -eq "$MAX_RETRIES" ]; then
    echo "Migration failed after ${MAX_RETRIES} attempts."
    exit 1
  fi

  echo "Database not ready yet (attempt ${attempt}/${MAX_RETRIES}). Retrying in ${RETRY_DELAY}s..."
  attempt=$((attempt + 1))
  sleep "$RETRY_DELAY"
done

echo "Collecting static files..."
python manage.py collectstatic --noinput

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --noinput || true
fi

if [ "$DEBUG" = "True" ] || [ "$DEBUG" = "true" ] || [ "$DEBUG" = "1" ]; then
  exec python manage.py runserver 0.0.0.0:${PORT:-8000}
fi

exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 2 --timeout 120
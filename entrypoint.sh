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
  echo "Ensuring superuser exists..."
  python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ["DJANGO_SUPERUSER_USERNAME"]
email = os.environ["DJANGO_SUPERUSER_EMAIL"]
password = os.environ["DJANGO_SUPERUSER_PASSWORD"]

user, created = User.objects.get_or_create(
  username=username,
  defaults={
    "email": email,
    "is_staff": True,
    "is_superuser": True,
  },
)

if created:
  user.set_password(password)
  user.save(update_fields=["password"])
  print("Superuser created.")
else:
  fields_to_update = []
  if email and user.email != email:
    user.email = email
    fields_to_update.append("email")
  if not user.is_staff:
    user.is_staff = True
    fields_to_update.append("is_staff")
  if not user.is_superuser:
    user.is_superuser = True
    fields_to_update.append("is_superuser")

  if fields_to_update:
    user.save(update_fields=fields_to_update)
    print("Superuser already existed; permissions/profile updated.")
  else:
    print("Superuser already exists; no changes needed.")
PY
fi

if [ "$DEBUG" = "True" ] || [ "$DEBUG" = "true" ] || [ "$DEBUG" = "1" ]; then
  exec python manage.py runserver 0.0.0.0:${PORT:-8000}
fi

exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 2 --timeout 120
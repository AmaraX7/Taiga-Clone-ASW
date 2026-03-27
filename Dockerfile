FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

<<<<<<< HEAD
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:${PORT:-8000}"]
=======
CMD ["sh", "-c", "python manage.py migrate && if [ -n \"$DJANGO_SUPERUSER_USERNAME\" ] && [ -n \"$DJANGO_SUPERUSER_EMAIL\" ] && [ -n \"$DJANGO_SUPERUSER_PASSWORD\" ]; then python manage.py createsuperuser --noinput || true; fi && python manage.py runserver 0.0.0.0:${PORT:-8000}"]
>>>>>>> 2b1a82ea66d2c0074b3bdb81e8a880ec92491645

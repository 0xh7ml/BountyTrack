#!/bin/sh

set -e

# Collect Static Files
python manage.py collectstatic --no-input

python manage.py makemigrations backend

python manage.py migrate

# Create superuser if not exists
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
username = "${DJANGO_SUPERUSER_USERNAME}"
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username,
        email="${DJANGO_SUPERUSER_EMAIL}",
        password="${DJANGO_SUPERUSER_PASSWORD}"
    )
    print("Superuser created.")
else:
    print("Superuser already exists.")
END

exec "$@"
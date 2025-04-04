#!/bin/sh

# Run Django migrations and create superuser if not exists
python manage.py makemigrations
python manage.py migrate

python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='${DJANGO_SUPERUSER_USERNAME}').exists():
    User.objects.create_superuser(username='${DJANGO_SUPERUSER_USERNAME}', email='${DJANGO_SUPERUSER_EMAIL}', password='${DJANGO_SUPERUSER_PASSWORD}');
"

# Start the Django development server
python manage.py runserver 0.0.0.0:8000

#!/bin/sh
echo "==> Applying database migrations..."
python manage.py migrate --noinput

echo "==> Starting development server..."
exec python manage.py runserver 0.0.0.0:8000
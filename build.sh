#!/bin/bash
# build.sh
set -o errexit

echo "Installing dependencies..."
#pip install -r requirements/production.txt
pip install -r requirements.txt

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Building documentation..."
python manage.py generate_swagger -o static/swagger.json

echo "Setting up cron jobs..."
# Add any cron job setup commands here
# For Render, we use Celery Beat instead of cron

echo "Build completed successfully!"

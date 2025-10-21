#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status, treat unset variables as errors, and prevent errors in a pipeline from being hidden.
set -euo pipefail

# Change directory to the application root
cd /home/site/wwwroot

# --- 1. ACTIVATE VIRTUAL ENVIRONMENT (CRITICAL) ---
VENV_PATH="antenv"
if [ -d "$VENV_PATH" ]; then
    echo "Activating virtual environment at $VENV_PATH..."
    source $VENV_PATH/bin/activate
else
    echo "Error: Virtual environment '$VENV_PATH' not found."
    exit 1
fi

# --- DEBUG & ESSENTIAL ENVIRONMENT VARIABLES (Temporary for testing!) ---
# If your Django settings use environment variables for SECRET_KEY or DEBUG,
# setting these here can prevent silent crashes during setup.
# WARNING: Do NOT use a real secret key here in production!
export DJANGO_SECRET_KEY='temporary-insecure-key-for-testing'
export DJANGO_DEBUG='True' # Setting this to True can give better logging

# --- 2. DATABASE SETUP & STATIC FILES ---
echo "Running migrations and collecting static files..."
# The settings path is now CORRECT based on your file structure.
SETTINGS_PATH="myproject.myprojectsettings.settings"

python manage.py migrate --settings=$SETTINGS_PATH || { echo "ERROR: Django migration failed. Check settings: $SETTINGS_PATH"; exit 1; }
python manage.py collectstatic --noinput --settings=$SETTINGS_PATH || { echo "ERROR: Collectstatic failed. Check settings: $SETTINGS_PATH"; exit 1; }

# --- 3. START GUNICORN ---
echo "Starting Gunicorn..."
# WSGI path is now CORRECT based on your file structure.
WSGI_PATH="myproject.myprojectsettings.wsgi:application"

exec gunicorn \
  --chdir /home/site/wwwroot \
  --bind=0.0.0.0:${PORT:-8000} \
  --timeout 600 \
  $WSGI_PATH

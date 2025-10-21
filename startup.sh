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

# --- 2. ESSENTIAL ENVIRONMENT VARIABLES ---
# Path variables are set based on confirmed file structure:
SETTINGS_MODULE="myproject.myprojectsettings.settings"
WSGI_PATH="myproject.myprojectsettings.wsgi:application"

# We can rely on manage.py to set DJANGO_SETTINGS_MODULE now.
# export DJANGO_SETTINGS_MODULE=$SETTINGS_MODULE <-- REMOVED, manage.py handles this.

# Secondary variables (for testing/runtime)
export SECRET_KEY='temporary-insecure-key-for-testing'
export DEBUG='True' 

# IMPORTANT: If using external DB (Postgres/MySQL), ensure credentials 
# are set as environment variables in the Azure Portal!

# --- 3. DATABASE SETUP & STATIC FILES ---
echo "Running migrations and collecting static files..."

# Running commands, relying on manage.py's settings logic
python manage.py migrate --noinput || { echo "ERROR: Django migration failed. Check DB connection/settings."; exit 1; }
python manage.py collectstatic --noinput || { echo "ERROR: Collectstatic failed. Check static configuration."; exit 1; }

# --- 4. START GUNICORN ---
echo "--- Django setup finished. Starting Gunicorn. ---"

# Use exec to replace the shell process with the Gunicorn process
exec gunicorn \
  --chdir /home/site/wwwroot \
  --bind=0.0.0.0:${PORT:-8000} \
  --timeout 600 \
  $WSGI_PATH


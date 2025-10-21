#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status, treat unset variables as errors, and prevent errors in a pipeline from being hidden.
set -euo pipefail

# Change directory to the application root
APP_ROOT="/home/site/wwwroot"
cd $APP_ROOT

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
# CRITICAL: Ensure the application root is in Python's search path.
export PYTHONPATH=$APP_ROOT:$PYTHONPATH

# Path variables used for Gunicorn below
# UPDATED: Assuming the configuration folder has been renamed to 'settings'.
SETTINGS_MODULE="myproject.settings.settings"
WSGI_PATH="myproject.settings.wsgi:application"

# Secondary variables (for testing/runtime)
export SECRET_KEY='temporary-insecure-key-for-testing'
export DEBUG='True' 

# --- 3. DATABASE SETUP & STATIC FILES ---
echo "Running migrations and collecting static files..."

# Running manage.py commands
python manage.py migrate --noinput || { echo "ERROR: Django migration failed. Check DB connection/settings."; exit 1; }
python manage.py collectstatic --noinput || { echo "ERROR: Collectstatic failed. Check static configuration."; exit 1; }

# --- 4. START GUNICORN (FINAL FIX ATTEMPT) ---
echo "--- Django setup finished. Starting Gunicorn. ---"

# FIX: Forcing the DJANGO_SETTINGS_MODULE environment variable *directly* # into the Gunicorn command via the --env flag. This is the last and most 
# aggressive way to ensure the worker process gets the correct setting.
exec gunicorn \
  --chdir $APP_ROOT \
  --bind=0.0.0.0:${PORT:-8000} \
  --timeout 600 \
  --env DJANGO_SETTINGS_MODULE=$SETTINGS_MODULE \
  $WSGI_PATH


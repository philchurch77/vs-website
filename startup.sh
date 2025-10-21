#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status, treat unset variables as errors, and prevent errors in a pipeline from being hidden.
set -euo pipefail

# Change directory to the application root
cd /home/site/wwwroot

# --- 1. ACTIVATE VIRTUAL ENVIRONMENT (CRITICAL) ---
# Use 'antenv' as confirmed by Oryx logs.
VENV_PATH="antenv"
if [ -d "$VENV_PATH" ]; then
    echo "Activating virtual environment at $VENV_PATH..."
    source $VENV_PATH/bin/activate
else
    echo "Error: Virtual environment '$VENV_PATH' not found."
    exit 1
fi

# --- 2. DATABASE SETUP & STATIC FILES ---
echo "Running migrations and collecting static files..."
# NOTE: Ensure myproject.settings is the correct path to your settings file
python manage.py migrate --settings=myproject.settings
python manage.py collectstatic --noinput --settings=myproject.settings

# --- 3. START GUNICORN ---
echo "Starting Gunicorn..."
# Use exec to replace the shell process with the Gunicorn process
exec gunicorn \
  --chdir /home/site/wwwroot \
  --bind=0.0.0.0:${PORT:-8000} \
  --timeout 600 \
  # CHANGED: Using the standard path. If your inner folder is 'myproject', this should work.
  myproject.wsgi:application

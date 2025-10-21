#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status, treat unset variables as errors, and prevent errors in a pipeline from being hidden.
set -euo pipefail

# Change directory to the application root
cd /home/site/wwwroot

# --- 1. OPTIONAL: Unpack Artifact ---
# Conditional extraction of the application code
if [ -f output.tar.gz ]; then
  echo "Unpacking application archive..."
  tar -xzf output.tar.gz -C .
fi

# --- 2. ACTIVATE VIRTUAL ENVIRONMENT (CRITICAL) ---
VENV_PATH=".venv"
if [ -d "$VENV_PATH" ]; then
    echo "Activating virtual environment at $VENV_PATH..."
    source $VENV_PATH/bin/activate
else
    echo "Error: Virtual environment '$VENV_PATH' not found. Please ensure it was created during deployment."
    exit 1
fi

# --- 3. DATABASE SETUP & STATIC FILES ---
echo "Running migrations and collecting static files..."
# NOTE: Ensure myproject.settings is the correct path to your settings file
python manage.py migrate --settings=myproject.settings
python manage.py collectstatic --noinput --settings=myproject.settings

# --- 4. START GUNICORN ---
echo "Starting Gunicorn..."
# Use exec to replace the shell process with the Gunicorn process (good practice)
exec gunicorn \
  --chdir /home/site/wwwroot \
  --bind=0.0.0.0:${PORT:-8000} \
  --timeout 600 \
  # CRITICAL: Replace 'myproject.myprojectsettings.wsgi:application' with your actual WSGI module path
  myproject.myprojectsettings.wsgi:application

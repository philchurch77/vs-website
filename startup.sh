#!/usr/bin/env bash
set -euo pipefail

# Oryx starts this script with CWD already set to the extracted app path (e.g. /tmp/xxxx).
APP_ROOT="$(pwd)"

# 1) Activate the virtualenv created by Oryx (relative path)
VENV_PATH="$APP_ROOT/antenv"
if [ -d "$VENV_PATH" ]; then
  echo "Activating virtualenv: $VENV_PATH"
  # shellcheck disable=SC1091
  source "$VENV_PATH/bin/activate"
else
  echo "Warning: virtualenv not found at $VENV_PATH (Oryx may have set PYTHONPATH already). Continuing..."
fi

# 2) Python path + settings
export PYTHONPATH="$APP_ROOT:${PYTHONPATH:-}"
: "${DJANGO_SETTINGS_MODULE:=myproject.settings.settings}"   # <-- change if needed
WSGI_PATH="${WSGI_PATH:-myproject.settings.wsgi:application}"# <-- change if needed

# 3) Optional: run migrations & collectstatic (skip failing these in case DB not reachable)
if [ -f "$APP_ROOT/manage.py" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput || echo "Migrations failed (continuing)."
  echo "Collecting static..."
  python manage.py collectstatic --noinput || echo "Collectstatic failed (continuing)."
fi

# 4) Start gunicorn from the current app path
echo "Starting gunicorn..."
exec gunicorn \
  --chdir "$APP_ROOT" \
  --bind "0.0.0.0:${PORT:-8000}" \
  --timeout 600 \
  --env "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE" \
  "$WSGI_PATH"

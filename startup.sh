#!/usr/bin/env bash
set -euo pipefail

cd /home/site/wwwroot

# If you really need to unpack an artifact, leave this on; otherwise remove it
if [ -f /home/site/wwwroot/output.tar.gz ]; then
  tar -xzf /home/site/wwwroot/output.tar.gz -C /home/site/wwwroot
fi

# Optional: uncomment if you want these handled here
# python manage.py migrate --settings=myproject.settings
# python manage.py collectstatic --noinput --settings=myproject.settings

exec gunicorn \
  --chdir /home/site/wwwroot \
  --bind=0.0.0.0:${PORT:-8000} \
  --timeout 600 \
  myproject.myprojectsettings.wsgi:application

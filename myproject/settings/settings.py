from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# --- Core ---
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")  # safe default for local
DEBUG = os.getenv("DEBUG", "0") in ("1", "true", "True")

# --- Hosts / CSRF ---
runtime_host = os.environ.get("WEBSITE_HOSTNAME")  # set by Azure
extra_hosts = [x.strip() for x in os.getenv("ALLOWED_HOSTS_EXTRA", "").split(",") if x.strip()]
allow_all = os.getenv("ALLOW_ALL_HOSTS", "0") in ("1", "true", "True")

if allow_all:
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = [h for h in [
        runtime_host, *extra_hosts,
        "localhost", "127.0.0.1",
        ".azurewebsites.net", ".scm.azurewebsites.net",
    ] if h]

CSRF_TRUSTED_ORIGINS = []
for h in ALLOWED_HOSTS:
    h = h.lstrip(".")
    # Always include https origin
    CSRF_TRUSTED_ORIGINS.append(f"https://{h}")
# Explicitly add your Azure site
if "https://vs-training-website.azurewebsites.net" not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append("https://vs-training-website.azurewebsites.net")
# Add local http origins when DEBUG
if DEBUG:
    CSRF_TRUSTED_ORIGINS += ["http://localhost", "http://127.0.0.1"]

# --- Apps / Middleware ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "taggit",
    "myproject.users",
    "myproject.posts",
    "myproject.evaluation.apps.EvaluationConfig",
    "myproject.flashcards",
    "myproject.training",
    "myproject.sdq",
    "myproject.resources",
    "myproject.tolerance",
    "myproject.animation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "myproject.settings.urls"
WSGI_APPLICATION = "myproject.settings.wsgi.application"
ASGI_APPLICATION = "myproject.settings.asgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

# --- Database ---
SQLITE_PATH = os.environ.get("SQLITE_PATH")
if not SQLITE_PATH:
    # Use Azure path in prod, local file in dev
    SQLITE_PATH = "/home/site/data/db.sqlite3" if not DEBUG else (BASE_DIR / "db.sqlite3")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": SQLITE_PATH,
    }
}

# --- i18n / tz ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

# --- Static / media ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Use a simpler storage in DEBUG to avoid manifest errors
if DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join("/home/site/wwwroot", "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Proxy & cookie security ---
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = not DEBUG  # allow http locally
CSRF_COOKIE_SECURE = not DEBUG     # allow http locally

# --- Logging ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "django.security.csrf": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

if not SECRET_KEY and not DEBUG:
    raise RuntimeError("SECRET_KEY must be set in production")





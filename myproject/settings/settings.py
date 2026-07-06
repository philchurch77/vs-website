from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# --- Core ---
SECRET_KEY = os.getenv("SECRET_KEY", "")
DEBUG = os.getenv("DEBUG", "0") in ("1", "true", "True")

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-secret-key"  # local development only
    else:
        raise RuntimeError("SECRET_KEY must be set in production")

# --- Hosts / CSRF ---
runtime_host = os.environ.get("WEBSITE_HOSTNAME")  # set by Azure
extra_hosts = [x.strip() for x in os.getenv("ALLOWED_HOSTS_EXTRA", "").split(",") if x.strip()]

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
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "taggit",
    "myproject.core",
    "myproject.users",
    "myproject.flashcards",
    "myproject.sdq",
    "myproject.resources",
    "myproject.tolerance",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
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
# /home/site/data is Azure's persistent volume; wwwroot is wiped on each deploy
MEDIA_ROOT = "/home/site/data/media" if not DEBUG else os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Passwords ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Proxy & transport security ---
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = not DEBUG  # allow http locally
CSRF_COOKIE_SECURE = not DEBUG     # allow http locally
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    # Start with 1 hour; raise to 31536000 + INCLUDE_SUBDOMAINS once confirmed stable
    SECURE_HSTS_SECONDS = 3600

# --- Auth ---
LOGIN_URL = "/users/login/"
LOGIN_REDIRECT_URL = "/"

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Microsoft SSO is disabled for the user-testing phase. When re-enabling:
# restrict TENANT to the Cambridgeshire tenant ID (not "organizations"), and add a
# SOCIALACCOUNT_ADAPTER with an email-domain allowlist before turning auto-signup on.

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





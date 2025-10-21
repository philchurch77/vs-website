from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = False

runtime_host = os.environ.get("WEBSITE_HOSTNAME")  # set by Azure
extra_hosts = [x.strip() for x in os.getenv("ALLOWED_HOSTS_EXTRA", "").split(",") if x.strip()]

ALLOWED_HOSTS = [h for h in [runtime_host, *extra_hosts] if h]

# CSRF: include all allowed hosts + explicit Azure hostname (handy if WEBSITE_HOSTNAME is missing during local runs)
CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS]
if "vs-training-website.azurewebsites.net" not in [h.replace("https://","") for h in ALLOWED_HOSTS]:
    CSRF_TRUSTED_ORIGINS.append("https://vs-training-website.azurewebsites.net")

allow_all = os.getenv("ALLOW_ALL_HOSTS", "0") in ("1", "true", "True")
if allow_all:
    ALLOWED_HOSTS = ["*"]
else:
    runtime_host = os.environ.get("WEBSITE_HOSTNAME")
    extra_hosts = [x.strip() for x in os.getenv("ALLOWED_HOSTS_EXTRA", "").split(",") if x.strip()]
    ALLOWED_HOSTS = [h for h in [runtime_host, *extra_hosts, "localhost", "127.0.0.1", ".azurewebsites.net", ".scm.azurewebsites.net"] if h]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "taggit",

    # use dotted paths under the project package:
    "myproject.users",
    "myproject.posts",
    "myproject.evaluation.apps.EvaluationConfig",
    "myproject.flashcards",
    "myproject.training",
    "myproject.sdq",
    "myproject.resources",
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

WSGI_APPLICATION = "myproject.settings.wsgi.application"
ASGI_APPLICATION = "myproject.settings.asgi.application"

DATABASES = {"default": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": BASE_DIR / "db.sqlite3",
}}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SECRET_KEY and not DEBUG:
    raise RuntimeError("SECRET_KEY must be set in production")




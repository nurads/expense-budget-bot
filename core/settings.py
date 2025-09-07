from pathlib import Path

from dotenv import load_dotenv
import os
from urllib.parse import urlparse,parse_qsl

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv("SECRET_KEY")

BOT_TOKEN = os.getenv("DJANGO_BOT_TOKEN")

WEB_HOOK_URL = os.getenv("DJANGO_WEBHOOK_URL")

DEBUG = True

ALLOWED_HOSTS = ["expense-budget-bot.vercel.app","localhost","127.0.0.1"]

AUTH_USER_MODEL = "bot.User"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "bot",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

postgres_url=urlparse(os.getenv("DJANGO_POSTGRES_URL"))


DATABASES = {
    "dev": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": postgres_url.path[1:],
        "USER": postgres_url.username,
        "PASSWORD": postgres_url.password,
        "HOST": postgres_url.hostname,
        "PORT": postgres_url.port,
        "OPTIONS": dict(parse_qsl(postgres_url.query)),
        "DISABLE_SERVER_SIDE_CURSORS": True,
    }
}
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


STATIC_URL = "static/"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles", "static")
STATIC_URL = "/static/"

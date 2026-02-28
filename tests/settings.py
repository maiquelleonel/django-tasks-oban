import os
from pathlib import Path

# Base do projeto para caminhos relativos
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-oban-test-key-para-desenvolvimento"

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.postgres",
    "django_tasks_oban",
    "tests",
]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "oban"),
        "USER": os.environ.get("POSTGRES_USER", "default"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "default"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

TASKS = {
    "default": {
        "BACKEND": "django_tasks_oban.backends.ObanTaskBackend",
        "OPTIONS": {
            "QUEUE": "default",
            "DEFAULT_CONCURRENCY": 10,
        },
    }
}


USE_TZ = False
TIME_ZONE = "UTC"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

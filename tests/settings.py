import os
from pathlib import Path

# Base do projeto para caminhos relativos
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-oban-test-key-para-desenvolvimento"

DEBUG = True

ALLOWED_HOSTS = []

# Apps necessários para o funcionamento do django-tasks-oban
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.postgres",  # OBRIGATÓRIO para ArrayField
    "django_tasks_oban",  # O seu pacote
]

# Configuração de Banco de Dados (Postgres é mandatório para Oban/ArrayField)
# Tenta ler do ambiente (útil para GitHub Actions/Docker) ou usa um padrão local
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

# Configuração da nova Tasks API do Django 6
TASKS = {
    "default": {
        "BACKEND": "django_tasks_oban.backends.ObanTaskBackend",
        "OPTIONS": {
            "QUEUE": "default",
            "DEFAULT_CONCURRENCY": 10,
        },
    }
}

# Configurações básicas de fuso horário (Oban depende disso para scheduled_at)
USE_TZ = False
TIME_ZONE = "UTC"

# Necessário para o Runner do Django não reclamar de tabelas de migração
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

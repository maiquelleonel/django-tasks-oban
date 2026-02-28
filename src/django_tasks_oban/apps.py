from django.apps import AppConfig
from django.core import checks


class DjangoTasksObanConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_tasks_oban"
    verbose_name = "Django Tasks Oban"

    def ready(self):
        # Registra o check de sistema quando o Django inicia
        checks.register(check_postgres_compatibility, checks.Tags.compatibility)


def check_postgres_compatibility(app_configs, **kwargs):
    """
    Verifica se o django.contrib.postgres está instalado,
    já que o ObanJob depende de ArrayField.
    """
    from django.conf import settings

    errors = []

    if "django.contrib.postgres" not in settings.INSTALLED_APPS:
        errors.append(
            checks.Error(
                "'django.contrib.postgres' must be in INSTALLED_APPS.",
                hint="Oban uses PostgreSQL-specific fields like ArrayField. Add 'django.contrib.postgres' to your INSTALLED_APPS settings.",
                obj="django_tasks_oban",
                id="django_tasks_oban.E001",
            )
        )

    # Opcional: Verificar se o banco default é de fato Postgres
    from django.db import connections

    # Tentamos verificar apenas se as conexões já estiverem configuradas
    try:
        for alias in connections:
            engine = settings.DATABASES[alias]["ENGINE"]
            if "postgresql" not in engine:
                errors.append(
                    checks.Warning(
                        f"Database alias '{alias}' is not PostgreSQL.",
                        hint=f"django-tasks-oban is optimized for PostgreSQL. Using {engine} might cause errors with ArrayField.",
                        obj=f"settings.DATABASES['{alias}']",
                        id="django_tasks_oban.W001",
                    )
                )
    except Exception:
        # Evita quebrar se o DB não estiver acessível no momento do check
        pass

    return errors

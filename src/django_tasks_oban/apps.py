from django.apps import AppConfig
from django.core import checks


class DjangoTasksObanConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_tasks_oban"
    verbose_name = "Django Tasks Oban"

    def ready(self):
        checks.register(check_postgres_compatibility, checks.Tags.compatibility)
        checks.register(check_oban_migrations_applied, checks.Tags.database)


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


def check_oban_migrations_applied(app_configs, **kwargs):
    """
    Checks whether the oban_jobs table exists in the database,
    i.e. whether the django_tasks_oban migrations have been applied.
    """
    from django.db import connections

    errors = []

    try:
        connection = connections["default"]
        table_names = connection.introspection.table_names()

        if "oban_jobs" not in table_names:
            errors.append(
                checks.Warning(
                    "The 'oban_jobs' table was not found in the default database.",
                    hint=(
                        "Run 'manage.py migrate' to create the Oban schema. "
                        "The django_tasks_oban package requires the oban_jobs table to enqueue jobs."
                    ),
                    obj="django_tasks_oban",
                    id="django_tasks_oban.W002",
                )
            )
    except Exception:
        # Avoid breaking if the database is not reachable during the check
        pass

    return errors

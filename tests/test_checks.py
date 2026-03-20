from unittest.mock import MagicMock, patch

from django.core import checks
from django.test import TestCase, override_settings

from django_tasks_oban.apps import check_oban_migrations_applied, check_postgres_compatibility


class CheckPostgresCompatibilityTest(TestCase):
    @override_settings(INSTALLED_APPS=["django.contrib.auth"])
    def test_error_when_postgres_not_in_installed_apps(self):
        errors = check_postgres_compatibility(None)

        self.assertTrue(
            any(e.id == "django_tasks_oban.E001" for e in errors),
        )

    def test_no_error_when_postgres_in_installed_apps(self):
        errors = check_postgres_compatibility(None)

        postgres_errors = [e for e in errors if e.id == "django_tasks_oban.E001"]
        self.assertEqual(len(postgres_errors), 0)


class CheckObanMigrationsAppliedTest(TestCase):
    def test_no_warning_when_oban_jobs_table_exists(self):
        errors = check_oban_migrations_applied(None)

        migration_warnings = [e for e in errors if e.id == "django_tasks_oban.W002"]
        self.assertEqual(len(migration_warnings), 0)

    @patch("django.db.connections")
    def test_warning_when_oban_jobs_table_missing(self, mock_connections):
        mock_conn = MagicMock()
        mock_conn.introspection.table_names.return_value = ["auth_user", "django_migrations"]
        mock_connections.__getitem__.return_value = mock_conn

        errors = check_oban_migrations_applied(None)

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, "django_tasks_oban.W002")
        self.assertIn("oban_jobs", errors[0].msg)
        self.assertIn("manage.py migrate", errors[0].hint)

    @patch("django.db.connections")
    def test_no_error_when_database_unreachable(self, mock_connections):
        mock_conn = MagicMock()
        mock_conn.introspection.table_names.side_effect = Exception("Connection refused")
        mock_connections.__getitem__.return_value = mock_conn

        errors = check_oban_migrations_applied(None)

        self.assertEqual(len(errors), 0)

    @patch("django.db.connections")
    def test_warning_is_correct_level(self, mock_connections):
        mock_conn = MagicMock()
        mock_conn.introspection.table_names.return_value = []
        mock_connections.__getitem__.return_value = mock_conn

        errors = check_oban_migrations_applied(None)

        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], checks.CheckMessage)
        self.assertEqual(errors[0].level, checks.WARNING)

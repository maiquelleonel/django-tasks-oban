from datetime import datetime, timedelta

from django.db import transaction
from django.tasks import task
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from django_tasks_oban.decorators import oban_task
from django_tasks_oban.models import ObanJob, ObanJobState


@task()
def notify_user_task(): ...


@task()
def delayed_task(): ...


@oban_task(unique=True)
def send_welcome_task(): ...


@oban_task(unique={"period": 10, "states": [ObanJobState.AVAILABLE]})
def unique_for_next_10_seconds_task(): ...


@oban_task(unique={"states": "available"})
def generate_user_identity(): ...


@oban_task(tags="new_costumer")
def process_order_task(): ...


@oban_task(unique={"period": 1, "states": [ObanJobState.AVAILABLE]}, tags=["Admin", "refund"])
def process_refund_order_task(): ...


@oban_task(cron="@weekly")
def weekly_report_task(): ...


@oban_task(cron="15 20 * * *")
def stock_balance_report_task(): ...


@oban_task(cron="99 20,30 * * 1")
def invalid_cron_task(): ...


@oban_task(cron=["0 0 * * *", "1 2 3 * *"])
def invalid_type_cron_task(): ...


@oban_task(scheduled_at="2026-12-31 18:00:00", customer_id="213123", trace_id="xpto-42-989")
def custom_schedule_with_attr_task(): ...


@task()
def sao_paulo_menagement_report(): ...


@oban_task(cron="@monthly", timezone="Europe/Paris")
def french_management_report(): ...


class ObanBackendTest(TransactionTestCase):
    def test_enqueue_creates_job_record(self):

        notify_user_task.enqueue(user_id=42)

        db_job = ObanJob.objects.filter(worker="notify_user_task").last()
        self.assertEqual(db_job.args, {"user_id": 42})
        self.assertEqual(db_job.state, ObanJobState.AVAILABLE)

    def test_enqueue_outside_transaction(self):
        self.assertFalse(transaction.get_connection().in_atomic_block)

        notify_user_task.enqueue(x=10)

        self.assertTrue(
            ObanJob.objects.filter(
                worker="notify_user_task",
                args={"x": 10},
            ).exists()
        )

    def test_enqueue_inside_transaction_atomic(self):
        query = ObanJob.objects.filter(args={"x": 20}).exists
        with transaction.atomic():
            notify_user_task.enqueue(x=20)
            self.assertFalse(query())

        self.assertTrue(query())

    def test_enqueue_rollback_transaction(self):
        try:
            with transaction.atomic():
                notify_user_task.enqueue(x=30)
                raise Exception("Just simulate a rollback")
        except Exception:
            pass

        self.assertFalse(ObanJob.objects.filter(args={"x": 30}).exists())

    def test_scheduled_job_has_correct_state(self):
        delayed_task.using(run_after=timedelta(seconds=3)).enqueue(some_id=2)

        db_job = ObanJob.objects.get(worker="delayed_task")
        self.assertEqual(db_job.state, ObanJobState.SCHEDULED)
        self.assertGreater(db_job.scheduled_at, timezone.now())

    def test_scheduled_job_inside_atomic_transaction(self):
        with transaction.atomic():
            delayed_task.using(run_after=timedelta(seconds=3)).enqueue(some_id=24)
            self.assertFalse(
                ObanJob.objects.filter(
                    worker="delayed_task", args={"some_id": 24}, state=ObanJobState.SCHEDULED
                ).exists()
            )

        db_job = ObanJob.objects.filter(worker="delayed_task", args={"some_id": 24}).get()

        self.assertEqual(db_job.state, ObanJobState.SCHEDULED)
        self.assertTrue(db_job.scheduled_at > timezone.now())

    def test_enqueue_unique_job(self):

        send_welcome_task.enqueue(user_id=1)

        job = ObanJob.objects.get(worker="send_welcome_task")
        self.assertIn("unique_key", job.meta)
        self.assertEqual(job.meta["unique_period"], 60)  # default value
        # Garante que o hash é uma string SHA256 válida
        self.assertEqual(len(job.meta["unique_key"]), 64)

    def test_enqueue_unique_for_next_10_seconds_job(self):
        unique_for_next_10_seconds_task.enqueue(user_id=1)

        job = ObanJob.objects.get(worker="unique_for_next_10_seconds_task")
        self.assertIn("unique_key", job.meta)
        self.assertEqual(job.meta["unique_period"], 10)
        # Garante que o hash é uma string SHA256 válida
        self.assertEqual(len(job.meta["unique_key"]), 64)

    def test_enqueue_with_string_status(self):
        generate_user_identity.enqueue(user_id=23)

        job = ObanJob.objects.get(worker="generate_user_identity")
        self.assertIn("unique_key", job.meta)
        self.assertEqual(job.meta["unique_period"], 60)
        self.assertEqual(len(job.meta["unique_key"]), 64)
        self.assertEqual(job.meta["unique_states"], [ObanJobState.AVAILABLE])

    def test_enqueue_tagged_job(self):
        process_order_task.enqueue(order_id=123)
        job = ObanJob.objects.get(worker="process_order_task")

        self.assertEqual(job.tags, ["new_costumer"])

    def test_enqueue_unique_tagged_job(self):
        process_refund_order_task.enqueue(order_id=123)
        job = ObanJob.objects.get(worker="process_refund_order_task")

        self.assertEqual(job.tags, ["admin", "refund"])
        self.assertEqual(job.meta["unique_period"], 1)
        self.assertEqual(len(job.meta["unique_key"]), 64)
        self.assertEqual(job.meta["unique_states"], [ObanJobState.AVAILABLE])

    def test_enqueue_nicknamed_cron_job(self):
        weekly_report_task.enqueue(order_id=123)
        job = ObanJob.objects.get(worker="weekly_report_task")

        self.assertTrue(job.meta["cron"])
        self.assertEqual(job.meta["cron_expr"], "@weekly")

    def test_enqueue_expressioned_cron_job(self):
        stock_balance_report_task.enqueue(order_id=123)
        job = ObanJob.objects.get(worker="stock_balance_report_task")

        self.assertTrue(job.meta["cron"])
        self.assertEqual(job.meta["cron_expr"], "15 20 * * *")

    def test_try_enqueue_invalid_cron_expression(self):
        with self.assertRaises(ValueError):
            invalid_cron_task.enqueue(oid=123)

    def test_try_enqueue_invalid_type_cron_expression(self):
        with self.assertRaises(ValueError):
            invalid_type_cron_task.enqueue(oid=123)

    def test_enqueue_custom_schedule_at_with_custom_attr(self):
        custom_schedule_with_attr_task.enqueue(user_id=989)

        job = ObanJob.objects.get(worker="custom_schedule_with_attr_task")

        self.assertEqual(job.meta["customer_id"], "213123")
        self.assertEqual(job.meta["trace_id"], "xpto-42-989")
        self.assertEqual(job.scheduled_at, datetime.strptime("2026-12-31 18:00:00", "%Y-%m-%d %H:%M:%S"))

    @override_settings(USE_TZ=True)
    def test_enqueue_timezoned_job(self):
        sao_paulo_menagement_report.enqueue(customer_id=12312)

        job = ObanJob.objects.get(worker="sao_paulo_menagement_report")

        self.assertEqual(job.state, ObanJobState.AVAILABLE)

    def test_enqueue_another_timezone_job(self):
        french_management_report.enqueue(customer_id=12312)

        job = ObanJob.objects.get(worker="french_management_report")

        self.assertEqual(job.state, ObanJobState.SCHEDULED)
        self.assertEqual(job.meta["timezone_tz"], "Europe/Paris")

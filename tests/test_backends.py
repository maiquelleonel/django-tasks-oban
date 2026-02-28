from datetime import timedelta

from django.db import transaction
from django.tasks import task
from django.test import TransactionTestCase
from django.utils import timezone

from django_tasks_oban.models import ObanJob, ObanJobState


@task()
def notify_user_task():  # user_id):
    pass


@task()
def delayed_task():
    pass


class ObanBackendTest(TransactionTestCase):
    def test_enqueue_creates_job_record(self):

        notify_user_task.enqueue(user_id=42)

        db_job = ObanJob.objects.get(worker="notify_user_task")
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
        self.assertTrue(db_job.scheduled_at > timezone.now())

    def test_scheduled_job_inside_atomic_transaction(self):
        with transaction.atomic():
            delayed_task.using(run_after=timedelta(seconds=3)).enqueue(some_id=24)
            self.assertFalse(
                ObanJob.objects.filter(
                    worker="delayed_task",
                    args={"some_id": 42},
                ).exists()
            )

        db_job = ObanJob.objects.get(worker="delayed_task")
        self.assertEqual(db_job.state, ObanJobState.SCHEDULED)
        self.assertTrue(db_job.scheduled_at > timezone.now())

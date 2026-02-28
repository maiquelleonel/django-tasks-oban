from datetime import timedelta

from django.tasks import task
from django.test import TestCase
from django.utils import timezone

from django_tasks_oban.backends import ObanTaskBackend
from django_tasks_oban.models import ObanJob, ObanJobState


@task()
def notify_user(_):  # user_id):
    pass


@task()
def delayed_task():
    pass


class ObanBackendTest(TestCase):
    def test_enqueue_creates_job_record(self):
        _ = ObanTaskBackend(alias="default", params={})

        _ = notify_user.enqueue(user_id=42)

        db_job = ObanJob.objects.get(worker="notify_user")
        self.assertEqual(db_job.args, {"user_id": 42})
        self.assertEqual(db_job.state, ObanJobState.AVAILABLE)

    def test_scheduled_job_has_correct_state(self):

        delayed_task.using(run_after=timedelta(seconds=3)).enqueue(some_id=2)

        db_job = ObanJob.objects.get(worker="delayed_task")
        self.assertEqual(db_job.state, ObanJobState.SCHEDULED)
        self.assertTrue(db_job.scheduled_at > timezone.now())

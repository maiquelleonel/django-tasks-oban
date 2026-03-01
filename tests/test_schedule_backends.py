from datetime import timedelta

from django.db import transaction
from django.tasks import task
from django.test import TransactionTestCase
from django.utils import timezone

from django_tasks_oban.models import ObanJob, ObanJobState


@task()
def notify_user_task(): ...


class ObanScheduledTestMixin:
    def assert_job_scheduled_correctly(self, job_query, expected_delay_seconds):
        job = job_query.get()
        self.assertEqual(job.state, ObanJobState.SCHEDULED)

        now = timezone.now()
        diff = job.scheduled_at - now

        self.assertAlmostEqual(diff.total_seconds(), expected_delay_seconds, delta=5)


class ObanScheduledTest(TransactionTestCase, ObanScheduledTestMixin):
    def test_sync_enqueue_scheduled(self):
        delay = 600  # 10 minutos
        notify_user_task.using(run_after=timedelta(seconds=delay)).enqueue(x=1)

        query = ObanJob.objects.filter(worker="notify_user_task", args={"x": 1})
        self.assert_job_scheduled_correctly(query, delay)

    def test_sync_enqueue_scheduled_atomic_commit(self):
        delay = 600
        with transaction.atomic():
            notify_user_task.using(run_after=timedelta(seconds=delay)).enqueue(x=2)
            self.assertFalse(
                ObanJob.objects.filter(
                    args={"x": 2},
                ).exists()
            )

        job = ObanJob.objects.get(args={"x": 2})
        self.assertEqual(job.state, ObanJobState.SCHEDULED)
        self.assertTrue(job.scheduled_at > timezone.now())

    def test_sync_enqueue_scheduled_atomic_rollback(self):
        try:
            with transaction.atomic():
                notify_user_task.using(run_after=timedelta(minutes=5)).enqueue(x=4)
                raise Exception("Random rollback")
        except Exception:
            pass

        self.assertFalse(ObanJob.objects.filter(args={"x": 4}).exists())

    async def test_async_aenqueue_scheduled(self):
        await notify_user_task.using(run_after=timedelta(seconds=300)).aenqueue(y=2)
        query = ObanJob.objects.filter(worker="notify_user_task", args={"y": 2})

        job = await query.aget()
        self.assertEqual(job.state, ObanJobState.SCHEDULED)
        self.assertTrue(job.scheduled_at > timezone.now())

    async def test_async_aenqueue_scheduled_atomic_rollback(self):
        delay = 300

        try:
            with transaction.atomic():
                await notify_user_task.using(run_after=timedelta(seconds=delay)).aenqueue(y=1)

                exists_inside = await ObanJob.objects.filter(args={"y": 1}).aexists()
                self.assertTrue(exists_inside)
                raise Exception("Async Rollback")
        except Exception:
            pass

        exists_after = await ObanJob.objects.filter(args={"y": 1}).aexists()
        self.assertFalse(exists_after)

import uuid
from datetime import timedelta

from django.db import transaction
from django.tasks import TaskResult, TaskResultStatus
from django.tasks.backends.base import BaseTaskBackend
from django.utils import timezone

from .models import ObanJob, ObanJobState


class ObanTaskBackend(BaseTaskBackend):
    supports_defer = True
    supports_priority = True
    supports_run_after = True

    def __init__(self, alias, params):
        super().__init__(alias, params)
        self.queue_name = params.get("QUEUE", "default")

    def _prepare_job_data(self, task, args, kwargs):
        now = timezone.now()

        run_after = getattr(task, "run_after", None)

        scheduled_at = now
        if isinstance(run_after, timedelta):
            scheduled_at += run_after

        state = ObanJobState.AVAILABLE
        if scheduled_at > now:
            state = ObanJobState.SCHEDULED

        return {
            "worker": task.name,
            "args": kwargs or {},
            "meta": {"args": list(args)},
            "queue": getattr(task, "queue_name", self.queue_name),
            "errors": [],
            "state": state,
            "priority": getattr(task, "priority", 0),
            "scheduled_at": scheduled_at,
        }

    def enqueue(self, task, args, kwargs):
        data = self._prepare_job_data(task, args, kwargs)

        conn = transaction.get_connection()

        def _save():
            return ObanJob.objects.create(**data)

        if conn.in_atomic_block:
            transaction.on_commit(_save)
        else:
            _save()

        return self._result(task, args, kwargs)

    async def aenqueue(self, task, args, kwargs):
        """Implementação Assíncrona: Injeta .acreate()"""
        data = self._prepare_job_data(task, args, kwargs)

        await ObanJob.objects.acreate(**data)

        return self._result(task, args, kwargs)

    def _result(self, task, args, kwargs):

        return TaskResult(
            id=str(uuid.uuid4()),
            status=TaskResultStatus.READY,
            enqueued_at=timezone.now(),
            args=args,
            kwargs=kwargs,
            task=task,
            backend=self,
            started_at=None,
            finished_at=None,
            last_attempted_at=None,
            errors=[],
            worker_ids=[],
        )

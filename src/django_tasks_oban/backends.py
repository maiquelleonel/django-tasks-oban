import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from django.db import transaction
from django.tasks import Task, TaskResult, TaskResultStatus
from django.tasks.backends.base import BaseTaskBackend
from django.utils import timezone
from oban._scheduler import Expression
from oban.job import Job

from .decorators import OBAN_TASK_REGISTRY
from .models import ObanJob, ObanJobState


def _normalize_timezone(dt):
    if isinstance(dt, str):
        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")

    if dt and timezone.is_naive(dt):
        tz = timezone.get_current_timezone()
        return timezone.make_aware(dt, tz)
    return dt


def _generate_unique_key(worker_name, args, kwargs):
    try:
        payload = json.dumps(
            {"w": worker_name, "a": args, "k": kwargs},
            sort_keys=True,
            default=str,
        )
    except (ValueError, TypeError):
        payload = f"{worker_name}-{repr(args)}-{repr(kwargs)}"

    return hashlib.sha256(payload.encode()).hexdigest()


class ObanTaskBackend(BaseTaskBackend):
    supports_defer = True
    supports_priority = True
    supports_run_after = True

    def __init__(self, alias, params):
        super().__init__(alias, params)
        self.queue_name = params.get("QUEUE", "default")

    def _prepare_job_data(self, task: Task, args: list, kwargs: dict) -> dict[str, Any]:
        now = _normalize_timezone(timezone.now())

        run_after = getattr(task, "run_after", None)
        worker_func = getattr(task, "func", None)
        opts = OBAN_TASK_REGISTRY.get(worker_func, {}).copy()
        meta: dict[str, Any] = {}
        meta["args"] = list(args)
        tags = []
        scheduled_at = now

        if "unique" in opts:
            meta["unique_key"] = _generate_unique_key(task.name, args, kwargs)
            unique_period = 60
            unique_states = ["available", "scheduled", "executing"]

            if isinstance(opts["unique"], dict):
                unique_period = opts["unique"].get("period", 60)
                states = opts["unique"].get("states", unique_states)
                # Garante que o Postgres receba um array JSONB, não uma string solta
                unique_states = states if isinstance(states, list) else [states]

            meta["unique_period"] = unique_period
            meta["unique_states"] = unique_states

        if "tags" in opts:
            opt_tags = opts.get("tags", [])
            tags = opt_tags if isinstance(opt_tags, list) else [opt_tags]
            job_ = Job(worker=task.name, tags=tags)
            job_._normalize_tags()
            tags = job_.tags

        if "cron" in opts:
            if not isinstance(opts["cron"], (str, dict)):
                raise ValueError("Strange value for cron expression, review value")

            candidate = opts["cron"] if isinstance(opts["cron"], str) else opts["cron"]["expr"]

            Expression.parse(candidate)  # validate cron expressions
            meta["cron"] = True
            meta["cron_expr"] = opts["cron"]
            meta["timezone_tz"] = opts.get("timezone", None) or "UTC"
            state = ObanJobState.SCHEDULED  # type: ignore[attr-defined]
            priority = 0
        else:
            if isinstance(run_after, timedelta):
                scheduled_at += run_after
            elif opts.get("scheduled_at", None):
                scheduled_at = _normalize_timezone(opts.get("scheduled_at"))
                opts.pop("scheduled_at", None)

            state = ObanJobState.AVAILABLE  # type: ignore[attr-defined]
            if scheduled_at > now:
                state = ObanJobState.SCHEDULED  # type: ignore[attr-defined]

            priority = getattr(task, "priority", 0)

        for key in ["cron", "tags", "unique"]:
            opts.pop(key, None)

        meta |= opts

        return {
            "worker": task.name,
            "args": kwargs or {},
            "meta": meta,
            "queue": getattr(task, "queue_name", self.queue_name),
            "errors": [],
            "state": state,
            "tags": tags,
            "priority": priority,
            "scheduled_at": scheduled_at,
        }

    def enqueue(self, task: Task, args: list, kwargs: dict) -> TaskResult:
        data = self._prepare_job_data(task, args, kwargs)

        conn = transaction.get_connection()

        def _save():
            return ObanJob.objects.create(**data)

        if conn.in_atomic_block:
            transaction.on_commit(_save)
        else:
            _save()

        return self._result(task, args, kwargs)

    async def aenqueue(self, task: Task, args: list, kwargs: dict) -> TaskResult:
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
            backend=self.__repr__(),
            started_at=None,
            finished_at=None,
            last_attempted_at=None,
            errors=[],
            worker_ids=[],
        )

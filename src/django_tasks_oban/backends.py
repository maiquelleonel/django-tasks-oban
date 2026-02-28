import uuid
from datetime import timedelta

from django.tasks.backends.base import BaseTaskBackend
from django.tasks.base import TaskResult, TaskResultStatus  # No Django 6 real
from django.utils import timezone

from .models import ObanJob, ObanJobState


class ObanTaskBackend(BaseTaskBackend):
    supports_defer = True
    supports_run_after = True
    supports_priority = True

    def __init__(self, alias, params):
        super().__init__(alias, params)
        self.queue_name = params.get("QUEUE", "default")

    def enqueue(self, task, args, kwargs):
        # 1. Preparar dados para o Oban
        now = timezone.now()

        # 1. Pegar o run_after do objeto Task (timedelta)
        # O Django 6 Task object tem o atributo .run_after
        run_after = getattr(task, "run_after", None)

        # 2. Calcular o scheduled_at
        if run_after and isinstance(run_after, timedelta):
            scheduled_at = now + run_after
        else:
            # Fallback para o 'run_at' que pode vir nas options (se houver)
            scheduled_at = now

        state = ObanJobState.AVAILABLE
        if scheduled_at > timezone.now():
            state = ObanJobState.SCHEDULED

        # 2. Criar o registro no banco (Sync)
        # O Django 6 espera que retornemos um ID. Como o ObanJob ainda
        # não foi persistido (on_commit), geramos um UUID ou usamos o ID do DB.
        job_id = str(uuid.uuid4())

        # Persistência

        ObanJob.objects.create(
            worker=task.name,
            args=kwargs or {},
            meta={"args": list(args), "django_task_id": job_id},
            queue=getattr(task, "queue", "default"),
            state=state,
            priority=getattr(task, "priority", 0),
            scheduled_at=scheduled_at,
        )

        # 3. Retornar o TaskResult com TODOS os 10 argumentos obrigatórios
        # Como a tarefa acabou de ser enfileirada, preenchemos o "estado inicial"
        return TaskResult(
            id=job_id,
            status=TaskResultStatus.READY,
            enqueued_at=timezone.now(),
            started_at=None,
            finished_at=None,
            last_attempted_at=None,
            args=args,
            kwargs=kwargs,
            errors=[],
            worker_ids=[],
            task=task,
            backend=self,
        )

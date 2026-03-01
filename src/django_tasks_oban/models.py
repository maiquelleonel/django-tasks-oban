from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from oban.job import JobState


class ObanJobState(models.TextChoices): ...


for s in JobState:
    setattr(ObanJobState, s.name, s.value)

ObanJobState._choices = [(s.value, s.name.title()) for s in JobState]


class ObanJob(models.Model):
    id = models.BigAutoField(primary_key=True)
    state = models.TextField(
        choices=ObanJobState._choices,
        default=ObanJobState.AVAILABLE,
    )
    queue = models.TextField(default="default")
    worker = models.TextField()

    # JSON nativo (JSONB no Postgres)
    args = models.JSONField(default=dict)
    meta = models.JSONField(default=dict, null=True)

    errors = models.JSONField(default=list)
    tags = ArrayField(models.TextField(), default=list, null=True)
    attempted_by = ArrayField(models.TextField(), default=list, null=True)

    attempt = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=20)
    priority = models.IntegerField(default=0)

    # Timestamps com precisão de 6 (padrão do Oban/Elixir)
    inserted_at = models.DateTimeField(default=timezone.now)
    scheduled_at = models.DateTimeField(default=timezone.now)
    attempted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    discarded_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "oban_jobs"
        indexes = [
            models.Index(fields=["queue"], name="oban_jobs_queue_index"),
            models.Index(fields=["state"], name="oban_jobs_state_index"),
            models.Index(fields=["state", "queue", "priority", "scheduled_at", "id"], name="oban_jobs_main_idx"),
        ]

    def __str__(self):  # pragma: no cover
        return f"{self.id}: {self.worker} [{self.state}]"

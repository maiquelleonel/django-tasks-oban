from django.db import models
from django.utils import timezone

# conditional imports

try:
    from django.contrib.postgres.fields import ArrayField
except ImportError:
    ArrayField = None


class ObanJob(models.Model):
    id = models.BigAutoField(primary_key=True)
    state = models.TextField(default="available")
    queue = models.TextField(default="default")
    worker = models.TextField()

    args = models.JSONField(default=dict)
    meta = models.JSONField(default=dict, null=True)

    if ArrayField:
        errors = ArrayField(models.JSONField(), default=list)
        tags = ArrayField(models.TextField(), default=list, null=True)
        attempted_by = ArrayField(models.TextField(), default=list, null=True)
    else:
        errors = models.JSONField(default=list)
        tags = models.JSONField(default=list, null=True)
        attempted_by = models.JSONField(default=list, null=True)

    attempt = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=20)
    priority = models.IntegerField(default=0)

    inserted_at = models.DateTimeField(default=timezone.now)
    scheduled_at = models.DateTimeField(default=timezone.now)
    attempted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    discarded_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "oban_jobs"
        indexes = [
            models.Index(fields=["queue"], name="oban_jobs_queue_index"),
            models.Index(fields=["state"], name="oban_jobs_state_index"),
        ]

    def __str__(self):
        return f"{self.id}: {self.worker} [{self.state}]"

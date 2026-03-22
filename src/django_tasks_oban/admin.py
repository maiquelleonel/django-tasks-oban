from django.contrib import admin

from .models import ObanJob


@admin.register(ObanJob)
class ObanJobAdmin(admin.ModelAdmin):
    list_display = ("id", "worker", "state", "queue", "attempt", "scheduled_at")
    list_filter = ("state", "queue", "worker")
    search_fields = ("worker", "args", "attempted_by")

    readonly_fields = (
        "inserted_at",
        "attempted_at",
        "completed_at",
        "cancelled_at",
        "discarded_at",
        "attempted_by",
    )

    fieldsets = (
        ("Status", {"fields": ("state", "queue", "worker", "priority")}),
        ("Payload & Metadata", {"fields": ("args", "meta", "tags")}),
        (
            "Execution & Errors",
            {
                "fields": ("attempt", "max_attempts", "attempted_by", "errors"),
                "description": "Id's which try to execute this job.",
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "inserted_at",
                    "scheduled_at",
                    "attempted_at",
                    "completed_at",
                    "cancelled_at",
                    "discarded_at",
                ),
            },
        ),
    )

    ordering = ("-scheduled_at",)

from django.contrib import admin

from .models import ObanJob


@admin.register(ObanJob)
class ObanJobAdmin(admin.ModelAdmin):
    # Exibição na lista principal
    list_display = ("id", "worker", "state", "queue", "attempt", "scheduled_at")
    list_filter = ("state", "queue", "worker")
    search_fields = ("worker", "args", "attempted_by")

    # Campos somente leitura para evitar alteração acidental de logs
    readonly_fields = (
        "inserted_at",
        "attempted_at",
        "completed_at",
        "cancelled_at",
        "discarded_at",
        "attempted_by",  # Rastreabilidade: Quem tentou rodar?
    )

    fieldsets = (
        ("Status Principal", {"fields": ("state", "queue", "worker", "priority")}),
        ("Payload & Metadados", {"fields": ("args", "meta", "tags")}),
        (
            "Execução & Erros",
            {
                "fields": ("attempt", "max_attempts", "attempted_by", "errors"),
                "description": "Lista de IDs de processos/hosts que tentaram executar este job.",
            },
        ),
        (
            "Linha do Tempo (Timestamps)",
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

    # Ordenação padrão: Jobs mais novos ou agendados primeiro
    ordering = ("-scheduled_at",)

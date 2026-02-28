import asyncio
import signal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from django_tasks_oban.engine import get_oban_instance


class Command(BaseCommand):
    help = "Roda o worker do Oban para processar tarefas do Django 6 Tasks"

    def add_arguments(self, parser):
        parser.add_argument(
            "--queues",
            type=str,
            help="Filas (ex: default,mail:20). Default concorrência: lida do settings ou 10",
        )
        parser.add_argument(
            "--database",
            type=str,
            default="default",
            help="Alias do banco de dados (default: 'default')",
        )

    def _parse_queues(self, queues_str: str, default_val: int) -> dict[str, int]:
        """Converte 'mail,default:20' -> {'mail': default_val, 'default': 20}"""
        queues = {}
        parts = [p.strip() for p in queues_str.split(",") if p.strip()]

        for part in parts:
            if ":" in part:
                try:
                    name, val = part.split(":", 1)
                    queues[name.strip()] = int(val)
                except ValueError:
                    raise CommandError(f"❌ Formato inválido: '{part}'. Use nome:valor")
            else:
                queues[part] = default_val
        return queues

    def handle(self, *args, **options):
        db_alias = options["database"]

        task_config = getattr(settings, "TASKS", {}).get(db_alias, {})
        backend_options = task_config.get("OPTIONS", {})

        default_concurrency = backend_options.get("DEFAULT_CONCURRENCY", 10)

        # 3. Resolução de Filas (CLI > Settings > Default)
        queues_raw = options.get("queues")
        if queues_raw:
            queues = self._parse_queues(queues_raw, default_concurrency)
        else:
            # Se não passou nada no CLI, pega o dict de QUEUES do settings ou usa a default
            queues = backend_options.get("QUEUES", {"default": default_concurrency})

        # 4. Configurações de Pool (Soma das concorrências + folga)
        pool_options = backend_options.get("POOL", {"min_size": 1, "max_size": sum(queues.values()) + 2})

        self.stdout.write(self.style.SUCCESS(f"🚀 Iniciando Oban Worker [DB: {db_alias}]"))
        self.stdout.write(f"📊 Concorrência Padrão: {default_concurrency}")
        self.stdout.write(f"📋 Filas Ativas: {', '.join([f'{k}({v})' for k, v in queues.items()])}")

        try:
            asyncio.run(self.run_worker(db_alias, queues, pool_options))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n🛑 Worker interrompido pelo usuário."))

    async def run_worker(self, db_alias, queues, pool_options):
        oban = await get_oban_instance(alias=db_alias, queues=queues, pool_options=pool_options)

        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()

        # Handler para encerrar o loop com segurança
        def stop_handler():
            self.stdout.write(self.style.WARNING("\n🛑 Sinal de parada recebido. Encerrando..."))
            stop_event.set()

        # Registra os sinais (SIGINT para Ctrl+C, SIGTERM para encerramento do sistema)
        for s in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(s, stop_handler)
            except NotImplementedError:
                pass  # Fallback para Windows (que não suporta signal handlers de loop)

        try:
            async with oban:
                self.stdout.write(self.style.HTTP_INFO("⚡ Worker pronto. Pressione Ctrl+C para sair."))
                await stop_event.wait()  # Aguarda o sinal de parada
        finally:
            # Garante que o pool do asyncpg feche antes do processo morrer
            if hasattr(oban, "pool"):
                await oban.pool.close()
            self.stdout.write(self.style.SUCCESS("🔌 Pool de conexões fechado com sucesso."))

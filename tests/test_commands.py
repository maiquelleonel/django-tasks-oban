from unittest.mock import AsyncMock, patch

from django.core.management import call_command
from django.test import TestCase


class ObanCommandTest(TestCase):
    def test_parse_queues_internal_logic(self):
        from tests.management.commands.oban_worker import Command

        cmd = Command()

        parsed = cmd._parse_queues("mail:5,default", default_val=10)
        self.assertEqual(parsed["mail"], 5)
        self.assertEqual(parsed["default"], 10)

    @patch("tests.management.commands.oban_worker.Command.run_worker", new_callable=AsyncMock)
    def test_call_command_passes_args(self, mock_run_worker):
        mock_run_worker.return_value = "ok"
        call_command("oban_worker", queues="mail:25,reports", database="default")

        mock_run_worker.assert_awaited_once()

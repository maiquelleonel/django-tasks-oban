import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


def run_tests():
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"

    # Adiciona o diretório src ao path para o Django achar seu pacote
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True)

    # Roda os testes do seu app
    failures = test_runner.run_tests(["django_tasks_oban"])
    sys.exit(bool(failures))


if __name__ == "__main__":
    run_tests()

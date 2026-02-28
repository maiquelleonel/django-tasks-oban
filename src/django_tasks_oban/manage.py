#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
    # Garante que o código em src/ seja visível
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Django não encontrado.") from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

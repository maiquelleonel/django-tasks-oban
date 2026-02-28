#!/usr/bin/env python
import os
import sys
from pathlib import Path


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
    # Garante que o código em src/ seja visível
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Django não encontrado.") from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("django-tasks-oban")
except PackageNotFoundError:
    # Pacote não instalado (ex: rodando localmente sem pip/uv install)
    __version__ = "0.1.0-dev"

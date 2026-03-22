import inspect
import weakref
from typing import Any

from django.tasks import Task
from django.tasks import task as django_task

OBAN_TASK_REGISTRY: weakref.WeakKeyDictionary[Any, dict[str, Any]] = weakref.WeakKeyDictionary()


def oban_task(**kwargs):
    task_params = inspect.signature(Task).parameters.keys()

    django_kwargs = {k: v for k, v in kwargs.items() if k in task_params}
    oban_opts = {k: v for k, v in kwargs.items() if k not in task_params}

    def decorator(func):
        t = django_task(**django_kwargs)(func)

        OBAN_TASK_REGISTRY[func] = oban_opts

        return t

    return decorator

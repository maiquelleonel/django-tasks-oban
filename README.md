# 🐘 django-tasks-oban 🚀

[![CI](https://github.com/maiquelleonel/django-tasks-oban/actions/workflows/ci.yml/badge.svg)](https://github.com/maiquelleonel/django-tasks-oban/actions/workflows/ci.yml/badge.svg)

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Python](https://img.shields.io/badge/python-3.13-blue.svg?link=https%3A%2F%2Fwww.python.org)](https://www.python.org)
[![Django](https://img.shields.io/badge/django-6.0%2B-darkgreen.svg?link=https%3A%2F%2Fwww.djangoproject.com)](https:://www.djangoproject.com)

[![codecov](https://codecov.io/github/maiquelleonel/django-tasks-oban/graph/badge.svg?token=OG4ZFY7FX6)](https://codecov.io/github/maiquelleonel/django-tasks-oban)

![GitHub License](https://img.shields.io/github/license/maiquelleonel/django-tasks-oban)


**A high-performance, transactional, and PostgreSQL-native task producer for Django 6.0+, fully compatible with the [Oban](https://github.comhttps://github.com/oban-bg/oban) ecosystem.**

---

## ✨ Why django-tasks-oban?

Built for the modern Django era, this package provides a seamless bridge to the Oban job processing engine. By using your existing PostgreSQL database as a queue, you eliminate the need for Redis or RabbitMQ.

*   **📦 Transactional Integrity**: Enqueue jobs within the same database transaction. If the transaction rolls back, the job is never created. No more "ghost jobs"!
*   **⚡ Async-Native DI**: Optimized for **Python 3.13**, supporting both `enqueue` (Sync) and `aenqueue` (Async) using Django 6's ORM `create`/`acreate` dependency injection.
*   **🕒 Precise Scheduling**: Full support for Django's `.using(run_after=...)` sugar syntax.
*   **🛠️ 100% Test Coverage**: Solid code base, fully tested from backends to models.
*   **🌍 Multi-Language Ready**: Uses the official Oban schema, allowing workers in **Elixir**, **Python**, or any Oban-compatible runner to process your Django jobs.

---

## 🏗 Architectural Design: Producer-Only

This package is a **Producer-Only** implementation. It focuses on safely enqueuing jobs with maximum reliability. 

To process jobs, you should use an official Oban worker:
1. **[Oban (Elixir)](https://github.com/oban-bg/oban)**: For high-throughput Elixir/Phoenix clusters.
2. **[Oban-py](https://github.com/oban-bg/oban-py.git)**: For Python-based workers.

---

## 🛠 Installation

Optimized for the **uv** package manager:

```bash
uv add "django-tasks-oban @ git+https://github.com/maiquelleonel/django-tasks-oban.git"
```

---
## ⚙️ Configuration

Add to your `INSTALLED_APPS` (django.contrib.postgres is required):

```python
# settings.py

INSTALLED_APPS = [
    ...,
    "django.contrib.postgres",
    "django_tasks_oban",
]

TASKS = {
    "default": {
        "BACKEND": "django_tasks_oban.backends.ObanTaskBackend",
        "OPTIONS": {
            "QUEUE": "default",               
            "DEFAULT_CONCURRENCY": 15,
        }
    }
}
```
## Run migrations to create the `oban_jobs` table

```shell
uv run manage.py migrate
```

## 📝 Usage (Django 6 Tasks API)

### 🔁 Sync WSGI

```python
from django.tasks import task
from datetime import timedelta

@task()
def process_order(order_id):
    pass

# simple enqueue
process_order.enqueue(order_id=123)

# scheduled
process_order.using(run_after=timedelta(minutes=5)).enqueue(order_id=123)

process_order.using(queue="heavy_reports").enqueue(order_id=123)
```

### 🔀 Assync (ASGI/Ninja/FastAPI)
```python

@task()
async def process_data(data):
    pass

await process_data.aenqueue(data={...})
```

---
## 💎 Advanced Features

### 🛡️ Unique Jobs (Oban Enterprise Compatible)
Prevent duplicate jobs from cluttering your queue. `django-tasks-oban` generates a deterministic SHA256 `unique_key` 
based on the worker name and arguments, fully compatible with the Oban Elixir/Pro schema.

```python
from django_tasks_oban.decorators import oban_task

@oban_task(
    unique={"period": 300, "states": ["available", "scheduled"]},
    priority=10
)
def generate_report(user_id):
    pass
```

### 🗓️ Cron & Recurrence Metadata
Easily tag jobs for recurrent execution. While this package is a Producer, it injects the necessary cron and 
cron_expr metadata so your Oban workers (Python or Elixir) can manage recurrence windows.

```python
@oban_task(cron="*/5 * * * *", tags=["cleanup", "daily"])
def nightly_cleanup():
    pass
```
### 🛠️ Extensible Metadata
Since Django 6 Task objects are immutable (frozen=True), we use a WeakKeyDictionary registry to attach 
unlimited custom metadata to your tasks without hacking the Django core.

```python
@oban_task(custom_id="ABC-123", internal_trace_id="xyz-789")
def trace_task():
    pass
# These will be automatically injected into the Oban 'meta' JSONB column.
```

### Interoperability with Elixir Workers
When using django-tasks-oban as a producer for Elixir-based Oban workers, the unique_key generated follows the standard SHA256 format. 
Ensure your Elixir workers are configured to listen for the keys provided in the meta column.


## 📊 Test Coverage
We take reliability seriously. Our core modules maintain 100% coverage:

|Module|Stmts|Miss|Branch|Cover|
|---|---|---|---|---|
|src/django_tasks_oban/backends.py|39|0|6|100%|
|src/django_tasks_oban/decorators.py|14|0|0|100%|
|src/django_tasks_oban/engine.py|3|0|0|100%|
|src/django_tasks_oban/models.py|33|0|0|100%|

## 🤝 Contributing

Clone the repo.
Ensure you have Python **3.13** and **PostgreSQL**.

Install dev dependencies: `uv sync --dev`.

Run tests: `uv run python manage.py test tests -v 2`.


## 📄 Licença

MIT License. See `LICENSE` for details.

Build with ❤️ and ☕


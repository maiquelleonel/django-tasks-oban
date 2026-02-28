# 🐘 django-tasks-oban 🚀

[![CI](https://github.com)](https://github.com)
[![Python versions](https://img.shields.io)](https://www.python.org)
[![Django versions](https://img.shields.io)](https://docs.djangoproject.com)
[![Coverage Status](https://img.shields.io)](#-test-coverage)
[![License: MIT](https://img.shields.io)](https://opensource.org)

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

### Sync WSGI

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

### Assync (ASGI/Ninja/FastAPI)
```python

@task()
async def process_data(data):
    pass

await process_data.aenqueue(data={...})
```

## 📊 Test Coverage
We take reliability seriously. Our core modules maintain 100% coverage:

|Module|Stmts|Miss|Branch|Cover|
|---|---|---|---|---|
|backends.py|39|0|6|100%|
|engine.py|3|0|0|100%|
|models.py|33|0|0|100%|

## 🤝 Contributing

Clone the repo.
Ensure you have Python **3.13** and **PostgreSQL**.

Install dev dependencies: `uv sync --dev`.

Run tests: `uv run python manage.py test tests -v 2`.


## 📄 Licença

MIT License. See `LICENSE` for details.

Build with ❤️ and ☕

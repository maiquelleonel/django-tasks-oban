# 🐘 django-tasks-oban 🚀

[![Python versions](https://img.shields.io)](https://pypi.org)
[![Django versions](https://img.shields.io)](https://pypi.org)
[![Coverage Status](https://img.shields.io)](#-test-coverage)
[![License: MIT](https://img.shields.io)](https://opensource.org)

**A reliable, transactional, and PostgreSQL-native background job runner for Django 6.0+, powered by [Oban.py](https://github.com).**

---

## ✨ Por que o django-tasks-oban?

O **Oban** utiliza o seu próprio banco de dados PostgreSQL como fila, eliminando a necessidade de Redis ou RabbitMQ. Esta implementação para Django 6 traz:

*   **📦 Consistência Transacional (Sync/Async)**: Enfileire tarefas dentro da mesma transação do banco. Se o `commit` falhar, a tarefa não é criada.
*   **⚡ Injeção de Dependência (DI)**: Suporte nativo para `enqueue` (Sync) e `aenqueue` (Async) usando `create` e `acreate` do Django 6.
*   **🕒 Agendamento Preciso**: Suporte total à sugar syntax `.using(run_after=...)` do Django.
*   **🛠️ 100% Code Coverage**: Código testado exaustivamente, do backend ao worker.
*   **🌍 Compatibilidade Elixir**: Estrutura de tabela idêntica ao [Oban Elixir](https://github.com).

---

## 🛠 Instalação

Otimizado para o moderno gerenciador de pacotes **uv**:

```bash
uv add "django-tasks-oban @ git+https://github.com"
```

---
## ⚙️ Configuração

Adicione ao seu INSTALLED_APPS (O django.contrib.postgres é obrigatório):

```python
# no settings.py

INSTALLED_APPS = [
    ...,
    "django.contrib.postgres",
    "django_tasks_oban",
]

TASKS = {
    "default": {
        "BACKEND": "django_tasks_oban.backends.ObanTaskBackend",
        "OPTIONS": {
            "QUEUE": "default",                # Fila padrão
            "DEFAULT_CONCURRENCY": 15,         # Concorrência se não especificada
            "QUEUES": {                        # Definição de filas e limites
                "default": 10,
                "mail": 5,
                "heavy_reports": 2
            },
            "POOL": {                          # Configurações do Pool de Conexões Async
                "min_size": 1,
                "max_size": 20
            }
        }
    }
}
```

```shell
uv run manage.py migrate
```


## 🏃‍♂️ Rodando o Worker
O worker é um comando de gerenciamento assíncrono que suporta escalas flexíveis:

```shell 
# Roda as filas configuradas no settings
uv run manage.py oban_worker

# Sobrescreve as filas via CLI (específico para este nó)
uv run manage.py oban_worker --queues high_priority:20,default,mail:5
```

## 📝 Uso (Django 6 Tasks API)

### Sincrono WSGI

```python
from django.tasks import task
from datetime import timedelta

@task()
def process_order(order_id):
    pass

process_order.enqueue(order_id=123)

process_order.using(run_after=timedelta(minutes=5)).enqueue(order_id=123)

process_order.using(queue="heavy_reports").enqueue(order_id=123)
```

### Assíncrono (ASGI/Ninja/FastAPI)
```python

@task()
async def process_data(data):
    pass

await process_data.aenqueue(data={...})
```

## 📊 Test Coverage
Levamos a qualidade a sério. Nossos backends e modelos possuem cobertura total:

| Name | Stmts | Miss | Cover |
|---|---|---|---|
|backends.py | 39 | 0 | 100%|
|engine.py | 3 | 0| 100%|
|models.py | 33 | 0 | 100%|
|TOTAL | 75 | 0 | 100%|

## 🤝 Contribuição

1. Clone o repositório.
2. Certifique-se de ter o **Python 3.13** e **PostgreSQL**.
3. Instale as dependências: uv sync --dev.
4. Rode os testes: uv run python manage.py test tests -v 2.


## 📄 Licença

Distribuído sob a licença MIT. Veja LICENSE para mais informações.

Desenvolvido com ❤️ pela comunidade Python.

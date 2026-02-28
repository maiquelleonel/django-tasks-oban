import asyncpg
from django.core.exceptions import ImproperlyConfigured
from django.db import connections
from oban import Oban


async def get_oban_instance(alias: str = "default", queues: dict = None, pool_options: dict = None):  # pragma: no cover
    db_conf = connections[alias].settings_dict

    if "postgresql" not in db_conf["ENGINE"]:
        raise ImproperlyConfigured("O django-tasks-oban exige PostgreSQL (asyncpg).")

    pool_options = pool_options or {}

    pool = await asyncpg.create_pool(
        database=db_conf["NAME"],
        user=db_conf.get("USER"),
        password=db_conf.get("PASSWORD"),
        host=db_conf.get("HOST"),
        port=db_conf.get("PORT"),
        min_size=pool_options.get("min_size", 1),
        max_size=pool_options.get("max_size", 10),
    )

    return Oban(pool=pool, queues=queues or {"default": 10})

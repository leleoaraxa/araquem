"""Remove todas as chaves de cache para o build/ambiente atual.

Uso:

    python scripts/cache/flush_all.py
"""

import os

from app.cache.rt_cache import RedisCache


def flush_all(build_id: str) -> int:
    cache = RedisCache()
    pattern = f"araquem:{build_id}:*"
    deleted = 0
    for key in cache.raw.scan_iter(pattern):
        deleted += int(cache.delete(key))
    return deleted


def main() -> None:
    build_id = os.getenv("BUILD_ID", "dev")
    deleted = flush_all(build_id)
    print(f"[flush_all] Removidas {deleted} chaves para o prefixo 'araquem:{build_id}'")


if __name__ == "__main__":
    main()

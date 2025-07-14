
"""
Abstraction simple autour de DiskCache avec TTL par clé.
"""
from contextlib import asynccontextmanager
import hashlib, json
from typing import Any, Dict, AsyncIterator
import diskcache as dc
from .settings import CACHE_DIR, DISK_CACHE_SIZE, DEFAULT_TTL
_cache = dc.Cache(directory=CACHE_DIR, size_limit=DISK_CACHE_SIZE, disk_min_file_size=0)

def _make_key(url: str, params: Dict[str, Any] | None) -> str:
    h = hashlib.md5()
    h.update(url.encode())
    if params:
        h.update(json.dumps(params, sort_keys=True).encode())
    return h.hexdigest()

def get(url: str, params: Dict[str, Any] | None = None) -> Any | None:
    key = _make_key(url, params)
    return _cache.get(key, default=None)

def set(url: str, params: Dict[str, Any] | None, value: Any, ttl: int = DEFAULT_TTL):
    key = _make_key(url, params)
    _cache.set(key, value, expire=ttl)

@asynccontextmanager
async def cached_request(
    url: str, params: Dict[str, Any] | None, coro
) -> AsyncIterator[Any]:
    data = get(url, params)
    if data is None:
        data = await coro()
        set(url, params, data)
    yield data

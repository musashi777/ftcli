import asyncio, os, time
from typing import Any, Dict
import httpx
from dotenv import load_dotenv
from .settings import TOKEN_URL

# Charge les variables depuis le fichier .env à la racine du projet
load_dotenv(dotenv_path=".env")

class Auth:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls, *a, **kw):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._client_id = os.getenv("FT_CLIENT_ID")
        self._client_secret = os.getenv("FT_CLIENT_SECRET")

        if not self._client_id or not self._client_secret:
            raise RuntimeError("FT_CLIENT_ID ou FT_CLIENT_SECRET manquant dans .env")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, *_):
        return False

    async def _refresh(self):
        payload = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": "api_offresdemploiv2 o2dsoffre api_labonneboitev2",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                TOKEN_URL,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()

        data = resp.json()
        self._token = data["access_token"]
        self._expires_at = time.time() + data["expires_in"] - 30

    async def get_token(self) -> str:
        async with self._lock:
            if self._token is None or time.time() >= self._expires_at:
                await self._refresh()
            return self._token

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


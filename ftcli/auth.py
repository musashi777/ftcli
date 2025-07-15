import asyncio
import os
import time
import httpx
from dotenv import load_dotenv

# Charge les variables depuis le fichier .env
load_dotenv(dotenv_path=".env")

TOKEN_URL = (
    "https://entreprise.francetravail.fr/connexion/"
    "oauth2/access_token?realm=/partenaire"
)

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
        self._scope = "api_offresdemploiv2 o2dsoffre api_labonneboitev2"

        if not self._client_id or not self._client_secret:
            raise RuntimeError("FT_CLIENT_ID ou FT_CLIENT_SECRET manquant dans .env")

    async def _refresh(self):
        payload = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": self._scope,
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
        self._expires_at = time.time() + data.get("expires_in", 3600) - 60

    async def get_token(self) -> str:
        async with self._lock:
            if self._token is None or time.time() >= self._expires_at:
                await self._refresh()
            return self._token

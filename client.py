"""
Client async pour toutes les APIs France Travail activées.
"""
import asyncio
from typing import Any, Dict, List
import httpx
from auth import Auth
from cache import cached_request
from settings import BASE_URL, RATE_LIMIT_PER_SEC

_semaphore = asyncio.Semaphore(RATE_LIMIT_PER_SEC)

class FTClient:
    def __init__(self):
        self._http = None
        self._auth = None

    async def __aenter__(self):
        self._auth = await Auth().__aenter__()
        token = await self._auth.get_token()
        self._http = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=20.0,
        )
        return self

    async def __aexit__(self, exc_type, *exc):
        if self._http:
            await self._http.aclose()
        if self._auth:
            await self._auth.__aexit__(exc_type, *exc)
        return False

    async def _get_json(
        self, endpoint: str, params: Dict[str, Any] | None = None, ttl: int | None = None
    ):
        url = f"{BASE_URL}{endpoint}"
        async def _fetch():
            async with _semaphore:
                resp = await self._http.get(endpoint, params=params)
                resp.raise_for_status()
                # Sécurisation : vérifier que la réponse n'est pas vide
                if resp.content:
                    return resp.json()
                else:
                    return {}
        async with cached_request(url, params, _fetch) as data:
            return data

    async def search_offres(
        self,
        *,
        mots: str | None = None,
        departement: str | None = None,
        communes: list[str] | None = None,
        distance: int | None = None,
        publieeDepuis: int | None = None,
        **extra,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if mots:
            params["motsCles"] = mots
        if departement:
            params["departement"] = departement
        if communes and len(communes) > 0:
            # API attend 'commune' (pas 'communes') : on prend le premier élément
            params["commune"] = communes[0]
        if distance is not None:
            params["distance"] = distance
        if publieeDepuis:
            params["publieeDepuis"] = publieeDepuis
        params.update(extra)
        try:
            data = await self._get_json("/offresdemploi/v2/offres/search", params)
        except Exception as e:
            print(f"Erreur lors de la requête API France Travail : {e}")
            data = {}
        # Pour debug : affiche les params envoyés
        # print(">>> DEBUG params envoyés à l’API :", params)
        return data.get("resultats", [])

    async def get_offre(self, offre_id: str) -> Dict[str, Any]:
        return await self._get_json(f"/offresdemploi/v2/offres/{offre_id}")

    async def referentiel_rome(self, code_rome: str):
        return await self._get_json(f"/referentielRome/v1/metiers/{code_rome}")

import httpx
import diskcache
import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv
from .auth import Auth

load_dotenv()

class FTClient:
    """Client pour interagir avec les API France Travail."""

    def __init__(self):
        self.auth = Auth()
        self.cache = diskcache.Cache("ft_cache")
        self.offres_url = "https://api.francetravail.io/partenaire/offresdemploi/v2"
        self.lbb_url = "https://api.francetravail.io/partenaire/labonneboite/v2"

    async def get_potential_companies(
        self,
        job_label: str,
        location_label: str,
    ) -> List[Dict]:
        """Récupère les entreprises à fort potentiel via l'API La Bonne Boite avec une recherche textuelle."""
        token = await self.auth.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        params = {
            "job": job_label,
            "location": location_label,
            "distance": 20,
            "sort": "score"
        }
        cache_key = f"lbb_{json.dumps(params, sort_keys=True)}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.lbb_url}/recherche",
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            companies = response.json().get("items", [])
            self.cache[cache_key] = companies
            return companies

    async def search_offres(
        self,
        mots: Optional[str] = None,
        departement: Optional[str] = None,
        commune: Optional[str] = None,
        max_results: int = 15,
        typeContrat: Optional[str] = None,
    ) -> List[Dict]:
        """Recherche des offres d'emploi avec des filtres."""
        token = await self.auth.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        params = {}

        if mots: params["motsCles"] = mots
        if departement: params["departement"] = departement
        if commune: params["commune"] = commune
        if typeContrat: params["typeContrat"] = typeContrat
        params["range"] = f"0-{max_results - 1}"

        cache_key = json.dumps(params, sort_keys=True)
        if cache_key in self.cache: return self.cache[cache_key]

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.offres_url}/offres/search",
                headers=headers, params=params, timeout=30
            )
            response.raise_for_status()
            offres = response.json().get("resultats", [])
            self.cache[cache_key] = offres
            return offres

    async def get_offre(self, offre_id: str) -> Dict:
        """Récupère les détails d'une offre spécifique."""
        token = await self.auth.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        cache_key = f"offre_{offre_id}"
        if cache_key in self.cache: return self.cache[cache_key]

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.offres_url}/offres/{offre_id}",
                headers=headers, timeout=30
            )
            response.raise_for_status()
            offre = response.json()
            self.cache[cache_key] = offre
            return offre

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.cache.close()

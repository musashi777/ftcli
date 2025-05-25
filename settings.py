
"""
Paramètres globaux de ftcli, regroupés ici pour être modifiables sans toucher au reste du code.
"""
from pathlib import Path
import os
APP_DIR = Path(os.environ.get("FTCLI_HOME", Path.home() / ".ftcli")).expanduser()
APP_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = APP_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)
BASE_URL = "https://api.francetravail.io/partenaire"
TOKEN_URL = (
    "https://entreprise.francetravail.fr/connexion/"
    "oauth2/access_token?realm=/partenaire"
)
RATE_LIMIT_PER_SEC = int(os.getenv("FTCLI_RATE_LIMIT", "10"))
DEFAULT_TTL = 60 * 45
DISK_CACHE_SIZE = 1024 * 1024 * 256
SECRETS_FILE = APP_DIR / "secrets.enc"

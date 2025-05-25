#!/bin/bash
# --- Variables à adapter si besoin
CLIENT_ID="PAR_jobsearch_a1c457aabf2681ceb1da9da029d391432f898d2eef034b512eb64e1593ba629d"
CLIENT_SECRET="2e37dc339fd06ac8160041a9af1154e37e0aff4700d5b637b6d8acbf2449ed9b"
SCOPE="api_openformationv1"

if [ $# -lt 3 ]; then
  echo "Usage : $0 \"mot clé formation\" code_postal rayon_km"
  exit 1
fi

MOT_CLE="$1"
CODE_POSTAL="$2"
RADIUS="$3"

# 1. Obtenir le token OAuth2
TOKEN_RESPONSE=$(curl -s -X POST "https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$CLIENT_ID&client_secret=$CLIENT_SECRET&scope=$SCOPE")

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')
if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" == "null" ]; then
    echo "[ERREUR] Impossible de récupérer le token !"
    echo "$TOKEN_RESPONSE"
    exit 1
fi
echo "[OK] Token récupéré."

# 2. Recherche formation
RESULTS=$(curl -s -X GET "https://api.francetravail.io/partenaire/openformation/v1/catalogue?codePostal=$CODE_POSTAL&radius=$RADIUS&motCle=$MOT_CLE" \
  -H "Authorization: Bearer $ACCESS_TOKEN" -H "Accept: application/json")

echo "$RESULTS" | jq '.formations[] | {titre: .intitule, organisme: .organismeFormation.raisonSociale, ville: .lieuFormation.ville, sessions: .sessions}'

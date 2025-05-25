#!/bin/bash
pkg install -y jq > /dev/null

# === IDENTIFIANTS ===
CLIENT_ID="PAR_jobsearch_a1c457aabf2681ceb1da9da029d391432f898d2eef034b512eb64e1593ba629d"
CLIENT_SECRET="2e37dc339fd06ac8160041a9af1154e37e0aff4700d5b637b6d8acbf2449ed9b"
SCOPE="api_openformationv1"

# === PARAMÈTRES DE RECHERCHE ===
MOTS_CLE="technicien assistant informatique"
CODE_POSTAL="13006"
RADIUS="20"

# === 1. OBTENIR LE TOKEN ===
TOKEN_RESPONSE=$(curl -s -X POST "https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$CLIENT_ID&client_secret=$CLIENT_SECRET&scope=$SCOPE")

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
  echo "[ERREUR] Impossible de récupérer le token !"
  echo "$TOKEN_RESPONSE"
  exit 1
fi

echo "[OK] Token récupéré."

# === 2. RECHERCHE DE FORMATION ===
RESPONSE=$(curl -s -X GET "https://api.francetravail.io/partenaire/openformation/v1/catalogue?motCle=$(echo $MOTS_CLE | jq -sRr @uri)&codePostal=$CODE_POSTAL&radius=$RADIUS" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Accept: application/json")

echo "$RESPONSE" | jq '.formations[] | {
  intitule,
  organisme: .organismeFormation?.nom,
  commune: .organismeFormation?.adresse?.commune,
  dateDebut: .sessions[0]?.dateDebut,
  numeroSession: .sessions[0]?.numeroSession
}'

#!/bin/sh
# Fills a FRESH local install with demo data: an admin, two units, four users, and a
# few meetings (including one invitation). For local testing only — never run this
# against a real deployment.
#
#   ./scripts/seed-demo.sh [API_BASE]      default: http://localhost:4100/api/v1
#
# Every demo account uses the password below.
set -e
API=${1:-http://localhost:4100/api/v1}
PASSWORD="situng-demo-123"

json() { curl -sf -H 'Content-Type: application/json' "$@"; }
token() { json -X POST "$API/auth/login" -d "{\"email\":\"$1\",\"password\":\"$PASSWORD\"}" | sed 's/.*"access_token":"\([^"]*\)".*/\1/'; }
id_of() { sed 's/^{"id":\([0-9]*\).*/\1/'; }

json -X POST "$API/auth/register" -d "{\"email\":\"admin@situng.go.id\",\"full_name\":\"Admin SITUNG\",\"password\":\"$PASSWORD\"}" >/dev/null
ADMIN=$(token admin@situng.go.id)

U1=$(json -H "Authorization: Bearer $ADMIN" -X POST "$API/units" -d '{"name":"Biro Perencanaan","code":"RENC"}' | id_of)
U2=$(json -H "Authorization: Bearer $ADMIN" -X POST "$API/units" -d '{"name":"Biro Hukum","code":"HKM"}' | id_of)

user() {
	json -H "Authorization: Bearer $ADMIN" -X POST "$API/users" \
		-d "{\"email\":\"$1\",\"full_name\":\"$2\",\"position\":\"$3\",\"unit_id\":$4,\"password\":\"$PASSWORD\"}" | id_of
}
ANI=$(user ani@situng.go.id "Ani Wijaya" "Kepala Bagian Program" "$U1")
BUDI=$(user budi@situng.go.id "Budi Santoso" "Analis Perencanaan" "$U1")
CICI=$(user cici@situng.go.id "Cici Rahma" "Analis Hukum" "$U2")
DEDI=$(user dedi@situng.go.id "Dedi Pratama" "Kepala Bagian Peraturan" "$U2")

# The demo organisation sits in Jakarta: its meetings are written as WIB (+07:00)
# instants, and "today" is today there, not on whatever clock this machine runs.
TODAY=$(TZ=Asia/Jakarta date +%Y-%m-%d)
TOMORROW=$(TZ=Asia/Jakarta date -v+1d +%Y-%m-%d 2>/dev/null || TZ=Asia/Jakarta date -d tomorrow +%Y-%m-%d)

T_BUDI=$(token budi@situng.go.id)
json -H "Authorization: Bearer $T_BUDI" -X POST "$API/meetings" \
	-d "{\"title\":\"Rakor Anggaran Triwulan\",\"timezone\":\"Asia/Jakarta\",\"scheduled_start\":\"${TOMORROW}T09:00+07:00\",\"scheduled_end\":\"${TOMORROW}T11:00+07:00\",\"location_type\":\"offline\",\"location_place\":\"Ruang Rapat Lt. 3\",\"location_city\":\"Jakarta Pusat\",\"categories\":[\"rakor\"]}" >/dev/null

T_CICI=$(token cici@situng.go.id)
json -H "Authorization: Bearer $T_CICI" -X POST "$API/meetings" \
	-d "{\"title\":\"Harmonisasi Rancangan Peraturan\",\"timezone\":\"Asia/Jakarta\",\"scheduled_start\":\"${TOMORROW}T13:00+07:00\",\"scheduled_end\":\"${TOMORROW}T15:00+07:00\",\"categories\":[\"harmonisasi\"],\"invitee_ids\":[$ANI]}" >/dev/null

T_ANI=$(token ani@situng.go.id)
json -H "Authorization: Bearer $T_ANI" -X POST "$API/meetings" \
	-d "{\"title\":\"Coffee morning tim program\",\"timezone\":\"Asia/Jakarta\",\"scheduled_start\":\"${TODAY}T16:00+07:00\",\"scheduled_end\":\"${TODAY}T17:00+07:00\",\"is_formal\":false}" >/dev/null

echo "Seeded. Log in at the frontend with any of:"
echo "  admin@situng.go.id (administrator), ani@, budi@, cici@, dedi@situng.go.id"
echo "  password: $PASSWORD"

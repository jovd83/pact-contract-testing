#!/usr/bin/env bash
# Provision a self-hosted Pact Broker via Docker when you don't already have one.
# Idempotent: starts assets/broker/docker-compose.yml and waits until healthy.
#
# Use a broker you ALREADY have instead of this if one exists (PactFlow or org broker) —
# just set PACT_BROKER_BASE_URL/token and skip this script.
#
# Override defaults via env before running: PACT_BROKER_PORT, PACT_BROKER_USERNAME,
# PACT_BROKER_PASSWORD (see assets/broker/README.md).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/../assets/broker/docker-compose.yml"
PORT="${PACT_BROKER_PORT:-9292}"
USER="${PACT_BROKER_USERNAME:-pact}"
PASS="${PACT_BROKER_PASSWORD:-pact}"
BASE_URL="http://localhost:${PORT}"

[[ -f "$COMPOSE_FILE" ]] || { echo "FAIL: $COMPOSE_FILE not found"; exit 2; }
command -v docker >/dev/null || { echo "FAIL: docker not installed/in PATH"; exit 2; }

# Pick `docker compose` (v2) or fall back to `docker-compose` (v1).
if docker compose version >/dev/null 2>&1; then COMPOSE=(docker compose); else COMPOSE=(docker-compose); fi

echo "Starting Pact Broker via $COMPOSE_FILE ..."
"${COMPOSE[@]}" -f "$COMPOSE_FILE" up -d

echo -n "Waiting for broker heartbeat at ${BASE_URL} "
HEARTBEAT="${BASE_URL}/diagnostic/status/heartbeat"
for _ in $(seq 1 60); do
  if curl -fsS -u "${USER}:${PASS}" "$HEARTBEAT" >/dev/null 2>&1; then
    echo " OK"
    cat <<EOF

Pact Broker is up: ${BASE_URL}  (UI in a browser, basic auth ${USER} / ${PASS})

Point the skill at it:
  export PACT_BROKER_BASE_URL=${BASE_URL}
  export PACT_BROKER_USERNAME=${USER}
  export PACT_BROKER_PASSWORD=${PASS}

Stop (keep data):  ${COMPOSE[*]} -f $COMPOSE_FILE down
Stop + wipe data:  ${COMPOSE[*]} -f $COMPOSE_FILE down -v
EOF
    exit 0
  fi
  echo -n "."
  sleep 2
done

echo " TIMEOUT"
echo "FAIL: broker did not become healthy. Check logs: ${COMPOSE[*]} -f $COMPOSE_FILE logs broker"
exit 1

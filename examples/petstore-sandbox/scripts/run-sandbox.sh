#!/usr/bin/env bash
# End-to-end Petstore contract-testing sandbox: runs all 4 iterations exactly as
# documented in docs/ITERATIONS.md. Designed for Git Bash on Windows + Docker Desktop.
#
# Prereqs: docker, node, java+maven on PATH. Python and Go run inside containers.
set -uo pipefail

SB="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SB"
export NODE_PATH="$SB/provider/node_modules"
BROKER="http://localhost:9292"
BU_IN_DOCKER="http://host.docker.internal:9292"
AUTH="--broker-base-url $BU_IN_DOCKER --broker-username pact --broker-password pact"
PACTCLI="pactfoundation/pact-cli:latest"

step() { echo; echo "==================== $* ===================="; }

# ---------------------------------------------------------------------------
step "0. Broker up + provider up"
docker compose up -d
until [ "$(curl -s -o /dev/null -w '%{http_code}' -u pact:pact $BROKER/)" = "200" ]; do sleep 2; done
( cd provider && npm install --no-fund --no-audit >/dev/null 2>&1 )
PORT=8082 node provider/server.js & PROV_PID=$!
PORT=8083 PROVIDER_BREAKING=1 node provider/server.js & PROV_BREAK_PID=$!
sleep 2
trap 'kill $PROV_PID $PROV_BREAK_PID 2>/dev/null' EXIT

# ---------------------------------------------------------------------------
step "ITERATION 1 — consumer tests vs MOCK, then publish pacts to broker"
node consumers/javascript/pactConsumer.js
( cd consumers/java && mvn -q -B test ) && cp consumers/java/target/pacts/JavaPetClient-PetstoreProvider.json pacts/
MSYS_NO_PATHCONV=1 docker run --rm -v "$SB:/work" -w /work/consumers/python python:3.12-slim \
  bash -c "pip install -q 'pact-python>=2.2' 2>/dev/null && python pact_consumer.py"
MSYS_NO_PATHCONV=1 docker run --rm -v "$SB:/work" -w /work/consumers/go -e GOFLAGS=-mod=mod golang:1.22-bookworm \
  bash -c 'go mod tidy >/dev/null 2>&1; go run github.com/pact-foundation/pact-go/v2 install --libDir /usr/local/lib >/dev/null 2>&1; LD_LIBRARY_PATH=/usr/local/lib go test -count=1 ./...'
for c in JsPetClient JavaPetClient PythonPetClient GoPetClient; do
  node scripts/publish-pact.js "pacts/${c}-PetstoreProvider.json" 1.0.0-iter1 main
done

step "ITERATION 1b — broker stub server demo (canned responses, no real provider)"
docker rm -f petstore-stub >/dev/null 2>&1
MSYS_NO_PATHCONV=1 docker run -d --name petstore-stub -p 9999:8080 -v "$SB/pacts:/pacts" \
  pactfoundation/pact-stub-server:latest -d /pacts -p 8080 >/dev/null
sleep 4; echo "stub GET /api/v3/pet/1 ->"; curl -s http://localhost:9999/api/v3/pet/1; echo
docker rm -f petstore-stub >/dev/null 2>&1

# ---------------------------------------------------------------------------
step "ITERATION 2 — provider verification replays the STORED pacts (expect all PASS)"
PROVIDER_BASE_URL=http://localhost:8082 PROVIDER_VERSION=prov-1.0.0-iter2 node provider/verify.js

# ---------------------------------------------------------------------------
step "ITERATION 3 — a 5th consumer that MISINTERPRETED the contract"
node consumers/javascript-bad/badConsumer.js
node scripts/publish-pact.js pacts/BadPetClient-PetstoreProvider.json 0.1.0-iter3 main
echo "(re-verify: bad consumer FAILS but is PENDING, so the build stays green)"
PROVIDER_BASE_URL=http://localhost:8082 PROVIDER_VERSION=prov-1.0.0-iter3 node provider/verify.js

step "Record production deployments + safe can-i-deploy"
MSYS_NO_PATHCONV=1 docker run --rm --entrypoint sh $PACTCLI -c "
  pact-broker record-deployment --pacticipant PetstoreProvider --version prov-1.0.0-iter3 --environment production $AUTH
  pact-broker record-deployment --pacticipant JsPetClient     --version 1.0.0-iter1 --environment production $AUTH
  pact-broker record-deployment --pacticipant JavaPetClient   --version 1.0.0-iter1 --environment production $AUTH
  pact-broker record-deployment --pacticipant PythonPetClient --version 1.0.0-iter1 --environment production $AUTH
  pact-broker record-deployment --pacticipant GoPetClient     --version 1.0.0-iter1 --environment production $AUTH
  pact-broker can-i-deploy --pacticipant PetstoreProvider --version prov-1.0.0-iter3 --to-environment production $AUTH
"

# ---------------------------------------------------------------------------
step "ITERATION 4 — provider introduces a BREAKING change (status -> availability)"
echo "(verify breaking provider on :8083 — expect HARD FAIL)"
PROVIDER_BASE_URL=http://localhost:8083 PROVIDER_VERSION=prov-2.0.0-breaking node provider/verify.js
echo "(can-i-deploy the breaking provider to production — expect BLOCKED)"
MSYS_NO_PATHCONV=1 docker run --rm --entrypoint sh $PACTCLI -c "
  pact-broker can-i-deploy --pacticipant PetstoreProvider --version prov-2.0.0-breaking --to-environment production $AUTH
"

step "DONE — open the broker UI at $BROKER (pact/pact). Teardown: docker compose down -v"

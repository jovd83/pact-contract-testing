#!/usr/bin/env bash
# Publish pact files to the broker with version=git SHA and branch=current branch.
# Requires the pact-broker CLI (pact_broker-client / Docker pactfoundation/pact-cli).
#
# Env: PACT_BROKER_BASE_URL (required), PACT_BROKER_TOKEN or PACT_BROKER_USERNAME/PASSWORD.
# Usage: ./publish_pacts.sh [PACTS_DIR]   (default PACTS_DIR=./pacts ./build/pacts ./target/pacts)
set -euo pipefail

PACTS_DIR="${1:-}"
if [[ -z "$PACTS_DIR" ]]; then
  for d in ./pacts ./build/pacts ./target/pacts; do
    [[ -d "$d" ]] && PACTS_DIR="$d" && break
  done
fi
[[ -z "${PACTS_DIR:-}" || ! -d "$PACTS_DIR" ]] && { echo "FAIL: pacts dir not found (pass it as arg)"; exit 2; }
[[ -z "${PACT_BROKER_BASE_URL:-}" ]] && { echo "FAIL: PACT_BROKER_BASE_URL not set"; exit 2; }

VERSION="$(git rev-parse --short HEAD)"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"

AUTH=()
if [[ -n "${PACT_BROKER_TOKEN:-}" ]]; then
  AUTH=(--broker-token "$PACT_BROKER_TOKEN")
elif [[ -n "${PACT_BROKER_USERNAME:-}" ]]; then
  AUTH=(--broker-username "$PACT_BROKER_USERNAME" --broker-password "${PACT_BROKER_PASSWORD:-}")
fi

echo "Publishing $PACTS_DIR  version=$VERSION  branch=$BRANCH"
pact-broker publish "$PACTS_DIR" \
  --consumer-app-version "$VERSION" \
  --branch "$BRANCH" \
  --broker-base-url "$PACT_BROKER_BASE_URL" \
  "${AUTH[@]}"

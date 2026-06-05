#!/usr/bin/env bash
# Deploy gate: ask the broker whether a pacticipant version is safe to deploy.
# Exit 0 = safe, 1 = blocked.
#
# Env: PACT_BROKER_BASE_URL (required), PACT_BROKER_TOKEN or PACT_BROKER_USERNAME/PASSWORD.
# Usage: ./can_i_deploy.sh --pacticipant Foo [--version <sha>] --to-environment production
set -euo pipefail

PACTICIPANT="" ; VERSION="" ; ENVIRONMENT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --pacticipant) PACTICIPANT="$2"; shift 2;;
    --version) VERSION="$2"; shift 2;;
    --to-environment) ENVIRONMENT="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 2;;
  esac
done

[[ -z "$PACTICIPANT" ]] && { echo "FAIL: --pacticipant required"; exit 2; }
[[ -z "$ENVIRONMENT" ]] && { echo "FAIL: --to-environment required"; exit 2; }
[[ -z "${PACT_BROKER_BASE_URL:-}" ]] && { echo "FAIL: PACT_BROKER_BASE_URL not set"; exit 2; }
[[ -z "$VERSION" ]] && VERSION="$(git rev-parse --short HEAD)"

AUTH=()
if [[ -n "${PACT_BROKER_TOKEN:-}" ]]; then
  AUTH=(--broker-token "$PACT_BROKER_TOKEN")
elif [[ -n "${PACT_BROKER_USERNAME:-}" ]]; then
  AUTH=(--broker-username "$PACT_BROKER_USERNAME" --broker-password "${PACT_BROKER_PASSWORD:-}")
fi

echo "can-i-deploy: $PACTICIPANT@$VERSION -> $ENVIRONMENT"
pact-broker can-i-deploy \
  --pacticipant "$PACTICIPANT" \
  --version "$VERSION" \
  --to-environment "$ENVIRONMENT" \
  --broker-base-url "$PACT_BROKER_BASE_URL" \
  "${AUTH[@]}"

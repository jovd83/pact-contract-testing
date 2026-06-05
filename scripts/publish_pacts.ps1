<#
.SYNOPSIS
  Publish pact files to the broker with version=git SHA and branch=current branch.
.DESCRIPTION
  Requires the pact-broker CLI (pact_broker-client / Docker pactfoundation/pact-cli).
  Env: PACT_BROKER_BASE_URL (required), PACT_BROKER_TOKEN or PACT_BROKER_USERNAME/PASSWORD.
.EXAMPLE
  ./publish_pacts.ps1 -PactsDir ./build/pacts
#>
param([string]$PactsDir)

$ErrorActionPreference = "Stop"

if (-not $PactsDir) {
  foreach ($d in @("./pacts", "./build/pacts", "./target/pacts")) {
    if (Test-Path $d) { $PactsDir = $d; break }
  }
}
if (-not $PactsDir -or -not (Test-Path $PactsDir)) { Write-Error "FAIL: pacts dir not found (pass -PactsDir)"; exit 2 }
if (-not $env:PACT_BROKER_BASE_URL) { Write-Error "FAIL: PACT_BROKER_BASE_URL not set"; exit 2 }

$version = (git rev-parse --short HEAD).Trim()
$branch  = (git rev-parse --abbrev-ref HEAD).Trim()

$auth = @()
if ($env:PACT_BROKER_TOKEN) {
  $auth = @("--broker-token", $env:PACT_BROKER_TOKEN)
} elseif ($env:PACT_BROKER_USERNAME) {
  $auth = @("--broker-username", $env:PACT_BROKER_USERNAME, "--broker-password", $env:PACT_BROKER_PASSWORD)
}

Write-Host "Publishing $PactsDir  version=$version  branch=$branch"
pact-broker publish $PactsDir `
  --consumer-app-version $version `
  --branch $branch `
  --broker-base-url $env:PACT_BROKER_BASE_URL `
  @auth

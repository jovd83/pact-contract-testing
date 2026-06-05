<#
.SYNOPSIS
  Provision a self-hosted Pact Broker via Docker when you don't already have one.
.DESCRIPTION
  Idempotent: starts assets/broker/docker-compose.yml and waits until healthy.
  Use a broker you ALREADY have instead (PactFlow or org broker) if one exists —
  just set PACT_BROKER_BASE_URL/token and skip this script.
  Override defaults via env first: PACT_BROKER_PORT, PACT_BROKER_USERNAME,
  PACT_BROKER_PASSWORD (see assets/broker/README.md).
.EXAMPLE
  ./start_broker.ps1
#>
$ErrorActionPreference = "Stop"

$scriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$composeFile = Join-Path $scriptDir "..\assets\broker\docker-compose.yml"
$port    = if ($env:PACT_BROKER_PORT) { $env:PACT_BROKER_PORT } else { "9292" }
$user    = if ($env:PACT_BROKER_USERNAME) { $env:PACT_BROKER_USERNAME } else { "pact" }
$pass    = if ($env:PACT_BROKER_PASSWORD) { $env:PACT_BROKER_PASSWORD } else { "pact" }
$baseUrl = "http://localhost:$port"

if (-not (Test-Path $composeFile)) { Write-Error "FAIL: $composeFile not found"; exit 2 }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Write-Error "FAIL: docker not installed/in PATH"; exit 2 }

Write-Host "Starting Pact Broker via $composeFile ..."
docker compose -f $composeFile up -d

Write-Host -NoNewline "Waiting for broker heartbeat at $baseUrl "
$heartbeat = "$baseUrl/diagnostic/status/heartbeat"
$cred = [pscredential]::new($user, (ConvertTo-SecureString $pass -AsPlainText -Force))
for ($i = 0; $i -lt 60; $i++) {
  try {
    Invoke-WebRequest -Uri $heartbeat -Credential $cred -UseBasicParsing -TimeoutSec 3 | Out-Null
    Write-Host " OK"
    Write-Host ""
    Write-Host "Pact Broker is up: $baseUrl  (UI in a browser, basic auth $user / $pass)"
    Write-Host ""
    Write-Host "Point the skill at it:"
    Write-Host "  `$env:PACT_BROKER_BASE_URL = '$baseUrl'"
    Write-Host "  `$env:PACT_BROKER_USERNAME = '$user'"
    Write-Host "  `$env:PACT_BROKER_PASSWORD = '$pass'"
    Write-Host ""
    Write-Host "Stop (keep data):  docker compose -f $composeFile down"
    Write-Host "Stop + wipe data:  docker compose -f $composeFile down -v"
    exit 0
  } catch {
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 2
  }
}

Write-Host " TIMEOUT"
Write-Error "FAIL: broker did not become healthy. Check logs: docker compose -f $composeFile logs broker"
exit 1

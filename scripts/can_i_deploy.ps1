<#
.SYNOPSIS
  Deploy gate: ask the broker whether a pacticipant version is safe to deploy.
.DESCRIPTION
  Exit 0 = safe, 1 = blocked. Env: PACT_BROKER_BASE_URL (required),
  PACT_BROKER_TOKEN or PACT_BROKER_USERNAME/PASSWORD.
.EXAMPLE
  ./can_i_deploy.ps1 -Pacticipant Foo -ToEnvironment production
#>
param(
  [Parameter(Mandatory = $true)][string]$Pacticipant,
  [string]$Version,
  [Parameter(Mandatory = $true)][string]$ToEnvironment
)

$ErrorActionPreference = "Stop"

if (-not $env:PACT_BROKER_BASE_URL) { Write-Error "FAIL: PACT_BROKER_BASE_URL not set"; exit 2 }
if (-not $Version) { $Version = (git rev-parse --short HEAD).Trim() }

$auth = @()
if ($env:PACT_BROKER_TOKEN) {
  $auth = @("--broker-token", $env:PACT_BROKER_TOKEN)
} elseif ($env:PACT_BROKER_USERNAME) {
  $auth = @("--broker-username", $env:PACT_BROKER_USERNAME, "--broker-password", $env:PACT_BROKER_PASSWORD)
}

Write-Host "can-i-deploy: $Pacticipant@$Version -> $ToEnvironment"
pact-broker can-i-deploy `
  --pacticipant $Pacticipant `
  --version $Version `
  --to-environment $ToEnvironment `
  --broker-base-url $env:PACT_BROKER_BASE_URL `
  @auth

# Setup script for speckit-plan
# Detects current spec and sets up plan environment

param(
    [switch]$Json,
    [string]$Feature
)

# Detect repository root
$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) {
    $repoRoot = Get-Location
}

$specsDir = Join-Path $repoRoot "specs/features"

# Auto-detect feature from git branch or use provided
$featureId = $Feature
if (-not $featureId) {
    $branchName = git rev-parse --abbrev-ref HEAD 2>$null
    if ($branchName -match 'feature/(\d+)') {
        $featureId = $matches[1]
    }
}

# Default to 000 if not detected
if (-not $featureId) {
    $featureId = "000"
}

# Find feature spec file
$featureSpec = Join-Path $specsDir "${featureId}-domain-contracts.md"
if (-not (Test-Path $featureSpec)) {
    $found = Get-ChildItem -Path $specsDir -Filter "${featureId}-*.md" | Select-Object -First 1
    if ($found) {
        $featureSpec = $found.FullName
    }
}

# Set plan output path
$planId = Get-Date -Format "yyyyMMdd-HHmmss"
$plansDir = Join-Path $repoRoot ".specify/plans"
$implPlan = Join-Path $plansDir "${featureId}-${planId}-plan.md"

# Ensure directories exist
$planDir = Split-Path -Parent $implPlan
if (-not (Test-Path $planDir)) {
    New-Item -ItemType Directory -Path $planDir -Force | Out-Null
}

# Output
if ($Json) {
    $output = @{
        FEATURE_SPEC = $featureSpec
        IMPL_PLAN = $implPlan
        SPECS_DIR = $specsDir
        BRANCH = $branchName
        PLAN_ID = $planId
    } | ConvertTo-Json
    Write-Output $output
} else {
    Write-Output "Feature Spec: $featureSpec"
    Write-Output "Impl Plan: $implPlan"
    Write-Output "Specs Dir: $specsDir"
    Write-Output "Branch: $branchName"
}

# Setup script for speckit-implement
# Detects current plan and sets up implementation environment

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

# Find the latest plan for this feature
$plansDir = Join-Path $repoRoot ".specify/plans"
$latestPlan = $null
if (Test-Path $plansDir) {
    $planFiles = Get-ChildItem -Path $plansDir -Filter "${featureId}-*-plan.md" | Sort-Object LastWriteTime -Descending
    if ($planFiles) {
        $latestPlan = $planFiles[0].FullName
    }
}

if (-not $latestPlan) {
    Write-Error "No plan found for feature ${featureId}"
    Write-Error "Run '/speckit-plan' first to create a plan"
    exit 1
}

# Find feature spec
$featureSpec = Join-Path $specsDir "${featureId}-domain-contracts.md"
if (-not (Test-Path $featureSpec)) {
    $found = Get-ChildItem -Path $specsDir -Filter "${featureId}-*.md" | Select-Object -First 1
    if ($found) {
        $featureSpec = $found.FullName
    }
}

# Set tasks file path
$tasksFile = Join-Path $repoRoot ".specify/tasks/${featureId}-tasks.md"

# Output
if ($Json) {
    $output = @{
        FEATURE_SPEC = $featureSpec
        IMPL_PLAN = $latestPlan
        TASKS_FILE = $tasksFile
        SPECS_DIR = $specsDir
        BRANCH = $branchName
    } | ConvertTo-Json
    Write-Output $output
} else {
    Write-Output "Feature Spec: $featureSpec"
    Write-Output "Impl Plan: $latestPlan"
    Write-Output "Tasks File: $tasksFile"
    Write-Output "Specs Dir: $specsDir"
    Write-Output "Branch: $branchName"
}

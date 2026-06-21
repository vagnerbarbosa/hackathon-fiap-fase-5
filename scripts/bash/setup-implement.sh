#!/bin/bash
# Setup script for speckit-implement
# Detects current plan and sets up implementation environment

set -e

# Parse arguments
JSON_OUTPUT=false
FEATURE_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --feature)
            FEATURE_ID="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Detect repository root
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SPECS_DIR="${REPO_ROOT}/specs/features"

# Auto-detect feature from git branch or use provided
if [ -z "$FEATURE_ID" ]; then
    BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
    # Try to extract feature number from branch name
    if [[ $BRANCH_NAME =~ feature/([0-9]+) ]]; then
        FEATURE_ID="${BASH_REMATCH[1]}"
    fi
fi

# Default to 000 if not detected
if [ -z "$FEATURE_ID" ]; then
    FEATURE_ID="000"
fi

# Find the latest plan for this feature
PLANS_DIR="${REPO_ROOT}/.specify/plans"
LATEST_PLAN=$(find "$PLANS_DIR" -name "${FEATURE_ID}-*-plan.md" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)

if [ -z "$LATEST_PLAN" ]; then
    # No plan found, suggest creating one
    echo "Error: No plan found for feature ${FEATURE_ID}" >&2
    echo "Run '/speckit-plan' first to create a plan" >&2
    exit 1
fi

# Find feature spec
FEATURE_SPEC="${SPECS_DIR}/${FEATURE_ID}-domain-contracts.md"
if [ ! -f "$FEATURE_SPEC" ]; then
    FEATURE_SPEC=$(find "$SPECS_DIR" -name "${FEATURE_ID}-*.md" | head -1)
fi

# Set tasks file path
TASKS_FILE="${REPO_ROOT}/.specify/tasks/${FEATURE_ID}-tasks.md"

# Output JSON if requested
if [ "$JSON_OUTPUT" = true ]; then
    cat <<EOF
{
    "FEATURE_SPEC": "${FEATURE_SPEC}",
    "IMPL_PLAN": "${LATEST_PLAN}",
    "TASKS_FILE": "${TASKS_FILE}",
    "SPECS_DIR": "${SPECS_DIR}",
    "BRANCH": "${BRANCH_NAME:-feature/${FEATURE_ID}-implementation}"
}
EOF
else
    echo "Feature Spec: $FEATURE_SPEC"
    echo "Impl Plan: $LATEST_PLAN"
    echo "Tasks File: $TASKS_FILE"
    echo "Specs Dir: $SPECS_DIR"
    echo "Branch: ${BRANCH_NAME:-feature/${FEATURE_ID}-implementation}"
fi

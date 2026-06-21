#!/bin/bash
# Check prerequisites for speckit commands

set -e

# Parse arguments
JSON_OUTPUT=false
REQUIRE_PLAN=false
REQUIRE_TASKS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --require-plan)
            REQUIRE_PLAN=true
            shift
            ;;
        --require-tasks)
            REQUIRE_TASKS=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Detect repository root
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Check prerequisites
ERRORS=()

if [ ! -d "$REPO_ROOT/.specify" ]; then
    ERRORS+=(".specify directory not found")
fi

if [ ! -f "$REPO_ROOT/.specify/memory/constitution.md" ]; then
    ERRORS+=("constitution.md not found")
fi

if [ "$REQUIRE_PLAN" = true ]; then
    PLANS_DIR="$REPO_ROOT/.specify/plans"
    if [ ! -d "$PLANS_DIR" ] || [ -z "$(ls -A $PLANS_DIR 2>/dev/null)" ]; then
        ERRORS+=("no plans found (run /speckit-plan first)")
    fi
fi

if [ "$REQUIRE_TASKS" = true ]; then
    TASKS_DIR="$REPO_ROOT/.specify/tasks"
    if [ ! -d "$TASKS_DIR" ] || [ -z "$(ls -A $TASKS_DIR 2>/dev/null)" ]; then
        ERRORS+=("no tasks found (run /speckit-plan first)")
    fi
fi

# Output
if [ "$JSON_OUTPUT" = true ]; then
    if [ ${#ERRORS[@]} -eq 0 ]; then
        echo '{"ready": true, "errors": []}'
    else
        echo "{\"ready\": false, \"errors\": [$(printf '\"%s\",' "${ERRORS[@]}" | sed 's/,$//')] }"
    fi
else
    if [ ${#ERRORS[@]} -eq 0 ]; then
        echo "✓ All prerequisites met"
    else
        echo "✗ Prerequisites missing:"
        for error in "${ERRORS[@]}"; do
            echo "  - $error"
        done
        exit 1
    fi
fi

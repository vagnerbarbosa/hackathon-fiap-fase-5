#!/usr/bin/env bash
# =============================================================================
# run_ci_checks.sh — Run the same checks as the GitHub Actions CI pipeline
# locally before pushing or opening a PR.
#
# Usage:
#   ./scripts/run_ci_checks.sh              # Run all checks
#   ./scripts/run_ci_checks.sh --lint       # Lint + type check only
#   ./scripts/run_ci_checks.sh --test       # Tests only
#   ./scripts/run_ci_checks.sh --dataset    # Dataset validation only
#   ./scripts/run_ci_checks.sh --docker     # Docker build + health check only
#   ./scripts/run_ci_checks.sh --fix        # Auto-fix ruff issues then run all
#   ./scripts/run_ci_checks.sh --help       # Show this help message
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_ACTIVATE="$PROJECT_ROOT/.venv/bin/activate"
MIN_TRAIN_IMAGES=70
MIN_VAL_IMAGES=20
COVERAGE_MIN=70

# Colours (disabled if not a terminal)
if [ -t 1 ]; then
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
  BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; BLUE=''; BOLD=''; NC=''
fi

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
step()    { echo -e "\n${BLUE}${BOLD}▶ $*${NC}"; }
success() { echo -e "${GREEN}  ✓ $*${NC}"; }
warning() { echo -e "${YELLOW}  ⚠ $*${NC}"; }
fail()    { echo -e "${RED}  ✗ $*${NC}"; }
info()    { echo -e "  ℹ $*"; }

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

mark_pass() { PASS_COUNT=$((PASS_COUNT + 1)); success "$1"; }
mark_fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); fail "$1"; }
mark_warn() { WARN_COUNT=$((WARN_COUNT + 1)); warning "$1"; }

# ---------------------------------------------------------------------------
# Activate Poetry virtualenv
# ---------------------------------------------------------------------------
activate_venv() {
  if [ -f "$VENV_ACTIVATE" ]; then
    # shellcheck source=/dev/null
    source "$VENV_ACTIVATE"
  elif command -v poetry &>/dev/null; then
    info "No .venv found; running via 'poetry run'"
    POETRY_PREFIX="poetry run"
  else
    echo -e "${RED}ERROR: Neither .venv nor poetry found.${NC}"
    echo "  Install Poetry: https://python-poetry.org/docs/#installation"
    echo "  Then run: poetry install"
    exit 1
  fi
}

run() {
  # Run a command, optionally prefixed with poetry run
  if [ -n "${POETRY_PREFIX:-}" ]; then
    $POETRY_PREFIX "$@"
  else
    "$@"
  fi
}

# ---------------------------------------------------------------------------
# Check: Lint (ruff check)
# ---------------------------------------------------------------------------
check_lint() {
  step "Lint — ruff check src/"
  cd "$PROJECT_ROOT"
  if run ruff check src/; then
    mark_pass "ruff check passed"
  else
    mark_fail "ruff check found errors (run 'ruff check --fix src/' to auto-fix)"
    return 1
  fi
}

# ---------------------------------------------------------------------------
# Check: Format (ruff format)
# ---------------------------------------------------------------------------
check_format() {
  step "Format — ruff format --check src/"
  cd "$PROJECT_ROOT"
  if run ruff format --check src/; then
    mark_pass "ruff format check passed"
  else
    mark_fail "ruff format found unformatted files (run 'ruff format src/' to fix)"
    return 1
  fi
}

# ---------------------------------------------------------------------------
# Auto-fix: ruff lint + format
# ---------------------------------------------------------------------------
autofix() {
  step "Auto-fix — ruff check --fix + ruff format src/"
  cd "$PROJECT_ROOT"
  run ruff check --fix src/ && success "ruff --fix applied"
  run ruff format src/      && success "ruff format applied"
}

# ---------------------------------------------------------------------------
# Check: Type check (mypy)
# ---------------------------------------------------------------------------
check_types() {
  step "Type check — mypy src/"
  cd "$PROJECT_ROOT"
  if run mypy src/; then
    mark_pass "mypy passed"
  else
    mark_fail "mypy found type errors"
    return 1
  fi
}

# ---------------------------------------------------------------------------
# Check: Tests with coverage
# ---------------------------------------------------------------------------
check_tests() {
  step "Tests — pytest tests/ (coverage ≥ ${COVERAGE_MIN}%)"
  cd "$PROJECT_ROOT"

  # Check for running PostgreSQL + Redis (warn if not available)
  if ! command -v docker &>/dev/null; then
    mark_warn "docker not found — integration tests may be skipped"
  else
    if ! docker compose ps db 2>/dev/null | grep -q "running\|Up"; then
      mark_warn "PostgreSQL service not running — start with 'docker compose up -d db redis'"
      info "Integration tests that require the database will be skipped or fail."
    fi
  fi

  if run pytest tests/ \
      --cov=src \
      --cov-report=term-missing \
      --cov-report=html:htmlcov \
      --cov-fail-under="${COVERAGE_MIN}" \
      -v; then
    mark_pass "All tests passed (coverage ≥ ${COVERAGE_MIN}%)"
    info "HTML coverage report: htmlcov/index.html"
  else
    mark_fail "Tests failed or coverage < ${COVERAGE_MIN}%"
    return 1
  fi
}

# ---------------------------------------------------------------------------
# Check: Dataset validation
# ---------------------------------------------------------------------------
check_dataset() {
  step "Dataset validation"
  cd "$PROJECT_ROOT"
  local dataset_ok=true

  # data.yaml
  if [ ! -f "dataset/data.yaml" ]; then
    mark_fail "dataset/data.yaml not found"
    dataset_ok=false
  else
    if python3 -c "
import yaml, sys
with open('dataset/data.yaml') as f:
    data = yaml.safe_load(f)
required = ['nc', 'names']
missing = [k for k in required if k not in data]
if missing:
    print(f'Missing keys: {missing}')
    sys.exit(1)
print(f'nc={data[\"nc\"]}, classes={len(data[\"names\"])}')
" 2>&1; then
      mark_pass "dataset/data.yaml is valid"
    else
      mark_fail "dataset/data.yaml is invalid or missing required keys"
      dataset_ok=false
    fi
  fi

  # Train images
  if [ ! -d "dataset/train/images" ]; then
    mark_fail "dataset/train/images/ directory not found"
    dataset_ok=false
  else
    COUNT=$(find dataset/train/images -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) | wc -l)
    if [ "$COUNT" -lt "$MIN_TRAIN_IMAGES" ]; then
      mark_fail "Training images: $COUNT (need ≥ $MIN_TRAIN_IMAGES)"
      dataset_ok=false
    else
      mark_pass "Training images: $COUNT (≥ $MIN_TRAIN_IMAGES)"
    fi
  fi

  # Val images
  if [ ! -d "dataset/val/images" ]; then
    mark_fail "dataset/val/images/ directory not found"
    dataset_ok=false
  else
    COUNT=$(find dataset/val/images -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) | wc -l)
    if [ "$COUNT" -lt "$MIN_VAL_IMAGES" ]; then
      mark_fail "Validation images: $COUNT (need ≥ $MIN_VAL_IMAGES)"
      dataset_ok=false
    else
      mark_pass "Validation images: $COUNT (≥ $MIN_VAL_IMAGES)"
    fi
  fi

  # Test images (informational only)
  if [ -d "dataset/test/images" ]; then
    COUNT=$(find dataset/test/images -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) | wc -l)
    info "Test images: $COUNT (informational)"
  fi

  # Model file (warning only — may not exist before Spec 002)
  if [ ! -f "models/best.pt" ]; then
    mark_warn "models/best.pt not found (expected after Spec 002 training)"
    info "The API will use the YOLO stub in development mode."
  else
    SIZE=$(du -sh models/best.pt | cut -f1)
    mark_pass "models/best.pt exists ($SIZE)"
  fi

  $dataset_ok || return 1
}

# ---------------------------------------------------------------------------
# Check: Docker build
# ---------------------------------------------------------------------------
check_docker() {
  step "Docker build & health check"
  cd "$PROJECT_ROOT"

  if ! command -v docker &>/dev/null; then
    mark_warn "docker not installed — skipping Docker checks"
    return 0
  fi

  # Build image
  info "Building Docker image (tag: fiap-stride:local-ci)..."
  if docker build -t fiap-stride:local-ci .; then
    mark_pass "Docker image built successfully"
  else
    mark_fail "Docker build failed"
    return 1
  fi

  # Start stack
  info "Starting services with docker compose..."
  docker compose up -d db redis
  echo "Waiting for PostgreSQL to be ready..."
  timeout 60 bash -c 'until docker compose exec -T db pg_isready -U postgres -d fiap_stride 2>/dev/null; do sleep 2; done' \
    && success "PostgreSQL is ready" \
    || { mark_fail "PostgreSQL did not become ready in time"; docker compose down -v; return 1; }

  docker compose up -d api
  info "Waiting 15s for API to start..."
  sleep 15

  # Health check
  MAX_RETRIES=10
  RETRY=0
  HEALTH_OK=false
  while [ "$RETRY" -lt "$MAX_RETRIES" ]; do
    if curl -sf http://localhost:8001/health | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d.get('status') == 'healthy', f'status={d}'
" 2>/dev/null; then
      HEALTH_OK=true
      break
    fi
    RETRY=$((RETRY + 1))
    info "Health check attempt $RETRY/$MAX_RETRIES..."
    sleep 5
  done

  if $HEALTH_OK; then
    mark_pass "/health responded with status=healthy"
  else
    mark_fail "/health did not return healthy"
    docker compose logs api
    docker compose down -v
    return 1
  fi

  docker compose down -v
  mark_pass "Docker compose teardown complete"
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print_summary() {
  echo ""
  echo -e "${BOLD}═══════════════════════════════════════${NC}"
  echo -e "${BOLD}  CI Checks Summary${NC}"
  echo -e "${BOLD}═══════════════════════════════════════${NC}"
  [ "$PASS_COUNT" -gt 0 ] && echo -e "  ${GREEN}${BOLD}✓ Passed : $PASS_COUNT${NC}"
  [ "$WARN_COUNT" -gt 0 ] && echo -e "  ${YELLOW}${BOLD}⚠ Warnings: $WARN_COUNT${NC}"
  [ "$FAIL_COUNT" -gt 0 ] && echo -e "  ${RED}${BOLD}✗ Failed : $FAIL_COUNT${NC}"
  echo -e "${BOLD}═══════════════════════════════════════${NC}"
  if [ "$FAIL_COUNT" -gt 0 ]; then
    echo -e "${RED}${BOLD}  RESULT: FAILED — fix errors before pushing${NC}"
    return 1
  else
    echo -e "${GREEN}${BOLD}  RESULT: ALL CHECKS PASSED${NC}"
  fi
}

# ---------------------------------------------------------------------------
# Argument parsing & entrypoint
# ---------------------------------------------------------------------------
usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Run GitHub Actions CI checks locally.

Options:
  (no args)    Run all checks: lint, format, types, tests, dataset
  --lint       Run lint + format + type checks only
  --test       Run tests only
  --dataset    Run dataset validation only
  --docker     Run Docker build + health check only
  --fix        Auto-fix ruff issues, then run all checks
  --help       Show this help message

Examples:
  ./scripts/run_ci_checks.sh            # Full CI check
  ./scripts/run_ci_checks.sh --fix      # Fix formatting, then check all
  ./scripts/run_ci_checks.sh --lint     # Quick lint check before committing
EOF
}

main() {
  cd "$PROJECT_ROOT"
  activate_venv

  case "${1:-}" in
    --help|-h)
      usage
      exit 0
      ;;
    --lint)
      check_lint || true
      check_format || true
      check_types || true
      ;;
    --test)
      check_tests || true
      ;;
    --dataset)
      check_dataset || true
      ;;
    --docker)
      check_docker || true
      ;;
    --fix)
      autofix
      check_lint || true
      check_format || true
      check_types || true
      check_tests || true
      check_dataset || true
      ;;
    "")
      # Run all checks (except docker, which is slow — use --docker explicitly)
      check_lint || true
      check_format || true
      check_types || true
      check_tests || true
      check_dataset || true
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      usage
      exit 1
      ;;
  esac

  print_summary
}

main "$@"

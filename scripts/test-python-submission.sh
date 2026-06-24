#!/usr/bin/env bash
set -euo pipefail

readonly LANGUAGE="python"

usage() {
  echo "Usage: bash scripts/test-python-submission.sh <week> <problem> <github-username>" >&2
}

fail() {
  echo "error: $*" >&2
  exit 1
}

require_safe_path_segment() {
  local name="$1"
  local value="$2"

  [[ -n "$value" ]] || fail "$name must not be empty"
  [[ "$value" != "." ]] || fail "$name must not be '.'"
  [[ "$value" != ".." ]] || fail "$name must not be '..'"
  [[ "$value" != *"/"* ]] || fail "$name must not contain '/'"
}

if [[ "$#" -ne 3 ]]; then
  usage
  exit 2
fi

readonly WEEK="$1"
readonly PROBLEM="$2"
readonly USERNAME="$3"

require_safe_path_segment "week" "$WEEK"
require_safe_path_segment "problem" "$PROBLEM"
require_safe_path_segment "github-username" "$USERNAME"

readonly REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly SUBMISSION_DIR="$REPO_ROOT/$WEEK/submissions/$USERNAME/$PROBLEM/$LANGUAGE"
readonly TEST_DIR="$REPO_ROOT/$WEEK/problems/$PROBLEM/$LANGUAGE/tests"

[[ -d "$SUBMISSION_DIR" ]] || fail "submission directory not found: $SUBMISSION_DIR"
[[ -f "$SUBMISSION_DIR/solution.py" ]] || fail "missing solution.py in $SUBMISSION_DIR"
[[ -f "$SUBMISSION_DIR/requirements.txt" ]] || fail "missing requirements.txt in $SUBMISSION_DIR"
[[ -d "$TEST_DIR" ]] || fail "test directory not found: $TEST_DIR"

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

cp "$SUBMISSION_DIR/solution.py" "$TMP_DIR/solution.py"
cp "$SUBMISSION_DIR/requirements.txt" "$TMP_DIR/requirements.txt"
mkdir -p "$TMP_DIR/tests"
cp -R "$TEST_DIR/." "$TMP_DIR/tests/"

python3 -m venv "$TMP_DIR/.venv"
PYTHON_BIN="$TMP_DIR/.venv/bin/python"
PIP_CACHE_DIR="$TMP_DIR/pip-cache" "$PYTHON_BIN" -m pip install --upgrade pip
PIP_CACHE_DIR="$TMP_DIR/pip-cache" "$PYTHON_BIN" -m pip install -r "$TMP_DIR/requirements.txt"

(
  cd "$TMP_DIR"
  "$PYTHON_BIN" -m unittest discover -s tests -p "*.py"
)

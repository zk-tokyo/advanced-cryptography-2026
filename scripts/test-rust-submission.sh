#!/usr/bin/env bash
set -euo pipefail

readonly LANGUAGE="rust"

usage() {
  echo "Usage: bash scripts/test-rust-submission.sh <week> <problem> <github-username>" >&2
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
[[ -f "$SUBMISSION_DIR/Cargo.toml" ]] || fail "missing Cargo.toml in $SUBMISSION_DIR"
[[ -f "$SUBMISSION_DIR/src/lib.rs" ]] || fail "missing src/lib.rs in $SUBMISSION_DIR"
[[ -d "$TEST_DIR" ]] || fail "test directory not found: $TEST_DIR"

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

cp -R "$SUBMISSION_DIR/." "$TMP_DIR/"
mkdir -p "$TMP_DIR/tests"
cp -R "$TEST_DIR/." "$TMP_DIR/tests/"

cargo test --manifest-path "$TMP_DIR/Cargo.toml" --all-targets

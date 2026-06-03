#!/usr/bin/env bash
#
# Exercise the kickstart install / uninstall lifecycle end-to-end.
#
# Usage: smoke-install.sh KICKSTART_CMD TARGET_DIR [APP_DIR] [RC_FILE]
#
#   KICKSTART_CMD   Whitespace-separated command that invokes kickstart, e.g.
#                   "poetry run kickstart" or "/path/to/kickstart".
#   TARGET_DIR      Directory the launcher will live in.
#   APP_DIR         Optional --app-dir argument. Pass "" to skip.
#   RC_FILE         Optional rc file. When given, --update-path is exercised and
#                   the managed PATH block is asserted to be added then removed.
#
# Behavior: prints progress, exits non-zero on any failure (the script lives in
# both ci.yml::integration-test and release.yml::binary smoke steps).
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 KICKSTART_CMD TARGET_DIR [APP_DIR] [RC_FILE]" >&2
  exit 2
fi

KICKSTART_CMD="$1"
TARGET_DIR="$2"
APP_DIR="${3:-}"
RC_FILE="${4:-}"

# Split the kickstart command into argv so subcommands and flags compose cleanly.
read -ra KS <<<"$KICKSTART_CMD"

# Compose --app-dir args once so each install/uninstall reuses the same value.
APP_ARGS=()
if [[ -n "$APP_DIR" ]]; then
  APP_ARGS+=(--app-dir "$APP_DIR")
fi

echo "[smoke-install] install --check"
"${KS[@]}" install --target "$TARGET_DIR" "${APP_ARGS[@]}" --check

echo "[smoke-install] install --force"
"${KS[@]}" install --target "$TARGET_DIR" "${APP_ARGS[@]}" --shell bash --force
test -x "$TARGET_DIR/kickstart"
"$TARGET_DIR/kickstart" version

if [[ -z "$RC_FILE" ]]; then
  echo "[smoke-install] no rc file supplied; skipping --update-path lifecycle"
  exit 0
fi

echo "[smoke-install] install --update-path"
"${KS[@]}" install \
  --target "$TARGET_DIR" \
  "${APP_ARGS[@]}" \
  --rc-file "$RC_FILE" \
  --shell zsh \
  --update-path \
  --force
grep -q ">>> kickstart install >>>" "$RC_FILE"
grep -q "$TARGET_DIR" "$RC_FILE"

echo "[smoke-install] uninstall --clean-path"
"${KS[@]}" uninstall \
  --target "$TARGET_DIR" \
  "${APP_ARGS[@]}" \
  --rc-file "$RC_FILE" \
  --shell zsh \
  --clean-path
test ! -e "$TARGET_DIR/kickstart"
if grep -q ">>> kickstart install >>>" "$RC_FILE"; then
  echo "[smoke-install] expected managed block to be removed" >&2
  exit 1
fi

echo "[smoke-install] OK"

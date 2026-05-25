#!/usr/bin/env bash
#
# Rename the freshly-built PyInstaller `--onedir` payload, smoke-test the
# `install` subcommand against an isolated target, archive the payload into a
# tar.gz, and emit a sha256 file. Single source of truth for the binary
# packaging step shared by ci.yml (build-test) and release.yml (binary).
#
# Usage: name-and-smoke-binary.sh PLATFORM PYTHON_MINOR [DIST_DIR] [SMOKE_ROOT]
#
#   PLATFORM       e.g. linux-x64, macos-arm64
#   PYTHON_MINOR   e.g. 3.14
#   DIST_DIR       Directory holding the build output (default: dist)
#   SMOKE_ROOT     Directory used for the install smoke
#                  (default: $RUNNER_TEMP or /tmp)
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 PLATFORM PYTHON_MINOR [DIST_DIR] [SMOKE_ROOT]" >&2
  exit 2
fi

PLATFORM="$1"
PYTHON_MINOR="$2"
DIST_DIR="${3:-dist}"
SMOKE_ROOT="${4:-${RUNNER_TEMP:-/tmp}}"

asset="kickstart-${PLATFORM}-py${PYTHON_MINOR}"
payload="${DIST_DIR}/${asset}"

mv "${DIST_DIR}/kickstart" "${payload}"
"${payload}/kickstart" version
"${payload}/kickstart" --help

# Smoke-test the install subcommand end-to-end against an isolated target dir.
here="$(cd "$(dirname "$0")" && pwd)"
"${here}/smoke-install.sh" \
  "${payload}/kickstart" \
  "${SMOKE_ROOT}/install-smoke" \
  "${SMOKE_ROOT}/install-smoke-app"

tar -czf "${payload}.tar.gz" -C "${DIST_DIR}" "${asset}"
shasum -a 256 "${payload}.tar.gz" > "${payload}.tar.gz.sha256"
rm -rf "${payload}"
echo "[name-and-smoke] wrote ${payload}.tar.gz and ${payload}.tar.gz.sha256"

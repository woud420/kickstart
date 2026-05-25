#!/usr/bin/env bash
#
# kickstart install script.
#
# Downloads a prebuilt kickstart binary archive from a GitHub release, verifies
# its SHA-256 checksum, installs the binary payload under ~/.local/share/kickstart
# by default, and exposes a `kickstart` launcher in ~/.local/bin.
#
# Quick install (latest release):
#   curl -fsSL https://raw.githubusercontent.com/woud420/kickstart/master/scripts/install.sh | bash
#
# Pinned version, custom location (replace v<TAG> with a tag from the Releases page):
#   curl -fsSL https://raw.githubusercontent.com/woud420/kickstart/master/scripts/install.sh \
#     | KICKSTART_VERSION=v<TAG> KICKSTART_INSTALL_DIR=/usr/local/bin bash
#
# All knobs are environment variables or flags. Each flag has a matching env var.
#   --version VERSION         Release tag to install (default: latest)              [KICKSTART_VERSION]
#   --target DIR              Launcher install directory (default: ~/.local/bin)    [KICKSTART_INSTALL_DIR]
#   --app-dir DIR             Binary payload directory.                             [KICKSTART_APP_ROOT]
#                             Default: derived from --target. If --target ends in /bin,
#                             use <target_parent>/share/kickstart (~/.local/share/kickstart
#                             for the default --target). Otherwise use <target>/.kickstart.
#   --python-minor X.Y        Python minor of the binary archive (default: 3.14)    [KICKSTART_PYTHON_MINOR]
#   --no-path-update          Skip the PATH update prompt                           [KICKSTART_UPDATE_PROFILE=no]
#   --yes                     Answer yes to prompts (suitable for non-interactive)  [KICKSTART_ASSUME_YES=1
#                                                                                    or KICKSTART_UPDATE_PROFILE=yes]
#   -h, --help                Show this help
#
# Additional env vars (no matching flag):
#   KICKSTART_REPO            owner/repo to install from (default: woud420/kickstart)

set -euo pipefail

REPO="${KICKSTART_REPO:-woud420/kickstart}"
TARGET_DIR="${KICKSTART_INSTALL_DIR:-${HOME}/.local/bin}"
APP_ROOT="${KICKSTART_APP_ROOT:-}"
PYTHON_MINOR="${KICKSTART_PYTHON_MINOR:-3.14}"
VERSION="${KICKSTART_VERSION:-}"
UPDATE_PROFILE="${KICKSTART_UPDATE_PROFILE:-prompt}"
ASSUME_YES="${KICKSTART_ASSUME_YES:-0}"

print() { printf '%s\n' "$*"; }
warn() { printf 'kickstart-install: %s\n' "$*" >&2; }
die() {
  printf 'kickstart-install: error: %s\n' "$*" >&2
  exit 1
}

usage() {
  sed -n '3,30p' "$0" | sed 's/^# \{0,1\}//'
}

# Assign the value of a `--flag VALUE` / `--flag=VALUE` pair to a shell variable
# named by the first argument, and set SHIFT_AMT to how many positionals to consume.
# `printf -v` is used (instead of `echo` inside `$(...)`) so the helper can set a
# variable in the caller's scope without spawning a subshell that would discard it.
SHIFT_AMT=0
take_value() {
  local target_var="$1"
  local current="$2"
  local next="${3-}"
  if [[ "$current" == *=* ]]; then
    printf -v "$target_var" '%s' "${current#*=}"
    SHIFT_AMT=1
  else
    printf -v "$target_var" '%s' "$next"
    SHIFT_AMT=2
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version|--version=*)            take_value VERSION "$@";      shift "$SHIFT_AMT" ;;
    --target|--target=*)              take_value TARGET_DIR "$@";   shift "$SHIFT_AMT" ;;
    --app-dir|--app-dir=*)            take_value APP_ROOT "$@";     shift "$SHIFT_AMT" ;;
    --python-minor|--python-minor=*)  take_value PYTHON_MINOR "$@"; shift "$SHIFT_AMT" ;;
    --no-path-update)                 UPDATE_PROFILE="no"; shift ;;
    --yes|-y)                         ASSUME_YES=1; shift ;;
    -h|--help)                        usage; exit 0 ;;
    *)                                die "unknown argument: $1" ;;
  esac
done

need() {
  command -v "$1" >/dev/null 2>&1 || die "missing required dependency: $1"
}
need uname
need mkdir
need basename
need chmod
need dirname
need ln
need mv
need rm
need tar

DOWNLOADER=""
if command -v curl >/dev/null 2>&1; then
  DOWNLOADER="curl"
elif command -v wget >/dev/null 2>&1; then
  DOWNLOADER="wget"
else
  die "neither curl nor wget is available"
fi

# fetch URL [OUTFILE]
#
# When OUTFILE is omitted (or "-"), writes to stdout. Both curl and wget accept "-"
# as the destination for their respective output flags, so a single dispatch line
# covers both shapes.
fetch() {
  local url="$1"
  local out="${2:--}"
  case "$DOWNLOADER" in
    curl) curl --fail --silent --show-error --location --output "$out" "$url" ;;
    wget) wget --quiet --output-document "$out" "$url" ;;
  esac
}

uname_s="$(uname -s)"
uname_m="$(uname -m)"
case "$uname_s" in
  Linux) os="linux" ;;
  Darwin) os="macos" ;;
  *) die "unsupported operating system: $uname_s" ;;
esac
case "$uname_m" in
  x86_64|amd64) arch="x64" ;;
  arm64|aarch64) arch="arm64" ;;
  *) die "unsupported architecture: $uname_m" ;;
esac
platform="${os}-${arch}"

if [[ -z "$APP_ROOT" ]]; then
  target_parent="$(dirname "$TARGET_DIR")"
  target_name="$(basename "$TARGET_DIR")"
  if [[ "$target_name" == "bin" ]]; then
    APP_ROOT="${target_parent}/share/kickstart"
  else
    APP_ROOT="${TARGET_DIR}/.kickstart"
  fi
fi

if [[ -z "$VERSION" ]]; then
  print "Resolving latest kickstart release..."
  latest_json="$(fetch "https://api.github.com/repos/${REPO}/releases/latest")" \
    || die "could not query the latest release for $REPO"
  VERSION="$(printf '%s' "$latest_json" \
    | grep -E '"tag_name"' \
    | head -n 1 \
    | sed -E 's/.*"tag_name"[^"]*"([^"]+)".*/\1/')"
  [[ -n "$VERSION" ]] || die "could not parse the latest release tag for $REPO"
fi

asset="kickstart-${platform}-py${PYTHON_MINOR}"
archive="${asset}.tar.gz"
base_url="https://github.com/${REPO}/releases/download/${VERSION}"
archive_url="${base_url}/${archive}"
hash_url="${base_url}/${archive}.sha256"

print "Installing kickstart ${VERSION} for ${platform} (py${PYTHON_MINOR})"
print "  source:    ${archive_url}"
print "  launcher:  ${TARGET_DIR}/kickstart"
print "  binary:    ${APP_ROOT}/current"

tmpdir="$(mktemp -d 2>/dev/null || mktemp -d -t kickstart-install)"
trap 'rm -rf "$tmpdir"' EXIT

print "Downloading binary archive..."
fetch "$archive_url" "${tmpdir}/${archive}" \
  || die "could not download $archive_url (is the platform/python combination published for $VERSION?)"

print "Verifying checksum..."
if fetch "$hash_url" "${tmpdir}/${archive}.sha256" 2>/dev/null; then
  expected="$(awk '{print $1}' "${tmpdir}/${archive}.sha256")"
  if command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "${tmpdir}/${archive}" | awk '{print $1}')"
  elif command -v shasum >/dev/null 2>&1; then
    actual="$(shasum -a 256 "${tmpdir}/${archive}" | awk '{print $1}')"
  else
    warn "no sha256sum/shasum available; skipping checksum verification"
    actual="$expected"
  fi
  if [[ "$expected" != "$actual" ]]; then
    die "checksum mismatch (expected $expected, got $actual)"
  fi
  print "  ok ($expected)"
else
  warn "no published checksum for $archive; skipping verification"
fi

print "Extracting app..."
tar -xzf "${tmpdir}/${archive}" -C "$tmpdir" \
  || die "could not extract ${archive}"
test -x "${tmpdir}/${asset}/kickstart" \
  || die "archive did not contain an executable ${asset}/kickstart"

mkdir -p "$TARGET_DIR" "$APP_ROOT" || die "could not create install directories"
rm -rf "${APP_ROOT}/current"
mv "${tmpdir}/${asset}" "${APP_ROOT}/current" \
  || die "could not install binary payload to ${APP_ROOT}/current"
chmod 0755 "${APP_ROOT}/current/kickstart"
ln -sfn "${APP_ROOT}/current/kickstart" "${TARGET_DIR}/kickstart" \
  || die "could not link launcher at ${TARGET_DIR}/kickstart"
print "Installed kickstart launcher to ${TARGET_DIR}/kickstart"

# Decide whether to ask kickstart to update PATH.
already_on_path="no"
case ":$PATH:" in
  *":${TARGET_DIR}:"*) already_on_path="yes" ;;
esac

if [[ "$already_on_path" == "yes" ]]; then
  print "${TARGET_DIR} is already on your PATH."
  print "Run 'kickstart --help' to get started."
  exit 0
fi

if [[ "$UPDATE_PROFILE" == "no" ]]; then
  print ""
  print "${TARGET_DIR} is not on your PATH yet."
  "${TARGET_DIR}/kickstart" install --check --target "$TARGET_DIR" --app-dir "$APP_ROOT" || true
  print ""
  print "Re-run with KICKSTART_UPDATE_PROFILE=yes (or --yes) to update your shell rc file."
  exit 0
fi

should_update="0"
if [[ "$UPDATE_PROFILE" == "yes" || "$ASSUME_YES" == "1" ]]; then
  should_update="1"
elif [[ -t 0 ]]; then
  printf 'Add %s to your PATH by updating your shell rc file? [Y/n] ' "$TARGET_DIR"
  read -r reply || reply=""
  case "$reply" in
    ""|y|Y|yes|YES) should_update="1" ;;
    *) should_update="0" ;;
  esac
else
  # Non-interactive run without explicit consent: leave PATH untouched.
  should_update="0"
fi

if [[ "$should_update" == "1" ]]; then
  "${TARGET_DIR}/kickstart" install \
    --target "$TARGET_DIR" \
    --app-dir "$APP_ROOT" \
    --update-path \
    --force \
    || warn "kickstart install --update-path failed; update PATH manually with:
  export PATH=\"${TARGET_DIR}:\$PATH\""
else
  print ""
  print "Skipping PATH update. Add this line to your shell startup file:"
  print "  export PATH=\"${TARGET_DIR}:\$PATH\""
  print "or run: '${TARGET_DIR}/kickstart' install --update-path"
fi

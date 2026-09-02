#!/usr/bin/env bash
#
# ENG-205 release-binary reproduction: prove that an old updater nests the
# managed payload, then prove that a candidate build repairs that layout from a
# staged process (exit 0, launcher resolves to <app_root>/current/kickstart),
# refuses a self-destructive `install --force`, stays idempotent, and upgrades a
# healthy managed install through the same handoff chain.
#
# Usage: legacy-layout-smoke.sh CANDIDATE_LAUNCHER [OLD_TAG]
#
#   CANDIDATE_LAUNCHER  Launcher of an onedir build of the working tree, e.g.
#                       dist/kickstart/kickstart after `make binary`.
#   OLD_TAG             Release whose updater still nests payloads (default v0.4.3).
#
# Environment:
#   KICKSTART_REPO          owner/repo to download OLD_TAG from (default woud420/kickstart)
#   KICKSTART_PYTHON_MINOR  Python minor in the release asset name (default 3.14)
#   SMOKE_ROOT              Scratch directory (default: a fresh mktemp -d)
#   KEEP_SMOKE_ROOT         Set to 1 to keep the scratch directory on success
#   KICKSTART_OLD_LAUNCHER  Launcher of an already-built OLD_TAG onedir payload; skips
#                           the release download (for hosts whose libc is older
#                           than the published build's).
#   KICKSTART_LEGACY_REPRO  `live` (default) runs the OLD binary's own updater
#                           against the live latest release to reproduce the
#                           nesting; `synthetic` lays the nested shape out by
#                           hand for hosts that cannot reach the GitHub API.
#
# The reproduction step is the handoff the fix cannot change (the old binary
# controls it); every later step talks only to a local fake release served from
# SMOKE_ROOT.
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 CANDIDATE_LAUNCHER [OLD_TAG]" >&2
  exit 2
fi

CANDIDATE_LAUNCHER="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OLD_TAG="${2:-v0.4.3}"
REPO="${KICKSTART_REPO:-woud420/kickstart}"
PYTHON_MINOR="${KICKSTART_PYTHON_MINOR:-3.14}"
SMOKE_ROOT="${SMOKE_ROOT:-$(mktemp -d "${TMPDIR:-/tmp}/kickstart-legacy-layout.XXXXXX")}"
KEEP_SMOKE_ROOT="${KEEP_SMOKE_ROOT:-0}"
LEGACY_REPRO="${KICKSTART_LEGACY_REPRO:-live}"

log() { printf '[legacy-layout] %s\n' "$*"; }
fail() { printf '[legacy-layout] FAIL: %s\n' "$*" >&2; exit 1; }
realpath_of() { python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1"; }

case "$(uname -s)-$(uname -m)" in
  Linux-x86_64|Linux-amd64) PLATFORM=linux-x64 ;;
  Linux-aarch64|Linux-arm64) PLATFORM=linux-arm64 ;;
  Darwin-arm64) PLATFORM=macos-arm64 ;;
  *) fail "unsupported host $(uname -s)-$(uname -m)" ;;
esac
ASSET="kickstart-${PLATFORM}-py${PYTHON_MINOR}"

if command -v sha256sum >/dev/null 2>&1; then
  SHA256=(sha256sum)
else
  SHA256=(shasum -a 256)
fi

[[ -x "$CANDIDATE_LAUNCHER" ]] || fail "candidate launcher $CANDIDATE_LAUNCHER is not executable"
[[ -d "$(dirname "$CANDIDATE_LAUNCHER")/_internal" ]] || fail "candidate launcher is not an onedir payload"
CANDIDATE_BUNDLE="$(dirname "$CANDIDATE_LAUNCHER")"
CANDIDATE_VERSION="$(
  KICKSTART_TELEMETRY_DISABLED=1 "$CANDIDATE_LAUNCHER" --version | sed -E 's/.*kickstart v([0-9.]+).*/\1/'
)"
[[ "$CANDIDATE_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "could not read candidate version"

mkdir -p "$SMOKE_ROOT"
SMOKE_ROOT="$(cd "$SMOKE_ROOT" && pwd)"
HOME_DIR="$SMOKE_ROOT/home"
TARGET="$HOME_DIR/.local/bin"
APP_ROOT="$HOME_DIR/.local/share/kickstart"
SCRATCH_TMP="$SMOKE_ROOT/tmp"
RELEASES="$SMOKE_ROOT/releases"
mkdir -p "$TARGET" "$APP_ROOT" "$SCRATCH_TMP" "$RELEASES" "$SMOKE_ROOT/config"

# Every kickstart invocation below is isolated from the real user profile.
run_kickstart() {
  env KICKSTART_TELEMETRY_DISABLED=1 XDG_CONFIG_HOME="$SMOKE_ROOT/config" TMPDIR="$SCRATCH_TMP" "$@"
}

SERVER_PID=""
cleanup() {
  if [[ -n "$SERVER_PID" ]]; then
    kill "$SERVER_PID" 2>/dev/null || true
  fi
  if [[ "$KEEP_SMOKE_ROOT" != "1" && "${SMOKE_OK:-0}" == "1" ]]; then
    rm -rf "$SMOKE_ROOT"
  else
    log "scratch directory kept at $SMOKE_ROOT"
  fi
}
trap cleanup EXIT

assert_canonical_layout() {
  local real
  real="$(realpath_of "$TARGET/kickstart")"
  [[ "$real" == "$(realpath_of "$APP_ROOT/current")/kickstart" ]] \
    || fail "launcher resolves to $real, expected $APP_ROOT/current/kickstart"
  [[ ! -L "$APP_ROOT/current/kickstart" ]] || fail "$APP_ROOT/current/kickstart is still a symlink"
  [[ ! -e "$APP_ROOT/current/.kickstart" ]] || fail "nested payload survived at $APP_ROOT/current/.kickstart"
  local leftovers
  leftovers="$(find "$SCRATCH_TMP" -mindepth 1 -maxdepth 1 -name 'kickstart-*' | wc -l | tr -d ' ')"
  [[ "$leftovers" == "0" ]] || fail "staging directories left behind under $SCRATCH_TMP"
}

# --- 1. Install the old release ------------------------------------------
if [[ -n "${KICKSTART_OLD_LAUNCHER:-}" ]]; then
  log "using prebuilt $OLD_TAG payload at $KICKSTART_OLD_LAUNCHER"
  [[ -d "$(dirname "$KICKSTART_OLD_LAUNCHER")/_internal" ]] || fail "old launcher is not an onedir payload"
  mkdir -p "$RELEASES/old"
  cp -R "$(dirname "$KICKSTART_OLD_LAUNCHER")" "$RELEASES/old/$ASSET"
else
  log "downloading $OLD_TAG $ASSET"
  (
    cd "$RELEASES"
    curl -fsSL -o "$ASSET.tar.gz" "https://github.com/$REPO/releases/download/$OLD_TAG/$ASSET.tar.gz"
    curl -fsSL -o "$ASSET.tar.gz.sha256" "https://github.com/$REPO/releases/download/$OLD_TAG/$ASSET.tar.gz.sha256"
    # Published .sha256 files name the asset by its build path, so compare digests directly.
    expected="$(cut -d' ' -f1 "$ASSET.tar.gz.sha256")"
    actual="$("${SHA256[@]}" "$ASSET.tar.gz" | cut -d' ' -f1)"
    [[ "$expected" == "$actual" ]] || { echo "[legacy-layout] FAIL: checksum mismatch for $OLD_TAG $ASSET" >&2; exit 1; }
    mkdir -p old && tar -xzf "$ASSET.tar.gz" -C old
  )
fi
OLD_LAUNCHER="$RELEASES/old/$ASSET/kickstart"

log "installing $OLD_TAG into an isolated managed root"
run_kickstart "$OLD_LAUNCHER" install --target "$TARGET" --app-dir "$APP_ROOT" >/dev/null
[[ "$(realpath_of "$TARGET/kickstart")" == "$(realpath_of "$APP_ROOT/current")/kickstart" ]] \
  || fail "fresh $OLD_TAG install is not canonical"

# --- 2. Reproduce the legacy handoff: the old updater nests the payload ----
case "$LEGACY_REPRO" in
  live)
    log "running the $OLD_TAG updater against the live latest release"
    run_kickstart "$TARGET/kickstart" upgrade
    ;;
  synthetic)
    # Mirror what the pre-fix updater did: it resolved the launcher first, so it
    # treated <app_root>/current as the launcher directory, installed the new
    # payload under <app_root>/current/.kickstart/current, and replaced
    # <app_root>/current/kickstart with an absolute symlink into it.
    log "synthesizing the nested layout the $OLD_TAG updater produces (live reproduction skipped)"
    mkdir -p "$APP_ROOT/current/.kickstart"
    cp -R "$RELEASES/old/$ASSET" "$APP_ROOT/current/.kickstart/current"
    rm "$APP_ROOT/current/kickstart"
    ln -s "$APP_ROOT/current/.kickstart/current/kickstart" "$APP_ROOT/current/kickstart"
    ;;
  *) fail "KICKSTART_LEGACY_REPRO must be live or synthetic" ;;
esac
NESTED_REAL="$(realpath_of "$TARGET/kickstart")"
[[ "$NESTED_REAL" == "$(realpath_of "$APP_ROOT/current")/.kickstart/current/kickstart" ]] \
  || fail "expected the $OLD_TAG updater to nest the payload, launcher resolves to $NESTED_REAL"
log "reproduced: launcher resolves to $NESTED_REAL"

# --- 3. Put the candidate build into the nested slot ----------------------
# This models the first fixed binary running from the legacy nested layout.
log "replacing the nested payload with the candidate build ($CANDIDATE_VERSION)"
rm -rf "$APP_ROOT/current/.kickstart/current"
cp -R "$CANDIDATE_BUNDLE" "$APP_ROOT/current/.kickstart/current"
[[ -L "$APP_ROOT/current/kickstart" ]] || fail "managed executable is no longer a symlink into the nested payload"
run_kickstart "$TARGET/kickstart" --version | grep -q "v$CANDIDATE_VERSION" || fail "nested candidate does not run"

# --- 4. The self-destructive fallback is refused ---------------------------
log "install --force from inside the app root must refuse"
if run_kickstart "$APP_ROOT/current/.kickstart/current/kickstart" install --force --target "$TARGET" --app-dir "$APP_ROOT" >"$SMOKE_ROOT/install-force.log" 2>&1; then
  fail "install --force from the nested payload succeeded instead of refusing"
fi
grep -q "kickstart upgrade" "$SMOKE_ROOT/install-force.log" || fail "refusal does not point at kickstart upgrade"
[[ "$(realpath_of "$TARGET/kickstart")" == "$NESTED_REAL" ]] || fail "refused install modified the layout"

# --- 5. Serve a fake release matching the candidate version ---------------
PORT="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')"
BASE_URL="http://127.0.0.1:$PORT"
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$RELEASES" >"$SMOKE_ROOT/http.log" 2>&1 &
SERVER_PID=$!
for _ in $(seq 1 50); do
  curl -fsS "$BASE_URL/" >/dev/null 2>&1 && break
  sleep 0.1
done

write_release_json() {
  local file="$1" tag="$2"
  cat >"$file" <<JSON
{"tag_name": "$tag", "assets": [
  {"name": "$ASSET.tar.gz", "browser_download_url": "$BASE_URL/candidate/$ASSET.tar.gz"},
  {"name": "$ASSET.tar.gz.sha256", "browser_download_url": "$BASE_URL/candidate/$ASSET.tar.gz.sha256"}
]}
JSON
}
write_release_json "$RELEASES/same-version.json" "v$CANDIDATE_VERSION"

# --- 6. Same-version repair through the staged handoff --------------------
log "running the candidate updater with no newer release available"
run_kickstart env KICKSTART_RELEASE_URL="$BASE_URL/same-version.json" "$TARGET/kickstart" upgrade | tee "$SMOKE_ROOT/repair.log"
grep -q "Repaired the managed install layout" "$SMOKE_ROOT/repair.log" || fail "repair did not report success"
assert_canonical_layout
run_kickstart "$TARGET/kickstart" --version | grep -q "v$CANDIDATE_VERSION" || fail "repaired install does not run"
log "repaired: launcher resolves to $APP_ROOT/current/kickstart"

# --- 7. A healthy same-version install is idempotent ---------------------
log "running the candidate updater again on the healthy layout"
run_kickstart env KICKSTART_RELEASE_URL="$BASE_URL/same-version.json" "$TARGET/kickstart" upgrade | tee "$SMOKE_ROOT/idempotent.log"
grep -q "already up to date" "$SMOKE_ROOT/idempotent.log" || fail "healthy install was not reported as current"
assert_canonical_layout

# --- 8. A newer release activates through the same handoff ---------------
log "packaging the candidate as a fake newer release"
mkdir -p "$RELEASES/candidate/stage"
rm -rf "$RELEASES/candidate/stage/$ASSET"
cp -R "$CANDIDATE_BUNDLE" "$RELEASES/candidate/stage/$ASSET"
tar -czf "$RELEASES/candidate/$ASSET.tar.gz" -C "$RELEASES/candidate/stage" "$ASSET"
(cd "$RELEASES/candidate" && "${SHA256[@]}" "$ASSET.tar.gz" >"$ASSET.tar.gz.sha256")
write_release_json "$RELEASES/newer.json" "v9.9.9"

log "upgrading the healthy managed install to the fake newer release"
run_kickstart env KICKSTART_RELEASE_URL="$BASE_URL/newer.json" "$TARGET/kickstart" upgrade | tee "$SMOKE_ROOT/upgrade.log"
grep -q "Checksum verified" "$SMOKE_ROOT/upgrade.log" || fail "upgrade skipped checksum verification"
grep -q "Updated to 9.9.9" "$SMOKE_ROOT/upgrade.log" || fail "upgrade did not report success"
assert_canonical_layout
run_kickstart "$TARGET/kickstart" --version | grep -q "v$CANDIDATE_VERSION" || fail "upgraded install does not run"

SMOKE_OK=1
log "OK ($PLATFORM, candidate $CANDIDATE_VERSION, legacy $OLD_TAG, reproduction $LEGACY_REPRO)"

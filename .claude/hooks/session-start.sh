#!/bin/bash
#
# SessionStart hook for the Claude Code on the web sandbox.
#
# Claude Code-specific: registered in .claude/settings.json and fired on
# the SessionStart lifecycle event. Hooks have no cross-vendor standard,
# so this stays under .claude/ rather than the neutral .agents/ namespace.
#
# Bootstraps the kickstart toolchain in a fresh remote sandbox so that
# `make check` and the website checks work immediately, instead of every
# session re-discovering that the default `python3` is too old for the
# `>=3.12` floor and re-running poetry/bun installs by hand.
#
# Synchronous, idempotent, non-interactive. Verbose install output goes to
# stderr (visible in logs) so the agent's context stays clean; only a short
# readiness summary is written to stdout.
set -euo pipefail

# Only bootstrap in the remote (Claude Code on the web) sandbox. Local
# sessions manage their own environment.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"

log() { printf 'session-start: %s\n' "$*" >&2; }

# kickstart requires Python >=3.12,<3.15 (pyproject [project].requires-python).
# The sandbox default may be older, so pin Poetry's virtualenv to the newest
# supported interpreter that is actually present.
for py in python3.14 python3.13 python3.12; do
  if command -v "$py" >/dev/null 2>&1; then
    log "using $py for the Poetry environment"
    poetry env use "$py" >&2
    break
  fi
done

# Python dependencies. `install` (not a frozen/sync variant) lets the cached
# container state be reused across sessions.
log "installing Python dependencies with Poetry"
poetry install --no-interaction >&2

# Website dependencies (TypeScript Cloudflare Worker under website/).
if command -v bun >/dev/null 2>&1 && [ -f website/package.json ]; then
  log "installing website dependencies with Bun"
  (cd website && bun install) >&2
fi

echo "kickstart sandbox ready: 'make check' and 'cd website && bun run check' will work."

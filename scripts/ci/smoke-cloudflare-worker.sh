#!/usr/bin/env bash
#
# Generate a TypeScript Cloudflare Workers service via `kickstart create service`
# and run `make install / make test / make check` inside the generated project.
# Emits GitHub Actions `::error` annotations and log tails on failure.
#
# Usage: smoke-cloudflare-worker.sh
#
# Environment:
#   KICKSTART_CMD   Whitespace-separated kickstart command to invoke
#                   (default: "poetry run kickstart")
#   PROJECT_NAME    Generated project directory name
#                   (default: "test-cf-worker-flagship")
set -euo pipefail

KICKSTART_CMD="${KICKSTART_CMD:-poetry run kickstart}"
PROJECT_NAME="${PROJECT_NAME:-test-cf-worker-flagship}"

read -ra KS <<<"$KICKSTART_CMD"

temp_root="$(mktemp -d /tmp/kickstart-cf-worker-smoke-XXXXXX)"
project_path="${temp_root}/${PROJECT_NAME}"
log_dir="${temp_root}/logs"
generation_log="${log_dir}/generate.log"

mkdir -p "${log_dir}"

echo "Cloudflare Worker smoke temp root: ${temp_root}"
echo "Generated Cloudflare Worker project path: ${project_path}"
echo "Smoke log directory: ${log_dir}"

# Run a command, capture stdout+stderr to a log file, and emit a GitHub Actions
# error annotation + log tail when the command fails. `tag` is used in the
# annotation title; `label` is the display string for the command.
log_and_run() {
  local tag="$1" label="$2" log="$3" exit_code=0
  shift 3
  echo "Running: ${label}"
  if "$@" >"${log}" 2>&1; then
    echo "Passed: ${label}"
  else
    exit_code=$?
    echo "::error title=Cloudflare Worker ${tag} failed::project=${project_path}; command=${label}; exit_code=${exit_code}; log=${log}"
    echo "---- tail -n 80 ${log} ----"
    tail -n 80 "${log}" || true
    echo "---- end log tail ----"
    exit "${exit_code}"
  fi
}

log_and_run "generation" \
  "${KICKSTART_CMD} create service ${PROJECT_NAME} --root ${temp_root} --lang typescript --runtime cloudflare-workers" \
  "${generation_log}" \
  env KICKSTART_EVAL=1 "${KS[@]}" create service "${PROJECT_NAME}" \
    --root "${temp_root}" \
    --lang typescript \
    --runtime cloudflare-workers

run_in_project() {
  local name="$1"
  shift
  local label="$*"
  local log="${log_dir}/${name}.log"
  ( cd "${project_path}" && log_and_run "smoke check" "${label}" "${log}" "$@" )
}

run_in_project make-install make install
run_in_project make-test make test
run_in_project make-check make check

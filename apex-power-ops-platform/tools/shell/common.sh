#!/usr/bin/env bash
set -euo pipefail

get_apex_repo_root() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "${script_dir}/../.." && pwd
}

import_apex_env_file() {
  local repo_root env_file
  repo_root="$(get_apex_repo_root)"
  env_file="${1:-${repo_root}/.env.dev}"

  if [[ ! -f "${env_file}" ]]; then
    env_file="${repo_root}/.env.dev.template"
  fi

  if [[ ! -f "${env_file}" ]]; then
    return 0
  fi

  set -a
  # shellcheck disable=SC1090
  source "${env_file}"
  set +a
}

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
  source <(sed 's/\r$//' "${env_file}")
  set +a
}

get_apex_repo_python() {
  local repo_root
  repo_root="$(get_apex_repo_root)"

  if [[ -n "${APEX_PLATFORM_PYTHON:-}" ]]; then
    printf '%s' "${APEX_PLATFORM_PYTHON}"
    return 0
  fi

  if [[ -x "${repo_root}/.venv/bin/python" ]]; then
    printf '%s' "${repo_root}/.venv/bin/python"
    return 0
  fi

  if [[ -f "${repo_root}/.venv/Scripts/python.exe" ]]; then
    printf '%s' "${repo_root}/.venv/Scripts/python.exe"
    return 0
  fi

  printf '%s\n' "No repo-local Python interpreter found under ${repo_root}/.venv." >&2
  return 1
}

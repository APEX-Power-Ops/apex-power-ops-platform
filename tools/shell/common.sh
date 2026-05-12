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
  local repo_root is_linux_shell configured_python
  repo_root="$(get_apex_repo_root)"

  is_linux_shell=false
  case "$(uname -s)" in
    Linux*)
      is_linux_shell=true
      ;;
  esac

  configured_python="${APEX_PLATFORM_PYTHON:-}"
  if [[ -n "${configured_python}" ]]; then
    if [[ "${is_linux_shell}" != "true" || "${configured_python}" != *.exe ]]; then
      if [[ "${configured_python}" == *[\\/]* ]]; then
        if [[ -f "${configured_python}" || -x "${configured_python}" ]]; then
          printf '%s' "${configured_python}"
          return 0
        fi

        printf '%s\n' "Configured APEX_PLATFORM_PYTHON path not found: ${configured_python}" >&2
        return 1
      fi

      if command -v "${configured_python}" >/dev/null 2>&1; then
        command -v "${configured_python}"
        return 0
      fi

      printf '%s\n' "Configured APEX_PLATFORM_PYTHON command not found: ${configured_python}" >&2
      return 1
    fi

    if [[ "${is_linux_shell}" == "true" ]]; then
      printf '%s\n' "Configured APEX_PLATFORM_PYTHON points at a Windows interpreter not usable from this shell: ${configured_python}" >&2
      return 1
    fi
  fi

  if [[ -x "${repo_root}/.venv/bin/python" ]]; then
    printf '%s' "${repo_root}/.venv/bin/python"
    return 0
  fi

  if [[ "${is_linux_shell}" != "true" && -f "${repo_root}/.venv/Scripts/python.exe" ]]; then
    printf '%s' "${repo_root}/.venv/Scripts/python.exe"
    return 0
  fi

  printf '%s\n' "No repo-local Python interpreter found under ${repo_root}/.venv." >&2
  return 1
}

get_apex_preferred_python() {
  local repo_python repo_root

  repo_root="$(get_apex_repo_root)"

  repo_python="$(get_apex_repo_python 2>/dev/null || true)"
  if [[ -n "${repo_python}" ]]; then
    printf '%s' "${repo_python}"
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi

  printf '%s\n' "No usable Python interpreter found for ${repo_root}." >&2
  return 1
}

get_apex_default_packet_id() {
  local label="${1:-operator}"

  if [[ -n "${APEX_PACKET_ID:-}" ]]; then
    if ! is_apex_packet_id_valid "${APEX_PACKET_ID}"; then
      printf '%s\n' "Invalid packet id '${APEX_PACKET_ID}'. Packet ids must match ^[A-Za-z0-9][A-Za-z0-9._-]*$." >&2
      return 1
    fi

    printf '%s' "${APEX_PACKET_ID}"
    return 0
  fi

  printf 'adhoc-%s-%s' "${label}" "$(date -u +%Y-%m-%d-%H%M%S)"
}

is_apex_packet_id_valid() {
  local packet_id="$1"
  [[ "${packet_id}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]
}

require_apex_packet_id() {
  local packet_id="$1"

  if is_apex_packet_id_valid "${packet_id}"; then
    return 0
  fi

  printf '%s\n' "Invalid packet id '${packet_id}'. Packet ids must match ^[A-Za-z0-9][A-Za-z0-9._-]*$." >&2
  return 1
}

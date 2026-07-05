"""apex-jobs subprocess env policy -- a default-deny allowlist (exact names plus
two provably-safe standard namespace prefixes) for the environment handed to job
child processes. A secret sourced into the worker's own environment (*_PASSWORD /
*_DSN / *_TOKEN / *_KEY / service keys) is never inherited by a child via the
process environment -- it is dropped by construction. On-disk credential stores
under HOME (e.g. ~/.pgpass, ~/.aws/credentials) remain reachable and are out of
scope for this env-policy helper; filesystem isolation is a separate concern.
"""
import os

# Exact names kept: home/user/shell basics, temp dirs, timezone, base locale.
ENV_ALLOW_EXACT = frozenset({
    "HOME", "PATH", "USER", "LOGNAME", "SHELL", "TERM",
    "TMPDIR", "TMP", "TEMP", "TZ", "LANG",
})

# Standard non-secret namespaces kept by prefix: POSIX locale (LC_*) and XDG
# base-directory (XDG_*). A prefix admits future members with no code change;
# no platform secret lives under either namespace.
ENV_ALLOW_PREFIXES = ("LC_", "XDG_")


def _allowed(name):
    return name in ENV_ALLOW_EXACT or name.startswith(ENV_ALLOW_PREFIXES)


def sanitized_env(job_env, extra_path=None):
    """Sterile subprocess env: the allowlisted names from os.environ plus the
    APEX_JOB_ENV marker. If extra_path is given, prepend it to PATH (the agent
    path uses this for the claude/codex bin dirs; command jobs pass None)."""
    env = {k: v for k, v in os.environ.items() if _allowed(k)}
    env["APEX_JOB_ENV"] = job_env
    if extra_path:
        # filter(None, ...) drops an absent PATH so no trailing os.pathsep (an
        # empty PATH element = CWD) is ever emitted.
        env["PATH"] = os.pathsep.join(filter(None, [extra_path, env.get("PATH")]))
    return env

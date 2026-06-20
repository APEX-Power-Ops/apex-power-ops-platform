"""Deterministic fake agent for offline TDD of the agent-runner. Stands in for
`claude -p`: writes AGENT_OUTPUT.md in the cwd and prints a JSON envelope.
  --fail              -> exit 1 without writing (agent error path)
  --no-write          -> exit 0 without writing (no-changes path)
  --probe F --sleep S -> bracket a START/END interval (tagged by pid) in file F,
                         sleeping S seconds between, so a test can measure how many
                         agents the pool ran at once. Still writes output + succeeds.
No tokens, no network, no auth."""
import json
import os
import pathlib
import sys
import time


def _write_output(argv):
    prompt = next((a for a in argv if not a.startswith("-")), "")
    pathlib.Path("AGENT_OUTPUT.md").write_text(f"# done\n\nprompt: {prompt}\n")


def main(argv):
    if "--fail" in argv:
        print(json.dumps({"result": "refused", "is_error": True}))
        return 1
    if "--no-write" in argv:
        print(json.dumps({"result": "no changes needed", "is_error": False}))
        return 0
    if "--probe" in argv:
        probe = argv[argv.index("--probe") + 1]
        sleep_s = float(argv[argv.index("--sleep") + 1]) if "--sleep" in argv else 0.0
        tag = os.getpid()
        with open(probe, "a") as f:           # O_APPEND: each short line writes atomically
            f.write(f"START {tag} {time.time():.6f}\n")
        time.sleep(sleep_s)
        with open(probe, "a") as f:
            f.write(f"END {tag} {time.time():.6f}\n")
        _write_output(argv)
        print(json.dumps({"result": "probe done", "is_error": False}))
        return 0
    _write_output(argv)
    print(json.dumps({"result": "wrote AGENT_OUTPUT.md", "is_error": False}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

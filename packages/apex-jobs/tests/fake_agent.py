"""Deterministic fake agent for offline TDD of the agent-runner. Stands in for
`claude -p`: writes AGENT_OUTPUT.md in the cwd and prints a JSON envelope.
  --fail      -> exit 1 without writing (agent error path)
  --no-write  -> exit 0 without writing (no-changes path)
No tokens, no network, no auth."""
import json
import pathlib
import sys


def main(argv):
    if "--fail" in argv:
        print(json.dumps({"result": "refused", "is_error": True}))
        return 1
    if "--no-write" in argv:
        print(json.dumps({"result": "no changes needed", "is_error": False}))
        return 0
    prompt = next((a for a in argv if not a.startswith("-")), "")
    pathlib.Path("AGENT_OUTPUT.md").write_text(f"# done\n\nprompt: {prompt}\n")
    print(json.dumps({"result": "wrote AGENT_OUTPUT.md", "is_error": False}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

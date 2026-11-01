"""Hash-chained audit log (ADR-012). Records events and data fingerprints, never data contents."""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

GENESIS = "0" * 64


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class AuditLog:
    def __init__(self, run_dir):
        self.path = Path(run_dir) / "audit.jsonl"
        self.anchor = Path(run_dir) / "anchor.txt"
        self.prev = GENESIS

    def append(self, event, **fields):
        entry = {"time": datetime.now(timezone.utc).isoformat(), "event": event, **fields, "prev": self.prev}
        entry["hash"] = sha256(json.dumps(entry, sort_keys=True, ensure_ascii=False))
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.prev = entry["hash"]

    def close(self):
        self.anchor.write_text(self.prev + "\n", encoding="utf-8")


def verify(run_dir):
    """Recompute the chain and compare it with the anchor. Returns (ok, message)."""
    run_dir = Path(run_dir)
    prev = GENESIS
    lines = (run_dir / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines, 1):
        entry = json.loads(line)
        stored = entry.pop("hash")
        if entry["prev"] != prev or sha256(json.dumps(entry, sort_keys=True, ensure_ascii=False)) != stored:
            return False, f"Chain broken at line {number}"
        prev = stored
    if prev != (run_dir / "anchor.txt").read_text(encoding="utf-8").strip():
        return False, "Last hash does not match the anchor"
    return True, f"OK: {len(lines)} events verified"


if __name__ == "__main__":
    ok, message = verify(sys.argv[1])
    print(message)
    sys.exit(0 if ok else 1)

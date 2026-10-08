#!/usr/bin/env python3


from __future__ import annotations

import contextlib
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

THREAT_PATTERNS: list[tuple[str, str]] = [
    (r"ignore previous instructions|bypass|override safeguards", "prompt_injection"),
    (r"api key|token|secret|password", "credential_exposure"),
    (r"drop database|rm -rf|delete all", "system_destruction"),
    (r"sudo|chmod 777|sudoers", "privilege_escalation"),
    (r"exfiltrat|export .* customer", "data_exfiltration"),
]


def get_log_file(ws_path: Path) -> Path:
    log_dir = ws_path / "logs" / "copilot" / "governance"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "audit.log"


def append_entry(log_file: Path, entry: dict) -> None:
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main() -> None:
    event = sys.argv[1] if len(sys.argv) > 1 else "unknown"

    raw = sys.stdin.read()
    data: dict = {}
    with contextlib.suppress(json.JSONDecodeError, ValueError):
        data = json.loads(raw)

    ws_path = Path(data.get("cwd", os.getcwd()))
    log_file = get_log_file(ws_path)

    if event == "session_start":
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": "session_start",
            "governance_level": "standard",
            "cwd": str(ws_path),
        }
        append_entry(log_file, entry)
        print("[governance-audit] session start logged (standard mode).")

    elif event == "user_prompt_submit":
        prompt_text = data.get("prompt", "").lower()
        threats = [
            label
            for pattern, label in THREAT_PATTERNS
            if re.search(pattern, prompt_text)
        ]
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": "prompt_scanned",
            "governance_level": "standard",
            "threat_count": len(threats),
            "threats": threats,
        }
        append_entry(log_file, entry)
        if threats:
            threats_str = ", ".join(threats)
            print(
                f"[governance-audit] warning: potential threats detected: {threats_str}"
            )
        else:
            print("[governance-audit] prompt scan clean.")

    elif event == "session_end":
        scan_count = 0
        if log_file.exists():
            with open(log_file, encoding="utf-8") as f:
                scan_count = sum(1 for line in f if '"prompt_scanned"' in line)
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": "session_end",
            "scanned_prompts": scan_count,
        }
        append_entry(log_file, entry)
        print(
            "[governance-audit] session end logged."
            " Verify get_errors and final validation summary."
        )


if __name__ == "__main__":
    main()

from __future__ import annotations

import re
import subprocess
from pathlib import Path


FORBIDDEN_NAMES = {".env", ".env.local"}
FORBIDDEN_SUFFIXES = {".db", ".dump", ".sqlite", ".sql"}
SECRET_ASSIGNMENT = re.compile(r"(?im)^(?:GEMINI_API_KEY|OPENROUTER_API_KEY|SUPABASE_DB_URL)[ \t]*=[ \t]*[^\s#]+")


def tracked_files() -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8")
    return [Path(item) for item in output.split("\0") if item]


def main() -> int:
    failures: list[str] = []
    paths = tracked_files()
    for path in paths:
        if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            failures.append(f"forbidden tracked artifact: {path}")
            continue
        if path.suffix.lower() not in {".env", ".example", ".md", ".py", ".ts", ".tsx", ".yml", ".yaml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if SECRET_ASSIGNMENT.search(text):
            failures.append(f"possible committed secret value: {path}")

    if failures:
        print("\n".join(failures))
        return 1
    print(f"guardrails passed: {len(paths)} repository files checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Block things that must never reach this public repo.

Copied from analysttom712/total-rewards-analytics (scripts/public_scan.py); keep the two in step.

Scans the lines a change ADDS (not removed lines, not untouched files) for:
secrets and tokens, AWS access keys, 12-digit AWS account IDs, SSN-shaped
numbers (with or without hyphens; synthetic SSNs starting 000 or 666 are
allowed), Windows/Git Bash paths under a user's home folder, files that hold
secrets, and any word in the local blocklist (.scan-blocklist.local.txt,
gitignored: the names in it are themselves the secret).

Usage (run from the repo root):
    python scripts/public_scan.py              # staged changes (pre-commit)
    python scripts/public_scan.py --base REF   # this branch vs REF (CI)

Exit codes: 0 = clean, 1 = hits found, 2 = the scan itself could not run.
Hits show a masked preview, never the full value: CI logs on a public repo
are public too.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

BLOCKLIST_FILE = ".scan-blocklist.local.txt"

# (rule name, pattern). Each pattern is tried against every added line.
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    (
        "github-token",
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})"),
    ),
    ("api-key", re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}")),
    ("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    (
        "secret-assignment",
        re.compile(
            r"(?i)\b(?:aws_secret_access_key|secret|token|password|passwd|api_?key)"
            r"\w*\s*[:=]\s*['\"]?[A-Za-z0-9/+_.\-]{16,}"
        ),
    ),
    ("aws-account-id", re.compile(r"(?<![\w.-])\d{12}(?![\w-])")),
    # SSN-shaped values. Synthetic SSNs in this repo start with 000 or 666 (area
    # numbers the SSA never issues), so those are allowed; anything else is flagged.
    # HR files often drop the hyphens, so a standalone 9-digit number counts too.
    (
        "ssn",
        re.compile(r"(?<![\w-])(?!000|666)\d{3}-\d{2}-\d{4}(?![\w-])"),
    ),
    ("ssn-no-dashes", re.compile(r"(?<![\w.-])(?!000|666)\d{9}(?![\w-])")),
    (
        "windows-user-path",
        re.compile(
            r"(?i)(?:\b[a-z]:[\\/]+|(?<![\w.])/[a-z]/)users[\\/]+"
            r"(?!public\b|default\b)(?=[\w.-])[\w.-]+"
        ),
    ),
]

# Files that should never be committed, whatever is inside them.
SECRET_FILE_NAMES = re.compile(
    r"(?i)(?:^|/)(?:\.env(?:\..+)?|[^/]*\.env|profiles\.yml|credentials"
    r"|[^/]*\.pem|\.scan-blocklist\.local\.txt)$"
)


@dataclass(frozen=True)
class Hit:
    """One finding: where it is, which rule fired and a masked preview."""

    file: str
    line: int
    rule: str
    preview: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line}: [{self.rule}] {self.preview}"


def mask(value: str) -> str:
    """Show only the first 4 characters of a match."""
    return value[:4] + "..." if len(value) > 4 else value


def load_blocklist(path: Path) -> list[str]:
    """Read blocklist words: one per line; blank lines and # comments skipped."""
    if not path.exists():
        return []
    words = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        word = raw.strip()
        if word and not word.startswith("#"):
            words.append(word)
    return words


def build_rules(blocklist: list[str]) -> list[tuple[str, re.Pattern[str]]]:
    """The fixed patterns plus one whole-word, case-insensitive rule per word."""
    rules = list(PATTERNS)
    for word in blocklist:
        rules.append(
            ("blocklist", re.compile(r"(?i)(?<!\w)" + re.escape(word) + r"(?!\w)"))
        )
    return rules


def scan_line(
    text: str, rules: list[tuple[str, re.Pattern[str]]]
) -> list[tuple[str, str]]:
    """Return (rule, masked match) for every rule that matches this line."""
    found = []
    for name, pattern in rules:
        match = pattern.search(text)
        if match:
            # Blocklist words are the secret: show no part of them, even masked.
            hidden = name == "blocklist"
            found.append((name, "(word hidden)" if hidden else mask(match.group(0))))
    return found


def scan_diff(diff_text: str, rules: list[tuple[str, re.Pattern[str]]]) -> list[Hit]:
    """Scan a `git diff --unified=0` for added lines and new secret-named files."""
    hits: list[Hit] = []
    current_file = ""
    line_no = 0
    in_hunk = False
    for raw in diff_text.splitlines():
        if raw.startswith("diff --git "):
            in_hunk = False
            continue
        if not in_hunk and raw.startswith("+++ "):
            target = raw[4:]
            current_file = target.removeprefix("b/")
            if current_file != "/dev/null" and SECRET_FILE_NAMES.search(current_file):
                hits.append(Hit(current_file, 0, "secret-file", current_file))
            continue
        if raw.startswith("@@"):
            in_hunk = True
            header = re.search(r"\+(\d+)", raw)
            line_no = int(header.group(1)) if header else 0
            continue
        if in_hunk and raw.startswith("+"):
            for rule, preview in scan_line(raw[1:], rules):
                hits.append(Hit(current_file, line_no, rule, preview))
            line_no += 1
    return hits


def git_diff(base: str | None) -> str:
    """Staged changes, or this branch's changes since `base`."""
    args = ["git", "diff", "--unified=0", "--no-color", "--no-ext-diff"]
    args += [f"{base}...HEAD"] if base else ["--cached"]
    result = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", help="scan this branch's changes since REF")
    args = parser.parse_args(argv)

    try:
        diff_text = git_diff(args.base)
    except RuntimeError as err:
        print(f"public_scan: could not read the diff: {err}", file=sys.stderr)
        return 2

    rules = build_rules(load_blocklist(Path(BLOCKLIST_FILE)))
    hits = scan_diff(diff_text, rules)
    if not hits:
        print("public_scan: clean")
        return 0
    print(f"public_scan: {len(hits)} hit(s). Remove them before committing:")
    for hit in hits:
        print(f"  {hit}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

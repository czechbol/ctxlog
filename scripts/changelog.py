#!/usr/bin/env python3
import re
import sys


def extract_changelog(version: str, changelog_path: str = "CHANGELOG.md") -> None:
    with open(changelog_path, "r") as f:
        content = f.read()

    # Regex to match the version header and capture its section
    pattern = rf"^## \[{re.escape(version)}\][\s\S]*?(?=^## |\Z)"
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        with open("release_body.txt", "w") as out:
            out.write(match.group().strip() + "\n")
    else:
        print(f"No changelog found for version {version}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    version = None
    if len(sys.argv) > 1:
        version = sys.argv[1]
    elif not sys.stdin.isatty():
        version = sys.stdin.read().strip()

    if version is None:
        print("Please provide a version as an argument or via stdin.", file=sys.stderr)
        sys.exit(1)
    extract_changelog(version)

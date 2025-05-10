#!/usr/bin/env python3
import re
import sys
from datetime import date


def update_docs_version(version: str, conf_path: str = "docs/source/conf.py") -> None:
    with open(conf_path, "r") as f:
        content = f.read()

    # Update the version in the conf.py file
    version_pattern = r"^release\s*=\s*['\"]\d+\.\d+\.\d+['\"]"
    new_version_line = f"release = '{version}'"
    updated_content = re.sub(
        version_pattern, new_version_line, content, flags=re.MULTILINE
    )

    with open(conf_path, "w") as f:
        f.write(updated_content)


def extract_changelog(version: str, changelog_path: str = "CHANGELOG.md") -> None:
    today = date.today().isoformat()
    with open(changelog_path, "r") as f:
        content = f.read()

    unreleased_pattern = r"^## \[Unreleased\][\s\S]*?(?=^## |\Z)"
    unreleased_match = re.search(unreleased_pattern, content, re.MULTILINE)
    if unreleased_match:
        section = unreleased_match.group()
        # Replace 'Unreleased' with version and date
        replaced_section = re.sub(
            r"^## \[Unreleased\]",
            f"## [{version}] - {today}",
            section,
            flags=re.MULTILINE,
        )
        # Update the original file
        new_content = content.replace(section, replaced_section)
        with open(changelog_path, "w") as f:
            f.write(new_content)
        content = new_content  # Use updated content for extraction

    # Now, always try to find the version section
    version_pattern = rf"^## \[{re.escape(version)}\](?: - \d{{4}}-\d{{2}}-\d{{2}})?[\s\S]*?(?=^## |\Z)"
    version_match = re.search(version_pattern, content, re.MULTILINE)
    if version_match:
        with open("release_body.txt", "w") as out:
            out.write(version_match.group().strip() + "\n")
        return

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

    update_docs_version(version)
    extract_changelog(version)

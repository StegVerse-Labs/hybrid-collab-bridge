#!/usr/bin/env python3
"""Normalize the managed README workflow-badge block deterministically."""

import os
import pathlib
import re

README = pathlib.Path("README.md")
START = "<!-- badges:start -->"
END = "<!-- badges:end -->"
CANONICAL = [
    ("autopatch-apply", "AutoPatch Apply"),
    ("autopatch-reindex", "AutoPatch Reindex"),
    ("autodocs", "AutoDocs"),
    ("docs-badge-sync", "Badges Keeper"),
    ("export-hcb", "Export HCB"),
]
BADGE_RE = re.compile(r"\[!\[[^\]]+\]\([^\n]+?\)\]\([^\n]+?\)")


def wf_exists(name: str) -> bool:
    return any(
        pathlib.Path(f".github/workflows/{name}.{suffix}").exists()
        for suffix in ("yml", "yaml")
    )


def wf_badge(repo: str, name: str, label: str) -> str:
    repository = repo or "StegVerse/unknown"
    workflow = f"{name}.yml"
    base = f"https://github.com/{repository}/actions/workflows/{workflow}"
    return f"[![{label}]({base}/badge.svg)]({base})"


def unique(items: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output


def ensure_block(text: str) -> str:
    if START in text and END in text:
        return text
    return f"{START}\n{END}\n\n{text}"


def split_badges(block: str) -> list[str]:
    """Extract complete Markdown badges without newline-sensitive substitution."""
    matches = BADGE_RE.findall(block)
    if matches:
        return [badge.strip() for badge in matches]
    return [line.strip() for line in block.splitlines() if line.strip()]


def join_badges(lines: list[str]) -> str:
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    if not README.exists():
        print("README.md not found; skipping.")
        return 0

    text = ensure_block(README.read_text(encoding="utf-8"))
    head, rest = text.split(START, 1)
    middle, tail = rest.split(END, 1)
    badges = split_badges(middle.strip())

    for workflow, _ in CANONICAL:
        badges = [
            badge
            for badge in badges
            if f"actions/workflows/{workflow}.yml" not in badge
            and f"actions/workflows/{workflow}.yaml" not in badge
        ]

    repository = os.getenv("GITHUB_REPOSITORY", "").strip()
    canonical_badges = [
        wf_badge(repository, workflow, label)
        for workflow, label in CANONICAL
        if wf_exists(workflow)
    ]
    badges = unique(canonical_badges + badges)

    new_block = join_badges(badges)
    new_text = f"{head}{START}\n{new_block}{END}{tail}"
    if new_text != text:
        README.write_text(new_text, encoding="utf-8")
        print("README badges updated.")
    else:
        print("README badges already up-to-date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

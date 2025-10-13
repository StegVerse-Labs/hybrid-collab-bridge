#!/usr/bin/env python3
import os, re, pathlib
REPO   = os.getenv("GITHUB_REPOSITORY", "").strip()
README = pathlib.Path("README.md")
START  = "<!-- badges:start -->"
END    = "<!-- badges:end -->"
CANONICAL = [
    ("autopatch-apply",   "AutoPatch Apply"),
    ("autopatch-reindex", "AutoPatch Reindex"),
    ("autodocs",          "AutoDocs"),
    ("docs-badge-sync",   "Badges Keeper"),
    ("export-hcb",        "Export HCB"),
]
def wf_exists(name:str)->bool:
    p1 = pathlib.Path(f".github/workflows/{name}.yml")
    p2 = pathlib.Path(f".github/workflows/{name}.yaml")
    return p1.exists() or p2.exists()
def wf_badge(repo:str, name:str, label:str)->str:
    r = repo or "StegVerse/unknown"
    return f"[![{label}](https://github.com/{r}/actions/workflows/{name}.yml/badge.svg)](https://github.com/{r}/actions/workflows/{name}.yml)"
def unique(seq):
    out, seen = [], set()
    for s in seq:
        if s not in seen:
            seen.add(s); out.append(s)
    return out
def ensure_block(text:str):
    if START in text and END in text:
        return text
    return f"{START}\n{END}\n\n{text}"
def split_badges(block:str):
    block = re.sub(r"\\)\\s*\\(", ")\\n(", block.strip())
    return [ln.strip() for ln in block.splitlines() if ln.strip()]
def join_badges(lines): return " ".join(lines).strip() + "\\n"
def main():
    if not README.exists():
        print("README.md not found; skipping."); return 0
    text = README.read_text(encoding="utf-8")
    text = ensure_block(text)
    head, rest = text.split(START, 1)
    mid, tail  = rest.split(END, 1)
    block = mid.strip()
    badges = split_badges(block) if block else []
    for wf, _ in CANONICAL:
        badges = [b for b in badges if f"actions/workflows/{wf}.yml" not in b and f"actions/workflows/{wf}.yaml" not in b]
    repo = os.getenv("GITHUB_REPOSITORY","").strip()
    for wf, label in CANONICAL:
        if wf_exists(wf):
            badges.insert(0, wf_badge(repo, wf, label))
    badges = unique(badges)
    new_block = join_badges(badges)
    new_text  = f"{head}{START}\\n{new_block}{END}{tail}"
    if new_text != text:
        README.write_text(new_text, encoding="utf-8")
        print("README badges updated.")
    else:
        print("README badges already up-to-date.")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())

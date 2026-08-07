#!/usr/bin/env python3
"""
Keeps each plugin's three manifests on one, correctly-incrementing version.

Every plugin carries the same `version` in `plugin.json`, `.claude-plugin/plugin.json`, and
`.cursor-plugin/plugin.json` (see CLAUDE.md's "Per-IDE manifest convention"). A commit that touches
a plugin is supposed to bump that version, but nothing enforces it — a forgotten bump, an edit to
only one of the three files, or an accidental downgrade all land silently. This script runs after
such a commit and repairs it:

  1. For each plugin whose directory changed between BASE_SHA and HEAD, read the version each of
     the three manifests declares now, and what they declared at BASE_SHA.
  2. If the highest version declared now is a genuine semver increase over the highest version
     declared at BASE_SHA, that is the intended bump — every manifest is synced to it.
  3. Otherwise (unchanged, or a downgrade in any file), nothing in this commit can be trusted as
     the new version, so the previous version's patch component is incremented by one instead.
  4. All three manifests are rewritten to agree on the resulting version.

A plugin with no BASE_SHA history (new in this push) has nothing to compare against, so step 2/3 is
skipped and its declared versions are simply synced to the highest one given.

Idempotent: re-running against an already-consistent set of manifests touches nothing, which is
what lets the calling workflow's rebase-retry loop call this again after every reset.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
PLUGINS_DIR = REPO_ROOT / "plugins"
ZERO_SHA = "0" * 40

MANIFEST_LABELS = ("plugin.json", ".claude-plugin/plugin.json", ".cursor-plugin/plugin.json")

VERSION_RE = re.compile(
    r"^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$"
)


def parse_version(raw: str):
    m = VERSION_RE.match(raw.strip())
    if not m:
        return None
    major, minor, patch, pre = m.groups()
    pre_ids = tuple(pre.split(".")) if pre else None
    return (int(major), int(minor), int(patch), pre_ids)


def _pre_key(ident: str):
    return (0, int(ident)) if ident.isdigit() else (1, ident)


def compare_versions(a, b) -> int:
    """Semver precedence: numeric core first, then pre-release (absent beats present)."""
    if a[:3] != b[:3]:
        return -1 if a[:3] < b[:3] else 1
    a_pre, b_pre = a[3], b[3]
    if a_pre is None and b_pre is None:
        return 0
    if a_pre is None:
        return 1
    if b_pre is None:
        return -1
    ak, bk = [_pre_key(x) for x in a_pre], [_pre_key(x) for x in b_pre]
    if ak == bk:
        return 0
    return -1 if ak < bk else 1


def max_version(raw_versions):
    """Highest of a set of raw version strings, or None if none parse as semver."""
    best_raw, best_parsed = None, None
    for raw in raw_versions:
        parsed = parse_version(raw)
        if parsed is None:
            continue
        if best_parsed is None or compare_versions(parsed, best_parsed) > 0:
            best_raw, best_parsed = raw, parsed
    return best_raw


def bump_patch(raw: str) -> str:
    major, minor, patch, _pre = parse_version(raw)
    return f"{major}.{minor}.{patch + 1}"


def git_show(ref: str, relpath: str):
    result = subprocess.run(
        ["git", "show", f"{ref}:{relpath}"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    return result.stdout if result.returncode == 0 else None


def write_json(path: pathlib.Path, data) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def changed_plugin_ids(base_sha: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", base_sha, "HEAD", "--", "plugins"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    ids = set()
    for line in result.stdout.splitlines():
        parts = line.split("/")
        if len(parts) >= 2 and parts[0] == "plugins":
            ids.add(parts[1])
    return sorted(ids)


def process_plugin(plugin_id: str, base_sha: str, problems: list[str], touched: list[str], report: list[str]) -> None:
    root = PLUGINS_DIR / plugin_id
    current = {}   # label -> raw version string
    loaded = {}    # label -> (path, parsed json data)

    for label in MANIFEST_LABELS:
        path = root / label
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            problems.append(f"{plugin_id}: cannot parse {label}: {e}")
            continue
        version = data.get("version")
        if not version:
            problems.append(f"{plugin_id}: {label} has no 'version' field")
            continue
        current[label] = version
        loaded[label] = (path, data)

    if not current:
        return

    candidate = max_version(current.values())
    if candidate is None:
        problems.append(f"{plugin_id}: no manifest has a parseable semver version {current}")
        return

    baseline = {}
    for label in MANIFEST_LABELS:
        content = git_show(base_sha, f"plugins/{plugin_id}/{label}")
        if content is None:
            continue
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            continue
        version = data.get("version")
        if version:
            baseline[label] = version

    prev_candidate = max_version(baseline.values()) if baseline else None

    if prev_candidate is None:
        final, reason = candidate, "new plugin — synced to its declared version"
    elif compare_versions(parse_version(candidate), parse_version(prev_candidate)) > 0:
        final, reason = candidate, f"valid bump from {prev_candidate}"
    else:
        final, reason = bump_patch(prev_candidate), f"not upgraded from {prev_candidate} — bumped patch"

    changed = False
    for label, (path, data) in loaded.items():
        if data.get("version") != final:
            data["version"] = final
            write_json(path, data)
            touched.append(path.relative_to(REPO_ROOT).as_posix())
            changed = True

    if changed:
        report.append(f"{plugin_id}: -> {final} ({reason})")


def main() -> int:
    base_sha = os.environ.get("BASE_SHA", "").strip()
    if not base_sha or base_sha == ZERO_SHA:
        print("No usable base commit (new branch, or none given) — skipping version check.")
        return 0
    if subprocess.run(["git", "cat-file", "-e", base_sha], cwd=REPO_ROOT).returncode != 0:
        print(f"Base commit {base_sha} not found in this checkout — skipping.", file=sys.stderr)
        return 0

    plugin_ids = [p for p in changed_plugin_ids(base_sha) if (PLUGINS_DIR / p).is_dir()]
    if not plugin_ids:
        print("No plugin directories changed — nothing to check.")
        return 0

    problems: list[str] = []
    touched: list[str] = []
    report: list[str] = []
    for plugin_id in plugin_ids:
        process_plugin(plugin_id, base_sha, problems, touched, report)

    touched_out = os.environ.get("TOUCHED_FILES_OUT")
    if touched_out:
        pathlib.Path(touched_out).write_text(
            "".join(f"{p}\n" for p in touched), encoding="utf-8"
        )
    names_out = os.environ.get("CHANGED_PLUGINS_OUT")
    if names_out:
        changed_ids = sorted({line.split(":", 1)[0] for line in report})
        pathlib.Path(names_out).write_text(",".join(changed_ids), encoding="utf-8")

    for problem in problems:
        print(f"  ! {problem}", file=sys.stderr)
    if report:
        print(f"Checked {len(plugin_ids)} plugin(s); updated {len(touched)} file(s):")
        for line in report:
            print(f"  - {line}")
    else:
        print(f"Checked {len(plugin_ids)} plugin(s) — versions already in sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

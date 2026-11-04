"""Report how a pyproject.toml drifts from the python-project baseline, or apply it.

Uses:

- Report drift from the baseline (the default, check mode).
- Apply the baseline's `[tool.*]` tables (`--write`).
- Change the typing mode (`--typing-mode <mode> --write`).
- Add an optional checker's tables (`--with ty` or `--with pyrefly`).

The baseline is the tool tables in `assets/pyproject/`, plus the settings for the
project's typing mode (`[tool.basedpyright] typeCheckingMode`). What the script
knows about each tool lives in `assets/pyproject/toolsets.toml`. Check mode exits 1
on any finding except RELAXED. `--write` keeps the file's comments and prints what
still needs a hand: dev dependencies, conflicting settings, and the build backend.
"""

import argparse
import json
import re
import sys

from pathlib import Path
from typing import Any

import tomlkit

from tomlkit.toml_document import TOMLDocument

from python_project.dependencies import find_dependency_gaps, find_version_gaps
from python_project.models import (
    REVIEW_ONLY,
    Finding,
    KeyPath,
    Record,
    ensure_table,
    lookup,
    render,
)
from python_project.toolsets import (
    DEFAULT_TYPING_MODE,
    TYPING_MODES,
    config_tables,
    forbidden,
    load_baseline,
    load_toolsets,
    manifest_paths,
    packages,
    rule_lists,
)


def compare(
    *,
    expected: Any,
    actual: Any,
    seeded: dict[KeyPath, Any],
    lists: dict[KeyPath, bool],
    path: KeyPath = (),
) -> list[Finding]:
    """Walk the baseline and report keys that are missing or hold another value.

    A seeded key is not compared once present. A rule list is left to
    compare_rule_lists while it holds a list.
    """
    findings = []
    for key, value in expected.items():
        key_path = (*path, key)
        if not isinstance(actual, dict) or key not in actual:
            findings.append(
                Finding(
                    kind="MISSING",
                    path=key_path,
                    detail=f"= {render(value=value)}",
                )
            )
        elif isinstance(value, dict) and isinstance(actual[key], dict):
            nested = compare(
                expected=value,
                actual=actual[key],
                seeded=seeded,
                lists=lists,
                path=key_path,
            )
            findings.extend(nested)
        elif key_path in seeded or (
            key_path in lists and isinstance(actual[key], list)
        ):
            continue
        elif not same_value(left=value, right=actual[key]):
            findings.append(
                Finding(
                    kind="DIFFERS",
                    path=key_path,
                    detail=f"is {render(value=actual[key])}, baseline {render(value=value)}",
                )
            )
    return findings


def compare_rule_lists(
    *,
    expected: Record,
    actual: Record,
    lists: dict[KeyPath, bool],
    banned_entries: dict[KeyPath, set[str]],
    typing_mode: str,
) -> list[Finding]:
    """Report baseline entries a rule list lacks, and entries it should not hold.

    A project's own additions to a list are left alone. Additions to a list that
    relaxes checks turn them off, so they are reported for review, not removed.
    """
    findings = []
    for path, relaxes in sorted(lists.items()):
        wanted = lookup(data=expected, path=path)
        have = lookup(data=actual, path=path)
        if not isinstance(wanted, list) or not isinstance(have, list):
            continue  # compare reports it as MISSING or DIFFERS.
        banned = banned_entries.get(path, set())
        missing = tuple(entry for entry in wanted if entry not in have)
        present = tuple(entry for entry in have if entry in banned)
        extra = tuple(entry for entry in have if entry not in wanted + list(banned))
        relaxed = extra if relaxes else ()
        checks = (
            ("MISSING", missing, "lacks {}"),
            ("EXTRA", present, f"has {{}} - typing mode {typing_mode}"),
            ("RELAXED", relaxed, "turns off {} - confirm it is deliberate"),
        )
        findings += [
            Finding(
                kind=kind,
                path=path,
                detail=template.format(render(value=list(entries))),
                entries=entries,
            )
            for kind, entries, template in checks
            if entries
        ]
    return findings


def same_value(*, left: Any, right: Any) -> bool:
    """Compare two values, treating lists of strings as unordered."""
    if (
        isinstance(left, list)
        and isinstance(right, list)
        and all(isinstance(item, str) for item in left + right)
    ):
        return sorted(left) == sorted(right)
    return left == right


def find_removals(
    *,
    project: Record,
    selected: list[str],
    banned_keys: dict[KeyPath, str],
) -> list[Finding]:
    """Report superseded keys, keys the typing mode forbids, and conflicting ones."""
    groups = (
        ("OBSOLETE", manifest_paths(selected=selected, field=("remove_if_present",))),
        ("EXTRA", banned_keys),
        (
            "CONFLICT",
            manifest_paths(selected=selected, field=("conflicting_settings",)),
        ),
    )
    return [
        Finding(kind=kind, path=path, detail=f"- {reason}")
        for kind, keys in groups
        for path, reason in keys.items()
        if lookup(data=project, path=path) is not None
    ]


def find_build_gap(*, project: Record, selected: list[str]) -> list[Finding]:
    """Report a build backend other than the one a selected package names."""
    toolsets = load_toolsets()
    wanted = [b for name in selected if (b := toolsets[name].get("build_backend"))]
    backend = lookup(data=project, path=("build-system", "build-backend"))
    if not wanted or backend == wanted[0]:
        return []
    return [
        Finding(
            kind="BUILD",
            path=("build-system", "build-backend"),
            detail=f"is {render(value=backend)}, baseline {render(value=wanted[0])}",
        )
    ]


def detect_typing_mode(*, project: Record) -> str:
    """Read the typing mode from the project's basedpyright config.

    Strict mode is `typeCheckingMode = "standard"` plus `strict = ["src"]`. A plain
    `typeCheckingMode = "strict"` also reads as strict, so the script can move it
    to the src-only form.
    """
    config = lookup(data=project, path=("tool", "basedpyright")) or {}
    mode = config.get("typeCheckingMode")
    if mode == "standard" and config.get("strict"):
        return "strict"
    return mode if mode in TYPING_MODES else DEFAULT_TYPING_MODE


def detect_optional_tools(*, project: Record, requested: list[str]) -> list[str]:
    """Combine requested checkers with any the project already configures."""
    return [
        name
        for name in packages(default=False)
        if name in requested
        or any(
            lookup(data=project, path=("tool", table))
            for table in config_tables(package=name)
        )
    ]


def apply(
    *, doc: TOMLDocument, baseline: TOMLDocument, findings: list[Finding]
) -> None:
    """Write fixable findings into doc in place."""
    for finding in findings:
        if not finding.fixable:
            continue
        if finding.entries:
            edit_rule_list(doc=doc, finding=finding)
        elif finding.kind in {"OBSOLETE", "EXTRA"}:
            del lookup(data=doc, path=finding.path[:-1])[finding.path[-1]]
        else:
            parent = ensure_table(doc=doc, path=finding.path[:-1])
            source = lookup(data=baseline, path=finding.path)
            parent[finding.path[-1]] = source


def edit_rule_list(*, doc: TOMLDocument, finding: Finding) -> None:
    """Add a rule list's missing entries, or remove its forbidden ones."""
    rules = lookup(data=doc, path=finding.path)
    if finding.kind == "MISSING":
        rules.extend(finding.entries)
        return
    for index in reversed(range(len(rules))):
        if rules[index] in finding.entries:
            del rules[index]


def format_path(*, path: KeyPath) -> str:
    """Join a key path, quoting keys that are not bare TOML keys."""
    return ".".join(
        key if re.fullmatch(r"[A-Za-z0-9_-]+", key) else json.dumps(key) for key in path
    )


def build_parser() -> argparse.ArgumentParser:
    """Define the command-line interface."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--project", type=Path, default=Path(), help="project root")
    parser.add_argument(
        "--typing-mode",
        choices=TYPING_MODES,
        help="defaults to the project's [tool.basedpyright] typeCheckingMode, else standard",
    )
    parser.add_argument(
        "--with",
        dest="optional_tools",
        action="append",
        choices=packages(default=False),
        default=[],
        help="also configure this checker (repeatable); detected when already present",
    )
    parser.add_argument("--write", action="store_true", help="apply fixable findings")
    return parser


def main(*, argv: list[str] | None = None) -> int:
    """Run the check or the write and return the exit code."""
    args = build_parser().parse_args(argv)
    pyproject = args.project / "pyproject.toml"
    if not pyproject.is_file():
        print(f"No pyproject.toml in {args.project}. Run `uv init --package` first.")
        return 2

    doc = tomlkit.parse(pyproject.read_text(encoding="utf-8"))
    project = doc.unwrap()
    typing_mode = args.typing_mode or detect_typing_mode(project=project)
    optional_tools = detect_optional_tools(
        project=project, requested=args.optional_tools
    )
    selected = [*packages(default=True), *optional_tools]
    baseline = load_baseline(selected=selected, typing_mode=typing_mode)
    expected = baseline.unwrap()
    banned_keys, banned_entries = forbidden(
        selected=selected, typing_mode=typing_mode, baseline=expected
    )
    lists = rule_lists(selected=selected, baseline=expected)
    seeded = manifest_paths(selected=selected, field=("add_if_missing",))

    findings = [
        *compare(expected=expected, actual=project, seeded=seeded, lists=lists),
        *compare_rule_lists(
            expected=expected,
            actual=project,
            lists=lists,
            banned_entries=banned_entries,
            typing_mode=typing_mode,
        ),
        *find_removals(project=project, selected=selected, banned_keys=banned_keys),
        *find_dependency_gaps(project=project, selected=selected),
        *find_version_gaps(project_dir=args.project, selected=selected),
        *find_build_gap(project=project, selected=selected),
    ]

    toolsets = load_toolsets()
    checkers = ", ".join(n for n in selected if "typecheck" in toolsets[n]["functions"])
    print(f"{pyproject} (typing mode: {typing_mode}; checkers: {checkers})")
    if args.write:
        apply(doc=doc, baseline=baseline, findings=findings)
        pyproject.write_text(tomlkit.dumps(doc), encoding="utf-8")
        print(f"  applied {sum(finding.fixable for finding in findings)} change(s)")
        findings = [finding for finding in findings if not finding.fixable]

    for finding in findings:
        print(f"  {finding.kind:<10} {format_path(path=finding.path)} {finding.detail}")
    failing = [finding for finding in findings if finding.kind not in REVIEW_ONLY]
    if not failing:
        print("  matches the baseline")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())

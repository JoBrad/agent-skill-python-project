"""Read toolsets.toml and build the baseline a project is compared against.

toolsets.toml holds which package fills each function, the Poe tasks each
function must provide, and what the commands know about each package: its config
file, tasks, the keys it seeds or supersedes, its rule lists, and its settings per
typing mode.
"""

import tomllib

from functools import cache
from pathlib import Path
from typing import Any

import tomlkit

from tomlkit.toml_document import TOMLDocument

from python_project.models import KeyPath, Record, ensure_table, lookup


SKILL_DIR = Path(__file__).resolve().parents[2]
FRAGMENT_DIR = SKILL_DIR / "assets" / "pyproject"
# What the script knows about each tool; see the file's header.
TOOLSETS_FILE = FRAGMENT_DIR / "toolsets.toml"

TYPING_MODES = ("off", "basic", "standard", "strict")
DEFAULT_TYPING_MODE = "standard"


@cache
def load_manifest() -> dict[str, Any]:
    """Read toolsets.toml whole: selections, task requirements, and packages."""
    return tomllib.loads(TOOLSETS_FILE.read_text(encoding="utf-8"))


def load_toolsets() -> dict[str, dict[str, Any]]:
    """Return the manifest's packages, keyed by package name."""
    return load_manifest()["packages"]


def packages(*, default: bool) -> list[str]:
    """List the packages some function selects, or the optional rest."""
    chosen = set(load_manifest()["tool_selections"].values())
    return [name for name in load_toolsets() if (name in chosen) is default]


def config_tables(*, package: str) -> Any:
    """Return the [tool.*] tables in a package's config file, or {} without one."""
    config_file = load_toolsets()[package].get("config_file")
    if config_file is None:
        return {}
    text = (FRAGMENT_DIR / config_file).read_text(encoding="utf-8")
    return tomlkit.parse(text)["tool"]


def manifest_paths(*, selected: list[str], field: KeyPath) -> dict[KeyPath, Any]:
    """Collect a per-key manifest field across packages, keyed by dotted path.

    A list field maps each path to None; a table field keeps each path's value.
    """
    found: dict[KeyPath, Any] = {}
    for name in selected:
        value = lookup(data=load_toolsets()[name], path=field) or {}
        pairs = (
            value.items() if isinstance(value, dict) else dict.fromkeys(value).items()
        )
        found.update({tuple(path.split(".")): detail for path, detail in pairs})
    return found


def load_baseline(*, selected: list[str], typing_mode: str) -> TOMLDocument:
    """Merge the selected packages' config files and apply the typing mode."""
    baseline = tomlkit.document()
    tool = tomlkit.table(is_super_table=True)
    baseline["tool"] = tool
    for package in selected:
        for name, table in config_tables(package=package).items():
            tool[name] = table
        for name, task in load_toolsets()[package].get("tasks", {}).items():
            # Inline, so each task reads as one line in the project's pyproject.
            entry = tomlkit.inline_table()
            entry.update(task)
            ensure_table(doc=baseline, path=("tool", "poe", "tasks"))[name] = entry
    settings = manifest_paths(selected=selected, field=("typing_modes", typing_mode))
    for path, value in settings.items():
        parent = ensure_table(doc=baseline, path=path[:-1])
        current = parent.get(path[-1])
        if isinstance(value, list) and isinstance(current, list):
            current.extend([entry for entry in value if entry not in current])
        else:
            parent[path[-1]] = value
    return baseline


def forbidden(
    *, selected: list[str], typing_mode: str, baseline: Record
) -> tuple[dict[KeyPath, str], dict[KeyPath, set[str]]]:
    """Find the keys and list entries other typing modes set and this one does not.

    A list the baseline holds loses only those entries; anything else loses its key.
    """
    current = manifest_paths(selected=selected, field=("typing_modes", typing_mode))
    keys: dict[KeyPath, str] = {}
    entries: dict[KeyPath, set[str]] = {}
    for mode in TYPING_MODES:
        settings = manifest_paths(selected=selected, field=("typing_modes", mode))
        for path, value in settings.items():
            if isinstance(value, list) and lookup(data=baseline, path=path) is not None:
                kept = set(current.get(path, []))
                entries.setdefault(path, set()).update(set(value) - kept)
            elif path not in current:
                keys[path] = f"typing mode {typing_mode} does not set it"
    return keys, entries


def rule_lists(*, selected: list[str], baseline: Record) -> dict[KeyPath, bool]:
    """Expand the adds_to and relaxes paths; True marks a list that relaxes checks."""
    found: dict[KeyPath, bool] = {}
    for field, relaxes in (("adds_to", False), ("relaxes", True)):
        for pattern in manifest_paths(selected=selected, field=(field,)):
            parent = pattern[:-1]
            keys = lookup(data=baseline, path=parent) if pattern[-1] == "*" else None
            found.update({(*parent, key): relaxes for key in keys or [pattern[-1]]})
    return found

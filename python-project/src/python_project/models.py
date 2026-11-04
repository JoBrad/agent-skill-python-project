"""Shared types and helpers for the python-project baseline commands.

A Finding is one way a project differs from the baseline. Every check returns a
list of them, and the CLI prints and applies them.
"""

import json

from dataclasses import dataclass
from typing import Any

import tomlkit

from tomlkit.toml_document import TOMLDocument


# Findings that ask for a look but never fail the check.
REVIEW_ONLY = {"RELAXED"}
# Findings that --write applies; the rest need a hand.
FIXABLE = {"MISSING", "DIFFERS", "OBSOLETE", "EXTRA"}

type KeyPath = tuple[str, ...]
type Record = dict[str, Any]


@dataclass(frozen=True)
class Finding:
    """One way the project differs from the baseline."""

    kind: str
    path: KeyPath
    detail: str
    # List entries to add or remove, for findings on a rule list.
    entries: tuple[str, ...] = ()

    @property
    def fixable(self) -> bool:
        """Whether --write can apply this finding."""
        return self.kind in FIXABLE


def render(*, value: Any) -> str:
    """Render a value for a one-line report."""
    return "(table)" if isinstance(value, dict) else json.dumps(value)


def lookup(*, data: Any, path: KeyPath) -> Any:
    """Return the value at path, or None when any part of it is absent."""
    for key in path:
        if not isinstance(data, dict) or key not in data:
            return None
        data = data[key]
    return data


def ensure_table(*, doc: TOMLDocument, path: KeyPath) -> Any:
    """Return the table at path, creating any missing tables along the way."""
    current: Any = doc
    for depth, key in enumerate(path):
        if key not in current:
            # A table that only holds other tables renders as a dotted header.
            current[key] = tomlkit.table(is_super_table=depth < len(path) - 1)
        current = current[key]
    return current

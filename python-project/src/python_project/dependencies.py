"""Check that a project's dev tools are installed and match version specifiers.

Findings output a uv command to resolve the issue.
"""

import re
import tomllib

from pathlib import Path

from packaging.specifiers import SpecifierSet

from python_project.models import Finding, Record, lookup
from python_project.toolsets import load_toolsets


def requirement_name(*, requirement: str) -> str:
    """Return the normalized distribution name from a requirement string."""
    match = re.match(r"[A-Za-z0-9._-]+", requirement.strip())
    name = match.group(0) if match else requirement
    return re.sub(r"[-_.]+", "-", name).lower()


def requirement(*, package: str) -> str:
    """Return the package with its manifest specifier, quoted for a shell command."""
    specifier = load_toolsets()[package].get("specifier")
    return f'"{package}{specifier}"' if specifier else package


def find_dependency_gaps(*, project: Record, selected: list[str]) -> list[Finding]:
    """Report dev tools that are missing from the dev group or sit in runtime deps."""
    toolsets = load_toolsets()
    wanted = [name for name in selected if toolsets[name].get("dev_dependency", True)]
    dev_group = lookup(data=project, path=("dependency-groups", "dev")) or []
    dev_names = {
        requirement_name(requirement=i) for i in dev_group if isinstance(i, str)
    }
    runtime = lookup(data=project, path=("project", "dependencies")) or []
    runtime_names = {requirement_name(requirement=item) for item in runtime}

    findings = []
    misplaced = sorted(name for name in wanted if name in runtime_names)
    if misplaced:
        findings.append(
            Finding(
                kind="MISPLACED",
                path=("project", "dependencies"),
                detail=f"holds dev tools - uv remove {' '.join(misplaced)}",
            )
        )
    missing = [name for name in wanted if name not in dev_names]
    if missing:
        command = "uv add --dev " + " ".join(requirement(package=n) for n in missing)
        findings.append(
            Finding(
                kind="DEPENDENCY",
                path=("dependency-groups", "dev"),
                detail=f"is missing tools - {command}",
            )
        )
    return findings


def find_version_gaps(*, project_dir: Path, selected: list[str]) -> list[Finding]:
    """Report locked dev tools whose version falls outside the manifest specifier.

    Reads the versions from uv.lock; a project without one is not checked.
    """
    lock_file = project_dir / "uv.lock"
    if not lock_file.is_file():
        return []
    lock = tomllib.loads(lock_file.read_text(encoding="utf-8"))
    locked = {
        requirement_name(requirement=entry["name"]): entry.get("version")
        for entry in lock.get("package", [])
    }
    findings = []
    for name in selected:
        specifier = load_toolsets()[name].get("specifier")
        version = locked.get(name)
        if specifier is None or version is None:
            continue
        if not SpecifierSet(specifier).contains(version, prereleases=True):
            findings.append(
                Finding(
                    kind="VERSION",
                    path=("dependency-groups", "dev"),
                    detail=(
                        f"has {name} {version}, needs {specifier} - "
                        f"uv add --dev {requirement(package=name)}"
                    ),
                )
            )
    return findings

"""Measure test coverage of the Python lines changed since a base commit.

New code ships with tests covering at least 90% of it, even when the project as a
whole sits below that. This reads coverage.py's JSON report and intersects it with
the lines added since the base: committed, staged, and unstaged changes, plus
untracked files. Branches count when their source line is a changed line.

Run the tests with `--cov --cov-report=json` first.
"""

import argparse
import json
import re
import subprocess
import sys

from dataclasses import dataclass
from pathlib import Path


DEFAULT_FAIL_UNDER = 90.0
HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


@dataclass(frozen=True)
class FileCoverage:
    """Covered and total measurable units among one file's changed lines."""

    path: str
    covered: int
    total: int
    missing_lines: list[int]


def git(*args: str) -> str:
    """Run a git command and return its stdout."""
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
    return result.stdout


def default_base() -> str:
    """Use the merge base with the remote default branch, else HEAD."""
    try:
        return git("merge-base", "HEAD", "origin/HEAD").strip()
    except subprocess.CalledProcessError:
        return "HEAD"


def parse_added_lines(*, diff: str) -> dict[str, set[int]]:
    """Map each file in a `git diff -U0` to the line numbers it adds."""
    added: dict[str, set[int]] = {}
    current = None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            target = line[4:]
            current = None if target == "/dev/null" else target.removeprefix("b/")
            if current is not None:
                added.setdefault(current, set())
            continue
        match = HUNK_HEADER.match(line)
        if match and current is not None:
            start = int(match.group(1))
            count = int(match.group(2)) if match.group(2) is not None else 1
            added[current].update(range(start, start + count))
    return added


def changed_lines(*, base: str) -> dict[str, set[int]]:
    """Collect added lines in tracked .py files plus every line of untracked ones."""
    added = parse_added_lines(
        diff=git("diff", "-U0", "--no-color", "--no-ext-diff", base, "--", "*.py")
    )
    untracked = git("ls-files", "--others", "--exclude-standard", "--", "*.py")
    for name in untracked.splitlines():
        line_count = len(Path(name).read_text(encoding="utf-8").splitlines())
        added[name] = set(range(1, line_count + 1))
    return added


def measure(*, report: dict, changes: dict[str, set[int]]) -> list[FileCoverage]:
    """Intersect a coverage.py JSON report with the changed lines."""
    results = []
    for name, data in sorted(report.get("files", {}).items()):
        lines = changes.get(Path(name).as_posix())
        if not lines:
            continue
        executed = lines & set(data.get("executed_lines", []))
        missing = lines & set(data.get("missing_lines", []))
        branches_hit = [
            arc for arc in data.get("executed_branches", []) if arc[0] in lines
        ]
        branches_missed = [
            arc for arc in data.get("missing_branches", []) if arc[0] in lines
        ]
        total = len(executed) + len(missing) + len(branches_hit) + len(branches_missed)
        if total:
            results.append(
                FileCoverage(
                    path=name,
                    covered=len(executed) + len(branches_hit),
                    total=total,
                    missing_lines=sorted(missing),
                )
            )
    return results


def main(*, argv: list[str] | None = None) -> int:
    """Report changed-line coverage and return 1 when it is under the threshold."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--coverage-json", type=Path, default=Path("coverage.json"))
    parser.add_argument("--base", help="commit to diff against (default: merge base)")
    parser.add_argument("--fail-under", type=float, default=DEFAULT_FAIL_UNDER)
    args = parser.parse_args(argv)

    if not args.coverage_json.is_file():
        print(f"{args.coverage_json} not found. Run pytest with --cov-report=json.")
        return 2
    report = json.loads(args.coverage_json.read_text(encoding="utf-8"))
    results = measure(
        report=report, changes=changed_lines(base=args.base or default_base())
    )
    if not results:
        print("No measurable changed lines.")
        return 0

    covered = sum(result.covered for result in results)
    total = sum(result.total for result in results)
    for result in results:
        percent = 100 * result.covered / result.total
        missing = ", ".join(str(line) for line in result.missing_lines) or "-"
        print(f"{result.path}: {percent:.1f}% (missing lines: {missing})")
    percent = 100 * covered / total
    print(f"Changed-line coverage: {percent:.1f}% (threshold {args.fail_under:.0f}%)")
    return 0 if percent >= args.fail_under else 1


if __name__ == "__main__":
    sys.exit(main())

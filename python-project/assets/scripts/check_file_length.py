"""Fail when a Python file grows past the line limit.

Ruff has no file-length rule. A file over the limit, or one holding more than about
two concerns, should be split into a subpackage, not exempted.
"""

import argparse
import sys

from pathlib import Path


DEFAULT_MAX_LINES = 500


def find_long_files(*, paths: list[Path], max_lines: int) -> list[tuple[Path, int]]:
    """Return each .py file under paths with more than max_lines lines."""
    files = []
    for path in paths:
        files.extend([path] if path.is_file() else sorted(path.rglob("*.py")))
    long_files = []
    for file in files:
        count = len(file.read_text(encoding="utf-8").splitlines())
        if count > max_lines:
            long_files.append((file, count))
    return long_files


def main(*, argv: list[str] | None = None) -> int:
    """Report long files and return 1 when there are any."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("paths", nargs="*", type=Path, default=[Path("src")])
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES)
    args = parser.parse_args(argv)

    long_files = find_long_files(paths=args.paths, max_lines=args.max_lines)
    for file, count in long_files:
        print(f"{file}: {count} lines (limit {args.max_lines})")
    return 1 if long_files else 0


if __name__ == "__main__":
    sys.exit(main())

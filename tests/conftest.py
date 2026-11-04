"""Shared pytest fixtures, and the import path for the skill's asset scripts.

pytest loads this file on its own, and every fixture defined here is available to
every test without an import. Put test-data builders in tests/factories.py and
import them as `from tests.factories import ...`; `pythonpath = ["."]` in
[tool.pytest] makes that work without any __init__.py files.

The skill package imports as `python_project`. The asset scripts under
python-project/assets/scripts/ are standalone files that the skill copies into
projects, not a package, so their directory goes on sys.path here and tests
import them by module name (`import check_file_length`).
"""

import sys

from pathlib import Path


ASSET_SCRIPTS_DIR = (
    Path(__file__).resolve().parents[1] / "python-project/assets/scripts"
)
sys.path.insert(0, str(ASSET_SCRIPTS_DIR))

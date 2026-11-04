"""Shared pytest fixtures.

pytest loads this file on its own, and every fixture defined here is available to
every test without an import. Put test-data builders in tests/factories.py and
import them as `from tests.factories import ...`; `pythonpath = ["."]` in
[tool.pytest] makes that work without any __init__.py files.
"""

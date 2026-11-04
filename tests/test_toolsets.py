import json

from pathlib import Path

import jsonschema
import pytest

from python_project import toolsets


SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / "toolsets.schema.json"


def validate(*, manifest):
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(instance=manifest, schema=schema)


def test_manifest_matches_its_schema():
    validate(manifest=toolsets.load_manifest())


@pytest.mark.parametrize(
    ("package", "field", "value"),
    [
        ("ruff", "conflict_settings", {}),
        ("ruff", "adds_to", ["ruff.lint.select"]),
        ("pytest", "tasks", {"test": {"shell": "pytest && rm -rf /"}}),
        ("ty", "typing_modes", {"off": {}}),
    ],
)
def test_schema_rejects_typos_and_unsafe_tasks(package, field, value):
    manifest = json.loads(json.dumps(toolsets.load_manifest()))
    manifest["packages"][package][field] = value
    with pytest.raises(jsonschema.ValidationError):
        validate(manifest=manifest)


# The manifest: every default sits in its package's functions, every function has
# exactly one default, and every config file exists.
def test_selections_point_to_packages_that_fill_the_function():
    manifest = toolsets.load_manifest()
    for function, package in manifest["tool_selections"].items():
        assert function in manifest["packages"][package]["functions"], function


def test_every_function_has_a_selection():
    manifest = toolsets.load_manifest()
    named = {f for spec in manifest["packages"].values() for f in spec["functions"]}
    assert named == set(manifest["tool_selections"])


def test_task_requirements_name_known_functions():
    # A function with no required tasks may be left out of task_requirements.
    manifest = toolsets.load_manifest()
    assert set(manifest["task_requirements"]) <= set(manifest["tool_selections"])


def test_packages_that_fill_a_function_supply_its_tasks():
    # Optional add-ons (no selection) are exempt: they run alongside the
    # selected package and must not replace its tasks.
    manifest = toolsets.load_manifest()
    chosen = set(manifest["tool_selections"].values())
    for name, spec in manifest["packages"].items():
        supplied = set(spec.get("tasks", {}))
        for function in spec["functions"] if name in chosen else []:
            required = set(manifest["task_requirements"].get(function, []))
            assert required <= supplied, (name, function, required - supplied)


def test_check_sequence_names_supplied_tasks():
    manifest = toolsets.load_manifest()
    chosen = set(manifest["tool_selections"].values())
    supplied = {
        task for name in chosen for task in manifest["packages"][name].get("tasks", {})
    }
    check = manifest["packages"]["poethepoet"]["tasks"]["check"]["sequence"]
    assert set(check) <= supplied


def test_toolsets_config_files_exist():
    for name, spec in toolsets.load_toolsets().items():
        if "config_file" in spec:
            assert (toolsets.FRAGMENT_DIR / spec["config_file"]).is_file(), name


def test_config_file_tables_need_not_match_package_name():
    assert "coverage" in toolsets.config_tables(package="pytest-cov")
    assert toolsets.config_tables(package="pre-commit") == {}

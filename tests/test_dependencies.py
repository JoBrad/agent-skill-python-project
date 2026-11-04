import pytest

from python_project import dependencies, sync_pyproject


def write_lock(*, project, **versions):
    packages = "".join(
        f'[[package]]\nname = "{name}"\nversion = "{version}"\n\n'
        for name, version in versions.items()
    )
    (project / "uv.lock").write_text(f"version = 1\n\n{packages}", encoding="utf-8")


def test_requirement_name_normalizes():
    assert dependencies.requirement_name(requirement="Pytest_Cov>=7") == "pytest-cov"
    assert dependencies.requirement_name(requirement="ty==0.0.90") == "ty"


@pytest.mark.parametrize(
    ("version", "reported"),
    [("0.15.2", True), ("0.17.1", False), ("0.18.0rc1", False)],
)
def test_locked_version_is_checked_against_specifier(tmp_path, version, reported):
    write_lock(project=tmp_path, ruff=version)
    findings = dependencies.find_version_gaps(project_dir=tmp_path, selected=["ruff"])
    assert bool(findings) is reported
    if reported:
        assert findings[0].kind == "VERSION"
        assert findings[0].detail == (
            f'has ruff {version}, needs >=0.17.1 - uv add --dev "ruff>=0.17.1"'
        )


def test_version_check_skips_missing_lock_unpinned_and_unlocked(tmp_path):
    assert dependencies.find_version_gaps(project_dir=tmp_path, selected=["ruff"]) == []
    write_lock(project=tmp_path, ty="0.0.1")
    assert dependencies.find_version_gaps(project_dir=tmp_path, selected=["ty"]) == []
    assert dependencies.find_version_gaps(project_dir=tmp_path, selected=["ruff"]) == []


def test_version_gap_reaches_the_report(tmp_path, capsys):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    write_lock(project=tmp_path, Pytest="8.4.0")
    sync_pyproject.main(argv=["--project", str(tmp_path)])
    assert (
        "VERSION    dependency-groups.dev has pytest 8.4.0" in capsys.readouterr().out
    )

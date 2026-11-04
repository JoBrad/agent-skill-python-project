import tomllib

import pytest

from python_project import sync_pyproject


FRESH = """\
[project]
name = "demo"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = []

[build-system]
requires = ["uv_build>=0.12.19,<0.13.0"]
build-backend = "uv_build"

[dependency-groups]
dev = [
    "ruff>=0.17.1",
    "pytest>=9.1.1",
    "pytest-cov>=7.1.0",
    "pre-commit>=4.7.0",
    "poethepoet>=0.49.0",
    "vulture>=2.16",
    "basedpyright>=1.40.2",
]
"""


@pytest.fixture
def project(tmp_path):
    (tmp_path / "pyproject.toml").write_text(FRESH, encoding="utf-8")
    return tmp_path


def run(*, project, extra=()):
    return sync_pyproject.main(argv=["--project", str(project), *extra])


def load(*, project):
    return tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))


def test_fresh_project_reports_missing_tables(project, capsys):
    assert run(project=project) == 1
    assert "MISSING    tool = (table)" in capsys.readouterr().out


def test_write_then_check_matches(project, capsys):
    assert run(project=project, extra=["--write"]) == 0
    assert run(project=project) == 0
    assert "matches the baseline" in capsys.readouterr().out
    data = load(project=project)
    assert data["tool"]["uv"]["required-version"] == ">=0.13.4"
    assert data["tool"]["basedpyright"]["typeCheckingMode"] == "standard"
    assert data["tool"]["ruff"]["lint"]["extend-select"] == ["ANN"]
    assert "any-type" in data["tool"]["ruff"]["lint"]["ignore"]


def test_write_keeps_fragment_comments(project):
    run(project=project, extra=["--write"])
    text = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert "# No target-version: ruff infers it from `requires-python`." in text


@pytest.mark.parametrize(
    ("mode", "extend_select", "allows_any"),
    [
        ("off", [], False),
        ("basic", ["missing-return-type-undocumented-public-function"], False),
        ("standard", ["ANN"], True),
        ("strict", ["ANN"], False),
    ],
)
def test_typing_mode_sets_ruff_and_basedpyright(
    project, mode, extend_select, allows_any
):
    run(project=project, extra=["--write", "--typing-mode", mode])
    data = load(project=project)
    pyright = data["tool"]["basedpyright"]
    if mode == "strict":
        assert pyright["typeCheckingMode"] == "standard"
        assert pyright["strict"] == ["src"]
    else:
        assert pyright["typeCheckingMode"] == mode
        assert "strict" not in pyright
    assert data["tool"]["ruff"]["lint"]["extend-select"] == extend_select
    assert ("any-type" in data["tool"]["ruff"]["lint"]["ignore"]) is allows_any


def test_mode_is_read_from_project(project, capsys):
    run(project=project, extra=["--write", "--typing-mode", "strict"])
    capsys.readouterr()
    assert run(project=project) == 0
    assert "typing mode: strict" in capsys.readouterr().out


def test_optional_checkers_follow_mode(project):
    run(
        project=project,
        extra=[
            "--write",
            "--typing-mode",
            "strict",
            "--with",
            "ty",
            "--with",
            "pyrefly",
        ],
    )
    tool = load(project=project)["tool"]
    assert tool["ty"]["rules"]["all"] == "error"
    assert tool["ty"]["terminal"]["error-on-warning"] is True
    assert tool["pyrefly"]["preset"] == "strict"


def test_existing_checker_is_detected_and_strict_rule_flagged(project, capsys):
    run(project=project, extra=["--write", "--typing-mode", "strict", "--with", "ty"])
    capsys.readouterr()
    assert run(project=project, extra=["--typing-mode", "basic"]) == 1
    out = capsys.readouterr().out
    assert "checkers: basedpyright, ty" in out
    assert "EXTRA      tool.ty.rules.all" in out
    assert "DIFFERS    tool.ty.terminal.error-on-warning is true, baseline false" in out
    run(project=project, extra=["--typing-mode", "basic", "--write"])
    assert "all" not in load(project=project)["tool"]["ty"].get("rules", {})


def test_differs_and_obsolete_are_reported_then_fixed(project, capsys):
    run(project=project, extra=["--write"])
    path = project / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "line-length = 88", 'line-length = 120\ntarget-version = "py314"'
    )
    path.write_text(text, encoding="utf-8")
    capsys.readouterr()

    assert run(project=project) == 1
    out = capsys.readouterr().out
    assert "DIFFERS    tool.ruff.line-length is 120, baseline 88" in out
    assert "OBSOLETE   tool.ruff.target-version" in out

    assert run(project=project, extra=["--write"]) == 0
    ruff = load(project=project)["tool"]["ruff"]
    assert ruff["line-length"] == 88
    assert "target-version" not in ruff


def test_project_owned_and_extra_keys_are_left_alone(project):
    run(project=project, extra=["--write"])
    path = project / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    text = text.replace('ignore_names = ["main"]', 'ignore_names = ["main", "cli"]')
    text = text.replace(
        "[tool.ruff.lint.per-file-ignores]\n",
        '[tool.ruff.lint.per-file-ignores]\n"scripts/**" = ["T20"]\n',
    )
    path.write_text(text, encoding="utf-8")
    assert run(project=project) == 0


def test_list_order_does_not_matter():
    assert sync_pyproject.same_value(left=["a", "b"], right=["b", "a"])
    assert not sync_pyproject.same_value(left=[1, 2], right=[2, 1])
    assert not sync_pyproject.same_value(left=["a"], right=["a", "b"])


def test_dependency_gaps_print_uv_command(project, capsys):
    path = project / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    text = text.replace('    "vulture>=2.16",\n', "").replace(
        "dependencies = []", 'dependencies = ["pytest-cov>=7"]'
    )
    path.write_text(text, encoding="utf-8")
    run(project=project, extra=["--write", "--with", "ty"])
    out = capsys.readouterr().out
    assert 'uv add --dev "vulture>=2.16" ty' in out
    assert (
        "MISPLACED  project.dependencies holds dev tools - uv remove pytest-cov" in out
    )


def test_non_uv_build_backend_is_reported(project, capsys):
    path = project / "pyproject.toml"
    text = path.read_text(encoding="utf-8").replace(
        'build-backend = "uv_build"', 'build-backend = "hatchling.build"'
    )
    path.write_text(text, encoding="utf-8")
    run(project=project, extra=["--write"])
    assert (
        'BUILD      build-system.build-backend is "hatchling.build", baseline "uv_build"'
        in (capsys.readouterr().out)
    )


def test_missing_pyproject_returns_2(tmp_path, capsys):
    assert run(project=tmp_path) == 2
    assert "uv init --package" in capsys.readouterr().out


def test_format_path_quotes_special_keys():
    path = ("tool", "ruff", "lint", "per-file-ignores", "tests/**")
    assert sync_pyproject.format_path(path=path) == (
        'tool.ruff.lint.per-file-ignores."tests/**"'
    )


def test_main_rejects_positional_argv():
    with pytest.raises(TypeError):
        # The positional call is the point: main() takes argv by keyword only.
        sync_pyproject.main([])  # pyright: ignore[reportCallIssue]


def test_plain_strict_mode_moves_to_src_only(project, capsys):
    run(project=project, extra=["--write"])
    path = project / "pyproject.toml"
    text = path.read_text(encoding="utf-8").replace(
        'typeCheckingMode = "standard"', 'typeCheckingMode = "strict"'
    )
    path.write_text(text, encoding="utf-8")
    capsys.readouterr()

    assert run(project=project) == 1
    out = capsys.readouterr().out
    assert "typing mode: strict" in out
    assert (
        'DIFFERS    tool.basedpyright.typeCheckingMode is "strict", baseline "standard"'
        in out
    )
    assert 'MISSING    tool.basedpyright.strict = ["src"]' in out

    run(project=project, extra=["--write"])
    assert run(project=project) == 0


def test_strict_paths_flagged_outside_strict_mode(project, capsys):
    run(project=project, extra=["--write", "--typing-mode", "strict"])
    capsys.readouterr()
    assert run(project=project, extra=["--typing-mode", "standard"]) == 1
    assert "EXTRA      tool.basedpyright.strict" in capsys.readouterr().out
    run(project=project, extra=["--typing-mode", "standard", "--write"])
    assert "strict" not in load(project=project)["tool"]["basedpyright"]


def edit(*, project, old, new):
    path = project / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def lint(*, project):
    return load(project=project)["tool"]["ruff"]["lint"]


# Rule lists: a baseline entry the project lacks is MISSING and gets added.
def test_select_missing_baseline_entry_is_added(project, capsys):
    run(project=project, extra=["--write"])
    edit(project=project, old='  "PTH",     # flake8-use-pathlib\n', new="")
    capsys.readouterr()
    assert run(project=project) == 1
    assert 'MISSING    tool.ruff.lint.select lacks ["PTH"]' in capsys.readouterr().out
    assert run(project=project, extra=["--write"]) == 0
    assert "PTH" in lint(project=project)["select"]


def test_ignore_missing_baseline_entry_is_added(project, capsys):
    run(project=project, extra=["--write"])
    edit(
        project=project,
        old='  "ARG",\n  "too-many-arguments",',
        new='  "too-many-arguments",',
    )
    capsys.readouterr()
    assert run(project=project) == 1
    out = capsys.readouterr().out
    assert 'MISSING    tool.ruff.lint.per-file-ignores."tests/**" lacks ["ARG"]' in out
    assert run(project=project, extra=["--write"]) == 0
    assert "ARG" in lint(project=project)["per-file-ignores"]["tests/**"]


# Rule lists: a project's own select entries are kept and not reported.
def test_select_project_entries_are_kept_silently(project, capsys):
    run(project=project, extra=["--write"])
    edit(
        project=project,
        old='extend-select = ["ANN"]',
        new='extend-select = ["ANN", "S"]',
    )
    edit(
        project=project,
        old='  "A",       # flake8-builtins\n',
        new='  "A",\n  "T20",\n',
    )
    capsys.readouterr()
    assert run(project=project, extra=["--write"]) == 0
    assert "applied 0 change(s)" in capsys.readouterr().out
    assert lint(project=project)["extend-select"] == ["ANN", "S"]
    assert "T20" in lint(project=project)["select"]


# Rule lists: a project's own ignores are reported for review, kept, and pass.
def test_ignore_project_entries_are_reported_and_kept(project, capsys):
    run(project=project, extra=["--write"])
    edit(project=project, old='  "ARG",\n', new='  "ARG",\n  "S101",\n')
    edit(
        project=project, old="ignore = [\n", new='ignore = [\n  "too-many-branches",\n'
    )
    capsys.readouterr()
    assert run(project=project, extra=["--write"]) == 0
    out = capsys.readouterr().out
    assert 'RELAXED    tool.ruff.lint.ignore turns off ["too-many-branches"]' in out
    assert (
        'RELAXED    tool.ruff.lint.per-file-ignores."tests/**" turns off ["S101"]'
        in out
    )
    assert "too-many-branches" in lint(project=project)["ignore"]
    assert "S101" in lint(project=project)["per-file-ignores"]["tests/**"]


# Rule lists: an entry the typing mode forbids is EXTRA and gets removed.
def test_select_entry_forbidden_by_mode_is_removed(project, capsys):
    run(project=project, extra=["--write"])
    edit(
        project=project,
        old='extend-select = ["ANN"]',
        new='extend-select = ["ANN", "S"]',
    )
    capsys.readouterr()
    assert run(project=project, extra=["--typing-mode", "off"]) == 1
    out = capsys.readouterr().out
    assert (
        'EXTRA      tool.ruff.lint.extend-select has ["ANN"] - typing mode off' in out
    )
    assert run(project=project, extra=["--typing-mode", "off", "--write"]) == 0
    assert lint(project=project)["extend-select"] == ["S"]


def test_ignore_entry_forbidden_by_mode_is_removed(project, capsys):
    run(project=project, extra=["--write"])
    edit(project=project, old="ignore = [\n", new='ignore = [\n  "S101",\n')
    capsys.readouterr()
    assert run(project=project, extra=["--typing-mode", "strict"]) == 1
    out = capsys.readouterr().out
    assert (
        'EXTRA      tool.ruff.lint.ignore has ["any-type"] - typing mode strict' in out
    )
    assert run(project=project, extra=["--typing-mode", "strict", "--write"]) == 0
    ignore = lint(project=project)["ignore"]
    assert "any-type" not in ignore
    assert "S101" in ignore


def test_rule_list_of_wrong_type_differs(project, capsys):
    run(project=project, extra=["--write"])
    edit(project=project, old='extend-select = ["ANN"]', new='extend-select = "ANN"')
    capsys.readouterr()
    assert run(project=project) == 1
    assert "DIFFERS    tool.ruff.lint.extend-select" in capsys.readouterr().out


def test_uv_is_not_a_dev_dependency(project, capsys):
    path = project / "pyproject.toml"
    path.write_text(
        path.read_text(encoding="utf-8").replace('    "ruff>=0.17.1",\n', "")
    )
    run(project=project)
    out = capsys.readouterr().out
    assert 'uv add --dev "ruff>=0.17.1"\n' in out


@pytest.mark.parametrize(
    ("table", "message"),
    [
        ("tool.pyright", "move its settings to [tool.basedpyright]"),
        ("tool.pytest.ini_options", "move its settings into [tool.pytest]"),
        ("tool.black", "ruff formats"),
    ],
)
def test_conflicting_settings_are_reported_not_changed(project, capsys, table, message):
    run(project=project, extra=["--write"])
    path = project / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    path.write_text(f"{text}\n[{table}]\nkeep = true\n", encoding="utf-8")
    capsys.readouterr()
    assert run(project=project, extra=["--write"]) == 1
    assert f"CONFLICT   {table} - {message}" in capsys.readouterr().out
    assert f"[{table}]\nkeep = true" in path.read_text(encoding="utf-8")


def test_write_adds_every_task_as_one_readable_line(project):
    run(project=project, extra=["--write"])
    text = (project / "pyproject.toml").read_text(encoding="utf-8")
    assert 'lint = {help = "Lint with ruff", cmd = "ruff check"}' in text
    tasks = load(project=project)["tool"]["poe"]["tasks"]
    assert tasks["check"]["sequence"] == [
        "lint",
        "format-check",
        "file-length",
        "typecheck",
        "coverage",
        "deadcode",
    ]

import json
import subprocess

import changed_lines_coverage
import pytest


DIFF = """\
diff --git a/src/pkg/a.py b/src/pkg/a.py
--- a/src/pkg/a.py
+++ b/src/pkg/a.py
@@ -3,0 +4,2 @@ def f():
+    y = 2
+    return y
@@ -10 +12 @@ def g():
-    old
+    new
diff --git a/src/pkg/gone.py b/src/pkg/gone.py
--- a/src/pkg/gone.py
+++ /dev/null
@@ -1,2 +0,0 @@
-a
-b
"""


def test_parse_added_lines():
    added = changed_lines_coverage.parse_added_lines(diff=DIFF)
    assert added == {"src/pkg/a.py": {4, 5, 12}}


def test_measure_counts_lines_and_branches():
    report = {
        "files": {
            "src/pkg/a.py": {
                "executed_lines": [1, 4, 12],
                "missing_lines": [5],
                "executed_branches": [[4, 5]],
                "missing_branches": [[12, 14], [20, 21]],
            },
            "src/pkg/untouched.py": {"executed_lines": [1], "missing_lines": [2]},
        }
    }
    results = changed_lines_coverage.measure(
        report=report, changes={"src/pkg/a.py": {4, 5, 12}}
    )
    assert len(results) == 1
    result = results[0]
    assert (result.covered, result.total) == (3, 5)
    assert result.missing_lines == [5]


def test_measure_skips_files_without_measurable_lines():
    report = {"files": {"src/pkg/a.py": {"executed_lines": [], "missing_lines": []}}}
    assert (
        changed_lines_coverage.measure(report=report, changes={"src/pkg/a.py": {1}})
        == []
    )


def git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    git("init", "-q", "-b", "main", cwd=tmp_path)
    git("config", "user.email", "test@example.com", cwd=tmp_path)
    git("config", "user.name", "Test", cwd=tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    git("add", ".", cwd=tmp_path)
    git("commit", "-q", "-m", "base", cwd=tmp_path)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def write_report(*, repo, files):
    (repo / "coverage.json").write_text(json.dumps({"files": files}), encoding="utf-8")


def test_main_passes_when_changes_are_covered(repo, capsys):
    (repo / "src" / "a.py").write_text("x = 1\ny = 2\n", encoding="utf-8")
    (repo / "src" / "b.py").write_text("z = 3\n", encoding="utf-8")
    write_report(
        repo=repo,
        files={
            "src/a.py": {"executed_lines": [1, 2], "missing_lines": []},
            "src/b.py": {"executed_lines": [1], "missing_lines": []},
        },
    )
    assert changed_lines_coverage.main(argv=[]) == 0
    out = capsys.readouterr().out
    assert "src/b.py: 100.0%" in out
    assert "Changed-line coverage: 100.0% (threshold 90%)" in out


def test_main_fails_under_threshold(repo, capsys):
    (repo / "src" / "a.py").write_text("x = 1\ny = 2\nz = 3\n", encoding="utf-8")
    write_report(
        repo=repo, files={"src/a.py": {"executed_lines": [1, 2], "missing_lines": [3]}}
    )
    assert changed_lines_coverage.main(argv=["--base", "HEAD"]) == 1
    assert "missing lines: 3" in capsys.readouterr().out


def test_main_with_no_changes(repo, capsys):
    write_report(repo=repo, files={"src/a.py": {"executed_lines": [1]}})
    assert changed_lines_coverage.main(argv=[]) == 0
    assert "No measurable changed lines." in capsys.readouterr().out


def test_main_without_report(repo, capsys):
    assert changed_lines_coverage.main(argv=[]) == 2
    assert "coverage.json not found" in capsys.readouterr().out


def test_default_base_falls_back_to_head(repo):
    assert changed_lines_coverage.default_base() == "HEAD"


def test_main_rejects_positional_argv():
    with pytest.raises(TypeError):
        # The positional call is the point: main() takes argv by keyword only.
        changed_lines_coverage.main([])  # pyright: ignore[reportCallIssue]

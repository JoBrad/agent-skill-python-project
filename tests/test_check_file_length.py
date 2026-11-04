import check_file_length
import pytest


def write_lines(*, path, count):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x = 1\n" * count, encoding="utf-8")


def test_reports_only_files_over_limit(tmp_path, capsys):
    write_lines(path=tmp_path / "pkg" / "long.py", count=6)
    write_lines(path=tmp_path / "pkg" / "short.py", count=5)
    (tmp_path / "pkg" / "notes.txt").write_text("x\n" * 50, encoding="utf-8")

    code = check_file_length.main(argv=[str(tmp_path), "--max-lines", "5"])

    assert code == 1
    out = capsys.readouterr().out
    assert "long.py: 6 lines (limit 5)" in out
    assert "short.py" not in out


def test_accepts_a_single_file(tmp_path):
    file = tmp_path / "one.py"
    write_lines(path=file, count=3)
    found = check_file_length.find_long_files(paths=[file], max_lines=2)
    assert found == [(file, 3)]


def test_clean_tree_returns_zero(tmp_path, capsys):
    write_lines(path=tmp_path / "a.py", count=1)
    assert check_file_length.main(argv=[str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


def test_main_rejects_positional_argv():
    with pytest.raises(TypeError):
        # The positional call is the point: main() takes argv by keyword only.
        check_file_length.main([])  # pyright: ignore[reportCallIssue]

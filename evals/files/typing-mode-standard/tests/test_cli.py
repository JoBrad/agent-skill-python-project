import json

from pathlib import Path

import pytest

from orders import cli


def test_main_prints_each_total(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "orders.json"
    path.write_text(json.dumps([{"id": "A1", "lines": [{"price": 5, "quantity": 3}]}]))
    monkeypatch.setattr("sys.argv", ["orders", str(path)])
    cli.main()
    assert capsys.readouterr().out == "A1 15\n"

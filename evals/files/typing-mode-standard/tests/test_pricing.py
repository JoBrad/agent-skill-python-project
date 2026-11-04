import json

from pathlib import Path

import pytest

from orders.pricing import line_count, load_orders, order_total, parse_cents


ORDER = {
    "id": "A1",
    "lines": [{"price": 250, "quantity": 2}, {"price": 100, "quantity": 1}],
}


def test_order_total_sums_lines() -> None:
    assert order_total(order=ORDER) == 600


def test_load_orders_reads_json(tmp_path: Path) -> None:
    path = tmp_path / "orders.json"
    path.write_text(json.dumps([ORDER]), encoding="utf-8")
    assert load_orders(path=path) == [ORDER]


def test_parse_cents_accepts_strings() -> None:
    assert parse_cents(value="250") == 250


def test_line_count() -> None:
    assert line_count(lines=ORDER["lines"]) == 2


@pytest.mark.parametrize(
    ("func", "args"),
    [
        (order_total, (ORDER,)),
        (load_orders, (Path(),)),
        (parse_cents, (1,)),
        (line_count, ([],)),
    ],
)
def test_positional_call_raises(func, args) -> None:
    with pytest.raises(TypeError):
        func(*args)

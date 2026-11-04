"""Order totals. Prices are integer cents, so totals never round."""

import json

from pathlib import Path
from typing import Any


def load_orders(*, path: Path) -> list[dict[str, Any]]:
    """Return the orders stored as a JSON list at `path`."""
    return json.loads(path.read_text(encoding="utf-8"))


def order_total(*, order: dict[str, Any]) -> int:
    """Return the total of an order's lines in cents."""
    return sum(
        parse_cents(value=line["price"]) * line["quantity"] for line in order["lines"]
    )


def parse_cents(*, value: Any) -> int:
    """Return `value` as integer cents, accepting numbers or numeric strings."""
    return int(value)


def line_count(*, lines: list) -> int:
    """Return how many lines an order has."""
    return len(lines)

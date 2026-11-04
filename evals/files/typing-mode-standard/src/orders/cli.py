"""Command-line entry point for orders."""

import sys

from pathlib import Path

from orders.pricing import line_count, load_orders, order_total


def main() -> None:
    """Print the total of each non-empty order in the file named on the command line."""
    for order in load_orders(path=Path(sys.argv[1])):
        if line_count(lines=order["lines"]):
            print(order["id"], order_total(order=order))

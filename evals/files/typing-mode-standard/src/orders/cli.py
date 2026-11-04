"""Command-line entry point for orders."""

import sys

from pathlib import Path

from orders.pricing import load_orders, order_total


def main() -> None:
    """Print the total of each order in the file named on the command line."""
    for order in load_orders(path=Path(sys.argv[1])):
        print(order["id"], order_total(order=order))

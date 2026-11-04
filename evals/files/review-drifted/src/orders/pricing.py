"""Order totals."""

import json
import os.path


def load_orders(path):
    """Return the orders stored as a JSON list at `path`."""
    if not os.path.exists(path):
        return []
    with open(path) as handle:
        return json.load(handle)


def order_total(order, discount=0):
    """Return the total of an order's lines in cents."""
    total = sum(line["price"] * line["quantity"] for line in order["lines"])
    return total - discount


def report(path):
    """Print the total of every order in `path`."""
    for order in load_orders(path):
        print(order["id"], order_total(order, 0))

"""Order totals in integer cents."""

from .models import Order


def order_total(order: Order) -> int:
    return sum(line.price * line.quantity for line in order.lines)


def parse_price(text):
    """Convert a dollar amount such as "2.50" to integer cents."""
    return int(float(text)) * 100

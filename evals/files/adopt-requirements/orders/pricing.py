"""Order totals in integer cents."""

from .models import Order


def order_total(order: Order) -> int:
    return sum(line.price * line.quantity for line in order.lines)

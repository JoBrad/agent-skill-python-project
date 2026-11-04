from orders.models import Order
from orders.pricing import order_total, parse_price


def test_order_total():
    order = Order(id="A1", lines=[{"price": 250, "quantity": 2}])
    assert order_total(order) == 500


def test_parse_price_keeps_cents():
    assert parse_price("2.50") == 250

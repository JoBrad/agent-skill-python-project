from orders.models import Order
from orders.pricing import order_total


def test_order_total():
    order = Order(id="A1", lines=[{"price": 250, "quantity": 2}])
    assert order_total(order) == 600

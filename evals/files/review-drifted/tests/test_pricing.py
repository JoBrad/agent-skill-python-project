from orders.pricing import order_total


def test_order_total() -> None:
    assert order_total({"lines": [{"price": 250, "quantity": 2}]}, 50) == 450

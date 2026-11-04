"""Print the total of each order in a JSON file."""

import json
import sys

from .models import Order
from .pricing import order_total


def main():
    with open(sys.argv[1]) as handle:
        for raw in json.load(handle):
            order = Order(**raw)
            print(order.id, order_total(order))


if __name__ == "__main__":
    main()

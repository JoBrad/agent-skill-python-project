"""Order records parsed from JSON input."""

from pydantic import BaseModel


class Line(BaseModel):
    price: int
    quantity: int


class Order(BaseModel):
    id: str
    lines: list[Line]

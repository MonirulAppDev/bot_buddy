from typing import Any
from pydantic import BaseModel, Field


class SMMActionRequest(BaseModel):
    key: str | None = None
    action: str = Field(..., description="Action name: services, add, status, balance")
    service: int | None = None
    link: str | None = None
    quantity: int | None = None
    runs: int | None = None
    interval: int | None = None
    comments: str | None = None
    order: str | None = None
    orders: str | None = None  # Comma-separated order IDs for multi-status


class SMMServiceItem(BaseModel):
    service: int
    name: str
    type: str
    category: str
    rate: str
    min: str
    max: str
    dripfeed: bool
    refill: bool
    cancel: bool


class SMMAddOrderResponse(BaseModel):
    order: str


class SMMOrderStatusResponse(BaseModel):
    charge: str = "0.00"
    start_count: str = "0"
    status: str
    remains: str
    currency: str = "USD"


class SMMBalanceResponse(BaseModel):
    balance: str
    currency: str

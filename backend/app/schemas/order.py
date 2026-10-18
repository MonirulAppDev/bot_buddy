from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.service import ServiceResponse


class OrderBase(BaseModel):
    service_id: int = Field(..., example=1)
    target_url: str = Field(..., example="https://www.facebook.com/example/posts/123456789")
    quantity: int = Field(..., ge=1, example=100)
    comments: str | None = Field(default=None, example="{Awesome|Nice|Great} work!\nLove this content!")
    drip_feed: bool = Field(default=False, example=True)
    interval_seconds: int = Field(default=5, ge=1, le=3600, example=10)
    runs: int = Field(default=1, ge=1, example=5)


class OrderCreate(OrderBase):
    pass


class OrderResponse(OrderBase):
    id: str
    delivered_count: int
    remains_count: int
    status: str
    created_at: datetime
    updated_at: datetime
    service: ServiceResponse | None = None

    model_config = ConfigDict(from_attributes=True)

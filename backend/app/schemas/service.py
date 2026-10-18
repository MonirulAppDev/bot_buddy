from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ServiceBase(BaseModel):
    name: str = Field(..., example="Facebook Post Love Reactions [Drip-Feed]")
    platform: str = Field(default="facebook", example="facebook")
    service_type: str = Field(..., example="reaction")
    rate_per_1000: float = Field(default=1.5, example=1.5)
    min_quantity: int = Field(default=10, example=10)
    max_quantity: int = Field(default=50000, example=50000)
    is_active: bool = True
    description: str = ""
    default_interval_seconds: int = 5


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: str | None = None
    rate_per_1000: float | None = None
    min_quantity: int | None = None
    max_quantity: int | None = None
    is_active: bool | None = None
    description: str | None = None
    default_interval_seconds: int | None = None


class ServiceResponse(ServiceBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

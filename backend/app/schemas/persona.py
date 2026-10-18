from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PersonaBase(BaseModel):
    username: str = Field(..., example="john_doe_99")
    display_name: str = Field(..., example="John Doe")
    avatar_url: str = Field(default="", example="https://images.unsplash.com/photo-example")
    platform: str = Field(default="facebook", example="facebook")
    locale: str = Field(default="en_US", example="en_US")
    status: str = Field(default="active", example="active")
    extra_metadata: str = "{}"


class PersonaCreate(PersonaBase):
    pass


class PersonaGenerateRequest(BaseModel):
    count: int = Field(default=10, ge=1, le=500, description="Number of dummy personas to generate")
    locale: str = Field(default="en_US", description="Locale for realistic names (e.g. en_US, bn_BD, en_GB)")
    platform: str = Field(default="facebook", description="Target platform")


class PersonaResponse(PersonaBase):
    id: str
    total_actions: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import List, Optional

class EntityRequest(BaseModel):
    name: Optional[str] = None
    appearance: Optional[str] = None
    detailed_appearance: Optional[str] = None
    description: Optional[str] = None
    dreambooth_url: Optional[str] = None

class ComicRequest(BaseModel):
    prompt: str
    entities: List[EntityRequest]

class ImageRequest(BaseModel):
    provider: str = Field(..., description="e.g. 'openai' or 'azure'")
    image_prompt: str
    entities: List[EntityRequest] = Field(default_factory=list)
    image_model: str = Field("gpt-image-1")
    size: str = Field("1024x1024")
    quality: str = Field("high")

    @field_validator("size")
    def _chk_size(cls, v):
        if v not in {"1024x1024", "1024x1536", "1536x1024"}:
            raise ValueError("size must be one of 1024x1024, 1024x1536, 1536x1024")
        return v

    @field_validator("quality")
    def _chk_quality(cls, v):
        if v not in {"low", "medium", "high", "standard", "hd"}:
            raise ValueError("quality invalid")
        return v

class Base64ImageRequest(BaseModel):
    provider: str = "openai"
    vision_model: str = "gpt-4o"
    image_base64: str

class ImageUrlRequest(BaseModel):
    provider: str = "openai"
    vision_model: str = "gpt-4o"
    image_url: HttpUrl

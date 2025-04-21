from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Optional
from app.utils.enums import StyleOptions


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
    provider: str = Field(..., description="The provider to use (e.g., 'openai' or 'azure').")
    image_prompt: str
    entities: List[EntityRequest]
    style: StyleOptions = StyleOptions.COMIC
    image_model: str = "dall-e-3"
    model_resolution: str = "1024x1024"



class Base64ImageRequest(BaseModel):
    provider: str = "openai"
    vision_model: str = "gpt-4o"
    image_base64: str  # Base64-encoded image string
    
class ImageUrlRequest(BaseModel):
    provider: str = "openai"
    vision_model: str = "gpt-4o"
    image_url: HttpUrl  # Ensures valid URL format
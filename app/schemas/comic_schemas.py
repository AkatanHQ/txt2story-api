from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from app.utils.enums import StyleOptions

class EntityRequest(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    appearance: Optional[str] = None
    detailed_appearance: Optional[str] = None
    description: Optional[str] = None
    dreambooth_url: Optional[str] = None
    dreambooth: bool = False

class ImageRequest(BaseModel):
    provider: str = Field(..., description="The provider to use (e.g., 'openai' or 'azure').")
    image_prompt: str
    entities: List[EntityRequest]
    style: StyleOptions = StyleOptions.COMIC
    image_model: str = "dall-e-3"
    model_resolution: str = "1024x1024"

class ComicRequest(BaseModel):
    user_id: int
    scenario: str
    language: str
    number_of_pages: int
    entities: List[EntityRequest]
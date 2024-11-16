from pydantic import BaseModel
from typing import List, Dict, Optional

class Entity(BaseModel):
    id: int
    name: Optional[str] = None 
    appearance: Optional[str] = None 
    detailed_appearance: Optional[str] = None  
    description: Optional[str] = None 
    picture: Optional[str] = None
    dreambooth: bool = False

class ComicRequest(BaseModel):
    user_id: int
    scenario: str
    language: str
    number_of_pages: int
    entities: List[Entity]

class ImageRequest(BaseModel):
    image_prompt: str
    style: str 
    entities: List[Dict]


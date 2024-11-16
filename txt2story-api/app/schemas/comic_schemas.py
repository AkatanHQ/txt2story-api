from pydantic import BaseModel
from typing import List, Dict

class Entity(BaseModel):
    name: str
    appearance: str
    detailed_appearance: str

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


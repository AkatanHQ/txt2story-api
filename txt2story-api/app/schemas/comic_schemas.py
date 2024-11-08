from pydantic import BaseModel
from typing import List, Dict

class ComicRequest(BaseModel):
    user_id: int
    scenario: str
    language: str
    number_of_pages: int
    img_model: str
    entities: List[Dict[str, str]]

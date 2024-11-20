from pydantic import BaseModel
from typing import List, Dict, Optional
from app.utils.enums import StyleOptions

class EntityRequest(BaseModel):
    id: int
    name: Optional[str] = None 
    appearance: Optional[str] = None 
    detailed_appearance: Optional[str] = None  
    description: Optional[str] = None 
    picture: Optional[str] = None
    dreambooth: bool = False


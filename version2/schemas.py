from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Tuple
from enum import Enum

# ────────────────────────────
# ░░ Data models ░░
# ────────────────────────────
class Mode(str, Enum):
    CONTINUE_CHAT = "continue_chat"

    GENERATE_IMAGE ="generate_image"

    EDIT_TEXT = "edit_text"
    EDIT_ALL = "edit_all"
    INSERT_PAGE = "insert_page"
    DELETE_PAGE = "delete_page"
    MOVE_PAGE = "move_page"
    EDIT_STORY_PROMPT = "edit_story_prompt"

    EDIT_IMAGE_PROMPT = "edit_image_prompt"

    # entity CRUD
    ADD_ENTITY = "add_entity"
    UPDATE_ENTITY = "update_entity"
    DELETE_ENTITY = "delete_entity"


class StoryImage(BaseModel):
    index: int
    prompt: Optional[str] = None        # prompt actually used for this image
    size:   Optional[str] = None        # 512×512 … 1024×1792
    quality: Optional[str] = None       # low / medium / high
    b64_json: Optional[str] = None      # base64 of the generated PNG


class StoryEntity(BaseModel):
    name: str = Field(default="")  # identifier (unique)
    b64_json: Optional[str] = None  # input image from the user
    prompt: Optional[str] = None    # input description/prompt from the user


class StoryText(BaseModel):
    index: int
    text: str = Field(default="")


class Story(BaseModel):
    prompt: str = Field(default="")
    pages: List[StoryText] = Field(default_factory=list)
    images: List[StoryImage] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Frontend payload.

    • `user_input` – the natural-language message.
    • `story` – optional partial/complete story state coming from the UI.
    • `entities` – optional list of entities coming from the UI.
    """
    user_input: str
    story: Optional[Story] = None
    entities: Optional[List[StoryEntity]] = None
    history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    modes: List[Mode]
    assistant_output: Optional[str] = None
    story: Optional[Story] = None
    entities: Optional[List[StoryEntity]] = None
    image_b64: Optional[str] = None
    history: Optional[List[dict]] = None


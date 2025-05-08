from __future__ import annotations

"""
StoryGPT Backend – FastAPI + OpenAI 2.2.0
-----------------------------------------

A FastAPI backend for an interactive, pageable storytelling chat.
It now supports editing/injecting **story prompts, story text, and entities** via
both the REST request body *and* new OpenAI tool calls.

Changes in v2.2.0 (2025-05-08)
• 🆕 Added **entities_state** in-memory store and CRUD helpers.
• 🆕 Added `add_entity`, `update_entity`, `delete_entity` tool calls.
• 🆕 `ChatRequest` may include a partial story and/or entity list to prime state.
• 🆕 `ChatResponse` now returns the current entities list.
• 🔄 Extended `Mode` enum with new actions.
• 🔄 Extended system prompt + TOOLS to advertise new helpers.
• 🔄 Updated endpoint logic to merge incoming story/entities before routing to
  the OpenAI function-calling flow.
• 🔄 Minor refactors & version bump.

Run:
    pip install fastapi uvicorn pydantic python-dotenv openai
    export OPENAI_API_KEY="sk-..."
    uvicorn main:app --reload
"""

import json
import logging
import os
import re
from enum import Enum
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field

# ────────────────────────────
# ░░ Environment & logging ░░
# ────────────────────────────
load_dotenv()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=LOG_LEVEL,
)
logger = logging.getLogger("storygpt")
logger.info("Logging initialised at %s level", LOG_LEVEL)

client = OpenAI()  # reads OPENAI_API_KEY

# ────────────────────────────
# ░░ FastAPI app ░░
# ────────────────────────────
app = FastAPI(title="StoryGPT Backend", version="2.2.0")

# ────────────────────────────
# ░░ Data models ░░
# ────────────────────────────
class Mode(str, Enum):
    CONTINUE_CHAT = "continue_chat"

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
    quality: Optional[str] = None


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


class ChatRequest(BaseModel):
    """Frontend payload.

    • `user_input` – the natural-language message.
    • `story` – optional partial/complete story state coming from the UI.
    • `entities` – optional list of entities coming from the UI.
    """

    user_input: str
    story: Optional[Story] = None
    entities: Optional[List[StoryEntity]] = None


class ChatResponse(BaseModel):
    mode: Mode
    assistant_output: Optional[str] = None
    story: Optional[Story] = None
    entities: Optional[List[StoryEntity]] = None
    image_urls: Optional[List[str]] = None


# ────────────────────────────
# ░░ In-memory state ░░
# ────────────────────────────
story_state = Story(
    prompt="An epic tale begins.",
    pages=[StoryText(index=0, text="Once upon a time …")],
)

entities_state: List[StoryEntity] = []

MAX_HISTORY = 20
MESSAGE_HISTORY: List[dict] = []  # excludes system prompt

# ────────────────────────────
# ░░ OpenAI tool definitions ░░
# ────────────────────────────
TOOLS: List[Dict] = [
    {
        "type": "function",
        "function": {
            "name": "edit_text",
            "description": "Edit the text of a single page by index.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "Zero-based page index."},
                    "new_text": {"type": "string", "description": "Replacement text."},
                },
                "required": ["page", "new_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_all",
            "description": "Replace every page with new text entries in order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_texts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of new page texts.",
                    }
                },
                "required": ["new_texts"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "insert_page",
            "description": "Insert a new page at the given index.",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "Insert position."},
                    "text": {"type": "string", "description": "Text for the new page."},
                },
                "required": ["index", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_page",
            "description": "Delete a page at the given index.",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "Index of the page."}
                },
                "required": ["index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_page",
            "description": "Move a page from one position to another.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_index": {"type": "integer", "description": "Current index."},
                    "to_index": {"type": "integer", "description": "Destination index."},
                },
                "required": ["from_index", "to_index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_story_prompt",
            "description": "Update the story prompt.",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_prompt": {"type": "string", "description": "New prompt."}
                },
                "required": ["new_prompt"],
            },
        },
    },
    # Entity CRUD tool calls
    {
        "type": "function",
        "function": {
            "name": "add_entity",
            "description": "Add a new entity usable by future story/image generations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Unique identifier."},
                    "b64_json": {"type": "string", "description": "Optional base64 image."},
                    "prompt": {"type": "string", "description": "Optional text description."},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_entity",
            "description": "Update an existing entity's prompt and/or image (identified by `name`).",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Identifier to update."},
                    "b64_json": {"type": "string", "description": "Optional base64 image."},
                    "prompt": {"type": "string", "description": "Optional text description."},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_entity",
            "description": "Remove an entity by its `name`.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Identifier to remove."}
                },
                "required": ["name"],
            },
        },
    }
]

# ────────────────────────────
# ░░ Helpers ░░
# ────────────────────────────

def _clean_json_fence(raw: str) -> str:
    cleaned = re.sub(r"```\w*", "", raw).strip()
    match = re.search(r"\[.*]", cleaned, re.S)
    return match.group(0).strip() if match else cleaned


def _parse_json_or_lines(text: str, expected: int) -> List[str]:
    cleaned = _clean_json_fence(text)
    try:
        data = json.loads(cleaned)
        pages = [str(x).strip() for x in data if str(x).strip()] if isinstance(data, list) else []
    except json.JSONDecodeError:
        pages = [
            re.sub(r"^\s*\d+[).\-]?\s*", "", ln).strip()
            for ln in cleaned.splitlines()
            if ln.strip() and ln.strip() not in {"[", "]"}
        ]
    if len(pages) < expected:
        pages += ["…"] * (expected - len(pages))
    return pages[:expected]


def _generate_initial_pages(prompt: str, num_pages: int = 5) -> List[str]:
    logger.info("Generating %d pages for prompt", num_pages)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a creative storyteller. Return *only* a JSON array with exactly {n} "
                "elements, each 1-2 sentences long, continuing the user's prompt. Do NOT wrap "
                "in markdown.".format(n=num_pages)
            ),
        },
        {"role": "user", "content": prompt},
    ]
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=400,
        temperature=0.7,
    )
    raw = resp.choices[0].message.content.strip()
    return _parse_json_or_lines(raw, expected=num_pages)


def _normalize_indexes() -> None:
    for i, pg in enumerate(story_state.pages):
        pg.index = i


# ────────────────────────────
# ░░ Entity helpers ░░
# ────────────────────────────

def _find_entity(name: str) -> Optional[StoryEntity]:
    return next((e for e in entities_state if e.name == name), None)

# ────────────────────────────
# ░░ OpenAI chat orchestration ░░
# ────────────────────────────

def _openai_call(user_msg: str) -> Tuple[List[Tuple[str, dict, str]], Optional[str]]:
    global MESSAGE_HISTORY
    MESSAGE_HISTORY.append({"role": "user", "content": user_msg})
    MESSAGE_HISTORY = MESSAGE_HISTORY[-MAX_HISTORY:]

    SYSTEM_PROMPT = (
        f"You are StoryGPT. Decide if the user is chatting or wants to use a tool.\n\n"
        f"Current story summary:\n"
        f"• Pages: {len(story_state.pages)}\n"
        f"• Entities: {len(entities_state)}\n"
        f"• Prompt: {story_state.prompt[:120]}{'...' if len(story_state.prompt) > 120 else ''}\n\n"
        "Tools:\n"
        "• edit_text – replace text of one page\n"
        "• edit_all – replace every page\n"
        "• insert_page – add a page\n"
        "• delete_page – remove a page\n"
        "• move_page – reorder pages\n"
        "• edit_story_prompt – new synopsis\n"
        "• add_entity – create a reusable entity (name, image, description)\n"
        "• update_entity – update an existing entity\n"
        "• delete_entity – remove an entity\n"
        "When you simply want to answer the user, reply with normal assistant text **without** invoking any tool. "
        "If you need to modify the story or entities, respond ONLY with the relevant function call JSON. "
        "If no tools really fit, but it is related to story editing, respond with edit_story_prompt."
    )


    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + MESSAGE_HISTORY
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    msg = resp.choices[0].message

    # multiple tool calls
    if msg.tool_calls:
        MESSAGE_HISTORY.append({
            "role": "assistant",
            "content": None,
            "tool_calls": msg.tool_calls,
        })

        actions = []
        for call in msg.tool_calls:
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            actions.append((call.function.name, args, call.id))
        return actions, None

    # fallback: normal assistant response
    assistant_text = (msg.content or "").strip()
    MESSAGE_HISTORY.append({"role": "assistant", "content": assistant_text})
    return [], assistant_text



# ────────────────────────────
# ░░ Apply actions ░░
# ────────────────────────────

def _apply_action(action: str, data: dict) -> Dict:
    extra: Dict = {}

    # Page / story tools (existing)
    if action == "edit_text":
        idx = data["page"]
        if not 0 <= idx < len(story_state.pages):
            raise HTTPException(400, "Page index out of range.")
        story_state.pages[idx].text = data["new_text"]

    elif action == "edit_all":
        new_texts = data["new_texts"]
        story_state.pages = [StoryText(index=i, text=t) for i, t in enumerate(new_texts)]

    elif action == "insert_page":
        idx = data["index"]
        text = data["text"]
        if not 0 <= idx <= len(story_state.pages):
            raise HTTPException(400, "Insert index out of range.")
        story_state.pages.insert(idx, StoryText(index=idx, text=text))
        _normalize_indexes()

    elif action == "delete_page":
        idx = data["index"]
        if not 0 <= idx < len(story_state.pages):
            raise HTTPException(400, "Delete index out of range.")
        story_state.pages.pop(idx)
        _normalize_indexes()

    elif action == "move_page":
        frm, to = data["from_index"], data["to_index"]
        if not (0 <= frm < len(story_state.pages)) or not (0 <= to < len(story_state.pages)):
            raise HTTPException(400, "Move indexes out of range.")
        page = story_state.pages.pop(frm)
        story_state.pages.insert(to, page)
        _normalize_indexes()

    elif action == "edit_story_prompt":
        new_prompt = data["new_prompt"]
        story_state.prompt = new_prompt
        pages = _generate_initial_pages(new_prompt)
        story_state.pages = [StoryText(index=i, text=p) for i, p in enumerate(pages)]

    # Entity tools
    elif action == "add_entity":
        name = data["name"]
        if _find_entity(name):
            raise HTTPException(400, f"Entity '{name}' already exists. Use update_entity instead.")
        entities_state.append(StoryEntity(**data))

    elif action == "update_entity":
        ent = _find_entity(data["name"])
        if ent is None:
            raise HTTPException(404, "Entity not found.")
        if "b64_json" in data:
            ent.b64_json = data["b64_json"]
        if "prompt" in data:
            ent.prompt = data["prompt"]

    elif action == "delete_entity":
        ent = _find_entity(data["name"])
        if ent is None:
            raise HTTPException(404, "Entity not found.")
        entities_state.remove(ent)

    else:
        raise HTTPException(400, f"Unknown action {action}")

    return extra


# ────────────────────────────
# ░░ API endpoint ░░
# ────────────────────────────

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    global story_state, entities_state, MESSAGE_HISTORY

    if req.story is not None:
        story_state = req.story
        _normalize_indexes()
    if req.entities is not None:
        entities_state = list(req.entities)

    tool_calls, assistant_output = _openai_call(req.user_input)
    print("TOOL_CALS: ", tool_calls, "\n---")

    # Normal chat
    if not tool_calls:
        return ChatResponse(
            mode=Mode.CONTINUE_CHAT,
            assistant_output=assistant_output,
            story=story_state,
            entities=entities_state,
        )

    # One or more tool calls
    for action, payload, tool_call_id in tool_calls:
        extras = _apply_action(action, payload)
        MESSAGE_HISTORY.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": action,
            "content": json.dumps({
                "prompt": story_state.prompt,
                "pages": [pg.text for pg in story_state.pages],
            }),
        })

    MESSAGE_HISTORY = MESSAGE_HISTORY[-MAX_HISTORY:]
    return ChatResponse(
        mode=Mode(tool_calls[-1][0]),  # mode of last action
        story=story_state,
        entities=entities_state,
        image_urls=extras.get("image_urls", None),
    )


# uvicorn main:app --reload

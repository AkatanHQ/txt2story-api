"""
StoryGPT Backend – FastAPI + OpenAI 2.1.0
-----------------------------------------

A FastAPI backend for an interactive, pageable storytelling chat.
It leverages OpenAI *function‑calling* to decide whether the user
wants to chat, tweak pages, or regenerate the entire story.

Changes in v2.1.0 (2025‑05‑07)
• 🆕 **set_page_count** – resize the story *and regenerate fresh text* so the
  page count and content always match.
• 🔄 Updated system‑prompt & TOOLS to advertise the new helper.
• 🧼 Removed placeholder logic; resizing now always produces coherent text.
• Minor tidy‑ups & version bump.

Run:
    pip install fastapi uvicorn pydantic python-dotenv openai
    export OPENAI_API_KEY="sk‑..."
    uvicorn main:app --reload
"""

from __future__ import annotations

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
app = FastAPI(title="StoryGPT Backend", version="2.1.0")

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
    GENERATE_IMAGE = "generate_image"
    SET_PAGE_COUNT = "set_page_count"


class StoryText(BaseModel):
    index: int
    text: str = Field(default="")
    image_url: Optional[str] = Field(default=None)


class Story(BaseModel):
    prompt: str = Field(default="")
    pages: List[StoryText] = Field(default_factory=list)


class ChatRequest(BaseModel):
    user_input: str


class ChatResponse(BaseModel):
    mode: Mode
    assistant_output: Optional[str] = None
    story: Optional[Story] = None
    image_urls: Optional[List[str]] = None


# ────────────────────────────
# ░░ In‑memory state ░░
# ────────────────────────────
story_state = Story(
    prompt="An epic tale begins.",
    pages=[StoryText(index=0, text="Once upon a time …")],
)

MAX_HISTORY = 20
MESSAGE_HISTORY: List[dict] = []  # excludes system prompt

# ────────────────────────────
# ░░ OpenAI tool definitions ░░
# ────────────────────────────
TOOLS: List[Dict] = [
    {
        "type": "function",
        "function": {
            "name": "continue_chat",
            "description": "Keep chatting with the user.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_text",
            "description": "Edit the text of a single page by index.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "Zero‑based page index."},
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
            "description": "Update the story prompt and regenerate initial pages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_prompt": {"type": "string", "description": "New prompt."}
                },
                "required": ["new_prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "Generate an illustration for a page and store its URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "description": "Page index."},
                    "prompt": {"type": "string", "description": "Image prompt override."},
                    "size": {
                        "type": "string",
                        "enum": ["512x512", "1024x1024", "1792x1024", "1024x1792"],
                        "description": "Image size.",
                    },
                },
                "required": ["page"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_page_count",
            "description": (
                "Resize the story to exactly `count` pages *and regenerate fresh page texts* "
                "based on the current story prompt."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "description": "Desired page count (≥1)."}
                },
                "required": ["count"],
            },
        },
    },
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
                "elements, each 1‑2 sentences long, continuing the user's prompt. Do NOT wrap "
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


def _generate_image_for_page(idx: int, prompt: str, size: str = "1024x1024") -> str:
    resp = client.images.generate(model="dall-e-3", prompt=prompt, n=1, size=size)
    url = resp.data[0].url  # type: ignore[attr-defined]
    story_state.pages[idx].image_url = url
    return url


def _openai_call(user_msg: str) -> Tuple[str, dict]:
    global MESSAGE_HISTORY
    MESSAGE_HISTORY.append({"role": "user", "content": user_msg})
    MESSAGE_HISTORY = MESSAGE_HISTORY[-MAX_HISTORY:]

    SYSTEM_PROMPT = (
        "You are StoryGPT. Decide if the user is chatting or wants to use a tool.\n\n"
        "Tools:\n"
        "• continue_chat – normal conversation\n"
        "• edit_text – replace text of one page\n"
        "• edit_all – replace every page\n"
        "• insert_page – add a page\n"
        "• delete_page – remove a page\n"
        "• move_page – reorder pages\n"
        "• edit_story_prompt – new synopsis\n"
        "• generate_image – illustrate a page\n"
        "• set_page_count – regenerate the story with a new number of pages\n\n"
        "If invoking a tool, respond ONLY with the function call JSON. Otherwise use continue_chat."
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + MESSAGE_HISTORY
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )
    msg = resp.choices[0].message

    if msg.tool_calls:
        call = msg.tool_calls[0]
        try:
            args = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        return call.function.name, args

    assistant_text = (msg.content or "").strip()
    MESSAGE_HISTORY.append({"role": "assistant", "content": assistant_text})
    MESSAGE_HISTORY = MESSAGE_HISTORY[-MAX_HISTORY:]
    return "continue_chat", {"assistant_output": assistant_text}


# ────────────────────────────
# ░░ Apply actions ░░
# ────────────────────────────

def _apply_action(action: str, data: dict) -> Dict:
    extra: Dict = {}
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

    elif action == "generate_image":
        idx = data["page"]
        if not 0 <= idx < len(story_state.pages):
            raise HTTPException(400, "Image page index out of range.")
        prompt = data.get("prompt") or story_state.pages[idx].text
        size = data.get("size", "1024x1024")
        url = _generate_image_for_page(idx, prompt, size)
        extra["image_urls"] = [url]

    elif action == "set_page_count":
        count = data["count"]
        if count < 1:
            raise HTTPException(400, "count must be ≥1")
        new_pages = _generate_initial_pages(story_state.prompt, num_pages=count)
        story_state.pages = [StoryText(index=i, text=t) for i, t in enumerate(new_pages)]

    else:
        raise HTTPException(400, f"Unknown action {action}")

    return extra


# ────────────────────────────
# ░░ API endpoint ░░
# ────────────────────────────

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    action, payload = _openai_call(req.user_input)

    # Simple chat
    if action == "continue_chat":
        return ChatResponse(
            mode=Mode.CONTINUE_CHAT,
            assistant_output=payload.get("assistant_output", ""),
            story=story_state,
        )

    # Tool call
    extras = _apply_action(action, payload)
    return ChatResponse(mode=Mode(action), story=story_state, image_urls=extras.get("image_urls"))


# uvicorn main:app --reload

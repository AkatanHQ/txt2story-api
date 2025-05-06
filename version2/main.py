"""StoryGPT Backend (main.py) – OpenAI ≥ 1.0 compatible
----------------------------------------------------------------
FastAPI backend for an interactive story‑telling chat, powered by
OpenAI *function calling* (`tools=` API) for intent detection.

Supported actions (tools):
• `continue_chat`      – keep chatting with the user
• `edit_text`          – edit the text of page N
• `edit_image_prompt`  – edit the image prompt of page N
• `edit_all`           – edit both text & image prompt of page N
• `edit_story_prompt`  – update the overall story synopsis
• `generate_image`     – create DALL·E images for page N

Quick start:
    pip install fastapi uvicorn pydantic openai python-dotenv
    export OPENAI_API_KEY="sk‑..."
    uvicorn main:app --reload
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel

# ────────────────────────────
# ░░ OpenAI client ░░
# ────────────────────────────
client = OpenAI()  # reads OPENAI_API_KEY from env or .env

# ────────────────────────────
# ░░ FastAPI app ░░
# ────────────────────────────
app = FastAPI(title="StoryGPT Backend", version="1.0.0")

# ────────────────────────────
# ░░ Data models ░░
# ────────────────────────────
class Mode(str, Enum):
    CONTINUE_CHAT = "continue_chat"
    EDIT_TEXT = "edit_text"
    EDIT_IMAGE_PROMPT = "edit_image_prompt"
    EDIT_ALL = "edit_all"
    EDIT_STORY_PROMPT = "edit_story_prompt"
    GENERATE_IMAGE = "generate_image"


class StoryPage(BaseModel):
    index: int
    text: str = ""
    image_prompt: Optional[str] = None


class Story(BaseModel):
    prompt: str = ""
    pages: List[StoryPage] = []


class ChatRequest(BaseModel):
    conversation_id: str
    user_input: str
    story_id: Optional[str] = None  # default: same as conversation


class ChatResponse(BaseModel):
    mode: Mode
    assistant_output: Optional[str] = None
    story: Optional[Story] = None
    image_urls: Optional[List[str]] = None


# ────────────────────────────
# ░░ In‑memory stores ░░   (swap for DB/Redis later)
# ────────────────────────────
messages: Dict[str, List[Dict[str, str]]] = {}
stories: Dict[str, Story] = {}

# ────────────────────────────
# ░░ Function / tool schema ░░
# ────────────────────────────
FUNCTION_DEFS = [
    {
        "name": "continue_chat",
        "description": "Continue the chat conversation with the user.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "edit_text",
        "description": "Edit the text of a single story page.",
        "parameters": {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "description": "Zero‑based page index."},
                "new_text": {"type": "string", "description": "Replacement page text."},
            },
            "required": ["page", "new_text"],
        },
    },
    {
        "name": "edit_image_prompt",
        "description": "Edit the image prompt of a single story page.",
        "parameters": {
            "type": "object",
            "properties": {
                "page": {"type": "integer"},
                "new_image_prompt": {"type": "string"},
            },
            "required": ["page", "new_image_prompt"],
        },
    },
    {
        "name": "edit_all",
        "description": "Edit both text and image prompt of a single story page.",
        "parameters": {
            "type": "object",
            "properties": {
                "page": {"type": "integer"},
                "new_text": {"type": "string"},
                "new_image_prompt": {"type": "string"},
            },
            "required": ["page", "new_text", "new_image_prompt"],
        },
    },
    {
        "name": "edit_story_prompt",
        "description": "Edit the overall story prompt / synopsis.",
        "parameters": {
            "type": "object",
            "properties": {
                "new_story_prompt": {"type": "string", "description": "New synopsis."},
            },
            "required": ["new_story_prompt"],
        },
    },
    {
        "name": "generate_image",
        "description": "Generate new DALL·E image(s) for a story page.",
        "parameters": {
            "type": "object",
            "properties": {
                "page": {"type": "integer"},
                "n": {
                    "type": "integer",
                    "default": 1,
                    "description": "Number of images to create (default 1)",
                },
            },
            "required": ["page"],
        },
    },
]

TOOLS = [{"type": "function", "function": f} for f in FUNCTION_DEFS]
FUNCTION_TO_MODE = {f["name"]: Mode(f["name"]) for f in FUNCTION_DEFS}

# ────────────────────────────
# ░░ Helper functions ░░
# ────────────────────────────
def detect_intent(user_input: str) -> Tuple[Mode, dict]:
    """Use GPT (tools API) to pick which function the user wants."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an intent‑detection assistant for a story‑telling chat. "
                    "Return exactly one function call that matches the user's request. "
                    "If none fit, call `continue_chat`."
                ),
            },
            {"role": "user", "content": user_input},
        ],
        tools=TOOLS,
        tool_choice="auto",
    )

    msg = resp.choices[0].message
    if msg.tool_calls:
        tc = msg.tool_calls[0]
        fn_name = tc.function.name  # type: ignore[attr-defined]
        raw_args = tc.function.arguments or "{}"  # type: ignore[attr-defined]
        try:
            args = json.loads(raw_args)
        except json.JSONDecodeError:
            args = {}
        return FUNCTION_TO_MODE.get(fn_name, Mode.CONTINUE_CHAT), args
    return Mode.CONTINUE_CHAT, {}


def chat_completion(history: List[Dict[str, str]]) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=history,
        temperature=0.8,
    )
    return resp.choices[0].message.content


def dalle_image(prompt: str, n: int = 1, size: str = "1024x1024") -> List[str]:
    resp = client.images.generate(prompt=prompt, n=n, size=size)
    return [d.url for d in resp.data]


def _ensure_page(story_id: str, idx: int) -> Story:
    story = stories.setdefault(story_id, Story(id=story_id))
    while len(story.pages) <= idx:
        story.pages.append(StoryPage(index=len(story.pages)))
    return story

# ────────────────────────────
# ░░ API route ░░
# ────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # 1 Detect intent
    mode, args = detect_intent(req.user_input)

    # 2 Record user message
    conv = messages.setdefault(req.conversation_id, [])
    conv.append({"role": "user", "content": req.user_input})

    # 3 Story context
    story_id = req.story_id or req.conversation_id

    # 4 Execute action
    if mode is Mode.CONTINUE_CHAT:
        assistant = chat_completion(conv)
        conv.append({"role": "assistant", "content": assistant})
        return ChatResponse(mode=mode, assistant_output=assistant)

    if mode is Mode.EDIT_STORY_PROMPT:
        new_prompt = args.get("new_story_prompt")
        if not new_prompt:
            raise HTTPException(400, "Missing `new_story_prompt`.")
        story = stories.setdefault(story_id, Story(id=story_id))
        story.prompt = new_prompt
        return ChatResponse(mode=mode,
                            assistant_output="Story prompt updated.",
                            story=story)

    if mode is Mode.EDIT_TEXT:
        idx, new_text = args.get("page"), args.get("new_text")
        if idx is None or new_text is None:
            raise HTTPException(400, "`page` and `new_text` are required.")
        story = _ensure_page(story_id, idx)
        story.pages[idx].text = new_text
        return ChatResponse(mode=mode,
                            assistant_output=f"Page {idx} text updated.",
                            story=story)

    if mode is Mode.EDIT_IMAGE_PROMPT:
        idx, new_img = args.get("page"), args.get("new_image_prompt")
        if idx is None or new_img is None:
            raise HTTPException(400, "`page` and `new_image_prompt` are required.")
        story = _ensure_page(story_id, idx)
        story.pages[idx].image_prompt = new_img
        return ChatResponse(mode=mode,
                            assistant_output=f"Page {idx} image prompt updated.",
                            story=story)

    if mode is Mode.EDIT_ALL:
        idx = args.get("page")
        new_text = args.get("new_text")
        new_img = args.get("new_image_prompt")
        if idx is None or new_text is None or new_img is None:
            raise HTTPException(400,
                                "`page`, `new_text`, and `new_image_prompt` are required.")
        story = _ensure_page(story_id, idx)
        story.pages[idx].text = new_text
        story.pages[idx].image_prompt = new_img
        return ChatResponse(mode=mode,
                            assistant_output=f"Page {idx} text and image prompt updated.",
                            story=story)

    if mode is Mode.GENERATE_IMAGE:
        idx = args.get("page")
        n = args.get("n", 1)
        if idx is None:
            raise HTTPException(400, "`page` is required.")
        story = _ensure_page(story_id, idx)
        prompt = story.pages[idx].image_prompt or f"Illustration for page {idx} of the story."
        urls = dalle_image(prompt, n=n)
        return ChatResponse(mode=mode,
                            assistant_output="Images generated.",
                            story=story,
                            image_urls=urls)

    # If we somehow fall through:
    raise HTTPException(500, f"Unhandled mode '{mode}'.")

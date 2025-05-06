"""StoryGPT Backend – FastAPI + OpenAI 1.4.1 function calling
-----------------------------------------------------------------
FastAPI backend for an interactive story‑telling chat. Uses OpenAI
function‑calling tools to decide whether the user wants to continue
chatting, edit a specific page, edit all pages, or update the story
synopsis.

Changes in v1.4.1 (2025‑05‑06):
• **Robust JSON parsing** – Fixed stray ```json code‑fence lines appearing as pages.
  ‑ `_parse_json_or_lines()` now strips triple‑backtick fences, isolates the JSON
    array between the first `[` and last `]`, and retries parsing. Fallback line
    split skips the lone `[` / `]` markers.
• **Prompt tweak** – Added a "Do *NOT* wrap in code fences" reminder so the model
  is less likely to output markdown blocks in the first place.

Run:
    pip install fastapi uvicorn pydantic openai python-dotenv
    export OPENAI_API_KEY="sk‑..."
    uvicorn main:app --reload
"""

from __future__ import annotations

import json
import logging
import os
import re
from enum import Enum
from typing import List, Optional, Tuple

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel

# ────────────────────────────
# ░░ Environment & logging ░░
# ────────────────────────────
load_dotenv()  # reads .env if present

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=LOG_LEVEL,
)
logger = logging.getLogger("storygpt")
logger.info("Logging initialised at %s level", LOG_LEVEL)

client = OpenAI()  # reads OPENAI_API_KEY from env or .env

# ────────────────────────────
# ░░ FastAPI app ░░
# ────────────────────────────
app = FastAPI(title="StoryGPT Backend", version="1.4.1")

# ────────────────────────────
# ░░ Data models ░░
# ────────────────────────────
class Mode(str, Enum):
    CONTINUE_CHAT = "continue_chat"
    EDIT_TEXT = "edit_text"
    EDIT_ALL = "edit_all"
    EDIT_STORY_PROMPT = "edit_story_prompt"


class StoryText(BaseModel):
    index: int
    text: str = ""


class Story(BaseModel):
    prompt: str = ""
    pages: List[StoryText] = []


class ChatRequest(BaseModel):
    user_input: str


class ChatResponse(BaseModel):
    mode: Mode
    assistant_output: Optional[str] = None
    story: Optional[Story] = None
    image_urls: Optional[List[str]] = None


# ────────────────────────────
# ░░ In‑memory story & chat state ░░
# ────────────────────────────
story_state = Story(
    prompt="An epic tale begins.",
    pages=[StoryText(index=0, text="Once upon a time …")],
)

# Keep the last N user/assistant messages to provide context.
MAX_HISTORY = 20
MESSAGE_HISTORY: List[dict] = []  # excludes the system prompt

# ────────────────────────────
# ░░ OpenAI tool definitions ░░
# ────────────────────────────
TOOLS = [
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
                    "page": {
                        "type": "integer",
                        "description": "Zero‑based page index to edit.",
                    },
                    "new_text": {
                        "type": "string",
                        "description": "Replacement text (1‑2 sentences).",
                    },
                },
                "required": ["page", "new_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_all",
            "description": "Replace every page with new text entries (same length).",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_texts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of new page texts in order (each 1‑2 sentences).",
                    }
                },
                "required": ["new_texts"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_story_prompt",
            "description": "Update the overall story prompt/synopsis and regenerate the story start to match (if no instruction given: 5 pages, 1‑2 sentences each).",
            "parameters": {
                "type": "object",
                "properties": {
                    "new_prompt": {
                        "type": "string",
                        "description": "New story prompt replacing the old one.",
                    }
                },
                "required": ["new_prompt"],
            },
        },
    },
]

SYSTEM_PROMPT = (
    "You are StoryGPT, a cooperative story‑writing assistant. A user will either chat "
    "casually or ask to modify the story. Decide which action fits best and respond as "
    "a function call.\n\nActions:\n• continue_chat – respond normally\n• edit_text – update one page"\
    "\n• edit_all – replace all pages\n• edit_story_prompt – change the synopsis. If the user asks to create/start a story and "
    "doesn't specify page content, pick *edit_story_prompt* with their request as `new_prompt`. "
    "When you regenerate, produce 5 pages with only 1‑2 sentences each.\n\nWhen editing, respond "
    "*only* with the function call and arguments (no prose). Otherwise, produce assistant_output via continue_chat."
)

# ────────────────────────────
# ░░ Helper functions ░░
# ────────────────────────────

def _clean_json_fence(raw: str) -> str:
    """Remove triple‑backtick fences and isolate JSON array text."""
    # Strip any ```json or ``` wrapper lines
    cleaned = re.sub(r"```\w*", "", raw).strip()
    # Extract substring between first '[' and last ']'
    match = re.search(r"\[.*]", cleaned, re.S)
    if match:
        cleaned = match.group(0)
    return cleaned.strip()


def _parse_json_or_lines(text: str, expected: int = 5) -> List[str]:
    """Parse a JSON array emitted by the model, handling code fences; fallback to line split."""
    cleaned = _clean_json_fence(text)

    # First try strict JSON
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            pages = [str(x).strip() for x in data if str(x).strip()]
        else:
            pages = []
    except json.JSONDecodeError:
        # Fallback: split into non‑empty lines, strip bullet numbers and lone brackets
        pages = [
            re.sub(r"^\s*\d+[).\-]?\s*", "", ln).strip()
            for ln in cleaned.splitlines()
            if ln.strip() and ln.strip() not in {"[", "]"}
        ]

    # Pad or trim
    if len(pages) < expected:
        pages += ["…"] * (expected - len(pages))
    return pages[:expected]


def _generate_initial_pages(prompt: str, num_pages: int = 5) -> List[str]:
    """Generate a short outline with exactly `num_pages` items, 1‑2 sentences each."""
    logger.info("⚙️  Generating %d short pages for new prompt …", num_pages)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a creative storyteller. Given the user's prompt below, respond "
                "with a *JSON array* of exactly 5 strings. Each string must be 1–2 sentences "
                "that can serve as a concise page of the story. Do *NOT* wrap the array in "
                "markdown or triple backticks. Return only the JSON array."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=300,
        temperature=0.7,
    )
    raw = response.choices[0].message.content.strip()
    logger.debug("Raw page list from model: %s", raw)
    pages = _parse_json_or_lines(raw, expected=num_pages)
    logger.debug("Parsed pages: %s", pages)
    return pages


def _openai_call(user_message: str) -> Tuple[str, dict]:
    """Send the user message + conversation context to OpenAI and return `(action, args)`."""
    global MESSAGE_HISTORY

    MESSAGE_HISTORY.append({"role": "user", "content": user_message})
    MESSAGE_HISTORY = MESSAGE_HISTORY[-MAX_HISTORY:]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + MESSAGE_HISTORY

    logger.info("🔁  Sending %d messages to OpenAI (latest user: %s)", len(messages), user_message)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    choice = response.choices[0]
    assistant_msg = choice.message

    if assistant_msg.tool_calls:
        call = assistant_msg.tool_calls[0]
        try:
            args = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        logger.info("🛠️  Tool chosen → %s %s", call.function.name, args)
        return call.function.name, args

    assistant_text = (assistant_msg.content or "").strip()
    logger.info("💬  Assistant chat response (no tool): %s", assistant_text)

    MESSAGE_HISTORY.append({"role": "assistant", "content": assistant_text})
    MESSAGE_HISTORY = MESSAGE_HISTORY[-MAX_HISTORY:]

    return "continue_chat", {"assistant_output": assistant_text}


def _apply_edit(action: str, data: dict) -> None:
    """Apply the requested edit to the in‑memory `story_state`."""
    global story_state

    logger.info("✏️  Applying edit action=%s payload=%s", action, data)

    if action == "edit_text":
        idx = data["page"]
        if not 0 <= idx < len(story_state.pages):
            logger.error("Page index %s out of range", idx)
            raise HTTPException(400, f"Page index {idx} is out of range.")
        story_state.pages[idx].text = data["new_text"]

    elif action == "edit_all":
        new_texts = data["new_texts"]
        story_state.pages = [ StoryText(index=i, text=t) for i, t in enumerate(new_texts) ]

    elif action == "edit_story_prompt":
        new_prompt = data["new_prompt"]
        story_state.prompt = new_prompt
        pages = _generate_initial_pages(new_prompt)
        story_state.pages = [StoryText(index=i, text=p) for i, p in enumerate(pages)]

    logger.debug("New story state: %s", story_state)


# ────────────────────────────
# ░░ API endpoint ░░
# ────────────────────────────
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Single endpoint that interprets the user's intent via OpenAI."""

    logger.info("➡️  /chat called with input: %s", req.user_input)
    action, payload = _openai_call(req.user_input)
    logger.info("⬅️  Action decided: %s", action)

    if action == "continue_chat":
        response = ChatResponse(
            mode=Mode.CONTINUE_CHAT,
            assistant_output=payload.get("assistant_output", ""),
            story=story_state,
        )
        logger.debug("Returning chat response: %s", response)
        return response

    _apply_edit(action, payload)
    response = ChatResponse(mode=Mode(action), story=story_state)
    logger.debug("Returning edit response: %s", response)
    return response


# ────────────────────────────
# ░░ Run locally ░░
# ────────────────────────────
# uvicorn main:app --reload
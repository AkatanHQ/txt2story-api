from __future__ import annotations
"""
StoryGPT Backend – FastAPI + OpenAI 2.2.1 (stateless)
----------------------------------------------------

This version refactors the `/chat` endpoint to be fully **stateless** per request
and async‑friendly, matching the signature the frontend now expects.
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI

from schemas import (
    Story,
    StoryText,
    StoryEntity,
    ChatRequest,
    ChatResponse,
    Mode,
)
from tools import TOOLS

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

client = OpenAI()

# ────────────────────────────
# ░░ Constants ░░
# ────────────────────────────
MAX_HISTORY = 20  # conversation turns we keep per request

# ────────────────────────────
# ░░ FastAPI app ░░
# ────────────────────────────
app = FastAPI(title="StoryGPT Backend", version="2.2.1")

# ────────────────────────────
# ░░ Helpers ░░
# ────────────────────────────

def _clean_json_fence(raw: str) -> str:
    cleaned = re.sub(r"```\w*", "", raw).strip()
    match = re.search(r"\[.*]", cleaned, re.S)
    return match.group(0).strip() if match else cleaned


def _parse_json_or_lines(text: str) -> List[str]:
    cleaned = _clean_json_fence(text)
    try:
        data = json.loads(cleaned)
        pages = (
            [str(x).strip() for x in data if str(x).strip()]
            if isinstance(data, list)
            else []
        )
    except json.JSONDecodeError:
        pages = [
            re.sub(r"^\s*\d+[).\-]?\s*", "", ln).strip()
            for ln in cleaned.splitlines()
            if ln.strip() and ln.strip() not in {"[", "]"}
        ]
    return pages


def _generate_story_pages(
    prompt: str, *, entities: Optional[List[StoryEntity]] = None, n: int = 5
) -> List[str]:
    """Call OpenAI to expand the prompt into *n* 1‑2 sentence pages."""

    ent_desc = "\n".join(
        f"- {e.name}: {e.prompt or 'image only'}" for e in (entities or [])
    ) or "(none)"

    logger.info("Generating pages for prompt with %d entit(y|ies)", len(entities or []))

    messages = [
        {
            "role": "system",
            "content": (
                "You are a creative storyteller. The following reusable story "
                "entities are available and should be woven naturally into the "
                "narrative whenever relevant:\n\n"
                f"{ent_desc}\n\n"
                "Return *only* a JSON array containing exactly {n} elements. "
                "Each element must be 1–2 sentences of story text that "
                "continues the user's prompt. Do **NOT** wrap the array in "
                "markdown code fences or add any extra keys."
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
    return _parse_json_or_lines(raw)


def _normalize_indexes(story: Story) -> None:
    for i, pg in enumerate(story.pages):
        pg.index = i

# ────────────────────────────
# ░░ Entity helpers ░░
# ────────────────────────────

def _find_entity(name: str, entities: List[StoryEntity]) -> Optional[StoryEntity]:
    return next((e for e in entities if e.name == name), None)

# ────────────────────────────
# ░░ OpenAI chat orchestration ░░
# ────────────────────────────

def _intent_agent(
    user_msg: str,
    story: Story,
    entities: List[StoryEntity],
    history: List[dict],
) -> Tuple[List[Tuple[str, dict]], Optional[str]]:
    """Run the shallow intent agent to decide whether to call tools."""

    history.append({"role": "user", "content": user_msg})
    history[:] = history[-MAX_HISTORY:]

    SYSTEM_PROMPT = (
        "You are StoryGPT. Decide if the user is chatting or wants to use a tool.\n\n"
        "If tool use is needed, respond ONLY with the appropriate function call(s).\n\n"
        "You are allowed to return **multiple tool calls in a single response**.\n\n"
        "Current story state:\n"
        f"• Pages: {len(story.pages)}\n"
        f"• Entities ({len(entities)}): {', '.join(e.name for e in entities) or '–'}\n"
        f"• Prompt: {story.prompt[:120]}{'…' if len(story.prompt) > 120 else ''}\n\n"
        "Available tools: see function definitions.\n\n"
        "If no tools make sense, just respond conversationally — but steer the user toward story creation."
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    msg = resp.choices[0].message

    tool_calls: List[Tuple[str, dict]] = []
    assistant_output: Optional[str] = None

    if msg.tool_calls:
        history.append({"role": "assistant", "content": None})
        for call in msg.tool_calls:
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            tool_calls.append((call.function.name, args))
    else:
        assistant_output = (msg.content or "").strip()
        history.append({"role": "assistant", "content": assistant_output})

    return tool_calls, assistant_output

# ────────────────────────────
# ░░ Apply actions ░░
# ────────────────────────────

def _apply_action(
    action: str,
    data: dict,
    story: Story,
    entities: List[StoryEntity],
) -> Dict:
    """Mutate *story* and *entities* in‑place according to the tool call."""

    extras: Dict = {}

    # Page / story tools
    if action == "edit_story_prompt":
        new_prompt = data["new_prompt"]
        story.prompt = new_prompt
        pages = _generate_story_pages(new_prompt, entities=entities)
        story.pages = [StoryText(index=i, text=p) for i, p in enumerate(pages)]

    elif action == "edit_text":
        idx = data["page"]
        if not 0 <= idx < len(story.pages):
            raise HTTPException(400, "Page index out of range.")
        story.pages[idx].text = data["new_text"]

    elif action == "edit_all":
        new_texts = data["new_texts"]
        story.pages = [StoryText(index=i, text=t) for i, t in enumerate(new_texts)]

    elif action == "insert_page":
        idx = data["index"]
        text = data["text"]
        if not 0 <= idx <= len(story.pages):
            raise HTTPException(400, "Insert index out of range.")
        story.pages.insert(idx, StoryText(index=idx, text=text))
        _normalize_indexes(story)

    elif action == "delete_page":
        idx = data["index"]
        if not 0 <= idx < len(story.pages):
            raise HTTPException(400, "Delete index out of range.")
        story.pages.pop(idx)
        _normalize_indexes(story)

    elif action == "move_page":
        frm, to = data["from_index"], data["to_index"]
        if not (0 <= frm < len(story.pages)) or not (0 <= to < len(story.pages)):
            raise HTTPException(400, "Move indexes out of range.")
        page = story.pages.pop(frm)
        story.pages.insert(to, page)
        _normalize_indexes(story)

    # Entity tools
    elif action == "add_entity":
        name = data["name"]
        if _find_entity(name, entities):
            raise HTTPException(400, f"Entity '{name}' already exists. Use update_entity instead.")
        entities.append(StoryEntity(**data))

    elif action == "update_entity":
        ent = _find_entity(data["name"], entities)
        if ent is None:
            raise HTTPException(404, "Entity not found.")
        if "new_name" in data and data["new_name"]:
            if _find_entity(data["new_name"], entities):
                raise HTTPException(400, f"Entity '{data['new_name']}' already exists.")
            ent.name = data["new_name"]
        if "b64_json" in data:
            ent.b64_json = data["b64_json"]
        if "prompt" in data:
            ent.prompt = data["prompt"]

    elif action == "delete_entity":
        ent = _find_entity(data["name"], entities)
        if ent is None:
            raise HTTPException(404, "Entity not found.")
        entities.remove(ent)

    else:
        raise HTTPException(400, f"Unknown action {action}")

    return extras

# ────────────────────────────
# ░░ API endpoint ░░
# ────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    print("\n======= NEW /chat REQUEST =======")
    print("User input:", req.user_input)

    story: Story = req.story or Story(prompt="")
    entities: List[StoryEntity] = list(req.entities or [])
    history: List[dict] = list(req.history or [])

    tool_calls, assistant_output = _intent_agent(req.user_input, story, entities, history)

    mode = Mode.CONTINUE_CHAT.value
    if tool_calls:
        for action, args in tool_calls:
            _apply_action(action, args, story, entities)
            mode = action  # name of the last tool executed

    if not tool_calls and not assistant_output:
        assistant_output = "(no response)"

    print("Returning response with mode:", mode)
    return ChatResponse(
        mode=mode,
        assistant_output=assistant_output,
        story=story,
        entities=entities,
        history=history,
    )

# uvicorn main:app --reload

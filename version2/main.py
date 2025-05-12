from __future__ import annotations
from schemas import *
from tools import *
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
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI

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
# ░░ FastAPI app ░░
# ────────────────────────────
app = FastAPI(title="StoryGPT Backend", version="2.2.0")

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
        pages = [str(x).strip() for x in data if str(x).strip()] if isinstance(data, list) else []
    except json.JSONDecodeError:
        pages = [
            re.sub(r"^\s*\d+[).\-]?\s*", "", ln).strip()
            for ln in cleaned.splitlines()
            if ln.strip() and ln.strip() not in {"[", "]"}
        ]
    return pages


def _generate_story_pages(prompt: str, entities: Optional[List[StoryEntity]] = None) -> List[str]:
\
    ent_desc = "\n".join(
        f"- {e.name}: {e.prompt or 'image only'}" for e in (entities or [])
    ) or "(none)"

    logger.info(
        "Generating pages for prompt with %d entit(y|ies)",
        len(entities or []),
    )

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

def _intent_agent(user_msg: str) -> Tuple[List[Tuple[str, dict, str]], Optional[str]]:
    global MESSAGE_HISTORY
    MESSAGE_HISTORY.append({"role": "user", "content": user_msg})
    MESSAGE_HISTORY = MESSAGE_HISTORY[-MAX_HISTORY:]

    SYSTEM_PROMPT = (
        "You are StoryGPT. Decide if the user is chatting or wants to use a tool.\n\n"
        "If tool use is needed, respond ONLY with the appropriate function call(s).\n\n"
        "You are allowed to return **multiple tool calls in a single response**. "
        "Do this when the user message implies a sequence of operations (e.g. "
        "creating entities and then starting the story).\n\n"
        "Current story state:\n"
        f"• Pages: {len(story_state.pages)}\n"
        f"• Entities ({len(entities_state)}): "
        f"{', '.join(e.name for e in entities_state) or '–'}\n"
        f"• Prompt: {story_state.prompt[:120]}{'…' if len(story_state.prompt) > 120 else ''}\n\n"
        "Available tools:\n"
        "• edit_story_prompt – replace the story synopsis\n"

        "• edit_text – replace one page\n"
        "• edit_all – replace all pages\n"
        
        "• insert_page – add a page\n"
        "• delete_page – remove a page\n"
        "• move_page – reorder pages\n"

        "• add_entity – create a new character/entity\n"
        "• update_entity – change an entity’s name (`new_name`), image, or **delete / replace its prompt**"
            " (pass an empty string for `prompt` to clear it)\n"
        "• delete_entity – remove an entity\n\n"

        "If no tools make sense, just respond conversationally — but steer the user toward story creation.\n"
        "If it’s story-related and no tool fits exactly, use edit_story_prompt.\n"
        "Example:\n"
            "User: Create two characters and write a story about them.\n"
            "Tool calls:\n"
            "1. add_entity → name: Valandor, prompt: A brave warrior…\n"
            "2. add_entity → name: Lyra, prompt: A healer…\n"
            "3. edit_story_prompt → new_prompt: A tale of Valandor and Lyra...\n\n"
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
    if action == "edit_story_prompt":
        new_prompt = data["new_prompt"]
        story_state.prompt = new_prompt
        pages = _generate_story_pages(new_prompt, entities=entities_state)
        story_state.pages = [StoryText(index=i, text=p) for i, p in enumerate(pages)]
    elif action == "edit_text":
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
        if "new_name" in data and data["new_name"]:
            if _find_entity(data["new_name"]):
                raise HTTPException(400, f"Entity '{data['new_name']}' already exists.")
            ent.name = data["new_name"]
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

    tool_calls, assistant_output = _intent_agent(req.user_input)
    print("TOOL_CALS: ", tool_calls, "\n---")

    if not tool_calls:
        return ChatResponse(
            mode=Mode.CONTINUE_CHAT,
            assistant_output=assistant_output,
            story=story_state,
            entities=entities_state,
        )

    extras = {}
    for action, payload, tool_call_id in tool_calls:
        print("Action:", action)
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
        mode=Mode(tool_calls[-1][0]),
        assistant_output=assistant_output,
        story=story_state,
        entities=entities_state,
        image_urls=extras.get("image_urls", None),
    )


# uvicorn main:app --reload

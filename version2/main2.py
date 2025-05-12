# ──────────────────────────────────────────────────────────────
# storygpt_service.py  – micro‑service that keeps the **tool‑call**
#                        architecture of your monolith, but scoped
#                        to each request so the service remains
#                        stateless and horizontally scalable.
# -------------------------------------------------------------
# – Requires OPENAI_API_KEY.
# – Receives the current `story`, `entities`, and an optional
#   `history` list on every /chat request.
# – Runs the same _intent_agent logic (with TOOLS) to let GPT
#   decide whether to chat or emit function calls.
# – Applies those calls locally, returns the mutated state plus
#   any assistant text.
#
# If you *don’t* send a history array, the model sees only the
# latest user message + the summarised “system state” prompt.
# Add history if you want a multi‑turn memory.
# -------------------------------------------------------------

from __future__ import annotations

import json, os, re
from typing import Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from schemas import Mode, Story, StoryEntity, StoryText  # reuse the same models
from tools import TOOLS  # exact same definition list

try:
    from openai import OpenAI
except ImportError as exc:
    raise RuntimeError("pip install openai>=2.2.0") from exc

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=OPENAI_API_KEY)

# ─── Helper regex -------------------------------------------------------
_JSON_ARRAY_RE = re.compile(r"\[.*]", re.S)

def _clean_json_fence(raw: str) -> str:
    cleaned = re.sub(r"```\w*", "", raw).strip()
    m = _JSON_ARRAY_RE.search(cleaned)
    return m.group(0).strip() if m else cleaned

def _parse_json_or_lines(text: str) -> List[str]:
    cleaned = _clean_json_fence(text)
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
    except json.JSONDecodeError:
        pass
    return [ln.strip() for ln in cleaned.splitlines() if ln.strip() and ln.strip() not in {"[", "]"}]

# ─── Story generation helpers -----------------------------------------
PAGE_COUNT_DEFAULT = 5

def _entities_desc(ents: List[StoryEntity]) -> str:
    return "(none)" if not ents else "\n".join(f"- {e.name}: {e.prompt or 'image only'}" for e in ents)

def _generate_pages(prompt: str, entities: List[StoryEntity], n: int = PAGE_COUNT_DEFAULT) -> List[str]:
    sys_prompt = (
        "You are a creative storyteller. The following reusable story entities are available:"\
        f"\n\n{_entities_desc(entities)}\n\n"
        f"Return *only* a JSON array with exactly {n} elements. Each element must be 1–2 sentences that continues the user's prompt. Do NOT add keys or markdown fences."
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.7,
    )
    pages = _parse_json_or_lines(resp.choices[0].message.content.strip())
    if len(pages) != n:
        raise HTTPException(500, f"Expected {n} pages, got {len(pages)}")
    return pages

# ─── CRUD helpers -------------------------------------------------------

def _find_entity(entities: List[StoryEntity], name: str) -> Optional[StoryEntity]:
    return next((e for e in entities if e.name == name), None)

def _normalize_indexes(story: Story):
    for i, pg in enumerate(story.pages):
        pg.index = i

# ─── Apply a single tool call ------------------------------------------

def _apply_action(action: str, data: dict, story: Story, entities: List[StoryEntity]):
    if action == "edit_story_prompt":
        story.prompt = data["new_prompt"]
        story.pages = [StoryText(index=i, text=t) for i, t in enumerate(_generate_pages(story.prompt, entities))]

    elif action == "edit_text":
        idx = data["page"]
        if not 0 <= idx < len(story.pages):
            raise HTTPException(400, "Page index out of range")
        story.pages[idx].text = data["new_text"]

    elif action == "edit_all":
        story.pages = [StoryText(index=i, text=t) for i, t in enumerate(data["new_texts"])]

    elif action == "insert_page":
        idx = data["index"]
        story.pages.insert(idx, StoryText(index=idx, text=data["text"]))
        _normalize_indexes(story)

    elif action == "delete_page":
        idx = data["index"]
        if not 0 <= idx < len(story.pages):
            raise HTTPException(400, "Delete index out of range")
        story.pages.pop(idx)
        _normalize_indexes(story)

    elif action == "move_page":
        frm, to = data["from_index"], data["to_index"]
        if not (0 <= frm < len(story.pages)) or not (0 <= to < len(story.pages)):
            raise HTTPException(400, "Move indexes out of range")
        story.pages.insert(to, story.pages.pop(frm))
        _normalize_indexes(story)

    # Entity CRUD -------------------------------------------------------
    elif action == "add_entity":
        if _find_entity(entities, data["name"]):
            raise HTTPException(400, "Entity already exists")
        entities.append(StoryEntity(**data))

    elif action == "update_entity":
        ent = _find_entity(entities, data["name"])
        if not ent:
            raise HTTPException(404, "Entity not found")
        if data.get("new_name"):
            if _find_entity(entities, data["new_name"]):
                raise HTTPException(400, "Entity with new_name already exists")
            ent.name = data["new_name"]
        if "prompt" in data:
            ent.prompt = data["prompt"]
        if "b64_json" in data:
            ent.b64_json = data["b64_json"]

    elif action == "delete_entity":
        ent = _find_entity(entities, data["name"])
        if not ent:
            raise HTTPException(404, "Entity not found")
        entities.remove(ent)

    else:
        raise HTTPException(400, f"Unknown tool action {action}")

# ─── Intent agent -------------------------------------------------------
MAX_HISTORY = 20

def _intent_agent(user_msg: str, story: Story, entities: List[StoryEntity], history: List[dict]) -> Tuple[List[Tuple[str, dict]], Optional[str]]:
    history.append({"role": "user", "content": user_msg})
    history[:] = history[-MAX_HISTORY:]

    sys_prompt = (
        "You are StoryGPT. Decide whether to chat or call a tool. If a tool is needed, respond ONLY with function call(s).\n\n"
        f"Current story: pages={len(story.pages)}, entities={len(entities)}, prompt='{story.prompt[:60]}...'"
    )

    messages = [{"role": "system", "content": sys_prompt}] + history

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )
    msg = resp.choices[0].message

    # If GPT decided to call tools
    if msg.tool_calls:
        history.append({"role": "assistant", "content": None, "tool_calls": msg.tool_calls})
        calls: List[Tuple[str, dict]] = []
        for c in msg.tool_calls:
            try:
                args = json.loads(c.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            calls.append((c.function.name, args))
        return calls, None

    # Otherwise normal chat text
    assistant_text = (msg.content or "").strip()
    history.append({"role": "assistant", "content": assistant_text})
    return [], assistant_text

# ─── FastAPI ----------------------------------------------------------------
app = FastAPI(title="StoryGPT‑svc", version="0.3.0‑tools")

class _ChatRequest(BaseModel):
    user_input: str
    story: Optional[Story] = None
    entities: Optional[List[StoryEntity]] = None
    history: Optional[List[dict]] = None  # optional conversation memory

class _ChatResponse(BaseModel):
    mode: str
    assistant_output: Optional[str] = None
    story: Story
    entities: List[StoryEntity]
    history: List[dict]

@app.post("/chat", response_model=_ChatResponse)
async def chat(req: _ChatRequest):
    story = req.story or Story(prompt="")
    entities = list(req.entities or [])
    history = list(req.history or [])

    # First request & prompt supplied but no pages → auto‑generate pages
    if not story.pages and story.prompt:
        story.pages = [StoryText(index=i, text=t) for i, t in enumerate(_generate_pages(story.prompt, entities))]

    tool_calls, assistant_output = _intent_agent(req.user_input, story, entities, history)

    mode = Mode.CONTINUE_CHAT.value

    if tool_calls:
        for action, args in tool_calls:
            _apply_action(action, args, story, entities)
            mode = action  # last action wins
    # If no tool calls and assistant_output is empty, ensure we at least echo something
    if not tool_calls and not assistant_output:
        assistant_output = "(no response)"

    return _ChatResponse(
        mode=mode,
        assistant_output=assistant_output,
        story=story,
        entities=entities,
        history=history,
    )

# ----------------------------------------------------------------------
# The upstream "app_backend.py" from earlier remains unchanged – it just
# needs to include `history` in future requests if you want memory.
# ----------------------------------------------------------------------

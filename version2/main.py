from __future__ import annotations
"""
StoryGPT Backend – FastAPI + OpenAI 2.2.1 (stateless)
----------------------------------------------------

This version refactors the `/chat` endpoint to be fully **stateless** per request
and async‑friendly, matching the signature the frontend now expects.
----------------------------------------------------

Information:
Inputs
- Story holds the generate structure,
- storytext holds the text of 1 page of the story
- storyimage holds the prompt,size and quality of 1 page of the story
- Entities are given by the user and have a name (as id), possibly an image and a prompt

Dependencies/Relations
- The entities are input for when generating a new story, such that the AI know what entities to use in the story
- When generating an image, the input-prompt for AI will be: the StoryImage + the entities that are mentioned in the prompt 
  - 1 entity includes an image + prompt, and by referencing it correctly in the input for the ai
- When generating a new story, the input-prompt for AI will be: the prompt + the entities, such that the AI knows how to use and who to use in the story.
- In the ImagePrompt, if a entitity is needed as input, it will reference it by the name/id
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple
import httpx

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
    StoryImage,
)
from tools import TOOLS
from openai_helpers import run_with_retry 
from openai import OpenAIError
from io import BytesIO
import base64

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
    print("parsing")
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict) and "pages" in data:
            data = data["pages"]
        if isinstance(data, list) and all(isinstance(x, str) for x in data):
            return [x.strip() for x in data if x.strip()]
        raise ValueError("Parsed JSON is not a list of strings.")
    except Exception as e:
        logger.warning("Failed to parse JSON properly: %s", e)
        # Fallback: naive line splitting
        return [
            re.sub(r"^\s*\d+[).\-]?\s*", "", ln).strip()
            for ln in cleaned.splitlines()
            if ln.strip() and ln.strip() not in {"[", "]"}
        ]




def _generate_story_pages(
    prompt: str, entities: Optional[List[StoryEntity]] = None) -> List[str]:
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
                "Return *only* a JSON array of 1–2 sentence story passages. "
                "Each array element should continue the user's prompt. "
                "DO NOT include any labels like 'Page 1:', 'Page 2:', etc. "
                "Each item should be plain story text. "
                "DO NOT use markdown or wrap the response in code fences."
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
        "If you intend to use tools, DO NOT reply in natural language. ONLY return tool_calls using the OpenAI tools format."
        "You are allowed to return **multiple tool calls in a single response**.\n\n"
        "Always consider history as well, but focus on the most recent questions."

        "Current story state:\n"
        f"• Pages: {len(story.pages)}\n"
        f"• Entities ({len(entities)}): {', '.join(e.name for e in entities) or '–'}\n"
        f"• Prompt: {story.prompt[:120]}{'…' if len(story.prompt) > 120 else ''}\n\n"

        "Available tools:\n"
        "• edit_story_prompt – replace the story synopsis\n"

        "• edit_text – replace one page\n"
        "• edit_all – replace all pages\n"
        
        "• insert_page – add a page\n"
        "• delete_page – remove a page\n"
        "• move_page – reorder pages\n"

        "• add_entity – create a new unique character/entity\n"
        "• update_entity – change an entity’s name (`new_name`), image, or **delete / replace its prompt**"
            " (pass an empty string for `prompt` to clear it)\n"
        "• delete_entity – remove an entity\n\n"

        "• generate_image – Generate an image with optional entity inputs as references.\n\n"
        "• generate_image_for_index – Generate an image for a specific page / index\n\n"


        "- If no tools make sense, just respond conversationally — but steer the user toward story creation.\n"
        "- If it’s story-related and no tool fits exactly, use edit_story_prompt.\n"
        "- Also look at histroy, to make a decision."
        "- Entities may include an image (b64_json) and a prompt."
        "   - If both are provided, the prompt should describe visual *modifications* or *extras* to add to the image."
        "   - If only a prompt is provided, it fully describes the entity."

        "Example:\n"
            "User: Create two characters and write a story about them.\n"
            "Tool calls:\n"
            "1. add_entity → name: Valandor, prompt: A brave warrior…\n"
            "2. add_entity → name: Lyra, prompt: A healer…\n"
            "3. edit_story_prompt → new_prompt: A tale of Valandor and Lyra...\n\n"
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    resp = run_with_retry(
        client.chat.completions.create,
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    msg = resp.choices[0].message

    tool_calls: List[Tuple[str, dict]] = []
    assistant_output: Optional[str] = None

    if msg.tool_calls:
        history.append({"role": "assistant", "content": ""})
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
def _render_image(
    *,
    prompt: str,
    entity_names: List[str],
    entities: List[StoryEntity],
    size: str = "1024x1024",
    quality: str = "low",
) -> str:                     # returns image_b64
    """
    Build a prompt that stitches in any referenced entities, perform the
    OpenAI image (edit or generate) call, and return the resulting base-64
    PNG.  This is used by both `generate_image_for_index` and `generate_image`.
    """
    used_ents   = [e for e in entities if e.name in entity_names]

    image_files = [
        BytesIO(base64.b64decode(e.b64_json))
        for e in used_ents if e.b64_json
    ]

    # add entity-level instructions onto the prompt
    extra_lines = []
    for e in used_ents:
        if not e.prompt:
            continue
        if e.b64_json:
            extra_lines.append(f"{e.name}: add the following to the image – {e.prompt}")
        else:
            extra_lines.append(f"{e.name}: {e.prompt}")
    if extra_lines:
        prompt = f"{prompt}\n\n" + "\n".join(extra_lines)

    # ——— call OpenAI ———
    if image_files:                                   # image *edit*
        files   = [("image[]", (f"ent_{i}.png", f, "image/png"))
                   for i, f in enumerate(image_files)]
        payload = {
            "model":   "gpt-image-1",
            "prompt":  prompt,
            "quality": quality,
            "size":    size,
        }
        headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}
        r = httpx.post(
            "https://api.openai.com/v1/images/edits",
            headers=headers,
            data=payload,
            files=files,
        )
        if r.status_code != 200:
            logger.error("Image generation failed: %s", r.text)
            raise HTTPException(502, "Image generation failed: " + r.text)
        return r.json()["data"][0]["b64_json"]

    else:                                             # pure text *generate*
        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            n=1,
            size=size,
            quality=quality,
        )
        return result.data[0].b64_json


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

    
    elif action == "generate_image_for_index":
        page_idx     = data["page"]
        prompt       = data["prompt"]
        entity_names = data.get("entity_names", [])
        size         = data.get("size",    "1024x1024")
        quality      = data.get("quality", "low")

        image_b64 = _render_image(
            prompt=prompt,
            entity_names=entity_names,
            entities=entities,
            size=size,
            quality=quality,
        )

        img_cfg = StoryImage(
            index   = page_idx,
            prompt  = prompt,
            size    = size,
            quality = quality,
            b64_json= image_b64,
        )

        # make sure the list is long enough, then store
        if len(story.images) <= page_idx:
            story.images.extend([None] * (page_idx + 1 - len(story.images)))
        story.images[page_idx] = img_cfg
        return {}                           # no extras

    elif action == "generate_image":        # generic, just hand back b64
        prompt       = data["prompt"]
        entity_names = data.get("entity_names", [])
        size         = data.get("size",    "1024x1024")
        quality      = data.get("quality", "low")

        image_b64 = _render_image(
            prompt=prompt,
            entity_names=entity_names,
            entities=entities,
            size=size,
            quality=quality,
        )
        return {"image_b64": image_b64}
    elif action == "edit_text":
        idx = data["page"]
        if not 0 <= idx < len(story.pages):
            raise HTTPException(400, "Page index out of range.")
        story.pages[idx].text = data["new_text"]

    elif action == "edit_all":
        new_texts = data["new_texts"]
        story.pages = [StoryText(index=i, text=t) for i, t in enumerate(new_texts)]
        _normalize_indexes(story)

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
            # Silently turn it into an update instead of bombing out
            action = "update_entity"
            data = {"name": name, **data}
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

    try:
        tool_calls, assistant_output = _intent_agent(
            req.user_input, story, entities, history
        )
    except OpenAIError as e:
        logger.error("OpenAI call failed: %s", str(e))
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI error: {str(e)}"
        )

    mode = Mode.CONTINUE_CHAT.value
    executed_modes: List[Mode] = []

    extras = {}
    if tool_calls:
        for action, args in tool_calls:
            print(">> Executing tool:", action, args)
            action_result = _apply_action(action, args, story, entities)
            executed_modes.append(Mode(action))
            extras.update(action_result)
    else:
        executed_modes.append(Mode.CONTINUE_CHAT)

    print("Returning response with mode:", mode)
    return ChatResponse(
        modes=executed_modes,
        assistant_output=assistant_output,
        story=story,
        entities=entities,
        history=history,
        image_b64=extras.get("image_b64")
    )

# uvicorn main2:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

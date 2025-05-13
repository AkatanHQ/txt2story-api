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




def _generate_story_pages(prompt: str, entities: Optional[List[StoryEntity]] = None) -> List[str]:
    """Call OpenAI to expand the prompt into *n* 1‑2 sentence pages."""

    ent_desc = "\n".join(
        f"- {e.name}: {e.prompt or 'image only'}" for e in (entities or [])
    ) or "(none)"

    logger.info("Generating pages for prompt with %d entit(y|ies)", len(entities or []))

    messages = [
        {
            "role": "system",
            "content": (
                "You are a creative and concise children's story writer. You will receive a short story prompt and a list of reusable story entities (characters or important elements)."

            "Your task is to continue the story by generating a JSON array of short story segments (1–2 sentences each). These will become the pages of a picture book."

            "📌 Unless the user explicitly specifies otherwise, generate exactly **5** story pages.\n\n"

            "\n\nEach item in the array should:\n"
            "- Flow naturally from the previous segments.\n"
            "- Be plain English narrative (not dialogue-only, not poetry).\n"
            "- Be simple enough for children to understand.\n"
            "- Use the listed entities where relevant, integrating them naturally.\n"

            "\n\nImportant formatting rules:\n"
            "- Return ONLY a valid **JSON array** of strings. Example:\n"
            "  [\"John picked up a stick.\", \"The dog wagged its tail excitedly.\"]\n"
            "- **Do NOT** include any labels like 'Page 1:', 'Page 2:', etc.\n"
            "- **Do NOT** use markdown, quotes, bullets, or code blocks.\n"
            "- **Do NOT** wrap the array in triple backticks or fences.\n"
            "- **Each array element must be plain story text only.**\n"

            "\nReusable entities you may use in the story:\n"
            f"{ent_desc or '(none)'}"

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

# main.py – near _normalize_indexes() or anywhere you keep helpers
def _summarise_images(images) -> str:
    """Return a short bulleted list of the page images, omitting b64 data."""
    if not images:
        return "(none)"
    lines = []
    for img in images:
        if img is None:           # hole in the list
            continue
        snippet = (img.prompt or "")[:60]            # first 60 chars
        if len(snippet) < len(img.prompt or ""):
            snippet += "…"
        lines.append(
            f"- page {img.index}: size={img.size or '?'} "
            f"quality={img.quality or '?'} • prompt: {snippet}"
        )
    return "\n".join(lines)


def _intent_agent(
    user_msg: str,
    story: Story,
    entities: List[StoryEntity],
    history: List[dict],
) -> Tuple[List[Tuple[str, dict]], Optional[str]]:
    """Run the shallow intent agent to decide whether to call tools."""

    history.append({"role": "user", "content": user_msg})
    history[:] = history[-MAX_HISTORY:]
    images_summary = _summarise_images(story.images)

    SYSTEM_PROMPT = (
        "You are StoryGPT. Decide if the user is chatting or wants to use a tool.\n\n"
        "If tool use is needed, respond ONLY with the appropriate function call(s).\n\n"
        "If you intend to use tools, DO NOT reply in natural language. ONLY return tool_calls using the OpenAI tools format."
        "You are allowed to return **multiple tool calls in a single response**.\n\n"
        "Always consider history as well, but focus on the most recent questions."
        "- Never generate images unless the user clearly says to (e.g. 'generate images', 'create illustrations').\n"
        "- If the user says something like 'give image prompts' or 'what would the image look like', call `edit_image_prompt` or suggest prompts, but DO NOT call `generate_image` or `generate_image_for_index`.\n"
        "-If generation of images is asked, first do the image prompts."


        "Current story state:\n"
        f"• Pages: {len(story.pages)}\n"
        f"• Entities ({len(entities)}): {', '.join(e.name for e in entities) or '–'}\n"
        f"• Prompt: {story.prompt[:120]}{'…' if len(story.prompt) > 120 else ''}\n\n"
        f"• Images ({sum(1 for i in story.images if i)}):\n{images_summary}\n\n"


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

        "• edit_image_prompt – Edit the stored *prompt / size / quality* metadata of an existing page image (does NOT regenerate the image).\n\n"
            "- If the user asks to add or update image prompts, iterate over existing pages and call edit_image_prompt for each page index."
        "• generate_image_for_index – Use this when the user requests an image **for a specific page** (e.g. 'generate image for page 1', 'illustrate the second page'). Always prefer this over `generate_image` when the target is a specific story page."
        "• generate_image – Only use when the user wants a general illustration, not tied to a story page (e.g. 'draw the characters', 'make a cover')."

        "- If no tools make sense, just respond conversationally — but steer the user toward story creation.\n"
        "- If it’s story-related and no tool fits exactly, use edit_story_prompt.\n"
        "- Also look at histroy, to make a decision.\n"
        "- Only generate images if specifically asked.\n"
        "- Entities may include an image (b64_json) and a prompt.\n"
        "   - If both are provided, the prompt should describe visual *modifications* or *extras* to add to the image.\n"
        "   - If only a prompt is provided, it fully describes the entity.\n"

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
def _generate_image(
    *,
    prompt: str,
    entity_names: List[str],
    entities: List[StoryEntity],
    size: str = "1024x1024",
    quality: str = "low",
) -> str:                     # returns image_b64    image_files = [BytesIO(base64.b64decode(e.b64_json)) for e in used_entities if e.b64_json]
    
    used_entities = [e for e in entities if e.name in entity_names]
    image_files = [BytesIO(base64.b64decode(e.b64_json)) for e in used_entities if e.b64_json]
    
    text_prompts = []
    for e in entities:
        if not e.prompt:
            continue
        if e.b64_json:
            text_prompts.append(f"{e.name}: add the following to the image – {e.prompt}")
        else:
            text_prompts.append(f"{e.name}: {e.prompt}")

    if text_prompts:
        prompt += "\n\n" + "\n".join(text_prompts)

    if image_files:
        # Send as multipart/form-data
        files = []
        for i, f in enumerate(image_files):
            files.append(("image[]", ("entity_image_%d.png" % i, f, "image/png")))

        data = {
            "model": "gpt-image-1",
            "prompt": prompt,
            "quality": "low",
            "size": "1024x1024"
        }

        headers = {
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"
        }

        response = httpx.post(
            "https://api.openai.com/v1/images/edits",
            headers=headers,
            data=data,
            files=files,
            timeout=300
        )

        if response.status_code != 200:
            logger.error("Image generation failed: %s", response.text)
            raise HTTPException(502, "Image generation failed: " + response.text)

        image_b64 = response.json()["data"][0]["b64_json"]
        return image_b64

    elif text_prompts:
        # No images, generate from text only
        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="low",
        )
        return result.data[0].b64_json

    else:
        raise HTTPException(400, "No valid image files or prompts provided for image generation.")
    
def _generate_image_prompts(pages: List[str], entities=None) -> List[str]:
    ent_desc = "\n".join(f"- {e.name}: {e.prompt or 'image only'}"
                         for e in (entities or [])) or "(none)"
    sys = (
        "You are a children-book art director. "
        "For each passage you receive, answer with ONE vivid DALL·E prompt. "
        "Return a JSON array, same length, no markdown."
        "\n\nReusable entities:\n" + ent_desc
    )
    joined = "\n".join(f"{i+1}. {p}" for i, p in enumerate(pages))
    raw = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": sys},
                  {"role": "user",   "content": joined}],
        temperature=0.8,
        max_tokens=400,
    ).choices[0].message.content.strip()
    return _parse_json_or_lines(raw)        # still the tolerant splitter


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

    elif action == "edit_image_prompt":
        # The only job here is to update the stored metadata of ONE page-image.
        # Absolutely no story text or page list should change.

        idx      = data["page"]          # zero-based page index
        new_p    = data.get("prompt")    # may be None
        new_size = data.get("size")      # may be None
        new_q    = data.get("quality")   # may be None

        # Ensure the images list is long enough to hold this page slot
        if len(story.images) <= idx:
            story.images.extend([None] * (idx + 1 - len(story.images)))

        # If the slot is empty, create a minimal StoryImage shell first
        if story.images[idx] is None:
            story.images[idx] = StoryImage(index=idx)

        img_cfg = story.images[idx]

        # Apply only the fields the user provided
        if new_p is not None:
            img_cfg.prompt = new_p
        if new_size is not None:
            img_cfg.size = new_size
        if new_q is not None:
            img_cfg.quality = new_q


    elif action == "generate_image_for_index":
        page_idx      = data["page"]
        prompt        = data["prompt"]
        entity_names  = data.get("entity_names", [])
        size    = data.get("size", "1024x1024")
        quality = data.get("quality", "low")

        image_b64 = _generate_image(
                prompt=prompt,
                entity_names=entity_names,
                entities=entities,
                size=size,
                quality=quality
            )

        # result is `image_b64` (string) after you’ve called the image API
        img_cfg = StoryImage(
            index   = page_idx,
            prompt  = prompt,
            size    = size,
            quality = quality,
            image_b64 = image_b64,
        )

        # ensure we have a slot for this page
        if len(story.images) <= page_idx:
            story.images.extend([None] * (page_idx + 1 - len(story.images)))
        story.images[page_idx] = img_cfg

        # nothing for extras now
        return {}

    elif action == "generate_image":
        prompt = data["prompt"]
        entity_names = data.get("entity_names", [])

        image_b64 = _generate_image(
                prompt=prompt,
                entity_names=entity_names,
                entities=entities,
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

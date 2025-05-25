from app.features.story_chat.core.utils import (_parse_json_or_lines, _clean_json_fence, _normalize_indexes, _find_entity, _summarise_images)
from .schemas import (
    Story,
    StoryText,
    StoryEntity,
    ChatRequest,
    ChatResponse,
    Mode,
    StoryImage,
)
from typing import Dict, List, Optional, Tuple
import httpx
from ..config import (logger, client, MAX_HISTORY)
import base64
from io import BytesIO
from fastapi import FastAPI, HTTPException


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
        model="gpt-4o",
        messages=messages,
        max_tokens=400,
        temperature=0.7,
    )
    raw = resp.choices[0].message.content.strip()
    return _parse_json_or_lines(raw)

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

    elif action == "edit_story_settings":
        if story.settings is None:
            story.settings = StorySettings()
        if "tone"  in data: story.settings.tone  = data["tone"]
        if "pages" in data: story.settings.pages = data["pages"]

    elif action == "no_tool":
        # deliberate no-op
        pass

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
        if not 0 <= idx <= len(story.pages):
            logger.warning("Page index %d out of bounds for edit_text. Page count: %d", idx, len(story.pages))
            raise HTTPException(400, "Page index out of range.")
        logger.info("✏️ Editing text on page %d", idx)
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

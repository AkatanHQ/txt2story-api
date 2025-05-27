
import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from .schemas import (
    Story,
    StoryText,
    StoryEntity,
    ChatRequest,
    ChatResponse,
    Mode,
    StoryImage,
)
from ..config import (logger, client, MAX_HISTORY)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
from typing import List, Dict

def history_for_api(raw_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Return a filtered list of messages, excluding any with role 'tool'.
    All other messages are returned as-is.
    """
    return [msg for msg in raw_history if msg.get("role") != "tool"]
def _generate_story_pages(story, entities: Optional[List[StoryEntity]] = None) -> List[str]:
    """Call OpenAI to expand the prompt into *n* 1‑2 sentence pages."""
    prompt = story.prompt
    
    ent_desc = "\n".join(
        f"- {e.name}: {e.prompt or 'image only'}" for e in (entities or [])
    ) or "(none)"

    desired_pages = (
        story.settings.target_page_count
        if story.settings and story.settings.target_page_count
        else 5
    )

    tone_instruction = (
        f"Write the story in a **{story.settings.tone}** tone.\n\n"
        if story.settings and story.settings.tone
        else ""
    )

    logger.info("Generating pages for prompt with %d entit(y|ies)", len(entities or []))

    messages = [
        {
            "role": "system",
            "content": (
            "You are a creative and concise children's story writer. You will receive a short story prompt and a list of reusable story entities (characters or important elements)."

            "Your task is to continue the story by generating a JSON array of short story segments (1–2 sentences each). These will become the pages of a picture book."

             f"📌 Unless the user explicitly specifies otherwise, generate exactly **{desired_pages}** story pages.\n\n"

            "\n\nEach item in the array should:\n"
            f"- Tone: {tone_instruction}"
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


logger = logging.getLogger("storygpt")

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


def _normalize_indexes(story: Story) -> None:
    for i, pg in enumerate(story.pages):
        pg.index = i

def _find_entity(name: str, entities: List[StoryEntity]) -> Optional[StoryEntity]:
    return next((e for e in entities if e.name == name), None)

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


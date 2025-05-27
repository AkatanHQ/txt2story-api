
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


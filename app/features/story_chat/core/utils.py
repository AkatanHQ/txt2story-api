
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

def _strip_for_api(msg: Dict[str, str]) -> Dict[str, str]:
    """Return a copy of *msg* that contains only keys accepted by the
    OpenAI Chat API (currently: `role` and `content`)."""

    return {k: v for k, v in msg.items() if k in ("role", "content")}


def history_for_api(raw_history: List[dict]) -> List[dict]:
    """Produce a *clean* history list suitable for the ChatCompletion call.

    * Drops any message whose `role` is "tool" (these are our internal
      audit entries).
    * Strips everything except `role` and `content` from the remaining
      messages so that the payload conforms to the API schema.
    """

    return [_strip_for_api(m) for m in raw_history if m.get("role") != "tool"]


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


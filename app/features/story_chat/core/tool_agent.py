from __future__ import annotations

"""Shallow intent‑agent that decides which OpenAI tools to invoke for a
StoryGPT conversation *and* records which tools were chosen so we can
inspect them later or drive more advanced logic.

**Changelog (May 2025, revision 2)**
───────────────────────────────────
* **`role == "tool"` logging** – per API‑consistency feedback we now use
  `role == "tool"` (instead of the previous `tool_log`) for the metadata
  message that stores selected tool names.
* **`history_for_api()` helper** – new utility that returns a sanitised
  history list with all `tool` messages removed **and** only `role` /
  `content` keys preserved, ready to send to the OpenAI Chat API.
"""

import json
from typing import Dict, List, Optional, Tuple

from .schemas import Story, StoryEntity
from .tools import TOOLS
from app.features.story_chat.core.utils import (
    _parse_json_or_lines,
    _clean_json_fence,
    _normalize_indexes,
    _find_entity,
    _summarise_images,
)
from ..config import client, MAX_HISTORY
from .utils import logger



# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def _tool_agent(
    story: Story,
    entities: List[StoryEntity],
    history: List[dict],
) -> Tuple[List[Tuple[str, dict]], Optional[str]]:
    """Decide which tool(s) to invoke **and** persist a log of those tools
    inside *history* (for downstream analytics / workflows).

    After every assistant turn we append one message of the form::

        {"role": "tool", "content": "[\"edit_text\", \"generate_image\"]"}

    When we prepare the payload for the next OpenAI call these messages
    are silently filtered out via :pyfunc:`history_for_api` so that the
    API never sees unsupported roles.
    """
    # ── 2. Build the system prompt with live story context ───────────────
    images_summary = _summarise_images(story.images)
    target_page_count = (
        story.settings.target_page_count
        if story.settings and story.settings.target_page_count
        else 5)
    
    target_page_count_instruction = f"- target_page_count: {target_page_count}"

    tone_instruction = (
        f"- tone: {story.settings.tone} \\n"
        if story.settings and story.settings.tone
        else ""
    )


    SYSTEM_PROMPT = (
        "You are StoryGPT‑DECIDER.  **Always** reply with *at least one* OpenAI tool‑call.\n"
        "If the user is only chatting, emit the `no_tool` function.\n"
        "Never produce natural‑language output yourself.\n\n"
        "Use the language of the user."

        "### BOOTSTRAP RULE\n"
        "• If you choose `edit_story_prompt` and the story has no pages, entities, or images:\n"
        "– You MUST also include:\n"
        "    • One `edit_story_title` call to set an initial title.\n"
        "    • One `edit_all` call to create full page content for the story. \n"
        "    • One `update_entity` call for **each entity** that should appear in the story.\n"
        "    • One `edit_image_prompt` call for **each story page**, with the appropriate `index`.\n"

        "### DECISION FLOW\n"
        "• If the user intends to use tools, respond ONLY with tool calls (OpenAI tool format). No natural language.\n"
        "• You may return MULTIPLE tool calls in a single response.\n"
        "• Consider chat history, but prioritise the most recent message.\n"
        "• If the number of pages is greater than `target_page_count`, and the user is asking to reduce or regenerate content, add a `truncate_to_page_count` call to remove the extra pages and images.\n\n"

        "### IMAGE RULES\n"
        "• Only generate images when clearly asked (e.g. 'generate image', 'create illustrations').\n"
        "• If user asks for 'image prompts' or visual descriptions, use `edit_image_prompt`, NOT `generate_image`.\n"
        "• Prefer `generate_image_for_index` over `generate_image` when the target is a specific page.\n\n"

        "### STORY CONTEXT\n"
        f"• Prompt: {story.prompt}\n"
        f"• Title: {story.title or '–'}\n"
        f"• Genre: {story.genre or '–'}\n"
        f"• Keywords: {', '.join(story.keywords) if story.keywords else '–'}\n"
        "• Story Settings:\n"
        f"   {tone_instruction}"
        f"   {target_page_count_instruction}"
        f"• Story: {story.pages}\n"
        f"• Entities ({len(entities)}): {', '.join(e.name for e in entities) or '–'}\n"
        f"• Image Prompts ({sum(1 for i in story.images if i)}):\n{images_summary}\n\n"



        "### TEXT FORMAT RULES (applies to `edit_all`, `edit_text`, `insert_page`, etc.)\\n"
        "• Use a descriptive narrative style (not poetry, not dialogue-only).\\n"
        "• Keep each page to 1–2 short sentences or one concise paragraph. Unless stated otherwise\\n"
        "• Text should flow logically and naturally from previous pages (if any).\\n"
        "• Integrate the story prompt and listed entities where appropriate.\\n"
        "• Avoid formatting artifacts:\\n"
        "  – Do NOT include labels like \\\"Page 1:\\\"\\n"
        "  – Do NOT use markdown, quotes, or code blocks\\n"

        "### TOOLS\n"
        "• edit_story_prompt – Replace the overall story prompt.\n\n"
        "• edit_story_title – Update the story’s title.\n"
        "• edit_story_genre – Update the genre (e.g. 'Fantasy').\n"
        "• edit_story_keywords – Replace the list of keywords (array of strings).\n\n"
        "• edit_target_page_count – Set how many pages the story should have (integer)\n"
        "• truncate_to_page_count – Trim the story’s pages and images to match the current `target_page_count`.\n"
        "• edit_story_tone – Change the overall tone (string, e.g. 'spooky')\n\n"
        "• edit_text – Replace a specific page.\n"
        "• edit_all – Replace all pages.\n"
        "• insert_page – Add a new page.\n"
        "• delete_page – Remove a page.\n"
        "• move_page – Reorder pages.\n\n"
        "• add_entity – Create a new character or entity.\n"
        "• update_entity – Change name, image, or prompt. (Use empty string to clear prompt.)\n"
        "• delete_entity – Remove an entity.\n\n"
        "• edit_image_prompt – Modify image metadata (prompt). Does NOT regenerate.\n"
        "• generate_image_for_index – Generate image for a specific story page.\n"
        "• generate_image – General‑purpose image (e.g. character portrait, cover art).\n\n"

        "### ENTITY IMAGE LOGIC\n"
        "• Entities may have:\n"
        "  – Just a prompt → fully describes the entity.\n"
        "  – An image + prompt → prompt describes modifications or extra details.\n\n"

        "### EXAMPLE\n"
        "User: Create two characters and write a story about them.\n"
        "Tool calls:\n"
        "1. add_entity → name: Valandor, prompt: A brave warrior with golden armour.\n"
        "2. add_entity → name: Lyra, prompt: A healer in silver robes.\n"
        "3. edit_story_prompt → new_prompt: A tale of Valandor and Lyra on a quest to save their world.\n"
        "\n"
        "User: Rewrite the story to be 3 pages instead of 5.\n"
        "Tool calls:\n"
        "1. edit_target_page_count → target_page_count: 3\n"
        "2. edit_all → new_texts: [ ...3 new pages... ]\n"
        "3. truncate_to_page_count\n"

    )

    # ── 3. Prepare messages for the model ────────────────────────────────
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    # ── 4. Call the model and parse tool calls ───────────────────────────
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            tools=TOOLS,
            tool_choice="required",
        )

        msg = resp.choices[0].message
        tool_calls: List[Tuple[str, dict]] = []
        called_tool_names: List[str] = []

        if msg.tool_calls:
            for call in msg.tool_calls:
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append((call.function.name, args))
                called_tool_names.append(call.function.name)

        else:
            tool_calls = [("no_tool", {})]
            called_tool_names.append("no_tool")

        return tool_calls

    except Exception as e:
        logger.error(f"Error deciding which tool: {e}", exc_info=True)
        return [], "I couldn't handle this request - can you please specify the request?"

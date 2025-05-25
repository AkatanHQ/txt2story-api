

import json
from typing import Dict, List, Optional, Tuple

from .schemas import (
    Story,
    StoryEntity,
)
from .tools import TOOLS

from app.features.story_chat.core.utils import (_parse_json_or_lines, _clean_json_fence, _normalize_indexes, _find_entity, _summarise_images)
from ..config import (client, MAX_HISTORY)
from .utils import logger

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
        "You are StoryGPT — a creative assistant that decides whether the user is chatting or wants to use a tool.\n\n"

        "### DECISION FLOW\n"
        "1. If the user is chatting or asking a question, respond in natural language.\n"
        "2. If the user intends to use tools, respond ONLY with tool calls (OpenAI tool format). No natural language.\n"
        "3. You may return MULTIPLE tool calls in a single response.\n"
        "4. Consider chat history, but prioritize the most recent message.\n"
        "5. If uncertain, respond conversationally and guide the user toward story creation.\n\n"

        "### IMAGE RULES\n"
        "• Only generate images when clearly asked (e.g. 'generate image', 'create illustrations').\n"
        "• If user asks for 'image prompts' or visual descriptions, use `edit_image_prompt`, NOT `generate_image`.\n"
        "• Prefer `generate_image_for_index` over `generate_image` when the target is a specific page.\n\n"

        "### STORY CONTEXT\n"
        f"• Pages: {len(story.pages)}\n"
        f"• Story: {story.pages}\n"
        f"• Entities ({len(entities)}): {', '.join(e.name for e in entities) or '–'}\n"
        f"• Prompt: {story.prompt[:120]}{'…' if len(story.prompt) > 120 else ''}\n"
        f"• Image Prompts ({sum(1 for i in story.images if i)}):\n{images_summary}\n\n"

        "### TOOLS\n"
        "• edit_story_prompt – Replace the overall story prompt.\n\n"

        "• edit_text – Replace a specific page.\n"
        "• edit_all – Replace all pages.\n"
        "• insert_page – Add a new page.\n"
        "• delete_page – Remove a page.\n"
        "• move_page – Reorder pages.\n\n"

        "• add_entity – Create a new character or entity.\n"
        "• update_entity – Change name, image, or prompt. (Use empty string to clear prompt.)\n"
        "• delete_entity – Remove an entity.\n\n"

        "• edit_image_prompt – Modify image metadata (prompt, size, quality). Does NOT regenerate.\n"
        "• generate_image_for_index – Generate image for a specific story page.\n"
        "• generate_image – General-purpose image (e.g. character portrait, cover art).\n\n"

        "### ENTITY IMAGE LOGIC\n"
        "• Entities may have:\n"
        "  – Just a prompt → fully describes the entity.\n"
        "  – An image + prompt → prompt describes modifications or extra details.\n\n"

        "### EXAMPLE\n"
        "User: Create two characters and write a story about them.\n"
        "Tool calls:\n"
        "1. add_entity → name: Valandor, prompt: A brave warrior with golden armor.\n"
        "2. add_entity → name: Lyra, prompt: A healer in silver robes.\n"
        "3. edit_story_prompt → new_prompt: A tale of Valandor and Lyra on a quest to save their world.\n"
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto")
        

        msg = resp.choices[0].message

        tool_calls: List[Tuple[str, dict]] = []
        assistant_output: Optional[str] = ""

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
    except Exception as e:
            logger.error(f"Error deciding which tool: {e}", exc_info=True)
            return [], "I couldn't handle this request - can you please specify the request?"

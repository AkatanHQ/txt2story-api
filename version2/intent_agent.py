

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
from openai import OpenAIError
from io import BytesIO
import base64
from utils import (_parse_json_or_lines, _clean_json_fence, _normalize_indexes, _find_entity, _summarise_images)
from config import (client, MAX_HISTORY)


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
        "If you don't know what to do, reply in natural language."
        "Always consider history as well, but focus on the most recent questions."
        "- Never generate images unless the user clearly says to (e.g. 'generate images', 'create illustrations').\n"
        "- If the user says something like 'give image prompts' or 'what would the image look like', call `edit_image_prompt` or suggest prompts, but DO NOT call `generate_image` or `generate_image_for_index`.\n"
        "-If generation of images is asked, first do the image prompts."


        "Current story state:\n"
        f"• Pages: {len(story.pages)}\n"
        f"• Entities ({len(entities)}): {', '.join(e.name for e in entities) or '–'}\n"
        f"• Prompt: {story.prompt[:120]}{'…' if len(story.prompt) > 120 else ''}\n\n"
        f"• Images Prompts({sum(1 for i in story.images if i)}):\n{images_summary}\n\n"

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

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
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

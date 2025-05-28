# app/features/story_chat/core/reply_agent.py
from openai import OpenAI
from .schemas import Story, StoryEntity, StoryText
from ..config import client, MAX_HISTORY
from app.features.story_chat.core.utils import (_parse_json_or_lines, _clean_json_fence, _normalize_indexes, _find_entity, _summarise_images)
import json

def reply_agent(
    user_msg: str,
    story_before: Story,
    story_after: Story,
    entities: list[StoryEntity],
    history: list[dict],
    tool_calls: list[tuple[str, dict]] | None = None,
) -> str:
    """Generate the assistant’s human-language answer after tools ran."""
    history = history[-MAX_HISTORY:]
    images_summary = _summarise_images(story_after.images)

    recent_tool_note = ""
    if tool_calls:
        lines = []
        for name, args in tool_calls:
            if args:
                lines.append(f"• {name} → {json.dumps(args, ensure_ascii=False)}")
            else:
                lines.append(f"• {name}")
        recent_tool_note = "### TOOLS JUST EXECUTED\n" + "\n".join(lines) + "\n\n"

    # Helper to make page diffing readable
    def summarise_story(pages: list[StoryText]) -> str:
        return "\n".join(f"{i + 1}. {p.text}" for i, p in enumerate(pages))

    messages = (
        [{
            "role": "system",
            "content": (
                "You are StoryGPT – a friendly assistant helping the user craft an illustrated story.\n"
                "First give a very concise summary of what changed.\n"
                "Then explain how it affects the story, and guide the user toward the next helpful step.\n"
                "You may reference the prompt, tone, target page count, or recent changes to suggest improvements or additions.\n\n"

                f"{recent_tool_note}"
                "### STORY CONTEXT AFTER CHANGES\n"
                f"• Prompt: {story_after.prompt}\n"
                f"• Title: {story_after.title or '–'}\n"
                f"• Genre: {story_after.genre or '–'}\n"
                f"• Keywords: {', '.join(story_after.keywords) if story_after.keywords else '–'}\n"
                f"• Tone: {story_after.settings.tone if story_after.settings and story_after.settings.tone else '–'}\n"
                f"• Target page count: {story_after.settings.target_page_count if story_after.settings and story_after.settings.target_page_count else '–'}\n"
                f"• Entities: {', '.join(e.name for e in entities) or '–'}\n"
                f"• Image Prompts ({sum(1 for i in story_after.images if i)}):\n{images_summary}\n\n"
                "### STORY TEXT BEFORE CHANGES\n"
                f"{summarise_story(story_before.pages)}\n\n"
                "### STORY TEXT AFTER CHANGES\n"
                f"{summarise_story(story_after.pages)}\n\n"
            )
        }] + history
    )

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=500,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


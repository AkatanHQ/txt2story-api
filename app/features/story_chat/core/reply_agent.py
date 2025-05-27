# app/features/story_chat/core/reply_agent.py
from openai import OpenAI
from .schemas import Story, StoryEntity
from ..config import client, MAX_HISTORY
from app.features.story_chat.core.utils import (_parse_json_or_lines, _clean_json_fence, _normalize_indexes, _find_entity, _summarise_images)
import json

def reply_agent(user_msg: str,
                story: Story,
                entities: list[StoryEntity],
                history: list[dict],
                tool_calls: list[tuple[str, dict]] | None = None) -> str:
    
    """Generate the assistant’s human-language answer after tools ran."""
    history = history[-MAX_HISTORY:]
    images_summary = _summarise_images(story.images)    

     # ── transient system note describing what just happened ─────────────
    recent_tool_note = ""
    if tool_calls:
        lines = []
        for name, args in tool_calls:
            if args:
                lines.append(f"• {name} → {json.dumps(args, ensure_ascii=False)}")
            else:
                lines.append(f"• {name}")
        recent_tool_note = "### TOOLS JUST EXECUTED\n" + "\n".join(lines) + "\n\n"

    messages = (
        [{"role": "system",
          "content": (
            "You are StoryGPT – a friendly assistant helping the user craft an illustrated story.\n"
            "Respond conversationally and helpfully in plain language.  "
            "The current story context is available for reference.\n\n"
            f"{recent_tool_note}"        # 🆕 only visible on this turn
           "### STORY CONTEXT\n"
            f"• Prompt: {story.prompt}\n"
            "• Story Settings:\n"
            f"   – tone: {story.settings.tone if story.settings and story.settings.tone else '–'}\n"
            f"   – target_page_count: {story.settings.target_page_count if story.settings and story.settings.target_page_count else '–'}\n"
            f"• Story: {story.pages}\n"
            f"• Entities ({len(entities)}): {', '.join(e.name for e in entities) or '–'}\n"
            f"• Image Prompts ({sum(1 for i in story.images if i)}):\n{images_summary}\n\n"
          )}]
        + history
    )

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=400,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()

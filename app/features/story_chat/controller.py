# app/features/story_chat/controller.py

from fastapi import HTTPException
from openai import OpenAIError
from typing import List

from .core.schemas import ChatRequest, ChatResponse, Story, StoryEntity, Mode
from .core.tool_agent import _tool_agent
from .core.actions import _apply_tool
from .config import logger
from .core.reply_agent  import reply_agent
from app.features.story_chat.core.utils import ( history_for_api )

async def handle_chat(req: ChatRequest) -> ChatResponse:
    story: Story = req.story or Story(prompt="")
    entities: List[StoryEntity] = list(req.entities or [])
    history_with_tools: List[dict] = list(req.history or [])

    history = history_for_api(history_with_tools)

    try:
        tool_calls = _tool_agent(req.user_input, story, entities, history)
    except OpenAIError as e:
        logger.error("OpenAI call failed: %s", str(e))
        raise HTTPException(502, f"OpenAI error: {str(e)}")

    executed_tools: List[Mode] = []
    extras = {}

    for tool, args in tool_calls:          # tool_calls is never empty now
        logger.info(">> Executing tool: %s %s", tool, args)
        action_result = _apply_tool(tool, args, story, entities)
        executed_tools.append(Mode(tool))
        extras.update(action_result)

    # ───────────────────────────────────────────
    # 2️⃣  HUMAN-LANGUAGE ANSWER
    # ───────────────────────────────────────────
    assistant_output = reply_agent(req.user_input, story, entities, history, tool_calls)
    history.append({"role": "assistant", "content": assistant_output})

    print("Returning response with mode:", executed_tools)
    return ChatResponse(
        modes=executed_tools,
        assistant_output=assistant_output,
        story=story,
        entities=entities,
        history=history,
        image_b64=extras.get("image_b64"),
        settings        = story.settings,
    )

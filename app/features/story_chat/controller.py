# app/features/story_chat/controller.py

from fastapi import HTTPException
from openai import OpenAIError
from typing import List

from .core.schemas import ChatRequest, ChatResponse, Story, StoryEntity, Mode
from .core.intent_agent import _intent_agent
from .core.actions import _apply_action
from .config import logger


async def handle_chat(req: ChatRequest) -> ChatResponse:
    story: Story = req.story or Story(prompt="")
    entities: List[StoryEntity] = list(req.entities or [])
    history: List[dict] = list(req.history or [])

    print(story)
    try:
        tool_calls, assistant_output = _intent_agent(
            req.user_input, story, entities, history
        )
    except OpenAIError as e:
        logger.error("OpenAI call failed: %s", str(e))
        raise HTTPException(502, f"OpenAI error: {str(e)}")

    executed_modes: List[Mode] = []
    extras = {}

    if tool_calls:
        for action, args in tool_calls:
            logger.info(">> Executing tool: %s %s", action, args)
            action_result = _apply_action(action, args, story, entities)
            executed_modes.append(Mode(action))
            extras.update(action_result)
    else:
        executed_modes.append(Mode.CONTINUE_CHAT)

    print("Returning response with mode:", executed_modes)
    return ChatResponse(
        modes=executed_modes,
        assistant_output=assistant_output,
        story=story,
        entities=entities,
        history=history,
        image_b64=extras.get("image_b64")
    )

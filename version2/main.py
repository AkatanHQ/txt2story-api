from __future__ import annotations
"""
StoryGPT Backend – FastAPI + OpenAI 2.2.1 (stateless)
----------------------------------------------------

This version refactors the `/chat` endpoint to be fully **stateless** per request
and async‑friendly, matching the signature the frontend now expects.
----------------------------------------------------

Information:
Inputs
- Story holds the generate structure,
- storytext holds the text of 1 page of the story
- storyimage holds the prompt,size and quality of 1 page of the story
- Entities are given by the user and have a name (as id), possibly an image and a prompt

Dependencies/Relations
- The entities are input for when generating a new story, such that the AI know what entities to use in the story
- When generating an image, the input-prompt for AI will be: the StoryImage + the entities that are mentioned in the prompt 
  - 1 entity includes an image + prompt, and by referencing it correctly in the input for the ai
- When generating a new story, the input-prompt for AI will be: the prompt + the entities, such that the AI knows how to use and who to use in the story.
- In the ImagePrompt, if a entitity is needed as input, it will reference it by the name/id
"""

import os
from typing import Dict, List, Optional, Tuple
import httpx

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
from config import (logger, client, MAX_HISTORY)
from intent_agent import _intent_agent
from actions import (_apply_action)

# ────────────────────────────
# ░░ API endpoint ░░
# ────────────────────────────

app = FastAPI(title="StoryGPT Backend", version="2.2.1")

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    print("\n======= NEW /chat REQUEST =======")
    print("User input:", req.user_input)

    story: Story = req.story or Story(prompt="")
    entities: List[StoryEntity] = list(req.entities or [])
    history: List[dict] = list(req.history or [])

    try:
        tool_calls, assistant_output = _intent_agent(
            req.user_input, story, entities, history
        )
    except OpenAIError as e:
        logger.error("OpenAI call failed: %s", str(e))
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI error: {str(e)}"
        )

    mode = Mode.CONTINUE_CHAT.value
    executed_modes: List[Mode] = []

    extras = {}
    if tool_calls:
        for action, args in tool_calls:
            print(">> Executing tool:", action, args)
            action_result = _apply_action(action, args, story, entities)
            executed_modes.append(Mode(action))
            extras.update(action_result)
    else:
        executed_modes.append(Mode.CONTINUE_CHAT)

    print("Returning response with mode:", mode)
    return ChatResponse(
        modes=executed_modes,
        assistant_output=assistant_output,
        story=story,
        entities=entities,
        history=history,
        image_b64=extras.get("image_b64")
    )

# uvicorn main2:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

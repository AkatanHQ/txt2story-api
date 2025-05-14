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
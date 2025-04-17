from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from app.utils.logger import logger
from app.services.text_generator import TextGenerator



class StoryChatManager:
    def __init__(self):
        self.generator = TextGenerator()
        self.story_state = {
            "title": None,
            "entities": [],
            "scenes": [],
            "scenario": None,
        }

    def process_message(self, message: str):
        prompt = f"""
        You are a friendly assistant helping a user co-create a story.

        If the user wants to:
        - Start a story → extract theme and scenario, call generate_scenes
        - Add characters or ideas → call extract_extra_entities_from_story
        - Modify story elements → describe what needs to change
        - Stop talking about the story → gently bring them back

        Always return a JSON object:
        {{
            "reply": "<chat message to user>",
            "action": "<action_to_take or null>",
            "params": {{ "scenario": "...", "entities": [...] }}
        }}

        Current state:
        {json.dumps(self.story_state, indent=2)}

        User said: "{message}"
        """

        completion = self.generator.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You're a story collaboration assistant."},
                {"role": "user", "content": prompt},
            ]
        )

        result = json.loads(completion.choices[0].message.content)
        reply = result.get("reply")
        action = result.get("action")
        params = result.get("params", {})

        if action == "generate_scenes":
            self.story_state["scenario"] = params.get("scenario")
            self.story_state["entities"] = params.get("entities", [])
            self.story_state["scenes"] = self.generator.generate_scenes(
                entities=self.story_state["entities"],
                number_of_pages=5,
                scenario=self.story_state["scenario"]
            )

        elif action == "extract_entities":
            new_entities = self.generator.extract_extra_entities_from_story(
                scenes=self.story_state["scenes"],
                entities=self.story_state["entities"]
            )
            self.story_state["entities"].extend(new_entities)

        elif action == "generate_metadata":
            self.story_state["metadata"] = self.generator.generate_metadata(
                self.story_state["scenes"]
            )

        # Extend: update scene, remove character, regenerate title, etc.

        return {
            "chat_reply": reply,
            "story_state": self.story_state
        }

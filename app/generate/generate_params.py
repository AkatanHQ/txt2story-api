import re
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# Load environment variables from a .env file
load_dotenv()

class ParamTextGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_title(self, scenes):
        prompt_template = """
        Given the following scenes and dialogues, generate a suitable title for the story. Make it short.

        Scenes:
        {scenes}

        Return only the title.
        """

        # Format the prompt by adding the scenes into the template
        formatted_prompt = prompt_template.format(scenes=scenes)

        # Interacting with the model using function calling
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": formatted_prompt},
                ],
            functions=[
                {
                    "name": "generate_title",
                    "description": "Generate a suitable title for the story",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "The generated title for the story"
                            }
                        },
                        "required": ["title"]
                    }
                }
            ],
            function_call={"name": "generate_title"}
        )
        # Extract the content from the API response
        result = json.loads(completion.choices[0].message.function_call.arguments)["title"]
        return result

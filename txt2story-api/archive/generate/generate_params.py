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

    def generate_character_description(self, characters, short_description=False):
        prompt_template = """
        Given the following character details, generate a vivid and detailed physical description of the character, focusing solely on their appearance, clothing, and notable features.

        Character Name: {name}
        Appearance: {appearance}

        Include specific details on height, body build, hairstyle, facial features, clothing, and posture. Exclude implied character traits, behavioral cues, and non-essential details. Aim for a description that directly informs the visual representation.
        """

        # Adjust the prompt for a short description if requested
        if short_description:
            prompt_template += "\nOnly add the most important. Ensure the description is no more than 200 characters."

        descriptions = []
        
        for character in characters:
            # Format the prompt for each character
            formatted_prompt = prompt_template.format(
                name=character['name'],
                appearance=character['appearance']
            )
            
            # Interacting with the model
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a creative assistant for character development."},
                    {"role": "user", "content": formatted_prompt},
                ],
                functions=[
                    {
                        "name": "generate_character_description",
                        "description": "Generate a detailed character description",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "description": {
                                    "type": "string",
                                    "description": "The detailed description of the character"
                                }
                            },
                            "required": ["description"]
                        }
                    }
                ],
                function_call={"name": "generate_character_description"}
            )
            
            # Extract the description from the API response
            description = json.loads(completion.choices[0].message.function_call.arguments)["description"]

            # Limit the description to 200 characters if short_description is True
            if short_description and len(description) > 200:
                description = description[:200].rstrip() + '...'  # Truncate and add ellipsis if necessary

            # Append the result to the list of descriptions
            descriptions.append({
                "name": character['name'],
                "description": description
            })
        
        return descriptions

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

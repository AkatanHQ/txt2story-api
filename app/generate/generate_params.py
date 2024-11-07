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
    
    def generate_story_text(self, characters, language, number_of_pages, description):
        """
        Generates a well-structured story based on the provided character information, language, number of pages, 
        and description, and returns it in a structured JSON format with panels.

        Parameters:
            characters (list): List of character details with 'name' and 'appearance'.
            language (str): The language in which the story should be written.
            number_of_pages (int): The target number of pages for the story.
            description (str): A brief description or storyline for the story.

        Returns:
            dict: A JSON object with a structured format containing the story panels.
        """

        # Construct the character descriptions part of the prompt
        character_descriptions = "\n".join([
            f"- {character['name']}: {character['appearance']}"
            for character in characters
        ])

        # Construct the structured story prompt
        formatted_prompt = f"""
        Write a story in {language} with approximately {number_of_pages} pages. The story should feature the following characters and follow the given storyline. The story structure should include:

        1. **Introduction**: Set the scene, introduce the main characters, and describe the setting.
        2. **Rising Action**: Present the main challenge or quest the characters face.
        3. **Climax**: The most intense part of the story where the characters face their biggest challenge.
        4. **Resolution**: Wrap up the quest, show character growth, or reveal the outcome.

        **Characters:**
        {character_descriptions}

        **Storyline Description:**
        {description}

        Structure the story in a series of narrative panels, where each panel represents a scene or important moment in the story. Each panel should include an index and a concise text that captures the moment within this structure.
        """

        # Interacting with the model using the function call format
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a creative assistant for storytelling."},
                {"role": "user", "content": formatted_prompt},
            ],
            functions=[
                {
                    "name": "generate_story_panels",
                    "description": "Generate a detailed story divided into panels with index and text",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "panels": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "index": {"type": "integer"},
                                        "text": {"type": "string"}
                                    },
                                    "required": ["index", "text"]
                                }
                            }
                        },
                        "required": ["panels"]
                    }
                }
            ],
            function_call={"name": "generate_story_panels"}
        )

        # Extract and return the story panels in JSON format
        story_panels = json.loads(completion.choices[0].message.function_call.arguments)["panels"]
        return story_panels

    def extract_characters_from_story(self, story_panels):
        """
        Extracts characters from a story based on mentions in story panels and returns a list of characters with their appearances.

        Parameters:
            story_panels (list): List of dictionaries with 'index' and 'text' for each story panel.

        Returns:
            list: A list of characters with their 'name' and 'appearance' fields.
        """

        # Initialize an empty list to store characters who appear in the story
        appearing_characters = []

        # Create the prompt for extracting character names and descriptions
        formatted_prompt = f"""
        Analyze the following story panels to identify all unique characters mentioned. For each character, return their name and any appearance or descriptive information given in the story.

        **Story Panels:**
        {story_panels}

        Return the characters in a JSON format, where each character includes 'name' and 'appearance' fields. Only include unique characters.
        """

        # Interacting with the model
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a creative assistant for character extraction."},
                {"role": "user", "content": formatted_prompt},
            ],
            functions=[
                {
                    "name": "extract_characters_from_story",
                    "description": "Extract characters from a story",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "characters": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "The name of the character"
                                        },
                                        "appearance": {
                                            "type": "string",
                                            "description": "The appearance or description of the character"
                                        }
                                    },
                                    "required": ["name", "appearance"]
                                }
                            }
                        },
                        "required": ["characters"]
                    }
                }
            ],
            function_call={"name": "extract_characters_from_story"}
        )

        # Extract the character list from the API response
        appearing_characters = json.loads(completion.choices[0].message.function_call.arguments)["characters"]

        return appearing_characters

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

# Example Usage
if __name__ == "__main__":
    # Define example story panels
    story_panels = [
        {"index": 0, "text": "In a sunny meadow, Benny the Bunny wakes up and stretches his little paws."},
        {"index": 1, "text": "Benny hops along the path, greeting the birds and butterflies."},
        {"index": 2, "text": "As Benny hops deeper into the woods, he meets a shy squirrel named Nibbles."},
        {"index": 3, "text": "Finally, Benny finds the big oak tree and, behind it, the clover patch!"},
        {"index": 4, "text": "With a heart full of joy, Benny hops home, carrying a small clover for each of his friends."}
    ]

    # Initialize the generator
    generator = ParamTextGenerator()
    
    # Extract characters from the story panels
    character_list = generator.extract_characters_from_story(story_panels)

    # Print the detected characters in JSON format
    print("Detected Characters:\n")
    print(json.dumps(character_list, indent=2))
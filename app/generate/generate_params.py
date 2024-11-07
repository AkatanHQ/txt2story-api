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
    
    def generate_story_text(self, entities, language, number_of_pages, description):
        """
        Generates a well-structured story based on the provided entity information, language, number of pages, 
        and description, and returns it in a structured JSON format with panels.

        Parameters:
            entities (list): List of entity details with 'name' and 'appearance'.
            language (str): The language in which the story should be written.
            number_of_pages (int): The target number of pages for the story.
            description (str): A brief description or storyline for the story.

        Returns:
            dict: A JSON object with a structured format containing the story panels.
        """

        # Construct the structured story prompt
        formatted_prompt = f"""
        Write a story in {language} with approximately {number_of_pages} pages. The story should feature the following entities and follow the given storyline. The story structure should include:

        1. **Introduction**: Set the scene, introduce the main entities, and describe the setting.
        2. **Rising Action**: Present the main challenge or quest the entities face.
        3. **Climax**: The most intense part of the story where the entities face their biggest challenge.
        4. **Resolution**: Wrap up the quest, show entity growth, or reveal the outcome.

        **entities:**
        {entities}

        **Storyline Description:**
        {description}

        - Structure the story in a series of narrative panels, where each panel represents a scene or important moment in the story.
        - Each panel should include an index, starting with 0, a concise text that captures the moment within this structure, and a Image prompt
        - Image prompts descriptions are stand alones, and don't know anything about the others
        - Image prompts should describe what a entity is doing (referencing by name) and some background-scenery details
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
                    "description": "Generate a detailed story divided into panels with index, text",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "panels": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "index": {"type": "integer"},
                                        "text": {"type": "string"},
                                        "image_prompt": {"type": "string"}

                                    },
                                    "required": ["index", "text", "image_prompt"]
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

    def extract_entities_from_story(self, story_panels):
        """
        Extracts entities from a story based on mentions in story panels and returns a list of entities with their appearances.

        Parameters:
            story_panels (list): List of dictionaries with 'index' and 'text' for each story panel.

        Returns:
            list: A list of entities with their 'name' and 'appearance' fields.
        """

        # Initialize an empty list to store entities who appear in the story
        appearing_entities = []

        # Create the prompt for extracting entity names and descriptions
        formatted_prompt = f"""
        Analyze the following story panels to identify all unique entity mentioned. For each entity, return their name/reference and any appearance or descriptive information given in the story.

        **Story Panels:**
        {story_panels}

        Return the entities in a JSON format, where each entity includes 'name' and 'appearance' fields. Only include unique entities that are mentioned at least twice in the story.
        """

        # Interacting with the model
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a creative assistant for entity extraction."},
                {"role": "user", "content": formatted_prompt},
            ],
            functions=[
                {
                    "name": "extract_entities_from_story",
                    "description": "Extract entities from a story",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entities": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "The name of the entity"
                                        },
                                        "appearance": {
                                            "type": "string",
                                            "description": "The appearance or description of the entity"
                                        }
                                    },
                                    "required": ["name", "appearance"]
                                }
                            }
                        },
                        "required": ["entities"]
                    }
                }
            ],
            function_call={"name": "extract_entities_from_story"}
        )

        # Extract the entity list from the API response
        appearing_entities = json.loads(completion.choices[0].message.function_call.arguments)["entities"]

        return appearing_entities

    def generate_entity_description(self, entity, short_description=False):
        """
        Generates a description for a single entity based on provided details.
        
        Parameters:
            entity (dict): Dictionary with entity's name and appearance.
            short_description (bool): If True, generates a shorter description.
            
        Returns:
            dict: Dictionary with the entity's name and generated detailed appearance.
        """
        # Define the prompt template
        prompt_template = """
        Given the following entity details, generate a vivid and detailed physical description of the entity, focusing solely on their appearance, clothing, and notable features.

        Entity Name: {name}
        Appearance: {appearance}

        If human/living creature, Include specific details on height, body build, hairstyle, facial features, clothing, and posture. Exclude implied entity traits, behavioral cues, and non-essential details. Aim for a description that directly informs the visual representation.
        """

        # Adjust the prompt for a short description if requested
        if short_description:
            prompt_template += "\nOnly add the most important (color included). Ensure the description is no more than 200 entities."

        # Format the prompt with entity information
        formatted_prompt = prompt_template.format(
            name=entity['name'],
            appearance=entity['appearance']
        )

        # Interact with the model to generate the description
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a creative assistant for entity development."},
                {"role": "user", "content": formatted_prompt},
            ],
            functions=[
                {
                    "name": "generate_entity_description",
                    "description": "Generate a detailed entity description",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "detailed_appearance": {
                                "type": "string",
                                "description": "The detailed description of the entity"
                            }
                        },
                        "required": ["detailed_appearance"]
                    }
                }
            ],
            function_call={"name": "generate_entity_description"}
        )

        # Extract the description from the API response
        detailed_appearance = json.loads(completion.choices[0].message.function_call.arguments)["detailed_appearance"]

        # Return the result as a dictionary
        return detailed_appearance

    def generate_entity_descriptions(self, entities, short_description=False):
        """
        Generates descriptions for a list of entities.
        
        Parameters:
            entities (list): List of entity dictionaries with name and appearance.
            short_description (bool): If True, generates shorter descriptions.
            
        Returns:
            list: List of dictionaries with each entity's name and generated detailed appearance.
        """
        descriptions = []

        for entity in entities:
            # Generate description for each entity
            detailed_appearance = self.generate_entity_description(entity, short_description)
            entity["detailed_appearance"] = detailed_appearance
            descriptions.append(entity)

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
    # Define entity details
    entities = [
        {
            "id": 1,
            "name": "Elara",
            "appearance": "Tall, lean, with short black hair and piercing green eyes. Wears a dark cloak over leather armor."
        },
        {
            "id": 2,
            "name": "Ronan",
            "appearance": "Broad-shouldered with a rugged beard and scar over his left brow. Dresses in a simple tunic and chainmail."
        }
    ]

    # Define other parameters
    language = "English"
    number_of_pages = 5
    description = "Elara and Ronan embark on a quest to retrieve a powerful relic to protect their kingdom. They must work together, facing challenges that test their courage, trust, and friendship."

    # Initialize the generator and generate the story
    generator = ParamTextGenerator()
    story_panels = generator.generate_story_text(entities, language, number_of_pages, description)
    entities = generator.extract_entities_from_story(story_panels)
    detailed_entities = generator.generate_entity_descriptions(entities)
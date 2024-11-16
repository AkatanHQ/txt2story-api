import re
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# Load environment variables from a .env file
load_dotenv()

class TextGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def generate_story_text(self, entities, language, number_of_pages, scenario):
        """
        Generates a well-structured story based on the provided entity information, language, number of pages, 
        and scenario, and returns it in a structured JSON format with panels.

        Parameters:
            entities (list): List of entity details with 'name' and 'appearance'.
            language (str): The language in which the story should be written.
            number_of_pages (int): The target number of pages for the story.
            scenario (str): A brief scenario or storyline for the story.

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

        **Storyline scenario:**
        {scenario}

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
                    "name": "generate_story_text",
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
            function_call={"name": "generate_story_text"}
        )

        # Extract and return the story panels in JSON format
        story_text = json.loads(completion.choices[0].message.function_call.arguments)["panels"]
        return story_text

    def extract_extra_entities_from_story(self, story_text, entities):
        """
        Extracts entities from a story based on mentions in story panels and returns a list of entities with their appearances.

        Parameters:
            story_text (list): List of dictionaries with 'index' and 'text' for each story panel.

        Returns:
            list: A list of entities with their 'name' and 'appearance' fields.
        """

        # Initialize an empty list to store entities who appear in the story
        appearing_entities = []

        # Create the prompt for extracting entity names and descriptions
        formatted_prompt = f"""
        Analyze the following story panels to identify all unique entity mentioned. For each entity, return their reference and any appearance or descriptive information given in the story.

        **Story Panels:**
        {story_text}

        **Existing Entities:**
        {entities}

        Return the entities in a JSON format, where each entity includes 'name' and 'appearance' fields. Only include unique entities that are mentioned at least twice in the story. Entities can be: objects, characters, animals, etc.
        Also include the existing entities.
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
                    "name": "extract_extra_entities_from_story",
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
            function_call={"name": "extract_extra_entities_from_story"}
        )

        # Extract the entity list from the API response
        appearing_entities = json.loads(completion.choices[0].message.function_call.arguments)["entities"]

        return appearing_entities

    def generate_entity_description(self, entity):
        """
        Generates a description for a single entity based on provided details.
        
        Parameters:
            entity (dict): Dictionary with entity's name and appearance.
            
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

    def generate_entity_descriptions(self, entities):
        """
        Generates descriptions for a list of entities.
        
        Parameters:
            entities (list): List of entity dictionaries with name and appearance.
            
        Returns:
            list: List of dictionaries with each entity's name and generated detailed appearance.
        """
        descriptions = []

        for entity in entities:
            # Generate description for each entity
            detailed_appearance = self.generate_entity_description(entity)
            entity["detailed_appearance"] = detailed_appearance
            descriptions.append(entity)

        return descriptions

    def generate_metadata(self, story_panels):
        """
        Generates metadata for a book, including title, genre, and keywords, based on the provided scenes 
        and optional description.

        Parameters:
            scenes (str): A brief summary of the scenes or main events of the book.
            description (str, optional): Additional information or storyline description for more context.

        Returns:
            dict: JSON object containing title, genre, and keywords.
        """

        # Define the prompt for generating metadata
        prompt_template = """
        Given the following scenes and storyline description, generate metadata for a story. Include:

        - A suitable, engaging title
        - A relevant genre for the story
        - 3-5 keywords that represent the core elements or themes of the story

        Scenes:
        {story_panels}

        Return the metadata in JSON format with "title", "genre", and "keywords" fields.
        """

        # Format the prompt
        formatted_prompt = prompt_template.format(
            story_panels=story_panels,
        )

        # Interact with the model to generate metadata
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a creative assistant for book metadata generation."},
                {"role": "user", "content": formatted_prompt},
            ],
            functions=[
                {
                    "name": "generate_metadata",
                    "description": "Generate metadata for a book",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "The generated title for the story"},
                            "genre": {"type": "string", "description": "The genre of the story"},
                            "keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of keywords relevant to the story"
                            }
                        },
                        "required": ["title", "genre", "keywords"]
                    }
                }
            ],
            function_call={"name": "generate_metadata"}
        )

        # Extract metadata from the API response
        metadata = json.loads(completion.choices[0].message.function_call.arguments)

        return metadata

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
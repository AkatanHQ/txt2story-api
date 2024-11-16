import re
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from app.utils.logger import logger

# Load environment variables from a .env file
load_dotenv()

class TextGenerator:
    def __init__(self):
        try:
            logger.info("Initializing TextGenerator")
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            if not self.client:
                raise ValueError("OpenAI API key is missing or invalid.")
        except Exception as e:
            logger.error(f"Error initializing TextGenerator: {e}", exc_info=True)
            raise RuntimeError("Failed to initialize TextGenerator")

    def generate_story_text(self, entities, language, number_of_pages, scenario):
        try:
            logger.info("Generating story text")
            logger.debug(f"Input parameters: entities={entities}, language={language}, number_of_pages={number_of_pages}, scenario={scenario}")

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
            - Each panel should include an index, starting with 0, a concise text that captures the moment within this structure, and an Image prompt.
            """

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

            story_text = json.loads(completion.choices[0].message.function_call.arguments)["panels"]
            logger.info("Successfully generated story text")
            logger.debug(f"Generated story panels: {story_text}")
            return story_text

        except Exception as e:
            logger.error(f"Error generating story text: {e}", exc_info=True)
            raise RuntimeError("Failed to generate story text")

    def extract_extra_entities_from_story(self, story_text, entities):
        try:
            logger.info("Extracting extra entities from story text")
            logger.debug(f"Story text: {story_text}, Existing entities: {entities}")

            formatted_prompt = f"""
            Analyze the following story panels to identify all unique entity mentioned. For each entity, return their reference and any appearance or descriptive information given in the story.

            **Story Panels:**
            {story_text}

            **Existing Entities:**
            {entities}

            Return the entities in a JSON format, where each entity includes 'name' and 'appearance' fields. Only include unique entities that are mentioned at least twice in the story. Entities can be: objects, characters, animals, etc.
            Also include the existing entities.
            """

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

            extracted_entities = json.loads(completion.choices[0].message.function_call.arguments)["entities"]
            logger.info("Successfully extracted extra entities")
            logger.debug(f"Extracted entities: {extracted_entities}")
            return extracted_entities

        except Exception as e:
            logger.error(f"Error extracting extra entities: {e}", exc_info=True)
            raise RuntimeError("Failed to extract entities from story")

    def generate_entity_description(self, entity):
        try:
            logger.info("Generating detailed description for entity")
            logger.debug(f"Entity input: {entity}")

            prompt_template = """
            Given the following entity details, generate a vivid and detailed physical description of the entity, focusing solely on their appearance, clothing, and notable features.

            Entity Name: {name}
            Appearance: {appearance}
            """

            formatted_prompt = prompt_template.format(name=entity['name'], appearance=entity['appearance'])

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

            detailed_appearance = json.loads(completion.choices[0].message.function_call.arguments)["detailed_appearance"]
            logger.info("Successfully generated entity description")
            logger.debug(f"Generated description: {detailed_appearance}")
            return {"name": entity["name"], "detailed_appearance": detailed_appearance}

        except Exception as e:
            logger.error(f"Error generating entity description: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate description for entity {entity['name']}")


    def generate_entity_descriptions(self, entities):
        """
        Generates descriptions for a list of entities.

        Parameters:
            entities (list): List of entity dictionaries with name and appearance.

        Returns:
            list: List of dictionaries with each entity's name and generated detailed appearance.
        """
        try:
            logger.info("Generating detailed descriptions for multiple entities")
            descriptions = []

            for entity in entities:
                logger.debug(f"Processing entity: {entity}")
                detailed_appearance = self.generate_entity_description(entity)
                entity["detailed_appearance"] = detailed_appearance
                descriptions.append(entity)

            logger.info("Successfully generated descriptions for all entities")
            return descriptions

        except Exception as e:
            logger.error(f"Error generating entity descriptions: {e}", exc_info=True)
            raise RuntimeError("Failed to generate entity descriptions")


    def generate_metadata(self, story_panels):
        """
        Generates metadata for a book, including title, genre, and keywords.

        Parameters:
            story_panels (list): A brief summary of the story panels or main events.

        Returns:
            dict: JSON object containing title, genre, and keywords.
        """
        try:
            logger.info("Generating metadata for the story")
            logger.debug(f"Story panels input: {story_panels}")

            prompt_template = """
            Given the following scenes and storyline description, generate metadata for a story. Include:

            - A suitable, engaging title
            - A relevant genre for the story
            - 3-5 keywords that represent the core elements or themes of the story

            Scenes:
            {story_panels}

            Return the metadata in JSON format with "title", "genre", and "keywords" fields.
            """

            formatted_prompt = prompt_template.format(story_panels=story_panels)

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

            metadata = json.loads(completion.choices[0].message.function_call.arguments)
            logger.info("Successfully generated metadata")
            logger.debug(f"Generated metadata: {metadata}")
            return metadata

        except Exception as e:
            logger.error(f"Error generating metadata: {e}", exc_info=True)
            raise RuntimeError("Failed to generate metadata")


    def generate_title(self, scenes):
        """
        Generates a suitable title for the story based on the scenes.

        Parameters:
            scenes (str): A brief summary or description of the scenes.

        Returns:
            str: The generated title.
        """
        try:
            logger.info("Generating title for the story")
            logger.debug(f"Scenes input: {scenes}")

            prompt_template = """
            Given the following scenes and dialogues, generate a suitable title for the story. Make it short.

            Scenes:
            {scenes}

            Return only the title.
            """

            formatted_prompt = prompt_template.format(scenes=scenes)

            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for title generation."},
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

            title = json.loads(completion.choices[0].message.function_call.arguments)["title"]
            logger.info("Successfully generated title")
            logger.debug(f"Generated title: {title}")
            return title

        except Exception as e:
            logger.error(f"Error generating title: {e}", exc_info=True)
            raise RuntimeError("Failed to generate title")

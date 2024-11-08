from app.services.text_generator import TextGenerator
import json

class ComicJsonGenerator:
    def __init__(self, entities, language, number_of_pages, scenario):
        """
        Initializes the ComicJsonGenerator with the parameters needed to generate a story.

        Parameters:
            entities (list): List of entity details with 'name' and 'appearance'.
            language (str): The language in which the story should be written.
            number_of_pages (int): The target number of pages for the story.
            scenario (str): A brief scenario or storyline for the story.
        """
        self.entities = entities
        self.language = language
        self.number_of_pages = number_of_pages
        self.scenario = scenario
        self.generator = TextGenerator()

    def generate_story_json(self):
        """
        Orchestrates the complete process of generating the story JSON, including story panels,
        detailed entity scenarios, and the story title.

        Returns:
            dict: A JSON-compatible dictionary with the generated title, story panels, and detailed entities.
        """
        # Step 1: Generate the story text with panels
        story_text = self.generator.generate_story_text(
            entities=self.entities,
            language=self.language,
            number_of_pages=self.number_of_pages,
            scenario=self.scenario
        )

        # Step 2: Extract unique entities from the story
        entities = self.generator.extract_extra_entities_from_story(story_text, self.entities)

        # Step 3: Generate detailed scenarios for each extracted entity
        detailed_entities = self.generator.generate_entity_descriptions(entities)

        # Step 4: Generate a title for the story
        metadata = self.generator.generate_metadata(story_text)

        # Compile the final JSON-compatible dictionary
        return {
            "metadata": metadata,
            "story_text": story_text,
            "entities": detailed_entities
        }

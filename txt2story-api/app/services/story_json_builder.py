from app.services.text_generator import TextGenerator
import json

class StoryJsonBuilder:
    def __init__(self):
        """
        Initializes the ComicJsonGenerator with the parameters needed to generate a story.
        """
        self.generator = TextGenerator()
    

    def generate_story(self, entities, language, number_of_pages, scenario):
        self.entities = entities
        self.language = language
        self.number_of_pages = number_of_pages
        self.scenario = scenario
    
        """
        Orchestrates the complete process of generating the story JSON, including story panels,
        detailed entity scenarios, and the story title.
        """
        # Step 1: Generate the story text with panels
        self.story_text = self.generator.generate_story_text(
            entities=self.entities,
            language=self.language,
            number_of_pages=self.number_of_pages,
            scenario=self.scenario
        )

        # Step 2: Extract unique entities from the story
        extracted_entities = self.generator.extract_extra_entities_from_story(self.story_text, self.entities)

        # Step 3: Generate detailed scenarios for each extracted entity
        self.detailed_entities = self.generator.generate_entity_descriptions(extracted_entities)

        # Step 4: Generate a title and metadata for the story
        self.metadata = self.generator.generate_metadata(self.story_text)

    # Get methods to retrieve each component after generation
    def get_metadata(self):
        """Returns the generated metadata/title for the story."""
        return self.metadata

    def get_story_text(self):
        """Returns the generated story text with panels."""
        return self.story_text

    def get_entities(self):
        """Returns the detailed description of entities involved in the story."""
        return self.detailed_entities

    def get_full_story(self):
        """
        Returns a dictionary containing all generated components in JSON format, useful for exporting or further processing.
        """
        return {
            "metadata": self.metadata,
            "story_text": self.story_text,
            "entities": self.detailed_entities
        }

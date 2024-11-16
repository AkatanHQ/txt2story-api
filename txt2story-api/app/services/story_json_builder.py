from app.services.text_generator import TextGenerator
import json
from app.utils.logger import logger

class StoryJsonBuilder:
    def __init__(self):
        try:
            logger.info("Initializing StoryJsonBuilder")
            self.generator = TextGenerator()
        except Exception as e:
            logger.error(f"Failed to initialize StoryJsonBuilder: {e}", exc_info=True)
            raise RuntimeError("Initialization error in StoryJsonBuilder")

    def generate_story(self, entities, language, number_of_pages, scenario):
        try:
            logger.info("Generating story")
            logger.debug(f"Story parameters: entities={entities}, language={language}, number_of_pages={number_of_pages}, scenario={scenario}")

            self.entities = entities
            self.language = language
            self.number_of_pages = number_of_pages
            self.scenario = scenario

            # Step 1: Generate story text
            self.story_text = self.generator.generate_story_text(
                entities=self.entities,
                language=self.language,
                number_of_pages=self.number_of_pages,
                scenario=self.scenario
            )
            logger.info("Story text generated successfully")

            # Step 2: Extract unique entities
            extracted_entities = self.generator.extract_extra_entities_from_story(self.story_text, self.entities)
            logger.debug(f"Extracted entities: {extracted_entities}")

            # Step 3: Generate detailed descriptions
            self.detailed_entities = self.generator.generate_entity_descriptions(extracted_entities)
            logger.info("Entity descriptions generated successfully")

            # Step 4: Generate metadata
            self.metadata = self.generator.generate_metadata(self.story_text)
            logger.info("Story metadata generated successfully")

        except Exception as e:
            logger.error(f"Error in story generation: {e}", exc_info=True)
            raise RuntimeError("Error generating story")

    def get_full_story(self):
        try:
            logger.info("Compiling full story data")
            return {
                "metadata": self.metadata,
                "story_text": self.story_text,
                "entities": self.detailed_entities
            }
        except Exception as e:
            logger.error(f"Error compiling full story: {e}", exc_info=True)
            raise RuntimeError("Error retrieving story data")


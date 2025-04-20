from app.services.text_generator import TextGenerator
from app.utils.logger import logger

class StoryJsonBuilder:
    def __init__(self):
        try:
            logger.info("Initializing StoryJsonBuilder")
            self.generator = TextGenerator()
        except Exception as e:
            logger.error(f"Failed to initialize StoryJsonBuilder: {e}", exc_info=True)
            raise RuntimeError("Initialization error in StoryJsonBuilder")

    def generate_story(self, entities, prompt):
        try:
            logger.info("Generating story")
            logger.debug(f"Story parameters: entities={entities}, prompt={prompt}")

            self.entities = entities
            self.prompt = prompt

            # Step 1: Generate story text
            self.scenes = self.generator.generate_scenes(
                entities=self.entities,
                prompt=self.prompt
            )
            logger.info("Story text generated successfully")

            # Step 2: Extract unique entities
            extracted_entities = self.generator.extract_extra_entities_from_story(self.scenes, self.entities)
            logger.debug(f"Extracted entities: {extracted_entities}")

            # Step 3: Generate detailed descriptions
            self.detailed_entities = self.generator.generate_entity_detailed_appearances(extracted_entities)
            logger.info("Entity descriptions generated successfully")

            # Step 4: Generate metadata
            self.metadata = self.generator.generate_metadata(self.scenes)
            logger.info("Story metadata generated successfully")

        except Exception as e:
            logger.error(f"Error in story generation: {e}", exc_info=True)
            raise RuntimeError("Error generating story")

    def get_full_story(self):
        try:
            logger.info("Compiling full story data")
            return {
                "metadata": self.metadata,
                "scenes": self.scenes,
                "entities": self.detailed_entities
            }
        except Exception as e:
            logger.error(f"Error compiling full story: {e}", exc_info=True)
            raise RuntimeError("Error retrieving story data")

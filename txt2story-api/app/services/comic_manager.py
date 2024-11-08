from app.services.text_generator import TextGenerator
from app.services.comic_json_generator import ComicJsonGenerator
from app.services.image_generator import ImageGenerator

class ComicManager:
    def __init__(self, entities, language, number_of_pages, scenario, img_model='dall-e-3', model_resolution="1024x1024"):
        self.entities = entities
        self.language = language
        self.number_of_pages = number_of_pages
        self.scenario = scenario
        self.img_model = img_model
        self.image_generator = ImageGenerator()
        self.model_resolution = model_resolution

        self.json_generator = ComicJsonGenerator(entities, language, number_of_pages, scenario)

    def generate_comic_and_save_to_cloud(self, user_id, comic_name, description):
        """
        Orchestrates the entire process of generating the comic, including story text, images,
        and saving it to the database.
        """
        # Use ComicJsonGenerator to get structured story JSON
        story_json = self.json_generator.generate_story_json()
        metadata = story_json["metadata"]
        print(story_json)


        # # Iterate through the story panels in JSON to save and generate images
        # for index, panel in enumerate(story_json["story_text"]):
        #     # Generate and upload image based on the image prompt
        #     image = self.image_generator.generate_image(panel["image_prompt"])
            

        return story_json

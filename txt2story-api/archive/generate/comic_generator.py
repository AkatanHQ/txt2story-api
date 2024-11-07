# generate/comic_generator.py

from generate.generate_panels import generate_panels
from generate.image_generator import ImageGenerator
from storage.storage_manager import ComicStorageManager
from utils.enums import StoryLength, StyleDescription
import concurrent.futures
import time
import sys

class ComicGenerator:
    def __init__(self, storage_manager: ComicStorageManager):
        self.storage_manager = storage_manager

    def generate_comic(self, scenario=None, user_id=None, story_title=None, img_model='dall-e-2', selectedStyle="tintin", language='english', num_panels=6):
        try:
            if not user_id:
                raise ValueError("user_id must be provided.")

            # Initialize the image generator
            self.image_generator = ImageGenerator(img_model=img_model)

            # Load or generate the panels
            book_data = self.generate_panels(scenario, user_id, language, num_panels)
            story_title = book_data["title"]
            self.storage_manager.save_json(book_data, user_id, story_title, 'panels.json')
            
            # Generate images for each panel and update the panels data
            panels = self.generate_images_for_panels(book_data["panels"], user_id, story_title, selectedStyle)
            book_data["panels"] = panels
            self.storage_manager.save_json(book_data, user_id, story_title, 'panels.json')

            print(f"Story generated successfully! Files saved to {self.storage_manager.get_comic_directory(user_id, story_title)}")
            return book_data

        except KeyboardInterrupt:
            print("Process interrupted by user. Shutting down...")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            return None

    def generate_panels(self, scenario, user_id, language, num_panels):
        if scenario:
            panels = generate_panels(scenario, num_panels, language)
        else:
            raise ValueError("You must provide a scenario")
        
        return panels

    def generate_images_for_panels(self, panels, user_id, story_title, selectedStyle):
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(self.generate_image_for_panel, panel, user_id, story_title, selectedStyle)
                    for panel in panels
                ]
                updated_panels = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            return updated_panels
        except KeyboardInterrupt:
            print("Process interrupted by user. Cancelling threads...")
            executor.shutdown(wait=False)
            raise

    def generate_image_for_panel(self, panel, user_id, story_title, selectedStyle):
        panel_prompt = f"{panel['description']}. {selectedStyle}"
        max_retries = 3
        retries = 0

        while retries < max_retries:
            try:
                print(f"Generating panel {panel['index']} with prompt: {panel_prompt}")
                panel_image = self.image_generator.generate_image(panel_prompt)
                panel_image_name = f"panel-{panel['index']}.png"
                panel_img_path = self.storage_manager.save_image(panel_image, user_id, story_title, panel_image_name)
                panel['txt2story_img_path'] = panel_img_path
                return panel
                
            except Exception as e:
                if 'rate_limit_exceeded' in str(e):
                    print(f"Rate limit exceeded for panel {panel['index']}. Retrying in 60 seconds... ({retries + 1}/{max_retries})")
                    time.sleep(60)
                    retries += 1
                else:
                    raise e

        print(f"Failed to generate image for panel {panel['index']} after {max_retries} attempts.")
        return panel

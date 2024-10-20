from app.generate.generate_panels import generate_panels
from app.generate.image_generator import ImageGenerator
from app.generate.generate_params import ParamTextGenerator
import concurrent.futures
import time
import signal
import sys
from flask import current_app

class ComicGenerator:
    def __init__(self, storage_manager):
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
            return panels

        except KeyboardInterrupt:
            print("Process interrupted by user. Shutting down...")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            return None

    def generate_panels(self, scenario, user_id, language, num_panels):
        """
        Loads panels from storage or generates them based on the provided scenario or manual input.
        Returns a list of panels.
        """
        panels = []
        
        if scenario:
            # Use number of panels derived from scenario or use a default value if unavailable
            panels = generate_panels(scenario, num_panels, language)
        else:
            raise ValueError("You must provide either a scenario")
        
        return panels

    def generate_images_for_panels(self, panels, user_id, story_title, selectedStyle):
        """
        Generates images for each panel concurrently using the given style and saves them.
        Includes retry logic to handle rate limit errors.
        Returns the updated list of panels with image paths.
        """
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Submit tasks to generate images for each panel concurrently
                futures = [
                    executor.submit(self.generate_image_for_panel, panel, user_id, story_title, selectedStyle)
                    for panel in panels
                ]
                
                # Collect the results as they are completed
                updated_panels = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            return updated_panels
        except KeyboardInterrupt:
            print("Process interrupted by user. Cancelling threads...")
            executor.shutdown(wait=False)  # Attempt to shut down threads immediately
            raise  # Re-raise the KeyboardInterrupt to handle it higher up the chain

    def generate_image_for_panel(self, panel, user_id, story_title, selectedStyle):
        """
        Generates and saves the image for a single panel with retry logic to handle rate limits.
        Returns the updated panel with the image path.
        """
        panel_prompt = f"{panel['description']}. {selectedStyle}"
        max_retries=3
        retries = 0

        while retries < max_retries:
            try:
                print(f"Generating panel {panel['index']} with prompt: {panel_prompt} \n")
                panel_image = self.image_generator.generate_image(panel_prompt)
                panel_image_name = f"panel-{panel['index']}.png"
                panel_txt2story_img_path = self.storage_manager.save_image(panel_image, user_id, story_title, panel_image_name)
                panel['txt2story_img_path'] = panel_txt2story_img_path
                return panel
                
            except Exception as e:
                if 'rate_limit_exceeded' in str(e):
                    print(f"Rate limit exceeded for panel {panel['index']}. Retrying in 60 seconds... ({retries + 1}/{max_retries})")
                    time.sleep(60)  # Wait for 60 seconds before retrying
                    retries += 1
                else:
                    raise e  # Re-raise the exception if it's not a rate limit error

        print(f"Failed to generate image for panel {panel['index']} after {max_retries} attempts.")
        return panel  # Return panel even if it fails to generate the image

# Example usage:
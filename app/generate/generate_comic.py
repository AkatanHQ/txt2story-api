from app.generate.generate_panels import generate_panels
from app.generate.text_to_image import *
from app.generate.add_text import add_text_to_panel
from app.generate.create_strip import create_strip
import concurrent.futures
import time
import signal
import sys
from flask import current_app


def generate_comic(storage_manager, scenario=None, user_id=None, story_title=None, style="american comic, colored", manual_panels=None):
    try:
        panels_file_name = 'panels.json'

        # Validate input
        if not story_title:
            raise ValueError("story_title must be provided.")
        if not user_id:
            raise ValueError("user_id must be provided.")
        
        panels = load_or_generate_panels(storage_manager, scenario, user_id, story_title, manual_panels)
        storage_manager.save_json(panels, user_id, story_title, panels_file_name)
        panels = generate_images_for_panels(panels, storage_manager, user_id, story_title, style)
        storage_manager.save_json(panels, user_id, story_title, panels_file_name)

        print(f"Story generated successfully! Files saved to {storage_manager.get_comic_directory(user_id, story_title)}")
        return panels

    except KeyboardInterrupt:
        print("Process interrupted by user. Shutting down...")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        return None


def load_or_generate_panels(storage_manager, scenario, user_id, story_title, manual_panels=None):
    """
    Loads panels from storage or generates them based on the provided scenario or manual input.
    Returns a list of panels.
    """
    panels_file_name = 'panels.json'
    panels = storage_manager.load_json(story_title, user_id, panels_file_name) or []

    if not panels:
        if manual_panels:
            panels = manual_panels
        elif scenario:
            panels = generate_panels(scenario)
        else:
            raise ValueError("You must provide either a scenario or manual_panels.")
    
    return panels


def generate_images_for_panels(panels, storage_manager, user_id, story_title, style, max_retries=3):
    """
    Generates images for each panel concurrently using the given style and saves them.
    Includes retry logic to handle rate limit errors.
    Returns the updated list of panels with image paths.
    """
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit tasks to generate images for each panel concurrently
            futures = [
                executor.submit(generate_image_for_panel, panel, storage_manager, user_id, story_title, style, max_retries)
                for panel in panels
            ]
            
            # Collect the results as they are completed
            updated_panels = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        return updated_panels
    except KeyboardInterrupt:
        print("Process interrupted by user. Cancelling threads...")
        executor.shutdown(wait=False)  # Attempt to shut down threads immediately
        raise  # Re-raise the KeyboardInterrupt to handle it higher up the chain


def generate_image_for_panel(panel, storage_manager, user_id, story_title, style, max_retries=3):
    """
    Generates and saves the image for a single panel with retry logic to handle rate limits.
    Returns the updated panel with the image path.
    """
    panel_prompt = f"{panel['description']}, cartoon box, {style}"
    retries = 0

    # Get the appropriate image generator based on the environment variables
    image_generator = get_image_generator()

    while retries < max_retries:
        try:
            print(f"Generating panel {panel['index']} with prompt: {panel_prompt} \n")
            panel_image = image_generator(panel_prompt)  # Use the dynamic image generator
            panel_image_name = f"panel-{panel['index']}.png"
            panel_txt2story_img_path = storage_manager.save_image(panel_image, user_id, story_title, panel_image_name)
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
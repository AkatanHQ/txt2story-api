import os
import json
from generate_panels import generate_panels, manage_panels
from text_to_image import text_to_image_dalle3
from add_text import add_text_to_panel
from create_strip import create_strip

def generate_comic(scenario=None, file_name=None, style="american comic, colored", manual_panels=None):
    try:
        # Validate input
        if not file_name:
            raise ValueError("file_name must be provided.")

        # Create output directory
        output_folder = f"output/{file_name}"
        os.makedirs(output_folder, exist_ok=True)

        panels_path = f'{output_folder}/panels.json'
        panels = []

        # Use the manage_panels function to get the panels
        if panels_path and os.path.exists(panels_path):
            # Load panels from a JSON file if the path is provided
            with open(panels_path, 'r') as infile:
                panels = json.load(infile)
        panels = manage_panels(scenario=scenario, panels_path=panels_path, manual_panels=manual_panels)

        # Generate images for each panel
        for panel in panels:
            panel_prompt = f"{panel['description']}, cartoon box, {style}"
            print(f"Generating panel {panel['number']} with prompt: {panel_prompt}")
            panel_image = text_to_image_dalle3(panel_prompt)
            panel_image_path = f"{output_folder}/panel-{panel['number']}.png"
            panel_image.save(panel_image_path)
            panel['image_path'] = panel_image_path

        # Save the panel descriptions to a JSON file
        with open(panels_path, 'w') as outfile:
            json.dump(panels, outfile)

        print(f"Images created successfully! Info to be retrieved at {panels_path}")
        return panels

    except Exception as e:
        print(f"Error: {e}")
        return None

def get_strip(file_name):
    try:
        strip_image_path = f"output/{file_name}/strip.png"
        if os.path.exists(strip_image_path):
            return strip_image_path
        else:
            raise FileNotFoundError(f"Strip image not found: {strip_image_path}")
    
    except Exception as e:
        print(f"Error: {e}")
        return None

# Example usage
scenario = "Characters: Lily is a little girl with curly brown hair and a red dress. Max is a small boy with spiky blonde hair and blue overalls. Lily and Max are best friends, and they go to the playground to play on the swings. Lily falls off the swing and Max helps her up. Lily cries and Max comforts her. Lily is happy again."
file_name = "Lily_and_Max_at_the_playground"
style = "american comic, colored"


generate_comic(scenario, file_name, style)

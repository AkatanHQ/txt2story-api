from app.generate.generate_panels import generate_panels, manage_panels
from app.generate.text_to_image import text_to_image_dalle3
from app.generate.add_text import add_text_to_panel
from app.generate.create_strip import create_strip


def generate_comic(storage_manager, scenario=None, user_id=None, file_name=None, style="american comic, colored", manual_panels=None):
    try:
        # Validate input
        if not file_name:
            raise ValueError("file_name must be provided.")
        if not user_id:
            raise ValueError("user_id must be provided.")

        # Load panels from existing JSON file if it exists
        panels = storage_manager.load_json(file_name, user_id, 'panels.json') or []

        # Use the manage_panels function to get the panels
        if not panels:
            panels = manage_panels(scenario=scenario, panels_path=None, manual_panels=manual_panels)

        # Generate images for each panel
        for panel in panels:
            panel_prompt = f"{panel['description']}, cartoon box, {style}"
            print(f"Generating panel {panel['number']} with prompt: {panel_prompt}")
            panel_image = text_to_image_dalle3(panel_prompt)
            panel_image_name = f"panel-{panel['number']}.png"
            panel_image_path = storage_manager.save_image(panel_image, user_id, file_name, panel_image_name)
            panel['image_path'] = panel_image_path

        # Save the panel descriptions to a JSON file
        storage_manager.save_json(panels, user_id, file_name, 'panels.json')

        print(f"Comic generated successfully! Files saved to {storage_manager.get_comic_directory(user_id, file_name)}")
        return panels

    except Exception as e:
        print(f"Error: {e}")
        return None

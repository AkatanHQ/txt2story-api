from app.generate.generate_panels import generate_panels
from app.generate.text_to_image import text_to_image_dalle3
from app.generate.add_text import add_text_to_panel
from app.generate.create_strip import create_strip


def generate_comic(storage_manager, scenario=None, user_id=None, story_title=None, style="american comic, colored", manual_panels=None):
    try:
        # Validate input
        if not story_title:
            raise ValueError("story_title must be provided.")
        if not user_id:
            raise ValueError("user_id must be provided.")

        # Load panels from existing JSON file if it exists
        panels_file_name = 'panels.json'
        panels = storage_manager.load_json(story_title, user_id, panels_file_name) or []

        # Use the manage_panels function to get the panels
        if not panels:
            """
            Manages panels by either generating new ones, loading existing ones, or using manually input panels.
            Returns a list of panels.
            """
            panels = []

            if manual_panels:
                # Use manually input panels if provided
                panels = manual_panels
            elif scenario:
                # Generate panels dynamically based on the scenario
                panels = generate_panels(scenario)
            else:
                raise ValueError("You must provide either a scenario, a valid panels_path, or manual_panels.")

        # Save the panel descriptions to a JSON file
        storage_manager.save_json(panels, user_id, story_title, panels_file_name)

        # Generate images for each panel
        for panel in panels:
            panel_prompt = f"{panel['description']}, cartoon box, {style}"
            print(f"Generating panel {panel['index']} with prompt: {panel_prompt}")
            panel_image = text_to_image_dalle3(panel_prompt)
            panel_image_name = f"panel-{panel['index']}.png"
            panel_txt2story_img_path = storage_manager.save_image(panel_image, user_id, story_title, panel_image_name)
            panel['txt2story_img_path'] = panel_txt2story_img_path

        # Save the panel descriptions (with images) to a JSON file
        storage_manager.save_json(panels, user_id, story_title, panels_file_name)

        print(f"Story generated successfully! Files saved to {storage_manager.get_comic_directory(user_id, story_title)}")
        return panels

    except Exception as e:
        print(f"Error: {e}")
        return None

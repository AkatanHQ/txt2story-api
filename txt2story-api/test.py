# Import the ComicManager class
from app.services.comic_manager import ComicManager

# Define your input parameters
entities = []
language = "English"
number_of_pages = 5
scenario = "An epic space battle unfolds between the hero and the villain."
user_id = "user123"
comic_name = "Galactic Adventure"
description = "A thrilling journey through space with unexpected twists and turns."

# Create an instance of ComicManager
comic_manager = ComicManager(entities=entities, language=language, number_of_pages=number_of_pages, scenario=scenario)

# Generate the comic and save it to the cloud
story_json = comic_manager.generate_comic_and_save_to_cloud(user_id=user_id, comic_name=comic_name, description=description)

# Display the generated JSON (optional)
print(story_json)

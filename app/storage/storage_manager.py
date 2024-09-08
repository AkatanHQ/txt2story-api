import os
import json
import threading
from PIL import Image

class ComicStorageManager:
    def __init__(self, base_directory='static'):
        self.base_directory = base_directory
        os.makedirs(self.base_directory, exist_ok=True)
        self.lock = threading.Lock()

    def get_comic_directory(self, user_id, comic_name):
        # Adjusted to make paths relative to Flask's static directory
        return os.path.join(self.base_directory, f'user_{user_id}', 'comics', comic_name)

    def create_comic_directory(self, user_id, comic_name):
        comic_directory = self.get_comic_directory(user_id, comic_name)
        with self.lock:
            os.makedirs(comic_directory, exist_ok=True)
        return comic_directory

    def save_json(self, data, user_id, comic_name, json_name):
        comic_directory = self.create_comic_directory(user_id, comic_name)
        json_path = os.path.join(comic_directory, json_name)
        with self.lock:
            with open(json_path, 'w') as outfile:
                json.dump(data, outfile)
        return json_path

    def load_json(self, user_id, comic_name, json_name):
        comic_directory = self.get_comic_directory(user_id, comic_name)
        json_path = os.path.join(comic_directory, json_name)
        if os.path.exists(json_path):
            with self.lock:
                with open(json_path, 'r') as infile:
                    return json.load(infile)
        return None

    def save_image(self, image, user_id, comic_name, image_name):
        comic_directory = self.create_comic_directory(user_id, comic_name)
        image_path = os.path.join(comic_directory, image_name)
        with self.lock:
            image.save(image_path)
        return image_path

    def load_image(self, user_id, comic_name, image_name):
        comic_directory = self.get_comic_directory(user_id, comic_name)
        image_path = os.path.join(comic_directory, image_name)
        if os.path.exists(image_path):
            with self.lock:
                return Image.open(image_path)
        return None

    def load_image_by_panel_index(self, user_id, comic_name, panel_index):
        comic_directory = self.get_comic_directory(user_id, comic_name)
        image_name = f"panel-{panel_index}.png"
        image_path = os.path.join(comic_directory, image_name)
        if os.path.exists(image_path):
            with self.lock:
                return Image.open(image_path)
        return None

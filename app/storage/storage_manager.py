import os
import json
from PIL import Image
import threading

class ComicStorageManager:
    def __init__(self, base_directory='output'):
        self.base_directory = base_directory
        os.makedirs(self.base_directory, exist_ok=True)
        self.lock = threading.Lock()

    def get_comic_directory(self, user_id, comic_name):
        return os.path.join(self.base_directory, f'user_{user_id}', 'comics', comic_name)

    def create_comic_directory(self, user_id, comic_name):
        comic_directory = self.get_comic_directory(user_id, comic_name)
        # Use a lock to avoid race conditions in directory creation
        with self.lock:
            os.makedirs(comic_directory, exist_ok=True)
        return comic_directory

    def save_json(self, data, user_id, comic_name, json_name):
        comic_directory = self.create_comic_directory(user_id, comic_name)
        json_path = os.path.join(comic_directory, json_name)
        # Use a lock to avoid race conditions in writing to the same file
        with self.lock:
            with open(json_path, 'w') as outfile:
                json.dump(data, outfile)
        return json_path

    def load_json(self, user_id, comic_name, json_name):
        comic_directory = self.get_comic_directory(user_id, comic_name)
        json_path = os.path.join(comic_directory, json_name)
        if os.path.exists(json_path):
            with self.lock:  # Ensure thread-safe read
                with open(json_path, 'r') as infile:
                    return json.load(infile)
        return None

    def save_image(self, image, user_id, comic_name, image_name):
        comic_directory = self.create_comic_directory(user_id, comic_name)
        txt2story_img_path = os.path.join(comic_directory, image_name)
        # Use a lock to avoid race conditions in writing images
        with self.lock:
            image.save(txt2story_img_path)
        return txt2story_img_path

    def load_image(self, user_id, comic_name, image_name):
        comic_directory = self.get_comic_directory(user_id, comic_name)
        txt2story_img_path = os.path.join(comic_directory, image_name)
        if os.path.exists(txt2story_img_path):
            with self.lock:  # Ensure thread-safe read
                return Image.open(txt2story_img_path)
        return None

    def load_image_by_panel_index(self, user_id, comic_name, panel_index):
        comic_directory = self.get_comic_directory(user_id, comic_name)
        image_name = f"panel-{panel_index}.png"
        txt2story_img_path = os.path.join(comic_directory, image_name)
        if os.path.exists(txt2story_img_path):
            with self.lock:  # Ensure thread-safe read
                return Image.open(txt2story_img_path)
        return None

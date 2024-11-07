import threading
from PIL import Image
from io import BytesIO
from sqlalchemy.orm import Session
from app.database.models import UserComics, ComicPanels
from app.database.crud import create_comic, create_comic_panel, get_comics_by_user, get_comic_by_id, get_panels_by_comic
from app.database.db import get_db

class ComicStorageManager:
    def __init__(self, db: Session):
        self.db = db
        self.lock = threading.Lock()

    def create_comic_entry(self, user_id, comic_name, title, genre=None, keywords=None, description=None, cover_image_path=None):
        """Creates a new comic entry in the database."""
        with self.lock:
            new_comic = create_comic(
                db=self.db,
                user_id=user_id,
                comic_name=comic_name,
                title=title,
                genre=genre,
                keywords=keywords,
                description=description,
                cover_image_path=cover_image_path
            )
        return new_comic

    def comic_exists(self, user_id, comic_name):
        """Check if a comic exists for a given user by name."""
        comics = get_comics_by_user(self.db, user_id)
        return any(comic.comic_name == comic_name for comic in comics)

    def get_all_comic_names(self, user_id):
        """Retrieve all comic names for a user from the database."""
        comics = get_comics_by_user(self.db, user_id)
        return [comic.comic_name for comic in comics]

    def update_comic_metadata(self, comic_id, title=None, genre=None, keywords=None, description=None, cover_image_path=None):
        """Update metadata for an existing comic in the database."""
        with self.lock:
            comic = get_comic_by_id(self.db, comic_id)
            if not comic:
                raise ValueError("Comic not found.")
            
            if title is not None:
                comic.title = title
            if genre is not None:
                comic.genre = genre
            if keywords is not None:
                comic.keywords = keywords
            if description is not None:
                comic.description = description
            if cover_image_path is not None:
                comic.cover_image_path = cover_image_path
            
            self.db.commit()
            self.db.refresh(comic)
        return comic

    def get_comic_metadata(self, comic_id):
        """Retrieve metadata for a specific comic."""
        comic = get_comic_by_id(self.db, comic_id)
        if not comic:
            raise ValueError("Comic not found.")
        return comic

    def save_image(self, image: Image, comic_id, panel_index, image_name):
        """Save an image for a specific panel in a comic and store the path in the database."""
        # Save image to file system or storage service and store the path
        image_path = f"user_{comic_id}/comics/{image_name}"
        image.save(image_path)

        # Save panel entry in the database
        with self.lock:
            new_panel = create_comic_panel(
                db=self.db,
                comic_id=comic_id,
                panel_index=panel_index,
                description=None,
                text=None,
                image_path=image_path
            )
        return new_panel

    def load_image(self, comic_id, panel_index):
        """Load an image for a specific panel in a comic from the database."""
        panels = get_panels_by_comic(self.db, comic_id)
        panel = next((p for p in panels if p.panel_index == panel_index), None)
        
        if panel and panel.image_path:
            with self.lock:
                return Image.open(panel.image_path)  # Open image from the stored path
        return None

    def load_image_by_panel_index(self, comic_id, panel_index):
        """Alternative method to load an image by panel index (same as load_image)."""
        return self.load_image(comic_id, panel_index)

    def sanitize_filename(self, filename):
        """Replace invalid characters in filenames."""
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename.replace(' ', '_')
        return filename

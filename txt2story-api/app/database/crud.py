from sqlalchemy.orm import Session
from .models import UserComics, ComicPanels
from sqlalchemy import select
from typing import List

# CRUD operations for UserComics
def create_comic(db: Session, user_id: int, comic_name: str, title: str, genre: str, keywords: List[str], description: str, cover_image_path: str):
    new_comic = UserComics(
        user_id=user_id,
        comic_name=comic_name,
        title=title,
        genre=genre,
        keywords=keywords,
        description=description,
        cover_image_path=cover_image_path
    )
    db.add(new_comic)
    db.commit()
    db.refresh(new_comic)
    return new_comic

def get_comics_by_user(db: Session, user_id: int):
    return db.query(UserComics).filter(UserComics.user_id == user_id).all()

def get_comic_by_id(db: Session, comic_id: int):
    return db.query(UserComics).filter(UserComics.comic_id == comic_id).first()

# CRUD operations for ComicPanels
def create_comic_panel(db: Session, comic_id: int, panel_index: int, description: str, text: str, image_path: str):
    new_panel = ComicPanels(
        comic_id=comic_id,
        panel_index=panel_index,
        description=description,
        text=text,
        image_path=image_path
    )
    db.add(new_panel)
    db.commit()
    db.refresh(new_panel)
    return new_panel

def get_panels_by_comic(db: Session, comic_id: int):
    return db.query(ComicPanels).filter(ComicPanels.comic_id == comic_id).order_by(ComicPanels.panel_index).all()

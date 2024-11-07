from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, ARRAY
from sqlalchemy.sql import func
from .db import Base

class UserComics(Base):
    __tablename__ = "user_comics"
    
    comic_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    comic_name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    genre = Column(String(100))
    keywords = Column(ARRAY(Text))  # Array of keywords
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    cover_image_path = Column(String(255))


class ComicPanels(Base):
    __tablename__ = "comic_panels"
    
    panel_id = Column(Integer, primary_key=True, index=True)
    comic_id = Column(Integer, ForeignKey("user_comics.comic_id", ondelete="CASCADE"), nullable=False)
    panel_index = Column(Integer, nullable=False)
    description = Column(Text)
    text = Column(Text)
    image_path = Column(String(255))

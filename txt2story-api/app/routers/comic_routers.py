from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.comic_schemas import ComicRequest
from app.services.comic_manager import ComicManager

router = APIRouter()

@router.post("/api/generate_comic")
async def generate_comic(request: ComicRequest):
    # Create the comic generator
    comic_generator = ComicManager(
        entities=request.entities,
        language=request.language,
        number_of_pages=request.number_of_pages,
        scenario=request.scenario,
        img_model=request.img_model
    )

    # Return the generated comic data
    return {"comic": comic_generator}

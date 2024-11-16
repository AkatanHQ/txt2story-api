from fastapi import APIRouter, Depends, HTTPException
from app.schemas.comic_schemas import ComicRequest
from app.services.story_json_builder import StoryJsonBuilder

router = APIRouter()

@router.post("/api/generate_comic")
async def generate_comic(request: ComicRequest):
    # Create the story JSON builder
    story_builder = StoryJsonBuilder()
    
    # Generate the story
    story_builder.generate_story(
        entities=request.entities,
        language=request.language,
        number_of_pages=request.number_of_pages,
        scenario=request.scenario
    )

    # Return the generated comic data as JSON
    return story_builder.get_full_story()

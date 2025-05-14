from fastapi import HTTPException
from app.services.story_json_builder import StoryJsonBuilder
from app.utils.logger import logger
from app.schemas.comic_schemas import ComicRequest, ImageRequest, ImageUrlRequest, Base64ImageRequest


async def generate_story_text_controller(request: ComicRequest):
    try:
        logger.info(f"Generating story text with prompt: {request.prompt}")
        story_builder = StoryJsonBuilder()
        story_builder.generate_story(
            entities=request.entities,
            prompt=request.prompt
        )
        return story_builder.get_full_story()
    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error generating story: {e}", exc_info=True)
        raise HTTPException(500, detail="Error generating story")

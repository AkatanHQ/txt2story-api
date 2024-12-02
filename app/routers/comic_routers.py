from fastapi import APIRouter, Depends, HTTPException
from app.services.story_json_builder import StoryJsonBuilder
from app.services.image_generator import ImageGenerator
from app.utils.logger import logger
from app.schemas.comic_schemas import EntityRequest, ComicRequest, ImageRequest
from app.utils.enums import StyleDescription
import json

router = APIRouter()


@router.post("/api/generate-comic-book")
async def generate_comic(request: ComicRequest):
    try:
        logger.info("Received request to generate comic")
        logger.info(f"Request details: {request}")

        # Create the story JSON builder
        story_builder = StoryJsonBuilder()

        # Generate the story
        story_builder.generate_story(
            entities=request.entities,
            language=request.language,
            number_of_pages=request.number_of_pages,
            scenario=request.scenario
        )

        logger.info("Comic generation completed successfully")
        return story_builder.get_full_story()

    except Exception as e:
        logger.error(f"Error generating comic: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating comic.")

@router.post("/api/generate-image")
async def generate_image(request: ImageRequest):
    try:
        logger.info("Received request to generate image")
        logger.debug(
            f"Image generation parameters: model={request.image_model}, resolution={request.model_resolution}, style={request.style}"
        )

        # Initialize the image generator
        image_generator = ImageGenerator(img_model=request.image_model, model_resolution=request.model_resolution)

        # Transform the style to a description
        try:
            style_description = StyleDescription[request.style.value].value
        except KeyError as ke:
            logger.error(f"Style mapping error: {ke}")
            raise ValueError(f"Style description not found for the given style: {request.style.value}")

        # Prepare the prompt
        prompt = json.dumps({
            "image_prompt": request.image_prompt,
            "entities": [entity.dict() for entity in request.entities],  # Assuming entities can be serialized with .dict()
            "style": style_description,
        })

        logger.debug(f"Generated prompt: {prompt}")

        # Generate the image
        generated_image_url = image_generator.generate_image(prompt)
        logger.info(f"Image generation completed with model {request.image_model}")

        return generated_image_url

    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.error(f"Error generating image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating image.")

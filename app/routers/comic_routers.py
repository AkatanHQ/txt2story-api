from app.utils.enums import StyleOptions, StyleDescription
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.comic_schemas import EntityRequest
from app.services.story_json_builder import StoryJsonBuilder
from app.services.image_generator import ImageGenerator
from fastapi.responses import StreamingResponse
from io import BytesIO
from app.utils.logger import logger
from typing import List, Dict, Optional
import json

router = APIRouter()

@router.post("/api/generate_comic")
async def generate_comic(
    user_id: int,
    scenario: str,
    language: str,
    number_of_pages: int,
    entities: List[EntityRequest]
):
    try:
        logger.info("Received request to generate comic")
        logger.info(f"Request details: user_id={user_id}, scenario={scenario}, language={language}, number_of_pages={number_of_pages}, entities={entities}")

        # Create the story JSON builder
        story_builder = StoryJsonBuilder()

        # Generate the story
        story_builder.generate_story(
            entities=entities,
            language=language,
            number_of_pages=number_of_pages,
            scenario=scenario
        )

        logger.info("Comic generation completed successfully")
        return story_builder.get_full_story()

    except Exception as e:
        logger.error(f"Error generating comic: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating comic.")


@router.post("/api/generate_image")
async def generate_image(
    image_prompt: str,
    entities: List[EntityRequest],
    style: StyleOptions = StyleOptions.COMIC,
    image_model: str = "dall-e-3",
    model_resolution: str = "1024x1024",
):
    try:
        logger.info("Received request to generate image")
        logger.debug(
            f"Image generation parameters: model={image_model}, resolution={model_resolution}, style={style}"
        )

        # Initialize the image generator
        image_generator = ImageGenerator(img_model=image_model, model_resolution=model_resolution)

        # Transform the style to a description
        try:
            style_description = StyleDescription[style.value].value
        except KeyError as ke:
            logger.error(f"Style mapping error: {ke}")
            raise ValueError(f"Style description not found for the given style: {style.value}")

        # Prepare the prompt
        prompt = json.dumps({
            "image_prompt": image_prompt,
            "entities": [entity.dict() for entity in entities],  # Assuming entities can be serialized with .dict()
            "style": style_description,
        })

        logger.debug(f"Generated prompt: {prompt}")

        # Generate the image
        generated_image_url = image_generator.generate_image(prompt)
        logger.info(f"Image generation completed with model {image_model}")

        # Stream the image back to the client
        return generated_image_url

    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.error(f"Error generating image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating image.")

# File: app/routers/comic_routers.py

from fastapi import APIRouter, HTTPException
from openai import BadRequestError, OpenAIError
from pydantic import BaseModel, HttpUrl
from app.services.story_json_builder import StoryJsonBuilder
from app.services.image_generator import ImageGenerator
from app.utils.logger import logger
from app.schemas.comic_schemas import EntityRequest, ComicRequest, ImageRequest
from app.utils.enums import StyleDescription
import json
import base64
from app.services.analyze_image import AnalyzeImage

router = APIRouter()

class Base64ImageRequest(BaseModel):
    provider: str = "openai"
    vision_model: str = "gpt-4o"
    base64_image: str  # Base64-encoded image string
    
class ImageUrlRequest(BaseModel):
    provider: str = "openai"
    vision_model: str = "gpt-4o"
    image_url: HttpUrl  # Ensures valid URL format

@router.post("/analyze-image-url")
async def analyze_image_url(request: ImageUrlRequest):
    """
    Endpoint to analyze an image from a given URL using OpenAI's GPT-4o Vision.
    """
    try:
        logger.info(f"Received request to analyze image from URL: {request.image_url}")

        # Initialize the analyzer
        analyzer = AnalyzeImage(provider=request.provider, vision_model=request.vision_model)

        # Analyze the image from the URL
        result = analyzer.analyze_image_url(str(request.image_url))

        logger.info(f"Successfully analyzed image from URL: {request.image_url}")
        return {"detailed_appearance": result}

    except Exception as e:
        logger.error(f"Error analyzing image from URL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error analyzing image from URL")
    
@router.post("/analyze-image-base64")
async def analyze_image_base64(request: Base64ImageRequest):
    try:
        logger.info("Received request to analyze base64 image")

        # Decode base64 image directly into bytes
        base64_image = request.base64_image

        # Initialize the analyzer
        analyzer = AnalyzeImage(provider=request.provider, vision_model=request.vision_model)

        # Analyze the image in memory
        result = analyzer.analyze_image_base64(base64_image)

        logger.info("Successfully analyzed base64 image")
        return {"detailed_appearance": result}

    except Exception as e:
        logger.error(f"Error analyzing base64 image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error analyzing base64 image")
    

@router.post("/generate-story-text")
async def generate_story_text(request: ComicRequest):
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

    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error generating comic: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating the comic. Please try again later."
        )

@router.post("/generate-image")
async def generate_image(request: ImageRequest):
    try:
        logger.info("Received request to generate image")

        image_generator = ImageGenerator(
            provider=request.provider,
            img_model=request.image_model,
            model_resolution=request.model_resolution
        )

        # Convert the style to a description
        try:
            style_description = request.style.value
        except KeyError:
            logger.error(f"Invalid style: {request.style}")
            raise HTTPException(
                status_code=400,
                detail="The selected style is not supported. Please choose a valid style."
            )

        # Prepare the JSON prompt
        prompt = json.dumps({
            "image_prompt": request.image_prompt,
            "entities": [entity.dict() for entity in request.entities],
            "style": style_description,
        })

        logger.debug(f"Final prompt: {prompt}")

        # Because we only moderate if provider == "openai", call moderate_content:
        if image_generator.moderate_content(prompt):
            logger.warning("Prompt flagged by the OpenAI moderation.")
            raise HTTPException(
                status_code=400,
                detail="The prompt contains inappropriate or prohibited content. Please modify and try again."
            )

        image_url = image_generator.generate_image(prompt)
        logger.info(f"Image generation completed with provider {request.provider}")
        return image_url

    except BadRequestError as ve:
        # This includes content policy violations and other user-facing errors
        logger.warning(f"Content policy violation or validation error: {ve}")
        raise HTTPException(
            status_code=400,
            detail=str("Content policy violation or validation error")
        )   
    except ValueError as ve:
        # This includes content policy violations and other user-facing errors
        logger.warning(f"Content policy violation or validation error: {ve}")
        raise HTTPException(
            status_code=400,
            detail=str("Content policy violation or validation error")
        )
    except RuntimeError as re:
        logger.error(f"Unexpected runtime error generating image: {re}", exc_info=False)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating the image. Please try again later."
        )

    except Exception as e:
        logger.error(f"Unexpected error generating image: {e}", exc_info=False)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again later."
        )

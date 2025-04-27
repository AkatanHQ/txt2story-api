# File: app/routers/comic_routers.py

from fastapi import APIRouter, HTTPException
from openai import BadRequestError, OpenAIError
from app.services.story_json_builder import StoryJsonBuilder
from app.services.image_generator import ImageGenerator
from app.utils.logger import logger
from app.schemas.comic_schemas import EntityRequest, ComicRequest, ImageRequest, ImageUrlRequest, Base64ImageRequest
from app.utils.enums import StyleDescription
import json
import base64
from app.services.analyze_image import AnalyzeImage

router = APIRouter()

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
        image_base64 = request.image_base64

        # Initialize the analyzer
        analyzer = AnalyzeImage(provider=request.provider, vision_model=request.vision_model)

        # Analyze the image in memory
        result = analyzer.analyze_image_base64(image_base64)

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
            prompt=request.prompt
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
    """
    Generate an image with GPT-Image-1 (OpenAI or Azure). Supports reference
    pictures stored in `entities[*].dreambooth_url`.
    """
    try:
        logger.info("Received request to generate image")

        img_gen = ImageGenerator(
            provider=request.provider,
            img_model=request.image_model,
            size=request.size,
            quality=request.quality,
        )
        
        image_b64 = img_gen.generate_image(
            request.image_prompt,
            entities=[e.model_dump() for e in request.entities],
        )

        return {"image_b64": str(image_b64)}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected server error", exc_info=True)
        raise HTTPException(500, detail="Image generation failed") from exc

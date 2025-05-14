# app/controllers/comic_controller.py

from fastapi import HTTPException
from app.utils.logger import logger
from app.services.analyze_image import AnalyzeImage
from app.schemas.comic_schemas import ComicRequest, ImageRequest, ImageUrlRequest, Base64ImageRequest


async def analyze_image_base64_controller(request: Base64ImageRequest):
    try:
        logger.info("Analyzing base64 image")
        analyzer = AnalyzeImage(provider=request.provider, vision_model=request.vision_model)
        result = analyzer.analyze_image_base64(request.image_base64)
        return {"detailed_appearance": result}
    except Exception as e:
        logger.error(f"Error analyzing base64 image: {e}", exc_info=True)
        raise HTTPException(500, detail="Error analyzing base64 image")

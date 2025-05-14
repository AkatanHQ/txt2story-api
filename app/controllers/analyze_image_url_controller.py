from fastapi import HTTPException
from app.utils.logger import logger
from app.services.analyze_image import AnalyzeImage
from app.schemas.comic_schemas import ComicRequest, ImageRequest, ImageUrlRequest, Base64ImageRequest


async def analyze_image_url_controller(request: ImageUrlRequest):
    try:
        logger.info(f"Analyzing image from URL: {request.image_url}")
        analyzer = AnalyzeImage(provider=request.provider, vision_model=request.vision_model)
        result = analyzer.analyze_image_url(str(request.image_url))
        return {"detailed_appearance": result}
    except Exception as e:
        logger.error(f"Error analyzing image from URL: {e}", exc_info=True)
        raise HTTPException(500, detail="Error analyzing image from URL")

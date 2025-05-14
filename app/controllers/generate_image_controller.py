from fastapi import HTTPException
from app.services.image_generator import ImageGenerator
from app.utils.logger import logger
from app.schemas.comic_schemas import ComicRequest, ImageRequest, ImageUrlRequest, Base64ImageRequest

async def generate_image_controller(request: ImageRequest):
    try:
        logger.info("Generating image")
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
    except Exception as exc:
        logger.error("Unexpected server error", exc_info=True)
        raise HTTPException(500, detail="Image generation failed") from exc

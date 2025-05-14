from fastapi import APIRouter
from app.controllers.analyze_image_url_controller import analyze_image_url_controller
from app.controllers.analyze_image_base64_controller import analyze_image_base64_controller
from app.controllers.generate_story_text_controller import generate_story_text_controller
from app.controllers.generate_image_controller import generate_image_controller

from app.schemas.comic_schemas import ComicRequest, ImageRequest, ImageUrlRequest, Base64ImageRequest

from app.features.story_chat.controller import handle_chat
from app.features.story_chat.core.schemas import ChatRequest, ChatResponse  # Assuming you moved the schemas
 

router = APIRouter()

@router.post("/analyze-image-url")
async def analyze_image_url(request: ImageUrlRequest):
    return await analyze_image_url_controller(request)

@router.post("/analyze-image-base64")
async def analyze_image_base64(request: Base64ImageRequest):
    return await analyze_image_base64_controller(request)

@router.post("/generate-story-text")
async def generate_story_text(request: ComicRequest):
    return await generate_story_text_controller(request)

@router.post("/generate-image")
async def generate_image(request: ImageRequest):
    return await generate_image_controller(request)

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    return await handle_chat(req)

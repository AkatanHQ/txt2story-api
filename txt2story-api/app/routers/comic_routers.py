from fastapi import APIRouter, Depends, HTTPException
from app.schemas.comic_schemas import ComicRequest, ImageRequest
from app.services.story_json_builder import StoryJsonBuilder
from app.services.image_generator import ImageGenerator
from app.services.image_generator import ImageGenerator
from app.schemas.comic_schemas import ImageRequest
from fastapi.responses import StreamingResponse
from io import BytesIO

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

@router.post("/api/generate_image")
async def generate_image(
    request: ImageRequest,
    image_model: str = "dall-e-3",
    model_resolution: str = "1024x1024"
):
    """
    Endpoint to generate an image based on the provided entities, image prompt, and model.
    Streams the image back to the client.
    """
    try:
        # Initialize the image generator with the specified model and resolution
        image_generator = ImageGenerator(img_model=image_model, model_resolution=model_resolution)

        # Use the prompt to generate an image
        generated_image = image_generator.generate_image(request.image_prompt)

        # Save the image into a BytesIO buffer
        img_buffer = BytesIO()
        generated_image.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        # Stream the image back to the client
        return StreamingResponse(img_buffer, media_type="image/png")
    except Exception as e:
        # Handle errors gracefully and log the exception
        print(f"Error generating image with model {image_model} and resolution {model_resolution}: {e}")
        raise HTTPException(status_code=500, detail="Error generating image.")
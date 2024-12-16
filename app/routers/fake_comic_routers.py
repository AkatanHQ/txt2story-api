from fastapi import APIRouter, Depends, HTTPException
from app.services.story_json_builder import StoryJsonBuilder
from app.services.image_generator import ImageGenerator
from app.utils.logger import logger
from app.schemas.comic_schemas import EntityRequest, ComicRequest, ImageRequest
from app.utils.enums import StyleDescription
import json
import uuid

router = APIRouter()

@router.post("/api/generate-comic-book")
async def generate_comic(request: ComicRequest):
    try:
        logger.info("Received request to generate comic fake")
        logger.info(f"Request details for fake: {request}")

        data = {
  "metadata": {
    "title": "The Lantern of Sylvestria",
    "genre": "Fantasy Adventure",
    "keywords": [
      "magical quest",
      "friendship",
      "courage",
      "self-discovery",
      "light vs darkness"
    ]
  },
  "scenes": [
    {
      "index": 0,
      "text": "In a distant land, nestled between towering snow-capped peaks and lush green valleys, lay the Kingdom of Sylvestria. The kingdom was renowned for its breathtaking landscapes and thriving wildlife. Every year, townsfolk gathered in the meadows to celebrate the Festival of Light, a joyous event that filled the skies with lanterns, symbolizing their dreams and hopes. On the eve of the festival, Elara, a young villager with a spirit as adventurous as her fiery red hair, stood at the edge of the village, looking out over the shimmering river. Her heart yearned for adventure beyond the confines of her quaint home.",
      "image": {
        "prompt": "A distant land with snow-capped peaks, lush green valleys, and a young girl with fiery red hair standing at the edge of a village during a festival with lanterns in the sky.",
        "url": "",
        "signed_url": ""
      }
    }
  ],
  "entities": [
    {
      "id": 0,
      "name": "Elara",
      "appearance": "A young villager with a spirit as adventurous as her fiery red hair, standing at the edge of the village looking out over the shimmering river.",
      "detailed_appearance": "Elara is a young villager with striking fiery red hair that cascades in soft waves down to her shoulders. Her bright green eyes gleam with a sense of adventure as she gazes towards the shimmering river. She wears a practical yet charming outfit: a tunic made of light, woven linen in earthy tones of brown and forest green, cinched at the waist with a braided leather belt. Her trousers are sturdy and fitted, allowing for ease of movement, while her bare feet connect her directly to the earth, conveying a sense of freedom. A simple silver pendant shaped like a compass hangs around her neck, glinting in the sunlight, symbolizing her adventurous spirit."
    },
    {
      "id": 1,
      "name": "Festival of Light",
      "appearance": "A joyous event where townsfolk filled the skies with lanterns, symbolizing dreams and hopes.",
      "detailed_appearance": "The Festival of Light is a vibrant tapestry of colors, where townsfolk don flowing garments in rich hues of gold, deep blue, and soft white, reminiscent of starlight and moonbeams. Their outfits are adorned with intricate patterns that shimmer like the glow of lanterns. Each person carries delicately crafted lanterns, made of translucent paper and bamboo, featuring various designs that capture the essence of dreams and aspirations. In the air, a gentle breeze sends a flurry of glowing lanterns drifting upwards, their warm glow illuminating smiling faces. Notable features include radiant smiles, twinkling eyes, and the soft glow of lantern light reflecting off their joyful expressions."
    }
  ]
}

        return data

    except Exception as e:
        logger.error(f"Error generating comic: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating comic.")

@router.post("/api/generate-image")
async def generate_image(request: ImageRequest):
    try:
        generated_image_url = "https://scontent-cph2-1.xx.fbcdn.net/v/t1.6435-9/122659566_2085416741594479_7361004250940575709_n.jpg?_nc_cat=103&ccb=1-7&_nc_sid=cc71e4&_nc_ohc=hmGAik-lepUQ7kNvgEt0K6D&_nc_zt=23&_nc_ht=scontent-cph2-1.xx&_nc_gid=A_gM-LHJcONzN1X-h9v3R3i&oh=00_AYBYvCqsUNF_Mxd1zLvZJMyqCucv70LsO--JnCEBUU_3aw&oe=6786B55F"

        return generated_image_url

    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.error(f"Error generating image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating image.")

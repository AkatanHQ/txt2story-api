from fastapi import APIRouter, Depends, HTTPException
from app.services.story_json_builder import StoryJsonBuilder
from app.services.image_generator import ImageGenerator
from app.utils.logger import logger
from app.schemas.comic_schemas import EntityRequest, ComicRequest, ImageRequest
from app.utils.enums import StyleDescription
import json
import uuid
import time


router = APIRouter()

@router.post("/generate-story-text")
async def generate_comic(request: ComicRequest):
    try:
        logger.info("Received request to generate comic fake")
        logger.info(f"Request details for fake: {request}")
        unique_id = str(uuid.uuid4())
        logger.info(f"Fake waiting 5 sec")
        time.sleep(5)


        data = {
  "metadata": {
    "title": f"The Lantern of Sylvestria_{unique_id}",
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
    },
    {
      "index": 1,
      "text": "Text for 2",
      "image": {
        "prompt": "prompt ofr 2 with lanterns in the sky.",
        "url": "",
        "signed_url": ""
      }
    },
    {
      "index": 2,
      "text": "Text for 3",
      "image": {
        "prompt": "prompt ofr 3 with lanterns in the sky.",
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

@router.post("/generate-image")
async def generate_image(request: ImageRequest):
    try:
        generated_image_url = "https://www.geeky-gadgets.com/wp-content/uploads/2023/10/DallE-3-vs-DallE-2-AI-image-creation-compared.webp"
        logger.info(f"Fake waiting 5 sec")
        time.sleep(5)

        return generated_image_url

    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.error(f"Error generating image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating image.")

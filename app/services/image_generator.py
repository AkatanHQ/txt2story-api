from openai import OpenAI
import requests
from io import BytesIO
from PIL import Image
import os
from dotenv import load_dotenv
from app.utils.logger import logger

load_dotenv()

class ImageGenerator:
    def __init__(self, img_model='dall-e-3', model_resolution="1024x1024"):
        try:
            logger.info("Initializing ImageGenerator")
            self.img_model = img_model
            self.model_resolution = model_resolution
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            if not self.openai_api_key:
                raise ValueError("OpenAI API key is missing.")
        except Exception as e:
            logger.error(f"Failed to initialize ImageGenerator: {e}", exc_info=True)
            raise RuntimeError("Initialization error in ImageGenerator")

    def text_to_image_openai(self, prompt):
        try:
            logger.info("Generating image via OpenAI")
            logger.debug(f"Prompt: {prompt}")

            client = OpenAI(api_key=self.openai_api_key)
            response = client.images.generate(
                model=self.img_model,
                prompt=prompt,
                quality="standard",
                size=self.model_resolution,
                n=1,
            )
            logger.debug(f"Image generation response: {response}")

            image_url = response.data[0].url
            image_response = requests.get(image_url)
            img = Image.open(BytesIO(image_response.content))

            return img
        except Exception as e:
            logger.error(f"Error in text_to_image_openai: {e}", exc_info=True)
            raise RuntimeError("Error generating image via OpenAI API")

    def generate_image(self, prompt):
        try:
            logger.info("Generating image")
            if "dall-e" in self.img_model:
                return self.text_to_image_openai(prompt)
            else:
                raise ValueError(f"Unsupported model: {self.img_model}")
        except ValueError as ve:
            logger.warning(f"Validation error in image generation: {ve}")
            raise ve
        except Exception as e:
            logger.error(f"Error generating image: {e}", exc_info=True)
            raise RuntimeError("Error in image generation")

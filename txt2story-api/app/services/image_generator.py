from openai import OpenAI
import requests
from io import BytesIO
from PIL import Image
import os
from dotenv import load_dotenv

load_dotenv()

class ImageGenerator:
    def __init__(self, img_model='dall-e-3', model_resolution="1024x1024"):
        self.img_model = img_model
        self.model_resolution = model_resolution
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

    def text_to_image_openai(self, prompt):
        # Initialize OpenAI client
        client = OpenAI(api_key=self.openai_api_key)

        # Generate image from OpenAI's API
        response = client.images.generate(
            model=self.img_model,
            prompt=prompt,
            quality="standard",
            size=self.model_resolution,
            n=1,
        )

        image_url = response.data[0].url
        image_response = requests.get(image_url)
        img = Image.open(BytesIO(image_response.content))

        return img

    def generate_image(self, prompt):
        # Verbose logging to show the selected model
        print(f"Selected model: {self.img_model}")

        # Image generation logic based on the img_model
        if "dall-e" in self.img_model:
            return self.text_to_image_openai(prompt)
        else:
            raise ValueError(f"Unsupported model: {self.img_model}")
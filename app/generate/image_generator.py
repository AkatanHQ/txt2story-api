from openai import OpenAI
import requests
from io import BytesIO
import io
import random
import warnings
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
import os
from dotenv import load_dotenv

load_dotenv()

class ImageGenerator:
    def __init__(self, img_model='dall-e-2', model_resolution="1024x1024"):
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
            size=self.model_resolution,
            n=1,
        )

        image_url = response.data[0].url
        image_response = requests.get(image_url)
        img = Image.open(BytesIO(image_response.content))

        return img

    def text_to_image_stabilityAI(self, prompt):
        os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'
        seed = random.randint(0, 1000000000)

        # Set up Stability API key from environment variable
        stability_api = client.StabilityInference(
            key=os.getenv('STABILITY_KEY'),  # API Key reference
            verbose=True,  # Print debug messages
            engine="stable-diffusion-xl-1024-v1-0", # Set the engine to use for generation.
        )

        # Set up generation parameters
        answers = stability_api.generate(
            prompt=prompt,
            seed=seed,
            steps=30,
            cfg_scale=8.0,
            width=1024,
            height=1024,
            sampler=generation.SAMPLER_K_DPMPP_2M
        )

        # Check for safety filters and display generated image
        for resp in answers:
            for artifact in resp.artifacts:
                if artifact.finish_reason == generation.FILTER:
                    warnings.warn(
                        "Your request activated the API's safety filters and could not be processed."
                        "Please modify the prompt and try again.")
                if artifact.type == generation.ARTIFACT_IMAGE:
                    img = Image.open(io.BytesIO(artifact.binary))
                    return img

    def generate_image(self, prompt):
        # Verbose logging to show the selected model
        print(f"Selected model: {self.img_model}")

        # Image generation logic based on the img_model
        if "dall-e" in self.img_model:
            return self.text_to_image_openai(prompt)
        elif "stability" in self.img_model:
            return self.text_to_image_stabilityAI(prompt)
        else:
            raise ValueError(f"Unsupported model: {self.img_model}")

# Example usage:
# generator = ImageGenerator(img_model='dall-e-2')
# image = generator.generate_image("A beautiful landscape painting of mountains during sunset")
# image.show()

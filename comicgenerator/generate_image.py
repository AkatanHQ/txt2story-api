import os
import openai
import requests
from io import BytesIO
import io
import random
import logging
import warnings
from PIL import Image
from dotenv import load_dotenv
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation

from dotenv import load_dotenv
load_dotenv()

def text_to_image_dalle3(prompt):
    # Set up OpenAI API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    openai.api_key = api_key

    print("Using OpenAI")
    # Initialize 
    client = openai.OpenAI()

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    # Fetch the image using the URL
    image_response = requests.get(image_url)
    
    # Open the image using PIL
    img = Image.open(BytesIO(image_response.content))

    return img


def text_to_image_stabilityAI(prompt):
    os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'

    # Configure logging
    logging.basicConfig(filename='generation_log.log', level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s')

    seed = random.randint(0, 1000000000)

    # Set up our connection to the API.
    stability_api = client.StabilityInference(
        key=os.environ['STABILITY_KEY'], # API Key reference.
        verbose=True, # Print debug messages.
        engine="stable-diffusion-xl-1024-v1-0", # Set the engine to use for generation.
    )


    # Set up our initial generation parameters.
    answers = stability_api.generate(
        prompt=prompt,
        seed=seed,
        steps=30,
        cfg_scale=8.0,
        width=1024,
        height=1024,
        sampler=generation.SAMPLER_K_DPMPP_2M
    )

    image_generated = False  # Flag to check if image was generated

    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                warnings.warn(
                    "Your request activated the API's safety filters and could not be processed."
                    "Please modify the prompt and try again."
                )
                logging.warning("Prompt activated safety filter: %s", prompt)
            if artifact.type == generation.ARTIFACT_IMAGE:
                img = Image.open(io.BytesIO(artifact.binary))
                image_generated = True
                return img

    if not image_generated:
        logging.error("No image was generated for prompt: %s", prompt)
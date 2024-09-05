import os
import openai
import requests
from io import BytesIO
import io
import random
import logging
import warnings
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

def text_to_image_openai(prompt, model="dall-e-2"):
    print(f"Using OpenAI with model: {model}")
    # Set up OpenAI API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    openai.api_key = api_key
    
    # Initialize 
    client = openai.OpenAI()

    response = client.images.generate(
        model=model,
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    image_response = requests.get(image_url)
    img = Image.open(BytesIO(image_response.content))

    return img


# Function to generate image using StabilityAI
def text_to_image_stabilityAI(prompt, model='stable-diffusion-xl-1024-v1-0'):
    print("Using StabilityAI")
    os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'
    
    # Configure logging
    logging.basicConfig(filename='generation_log.log', level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s')

    seed = random.randint(0, 1000000000)
    
    # Set up connection to Stability API
    stability_api = client.StabilityInference(
        key=os.getenv('STABILITY_KEY'),
        verbose=True, 
        engine=model, 
    )
    
    # Generate image
    answers = stability_api.generate(
        prompt=prompt,
        seed=seed,
        steps=30,
        cfg_scale=8.0,
        width=1024,
        height=1024,
        sampler=generation.SAMPLER_K_DPMPP_2M
    )
    
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                warnings.warn("Safety filter activated. Modify the prompt.")
                logging.warning("Prompt activated safety filter: %s", prompt)
            if artifact.type == generation.ARTIFACT_IMAGE:
                img = Image.open(io.BytesIO(artifact.binary))
                return img

    logging.error("No image generated for prompt: %s", prompt)
    return None

# Factory function to choose the model dynamically based on environment variables
def get_image_generator():
    model_provider = os.getenv("MODEL_PROVIDER", "openai").lower()
    model_name = os.getenv("MODEL_NAME", "dall-e-2")

    if model_provider == "openai":
        return lambda prompt: text_to_image_openai(prompt, model_name)
    elif model_provider == "stabilityai":
        return lambda prompt: text_to_image_stabilityAI(prompt, model_name) 
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")
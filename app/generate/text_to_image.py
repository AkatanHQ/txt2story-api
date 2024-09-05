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
    os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'

    seed = random.randint(0, 1000000000)

    # Set up our connection to the API.
    stability_api = client.StabilityInference(
        key=os.getenv('STABILITY_KEY'), # API Key reference.
        verbose=True, # Print debug messages.
        engine=model, # Set the engine to use for generation.
        # Check out the following link for a list of available engines: https://platform.stability.ai/docs/features/api-parameters#engine
    )
    # Set up our initial generation parameters.
    answers = stability_api.generate(
        # prompt="rocket ship launching from forest with flower garden under a blue sky, masterful, ghibli",
        prompt=prompt,
        seed=seed, # If a seed is provided, the resulting generated image will be deterministic.
                        # What this means is that as long as all generation parameters remain the same, you can always recall the same image simply by generating it again.
                        # Note: This isn't quite the case for CLIP Guided generations, which we tackle in the CLIP Guidance documentation.
        steps=30, # Amount of inference steps performed on image generation. Defaults to 30.
        cfg_scale=8.0, # Influences how strongly your generation is guided to match your prompt.
                    # Setting this value higher increases the strength in which it tries to match your prompt.
                    # Defaults to 7.0 if not specified.
        width=1024, # Generation width, defaults to 1024 if not included.
        height=1024, # Generation height, defaults to 1024 if not included.
        sampler=generation.SAMPLER_K_DPMPP_2M # Choose which sampler we want to denoise our generation with.
                                                    # Defaults to k_dpmpp_2m if not specified. Clip Guidance only supports ancestral samplers.
                                                    # (Available Samplers: ddim, plms, k_euler, k_euler_ancestral, k_heun, k_dpm_2, k_dpm_2_ancestral, k_dpmpp_2s_ancestral, k_lms, k_dpmpp_2m, k_dpmpp_sde)
    )

    # Set up our warning to print to the console if the adult content classifier is tripped.
    # If adult content classifier is not tripped, display generated image.
    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                warnings.warn(
                    "Your request activated the API's safety filters and could not be processed."
                    "Please modify the prompt and try again.")
            if artifact.type == generation.ARTIFACT_IMAGE:
                global img
                img = Image.open(io.BytesIO(artifact.binary))
                return img 



def get_image_generator():
    # Dictionary to store valid model names for each provider
    valid_models = {
        "openai": ["dall-e-2", "dall-e-3"],
        "stabilityai": ["stable-diffusion-xl-1024-v1-0"]
    }

    model_provider = os.getenv("MODEL_PROVIDER", "openai").lower()
    model_name = os.getenv("MODEL_NAME", "").lower()

    # Set default models if MODEL_NAME is empty
    if model_provider == "openai":
        model_name = model_name or "dall-e-3"
    elif model_provider == "stabilityai":
        model_name = model_name or "stable-diffusion-xl-1024-v1-0"
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")

    # Validate the model name against the list of valid models
    if model_name not in valid_models.get(model_provider, []):
        raise ValueError(f"Model '{model_name}' not found for provider '{model_provider}'.")

    # Image generation logic
    if model_provider == "openai":
        return lambda prompt: text_to_image_openai(prompt, model_name)
    elif model_provider == "stabilityai":
        return lambda prompt: text_to_image_stabilityAI(prompt, model_name)
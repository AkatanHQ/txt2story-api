import openai
import requests
from io import BytesIO
import io
import random
import warnings
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from app.utils.config_util import load_config, get_env_variable

# Load environment variables from the centralized config file
config = load_config()

# Function to generate image using OpenAI
def text_to_image_openai(prompt, model="dall-e-2"):
    model_resolution = config['environment'].get('model_resolution', '1024x1024').lower().strip()

    api_key = get_env_variable("OPENAI_API_KEY")
    openai.api_key = api_key
    
    # Initialize OpenAI client
    client = openai.OpenAI()
    
    # Generate image from OpenAI's API
    response = client.images.generate(
        model=model,
        prompt=prompt,
        size=model_resolution,
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

    # Set up Stability API key from environment variable using config_util
    stability_api = client.StabilityInference(
        key=get_env_variable('STABILITY_KEY'), # API Key reference
        verbose=True, # Print debug messages
        engine=model, # Set the engine to use for generation
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

# Function to generate image using Flux model
def text_to_image_flux(prompt, model='black-forest-labs/FLUX.1-schnell'):
    pipe = FluxPipeline.from_pretrained(model, torch_dtype=torch.bfloat16)
    image = pipe(
        prompt,
        guidance_scale=0.0,
        num_inference_steps=2,
        max_sequence_length=64,
        generator=torch.Generator("cpu").manual_seed(0)
    ).images[0]
    
    return image


# Function to select the image generation method based on config
def get_image_generator():


    # Get values from the config
    model_provider = config['environment'].get('model_provider', 'openai').lower().strip()
    model_name = config['environment'].get('model_name', '').lower().strip()

    # Verbose logging to show the selected provider and model
    print(f"Selected provider: {model_provider}, model: {model_name or 'default model for provider'}")

    # Image generation logic based on the provider
    if model_provider == "openai":
        return lambda prompt, model=model_name or "dall-e-2": text_to_image_openai(prompt, model)
    elif model_provider == "stabilityai":
        return lambda prompt, model=model_name or "stable-diffusion-xl-1024-v1-0": text_to_image_stabilityAI(prompt, model)
    elif model_provider == "flux":
        return lambda prompt, model=model_name or "black-forest-labs/FLUX.1-schnell": text_to_image_flux(prompt, model)
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")

import os
import openai
from PIL import Image
import requests
from io import BytesIO

# Set up OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

def text_to_image(prompt):
    # Call the OpenAI API to generate an image from a text prompt
    response = openai.Image.create(
        prompt=prompt,
        n=1,  # Number of images to generate
        size="1024x1024"  # Size of the generated image
    )

    # Get the URL of the generated image
    image_url = response['data'][0]['url']
    
    # Fetch the image from the URL
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    
    return img

def edit_image(input_image_path, prompt, output_image_name):
    # Since DALL·E does not support direct image editing, we simulate it with a detailed prompt
    # Optionally, include details from the original image
    detailed_prompt = f"{prompt}, inspired by the original image."

    # Generate a new image using the DALL·E API
    img = text_to_image(detailed_prompt)
    
    # Save the generated image
    img.save(output_image_name + ".png")

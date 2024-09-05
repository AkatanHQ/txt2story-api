import sys
import os

# Add the `app` directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now you can import from the `generate` module
from generate.text_to_image import *
from PIL import Image

# Test prompt for StabilityAI
test_prompt = "a futuristic city skyline at sunset with flying cars, photorealistic, vibrant colors"

# Generate image using StabilityAI
def test_stabilityai_image_generation():
    try:
        # Get the image generator function for StabilityAI
        image_generator = get_image_generator()

        # Generate an image based on the test prompt
        generated_image = image_generator(test_prompt)

        if generated_image:
            print("Image generated successfully!")
            
            # Display the image using PIL's built-in viewer
            generated_image.show()
        else:
            print("Failed to generate image.")
    except Exception as e:
        print(f"Error during image generation: {e}")

# Run the test
test_stabilityai_image_generation()

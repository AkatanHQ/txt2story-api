import sys
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.analyze_image import AnalyzeImage  # Adjust path if needed

# Initialize the AnalyzeImage class
analyzer = AnalyzeImage(provider="openai", vision_model="gpt-4o")

# Provide an image URL
image_url = "https://vancouvergold.ca/wp-content/uploads/2013/11/person2-500x500.jpg"  # Replace with a real image URL
api_key = os.getenv("OPENAI_API_KEY")

try:
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe the person's appearance, including general details such as hair, clothing, face-shape, accesoires, and facial expression, without making assumptions about their identity. Always include the color, including skin-color"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        },
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    print(response.choices[0])
    result = response.choices[0]
    print("\n=== Image Analysis Result ===")
    print(result)
except Exception as e:
    print(f"Error analyzing image: {e}")
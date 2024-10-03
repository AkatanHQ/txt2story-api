
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
# Initialize OpenAI client

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def text_to_image_openai(prompt):
        # Generate image from OpenAI's API
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            quality="standard",
            size="1024x1024",
            n=1,
        )

        image_url = response.data[0].url
        print(image_url)
        image_response = requests.get(image_url)
        img = Image.open(BytesIO(image_response.content))

        return img

style = "in a classic comic book style, similar to the original Tintin illustrations, characterized by clean outlines, bright primary colors, flat shading, and expressive but not overly detailed features."

same = "characters, expressions, and style should match previous images closely. Maintain the same color palettes, facial features, and level of detail as used in the earlier illustrations."

prompt1 = "\"A caucasian man with blond hair, around 6 feet tall, with strikingly defined six-pack abs. His blond hair is short and tousled, matching his adventurous spirit and youthful appearance. He has bright green eyes that reflect curiosity and determination. He is dressed in a casual white t-shirt, slightly stained with mud from the journey, and cargo shorts that allow for easy movement. His build is muscular, emphasizing his active lifestyle. His posture is upright and alert, expressing both readiness and excitement.\" and \"An African-American man of medium height, about 5'9\", with a well-groomed black beard and short black hair. His eyes are a deep, warm brown, filled with anticipation and nervous excitement. Dressed in a practical, dark green hoodie and rugged hiking trousers, he gives off a vibe of preparedness and adventure. His posture is slightly hunched forward in cautious intrigue, as if about to explore something unknown.\" They stand at the edge of a dense forest, trees towering around them, leaves rustling gently. Sunlight filters through the branches, casting dappled patterns on the forest floor. Birds are chirping softly, and a soft breeze rustles the foliage." + style

prompt2 = "\"A caucasian man with blond hair, around 6 feet tall, with strikingly defined six-pack abs. His blond hair is short and tousled, matching his adventurous spirit and youthful appearance. He has bright green eyes that reflect curiosity and determination. He is dressed in a casual white t-shirt, slightly stained with mud from the journey, and cargo shorts that allow for easy movement. His build is muscular, emphasizing his active lifestyle. His posture is leaning forward with wide-eyed amazement, as if in awe of a revelation.\" and \"An African-American man of medium height, about 5'9\", with a well-groomed black beard and short black hair. His eyes are a deep, warm brown, sparkling with excitement and a sense of wonder. Dressed in a practical, dark green hoodie and rugged hiking trousers, he now exudes fascination and enthusiasm. His posture is slightly crouched, peering into an opening with a look of discovery.\" The ancient tree with glowing leaves stands tall, its bark cracking open to reveal a hidden pathway. The inside is bathed in an eerie, soft blue glow leading to the mouth of an underground cave, where sparkling crystals illuminate the space, creating a breathtaking, otherworldly atmosphere." + style + same


text_to_image_openai(prompt1)
text_to_image_openai(prompt2)
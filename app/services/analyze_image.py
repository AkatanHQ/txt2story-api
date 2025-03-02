import os
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
from app.utils.logger import logger
import base64

class AnalyzeImage:
    def __init__(self, provider="openai", vision_model="gpt-4o"):
        """
        A class responsible for analyzing images using GPT-4 vision capabilities.
        """
        try:
            logger.info("Initializing AnalyzeImage")
            self.provider = provider.lower()
            self.vision_model = vision_model

            if self.provider == "openai":
                load_dotenv()
                self.api_key = os.getenv("OPENAI_API_KEY")
                if not self.api_key:
                    raise ValueError("OpenAI API key is missing.")
                self.client = OpenAI(api_key=self.api_key)
            else:
                raise ValueError(f"Provider '{self.provider}' does not support image analysis.")

        except Exception as e:
            logger.error(f"Failed to initialize AnalyzeImage: {e}", exc_info=True)
            raise RuntimeError("Initialization error in AnalyzeImage")
    
    def analyze_image_base64(self, base64_image: str) -> str:
        try:
            logger.info("Analyzing base64 image using GPT-4 vision") 
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe the person's appearance, including general details such as hair, clothing, face-shape, accesoires, and facial expression, without making assumptions about their identity. Always include the color, including skin-color"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/webp;base64,{base64_image}"  
                                },
                            },
                        ],
                    }
                ],
                max_tokens=300,
            )

            print(response.choices[0])
            result = response.choices[0].message.content
            logger.info("Image analysis completed successfully")
            return result
        except OpenAIError as oe:
            logger.error(f"OpenAI API error during image analysis: {oe}", exc_info=True)
            raise RuntimeError("Error analyzing image with OpenAI API")
        except Exception as e:
            logger.error(f"Unexpected error analyzing image: {e}", exc_info=True)
            raise RuntimeError("Failed to analyze image")

    def analyze_image_file(self, image_path: str) -> str:
        try:
            logger.info("Analyzing local image using GPT-4 vision")
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe the person's appearance, including general details such as hair, clothing, face-shape, accesoires, and facial expression, without making assumptions about their identity. Always include the color, including skin-color"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/webp;base64,{base64_image}"  
                                },
                            },
                        ],
                    }
                ],
                max_tokens=300,
            )

            print(response.choices[0])
            result = response.choices[0].message.content
            logger.info("Image analysis completed successfully")
            return result
        except OpenAIError as oe:
            logger.error(f"OpenAI API error during image analysis: {oe}", exc_info=True)
            raise RuntimeError("Error analyzing image with OpenAI API")
        except Exception as e:
            logger.error(f"Unexpected error analyzing image: {e}", exc_info=True)
            raise RuntimeError("Failed to analyze image")

    def analyze_image_url(self, image_url: str) -> str:
        try:
            logger.info(f"Analyzing image from URL: {image_url}")

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe the person's appearance, including general details such as hair, clothing, face-shape, accesoires, and facial expression, without making assumptions about their identity. Always include the color, including skin-color"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url  
                                },
                            },
                        ],
                    }
                ],
                max_tokens=300,
            )

            print(response.choices[0])

            result = response.choices[0].message.content
            logger.info("Image analysis completed successfully")
            return result
        except OpenAIError as oe:
            logger.error(f"OpenAI API error during image analysis: {oe}", exc_info=True)
            raise RuntimeError("Error analyzing image with OpenAI API")
        except Exception as e:
            logger.error(f"Unexpected error analyzing image: {e}", exc_info=True)
            raise RuntimeError("Failed to analyze image")
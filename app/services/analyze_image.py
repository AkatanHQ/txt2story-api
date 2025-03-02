import time
import json
from openai import OpenAI, AzureOpenAI, OpenAIError, BadRequestError
import os
from dotenv import load_dotenv
from app.utils.logger import logger
import ast

class AnalyzeImage:
    def __init__(self, provider="openai", vision_model="gpt-4o"):
        """
        A separate class responsible for analyzing images using GPT-4 vision capabilities.
        """
        try:
            logger.info("Initializing AnalyzeImage")
            self.provider = provider.lower()
            self.vision_model = vision_model
            
            # For now, only OpenAI GPT-4 vision is assumed
            if self.provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY")
                if not self.api_key:
                    raise ValueError("OpenAI API key is missing.")
                self.client = OpenAI(api_key=self.api_key)
            else:
                raise ValueError(f"Provider '{self.provider}' does not support image analysis.")

        except Exception as e:
            logger.error(f"Failed to initialize AnalyzeImage: {e}", exc_info=True)
            raise RuntimeError("Initialization error in AnalyzeImage")

    def analyze_image_file(self, image_path: str) -> str:
        """
        Analyzes an image from a local file path using GPT-4 vision capabilities.

        :param image_path: The local path to the image file.
        :return: A textual description of the image.
        """
        try:
            logger.info("Analyzing local image using GPT-4 vision")
            with open(image_path, "rb") as image_file:
                file_content = image_file.read()

            return self._analyze_image_bytes(file_content)
        except Exception as e:
            logger.error(f"Error analyzing local image: {e}", exc_info=True)
            raise RuntimeError("Failed to analyze local image")
        
    def analyze_image_url(self, image_url: str) -> str:
        """
        Analyzes an image from a URL using GPT-4o vision capabilities.

        :param image_url: The publicly accessible image URL.
        :return: A textual description of the image.
        """
        try:
            logger.info(f"Analyzing image from URL: {image_url}")

            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {"role": "system", "content": "You are an AI that analyzes images and provides descriptions."},
                    {"role": "user", "content": "Describe the contents of this image in detail."},
                    {"role": "user", "content": {"type": "image_url", "image_url": image_url}},
                ]
            )

            analysis = response.choices[0].message.content
            logger.info("Image analysis completed successfully")
            return analysis
        except OpenAIError as oe:
            logger.error(f"OpenAI API error during image analysis: {oe}", exc_info=True)
            raise RuntimeError("Error analyzing image with OpenAI API")
        except Exception as e:
            logger.error(f"Unexpected error analyzing image: {e}", exc_info=True)
            raise RuntimeError("Failed to analyze image")


    def analyze_image_bytes(self, image_content: bytes) -> str:
        """
        Analyzes an image provided as raw bytes using GPT-4 vision capabilities.

        :param image_content: The raw byte content of an image.
        :return: A textual description of the image.
        """
        try:
            logger.info("Analyzing image bytes using GPT-4 vision")
            return self._analyze_image_bytes(image_content)
        except Exception as e:
            logger.error(f"Error analyzing image bytes: {e}", exc_info=True)
            raise RuntimeError("Failed to analyze image bytes")

    def _analyze_image_bytes(self, image_content: bytes) -> str:
        """
        Internal helper to send image bytes to GPT-4.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {"role": "system", "content": "You are an AI that analyzes images and provides descriptions."},
                    {"role": "user", "content": "Describe the contents of this image in detail."},
                    {"role": "user", "content": {"type": "image", "image": image_content}},
                ]
            )

            analysis = response.choices[0].message.content
            logger.info("Image analysis completed successfully")
            return analysis
        except OpenAIError as oe:
            logger.error(f"OpenAI API error during image analysis: {oe}", exc_info=True)
            raise RuntimeError("Error analyzing image with OpenAI API")
        except Exception as e:
            logger.error(f"Unexpected error analyzing image: {e}", exc_info=True)
            raise RuntimeError("Failed to analyze image")

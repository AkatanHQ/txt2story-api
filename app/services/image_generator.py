# File: app/services/image_generator.py

import json
from openai import OpenAI, AzureOpenAI, OpenAIError, BadRequestError
import os
from dotenv import load_dotenv
from app.utils.logger import logger
import ast

load_dotenv()

class ImageGenerator:
    def __init__(self, provider="azure", img_model="dall-e-3", model_resolution="1024x1024"):
        try:
            logger.info("Initializing ImageGenerator")
            self.provider = provider.lower()
            self.img_model = img_model
            self.model_resolution = model_resolution
            self.max_prompt_length = 4000

            if self.provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY")
                if not self.api_key:
                    raise ValueError("OpenAI API key is missing.")
                self.client = OpenAI(api_key=self.api_key)

            elif self.provider == "azure":
                self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
                self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
                if not self.azure_endpoint or not self.api_key:
                    raise ValueError("Azure OpenAI API key or endpoint is missing.")
                self.client = AzureOpenAI(
                    api_version="2024-02-01",
                    azure_endpoint=self.azure_endpoint,
                    api_key=self.api_key,
                )

            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        
        except Exception as e:
            logger.error(f"Failed to initialize ImageGenerator: {e}", exc_info=True)
            raise RuntimeError("Initialization error in ImageGenerator")

    def moderate_content(self, prompt):
        """
        Checks the prompt for inappropriate content using OpenAI's Moderation API.
        Only applies if provider == "openai".
        """
        try:
            logger.info("Moderating content in the prompt")
            
            if self.provider != "openai":
                logger.info("Skipping moderation for non-OpenAI provider.")
                return False
            
            response = self.client.moderations.create(input=prompt)
            flagged = response.results[0].flagged
            logger.debug(f"Moderation result: {response.results[0]}")
            return flagged
        
        except OpenAIError as oe:
            logger.error(f"OpenAI Moderation API error: {oe}", exc_info=True)
            raise RuntimeError("Error using Moderation API")
        except Exception as e:
            logger.error(f"Error moderating content: {e}", exc_info=True)
            raise RuntimeError("Error in content moderation")

    from openai import OpenAI, AzureOpenAI, OpenAIError, BadRequestError

    def text_to_image(self, prompt):
        try:
            # ... same as before ...
            
            if self.provider == "azure":
                response = self.client.images.generate(
                    model=self.img_model,
                    prompt=prompt,
                    n=1,
                )
                image_url = json.loads(response.model_dump_json())['data'][0]['url']
                return image_url

            elif self.provider == "openai":
                # Attempting generation
                response = self.client.images.generate(
                    model=self.img_model,
                    prompt=prompt,
                    quality="standard",
                    size=self.model_resolution,
                    n=1,
                )
                image_url = response.data[0].url
                return image_url
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
        except BadRequestError as bre:
            raise bre
        except ValueError as ve:
            raise ve
        except OpenAIError as oe:
            raise oe
        except Exception as e:
            raise e

    def manage_prompt_length(self, prompt: str) -> str:
        """
        Adjusts the prompt length based on the model's maximum allowed prompt length.
        """
        try:
            logger.info("Managing prompt length based on the model")
            max_length = 1000 if "dall-e-2" in self.img_model else 4000
            if len(prompt) > max_length:
                logger.info(f"Prompt exceeds max length ({max_length}). Reducing it.")
                return prompt[:max_length]
            else:
                logger.info("Prompt length is within the acceptable range. No reduction needed.")
                return prompt

        except Exception as e:
            logger.error(f"Error managing prompt length: {e}", exc_info=True)
            raise RuntimeError("Failed to manage prompt length")

    def generate_image(self, prompt: str) -> str:
        """
        Generates an image using the specified provider and manages the prompt length.
        Raises:
            ValueError: For user-facing or content policy errors.
            RuntimeError: For unexpected errors.
        """
        try:
            logger.info("Starting image generation process")
            adjusted_prompt = self.manage_prompt_length(prompt)
            return self.text_to_image(adjusted_prompt)
        except BadRequestError as bre:
            try:
                self.handle_bad_request_error(bre)
            except Exception as e:
                raise e
            raise bre
        except ValueError as ve:
            # Bubble up user-facing errors
            raise ve
        except Exception as e:
            logger.error(f"Error generating image: {e}", exc_info=False)
            raise e

    def handle_bad_request_error(self, bre):
        try:
            # Attempt to parse the error response into a dictionary
            error_details = ast.literal_eval(bre.args[0].split(" - ", 1)[1])
            print("Error Details:", error_details)
            
            # Extract error information
            error = error_details.get('error', {})
            inner_error = error.get('inner_error', {})
            message = error.get('message', "No message provided")
            content_filter_results = inner_error.get('content_filter_results', {})
            revised_prompt = inner_error.get('revised_prompt', None)

            # Log content policy violation specifics
            if error.get('code') == 'content_policy_violation':
                print(f"Content Policy Violation: {message}")
                print("Content Filter Results:", content_filter_results)
            
            # Handle the presence of revised_prompt
            if revised_prompt:
                print("Using revised prompt for retry:", revised_prompt)
                return self.text_to_image(revised_prompt)
            else:
                print("Revised prompt is not available.")
                # Handle cases where no revised prompt is provided
                raise ValueError("Revised prompt not available in the error details.")
        
        except (ValueError, KeyError, SyntaxError) as e:
            # Handle parsing or missing key errors gracefully
            print(f"Error while processing the bad request error: {e}")
            raise e

        except Exception as e:
            # Catch any other unexpected exceptions
            print(f"Unexpected error: {e}")
            raise e
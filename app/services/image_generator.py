from openai import OpenAI, OpenAIError
import os
from dotenv import load_dotenv
from app.utils.logger import logger

load_dotenv()

class ImageGenerator:
    def __init__(self, img_model='dall-e-3', model_resolution="1024x1024"):
        try:
            logger.info("Initializing ImageGenerator")
            self.img_model = img_model
            self.model_resolution = model_resolution

            self.max_prompt_length = 4000
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            if not self.openai_api_key:
                raise ValueError("OpenAI API key is missing.")
            self.client = OpenAI(api_key=self.openai_api_key)
        except Exception as e:
            logger.error(f"Failed to initialize ImageGenerator: {e}", exc_info=True)
            raise RuntimeError("Initialization error in ImageGenerator")
        

    def text_to_image_openai(self, prompt):
        try:
            logger.info("Generating image via OpenAI")
            logger.debug(f"Prompt: {prompt}")

            response = self.client.images.generate(
                model=self.img_model,
                prompt=prompt,
                quality="standard",
                size=self.model_resolution,
                n=1,
            )
            logger.debug(f"Image generation response: {response}")

            image_url = response.data[0].url
            return image_url
        
        except OpenAIError as oe:
            logger.error(f"OpenAI API error: {oe}", exc_info=True)
            raise oe  # Re-raise the OpenAI-specific error
        except Exception as e:
            logger.error(f"Error in text_to_image_openai: {e}", exc_info=True)
            raise RuntimeError("Error generating image via OpenAI API")
        
    def manage_prompt_length(self, prompt: str) -> str:
        """
        Adjusts the prompt length based on the model's maximum allowed prompt length.

        Parameters:
            prompt (str): The original prompt to be adjusted.

        Returns:
            str: The adjusted (or original) prompt.
        """
        try:
            logger.info("Managing prompt length based on the model")
            if "dall-e-2" in self.img_model:
                max_length = 1000
            elif "dall-e-3" in self.img_model:
                max_length = 4000
            else:
                raise ValueError(f"Unsupported model: {self.img_model}")

            logger.debug(f"Model: {self.img_model}, Max length: {max_length}, Current length: {len(prompt)}")

            # Reduce the prompt if necessary
            if len(prompt) > max_length:
                logger.info(f"Prompt exceeds max length ({max_length}). Reducing it.")
                return self.reduce_prompt(prompt, max_length=max_length)
            else:
                logger.info("Prompt length is within the acceptable range. No reduction needed.")
                return prompt
        except Exception as e:
            logger.error(f"Error managing prompt length: {e}", exc_info=True)
            raise RuntimeError("Failed to manage prompt length")
        
    def reduce_prompt(self, prompt: str, max_length: int = 4000) -> str:
        """
        Reduces the length of an image generation prompt using OpenAI API.

        Parameters:
            prompt (str): The original prompt to be reduced.
            max_length (int): The maximum allowed length for the prompt.

        Returns:
            str: The reduced prompt.
        """
        try:
            logger.info(f"Reducing prompt length.")
            logger.info(f"Original prompt length: {len(prompt)}. Max allowed length: {max_length}")

            if len(prompt) <= max_length:
                logger.info("Prompt is already within the allowed length. No reduction needed.")
                return prompt

            # Format the request prompt
            formatted_prompt = f"""
            Reduce the following text to a maximum of {max_length - 100} characters while retaining its essential meaning and details:

            {prompt}

            Return only the reduced text. Maximum length is HARD LIMIT! Don't go above it.
            """

            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a creative assistant for prompt optimization."},
                    {"role": "user", "content": formatted_prompt},
                ],
                temperature=1,  # Optional: Adjust creativity
                response_format={"type": "text"}  # Specify the response format
            )

            # Extract the reduced prompt from the response
            logger.debug("MARIA:", response.choices[0].message.content)
            reduced_prompt = response.choices[0].message.content

            logger.info(f"Successfully reduced the prompt length to {len(reduced_prompt)}")
            logger.debug(f"Reduced prompt (Length: {len(reduced_prompt)}): {reduced_prompt}")
            return reduced_prompt

        except Exception as e:
            logger.error(f"Error reducing prompt: {e}", exc_info=True)
            raise RuntimeError("Failed to reduce prompt length")


    def generate_image(self, prompt: str) -> str:
        """
        Generates an image using the specified model and manages the prompt length.
        """
        try:
            logger.info("Starting image generation process")

            # Manage the prompt length
            adjusted_prompt = self.manage_prompt_length(prompt)

            # Generate the image based on the model
            if "dall-e" in self.img_model:
                return self.text_to_image_openai(adjusted_prompt)
            else:
                raise ValueError(f"Unsupported model: {self.img_model}")

        except ValueError as ve:
            logger.warning(f"Validation error in image generation: {ve}")
            raise ve
        except Exception as e:
            logger.error(f"Error generating image: {e}", exc_info=True)
            raise RuntimeError("Error in image generation")

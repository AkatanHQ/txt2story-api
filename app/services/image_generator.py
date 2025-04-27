import os, time, json, base64, requests, io
from dotenv import load_dotenv

from PIL import Image  # ➔ Requires: pip install Pillow
from openai import OpenAI, AzureOpenAI, OpenAIError, BadRequestError
from app.utils.logger import logger

load_dotenv()

MAX_PROMPT_CHARS = 32_000
MAX_REF_DIM      = 256
JPEG_QUALITY     = 85

class ImageGenerator:
    """
    GPT-Image-1 helper for generating images with optional reference pictures.
    """

    def __init__(self,
                 provider: str = "openai",
                 img_model: str = "gpt-image-1",
                 size: str = "1024x1024",
                 quality: str = "high"):
        logger.info(f"🚀 Initializing ImageGenerator (provider={provider}, model={img_model})")
        self.provider = provider.lower()
        self.img_model = img_model
        self.size = size
        self.quality = quality

        if self.provider == "openai":
            self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        elif self.provider == "azure":
            self.client = AzureOpenAI(
                api_key=os.environ["AZURE_OPENAI_API_KEY"],
                azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                api_version="2024-02-01",
            )
        else:
            raise ValueError(f"Unsupported provider '{provider}'")

    # ────────────────────────────────────────────────────────────────────────
    # Helpers
    # ────────────────────────────────────────────────────────────────────────
    def _fetch_and_shrink(self, url: str) -> io.BytesIO:
        r = requests.get(url, timeout=20)
        img = Image.open(io.BytesIO(r.content))
        img.thumbnail((MAX_REF_DIM, MAX_REF_DIM))

        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG", quality=JPEG_QUALITY)
        img_bytes.seek(0)  # Very important!

        return img_bytes

    # ────────────────────────────────────────────────────────────────────────
    # Public
    # ────────────────────────────────────────────────────────────────────────
    def generate_image(self, prompt: str, entities: list[dict] | None = None) -> str:
        """
        Generate an image with optional reference images (manual OpenAI HTTP request version, memory-only).
        """
        logger.info("🧱 Building final prompt for image generation (manual request mode, in-memory)")

        ref_images = []

        if entities:
            for ent in entities:
                url = ent.get("dreambooth_url")
                if url:
                    try:
                        img_bytes = self._fetch_and_shrink(url)  # Get BytesIO
                        ref_images.append(img_bytes)
                    except Exception as exc:
                        logger.warning(f"⚠️  Skipping invalid reference image: {exc}")

        try:
            if ref_images:
                logger.info(f"✏️  Using {len(ref_images)} reference image(s) ➔ manually calling OpenAI API")

                url = "https://api.openai.com/v1/images/edit"
                headers = {
                    "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
                }

                files = {}
                for idx, img_bytes in enumerate(ref_images):
                    files[f"image_{idx}"] = (f"image{idx}.jpg", img_bytes, "image/jpeg")

                data = {
                    "prompt": prompt,
                    "model": self.img_model,
                    "n": 1,
                    "size": self.size,
                    "quality": self.quality,
                }

                response = requests.post(url, headers=headers, data=data, files=files)
                response.raise_for_status()

                resp_data = response.json()

                image_b64 = resp_data["data"][0]["b64_json"]

                if not image_b64:
                    logger.error("🚫 No image base64 returned by OpenAI")
                    raise RuntimeError("No image base64 returned")

                logger.info("✅ Image generated successfully (base64)")
                return image_b64

            else:
                logger.info("🖌️  No references ➔ calling images.generate() with OpenAI SDK")
                resp = self.client.images.generate(
                    model=self.img_model,
                    prompt=prompt,
                    n=1,
                    size=self.size,
                    quality=self.quality,
                )

                image_b64 = (
                    resp.data[0].b64_json
                    if self.provider == "openai"
                    else json.loads(resp.model_dump_json())["data"][0]["b64_json"]
                )

                if not image_b64:
                    logger.error("🚫 No image base64 returned by OpenAI")
                    raise RuntimeError("No image base64 returned")

                logger.info("✅ Image generated successfully (base64)")
                return image_b64

        except requests.exceptions.RequestException as err:
            logger.error(f"🔥 OpenAI HTTP Request Error during image generation: {err}")
            raise
        except (BadRequestError, OpenAIError) as err:
            if "rate limit" in str(err).lower():
                logger.warning("🐢 Rate-limited, retrying after 60 seconds")
                time.sleep(60)
                return self.generate_image(prompt, entities)
            logger.error(f"🔥 OpenAI SDK Error during image generation: {err}")
            raise



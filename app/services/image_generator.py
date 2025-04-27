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
    def _fetch_and_shrink(self, url: str) -> str:
        """
        Fetch an image and shrink it to base64 data-URI.
        """
        logger.info(f"🌐 Downloading reference image: {url}")
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content))

        original_size = img.size
        img.thumbnail((MAX_REF_DIM, MAX_REF_DIM))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()

        logger.info(f"🖼️  Reference image resized from {original_size} ➔ {img.size}, encoded base64 ({len(b64)} chars)")
        return f"data:image/jpeg;base64,{b64}"

    def _moderate(self, text: str) -> bool:
        if self.provider != "openai":
            return False
        logger.info("🛡️  Moderating prompt content via OpenAI moderation endpoint")
        m = self.client.moderations.create(input=text)
        flagged = m.results[0].flagged
        if flagged:
            logger.warning("⚠️  Prompt was flagged by OpenAI moderation")
        else:
            logger.info("✅ Prompt passed moderation check")
        return flagged

    # ────────────────────────────────────────────────────────────────────────
    # Public
    # ────────────────────────────────────────────────────────────────────────
    def generate_image(self, prompt_json: str, entities: list[dict] | None = None) -> str:
        """
        Generate an image from prompt + optional references.
        """
        logger.info("🧱 Building final prompt for image generation")
        if self._moderate(prompt_json):
            raise ValueError("Prompt flagged by moderation")

        data_uris = []
        if entities:
            for ent in entities:
                url = ent.get("dreambooth_url")
                if url:
                    try:
                        encoded = self._fetch_and_shrink(url)
                        data_uris.append(encoded)
                    except Exception as exc:
                        logger.warning(f"⚠️  Skipping invalid reference: {exc}")

        # Try to add references under size limit
        prompt = prompt_json
        if data_uris:
            ref_block = "\n\nReference images:\n" + "\n".join(data_uris)
            logger.debug(f"🧩 Adding {len(data_uris)} base64 reference(s)")
            if len(prompt) + len(ref_block) <= MAX_PROMPT_CHARS:
                prompt += ref_block
            else:
                logger.warning("⚠️  Base64 refs would exceed 32k → falling back to plain URLs")
                url_block = "\n\nReference image URLs:\n" + "\n".join(
                    [e.get("dreambooth_url") for e in entities if e.get("dreambooth_url")]
                )
                if len(prompt) + len(url_block) <= MAX_PROMPT_CHARS:
                    prompt += url_block
                    logger.info("📎 Appended plain URLs instead of base64")
                else:
                    logger.error("🚫 Prompt + references still too large even with plain URLs")
                    raise RuntimeError("Prompt would exceed 32 000 chars even without base64 refs")

        logger.info(f"📝 Final prompt length: {len(prompt)} chars")
        logger.info(f"🎯 Requesting image generation (size={self.size}, quality={self.quality})")

        try:
            resp = self.client.images.generate(
                model   = self.img_model,
                prompt  = prompt,
                n       = 1,
                size    = self.size,
                quality = self.quality,
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

        except (BadRequestError, OpenAIError) as err:
            if "rate limit" in str(err).lower():
                logger.warning("🐢 Rate-limited, retrying after 60 seconds")
                time.sleep(60)
                return self.generate_image(prompt_json, entities)
            logger.error(f"🔥 OpenAI Error during image generation: {err}")
            raise

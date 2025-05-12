# version2/openai_helpers.py
import time
import logging
import openai

logger = logging.getLogger("openai-wrapper")

def run_with_retry(
    client_method,            # e.g. client.chat.completions.create
    max_attempts: int = 5,
    base_delay: float = 0.5,  # seconds
    **kwargs,
):
    "Call an OpenAI SDK method with exponential-back-off on 5-xx."
    for attempt in range(1, max_attempts + 1):
        try:
            return client_method(**kwargs)
        except openai.InternalServerError as exc:
            if attempt == max_attempts:
                raise
            sleep = base_delay * 2 ** (attempt - 1)
            logger.warning("OpenAI 500: retrying in %.1fs (attempt %d/%d)",
                           sleep, attempt, max_attempts)
            time.sleep(sleep)
        except openai.APIConnectionError as exc:   # network hiccup
            if attempt == max_attempts:
                raise
            sleep = base_delay * 2 ** (attempt - 1)
            logger.warning("OpenAI connection error: retrying in %.1fs "
                           "(attempt %d/%d)", sleep, attempt, max_attempts)
            time.sleep(sleep)

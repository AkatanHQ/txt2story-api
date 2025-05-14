# version2/config.py
import os
from dotenv import load_dotenv
from openai import OpenAI
import logging

# Load env vars
load_dotenv()

# ────────────────────────────
# ░░ Constants / Settings ░░
# ────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_HISTORY = 20

# ────────────────────────────
# ░░ OpenAI Client ░░
# ────────────────────────────
client = OpenAI(api_key=OPENAI_API_KEY)


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=LOG_LEVEL,
)

logger = logging.getLogger("storygpt")
logger.info("Logging initialised at %s level", LOG_LEVEL)

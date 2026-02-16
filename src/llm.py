import os
import logging
from dotenv import load_dotenv

from langchain_xai import ChatXAI

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ---------------- Env ----------------
load_dotenv()

XAI_API_KEY = os.getenv("XAI_API_KEY")

if not XAI_API_KEY:
    logger.critical("XAI_API_KEY environment variable not set.")
    raise ValueError("API Key for Grok must be set.")

# ---------------- Grok LLM ----------------
llm_model = ChatXAI(
    api_key=XAI_API_KEY,
    model="grok-4-fast-reasoning",          # or grok-2-mini for cheaper/faster
    temperature=0,
    max_retries=3,
    timeout=120,             # matches your extended timeout
)

# import os
# from dotenv import load_dotenv
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.rate_limiters import InMemoryRateLimiter 
# load_dotenv()

# # Get API key from .env
# api_key = os.getenv("GOOGLE_API_KEY")

# if not api_key:
#     raise ValueError("GOOGLE_API_KEY not found. Make sure it's set in the .env file.")

# # Initialize a rate limiter for 10 requests per minute
# # This is the crucial addition to manage your API calls
# rate_limiter = InMemoryRateLimiter(requests_per_second=10 / 60)

# # Define the LLM with the rate limiter included
# llm_model = ChatGoogleGenerativeAI(
#     model="gemini-3-flash-preview",
#     google_api_key=api_key,
#     temperature=0,
#     max_retries=3,
#     rate_limiter=rate_limiter,
# )

# import os
# from dotenv import load_dotenv

# from langchain_groq import ChatGroq
# from langchain_core.rate_limiters import InMemoryRateLimiter

# load_dotenv()

# # Get API key from .env
# api_key = os.getenv("GROQ_API_KEY")

# if not api_key:
#     raise ValueError("GROQ_API_KEY not found. Make sure it's set in the .env file.")

# # Rate limiter: 10 requests per minute
# rate_limiter = InMemoryRateLimiter(
#     requests_per_second=10 / 60
# )

# # Initialize Groq LLM
# llm_model = ChatGroq(
#     groq_api_key=api_key,
#     model_name="openai/gpt-oss-120b",
#     temperature=0,
#     max_retries=3,
#     rate_limiter=rate_limiter,
# )

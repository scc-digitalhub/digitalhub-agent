import os
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("DHCORE_ENDPOINT",  os.getenv("DHCORE_ENDPOINT"))
os.environ.setdefault("DHCORE_ISSUER", os.getenv("DHCORE_ISSUER"))
os.environ.setdefault("DHCORE_PERSONAL_ACCESS_TOKEN", os.getenv("DHCORE_PERSONAL_ACCESS_TOKEN"))

DEPLOYED_URL = os.getenv("DEPLOYED_URL")
LLM_MODEL = os.getenv("LLM_MODEL")
LLM_API_KEY = os.getenv("LLM_API_KEY")

import os
from dotenv import load_dotenv

load_dotenv()

# os.environ.setdefault("DHCORE_ENDPOINT",  os.getenv("DHCORE_ENDPOINT"))
# os.environ.setdefault("DHCORE_ISSUER", os.getenv("DHCORE_ISSUER"))
# os.environ.setdefault("DHCORE_PERSONAL_ACCESS_TOKEN", os.getenv("DHCORE_PERSONAL_ACCESS_TOKEN"))

def _normalize_base_url(url):
    """Accept the URL with or without trailing slash / '/v1' suffix."""
    if not url:
        return url
    url = url.strip().rstrip("/")
    return url[: -len("/v1")] if url.endswith("/v1") else url


DEPLOYED_URL = _normalize_base_url(os.getenv("DEPLOYED_URL"))
LLM_MODEL = os.getenv("LLM_MODEL")
LLM_API_KEY = os.getenv("LLM_API_KEY")

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=2024

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd --create-home --uid 1000 agent && chown -R agent:agent /app
USER 1000

EXPOSE 2024

# Runtime configuration (provided by the platform as env vars / secrets):
#   DEPLOYED_URL  - OpenAI-compatible base URL (with or without /v1)
#   LLM_MODEL     - model name
#   LLM_API_KEY   - API key (mount as a platform secret)
CMD ["python", "server.py"]

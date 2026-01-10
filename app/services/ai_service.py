import base64
import logging
from typing import Protocol, runtime_checkable

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Prompt we send to vision models
ASSET_DESCRIPTION_PROMPT = """You are an asset management assistant. Describe the physical asset in this image.
Include: type of device, brand/model if visible, color, condition, notable features.
Keep it to 2-3 sentences, professional tone."""


class AIProviderError(Exception):
    """Raised when an AI provider fails."""

    pass


@runtime_checkable
class AIProvider(Protocol):
    """Interface for AI providers - just needs describe_image method."""

    async def describe_image(self, image_bytes: bytes, mime_type: str) -> str: ...


class OllamaProvider:
    """Ollama local provider. Needs ollama running with a vision model like llava."""

    def __init__(self, endpoint: str = "http://localhost:11434", model: str = "llava"):
        self.endpoint = endpoint.rstrip("/")
        self.model = model

    async def describe_image(self, image_bytes: bytes, mime_type: str) -> str:
        base64_image = base64.standard_b64encode(image_bytes).decode("utf-8")

        payload = {
            "model": self.model,
            "prompt": f"{ASSET_DESCRIPTION_PROMPT}\n\nDescribe this asset.",
            "images": [base64_image],
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.endpoint}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                return response.json()["response"]
            except httpx.HTTPStatusError as e:
                logger.error(f"Ollama error: {e.response.status_code}")
                raise AIProviderError(f"Ollama failed: {e.response.status_code}") from e
            except httpx.RequestError as e:
                logger.error(f"Can't reach Ollama: {e}")
                raise AIProviderError(
                    f"Can't connect to Ollama at {self.endpoint}"
                ) from e
            except KeyError:
                raise AIProviderError("Bad response from Ollama")


class LMStudioProvider:
    """LMStudio local provider. Uses OpenAI-compatible API on localhost:1234."""

    def __init__(
        self, endpoint: str = "http://localhost:1234", model: str = "local-model"
    ):
        self.endpoint = endpoint.rstrip("/")
        self.model = model

    async def describe_image(self, image_bytes: bytes, mime_type: str) -> str:
        base64_image = base64.standard_b64encode(image_bytes).decode("utf-8")

        # OpenAI-compatible chat format
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": ASSET_DESCRIPTION_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            },
                        },
                        {"type": "text", "text": "Describe this asset."},
                    ],
                },
            ],
            "max_tokens": 300,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.endpoint}/v1/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                logger.error(f"LMStudio error: {e.response.status_code}")
                raise AIProviderError(
                    f"LMStudio failed: {e.response.status_code}"
                ) from e
            except httpx.RequestError as e:
                logger.error(f"Can't reach LMStudio: {e}")
                raise AIProviderError(
                    f"Can't connect to LMStudio at {self.endpoint}"
                ) from e
            except (KeyError, IndexError):
                raise AIProviderError("Bad response from LMStudio")


# Stubs for cloud providers - shows the architecture but not implemented
class OpenAIProvider:
    """OpenAI stub - not implemented, just here to show provider pattern."""

    API_BASE = "https://api.openai.com/v1"

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    async def describe_image(self, image_bytes: bytes, mime_type: str) -> str:
        raise NotImplementedError("OpenAI not implemented - use ollama or lmstudio")


class AnthropicProvider:
    """Anthropic stub - not implemented."""

    API_BASE = "https://api.anthropic.com/v1"

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model

    async def describe_image(self, image_bytes: bytes, mime_type: str) -> str:
        raise NotImplementedError("Anthropic not implemented - use ollama or lmstudio")


def get_ai_provider() -> AIProvider:
    """Factory to get the configured provider based on AI_PROVIDER setting."""
    provider_name = settings.AI_PROVIDER.lower()

    if provider_name == "ollama":
        return OllamaProvider(
            endpoint=settings.AI_ENDPOINT,
            model=settings.AI_MODEL or "llava",
        )

    if provider_name == "lmstudio":
        return LMStudioProvider(
            endpoint=settings.AI_ENDPOINT or "http://localhost:1234",
            model=settings.AI_MODEL or "local-model",
        )

    if provider_name == "openai":
        if not settings.AI_API_KEY:
            raise ValueError("AI_API_KEY required for OpenAI")
        return OpenAIProvider(
            api_key=settings.AI_API_KEY, model=settings.AI_MODEL or "gpt-4o"
        )

    if provider_name == "anthropic":
        if not settings.AI_API_KEY:
            raise ValueError("AI_API_KEY required for Anthropic")
        return AnthropicProvider(
            api_key=settings.AI_API_KEY,
            model=settings.AI_MODEL or "claude-sonnet-4-20250514",
        )

    raise ValueError(f"Unknown AI provider: {provider_name}")


class AIService:
    """Wraps AI providers for asset-specific operations."""

    def __init__(self, provider: AIProvider | None = None):
        self._provider = provider

    @property
    def provider(self) -> AIProvider:
        if self._provider is None:
            self._provider = get_ai_provider()
        return self._provider

    async def describe_asset_image(self, image_bytes: bytes, mime_type: str) -> str:
        """Generate description for an asset image."""
        logger.info(f"Generating description with {settings.AI_PROVIDER}")
        description = await self.provider.describe_image(image_bytes, mime_type)
        logger.info("Got description")
        return description


# Image validation
SUPPORTED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_image(content_type: str | None, size: int) -> None:
    """Check if uploaded file is a valid image."""
    if not content_type or content_type.lower() not in SUPPORTED_IMAGE_TYPES:
        raise ValueError(
            f"Unsupported image type: {content_type}. Use: {', '.join(SUPPORTED_IMAGE_TYPES)}"
        )

    if size > MAX_IMAGE_SIZE:
        raise ValueError(f"Image too large ({size / 1024 / 1024:.1f} MB). Max: 10 MB")

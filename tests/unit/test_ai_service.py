import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.ai_service import (
    AIService,
    AIProviderError,
    OpenAIProvider,
    AnthropicProvider,
    OllamaProvider,
    LMStudioProvider,
    get_ai_provider,
    validate_image,
    MAX_IMAGE_SIZE,
)


class TestValidateImage:
    def test_valid_jpeg(self):
        validate_image("image/jpeg", 1024)

    def test_valid_png(self):
        validate_image("image/png", 2048)

    def test_valid_webp(self):
        validate_image("image/webp", 4096)

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="Unsupported image type"):
            validate_image("application/pdf", 1024)

    def test_none_type(self):
        with pytest.raises(ValueError, match="Unsupported image type"):
            validate_image(None, 1024)

    def test_too_large(self):
        with pytest.raises(ValueError, match="too large"):
            validate_image("image/jpeg", MAX_IMAGE_SIZE + 1)

    def test_at_limit(self):
        validate_image("image/jpeg", MAX_IMAGE_SIZE)


class TestGetAIProvider:
    def test_ollama(self):
        with patch("app.services.ai_service.settings") as s:
            s.AI_PROVIDER = "ollama"
            s.AI_ENDPOINT = "http://localhost:11434"
            s.AI_MODEL = "llava"

            p = get_ai_provider()

            assert isinstance(p, OllamaProvider)
            assert p.endpoint == "http://localhost:11434"
            assert p.model == "llava"

    def test_lmstudio(self):
        with patch("app.services.ai_service.settings") as s:
            s.AI_PROVIDER = "lmstudio"
            s.AI_ENDPOINT = "http://localhost:1234"
            s.AI_MODEL = "llava-v1.6"

            p = get_ai_provider()

            assert isinstance(p, LMStudioProvider)
            assert p.endpoint == "http://localhost:1234"

    def test_openai_stub(self):
        with patch("app.services.ai_service.settings") as s:
            s.AI_PROVIDER = "openai"
            s.AI_API_KEY = "sk-test"
            s.AI_MODEL = "gpt-4o"

            p = get_ai_provider()
            assert isinstance(p, OpenAIProvider)

    def test_anthropic_stub(self):
        with patch("app.services.ai_service.settings") as s:
            s.AI_PROVIDER = "anthropic"
            s.AI_API_KEY = "sk-ant-test"
            s.AI_MODEL = "claude-3"

            p = get_ai_provider()
            assert isinstance(p, AnthropicProvider)

    def test_openai_needs_key(self):
        with patch("app.services.ai_service.settings") as s:
            s.AI_PROVIDER = "openai"
            s.AI_API_KEY = None

            with pytest.raises(ValueError, match="AI_API_KEY"):
                get_ai_provider()

    def test_anthropic_needs_key(self):
        with patch("app.services.ai_service.settings") as s:
            s.AI_PROVIDER = "anthropic"
            s.AI_API_KEY = None

            with pytest.raises(ValueError, match="AI_API_KEY"):
                get_ai_provider()

    def test_unknown_provider(self):
        with patch("app.services.ai_service.settings") as s:
            s.AI_PROVIDER = "unknown"

            with pytest.raises(ValueError, match="Unknown AI provider"):
                get_ai_provider()

    def test_case_insensitive(self):
        with patch("app.services.ai_service.settings") as s:
            s.AI_PROVIDER = "OLLAMA"
            s.AI_ENDPOINT = "http://localhost:11434"
            s.AI_MODEL = "llava"

            p = get_ai_provider()
            assert isinstance(p, OllamaProvider)


class TestOllamaProvider:
    @pytest.fixture
    def provider(self):
        return OllamaProvider(endpoint="http://localhost:11434", model="llava")

    @pytest.fixture
    def image(self):
        return b"\x89PNG\r\n"

    async def test_success(self, provider, image):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "A white iPhone."}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock = AsyncMock()
            mock.post.return_value = mock_resp
            mock.__aenter__.return_value = mock
            mock.__aexit__.return_value = None
            mock_client.return_value = mock

            result = await provider.describe_image(image, "image/png")
            assert result == "A white iPhone."

    async def test_strips_trailing_slash(self):
        p = OllamaProvider(endpoint="http://localhost:11434/", model="llava")
        assert p.endpoint == "http://localhost:11434"

    async def test_connection_error(self, provider, image):
        import httpx

        with patch("httpx.AsyncClient") as mock_client:
            mock = AsyncMock()
            mock.post.side_effect = httpx.RequestError("Connection refused")
            mock.__aenter__.return_value = mock
            mock.__aexit__.return_value = None
            mock_client.return_value = mock

            with pytest.raises(AIProviderError, match="Can't connect to Ollama"):
                await provider.describe_image(image, "image/png")

    async def test_api_error(self, provider, image):
        import httpx

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Error"

        with patch("httpx.AsyncClient") as mock_client:
            mock = AsyncMock()
            mock.post.side_effect = httpx.HTTPStatusError(
                "Error", request=MagicMock(), response=mock_resp
            )
            mock.__aenter__.return_value = mock
            mock.__aexit__.return_value = None
            mock_client.return_value = mock

            with pytest.raises(AIProviderError, match="Ollama failed"):
                await provider.describe_image(image, "image/png")


class TestLMStudioProvider:
    @pytest.fixture
    def provider(self):
        return LMStudioProvider(endpoint="http://localhost:1234", model="llava-v1.6")

    @pytest.fixture
    def image(self):
        return b"\xff\xd8\xff\xe0"

    async def test_success(self, provider, image):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "A silver MacBook."}}]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock = AsyncMock()
            mock.post.return_value = mock_resp
            mock.__aenter__.return_value = mock
            mock.__aexit__.return_value = None
            mock_client.return_value = mock

            result = await provider.describe_image(image, "image/jpeg")
            assert result == "A silver MacBook."

    async def test_strips_trailing_slash(self):
        p = LMStudioProvider(endpoint="http://localhost:1234/", model="llava")
        assert p.endpoint == "http://localhost:1234"

    async def test_connection_error(self, provider, image):
        import httpx

        with patch("httpx.AsyncClient") as mock_client:
            mock = AsyncMock()
            mock.post.side_effect = httpx.RequestError("Connection refused")
            mock.__aenter__.return_value = mock
            mock.__aexit__.return_value = None
            mock_client.return_value = mock

            with pytest.raises(AIProviderError, match="Can't connect to LMStudio"):
                await provider.describe_image(image, "image/jpeg")

    async def test_uses_openai_format(self, provider, image):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "A device."}}]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock = AsyncMock()
            mock.post.return_value = mock_resp
            mock.__aenter__.return_value = mock
            mock.__aexit__.return_value = None
            mock_client.return_value = mock

            await provider.describe_image(image, "image/jpeg")

            call_args = mock.post.call_args
            assert "/v1/chat/completions" in call_args[0][0]
            payload = call_args.kwargs["json"]
            assert "messages" in payload


class TestStubProviders:
    async def test_openai_not_implemented(self):
        p = OpenAIProvider(api_key="sk-test", model="gpt-4o")
        with pytest.raises(NotImplementedError):
            await p.describe_image(b"image", "image/png")

    async def test_anthropic_not_implemented(self):
        p = AnthropicProvider(api_key="sk-ant-test", model="claude-3")
        with pytest.raises(NotImplementedError):
            await p.describe_image(b"image", "image/png")


class TestAIService:
    async def test_delegates_to_provider(self):
        mock_provider = AsyncMock()
        mock_provider.describe_image.return_value = "A laptop."

        svc = AIService(provider=mock_provider)
        result = await svc.describe_asset_image(b"data", "image/jpeg")

        assert result == "A laptop."
        mock_provider.describe_image.assert_called_once_with(b"data", "image/jpeg")

    async def test_lazy_init(self):
        with patch("app.services.ai_service.get_ai_provider") as mock_get:
            mock_provider = AsyncMock()
            mock_provider.describe_image.return_value = "Description"
            mock_get.return_value = mock_provider

            svc = AIService()
            await svc.describe_asset_image(b"data", "image/png")

            mock_get.assert_called_once()

    async def test_error_propagates(self):
        mock_provider = AsyncMock()
        mock_provider.describe_image.side_effect = AIProviderError("Failed")

        svc = AIService(provider=mock_provider)

        with pytest.raises(AIProviderError, match="Failed"):
            await svc.describe_asset_image(b"data", "image/jpeg")

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.cache import cache_response, invalidate_cache
from app.services.auth_service import AuthService
from app.schemas.response import SuccessResponse
from app.models.user import User


# CACHING TESTS


class TestCache:
    @pytest.mark.asyncio
    async def test_cache_decorator_hit_and_miss(self):
        """Test that decorator checks cache, returns hit, or executes and sets cache."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # Cache miss first

        # Mock Redis client
        with patch("app.core.cache.redis_client", mock_redis):
            # Define decorated function
            @cache_response(key_pattern="test:key", expire=60)
            async def test_func():
                return SuccessResponse(message="Success", code=200, data={"foo": "bar"})

            # Call 1: Miss -> Execute -> Set
            result1 = await test_func()
            assert result1.data == {"foo": "bar"}
            mock_redis.get.assert_called_with("test:key")
            mock_redis.setex.assert_called_once()

            # Call 2: Hit
            mock_redis.get.return_value = result1.model_dump_json()
            mock_redis.reset_mock()

            result2 = await test_func()
            # Result comes from cache (mocked return)
            assert result2["data"] == {"foo": "bar"}
            mock_redis.get.assert_called_with("test:key")
            mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_decorator_with_sqlalchemy_model(self):
        """Test that decorator handles SQLAlchemy models via jsonable_encoder."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        # Create a mock SQLAlchemy model
        class MockAsset:
            def __init__(self, id, name):
                self.id = id
                self.name = name

        asset = MockAsset(id="123", name="Laptop")

        with patch("app.core.cache.redis_client", mock_redis):

            @cache_response(key_pattern="test:asset", expire=60)
            async def get_raw_asset():
                return SuccessResponse(message="Success", code=200, data=asset)

            result = await get_raw_asset()
            assert result.data.id == "123"

            # Check what was sent to Redis
            assert mock_redis.setex.called
            call_args = mock_redis.setex.call_args
            serialized_sent = call_args[0][2]
            data_sent = json.loads(serialized_sent)

            # Ensure the top-level structure is preserved
            assert data_sent["message"] == "Success"
            assert "data" in data_sent
            assert "MockAsset" in str(data_sent["data"])

    @pytest.mark.asyncio
    async def test_invalidate_cache(self):
        """Test cache invalidation helper."""
        mock_redis = AsyncMock()
        with patch("app.core.cache.redis_client", mock_redis):
            await invalidate_cache("test:key")
            mock_redis.delete.assert_called_once_with("test:key")


# SECURITY TESTS (IP Tracking)


class TestIPTracking:
    @pytest.mark.asyncio
    async def test_login_updates_ip(self):
        """Test that login updates the user's last_ip."""
        mock_session = AsyncMock()
        mock_user = User(
            id=1, email="test@example.com", hashed_password="hash", last_ip="1.1.1.1"
        )

        mock_session.scalar.return_value = mock_user

        # Mock password verification
        with patch("app.services.auth_service.verify_password", return_value=True):
            svc = AuthService()
            await svc.login(
                mock_session,
                "test@example.com",
                "password",
                ip_address="2.2.2.2",
                background_tasks=MagicMock(),
            )

            assert mock_user.last_ip == "2.2.2.2"
            mock_session.add.assert_called_with(mock_user)
            mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_login_alerts_on_mismatch(self):
        """Test that login triggers alert on IP mismatch."""
        mock_session = AsyncMock()
        mock_user = User(
            id=1, email="test@example.com", hashed_password="hash", last_ip="1.1.1.1"
        )
        mock_session.scalar.return_value = mock_user

        mock_bg_tasks = MagicMock()

        with patch("app.services.auth_service.verify_password", return_value=True):
            with patch(
                "app.services.email_service.EmailService.send_login_alert"
            ) as mock_alert:
                svc = AuthService()
                await svc.login(
                    mock_session,
                    "test@example.com",
                    "password",
                    ip_address="9.9.9.9",  # Different IP
                    background_tasks=mock_bg_tasks,
                )

                # Should verify alert was added to background tasks
                mock_bg_tasks.add_task.assert_called()
                # Verify arguments
                args = mock_bg_tasks.add_task.call_args
                assert args[0][0] == mock_alert
                assert args[0][1] == "test@example.com"
                assert args[0][2] == "9.9.9.9"

    @pytest.mark.asyncio
    async def test_login_no_alert_same_ip(self):
        """Test that login does NOT alert on same IP."""
        mock_session = AsyncMock()
        mock_user = User(
            id=1, email="test@example.com", hashed_password="hash", last_ip="1.1.1.1"
        )
        mock_session.scalar.return_value = mock_user

        mock_bg_tasks = MagicMock()

        with patch("app.services.auth_service.verify_password", return_value=True):
            svc = AuthService()
            await svc.login(
                mock_session,
                "test@example.com",
                "password",
                ip_address="1.1.1.1",  # Same IP
                background_tasks=mock_bg_tasks,
            )

            mock_bg_tasks.add_task.assert_not_called()

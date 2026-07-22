from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.redis import RedisManager, get_redis


@pytest.mark.asyncio
async def test_redis_manager_init():
    manager = RedisManager()
    assert manager.pool is None
    assert manager.client is None

    with patch("app.core.redis.ConnectionPool.from_url") as mock_pool, patch(
        "app.core.redis.Redis"
    ) as mock_redis:
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance

        manager.init_redis()

        assert manager.pool == mock_pool_instance
        assert manager.client == mock_redis_instance
        mock_pool.assert_called_once()
        mock_redis.assert_called_once_with(connection_pool=mock_pool_instance)


@pytest.mark.asyncio
async def test_redis_manager_ping_success():
    manager = RedisManager()
    manager.client = AsyncMock()
    manager.client.ping.return_value = True

    result = await manager.ping()
    assert result is True
    manager.client.ping.assert_called_once()


@pytest.mark.asyncio
async def test_redis_manager_ping_failure():
    manager = RedisManager()
    manager.client = AsyncMock()
    manager.client.ping.side_effect = Exception("Connection error")

    result = await manager.ping()
    assert result is False


@pytest.mark.asyncio
async def test_redis_manager_check_health_and_reconnect_success():
    manager = RedisManager()
    manager.ping = AsyncMock(side_effect=[False, True])
    manager.close = AsyncMock()
    manager.init_redis = MagicMock()

    with patch("app.core.redis.logger") as mock_logger:
        result = await manager.check_health_and_reconnect()
        assert result is True
        manager.close.assert_called_once()
        manager.init_redis.assert_called_once()
        mock_logger.info.assert_any_call("Reconnect Attempt")
        mock_logger.info.assert_any_call("Redis Connected")


@pytest.mark.asyncio
async def test_redis_manager_check_health_and_reconnect_failure():
    manager = RedisManager()
    manager.ping = AsyncMock(return_value=False)
    manager.close = AsyncMock()
    manager.init_redis = MagicMock()

    with patch("app.core.redis.logger") as mock_logger:
        result = await manager.check_health_and_reconnect()
        assert result is False
        manager.close.assert_called_once()
        manager.init_redis.assert_called_once()
        mock_logger.info.assert_any_call("Reconnect Attempt")
        mock_logger.error.assert_any_call("Connection Failed")


@pytest.mark.asyncio
async def test_redis_manager_close():
    manager = RedisManager()
    mock_client = AsyncMock()
    mock_pool = AsyncMock()
    manager.client = mock_client
    manager.pool = mock_pool

    with patch("app.core.redis.logger") as mock_logger:
        await manager.close()
        mock_client.close.assert_called_once()
        mock_pool.disconnect.assert_called_once()
        mock_logger.info.assert_called_once_with("Redis Disconnected")
        assert manager.client is None
        assert manager.pool is None


@pytest.mark.asyncio
async def test_get_redis():
    with patch("app.core.redis.redis_manager") as mock_manager:
        mock_manager.client = None
        mock_manager.init_redis = MagicMock()
        mock_manager.ping = AsyncMock(return_value=True)
        mock_client = MagicMock()

        def set_client():
            mock_manager.client = mock_client

        mock_manager.init_redis.side_effect = set_client

        client = await get_redis()
        mock_manager.init_redis.assert_called_once()
        assert client == mock_client

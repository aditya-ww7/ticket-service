import pytest
from unittest.mock import Mock, MagicMock
from app.repositories.ticket_repository import TicketRepository
from app.cache.redis_cache import RedisCache
from app.services.ticket_service import TicketService


@pytest.fixture
def mock_repository():
    repository = Mock(spec=TicketRepository)
    repository.get_all_tickets = MagicMock(return_value=[])
    repository.create_ticket = MagicMock()
    repository.get_ticket = MagicMock()
    repository.update_ticket_status = MagicMock()
    return repository


@pytest.fixture
def mock_cache():
    cache = Mock(spec=RedisCache)
    cache.redis = Mock()
    cache.redis.hgetall = MagicMock(return_value={})
    cache.redis.hset = MagicMock()
    cache.redis.expire = MagicMock()
    cache.generate_request_hash = MagicMock(return_value="test-hash")
    return cache


@pytest.fixture
def service(mock_repository, mock_cache):
    return TicketService(mock_repository, mock_cache)

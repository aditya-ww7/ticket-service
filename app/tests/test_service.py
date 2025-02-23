from typing import Dict, Any
import json
import pytest
from unittest.mock import Mock, MagicMock
from app.models.ticket import Ticket, TicketStatus
from app.services.ticket_service import TicketService


@pytest.fixture
def mock_cache():
    cache = Mock()
    cache.get_cached_request = MagicMock(return_value=None)
    cache.generate_request_hash = MagicMock(return_value="test-hash")
    cache.cache_request = MagicMock()
    return cache


@pytest.fixture
def mock_repository():
    repository = Mock()
    repository.get_all_tickets = MagicMock(return_value=[])
    repository.create_ticket = MagicMock()
    repository.get_ticket = MagicMock()
    repository.update_ticket_status = MagicMock()
    repository.save_booking_response = MagicMock()
    repository.get_booking_response = MagicMock()
    repository.session = Mock()
    return repository


@pytest.fixture
def service(mock_repository, mock_cache):
    return TicketService(mock_repository, mock_cache)


def test_book_ticket_success(service, mock_repository, mock_cache):
    request_data = {
        "passenger_name": "John Doe",
        "seat_number": "A1",
        "amount": 100.0
    }

    mock_cache.get_cached_request.return_value = None

    result = service.book_ticket("request_1", request_data)

    assert result["status"] == "SUCCESS"
    assert "booking_reference" in result
    assert result["code"] == "BOOKING_CREATED"


def test_book_ticket_duplicate_request_returns_original_response(service, mock_repository, mock_cache):
    request_data = {
        "passenger_name": "John Doe",
        "seat_number": "A2",
        "amount": 100.0
    }

    original_response = {
        "status": "SUCCESS",
        "code": "BOOKING_CREATED",
        "booking_reference": "TEST-REF-123",
        "message": "Ticket booked successfully",
        "ticket_details": {
            "passenger_name": "John Doe",
            "seat_number": "A2",
            "amount": 100.0,
            "status": "BOOKED"
        }
    }

    mock_cache.get_cached_request.return_value = {
        "hash": "test-hash",
        "data": request_data
    }

    mock_response = Mock()
    mock_response.response_data = original_response
    mock_repository.get_booking_response.return_value = mock_response

    result = service.book_ticket("request_2", request_data)

    assert result == original_response
    mock_cache.get_cached_request.assert_called_once_with("request_2")
    mock_repository.get_booking_response.assert_called_once_with("request_2")


def test_book_ticket_duplicate_request_with_different_body(service, mock_cache):
    original_request = {
        "passenger_name": "John Doe",
        "seat_number": "A2",
        "amount": 100.0
    }

    modified_request = {
        "passenger_name": "Jane Doe",
        "seat_number": "A2",
        "amount": 100.0
    }

    mock_cache.get_cached_request.return_value = {
        "hash": "test-hash",
        "data": original_request
    }

    result = service.book_ticket("request_2", modified_request)

    assert result["status"] == "ERROR"
    assert result["code"] == "INVALID_DUPLICATE_REQUEST"
    assert "Request body does not match" in result["message"]


def test_book_ticket_invalid_request(service, mock_cache):
    request_data = {
        "passenger_name": "John Doe"  # Missing required fields
    }

    mock_cache.get_cached_request.return_value = None

    result = service.book_ticket("request_4", request_data)

    assert result["status"] == "ERROR"
    assert result["code"] == "VALIDATION_ERROR"
    assert "Missing required field" in result["message"]

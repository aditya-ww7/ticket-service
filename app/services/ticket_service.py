from typing import Dict, Any, Optional, Tuple
import json
import uuid
from dataclasses import dataclass
from app.models.ticket import TicketStatus
from app.repositories.ticket_repository import TicketRepository
from app.cache.redis_cache import RedisCache
from app.schemas import PaginationParams, PaginatedResponse


@dataclass
class ErrorResponse:
    status: str = "ERROR"
    code: str = ""
    message: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "status": self.status,
            "code": self.code,
            "message": self.message
        }


class TicketService:
    def __init__(self, repository: TicketRepository, cache: RedisCache):
        self.repository = repository
        self.cache = cache

    def _create_error_response(self, code: str, message: str) -> Dict[str, str]:
        return ErrorResponse(code=code, message=message).to_dict()

    def _validate_booking_request(self, request_data: dict) -> Tuple[bool, Optional[str]]:
        required_fields = ['passenger_name', 'seat_number', 'amount']
        for field in required_fields:
            if field not in request_data:
                return False, f"Missing required field: {field}"
        return True, None

    def _check_seat_availability(self, seat_number: str) -> bool:
        existing_tickets = self.repository.get_all_tickets()
        return not any(
            ticket.seat_number == seat_number and ticket.status == TicketStatus.BOOKED
            for ticket in existing_tickets
        )

    def _validate_request_against_cache(self, current_request: dict, cached_request: dict) -> bool:
        def normalize_request(req: dict) -> str:
            return json.dumps(req, sort_keys=True)

        return normalize_request(current_request) == normalize_request(cached_request)

    def _handle_duplicate_request(self, request_id: str, request_data: dict, cached_request: dict) -> Dict[str, Any]:
        if not self._validate_request_against_cache(request_data, cached_request["data"]):
            return self._create_error_response(
                "INVALID_DUPLICATE_REQUEST",
                "Request body does not match original request"
            )

        stored_response = self.repository.get_booking_response(request_id)
        if not stored_response:
            return self._create_error_response(
                "RESPONSE_NOT_FOUND",
                "Original response not found for duplicate request"
            )

        return stored_response.response_data

    def _create_ticket_response(self, ticket, booking_reference: str) -> Dict[str, Any]:
        return {
            "status": "SUCCESS",
            "code": "BOOKING_CREATED",
            "booking_reference": booking_reference,
            "message": "Ticket booked successfully",
            "ticket_details": {
                "passenger_name": ticket.passenger_name,
                "seat_number": ticket.seat_number,
                "amount": ticket.amount,
                "status": ticket.status.value
            }
        }

    def _process_new_booking(self, request_id: str, request_data: dict) -> Dict[str, Any]:
        is_valid, error_message = self._validate_booking_request(request_data)
        if not is_valid:
            return self._create_error_response("VALIDATION_ERROR", error_message)

        if not self._check_seat_availability(request_data["seat_number"]):
            return self._create_error_response("SEAT_UNAVAILABLE", "Seat is not available")

        booking_reference = str(uuid.uuid4())
        ticket_data = {
            **request_data,
            "booking_reference": booking_reference,
            "status": TicketStatus.BOOKED
        }

        try:
            ticket = self.repository.create_ticket(ticket_data)
            response = self._create_ticket_response(ticket, booking_reference)

            self._save_booking_data(request_id, request_data, response)
            return response

        except Exception as e:
            self.repository.session.rollback()
            raise

    def _save_booking_data(self, request_id: str, request_data: dict, response: Dict[str, Any]) -> None:
        self.repository.save_booking_response(request_id, response)
        self.cache.cache_request(request_id, request_data)

    def book_ticket(self, request_id: str, request_data: dict) -> Dict[str, Any]:
        try:
            cached_request = self.cache.get_cached_request(request_id)
            if cached_request:
                return self._handle_duplicate_request(request_id, request_data, cached_request)

            return self._process_new_booking(request_id, request_data)

        except Exception as e:
            return self._create_error_response(
                "INTERNAL_ERROR",
                f"An error occurred: {str(e)}"
            )

    def _get_ticket_details_response(self, ticket) -> Dict[str, Any]:
        return {
            "status": "SUCCESS",
            "code": "TICKET_CANCELLED",
            "message": "Ticket cancelled successfully",
            "ticket_details": {
                "booking_reference": ticket.booking_reference,
                "passenger_name": ticket.passenger_name,
                "seat_number": ticket.seat_number,
                "status": ticket.status.value
            }
        }

    def cancel_ticket(self, booking_reference: str) -> Dict[str, Any]:
        ticket = self.repository.get_ticket(booking_reference)
        if not ticket:
            return self._create_error_response("TICKET_NOT_FOUND", "Ticket not found")

        if ticket.status == TicketStatus.CANCELLED:
            return self._create_error_response(
                "TICKET_ALREADY_CANCELLED",
                "Ticket is already cancelled"
            )

        updated_ticket = self.repository.update_ticket_status(
            booking_reference,
            TicketStatus.CANCELLED
        )

        return self._get_ticket_details_response(updated_ticket)

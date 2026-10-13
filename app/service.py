"""Ties together storage, Jev triage, and routing."""
import json

from app.jev_triage import MockTriager, get_triager
from app.models import STATUSES, Ticket
from app.router import apply_routing
from app.store import DATA_DIR, TicketStore


class TicketService:
    def __init__(self):
        self.store = TicketStore()
        self.triager = get_triager()
        self._fallback = MockTriager()

    @property
    def mode(self) -> str:
        return self.triager.name

    def _triage(self, ticket: Ticket) -> None:
        try:
            result = self.triager.triage(ticket.title, ticket.description)
        except Exception as error:  # network/API problems shouldn't crash the demo
            if isinstance(self.triager, MockTriager):
                raise
            print(f"  ! Jev call failed ({type(error).__name__}); using offline triage.")
            result = self._fallback.triage(ticket.title, ticket.description)
        apply_routing(ticket, result)

    def create_ticket(self, title: str, description: str, email: str) -> Ticket:
        title = (title or "").strip()
        description = (description or "").strip()
        email = (email or "").strip()
        if not title:
            raise ValueError("Title is required.")
        if not description:
            raise ValueError("Description is required.")
        if "@" not in email:
            raise ValueError("A valid customer email is required.")

        ticket = Ticket(title=title, description=description, customer_email=email)
        self._triage(ticket)
        self.store.add(ticket)
        return ticket

    def load_samples(self) -> list[Ticket]:
        samples = json.loads((DATA_DIR / "sample_tickets.json").read_text(encoding="utf-8"))
        return [self.create_ticket(s["title"], s["description"], s["email"]) for s in samples]

    def list_tickets(self) -> list[Ticket]:
        return self.store.all()

    def get_ticket(self, ticket_id: str) -> Ticket | None:
        return self.store.get(ticket_id)

    def update_status(self, ticket_id: str, status: str) -> Ticket | None:
        normalized_status = (status or "").strip().lower()
        if normalized_status not in STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(STATUSES)}")
        ticket = self.store.get(ticket_id)
        if ticket:
            ticket.status = normalized_status
            self.store.save()
        return ticket

    def close(self) -> None:
        self.triager.close()

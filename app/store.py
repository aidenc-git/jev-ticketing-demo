"""Simple JSON-file storage for tickets."""
import json
from pathlib import Path

from app.models import Ticket

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class TicketStore:
    def __init__(self, path: Path = DATA_DIR / "tickets.json"):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.tickets: dict[str, Ticket] = self._load()

    def _load(self) -> dict[str, Ticket]:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return {}

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, ValueError):
            return {}

        if isinstance(payload, dict):
            payload = payload.get("tickets", [])
        if not isinstance(payload, list):
            return {}

        tickets: dict[str, Ticket] = {}
        for item in payload:
            if not isinstance(item, dict):
                continue
            ticket_id = item.get("id")
            if not ticket_id:
                continue
            ticket = Ticket.from_dict(item)
            tickets[ticket.id] = ticket
        return tickets

    def save(self) -> None:
        data = [t.to_dict() for t in self.tickets.values()]
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add(self, ticket: Ticket) -> None:
        self.tickets[ticket.id] = ticket
        self.save()

    def get(self, ticket_id: str) -> Ticket | None:
        return self.tickets.get(ticket_id.strip().upper())

    def all(self) -> list[Ticket]:
        # Escalated first, then shortest SLA, then newest
        return sorted(
            self.tickets.values(),
            key=lambda t: (not t.escalated, t.sla_hours or 999, t.created_at),
        )

    def clear(self) -> None:
        self.tickets = {}
        self.save()

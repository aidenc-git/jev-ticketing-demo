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
        if not self.path.exists():
            return {}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return {item["id"]: Ticket.from_dict(item) for item in data}

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

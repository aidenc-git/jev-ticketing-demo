"""Data models for tickets and Jev triage results."""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

STATUSES = ("open", "in_progress", "resolved", "closed")


@dataclass
class TriageResult:
    """The typed decisions returned by Jev (or the offline mock) for one ticket."""

    category: str               # Choice answer, e.g. "billing"
    category_confidence: float  # 0..1, how sure the model is about the category
    priority_score: float       # Score answer, 0.0 (low) .. 3.0 (critical)
    priority_confidence: float  # 0..1
    escalate_probability: float # Noul answer: probability of "yes"
    refund_probability: float   # Noul answer: probability of "yes"
    model: str                  # which model produced the answer


@dataclass
class Ticket:
    title: str
    description: str
    customer_email: str
    id: str = field(default_factory=lambda: f"TKT-{uuid.uuid4().hex[:6].upper()}")
    status: str = "open"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    # Filled in by the router after triage
    triage: TriageResult | None = None
    assigned_queue: str | None = None
    priority_label: str | None = None
    sla_hours: int | None = None
    escalated: bool = False
    needs_review: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Ticket":
        data = dict(data)
        triage = data.pop("triage", None)
        ticket = cls(**data)
        if isinstance(triage, dict) and triage:
            try:
                ticket.triage = TriageResult(**triage)
            except TypeError:
                ticket.triage = None
        return ticket

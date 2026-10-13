"""Routing policy: plain, deterministic Python that acts on Jev's decisions.

Jev decides *what* the ticket is; this module decides *what to do about it*.
Keeping the policy here means you can change business rules without
touching the model questions.
"""
from app.models import Ticket, TriageResult

QUEUES = {
    "billing": "Billing Team",
    "technical": "Engineering Support",
    "account": "Account Services",
    "feature_request": "Product Team",
    "other": "General Support",
}
PRIORITY_LABELS = ["Low", "Medium", "High", "Critical"]
SLA_HOURS = [72, 24, 8, 1]  # response-time target per priority level

REVIEW_BELOW = 0.6    # confidence under this -> a human double-checks
ESCALATE_ABOVE = 0.7  # escalation probability over this -> flag for a lead


def apply_routing(ticket: Ticket, triage: TriageResult) -> Ticket:
    level = max(0, min(3, round(triage.priority_score)))
    escalated = triage.escalate_probability >= ESCALATE_ABOVE
    if escalated:
        level = max(level, 2)  # escalations are at least High

    needs_review = (
        triage.category_confidence < REVIEW_BELOW
        or triage.priority_confidence < REVIEW_BELOW
    )

    ticket.triage = triage
    ticket.priority_label = PRIORITY_LABELS[level]
    ticket.sla_hours = SLA_HOURS[level]
    ticket.escalated = escalated
    ticket.needs_review = needs_review
    ticket.assigned_queue = (
        "Manual Review" if needs_review else QUEUES.get(triage.category, "General Support")
    )
    return ticket

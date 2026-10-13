"""Unit tests for the routing policy. No API key needed: run  pytest"""
from app.models import Ticket, TriageResult
from app.router import apply_routing


def make_triage(**overrides) -> TriageResult:
    values = dict(category="billing", category_confidence=0.9, priority_score=1.0,
                  priority_confidence=0.9, escalate_probability=0.05,
                  refund_probability=0.05, model="test")
    values.update(overrides)
    return TriageResult(**values)


def new_ticket() -> Ticket:
    return Ticket(title="t", description="d", customer_email="a@b.com")


def test_billing_goes_to_billing_team():
    t = apply_routing(new_ticket(), make_triage(category="billing"))
    assert t.assigned_queue == "Billing Team"
    assert t.priority_label == "Medium"


def test_low_confidence_goes_to_manual_review():
    t = apply_routing(new_ticket(), make_triage(category_confidence=0.4))
    assert t.needs_review
    assert t.assigned_queue == "Manual Review"


def test_escalation_bumps_priority_to_at_least_high():
    t = apply_routing(new_ticket(), make_triage(priority_score=0.0, escalate_probability=0.95))
    assert t.escalated
    assert t.priority_label == "High"
    assert t.sla_hours == 8


def test_critical_priority():
    t = apply_routing(new_ticket(), make_triage(category="technical", priority_score=2.8))
    assert t.priority_label == "Critical"
    assert t.assigned_queue == "Engineering Support"

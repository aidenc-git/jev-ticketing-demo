"""Ticket triage with TypeSafe's Jev model, plus an offline mock.

Jev takes a *state* (the ticket text) and typed *questions*, and returns
typed answers with probabilities. All questions run in one parallel call.
"""
from __future__ import annotations

import os

from app.models import TriageResult

JEV_MODEL = "jev-1.13.0"  # pin the version so results don't shift when jev-latest moves

# Choice question: each key is a label Jev can return, each value describes it.
CATEGORIES = {
    "billing": "Charges, invoices, refunds, plans, or payment methods",
    "technical": "Bugs, errors, crashes, outages, or integrations that don't work",
    "account": "Login, passwords, access, permissions, or profile settings",
    "feature_request": "Asks for something the product does not do yet",
    "other": None,
}

# Score question: levels ordered low -> high. Jev returns a weighted position (0.0-3.0).
PRIORITY_LEVELS = [
    "Low: a question or minor inconvenience with no deadline",
    "Medium: something is broken but there is a workaround",
    "High: blocks the customer's work or affects many users",
    "Critical: outage, security problem, data loss, or money at risk right now",
]


def build_questions():
    from typesafe_sdk import Choice, Noul, Score

    return {
        "category": Choice(
            instructions="Which support team should handle `ticket`?",
            criteria=CATEGORIES,
        ),
        "priority": Score(
            instructions="How urgent is `ticket`?",
            criteria=PRIORITY_LEVELS,
        ),
        "escalate": Noul(
            instructions="Does `ticket` mention a security issue, legal action, "
            "or a threat to cancel?",
        ),
        "refund": Noul(
            instructions="Does `ticket` explicitly ask for a refund or money back?",
        ),
    }


class JevTriager:
    """Calls the real Jev model through the official typesafe-sdk."""

    name = "Jev (TypeSafe AI)"

    def __init__(self, model: str = JEV_MODEL):
        from typesafe_sdk import TypeSafeClient  # reads TYPESAFE_API_KEY

        self.client = TypeSafeClient(model=model)
        self.questions = build_questions()

    def triage(self, title: str, description: str) -> TriageResult:
        response = self.client.system_one(
            state={"ticket": f"{title}\n\n{description}"},
            questions=self.questions,
        )
        category = response.choices["category"]
        priority = response.scores["priority"]
        return TriageResult(
            category=category.choice,
            category_confidence=category.confidence,
            priority_score=priority.score,
            priority_confidence=priority.confidence,
            escalate_probability=response.nouls["escalate"].noul,
            refund_probability=response.nouls["refund"].noul,
            model=response.model,
        )

    def close(self) -> None:
        self.client.close()


class MockTriager:
    """Keyword-based stand-in with the same output shape as Jev.

    Lets the demo run without an API key (TypeSafe access is waitlisted).
    """

    name = "Offline mock (keyword rules)"

    KEYWORDS = {
        "billing": ["charge", "invoice", "refund", "payment", "bill", "subscription", "price"],
        "technical": ["error", "bug", "crash", "broken", "fail", "500", "timeout",
                      "not working", "down", "export"],
        "account": ["login", "log in", "password", "locked", "access", "2fa", "sign in"],
        "feature_request": ["would love", "feature", "please add", "wish", "could you add",
                            "dark mode"],
    }
    CRITICAL = ["outage", "security", "hacked", "data loss", "breach", "urgent", "asap"]
    HIGH = ["can't", "cannot", "blocked", "everyone", "whole team", "deadline", "board meeting"]
    ESCALATE = ["security", "hacked", "breach", "lawyer", "legal", "cancel"]
    REFUND = ["refund", "money back"]

    def triage(self, title: str, description: str) -> TriageResult:
        text = f"{title} {description}".lower()
        hits = {cat: sum(w in text for w in words) for cat, words in self.KEYWORDS.items()}
        total = sum(hits.values())
        if total == 0:
            category, confidence = "other", 0.65
        else:
            category = max(hits, key=hits.get)
            confidence = round(0.4 + 0.6 * hits[category] / total, 2)

        if any(w in text for w in self.CRITICAL):
            priority = 3.0
        elif any(w in text for w in self.HIGH):
            priority = 2.0
        elif category in ("technical", "billing"):
            priority = 1.0
        else:
            priority = 0.0

        return TriageResult(
            category=category,
            category_confidence=confidence,
            priority_score=priority,
            priority_confidence=0.8,
            escalate_probability=0.9 if any(w in text for w in self.ESCALATE) else 0.05,
            refund_probability=0.9 if any(w in text for w in self.REFUND) else 0.05,
            model="mock-keyword-v1",
        )

    def close(self) -> None:
        pass


def get_triager():
    """Use real Jev when an API key is set, otherwise fall back to the mock."""
    if os.getenv("TYPESAFE_API_KEY") and os.getenv("JEV_MOCK") != "1":
        try:
            return JevTriager()
        except ImportError:
            print("typesafe-sdk is not installed; using the offline mock.")
    return MockTriager()

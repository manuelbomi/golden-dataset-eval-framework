"""The fixed label taxonomy annotators tag conversation snippets with.

This lives in one place (not scattered across the frontend, the DB schema,
and the eval harness as three copies that can drift) because every other
module in this repo imports it: the annotation API validates against it,
the frontend fetches it to render the label picker, and the eval harness
uses it to build the confusion matrix axes.

Adding a new label is a one-line change here plus a migration for any
column that encodes it as a fixed-width type -- see docs/adr/ for why we
store labels as strings rather than a Postgres ENUM (schema-migration cost
of adding a label to an ENUM vs. a plain CHECK-less string column).
"""

from __future__ import annotations

SIGNAL_LABELS: list[str] = [
    "OBJECTION",
    "BUYING_SIGNAL",
    "COMPLIANCE_RISK",
    "QUESTION",
    "ACTION_ITEM",
    "NEUTRAL",
]

# A short human-readable description per label -- shown in the annotation UI
# as a tooltip so annotators don't have to memorize a style guide.
SIGNAL_DESCRIPTIONS: dict[str, str] = {
    "OBJECTION": "The speaker raises a concern, hesitation, or pushback.",
    "BUYING_SIGNAL": "The speaker expresses interest, urgency, or intent to proceed.",
    "COMPLIANCE_RISK": "The snippet contains language that could create regulatory "
    "or policy risk if left unaddressed (e.g. an unqualified guarantee).",
    "QUESTION": "The speaker asks a direct question that expects an answer.",
    "ACTION_ITEM": "A concrete next step or commitment is stated.",
    "NEUTRAL": "None of the above -- small talk, filler, or pure narration.",
}


def is_valid_label(label: str) -> bool:
    return label in SIGNAL_LABELS

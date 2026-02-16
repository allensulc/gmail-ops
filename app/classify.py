import re
from dataclasses import dataclass

@dataclass
class Classification:
    category: str
    priority: int
    label_short: str  # one primary OPS label

def classify(subject: str, snippet: str, from_header: str) -> Classification:
    text = f"{subject}\n{snippet}\n{from_header}".lower()

    # v1 simple heuristics (we'll replace with LLM scoring later)
    urgent = any(k in text for k in ["urgent", "asap", "immediately", "final notice", "overdue", "past due"])
    money = any(k in text for k in ["statement", "invoice", "receipt", "payment", "due", "bank", "credit card"])
    action = any(k in text for k in ["please reply", "can you", "could you", "confirm", "approve", "review", "sign"])
    deadline = bool(re.search(r"\b(today|tomorrow|deadline|due date|by end of day)\b", text))

    if urgent:
        return Classification(category="time_sensitive", priority=95, label_short="TIME_SENSITIVE")
    if money and (deadline or action):
        return Classification(category="finance", priority=90, label_short="FINANCE")
    if action:
        return Classification(category="action_required", priority=85, label_short="ACTION_REQUIRED")
    if money:
        return Classification(category="finance", priority=70, label_short="FINANCE")
    if deadline:
        return Classification(category="time_sensitive", priority=75, label_short="TIME_SENSITIVE")

    # default
    return Classification(category="watchlist", priority=60, label_short="WATCHLIST")

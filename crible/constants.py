"""Constants and enums for Crible."""
from typing import List


class Severity:
    """Severity levels for findings."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    ALL: List[str] = [CRITICAL, WARNING, INFO]


class ReviewDecision:
    """Review decision types."""
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    ANNOTATED = "annotated"


# Severity display styling
SEVERITY_EMOJI = {
    Severity.CRITICAL: "🔴",
    Severity.WARNING: "⚠️",
    Severity.INFO: "ℹ️",
}

SEVERITY_STYLE = {
    Severity.CRITICAL: "bold red",
    Severity.WARNING: "bold yellow",
    Severity.INFO: "bold blue",
}

# Review decision display
REVIEW_DECISION_EMOJI = {
    ReviewDecision.ACCEPTED: "✅",
    ReviewDecision.DISMISSED: "❌",
    ReviewDecision.ANNOTATED: "📝",
}

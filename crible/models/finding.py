"""Data model for assessment findings."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Finding:
    """Represents a single quality assessment finding from a layer.

    Attributes:
        layer_id: Layer number (0-3)
        layer_name: Human-readable layer name
        category: Finding category (e.g., "methodological_ambiguity")
        severity: One of "critical", "warning", or "info"
        location: Where in the skill file this applies (e.g., "step 3", "line 45-52")
        description: What the issue is
        recommendation: How to address it
        confidence: Optional confidence score (0.0-1.0), used primarily by Layer 2
        review_decision: User's review decision ("accepted", "dismissed", "annotated")
        review_note: User's reason for dismissal or annotation text
    """
    layer_id: int
    layer_name: str
    category: str
    severity: str  # "critical" | "warning" | "info"
    location: str
    description: str
    recommendation: str
    confidence: Optional[float] = None
    review_decision: Optional[str] = None  # "accepted" | "dismissed" | "annotated"
    review_note: Optional[str] = None

    def __post_init__(self):
        """Validate severity value."""
        valid_severities = {"critical", "warning", "info"}
        if self.severity not in valid_severities:
            raise ValueError(f"severity must be one of {valid_severities}, got {self.severity}")

        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")

        if self.review_decision is not None:
            valid_decisions = {"accepted", "dismissed", "annotated"}
            if self.review_decision not in valid_decisions:
                raise ValueError(
                    f"review_decision must be one of {valid_decisions}, got {self.review_decision}"
                )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "layer_id": self.layer_id,
            "layer_name": self.layer_name,
            "category": self.category,
            "severity": self.severity,
            "location": self.location,
            "description": self.description,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "review_decision": self.review_decision,
            "review_note": self.review_note,
        }

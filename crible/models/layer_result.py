"""Data model for layer execution results."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from .finding import Finding


@dataclass
class LayerResult:
    """Result of executing a single assessment layer.

    Attributes:
        success: Whether the layer executed successfully
        findings: List of findings produced by this layer (empty if failed)
        summary: Condensed summary for downstream context (empty if failed)
        structured_data: Structured data for downstream layers (optional)
        error: Error message if execution failed
    """
    success: bool
    findings: List[Finding] = field(default_factory=list)
    summary: str = ""
    structured_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

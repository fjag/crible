"""Data model for layer execution results."""
from dataclasses import dataclass
from typing import List, Optional
from .finding import Finding


@dataclass
class LayerResult:
    """Result of executing a single assessment layer.

    Attributes:
        success: Whether the layer executed successfully
        findings: List of findings produced by this layer (empty if failed)
        summary: Condensed summary for downstream context (empty if failed)
        error: Error message if execution failed
    """
    success: bool
    findings: List[Finding] = None
    summary: str = ""
    error: Optional[str] = None

    def __post_init__(self):
        """Initialize empty findings list if None."""
        if self.findings is None:
            self.findings = []

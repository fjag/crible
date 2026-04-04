"""Data model for assessment reports."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any
from .finding import Finding
from crible.constants import Severity, ReviewDecision


@dataclass
class Report:
    """Aggregated assessment report containing all findings from all layers.

    Attributes:
        skill_file_path: Path to the assessed skill file
        timestamp: When the assessment was run
        findings: List of all findings from all layers
        layer_summaries: Condensed summary of each layer's output (for context chaining)
        execution_metadata: Additional info (model used, token counts, errors, etc.)
    """
    skill_file_path: str
    timestamp: datetime
    findings: List[Finding]
    layer_summaries: Dict[int, str] = field(default_factory=dict)
    execution_metadata: Dict[str, Any] = field(default_factory=dict)

    def findings_by_severity(self) -> Dict[str, List[Finding]]:
        """Group findings by severity level.

        Returns:
            Dict with keys "critical", "warning", "info", each containing a list of findings
        """
        grouped = {s: [] for s in Severity.ALL}
        for finding in self.findings:
            if finding.severity in grouped:
                grouped[finding.severity].append(finding)
        return grouped

    def findings_by_layer(self) -> Dict[int, List[Finding]]:
        """Group findings by layer.

        Returns:
            Dict with layer IDs as keys, each containing a list of findings
        """
        grouped: Dict[int, List[Finding]] = {}
        for finding in self.findings:
            if finding.layer_id not in grouped:
                grouped[finding.layer_id] = []
            grouped[finding.layer_id].append(finding)
        return grouped

    def summary_stats(self) -> Dict[str, Any]:
        """Generate summary statistics for the report.

        Returns:
            Dict containing counts and other summary metrics
        """
        by_severity = self.findings_by_severity()
        by_layer = self.findings_by_layer()

        review_stats = {
            ReviewDecision.ACCEPTED: sum(1 for f in self.findings if f.review_decision == ReviewDecision.ACCEPTED),
            ReviewDecision.DISMISSED: sum(1 for f in self.findings if f.review_decision == ReviewDecision.DISMISSED),
            ReviewDecision.ANNOTATED: sum(1 for f in self.findings if f.review_decision == ReviewDecision.ANNOTATED),
        }

        return {
            "total_findings": len(self.findings),
            "by_severity": {
                Severity.CRITICAL: len(by_severity[Severity.CRITICAL]),
                Severity.WARNING: len(by_severity[Severity.WARNING]),
                Severity.INFO: len(by_severity[Severity.INFO]),
            },
            "by_layer": {str(layer_id): len(findings) for layer_id, findings in by_layer.items()},
            "reviewed": any(f.review_decision is not None for f in self.findings),
            **review_stats,
        }

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "skill_file": self.skill_file_path,
            "timestamp": self.timestamp.isoformat(),
            "model": self.execution_metadata.get("model", "unknown"),
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary_stats(),
            "layer_summaries": self.layer_summaries,
            "execution_metadata": self.execution_metadata,
        }

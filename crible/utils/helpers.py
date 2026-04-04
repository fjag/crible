"""Helper utilities for Crible."""
from typing import List, Dict, TYPE_CHECKING

from crible.constants import Severity

if TYPE_CHECKING:
    from crible.models import Finding


def count_severities(findings: List["Finding"]) -> Dict[str, int]:
    """Count findings by severity level.

    Args:
        findings: List of Finding objects

    Returns:
        Dict with counts for each severity level (critical, warning, info)
    """
    counts = {Severity.CRITICAL: 0, Severity.WARNING: 0, Severity.INFO: 0}
    for f in findings:
        if f.severity in counts:
            counts[f.severity] += 1
    return counts

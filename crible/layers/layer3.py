"""Layer 3: Domain Constraint Checking."""
from typing import List, Dict, Tuple, Any, Optional
from crible.layers.base import Layer
from crible.models import Finding
from crible.utils import AnthropicClient, ParseError, count_severities
from crible.constants import Severity
from crible.prompts.layer3_prompt import build_layer3_prompt


class Layer3(Layer):
    """Layer 3: Domain constraint checking.

    Validates methodological appropriateness given inferred data context.
    Depends on Layer 2's execution trace.
    """

    def __init__(self, llm_client: AnthropicClient):
        super().__init__(llm_client, layer_id=3, layer_name="Domain Constraints")
        self._structured_context: Dict[int, Dict[str, Any]] = {}

    def set_structured_context(self, structured_context: Dict[int, Dict[str, Any]]) -> None:
        """Set structured context from upstream layers.

        Args:
            structured_context: Dict mapping layer IDs to their structured data
        """
        self._structured_context = structured_context

    def build_prompt(self, skill_content: str, upstream_context: Dict[int, str]) -> str:
        """Build Layer 3 prompt.

        Args:
            skill_content: Skill file content
            upstream_context: Summaries from previous layers (especially Layer 2)

        Returns:
            Complete prompt string
        """
        # Try to get data from structured context first (preferred)
        layer2_data = self._structured_context.get(2, {})

        if layer2_data:
            # Use structured data directly - no parsing needed
            data_type = layer2_data.get("data_type", "unknown")
            organism = layer2_data.get("organism", "unknown")
            trace_confidence = layer2_data.get("trace_confidence", 0.0)
        else:
            # Fallback: parse from summary string (legacy support)
            data_type, organism, trace_confidence = self._parse_layer2_summary(
                upstream_context.get(2, "")
            )

        return build_layer3_prompt(skill_content, data_type, organism, trace_confidence)

    def _parse_layer2_summary(self, summary: str) -> Tuple[str, str, float]:
        """Parse Layer 2 summary string to extract context data.

        This is a fallback for when structured_data is not available.

        Args:
            summary: Layer 2 summary string

        Returns:
            Tuple of (data_type, organism, trace_confidence)
        """
        data_type = "unknown"
        organism = "unknown"
        trace_confidence = 0.0

        if summary:
            # Parse summary string to extract values
            # Format: "Inferred data type: X (confidence: Y). Organism: Z. Traced N steps..."
            parts = summary.split(". ")
            for part in parts:
                if "Inferred data type:" in part:
                    data_type = part.split("Inferred data type:")[1].strip().split(" (")[0]
                elif "Organism:" in part:
                    organism = part.split("Organism:")[1].strip()
                elif "average confidence" in part:
                    try:
                        conf_str = part.split("average confidence")[1].strip().split()[0]
                        trace_confidence = float(conf_str)
                    except (IndexError, ValueError):
                        pass

        return data_type, organism, trace_confidence

    def parse_response(self, response: str) -> Tuple[List[Finding], str]:
        """Parse domain violation findings from XML response.

        Args:
            response: XML response from LLM

        Returns:
            Tuple of (findings list, summary for downstream layers)

        Raises:
            ParseError: If response cannot be parsed
        """
        try:
            # Use XMLParser to extract findings
            findings = self.xml_parser.parse_findings(
                response,
                self.layer_id,
                self.layer_name,
                default_category="domain_violation"
            )

            # Enhance findings with explanation field if present
            root = self.xml_parser.parse(response)

            violation_elements = root.findall('.//violation')
            for i, elem in enumerate(violation_elements):
                if i < len(findings):
                    explanation = elem.findtext('explanation', '')
                    if explanation:
                        # Append explanation to recommendation
                        findings[i].recommendation = explanation

            # Generate summary
            if not findings:
                summary = "No domain constraint violations found."
            else:
                severity_counts = count_severities(findings)

                summary = (
                    f"Found {len(findings)} domain constraint issues: "
                    f"{severity_counts[Severity.CRITICAL]} critical, "
                    f"{severity_counts[Severity.WARNING]} warnings, "
                    f"{severity_counts[Severity.INFO]} info. "
                )

                # List top categories
                categories = {}
                for finding in findings:
                    categories[finding.category] = categories.get(finding.category, 0) + 1

                top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:2]
                summary += f"Main issues: {', '.join(cat for cat, _ in top_categories)}."

            return findings, summary

        except ParseError:
            raise  # Re-raise ParseError from xml_parser
        except Exception as e:
            raise ParseError(f"Unexpected error parsing domain violations: {e}")

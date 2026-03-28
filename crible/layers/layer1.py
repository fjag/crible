"""Layer 1: Instruction Ambiguity Scoring."""
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple
from crible.layers.base import Layer
from crible.models import Finding
from crible.utils import AnthropicClient, ParseError
from crible.prompts.layer1_prompt import build_layer1_prompt


class Layer1(Layer):
    """Layer 1: Instruction ambiguity scoring.

    Assesses how many plausible interpretations exist for each step.
    """

    AMBIGUITY_TO_SEVERITY = {
        "HIGH": "critical",
        "MEDIUM": "warning",
        "LOW": "info",
    }

    def __init__(self, llm_client: AnthropicClient):
        super().__init__(llm_client, layer_id=1, layer_name="Ambiguity Scoring")

    def build_prompt(self, skill_content: str, upstream_context: Dict[int, str]) -> str:
        """Build Layer 1 prompt.

        Args:
            skill_content: Skill file content
            upstream_context: Summaries from previous layers (Layer 0 if present)

        Returns:
            Complete prompt string
        """
        return build_layer1_prompt(skill_content)

    def parse_response(self, response: str) -> Tuple[List[Finding], str]:
        """Parse ambiguity findings from XML response.

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
                default_category="methodological_ambiguity"
            )

            # Map ambiguity_score to severity if present in response
            # (XMLParser gives us default severity, but we can override based on ambiguity_score)
            wrapped = f"<root>{response}</root>"
            root = ET.fromstring(wrapped)

            finding_elements = root.findall('.//finding')
            for i, elem in enumerate(finding_elements):
                if i < len(findings):
                    ambiguity_score = elem.findtext('ambiguity_score', '').upper()
                    if ambiguity_score in self.AMBIGUITY_TO_SEVERITY:
                        findings[i].severity = self.AMBIGUITY_TO_SEVERITY[ambiguity_score]

                    # Also extract additional details for description
                    interpretations = elem.findtext('plausible_interpretations', 'unknown')
                    aspects = elem.findtext('ambiguous_aspects', '')
                    consequence = elem.findtext('consequence', '')
                    resolution = elem.findtext('resolution', '')

                    findings[i].description = (
                        f"Ambiguity level: {ambiguity_score}. "
                        f"Plausible interpretations: {interpretations}. "
                        f"Ambiguous aspects: {aspects}. "
                        f"Consequence: {consequence}."
                    )
                    findings[i].recommendation = resolution if resolution else findings[i].recommendation

            # Generate summary
            severity_counts = {"critical": 0, "warning": 0, "info": 0}
            for finding in findings:
                severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1

            high_ambiguity_locations = [
                f.location for f in findings if f.severity == "critical"
            ]

            summary = (
                f"Identified {len(findings)} ambiguous steps: "
                f"{severity_counts['critical']} high-ambiguity, "
                f"{severity_counts['warning']} medium-ambiguity, "
                f"{severity_counts['info']} low-ambiguity. "
            )

            if high_ambiguity_locations:
                summary += f"High-ambiguity locations: {', '.join(high_ambiguity_locations[:3])}."

            return findings, summary

        except ET.ParseError as e:
            # Show snippet of response to help debug
            snippet = response[:500] if len(response) > 500 else response
            raise ParseError(
                f"Failed to parse ambiguity findings XML: {e}\n"
                f"Response snippet: {snippet}\n"
                f"Tip: LLM may have used unescaped < > & characters. "
                f"Try running again or use --skip-layer 1"
            )
        except Exception as e:
            raise ParseError(f"Unexpected error parsing ambiguity findings: {e}")

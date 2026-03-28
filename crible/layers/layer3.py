"""Layer 3: Domain Constraint Checking."""
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple
from crible.layers.base import Layer
from crible.models import Finding
from crible.utils import AnthropicClient, ParseError
from crible.utils.xml_parser import clean_xml_response
from crible.prompts.layer3_prompt import build_layer3_prompt


class Layer3(Layer):
    """Layer 3: Domain constraint checking.

    Validates methodological appropriateness given inferred data context.
    Depends on Layer 2's execution trace.
    """

    def __init__(self, llm_client: AnthropicClient):
        super().__init__(llm_client, layer_id=3, layer_name="Domain Constraints")

    def build_prompt(self, skill_content: str, upstream_context: Dict[int, str]) -> str:
        """Build Layer 3 prompt.

        Args:
            skill_content: Skill file content
            upstream_context: Summaries from previous layers (especially Layer 2)

        Returns:
            Complete prompt string
        """
        # Extract data type, organism, and trace confidence from Layer 2 summary
        layer2_summary = upstream_context.get(2, "")

        data_type = "unknown"
        organism = "unknown"
        trace_confidence = 0.0

        if layer2_summary:
            # Parse summary string to extract values
            # Format: "Inferred data type: X (confidence: Y). Organism: Z. Traced N steps..."
            parts = layer2_summary.split(". ")
            for part in parts:
                if "Inferred data type:" in part:
                    data_type = part.split("Inferred data type:")[1].strip().split(" (")[0]
                elif "Organism:" in part:
                    organism = part.split("Organism:")[1].strip()
                elif "average confidence" in part:
                    # Extract confidence value
                    try:
                        conf_str = part.split("average confidence")[1].strip().split()[0]
                        trace_confidence = float(conf_str)
                    except (IndexError, ValueError):
                        pass

        return build_layer3_prompt(skill_content, data_type, organism, trace_confidence)

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
            # Clean the XML first (fix common LLM issues)
            cleaned_xml = clean_xml_response(response)
            wrapped = f"<root>{cleaned_xml}</root>"
            root = ET.fromstring(wrapped)

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
                severity_counts = {"critical": 0, "warning": 0, "info": 0}
                for finding in findings:
                    severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1

                summary = (
                    f"Found {len(findings)} domain constraint issues: "
                    f"{severity_counts['critical']} critical, "
                    f"{severity_counts['warning']} warnings, "
                    f"{severity_counts['info']} info. "
                )

                # List top categories
                categories = {}
                for finding in findings:
                    categories[finding.category] = categories.get(finding.category, 0) + 1

                top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:2]
                summary += f"Main issues: {', '.join(cat for cat, _ in top_categories)}."

            return findings, summary

        except ET.ParseError as e:
            # Show snippet of response to help debug
            snippet = response[:500] if len(response) > 500 else response
            raise ParseError(
                f"Failed to parse domain violations XML: {e}\n"
                f"Response snippet: {snippet}\n"
                f"Tip: LLM may have used unescaped < > & characters. "
                f"Try running again or use --skip-layer 3"
            )
        except Exception as e:
            raise ParseError(f"Unexpected error parsing domain violations: {e}")

"""Layer 0: Dependency Extraction (Stub)."""
from typing import List, Dict, Tuple
from crible.layers.base import Layer
from crible.models import Finding
from crible.utils import AnthropicClient, ParseError
from crible.prompts.layer0_prompt import build_layer0_prompt


class Layer0(Layer):
    """Layer 0: Dependency extraction.

    Identifies external dependencies but does NOT validate them.
    Validation requires live API calls to package registries (deferred to v2).
    """

    def __init__(self, llm_client: AnthropicClient):
        super().__init__(llm_client, layer_id=0, layer_name="Dependency Extraction")

    def build_prompt(self, skill_content: str, upstream_context: Dict[int, str]) -> str:
        """Build Layer 0 prompt.

        Args:
            skill_content: Skill file content
            upstream_context: Summaries from previous layers (none for Layer 0)

        Returns:
            Complete prompt string
        """
        return build_layer0_prompt(skill_content)

    def parse_response(self, response: str) -> Tuple[List[Finding], str]:
        """Parse dependency extraction from XML response.

        Args:
            response: XML response from LLM

        Returns:
            Tuple of (findings list, summary for downstream layers)

        Raises:
            ParseError: If response cannot be parsed
        """
        try:
            root = self.xml_parser.parse(response)

            findings = []
            dependencies = root.findall('.//dependency')

            dep_types = {}

            for dep_elem in dependencies:
                dep_type = dep_elem.findtext('type', 'unknown')
                name = dep_elem.findtext('name', 'unnamed')
                version = dep_elem.findtext('version', 'unspecified')
                location = dep_elem.findtext('location', 'overall')
                note = dep_elem.findtext('note', 'Validation not performed.')

                # Count by type
                dep_types[dep_type] = dep_types.get(dep_type, 0) + 1

                # Create informational finding for each dependency
                description = f"Dependency identified: {name}"
                if version != "unspecified" and version != "N/A":
                    description += f" (version {version})"
                description += f". Type: {dep_type}."

                finding = Finding(
                    layer_id=self.layer_id,
                    layer_name=self.layer_name,
                    category="dependency_identified",
                    severity="info",
                    location=location,
                    description=description,
                    recommendation=note,
                )
                findings.append(finding)

            # Generate summary
            total_deps = len(findings)
            if total_deps == 0:
                summary = "No external dependencies identified."
            else:
                type_counts = ", ".join(f"{count} {dtype}" for dtype, count in dep_types.items())
                summary = f"Identified {total_deps} dependencies: {type_counts}. Validation not performed (requires live registry integration)."

            return findings, summary

        except ParseError:
            raise  # Re-raise ParseError from xml_parser
        except Exception as e:
            raise ParseError(f"Unexpected error parsing dependencies: {e}")

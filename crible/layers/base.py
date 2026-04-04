"""Base class for assessment layers."""
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple
from crible.models import Finding, LayerResult
from crible.utils import AnthropicClient, XMLParser, ParseError, LLMClientError


class Layer(ABC):
    """Abstract base class for assessment layers.

    Each layer implements prompt construction and response parsing.
    Execution logic is shared via the template method pattern.

    Attributes:
        llm_client: Client for calling the LLM API
        layer_id: Numeric identifier (0-3)
        layer_name: Human-readable name
        xml_parser: Parser for XML-tagged responses
    """

    def __init__(self, llm_client: AnthropicClient, layer_id: int, layer_name: str):
        """Initialize the layer.

        Args:
            llm_client: Anthropic client instance
            layer_id: Layer number (0-3)
            layer_name: Human-readable layer name
        """
        self.llm_client = llm_client
        self.layer_id = layer_id
        self.layer_name = layer_name
        self.xml_parser = XMLParser()

    @abstractmethod
    def build_prompt(self, skill_content: str, upstream_context: Dict[int, str]) -> str:
        """Construct the prompt for this layer.

        Args:
            skill_content: Content of the skill file being assessed
            upstream_context: Dict mapping layer IDs to their summary outputs

        Returns:
            Complete prompt string to send to LLM
        """
        pass

    @abstractmethod
    def parse_response(self, response: str) -> Tuple[List[Finding], str]:
        """Parse LLM response into findings and summary.

        Args:
            response: Raw text response from LLM

        Returns:
            Tuple of (findings list, condensed summary for downstream layers)

        Raises:
            ParseError: If response cannot be parsed
        """
        pass

    def execute(self, skill_content: str, upstream_context: Dict[int, str]) -> LayerResult:
        """Execute this layer: build prompt, call LLM, parse response.

        This is the template method that orchestrates the layer execution.

        Args:
            skill_content: Content of the skill file
            upstream_context: Summaries from previously executed layers

        Returns:
            LayerResult with findings and summary, or error information
        """
        try:
            # Build the prompt
            prompt = self.build_prompt(skill_content, upstream_context)

            # Call LLM
            response = self.llm_client.generate(prompt)

            # Parse response
            findings, summary = self.parse_response(response)

            return LayerResult(
                success=True,
                findings=findings,
                summary=summary,
            )

        except (ParseError, LLMClientError) as e:
            # Known error types
            return LayerResult(
                success=False,
                error=str(e),
            )

        except Exception as e:
            # Unexpected errors
            return LayerResult(
                success=False,
                error=f"Unexpected error: {type(e).__name__}: {e}",
            )

    def _format_upstream_context(self, upstream_context: Dict[int, str]) -> str:
        """Format upstream layer summaries for inclusion in prompts.

        Args:
            upstream_context: Dict mapping layer IDs to summaries

        Returns:
            Formatted string of upstream context
        """
        if not upstream_context:
            return ""

        formatted = []
        for layer_id in sorted(upstream_context.keys()):
            if layer_id < self.layer_id:  # Only include earlier layers
                formatted.append(f"Layer {layer_id} summary: {upstream_context[layer_id]}")

        return "\n".join(formatted) if formatted else ""

    def _handle_parse_error(self, error: Exception, response: str) -> ParseError:
        """Create a standardized ParseError with context.

        Args:
            error: The original exception (typically ET.ParseError)
            response: The raw response that failed to parse

        Returns:
            ParseError with helpful context for debugging
        """
        snippet = response[:500] if len(response) > 500 else response
        return ParseError(
            f"Failed to parse {self.layer_name} XML: {error}\n"
            f"Response snippet: {snippet}\n"
            f"Tip: LLM may have used unescaped < > & characters. "
            f"Try running again or use --skip-layer {self.layer_id}"
        )

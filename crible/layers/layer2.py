"""Layer 2: Simulated Execution Trace."""
from typing import List, Dict, Tuple, Any
from crible.layers.base import Layer
from crible.models import Finding, LayerResult
from crible.utils import ParseError, AnthropicClient, LLMClientError
from crible.prompts.layer2_prompt import build_layer2_prompt


class Layer2(Layer):
    """Layer 2: Simulated execution trace.

    Predicts data flow through the skill without executing code.
    This is the highest-risk layer in terms of LLM capability.
    """

    def __init__(self, llm_client: AnthropicClient):
        super().__init__(llm_client, layer_id=2, layer_name="Simulated Execution")

    def build_prompt(self, skill_content: str, upstream_context: Dict[int, str]) -> str:
        """Build Layer 2 prompt.

        Args:
            skill_content: Skill file content
            upstream_context: Summaries from previous layers

        Returns:
            Complete prompt string
        """
        # Get Layer 1 summary if available
        layer1_summary = upstream_context.get(1, "")
        return build_layer2_prompt(skill_content, layer1_summary)

    def parse_response(self, response: str) -> Tuple[List[Finding], str, Dict[str, Any]]:
        """Parse execution trace XML response.

        Args:
            response: XML response from LLM

        Returns:
            Tuple of (findings list, summary string, structured data dict)

        Raises:
            ParseError: If response cannot be parsed
        """
        try:
            # Parse the XML response
            root = self.xml_parser.parse(response)

            findings = []

            # Extract inferred input info
            inferred_input = root.find('.//inferred_input')
            data_type = "unknown"
            organism = "unknown"
            input_confidence = 0.0

            if inferred_input is not None:
                data_type = inferred_input.findtext('data_type', 'unknown')
                organism = inferred_input.findtext('organism', 'unknown')
                input_conf_text = inferred_input.findtext('confidence', '0.0')
                input_confidence = float(input_conf_text)

                # Create informational finding about inferred input
                data_format = inferred_input.findtext('format', 'unspecified')
                scale = inferred_input.findtext('scale', 'unspecified')
                design = inferred_input.findtext('experimental_design', 'unspecified')

                findings.append(Finding(
                    layer_id=self.layer_id,
                    layer_name=self.layer_name,
                    category="inferred_input",
                    severity="info",
                    location="overall",
                    description=f"Inferred input: {data_type} ({data_format}), organism: {organism}",
                    recommendation=f"Verify this matches your intended input. Scale: {scale}, Design: {design}",
                    confidence=input_confidence,
                ))

            # Extract trace steps and flag low-confidence ones
            trace = root.find('.//trace')
            step_confidences = []

            if trace is not None:
                for step_elem in trace.findall('.//step'):
                    location = step_elem.findtext('location', 'unknown')
                    operation = step_elem.findtext('operation', '')
                    conf_text = step_elem.findtext('confidence', '0.0')
                    confidence = float(conf_text)
                    note = step_elem.findtext('note', '')

                    step_confidences.append(confidence)

                    # Flag low-confidence trace steps
                    if confidence < 0.5:
                        findings.append(Finding(
                            layer_id=self.layer_id,
                            layer_name=self.layer_name,
                            category="uncertain_trace",
                            severity="warning",
                            location=location,
                            description=f"Execution trace uncertain for this step: {operation}",
                            recommendation=f"Clarify this step to enable confident tracing. {note}",
                            confidence=confidence,
                        ))

            # Calculate average trace confidence
            avg_confidence = sum(step_confidences) / len(step_confidences) if step_confidences else 0.0

            # Extract discrepancies as findings
            discrepancies = root.find('.//discrepancies')
            if discrepancies is not None:
                for disc in discrepancies.findall('.//discrepancy'):
                    location = disc.findtext('location', 'unknown')
                    severity = disc.findtext('severity', 'warning')
                    description = disc.findtext('description', '')
                    conf_text = disc.findtext('confidence', '0.7')
                    confidence = float(conf_text)

                    findings.append(Finding(
                        layer_id=self.layer_id,
                        layer_name=self.layer_name,
                        category="execution_discrepancy",
                        severity=severity,
                        location=location,
                        description=description,
                        recommendation="Review the data flow and ensure all dependencies are satisfied.",
                        confidence=confidence,
                    ))

            # Generate summary for downstream layers
            num_steps = len(step_confidences)
            num_discrepancies = len(discrepancies.findall('.//discrepancy')) if discrepancies is not None else 0

            summary = (
                f"Inferred data type: {data_type} (confidence: {input_confidence:.2f}). "
                f"Organism: {organism}. "
                f"Traced {num_steps} steps with average confidence {avg_confidence:.2f}. "
                f"Identified {num_discrepancies} discrepancies. "
            )

            if avg_confidence < 0.5:
                summary += "Note: Trace confidence is low - downstream findings may be tentative."

            # Return structured data for downstream layers
            structured_data = {
                "data_type": data_type,
                "organism": organism,
                "trace_confidence": avg_confidence,
                "input_confidence": input_confidence,
            }

            return findings, summary, structured_data

        except ParseError:
            raise  # Re-raise ParseError from xml_parser
        except ValueError as e:
            raise ParseError(f"Invalid numeric value in trace: {e}")
        except Exception as e:
            raise ParseError(f"Unexpected error parsing trace: {e}")

    def execute(self, skill_content: str, upstream_context: Dict[int, str]) -> LayerResult:
        """Execute Layer 2 with structured data for downstream layers.

        Overrides base class to include structured_data in result.

        Args:
            skill_content: Content of the skill file
            upstream_context: Summaries from previously executed layers

        Returns:
            LayerResult with findings, summary, and structured_data
        """
        try:
            prompt = self.build_prompt(skill_content, upstream_context)
            response = self.llm_client.generate(prompt)
            findings, summary, structured_data = self.parse_response(response)

            return LayerResult(
                success=True,
                findings=findings,
                summary=summary,
                structured_data=structured_data,
            )

        except (ParseError, LLMClientError) as e:
            return LayerResult(
                success=False,
                error=str(e),
            )

        except Exception as e:
            return LayerResult(
                success=False,
                error=f"Unexpected error: {type(e).__name__}: {e}",
            )

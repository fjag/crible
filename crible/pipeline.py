"""Pipeline orchestrator for running assessment layers."""
from datetime import datetime
from typing import List, Dict, Optional
import time

from crible.models import Report, Finding
from crible.layers.base import Layer
from crible.utils import AnthropicClient


class PipelineOrchestrator:
    """Orchestrates execution of assessment layers in sequence.

    Handles context passing between layers and dependency-aware error handling.
    """

    # Define layer dependencies: which layers depend on which
    LAYER_DEPENDENCIES = {
        0: [],      # Layer 0 is independent
        1: [],      # Layer 1 is independent
        2: [],      # Layer 2 is independent
        3: [2],     # Layer 3 depends on Layer 2's trace
    }

    def __init__(self, llm_client: AnthropicClient, layers: List[Layer]):
        """Initialize the orchestrator.

        Args:
            llm_client: Anthropic client for LLM calls
            layers: List of Layer instances to execute in order
        """
        self.llm_client = llm_client
        self.layers = sorted(layers, key=lambda l: l.layer_id)  # Ensure correct order

    def run(
        self,
        skill_file_path: str,
        skip_layers: Optional[List[int]] = None,
        verbose: bool = False
    ) -> Report:
        """Run the full assessment pipeline.

        Args:
            skill_file_path: Path to the skill file to assess
            skip_layers: List of layer IDs to skip (optional)
            verbose: If True, print progress messages

        Returns:
            Complete Report with all findings
        """
        skip_layers = skip_layers or []
        start_time = time.time()

        # Read skill file
        with open(skill_file_path, 'r', encoding='utf-8') as f:
            skill_content = f.read()

        if verbose:
            print(f"Assessing skill file: {skill_file_path}")
            print(f"Total layers to run: {len([l for l in self.layers if l.layer_id not in skip_layers])}")

        findings = []
        layer_summaries = {}
        upstream_context = {}
        failed_layers = set()

        for layer in self.layers:
            # Skip if requested
            if layer.layer_id in skip_layers:
                if verbose:
                    print(f"[Layer {layer.layer_id}] Skipped by user request")
                continue

            # Check dependencies
            dependencies_met, missing_deps = self._check_dependencies(
                layer.layer_id,
                failed_layers
            )

            if not dependencies_met:
                if verbose:
                    print(f"[Layer {layer.layer_id}] Skipped - dependencies failed: {missing_deps}")

                # Add error finding
                findings.append(Finding(
                    layer_id=layer.layer_id,
                    layer_name=layer.layer_name,
                    category="layer_skipped",
                    severity="warning",
                    location="layer execution",
                    description=f"Layer {layer.layer_id} skipped because prerequisite layers failed: {missing_deps}",
                    recommendation="Fix errors in prerequisite layers first.",
                ))
                failed_layers.add(layer.layer_id)
                continue

            # Execute layer
            if verbose:
                print(f"[Layer {layer.layer_id}] Executing: {layer.layer_name}")

            result = layer.execute(skill_content, upstream_context)

            if result.success:
                if verbose:
                    print(f"[Layer {layer.layer_id}] Success - found {len(result.findings)} findings")

                findings.extend(result.findings)
                layer_summaries[layer.layer_id] = result.summary
                upstream_context[layer.layer_id] = result.summary
            else:
                if verbose:
                    print(f"[Layer {layer.layer_id}] Failed: {result.error}")

                # Add error finding
                findings.append(Finding(
                    layer_id=layer.layer_id,
                    layer_name=layer.layer_name,
                    category="layer_error",
                    severity="warning",
                    location="layer execution",
                    description=f"Layer {layer.layer_id} failed: {result.error}",
                    recommendation="Review logs. This may affect downstream layers.",
                ))
                failed_layers.add(layer.layer_id)

        # Create report
        duration = time.time() - start_time

        if verbose:
            print(f"\nPipeline complete in {duration:.1f}s")
            print(f"Total findings: {len(findings)}")
            print(f"Token usage: {self.llm_client.get_token_count()}")

        report = Report(
            skill_file_path=skill_file_path,
            timestamp=datetime.now(),
            findings=findings,
            layer_summaries=layer_summaries,
            execution_metadata={
                "model": self.llm_client.model,
                "total_tokens": self.llm_client.get_token_count(),
                "duration_seconds": duration,
                "failed_layers": list(failed_layers),
                "skipped_layers": skip_layers,
            }
        )

        return report

    def _check_dependencies(
        self,
        layer_id: int,
        failed_layers: set
    ) -> tuple[bool, List[int]]:
        """Check if layer dependencies are met.

        Args:
            layer_id: Layer to check
            failed_layers: Set of layer IDs that have failed

        Returns:
            Tuple of (dependencies_met, list of missing dependency IDs)
        """
        dependencies = self.LAYER_DEPENDENCIES.get(layer_id, [])
        missing = [dep for dep in dependencies if dep in failed_layers]

        return len(missing) == 0, missing

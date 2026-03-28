"""Annotated markdown output renderer."""
import re
from typing import List, Dict
from crible.models import Report, Finding


class AnnotatedMarkdownRenderer:
    """Renders assessment reports as annotated markdown.

    Injects findings as inline annotations within the original skill file.
    """

    SEVERITY_EMOJI = {
        "critical": "🔴",
        "warning": "⚠️",
        "info": "ℹ️",
    }

    def __init__(self):
        pass

    def render(self, report: Report, skill_content: str) -> str:
        """Render report as annotated markdown.

        Args:
            report: The assessment report
            skill_content: Original skill file content

        Returns:
            Annotated markdown string
        """
        # Parse skill structure to identify sections/steps
        sections = self._parse_skill_structure(skill_content)

        # Group findings by location
        findings_by_location = self._group_findings_by_location(report.findings)

        # Build annotated output
        output_lines = []

        # Add header
        output_lines.append("# Crible Quality Assessment Report\n")
        output_lines.append(f"**Skill File:** {report.skill_file_path}  ")
        output_lines.append(f"**Assessment Date:** {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}  ")
        output_lines.append(f"**Model:** {report.execution_metadata.get('model', 'unknown')}  ")

        summary = report.summary_stats()
        output_lines.append(f"**Total Findings:** {summary['total_findings']} ")
        output_lines.append(f"({summary['by_severity']['critical']} critical, ")
        output_lines.append(f"{summary['by_severity']['warning']} warnings, ")
        output_lines.append(f"{summary['by_severity']['info']} info)\n")
        output_lines.append("---\n")

        # Add original content with annotations
        output_lines.append("## Original Skill File with Annotations\n")

        for i, section in enumerate(sections):
            # Add section content
            output_lines.append(section['content'])

            # Add findings for this section
            section_id = section['id']
            if section_id in findings_by_location:
                output_lines.append("")  # Blank line before annotations
                for finding in findings_by_location[section_id]:
                    annotation = self._format_annotation(finding)
                    output_lines.append(annotation)
                output_lines.append("")  # Blank line after annotations

        # Add findings that couldn't be mapped to specific locations
        unmapped = findings_by_location.get("overall", []) + findings_by_location.get("unknown", [])
        if unmapped:
            output_lines.append("\n---\n")
            output_lines.append("## General Findings\n")
            for finding in unmapped:
                annotation = self._format_annotation(finding)
                output_lines.append(annotation)
                output_lines.append("")

        # Add detailed findings section
        output_lines.append("\n---\n")
        output_lines.append("## All Findings (Detailed)\n")
        output_lines.append("\nComplete list of all findings with review decisions:\n")

        by_severity = report.findings_by_severity()
        for severity in ["critical", "warning", "info"]:
            severity_findings = by_severity[severity]
            if not severity_findings:
                continue

            emoji = self.SEVERITY_EMOJI[severity]
            output_lines.append(f"\n### {emoji} {severity.upper()} ({len(severity_findings)} findings)\n")

            for i, finding in enumerate(severity_findings, 1):
                output_lines.append(f"\n#### {i}. {finding.category.replace('_', ' ').title()}")
                output_lines.append(f"\n- **Layer:** {finding.layer_id} - {finding.layer_name}")
                output_lines.append(f"- **Location:** {finding.location}")
                output_lines.append(f"- **Issue:** {finding.description}")
                output_lines.append(f"- **Recommendation:** {finding.recommendation}")

                if finding.confidence is not None:
                    output_lines.append(f"- **Confidence:** {finding.confidence:.2f}")

                # Add review decision
                if finding.review_decision:
                    decision_emoji = {
                        "accepted": "✅",
                        "dismissed": "❌",
                        "annotated": "📝"
                    }.get(finding.review_decision, "•")
                    output_lines.append(f"- **Review Decision:** {decision_emoji} {finding.review_decision.title()}")

                    if finding.review_note:
                        output_lines.append(f"- **Review Note:** {finding.review_note}")
                else:
                    output_lines.append(f"- **Review Decision:** Not reviewed")

                output_lines.append("")  # Blank line between findings

        # Add summary section
        output_lines.append("\n---\n")
        output_lines.append("## Assessment Summary\n")

        # Findings by layer
        by_layer = report.findings_by_layer()
        output_lines.append("### Findings by Layer\n")
        for layer_id in sorted(by_layer.keys()):
            layer_findings = by_layer[layer_id]
            layer_name = layer_findings[0].layer_name if layer_findings else f"Layer {layer_id}"
            output_lines.append(f"**Layer {layer_id} ({layer_name}):** {len(layer_findings)} findings\n")

        # Findings by severity
        output_lines.append("\n### Findings by Severity\n")
        by_severity_count = report.findings_by_severity()
        for severity in ["critical", "warning", "info"]:
            emoji = self.SEVERITY_EMOJI[severity]
            count = len(by_severity_count[severity])
            output_lines.append(f"{emoji} **{severity.upper()}:** {count}\n")

        # Review statistics
        if any(f.review_decision for f in report.findings):
            output_lines.append("\n### Review Statistics\n")
            accepted = sum(1 for f in report.findings if f.review_decision == "accepted")
            dismissed = sum(1 for f in report.findings if f.review_decision == "dismissed")
            annotated = sum(1 for f in report.findings if f.review_decision == "annotated")
            not_reviewed = sum(1 for f in report.findings if not f.review_decision)

            output_lines.append(f"- ✅ **Accepted:** {accepted}\n")
            output_lines.append(f"- ❌ **Dismissed:** {dismissed}\n")
            output_lines.append(f"- 📝 **Annotated:** {annotated}\n")
            if not_reviewed > 0:
                output_lines.append(f"- ⚪ **Not Reviewed:** {not_reviewed}\n")

        # Metadata
        output_lines.append("\n### Execution Metadata\n")
        output_lines.append(f"- **Total Tokens:** {report.execution_metadata.get('total_tokens', 'N/A')}\n")
        output_lines.append(f"- **Duration:** {report.execution_metadata.get('duration_seconds', 0):.1f}s\n")

        failed = report.execution_metadata.get('failed_layers', [])
        if failed:
            output_lines.append(f"- **Failed Layers:** {', '.join(map(str, failed))}\n")

        return "\n".join(output_lines)

    def save(self, report: Report, skill_content: str, output_path: str):
        """Save annotated markdown to file.

        Args:
            report: The assessment report
            skill_content: Original skill file content
            output_path: Path to write markdown file
        """
        markdown = self.render(report, skill_content)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

    def _parse_skill_structure(self, skill_content: str) -> List[Dict]:
        """Parse skill content into sections.

        Args:
            skill_content: Original skill file content

        Returns:
            List of section dicts with 'id' and 'content'
        """
        sections = []
        lines = skill_content.split('\n')

        current_section = {"id": "header", "content": ""}
        section_counter = 0

        for line in lines:
            # Check if this is a step marker (various patterns)
            step_match = re.match(r'(?:#+\s*)?(?:step|Stage|Phase)\s+(\d+)', line, re.IGNORECASE)
            numbered_match = re.match(r'^(\d+)\.\s+', line)

            if step_match:
                # Save current section
                if current_section["content"]:
                    sections.append(current_section)

                # Start new section
                step_num = step_match.group(1)
                current_section = {"id": f"step {step_num}", "content": line + "\n"}
                section_counter += 1

            elif numbered_match:
                # Numbered list item (might be a step)
                # Save current section
                if current_section["content"]:
                    sections.append(current_section)

                # Start new section
                step_num = numbered_match.group(1)
                current_section = {"id": f"step {step_num}", "content": line + "\n"}
                section_counter += 1

            else:
                # Add to current section
                current_section["content"] += line + "\n"

        # Add final section
        if current_section["content"]:
            sections.append(current_section)

        return sections

    def _group_findings_by_location(self, findings: List[Finding]) -> Dict[str, List[Finding]]:
        """Group findings by their location.

        Args:
            findings: List of findings

        Returns:
            Dict mapping locations to finding lists
        """
        grouped = {}

        for finding in findings:
            location = finding.location.lower()
            if location not in grouped:
                grouped[location] = []
            grouped[location].append(finding)

        # Sort each group by severity
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        for location in grouped:
            grouped[location].sort(key=lambda f: severity_order.get(f.severity, 3))

        return grouped

    def _format_annotation(self, finding: Finding) -> str:
        """Format a finding as a markdown annotation.

        Args:
            finding: The finding to format

        Returns:
            Formatted markdown string
        """
        emoji = self.SEVERITY_EMOJI.get(finding.severity, "•")
        severity_text = finding.severity.upper()

        lines = []
        lines.append(f"> {emoji} **{severity_text}: {finding.category.replace('_', ' ').title()}** "
                    f"(Layer {finding.layer_id}: {finding.layer_name})")

        lines.append(f"> **Issue:** {finding.description}")

        if finding.recommendation:
            lines.append(f"> **Recommendation:** {finding.recommendation}")

        if finding.confidence is not None:
            lines.append(f"> **Confidence:** {finding.confidence:.2f}")

        if finding.review_decision:
            status_text = finding.review_decision.title()
            lines.append(f"> **Review Status:** {status_text}")

            if finding.review_note:
                lines.append(f"> **Review Note:** {finding.review_note}")

        return "\n".join(lines)

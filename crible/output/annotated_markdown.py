"""Annotated markdown output renderer."""
import re
from typing import List, Dict
from crible.models import Report, Finding
from crible.constants import Severity, ReviewDecision, SEVERITY_EMOJI, REVIEW_DECISION_EMOJI


class AnnotatedMarkdownRenderer:
    """Renders assessment reports as annotated markdown.

    Injects findings as inline annotations within the original skill file.
    """

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

        # Render each section
        output_lines.extend(self._render_header(report))
        output_lines.extend(self._render_annotated_content(sections, findings_by_location))
        output_lines.extend(self._render_detailed_findings(report))
        output_lines.extend(self._render_summary(report))

        return "\n".join(output_lines)

    def _render_header(self, report: Report) -> List[str]:
        """Render report header with metadata.

        Args:
            report: The assessment report

        Returns:
            List of header lines
        """
        lines = []
        lines.append("# Crible Quality Assessment Report\n")
        lines.append(f"**Skill File:** {report.skill_file_path}  ")
        lines.append(f"**Assessment Date:** {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}  ")
        lines.append(f"**Model:** {report.execution_metadata.get('model', 'unknown')}  ")

        summary = report.summary_stats()
        lines.append(f"**Total Findings:** {summary['total_findings']} ")
        lines.append(f"({summary['by_severity'][Severity.CRITICAL]} critical, ")
        lines.append(f"{summary['by_severity'][Severity.WARNING]} warnings, ")
        lines.append(f"{summary['by_severity'][Severity.INFO]} info)\n")
        lines.append("---\n")

        return lines

    def _render_annotated_content(
        self,
        sections: List[Dict],
        findings_by_location: Dict[str, List[Finding]]
    ) -> List[str]:
        """Render original content with inline annotations.

        Args:
            sections: Parsed skill content sections
            findings_by_location: Findings grouped by location

        Returns:
            List of annotated content lines
        """
        lines = []
        lines.append("## Original Skill File with Annotations\n")

        for section in sections:
            # Add section content
            lines.append(section['content'])

            # Add findings for this section
            section_id = section['id']
            if section_id in findings_by_location:
                lines.append("")  # Blank line before annotations
                for finding in findings_by_location[section_id]:
                    annotation = self._format_annotation(finding)
                    lines.append(annotation)
                lines.append("")  # Blank line after annotations

        # Add findings that couldn't be mapped to specific locations
        unmapped = findings_by_location.get("overall", []) + findings_by_location.get("unknown", [])
        if unmapped:
            lines.append("\n---\n")
            lines.append("## General Findings\n")
            for finding in unmapped:
                annotation = self._format_annotation(finding)
                lines.append(annotation)
                lines.append("")

        return lines

    def _render_detailed_findings(self, report: Report) -> List[str]:
        """Render detailed findings section.

        Args:
            report: The assessment report

        Returns:
            List of detailed findings lines
        """
        lines = []
        lines.append("\n---\n")
        lines.append("## All Findings (Detailed)\n")
        lines.append("\nComplete list of all findings with review decisions:\n")

        by_severity = report.findings_by_severity()
        for severity in Severity.ALL:
            severity_findings = by_severity[severity]
            if not severity_findings:
                continue

            emoji = SEVERITY_EMOJI[severity]
            lines.append(f"\n### {emoji} {severity.upper()} ({len(severity_findings)} findings)\n")

            for i, finding in enumerate(severity_findings, 1):
                lines.extend(self._render_finding_detail(finding, i))

        return lines

    def _render_finding_detail(self, finding: Finding, index: int) -> List[str]:
        """Render a single finding in detail.

        Args:
            finding: The finding to render
            index: The finding's index in its severity group

        Returns:
            List of finding detail lines
        """
        lines = []
        lines.append(f"\n#### {index}. {finding.category.replace('_', ' ').title()}")
        lines.append(f"\n- **Layer:** {finding.layer_id} - {finding.layer_name}")
        lines.append(f"- **Location:** {finding.location}")
        lines.append(f"- **Issue:** {finding.description}")
        lines.append(f"- **Recommendation:** {finding.recommendation}")

        if finding.confidence is not None:
            lines.append(f"- **Confidence:** {finding.confidence:.2f}")

        # Add review decision
        if finding.review_decision:
            decision_emoji = REVIEW_DECISION_EMOJI.get(finding.review_decision, "•")
            lines.append(f"- **Review Decision:** {decision_emoji} {finding.review_decision.title()}")

            if finding.review_note:
                lines.append(f"- **Review Note:** {finding.review_note}")
        else:
            lines.append(f"- **Review Decision:** Not reviewed")

        lines.append("")  # Blank line between findings
        return lines

    def _render_summary(self, report: Report) -> List[str]:
        """Render assessment summary section.

        Args:
            report: The assessment report

        Returns:
            List of summary lines
        """
        lines = []
        lines.append("\n---\n")
        lines.append("## Assessment Summary\n")

        # Findings by layer
        by_layer = report.findings_by_layer()
        lines.append("### Findings by Layer\n")
        for layer_id in sorted(by_layer.keys()):
            layer_findings = by_layer[layer_id]
            layer_name = layer_findings[0].layer_name if layer_findings else f"Layer {layer_id}"
            lines.append(f"**Layer {layer_id} ({layer_name}):** {len(layer_findings)} findings\n")

        # Findings by severity
        lines.append("\n### Findings by Severity\n")
        by_severity_count = report.findings_by_severity()
        for severity in Severity.ALL:
            emoji = SEVERITY_EMOJI[severity]
            count = len(by_severity_count[severity])
            lines.append(f"{emoji} **{severity.upper()}:** {count}\n")

        # Review statistics
        if any(f.review_decision for f in report.findings):
            lines.append("\n### Review Statistics\n")
            accepted = sum(1 for f in report.findings if f.review_decision == ReviewDecision.ACCEPTED)
            dismissed = sum(1 for f in report.findings if f.review_decision == ReviewDecision.DISMISSED)
            annotated = sum(1 for f in report.findings if f.review_decision == ReviewDecision.ANNOTATED)
            not_reviewed = sum(1 for f in report.findings if not f.review_decision)

            lines.append(f"- ✅ **Accepted:** {accepted}\n")
            lines.append(f"- ❌ **Dismissed:** {dismissed}\n")
            lines.append(f"- 📝 **Annotated:** {annotated}\n")
            if not_reviewed > 0:
                lines.append(f"- ⚪ **Not Reviewed:** {not_reviewed}\n")

        # Metadata
        lines.append("\n### Execution Metadata\n")
        lines.append(f"- **Total Tokens:** {report.execution_metadata.get('total_tokens', 'N/A')}\n")
        lines.append(f"- **Duration:** {report.execution_metadata.get('duration_seconds', 0):.1f}s\n")

        failed = report.execution_metadata.get('failed_layers', [])
        if failed:
            lines.append(f"- **Failed Layers:** {', '.join(map(str, failed))}\n")

        return lines

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
        severity_order = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}
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
        emoji = SEVERITY_EMOJI.get(finding.severity, "•")
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

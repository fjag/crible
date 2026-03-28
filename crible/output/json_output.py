"""JSON output renderer."""
import json
from crible.models import Report


class JSONRenderer:
    """Renders assessment reports as structured JSON."""

    @staticmethod
    def render(report: Report, pretty: bool = True) -> str:
        """Render report as JSON.

        Args:
            report: The assessment report
            pretty: If True, format with indentation

        Returns:
            JSON string
        """
        report_dict = report.to_dict()

        if pretty:
            return json.dumps(report_dict, indent=2, ensure_ascii=False)
        else:
            return json.dumps(report_dict, ensure_ascii=False)

    @staticmethod
    def save(report: Report, output_path: str, pretty: bool = True):
        """Save report to JSON file.

        Args:
            report: The assessment report
            output_path: Path to write JSON file
            pretty: If True, format with indentation
        """
        json_str = JSONRenderer.render(report, pretty)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_str)

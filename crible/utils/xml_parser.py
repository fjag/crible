"""XML parser for LLM responses."""
import xml.etree.ElementTree as ET
import re
from typing import List, Optional
from crible.models import Finding


class ParseError(Exception):
    """Raised when XML parsing fails."""
    pass


def clean_xml_response(xml_string: str) -> str:
    """Clean common XML formatting issues from LLM responses.

    LLMs sometimes generate invalid XML by not escaping special characters.
    This function attempts to fix common issues.

    Args:
        xml_string: Raw XML string from LLM

    Returns:
        Cleaned XML string
    """
    # Replace unescaped ampersands (but not already-escaped ones)
    xml_string = re.sub(r'&(?!(amp|lt|gt|quot|apos);)', '&amp;', xml_string)

    # Try to fix common issues in text content between tags
    # This is a best-effort cleanup, not perfect

    return xml_string


class XMLParser:
    """Parser for XML-tagged LLM responses."""

    @staticmethod
    def parse_findings(
        xml_response: str,
        layer_id: int,
        layer_name: str,
        default_category: str = "general",
    ) -> List[Finding]:
        """Extract Finding objects from XML response.

        Args:
            xml_response: XML-formatted string from LLM
            layer_id: ID of the layer that generated this response
            layer_name: Name of the layer
            default_category: Default category if not specified in XML

        Returns:
            List of Finding objects

        Raises:
            ParseError: If XML is malformed or required fields are missing
        """
        try:
            # Clean the XML first (fix common LLM issues)
            cleaned_xml = clean_xml_response(xml_response)

            # Wrap in root element to handle multiple top-level elements
            wrapped = f"<root>{cleaned_xml}</root>"
            root = ET.fromstring(wrapped)

            findings = []

            # Look for various possible finding element names
            finding_elements = (
                root.findall('.//finding') +
                root.findall('.//dependency') +
                root.findall('.//violation') +
                root.findall('.//discrepancy')
            )

            for elem in finding_elements:
                # Extract fields with defaults for missing values
                category = elem.findtext('category', default_category)
                severity = elem.findtext('severity', 'info')
                location = elem.findtext('location', 'overall')
                description = elem.findtext('description', '')
                recommendation = elem.findtext('recommendation', '')

                # Handle confidence field (may not exist for all layers)
                confidence_text = elem.findtext('confidence')
                confidence = float(confidence_text) if confidence_text else None

                # Create Finding object
                finding = Finding(
                    layer_id=layer_id,
                    layer_name=layer_name,
                    category=category,
                    severity=severity,
                    location=location,
                    description=description,
                    recommendation=recommendation,
                    confidence=confidence,
                )
                findings.append(finding)

            return findings

        except ET.ParseError as e:
            raise ParseError(f"Failed to parse XML: {e}")
        except ValueError as e:
            raise ParseError(f"Invalid field value: {e}")
        except Exception as e:
            raise ParseError(f"Unexpected parsing error: {e}")

    @staticmethod
    def extract_text(xml_response: str, tag_name: str) -> Optional[str]:
        """Extract text content from a specific XML tag.

        Args:
            xml_response: XML-formatted string
            tag_name: Name of the tag to extract

        Returns:
            Text content of the tag, or None if not found
        """
        try:
            wrapped = f"<root>{xml_response}</root>"
            root = ET.fromstring(wrapped)
            elem = root.find(f'.//{tag_name}')
            return elem.text if elem is not None else None
        except ET.ParseError:
            return None

    @staticmethod
    def extract_all_text(xml_response: str, tag_name: str) -> List[str]:
        """Extract text from all instances of a tag.

        Args:
            xml_response: XML-formatted string
            tag_name: Name of the tag to extract

        Returns:
            List of text content from all matching tags
        """
        try:
            wrapped = f"<root>{xml_response}</root>"
            root = ET.fromstring(wrapped)
            elements = root.findall(f'.//{tag_name}')
            return [elem.text for elem in elements if elem.text]
        except ET.ParseError:
            return []

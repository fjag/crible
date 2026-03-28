# Contributing to Crible

Thank you for your interest in contributing to Crible! This document provides guidelines and suggestions for contributing.

## Ways to Contribute

### 1. Report Issues

Found a bug or have a feature request?

**Before opening an issue:**
- Check existing issues to avoid duplicates
- Test with the latest version
- Prepare a minimal reproducible example

**Open an issue with:**
- Clear description of the problem or feature
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Environment details (Python version, OS, Crible version)
- Sample skill file (if relevant)

### 2. Improve Documentation

Documentation improvements are always welcome:
- Fix typos or unclear wording
- Add examples to USAGE_EXAMPLE.md
- Document edge cases in LIMITATIONS.md
- Add CI/CD patterns to CI_CD.md
- Improve architecture explanations

### 3. Submit Code

Contributions include:
- Bug fixes
- New layers
- Prompt improvements
- Output format enhancements
- Test coverage improvements

---

## Areas for Improvement

### High Priority

**Layer 0 Validation**
- Integrate with Bioconda/PyPI/CRAN APIs
- Real-time package existence checks
- Version availability verification
- URL validation for databases/references

**Test Coverage**
- Unit tests for each layer
- Integration tests with real skill files
- XML parsing edge cases
- Error handling scenarios

**Prompt Refinement**
- Reduce false positives
- Improve confidence scoring accuracy
- Better handling of reference documentation
- Domain-specific prompt variants

### Medium Priority

**Additional Layers**
- Layer 4: Security analysis (hardcoded credentials, unsafe operations)
- Layer 5: Performance analysis (computational complexity warnings)
- Layer 6: Reproducibility checks (random seeds, version pinning)

**Output Enhancements**
- HTML report format
- Interactive web viewer
- Diff mode (compare two skill versions)
- Suggested fixes (not just recommendations)

**Domain Expansion**
- Prompt libraries for proteomics, cheminformatics, image analysis
- Auto-detect domain from skill content
- Community-contributed domain packs

### Lower Priority

**Performance Optimization**
- Parallel layer execution (Layers 0 & 1)
- Response caching for identical inputs
- Streaming LLM responses
- Batch processing optimization

**Integration**
- VS Code extension
- GitHub App for automated PR comments
- Slack/Discord bot integration
- API endpoint for remote assessments

---

## Development Process

### 1. Fork and Clone

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/crible.git
cd crible

# Add upstream remote
git remote add upstream https://github.com/fjag/crible.git
```

### 2. Create Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 3. Make Changes

```bash
# Install in development mode
pip install -e .

# Make your changes
# ...

# Test your changes
pytest tests/

# Test on example skills
crible assess examples/scrna_clustering.md --no-review
```

### 4. Commit

```bash
# Stage changes
git add .

# Commit with clear message
git commit -m "Add feature: brief description

- Detail 1
- Detail 2
- Detail 3"
```

**Commit message format:**
- First line: Brief summary (50 chars max)
- Blank line
- Detailed explanation with bullet points

**Good commit messages:**
```
Add Layer 4: Security analysis

- Detect hardcoded API keys and credentials
- Flag unsafe operations (eval, exec, subprocess)
- Identify overly permissive file operations
- Add security_prompt.py with examples
```

```
Fix XML parsing for special characters

- Escape < and > in text content
- Handle CDATA sections properly
- Add test cases for edge cases
- Resolves #42
```

### 5. Submit Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name
```

Then:
1. Go to GitHub and open Pull Request
2. Provide clear description of changes
3. Reference related issues
4. Wait for review

---

## Code Style

### Python

Follow PEP 8 with these specifics:

**Formatting:**
```bash
# Use black for formatting
black crible/

# Use isort for imports
isort crible/
```

**Linting:**
```bash
# Check with flake8
flake8 crible/
```

**Docstrings:**
```python
def function_name(param1: str, param2: int) -> List[Finding]:
    """Brief description of function.

    Longer explanation if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When and why this is raised
    """
```

**Type Hints:**
Use type hints for all function signatures:
```python
from typing import List, Dict, Optional, Tuple

def parse_response(self, response: str) -> Tuple[List[Finding], str]:
    ...
```

---

## Testing

### Writing Tests

Place tests in `tests/` directory:

```python
# tests/test_xml_parser.py
import pytest
from crible.utils.xml_parser import XMLParser, clean_xml_response

def test_clean_xml_escapes_ampersands():
    input_xml = "<tag>foo & bar</tag>"
    expected = "<tag>foo &amp; bar</tag>"
    assert clean_xml_response(input_xml) == expected

def test_parse_findings_extracts_all_fields():
    xml = """
    <findings>
      <finding>
        <category>test_category</category>
        <severity>critical</severity>
        <location>step 1</location>
        <description>Test description</description>
        <recommendation>Test recommendation</recommendation>
      </finding>
    </findings>
    """

    findings = XMLParser.parse_findings(xml, layer_id=1, layer_name="Test Layer")

    assert len(findings) == 1
    assert findings[0].category == "test_category"
    assert findings[0].severity == "critical"
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_xml_parser.py

# Run specific test
pytest tests/test_xml_parser.py::test_clean_xml_escapes_ampersands

# Run with coverage
pytest --cov=crible tests/

# Generate coverage report
pytest --cov=crible --cov-report=html tests/
```

---

## Prompt Development Guidelines

### Structure

```python
def build_layerN_prompt(skill_content: str, upstream_summary: str = "") -> str:
    prompt = f"""<role>You are [specific expert role]</role>

<task>
[Clear task description]

[Detailed instructions with bullet points]

[Examples showing expected behavior]
</task>

<skill_content>
{skill_content}
</skill_content>

<output_format>
[XML schema with examples]

CRITICAL XML FORMATTING REQUIREMENTS:
- You MUST return valid, well-formed XML
- Every opening tag MUST have a matching closing tag
- All special characters MUST be escaped: & → &amp;, < → &lt;, > → &gt;
</output_format>"""

    return prompt
```

### Best Practices

**Be Specific:**
❌ "Analyze the skill file"
✅ "For each step, identify which tool is being used and whether parameters are specified"

**Provide Examples:**
Include 2-3 examples in the prompt showing:
- What constitutes a finding
- How to structure XML output
- Edge cases to handle

**Test Thoroughly:**
```bash
# Test on diverse skill files
crible assess examples/simple_skill.md --verbose
crible assess examples/complex_skill.md --verbose
crible assess examples/ambiguous_skill.md --verbose
```

**Iterate Based on Output:**
1. Run assessment
2. Review findings for false positives/negatives
3. Adjust prompt instructions
4. Re-run and compare
5. Repeat until quality improves

---

## Pull Request Checklist

Before submitting:

- [ ] Code follows style guidelines (black, flake8)
- [ ] Tests added for new functionality
- [ ] All tests pass (`pytest tests/`)
- [ ] Documentation updated (README, relevant .md files)
- [ ] Commit messages are clear and descriptive
- [ ] No sensitive information in code (API keys, credentials)
- [ ] Examples added (if applicable)
- [ ] Backwards compatibility maintained (or breaking change documented)

---

## Review Process

### What to Expect

1. **Automated Checks:** GitHub Actions runs tests on your PR
2. **Code Review:** Maintainer reviews code and provides feedback
3. **Discussion:** You may be asked questions or requested changes
4. **Approval:** Once approved, PR will be merged

### Addressing Feedback

```bash
# Make requested changes
# ...

# Commit changes
git add .
git commit -m "Address review feedback: [brief description]"

# Push to update PR
git push origin feature/your-feature-name
```

### Timeline

- Initial response: Within 1 week
- Full review: Within 2 weeks
- Depends on PR complexity and maintainer availability

---

## Communication

### Where to Ask Questions

- **GitHub Issues:** Bug reports, feature requests
- **GitHub Discussions:** General questions, ideas
- **Pull Request Comments:** Specific code questions

### Code of Conduct

Be respectful and constructive:
- Assume good intent
- Provide actionable feedback
- Be patient with new contributors
- Focus on the code, not the person

---

## Recognition

Contributors will be:
- Listed in project acknowledgements
- Credited in release notes
- Mentioned in relevant documentation

Thank you for contributing to Crible!

---

## Quick Reference

```bash
# Setup
git clone https://github.com/YOUR_USERNAME/crible.git
cd crible
pip install -e .
pip install pytest black flake8

# Development
git checkout -b feature/your-feature
# Make changes
black crible/
pytest tests/
git commit -m "Brief description"
git push origin feature/your-feature

# Testing
pytest tests/
crible assess examples/scrna_clustering.md --no-review --verbose

# Before PR
black crible/
flake8 crible/
pytest tests/
# Update documentation
```

---

## See Also

- [DEVELOPMENT.md](DEVELOPMENT.md) - Development guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture overview
- [PROJECT_LEARNINGS.md](PROJECT_LEARNINGS.md) - Lessons learned during development

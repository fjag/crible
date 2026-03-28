# Development Guide

## Setup

### Clone and Install

```bash
# Clone repository
git clone https://github.com/fjag/crible.git
cd crible

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-cov black flake8
```

### Configure API Key

```bash
# Option 1: Environment variable
export ANTHROPIC_API_KEY=your-api-key-here

# Option 2: Use setup command
crible setup
```

---

## Running Tests

### Unit Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=crible tests/

# Run specific test file
pytest tests/test_xml_parser.py

# Run with verbose output
pytest -v tests/
```

### Integration Tests

```bash
# Test on example skill files
crible assess examples/scrna_clustering.md --no-review

# Test different output formats
crible assess examples/scrna_clustering.md --format json --no-review

# Test with different models
crible assess examples/scrna_clustering.md --model haiku --no-review
```

---

## Code Quality

### Linting

```bash
# Check code style with flake8
flake8 crible/

# Format code with black
black crible/

# Check imports
isort --check-only crible/
```

### Type Checking

```bash
# Install mypy
pip install mypy

# Run type checks
mypy crible/
```

---

## Prompt Development

### Testing Prompts

Located in `crible/prompts/`:
- `layer0_prompt.py` - Dependency extraction
- `layer1_prompt.py` - Ambiguity scoring
- `layer2_prompt.py` - Execution trace
- `layer3_prompt.py` - Domain constraints

**Iteration workflow:**
1. Modify prompt template in `crible/prompts/layerN_prompt.py`
2. Test on sample skill: `crible assess examples/scrna_clustering.md --verbose`
3. Review findings for quality
4. Compare with baseline (previous prompt version)
5. Iterate based on false positive/negative rates

**Tips:**
- Add examples to prompt for better LLM performance
- Be explicit about XML formatting requirements
- Include edge case handling instructions
- Test on both simple and complex skills

---

## Adding a New Layer

### 1. Create Layer Class

`crible/layers/layer4.py`:

```python
from crible.layers.base import Layer
from crible.models import Finding
from typing import List, Dict, Tuple

class Layer4(Layer):
    """Layer 4: [Your layer purpose]"""

    def __init__(self, llm_client):
        super().__init__(llm_client, layer_id=4, layer_name="Your Layer Name")

    def build_prompt(self, skill_content: str, upstream_context: Dict[int, str]) -> str:
        """Build Layer 4 prompt"""
        # Get upstream summaries if needed
        layer3_summary = upstream_context.get(3, "")

        return build_layer4_prompt(skill_content, layer3_summary)

    def parse_response(self, response: str) -> Tuple[List[Finding], str]:
        """Parse Layer 4 XML response"""
        findings = self.xml_parser.parse_findings(
            response,
            self.layer_id,
            self.layer_name,
            default_category="your_category"
        )

        summary = f"Layer 4 summary: {len(findings)} findings"
        return findings, summary
```

### 2. Create Prompt Template

`crible/prompts/layer4_prompt.py`:

```python
def build_layer4_prompt(skill_content: str, layer3_summary: str = "") -> str:
    upstream_section = ""
    if layer3_summary:
        upstream_section = f"""
<upstream_context>
{layer3_summary}
</upstream_context>
"""

    prompt = f"""<role>You are [expert role]</role>

<task>
[Task description]
</task>

<skill_content>
{skill_content}
</skill_content>
{upstream_section}

<output_format>
Return findings as XML:

<findings>
  <finding>
    <category>category_name</category>
    <severity>critical|warning|info</severity>
    <location>step X</location>
    <description>What the issue is</description>
    <recommendation>How to fix it</recommendation>
  </finding>
</findings>

CRITICAL XML FORMATTING REQUIREMENTS:
- You MUST return valid, well-formed XML
- Every opening tag MUST have a matching closing tag
- All special characters MUST be escaped: & → &amp;, < → &lt;, > → &gt;
</output_format>"""

    return prompt
```

### 3. Register Layer in Pipeline

`crible/cli.py`:

```python
from crible.layers import Layer0, Layer1, Layer2, Layer3, Layer4

# In assess command:
layers = [
    Layer0(llm_client),
    Layer1(llm_client),
    Layer2(llm_client),
    Layer3(llm_client),
    Layer4(llm_client),  # Add new layer
]
```

### 4. Update Skip Layer Validation

If your layer has dependencies, update `PipelineOrchestrator._has_dependent_layers()` and `_skip_dependent_layers()`.

### 5. Test

```bash
# Test new layer
crible assess examples/scrna_clustering.md --verbose

# Test skipping new layer
crible assess examples/scrna_clustering.md --skip-layer 4
```

---

## Debugging

### Verbose Mode

```bash
# See detailed execution logs
crible assess skill.md --verbose
```

Shows:
- LLM prompts sent
- Token counts per layer
- Parse times
- Error traces

### Manual Layer Testing

```python
# Test a single layer in Python REPL
from crible.utils import AnthropicClient
from crible.layers import Layer1

client = AnthropicClient(api_key="your-key", model="sonnet")
layer1 = Layer1(client)

skill_content = open("examples/scrna_clustering.md").read()
result = layer1.execute(skill_content, {})

print(result.findings)
print(result.summary)
```

### XML Parsing Errors

If layer fails with XML parse error:

```bash
# Check raw response
crible assess skill.md --verbose 2>&1 | grep "Response snippet"

# Skip problematic layer temporarily
crible assess skill.md --skip-layer 2
```

Common causes:
- LLM didn't escape `&` characters
- Mismatched XML tags
- Very long responses truncated mid-tag

Fix by improving prompt XML instructions or adding cleaning logic in `xml_parser.py`.

---

## Performance Profiling

### Token Usage

```bash
# Profile token usage per layer
crible assess skill.md --verbose 2>&1 | grep "tokens"
```

### Timing

```python
import time
from crible.pipeline import PipelineOrchestrator
from crible.utils import AnthropicClient

client = AnthropicClient(api_key="your-key")
orchestrator = PipelineOrchestrator(client, [...])

start = time.time()
report = orchestrator.run("skill.md")
duration = time.time() - start

print(f"Total time: {duration:.2f}s")
print(f"Tokens: {client.get_token_count()}")
```

---

## Release Process

### Version Bump

1. Update version in `setup.py`:
   ```python
   version="0.2.0"
   ```

2. Update CHANGELOG (if exists)

3. Tag release:
   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0"
   git push origin v0.2.0
   ```

### Testing Before Release

```bash
# Run full test suite
pytest tests/

# Test on multiple skill files
for skill in examples/*.md; do
    crible assess "$skill" --no-review
done

# Test all models
crible assess examples/scrna_clustering.md --model sonnet --no-review
crible assess examples/scrna_clustering.md --model haiku --no-review

# Test output formats
crible assess examples/scrna_clustering.md --format json --no-review
```

---

## Prompt Refinement Loop

### Collecting Dismissed Findings

```bash
# Aggregate dismissed findings from reports
find reports/ -name "*.json" -exec jq '.findings[] | select(.review_decision=="dismissed")' {} \; > dismissed.json

# Analyze patterns
jq -s 'group_by(.category) | map({category: .[0].category, count: length})' dismissed.json
```

### Analyzing False Positives

1. **Group by layer:**
   ```bash
   jq -s 'group_by(.layer_id)' dismissed.json
   ```

2. **Look for common patterns:**
   - Which categories are dismissed most?
   - Which layers overfire?
   - Are there specific phrases that trigger false positives?

3. **Update prompts:**
   - Add negative examples to prompts
   - Adjust severity thresholds
   - Clarify edge case handling

4. **Regression test:**
   ```bash
   # Re-run on previously assessed skills
   for skill in regression_tests/*.md; do
       crible assess "$skill" --no-review --output "regression_output/$(basename $skill).json"
   done

   # Compare with baseline
   diff -r baseline_output/ regression_output/
   ```

---

## Documentation

### Updating Docs

Documentation files:
- `README.md` - Main documentation with summaries
- `USAGE_EXAMPLE.md` - Detailed usage examples
- `OUTPUTS.md` - Output format examples
- `LIMITATIONS.md` - Comprehensive limitations
- `CI_CD.md` - CI/CD integration guide
- `ARCHITECTURE.md` - Technical architecture
- `DEVELOPMENT.md` - This file
- `CONTRIBUTING.md` - Contribution guidelines

**When to update:**
- New layer added → Update README features, ARCHITECTURE.md
- New CLI option → Update README usage, USAGE_EXAMPLE.md
- Bug fixed → Update LIMITATIONS.md if limitation removed
- New integration pattern → Update CI_CD.md

### Building Example Outputs

```bash
# Generate example reports for documentation
crible assess examples/scrna_clustering.md --no-review --output examples/scrna_clustering_crible_report.md
crible assess examples/scrna_clustering.md --no-review --format json --output examples/scrna_clustering_crible_report.json
```

---

## Common Development Tasks

### Fix XML Parsing Issues

Location: `crible/utils/xml_parser.py`

```python
def clean_xml_response(xml_string: str) -> str:
    """Add new cleaning rules here"""
    # Escape ampersands
    xml_string = re.sub(r'&(?!(amp|lt|gt|quot|apos);)', '&amp;', xml_string)

    # Add more cleaning as needed
    # Example: Fix common malformed patterns

    return xml_string
```

### Add New Finding Category

1. Update layer's parse_response to use new category
2. Add category description to OUTPUTS.md
3. Test with skill that triggers the category

### Adjust Cost Table

Location: `README.md` - Expected Costs section

Update when:
- Anthropic changes pricing
- Prompt optimization reduces token usage
- New models added

---

## Troubleshooting Development Issues

### API Rate Limits

```python
# Increase retry backoff in llm_client.py
backoff = 2  # Start with 2 seconds instead of 1
```

### Memory Issues

Large skill files may exhaust memory:
```bash
# Increase max tokens if needed
# In llm_client.py generate() method
max_tokens = 8000  # Default is 4000
```

### Import Errors

```bash
# Reinstall in development mode
pip install -e .

# Or rebuild package
pip install --force-reinstall -e .
```

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture details
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [PROJECT_LEARNINGS.md](PROJECT_LEARNINGS.md) - Development lessons learned

# Crible

**Quality assessment tool for bioinformatics skill files**

Crible analyzes LLM instruction sets (skill files) used for bioinformatics tasks and produces structured quality reports. It runs a four-layer assessment pipeline using Claude to identify dependency issues, ambiguities, execution flow problems, and domain constraint violations — all without executing any code.

> **⚠️ EXPERIMENTAL TOOL:** Crible is an experimental research tool. Use findings as a starting point for manual review, not as definitive conclusions. Provided without warranty or support commitments. See full [disclaimer](#disclaimer) below.

## What Does It Do?

Crible performs **static quality analysis** on bioinformatics skill files without executing any code. Given a skill file (like a scRNA-seq clustering workflow), Crible:

1. **Extracts dependencies** - Catalogs all mentioned tools, packages, databases, and files
2. **Identifies ambiguities** - Flags steps with multiple plausible interpretations (e.g., "normalize data" → which method?)
3. **Traces execution flow** - Predicts data transformations through the pipeline (e.g., raw counts → filtered → normalized → clustered)
4. **Checks domain constraints** - Validates methodological appropriateness (e.g., bulk methods applied to single-cell data)

**Output:** A detailed report showing:
- All quality issues found (critical, warnings, info)
- Inline annotations within your original skill file
- Specific recommendations for each issue
- Your review decisions (accept/dismiss/annotate)

**Example findings:**
- "Step 3 doesn't specify which normalization method (library size? SCTransform? TPM?)"
- "Step 5 performs PCA but no normalization precedes it"
- "Workflow assumes 10x Genomics data but presents as general scRNA-seq pipeline"

**Use case:** Review skill files before deploying them, identify potential issues early, improve documentation quality.

## Features

- **Four-layer assessment pipeline:**
  - Layer 0: Dependency extraction (cataloging only - no validation in v1)
  - Layer 1: Instruction ambiguity scoring
  - Layer 2: Simulated execution trace
  - Layer 3: Domain constraint checking

- **Interactive review:** Review findings before final report generation

- **Dual output formats:**
  - Annotated markdown: Inline annotations within original skill file
  - JSON: Structured output for CI/CD and batch analysis

- **Fail-forward with dependency awareness:** Layers handle failures gracefully and skip dependent layers when prerequisites fail

## Requirements

### System Requirements
- **Python:** 3.8 or higher
- **Operating System:** Linux, macOS, or Windows (with WSL recommended)
- **Memory:** 512 MB minimum (for running the tool itself; skill file analysis is stateless)

### API Requirements
- **Anthropic API Key:** Required for Claude API access
  - Get your key at: https://console.anthropic.com/
  - API costs apply per assessment (see [Expected Costs](#expected-costs) section)

### Python Dependencies
Automatically installed via `pip install`:
- `anthropic>=0.18.0` - Anthropic Python SDK for Claude API
- `click>=8.1.0` - Command-line interface framework
- `rich>=13.0.0` - Rich terminal output formatting
- `pyyaml>=6.0` - YAML configuration file support

### Optional Requirements
- **git** - For cloning the repository
- **Virtual environment** - Recommended for isolated Python environment

### No Other Dependencies
Crible is **self-contained** and does not require:
- ❌ External databases
- ❌ Docker or containers
- ❌ GPU or specialized hardware
- ❌ Installation of bioinformatics tools (it only analyzes skill files, doesn't run them)

## Installation

```bash
# Clone the repository
cd crible

# Create virtual environment (if not already created)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

## Setup

Configure your Anthropic API key:

```bash
# Option 1: Environment variable
export ANTHROPIC_API_KEY=your-api-key-here

# Option 2: Interactive setup (creates ~/.crible/config)
crible setup
```

## Expected Costs

Crible uses the Anthropic API, which charges per token. Typical costs per skill file assessment:

| Skill Complexity | Model | Estimated Tokens | Approximate Cost* |
|------------------|-------|------------------|-------------------|
| Simple (10-20 steps) | Haiku | 8,000 - 15,000 | $0.01 - $0.02 |
| Simple (10-20 steps) | Sonnet | 8,000 - 15,000 | $0.02 - $0.05 |
| Medium (20-50 steps) | Haiku | 15,000 - 30,000 | $0.02 - $0.04 |
| Medium (20-50 steps) | Sonnet | 15,000 - 30,000 | $0.05 - $0.09 |
| Complex (50+ steps) | Haiku | 30,000 - 60,000 | $0.04 - $0.08 |
| Complex (50+ steps) | Sonnet | 30,000 - 60,000 | $0.09 - $0.18 |
| Complex (50+ steps) | Opus | 30,000 - 60,000 | $0.45 - $0.90 |

*Based on Anthropic API pricing as of March 2026. Actual costs vary based on skill length and complexity.

**Cost optimization tips:**
- Use `--model haiku` for batch processing (lower cost, slightly reduced quality)
- Use `--skip-layer 0` to skip dependency extraction if not needed
- Use `--skip-layer 2` to skip execution trace (highest token consumer)
- Default model (Sonnet) provides best cost/quality balance for most use cases

## Usage

### Basic Assessment

```bash
# Interactive review - saves to skill_crible_report.md
crible assess skill.md

# Save to custom file
crible assess skill.md --output my_report.md

# JSON format - saves to skill_crible_report.json
crible assess skill.md --format json

# Skip review for batch processing
crible assess skill.md --no-review

# Use Opus model with verbose logging
crible assess skill.md --model opus --verbose

# Skip Layer 0, use Haiku model
crible assess skill.md --skip-layer 0 --model haiku
```

**Output:** Reports are saved to files (not printed to terminal) for better readability. Default filename: `<skill_name>_crible_report.md` (or `.json` for JSON format).

### Command Options

```
crible assess [OPTIONS] SKILL_FILE

Options:
  --format [annotated|json]   Output format (default: annotated)
  --output PATH               Output file path (default: <skill_name>_crible_report.md)
  --no-review                 Skip interactive review (accept all findings)
  --skip-layer INTEGER        Skip specific layer (can be repeated)
  --model [sonnet|opus|haiku] Claude model to use (default: sonnet)
  --verbose                   Show detailed execution logs
```

### Interactive Review

When reviewing findings, you'll see clear prompts:

- Type **a** or **accept** - Keep this finding as-is
- Type **d** or **dismiss** - Mark as false positive (you'll be asked for a reason)
- Type **n** or **annotate** - Add a context note to this finding
- Type **s** or **skip_all** - Accept all remaining findings

The report is saved to a file for easy reading in your editor.

### Other Commands

```bash
# Show version
crible version

# Interactive API key setup
crible setup
```

## Architecture

### Module Structure

```
crible/
├── cli.py                      # CLI entry point
├── pipeline.py                 # Orchestrates layer execution
├── review_interface.py         # Interactive review UI
├── layers/
│   ├── base.py                 # Abstract Layer class
│   ├── layer0.py               # Dependency extraction
│   ├── layer1.py               # Ambiguity scoring
│   ├── layer2.py               # Simulated execution
│   └── layer3.py               # Domain constraints
├── models/
│   ├── finding.py              # Finding dataclass
│   ├── report.py               # Report dataclass
│   └── layer_result.py         # LayerResult dataclass
├── prompts/
│   ├── layer0_prompt.py        # Layer 0 prompt template
│   ├── layer1_prompt.py        # Layer 1 prompt template
│   ├── layer2_prompt.py        # Layer 2 prompt template
│   └── layer3_prompt.py        # Layer 3 prompt template
├── output/
│   ├── json_output.py          # JSON renderer
│   └── annotated_markdown.py   # Markdown renderer
└── utils/
    ├── llm_client.py           # Anthropic API wrapper
    └── xml_parser.py           # XML response parser
```

### Layer Pipeline

Layers run sequentially with selective context passing:

1. **Layer 0** extracts dependencies but does NOT validate them (v1 limitation)
2. **Layer 1** scores instruction ambiguity (independent of Layer 0)
3. **Layer 2** simulates execution flow (uses Layer 1 summary for context)
4. **Layer 3** checks domain constraints (depends on Layer 2's inferred data type)

Each layer produces:
- **Detailed findings** for the final report
- **Condensed summary** for downstream layers (reduces token costs)

### Error Handling

- **Independent layers** (0, 1, 2): Fail independently without affecting others
- **Dependent layers** (3): Skip if prerequisites fail, with clear error messages

## Known Limitations

> **⚠️ IMPORTANT:** Crible is a best-effort quality linter, not a definitive bug detector. All findings should be manually reviewed by domain experts. See full [disclaimer](#disclaimer) for details.

**Quick Summary of Limitations:**
- ❌ Layer 0 catalogs but does NOT validate dependencies (no live registry checks)
- ⚠️ Layer 2 execution traces are predictions, not actual runs (confidence scores indicate uncertainty)
- 🔍 LLM-based findings may include false positives (use interactive review to dismiss)
- 🚫 Cannot check execution environment (RAM, installed software, file system)
- 🧬 Prompts optimized for bioinformatics (may underperform on other domains)
- 💰 Token costs accumulate with complex skill files (use `--model haiku` or `--skip-layer` to reduce)

---

### 1. **Layer 0 Does Not Validate Dependencies** (CRITICAL)

Layer 0 extracts dependencies but **does not validate them**. It cannot:
- Check if packages exist in Bioconda/PyPI/CRAN
- Detect deprecated tools
- Verify database URLs or genome assemblies

**Why:** LLMs cannot reliably validate package registries from training knowledge alone. This requires live API calls to Bioconda, PyPI, CRAN, etc.

**v1 Scope:** Layer 0 catalogs dependencies and clearly states "Validation requires live registry integration (not implemented)."

**Future Work:** v2 will integrate with package registry APIs for real validation.

---

### 2. **Layer 2 Execution Trace is Best-Effort**

Layer 2 attempts to trace data flow without executing code. This works well for:
- Simple linear pipelines
- Well-documented steps with clear inputs/outputs

It struggles with:
- Complex branching logic
- Conditionals and loops
- Insufficient context in skill files

**Mitigation:** Confidence scores (0.0-1.0) indicate trace certainty. Low-confidence traces (<0.5) trigger warnings and flag downstream findings as tentative.

---

### 3. **LLM-Based Assessment Has Inherent Uncertainty**

Findings are **suggestions for code review**, not definitive bugs. The interactive review step allows you to:
- **Dismiss** false positives (with reason)
- **Annotate** valid findings that need context
- **Accept** findings as-is

Dismissed findings remain in the report marked as "reviewed - dismissed" with your stated reason. This preserves audit trail and generates signal for prompt refinement.

---

### 4. **No Execution Environment Validation**

Crible cannot check:
- Available system resources (RAM, disk, GPUs)
- Installed software versions
- File system structure

It only assesses the skill file itself.

---

### 5. **Bioinformatics-Tuned Prompts**

Prompts are optimized for bioinformatics workflows (scRNA-seq, genomics, etc.). Performance on other domains (cheminformatics, image analysis, proteomics) may vary until prompts are adapted.

---

### 6. **Token Costs Can Accumulate**

Complex skill files with long execution traces can consume significant tokens:
- Upstream context is passed between layers (summarized to reduce cost)
- Use `--skip-layer` to skip layers
- Use `--model haiku` for cost control (with some quality trade-off)

---

## Output Examples

### Annotated Markdown

```markdown
# Crible Quality Assessment Report

**Skill File:** examples/scrna_clustering.md
**Assessment Date:** 2026-03-28 14:30:00
**Model:** claude-sonnet-4-5
**Total Findings:** 8 (2 critical, 3 warnings, 3 info)

---

## Original Skill File with Annotations

### Step 1: Load Data
Load the count matrix from 10x CellRanger output.

> 🔴 **CRITICAL: Methodological Ambiguity** (Layer 1: Ambiguity Scoring)
> **Issue:** Ambiguity level: HIGH. Plausible interpretations: 5+. Ambiguous aspects: Which 10x chemistry version? Which CellRanger output structure?
> **Recommendation:** Specify 10x chemistry version (3' v2/v3, 5', multiome) and CellRanger output structure (filtered vs raw, h5 vs mtx)
> **Review Status:** Accepted

### Step 3: Normalize Data
Normalize the count matrix before clustering.

> ⚠️ **WARNING: Execution Discrepancy** (Layer 2: Simulated Execution)
> **Issue:** Step performs normalization but method is unspecified. Could be library size, log-normalization, SCTransform, etc.
> **Recommendation:** Specify normalization method explicitly (e.g., "scanpy.pp.normalize_total followed by scanpy.pp.log1p")
> **Confidence:** 0.65
> **Review Status:** Annotated
> **Review Note:** User review: Valid but our lab uses SCTransform by default - this is acceptable for us.

---

## Assessment Summary

### Findings by Layer
**Layer 0 (Dependency Extraction):** 3 findings
**Layer 1 (Ambiguity Scoring):** 2 findings
**Layer 2 (Simulated Execution):** 2 findings
**Layer 3 (Domain Constraints):** 1 findings

### Findings by Severity
🔴 **CRITICAL:** 2
⚠️ **WARNING:** 3
ℹ️ **INFO:** 3

### Execution Metadata
- **Total Tokens:** 12,340
- **Duration:** 18.3s
```

### JSON Output

```json
{
  "skill_file": "examples/scrna_clustering.md",
  "timestamp": "2026-03-28T14:30:00",
  "model": "claude-sonnet-4-5",
  "findings": [
    {
      "layer_id": 1,
      "layer_name": "Ambiguity Scoring",
      "category": "methodological_ambiguity",
      "severity": "critical",
      "location": "step 1",
      "description": "Ambiguity level: HIGH. Plausible interpretations: 5+...",
      "recommendation": "Specify 10x chemistry version...",
      "confidence": null,
      "review_decision": "accepted",
      "review_note": null
    }
  ],
  "summary": {
    "total_findings": 8,
    "by_severity": {"critical": 2, "warning": 3, "info": 3},
    "by_layer": {"0": 3, "1": 2, "2": 2, "3": 1},
    "reviewed": true,
    "accepted": 6,
    "dismissed": 1,
    "annotated": 1
  },
  "layer_summaries": {
    "0": "Identified 3 dependencies: 1 python_package, 2 tool. Validation not performed.",
    "1": "Identified 2 ambiguous steps: 1 high-ambiguity, 1 medium-ambiguity.",
    "2": "Inferred data type: scRNA-seq (confidence: 0.85). Traced 5 steps with average confidence 0.72.",
    "3": "Found 1 domain constraint issues: 1 warnings."
  },
  "execution_metadata": {
    "total_tokens": 12340,
    "duration_seconds": 18.3
  }
}
```

## CI/CD Integration

Use JSON output and exit codes for automated quality checks:

```bash
# Fail build if critical findings exist
crible assess skill.md --format json --no-review | jq '.summary.by_severity.critical > 0' && exit 1

# Generate report in CI pipeline
crible assess skill.md --no-review --output report.md
```

## Prompt Refinement Loop (Post-MVP)

Dismissed findings generate training signal for prompt improvement:

```bash
# Collect all dismissed findings across reports
find reports/ -name "*.json" -exec jq '.findings[] | select(.review_decision=="dismissed")' {} \;

# Analyze patterns: which layers overfire? Which categories are false positives?
# Refine prompts in crible/prompts/ based on patterns
# Regression test: re-run on previous skills, confirm improvements
```

This creates a self-improving system over time.

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest

# Run tests
pytest tests/
```

### Project Philosophy

Crible is a **best-effort quality linter**, not a **definitive bug detector**. The value is in:
- Surfacing likely issues for human review
- Making uncertainty explicit (confidence scores, tentative findings)
- Providing actionable recommendations
- Preserving audit trail (dismissed findings with reasons)

We prioritize **honesty about limitations** over false confidence.

## Contributing

Contributions welcome! Areas for improvement:
- Layer 0 validation with live registry APIs
- Additional layers (security, performance, reproducibility)
- Prompt refinement for non-bioinformatics domains
- Test coverage

## Acknowledgements

Crible was co-developed with **Claude Code**, Anthropic's agentic coding tool. The implementation plan, architecture, and code were created through interactive planning and development sessions with Claude Sonnet 4.5.

For insights into the development process, challenges encountered, and lessons learned, see [PROJECT_LEARNINGS.md](PROJECT_LEARNINGS.md).

## License

MIT License - see LICENSE file

## Citation

If you use Crible in research, please cite:

```
Crible: Quality Assessment Tool for Bioinformatics Skill Files
Version 0.1.0 (2026)
```

---

## Disclaimer

Crible is an experimental research tool intended to assist — not replace — expert judgement. Findings should be treated as a starting point for manual review, not as definitive conclusions.

**Important limitations:**
- Accuracy is not guaranteed
- Results may vary depending on skill file structure, complexity, and documentation quality
- Layer 0 does not validate dependencies (cataloging only)
- Layer 2 execution traces are best-effort predictions, not actual executions
- LLM-based assessment has inherent uncertainty

**Use responsibly:**
- Do not rely solely on Crible findings for critical decisions
- Always conduct manual expert review of flagged issues
- Findings represent likely issues, not definitive bugs
- Dismissed findings and confidence scores indicate uncertainty

**No warranty:**
The author assumes no responsibility for decisions made based on this tool's output. This project is maintained on a best-effort basis with no commitment to updates or user support.

---

**Built with Claude Sonnet 4.5 via the Anthropic API**

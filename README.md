# Crible

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Experimental](https://img.shields.io/badge/Status-Experimental-orange.svg)](https://github.com/fjag/crible)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Powered by Claude](https://img.shields.io/badge/Powered%20by-Claude%20API-blueviolet.svg)](https://www.anthropic.com/claude)
[![Built with Claude Code](https://img.shields.io/badge/Built%20with-Claude%20Code-5C6BC0.svg)](https://claude.ai/code)

**Quality assessment tool for bioinformatics skill files**

Crible analyzes LLM instruction sets (skill files) used for bioinformatics tasks and produces structured quality reports. It runs a four-layer assessment pipeline using Claude to identify dependency issues, ambiguities, execution flow problems, and domain constraint violations — all without executing any code.

> **⚠️ EXPERIMENTAL TOOL:** Crible is an experimental research tool. Use findings as a starting point for manual review, not as definitive conclusions. Provided without warranty or support commitments. See full [disclaimer](#disclaimer) below.

---

## What Does It Do?

Crible performs **static quality analysis** on bioinformatics skill files without executing any code. Given a skill file (like a scRNA-seq clustering workflow), Crible:

1. **Extracts dependencies** - Catalogs all mentioned tools, packages, databases, and files
2. **Identifies ambiguities** - Flags steps with multiple plausible interpretations (e.g., "normalize data" → which method?)
3. **Traces execution flow** - Predicts data transformations through the pipeline (e.g., raw counts → filtered → normalized → clustered)
4. **Checks domain constraints** - Validates methodological appropriateness (e.g., bulk methods applied to single-cell data)

**Example findings:**
- "Step 3 doesn't specify which normalization method (library size? SCTransform? TPM?)"
- "Step 5 performs PCA but no normalization precedes it"
- "Workflow assumes 10x Genomics data but presents as general scRNA-seq pipeline"

**Use case:** Review skill files before deploying them, identify potential issues early, improve documentation quality.

---

## Project Philosophy

Crible is a **best-effort quality linter**, not a **definitive bug detector**. The value is in:
- Surfacing likely issues for human review
- Making uncertainty explicit (confidence scores, tentative findings)
- Providing actionable recommendations
- Preserving audit trail (dismissed findings with reasons)

We prioritize **honesty about limitations** over false confidence.

---

## Features

- **Four-layer assessment pipeline:**
  - Layer 0: Dependency extraction (cataloging only - no validation in v1)
  - Layer 1: Instruction ambiguity scoring
  - Layer 2: Simulated execution trace
  - Layer 3: Domain constraint checking

- **Interactive review:** Review findings before final report generation with single-letter shortcuts (a/d/n/s)

- **Dual output formats:**
  - Annotated markdown: Inline annotations within original skill file
  - JSON: Structured output for CI/CD and batch analysis

- **Fail-forward with dependency awareness:** Layers handle failures gracefully and skip dependent layers when prerequisites fail

---

## Installation

```bash
# Clone the repository
git clone https://github.com/fjag/crible.git
cd crible

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install
pip install -e .
```

### Requirements

- **Python:** 3.8 or higher
- **Anthropic API Key:** Get yours at https://console.anthropic.com/
- **Dependencies:** Automatically installed (anthropic, click, rich, pyyaml)

---

## Setup

Configure your Anthropic API key:

```bash
# Option 1: Environment variable
export ANTHROPIC_API_KEY=your-api-key-here

# Option 2: Interactive setup (creates ~/.crible/config)
crible setup
```

---

## Usage

### Basic Assessment

```bash
# Interactive review - saves to skill_crible_report.md
crible assess skill.md

# Skip review for batch processing
crible assess skill.md --no-review

# JSON format for automation
crible assess skill.md --format json

# Use different model or skip layers
crible assess skill.md --model haiku --skip-layer 0
```

**Output:** Reports are saved to files (not printed to terminal) for better readability. Default filename: `<skill_name>_crible_report.md` (or `.json` for JSON format).

### Command Options

```
crible assess [OPTIONS] SKILL_FILE

Options:
  --format [annotated|json]   Output format (default: annotated)
  --output PATH               Output file path (auto-generated if omitted)
  --no-review                 Skip interactive review (accept all findings)
  --skip-layer INTEGER        Skip specific layer (can be repeated)
  --model [sonnet|opus|haiku] Claude model to use (default: sonnet)
  --verbose                   Show detailed execution logs
```

### Interactive Review

When reviewing findings, use single-letter shortcuts:
- **a** (accept) - Keep this finding as-is
- **d** (dismiss) - Mark as false positive (asks for reason)
- **n** (annotate) - Add context note
- **s** (skip_all) - Accept all remaining findings

See [USAGE_EXAMPLE.md](USAGE_EXAMPLE.md) for detailed examples.

---

## Expected Costs

Crible uses the Anthropic API, which charges per token. **Default model: Claude Sonnet 4.5** (`claude-sonnet-4-5-20250929`) - provides the best balance between analysis quality and cost.

**Available models:**
- `--model sonnet` (default): Claude Sonnet 4.5 - Balanced performance
- `--model opus`: Claude Opus 4.5 - Highest quality, highest cost
- `--model haiku`: Claude 3.5 Haiku - Fastest, lowest cost

| Skill Complexity | Model | Estimated Tokens | Approximate Cost* |
|------------------|-------|------------------|-------------------|
| Simple (10-20 steps) | Sonnet | 8,000 - 15,000 | $0.02 - $0.05 |
| Medium (20-50 steps) | Sonnet | 15,000 - 30,000 | $0.05 - $0.09 |
| Complex (50+ steps) | Sonnet | 30,000 - 60,000 | $0.09 - $0.18 |
| Complex (50+ steps) | Opus | 30,000 - 60,000 | $0.45 - $0.90 |

*Based on Anthropic API pricing as of March 2026. Actual costs vary based on skill length and complexity.

**Cost optimization:**
- Use `--model haiku` for batch processing (lower cost, slightly reduced quality)
- Use `--skip-layer 2` to skip execution trace (highest token consumer)

---

## Known Limitations

> **⚠️ IMPORTANT:** Crible is a best-effort quality linter, not a definitive bug detector. All findings should be manually reviewed by domain experts.

**Quick Summary:**
- ❌ Layer 0 catalogs but does NOT validate dependencies (no live registry checks)
- ⚠️ Layer 2 execution traces are predictions, not actual runs (confidence scores indicate uncertainty)
- 🔍 LLM-based findings may include false positives (use interactive review to dismiss)
- 🚫 Cannot check execution environment (RAM, installed software, file system)
- 🧬 Prompts optimized for bioinformatics (may underperform on other domains)
- 💰 Token costs accumulate with complex skill files

**📖 See [LIMITATIONS.md](LIMITATIONS.md) for detailed explanations, mitigation strategies, and workarounds.**

---

## Documentation

- **[USAGE_EXAMPLE.md](USAGE_EXAMPLE.md)** - Detailed usage examples and workflows
- **[OUTPUTS.md](OUTPUTS.md)** - Output format examples (annotated markdown and JSON)
- **[LIMITATIONS.md](LIMITATIONS.md)** - Comprehensive limitations documentation
- **[CI_CD.md](CI_CD.md)** - CI/CD integration guide (GitHub Actions, GitLab, Jenkins)
- **[IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md)** - Technical architecture details
- **[PROJECT_LEARNINGS.md](PROJECT_LEARNINGS.md)** - Development challenges and insights

---

## Architecture

### Layer Pipeline

Layers run sequentially with selective context passing:

1. **Layer 0** extracts dependencies (cataloging only - no validation in v1)
2. **Layer 1** scores instruction ambiguity (independent)
3. **Layer 2** simulates execution flow (uses Layer 1 summary for context)
4. **Layer 3** checks domain constraints (depends on Layer 2's inferred data type)

Each layer produces:
- **Detailed findings** for the final report
- **Condensed summary** for downstream layers (reduces token costs by ~60-70%)

### Error Handling

- **Independent layers** (0, 1, 2): Fail independently without affecting others
- **Dependent layers** (3): Skip if prerequisites fail, with clear error messages

See [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) for module structure and design details.

---

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest

# Run tests
pytest tests/
```

### Prompt Refinement

Dismissed findings generate training signal for prompt improvement:

```bash
# Collect dismissed findings across reports
find reports/ -name "*.json" -exec jq '.findings[] | select(.review_decision=="dismissed")' {} \;

# Analyze patterns: which layers overfire? Which categories are false positives?
# Refine prompts in crible/prompts/ based on patterns
# Regression test: re-run on previous skills
```

This creates a self-improving system over time.

---

## Contributing

Contributions welcome! Areas for improvement:
- Layer 0 validation with live registry APIs
- Additional layers (security, performance, reproducibility)
- Prompt refinement for non-bioinformatics domains
- Test coverage
- Documentation improvements

---

## Acknowledgements

Crible was co-developed with **Claude Code**, Anthropic's agentic coding tool. The implementation plan, architecture, and code were created through interactive planning and development sessions with Claude Sonnet 4.5.

For insights into the development process, challenges encountered, and lessons learned, see [PROJECT_LEARNINGS.md](PROJECT_LEARNINGS.md).

---

## License

MIT License - see [LICENSE](LICENSE) file

---

## Citation

If you use Crible in research, please cite:

```
Crible: Quality Assessment Tool for Bioinformatics Skill Files
Version 0.1.0 (2026)
https://github.com/fjag/crible
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

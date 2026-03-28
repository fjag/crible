# Crible

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Experimental](https://img.shields.io/badge/Status-Experimental-orange.svg)](https://github.com/fjag/crible)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Powered by Claude](https://img.shields.io/badge/Powered%20by-Claude%20API-blueviolet.svg)](https://www.anthropic.com/claude)


**Quality assessment tool for bioinformatics skill files**

The rapid proliferation of AI-generated, and insufficiently reviewed human-generated, skills targeting bioinformatics creates a real quality risk. Many lack ground-truth validation, conflate describing an analysis with correctly executing one, and use authoritative domain language without the scientific constraints that make it meaningful. Overstated automation claims are largely unfounded, and the downstream concern is concrete: users without deep domain grounding may trust outputs that are computationally plausible but biologically unreliable.

**Crible is an experimental response to this problem.** It assesses bioinformatics skill files across ambiguity, execution flow, and domain constraint dimensions using a four-layer Claude-powered pipeline, surfacing likely issues for human review before deployment — all without executing any code.

> **⚠️ EXPERIMENTAL TOOL:** Crible is a research tool designed to assist — not replace — expert judgement. Use findings as a starting point for manual review, not as definitive conclusions. Provided without warranty or support commitments. See full [disclaimer](#disclaimer) below.

---

## What Does It Do?

Crible performs **static quality analysis** on bioinformatics skill files. Given a skill file (like a scRNA-seq clustering workflow), Crible:

1. **Extracts dependencies** - Catalogs all mentioned tools, packages, databases, and files
2. **Identifies ambiguities** - Flags steps with multiple plausible interpretations (e.g., "normalize data" → which method?)
3. **Traces execution flow** - Predicts data transformations through the pipeline (e.g., raw counts → filtered → normalized → clustered)
4. **Checks domain constraints** - Validates methodological appropriateness (e.g., bulk methods applied to single-cell data)

**Example findings:**
- "Step 3 doesn't specify which normalization method (library size? SCTransform? TPM?)"
- "Step 5 performs PCA but no normalization precedes it"
- "Workflow assumes 10x Genomics data but presents as general scRNA-seq pipeline"

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

Crible uses the Anthropic API (charges per token). **Default model: Claude Sonnet 4.5** - best balance between quality and cost.

**Typical costs per skill:**
- Simple (10-20 steps): $0.02 - $0.05
- Medium (20-50 steps): $0.05 - $0.09
- Complex (50+ steps): $0.09 - $0.18

**Cost optimization:** Use `--model haiku` for batch processing (~50% savings), or `--skip-layer 2` to skip execution trace (~45% savings).

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

---

## Documentation

- **[USAGE_EXAMPLE.md](USAGE_EXAMPLE.md)** - Detailed usage examples and workflows
- **[OUTPUTS.md](OUTPUTS.md)** - Output format examples (annotated markdown and JSON)
- **[CI_CD.md](CI_CD.md)** - CI/CD integration guide (GitHub Actions, GitLab, Jenkins)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture, design patterns, and data models
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development setup, testing, and prompt development
- **[PROJECT_LEARNINGS.md](PROJECT_LEARNINGS.md)** - Development challenges and lessons learned

---

## Architecture

Crible uses a four-layer sequential assessment pipeline with selective context passing. Each layer produces detailed findings plus a condensed summary for downstream layers, reducing token costs by ~60-70%.

**Pipeline:** Layer 0 (dependencies) → Layer 1 (ambiguity) → Layer 2 (execution trace) → Layer 3 (domain constraints)

**Error handling:** Independent layers (0, 1, 2) fail independently. Dependent layer (3) skips if Layer 2 fails.

**📖 See [ARCHITECTURE.md](ARCHITECTURE.md) for complete technical details, design patterns, and performance characteristics.**

---

## Development

```bash
# Setup
pip install -e .
pip install pytest black flake8

# Run tests
pytest tests/

# Test on examples
crible assess examples/scrna_clustering.md --no-review
```

**Prompt refinement:** Dismissed findings generate training signal for iterative prompt improvement, creating a self-improving system over time.

**📖 See [DEVELOPMENT.md](DEVELOPMENT.md) for setup, testing, debugging, adding layers, and prompt development workflows.**

---

## Contributing

Contributions welcome! Priority areas: Layer 0 validation with live registry APIs, additional analysis layers (security, performance, reproducibility), prompt refinement for non-bioinformatics domains, and test coverage improvements.

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

Crible is an experimental research tool. Findings are suggestions for review, not definitive bugs. Always apply expert judgement and manual review — Crible assists but does not replace domain expertise.

**Key limitations:** Layer 0 catalogs but doesn't validate dependencies. Layer 2 execution traces are predictions with confidence scores. LLM-based analysis has inherent uncertainty. 

**MIT License** - provided as-is without warranty. Maintained on a best-effort basis.

---

**Built with Claude Sonnet 4.5 via the Anthropic API**

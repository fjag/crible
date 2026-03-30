# Crible Usage Example

This guide walks through complete examples of using Crible to assess bioinformatics skill files.

> **Prerequisites:** Install Crible and configure your API key. See [Installation](README.md#installation) and [Setup](README.md#setup) in the README.

## Example 1: Basic Assessment

Assess the example scRNA-seq clustering skill with interactive review:

```bash
crible assess examples/scrna_clustering.md
```

**What Crible will find:**

- **Layer 0:** Extracts dependencies (scanpy, Python 3.8+)
- **Layer 1:** Identifies ambiguities:
  - Step 1: 10x format version not specified (v2/v3/5')
  - Step 2: QC thresholds partially specified (min_genes=200 but no max_genes, no mito% filter)
  - Step 6: n_pcs=40 hardcoded without justification
- **Layer 2:** Traces execution flow, predicts data transformations
- **Layer 3:** May flag scope limitations (assumes human samples, 10x-specific)

**Interactive review process:**

1. Clear instructions shown upfront explaining each option
2. Crible presents findings grouped by severity (critical → warning → info)
3. For each finding, you choose (single letter shortcuts work):
   - **a** or **accept:** Keep as-is
   - **d** or **dismiss:** Mark as false positive (provide reason)
   - **n** or **annotate:** Add context note
   - **s** or **skip_all:** Accept all remaining findings
4. Report is saved to `scrna_clustering_crible_report.md`

## Example 2: JSON Output for downstream processing, e.g., pipelines, CI/CD

Generate JSON report without interactive review:

```bash
crible assess examples/scrna_clustering.md \
  --format json \
  --no-review \
  --output report.json
```

**Extract critical findings:**

```bash
jq '.findings[] | select(.severity=="critical")' report.json
```

**Check if assessment passes:**

```bash
# Exit with error if critical findings exist
if [ $(jq '.summary.by_severity.critical' report.json) -gt 0 ]; then
  echo "Critical findings detected!"
  exit 1
fi
```

## Example 3: Cost Optimization

Use Haiku model and skip Layer 0 to reduce token costs:

```bash
crible assess examples/scrna_clustering.md \
  --model haiku \
  --skip-layer 0 \
  --verbose
```

**Verbose output shows:**

```
Assessing: examples/scrna_clustering.md
Model: haiku
Total layers to run: 3

[Layer 0] Skipped by user request
[Layer 1] Executing: Ambiguity Scoring
[Layer 1] Success - found 4 findings
[Layer 2] Executing: Simulated Execution
[Layer 2] Success - found 3 findings
[Layer 3] Executing: Domain Constraints
[Layer 3] Success - found 1 findings

Pipeline complete in 12.3s
Total findings: 8
Token usage: 8,420
```

## Example 4: Batch Processing

Assess multiple skill files and aggregate results:

```bash
# Create reports directory
mkdir -p reports

# Process all skills in a directory
for skill in skills/*.md; do
  basename=$(basename "$skill" .md)
  crible assess "$skill" \
    --format json \
    --no-review \
    --output "reports/${basename}_report.json"
done

# Aggregate critical findings across all reports
jq -s 'map(.findings[] | select(.severity=="critical")) | group_by(.category) | map({category: .[0].category, count: length})' reports/*.json
```

**Output:**

```json
[
  {"category": "methodological_ambiguity", "count": 12},
  {"category": "execution_discrepancy", "count": 5},
  {"category": "domain_violation", "count": 3}
]
```

## Example 5: Analyzing Dismissed Findings

After reviewing many reports, analyze which findings users frequently dismiss (false positives):

```bash
# Extract all dismissed findings
jq -s 'map(.findings[] | select(.review_decision=="dismissed")) | group_by(.category) | map({category: .[0].category, count: length, reasons: map(.review_note)})' reports/*.json > dismissed_analysis.json

# Example output shows Layer 1 overfires on filename ambiguities
```

**Use this to refine prompts:**

1. Edit `crible/prompts/layer1_prompt.py`
2. Add examples of false positives to the prompt
3. Adjust severity thresholds
4. Re-test on previously assessed skills

## Example 6: Using Opus for Critical Assessments

For high-stakes skill files, use Opus for maximum quality:

```bash
crible assess critical_skill.md \
  --model opus \
  --output critical_assessment.md
```

**When to use Opus vs Sonnet vs Haiku:**

- **Opus:** Critical workflows, complex pipelines, maximum accuracy
- **Sonnet (default):** Balanced cost/quality for most use cases
- **Haiku:** Rapid prototyping, batch processing, cost-sensitive scenarios

## Example 7: Layer-Specific Analysis

Skip certain layers to focus on specific aspects:

```bash
# Only check ambiguities (skip dependency extraction, execution trace, domain constraints)
crible assess skill.md --skip-layer 0 --skip-layer 2 --skip-layer 3

# Only check execution flow and domain constraints
crible assess skill.md --skip-layer 0 --skip-layer 1
```

## Understanding Output

### Annotated Markdown

The default output format injects findings inline:

```markdown
### Step 3: Normalize Data

Normalize the count matrix.

> ⚠️ **WARNING: Execution Discrepancy** (Layer 2: Simulated Execution)
> **Issue:** Normalization method not specified. Could be library size, SCTransform, etc.
> **Recommendation:** Specify exact method (e.g., scanpy.pp.normalize_total)
> **Confidence:** 0.70
> **Review Status:** Accepted
```

### JSON Structure

```json
{
  "findings": [
    {
      "layer_id": 2,
      "layer_name": "Simulated Execution",
      "severity": "warning",
      "location": "step 3",
      "description": "Normalization method not specified...",
      "confidence": 0.70
    }
  ],
  "summary": {
    "total_findings": 8,
    "by_severity": {"critical": 2, "warning": 4, "info": 2}
  }
}
```

## Common Patterns

### Pattern 1: Pre-commit Hook

Add Crible check to Git pre-commit:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check modified skill files
for file in $(git diff --cached --name-only | grep '\.md$'); do
  if crible assess "$file" --no-review --format json | jq -e '.summary.by_severity.critical > 0' > /dev/null; then
    echo "Critical findings in $file - commit blocked"
    exit 1
  fi
done
```

### Pattern 2: GitHub Actions Workflow

```yaml
name: Skill Quality Check
on: [pull_request]

jobs:
  assess:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install Crible
        run: pip install crible
      - name: Assess Skills
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          for skill in skills/*.md; do
            crible assess "$skill" --no-review --format json --output "report_$(basename $skill).json"
          done
      - name: Upload Reports
        uses: actions/upload-artifact@v2
        with:
          name: assessment-reports
          path: "*.json"
```

## Tips

1. **Start with default settings** (`crible assess skill.md`) to understand what Crible finds
2. **Use --verbose** to see token usage and identify expensive layers
3. **Review findings interactively first**, then use --no-review for automation
4. **Track dismissed findings** to identify systematic false positives
5. **Iterate prompts** based on dismissed finding patterns
6. **Use JSON output** for programmatic analysis and CI/CD
7. **Choose models strategically**: Opus for critical, Haiku for batch

## Troubleshooting

### "API key not found"

```bash
# Verify environment variable
echo $ANTHROPIC_API_KEY

# Or run setup
crible setup
```

### "Layer X failed: ParseError"

The LLM response didn't match expected XML format. This can happen if:
- Skill file is very long (>20KB)
- Skill contains unusual formatting

**Solution:** Try with a different model or file a bug report.

### High token costs

- Use `--skip-layer` to skip non-essential layers
- Use `--model haiku` for cost control
- Break large skills into smaller sections

---

**Next Steps:** Read the full [README.md](README.md) for architecture details and known limitations.

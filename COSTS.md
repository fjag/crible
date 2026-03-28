# Cost Guide

Crible uses the Anthropic API, which charges per token (input and output). Understanding cost factors helps budget and optimize usage.

## Default Model

**Claude Sonnet 4.5** (`claude-sonnet-4-5-20250929`)
- Best balance between analysis quality and cost
- Recommended for production use
- All cost estimates below assume Sonnet unless stated otherwise

---

## Cost Estimates by Skill Complexity

Based on Anthropic API pricing as of March 2026:
- **Input tokens:** $3.00 per 1M tokens
- **Output tokens:** $15.00 per 1M tokens

### Simple Skills (10-20 steps)

**Characteristics:**
- Linear workflow
- Few tools/packages
- Clear instructions
- Minimal ambiguity

**Token Usage:**
- Haiku: 8,000 - 15,000 tokens
- Sonnet: 8,000 - 15,000 tokens
- Opus: 8,000 - 15,000 tokens

**Approximate Cost:**
| Model | Cost Range |
|-------|------------|
| Haiku | $0.01 - $0.02 |
| Sonnet | $0.02 - $0.05 |
| Opus | $0.45 - $0.90 |

**Examples:**
- Simple R script (load data, filter, plot)
- Basic Python workflow (read file, process, save)
- Linear bash pipeline (3-4 commands)

---

### Medium Skills (20-50 steps)

**Characteristics:**
- Some branching logic
- Multiple tools/packages
- Moderate documentation
- Some ambiguous steps

**Token Usage:**
- Haiku: 15,000 - 30,000 tokens
- Sonnet: 15,000 - 30,000 tokens
- Opus: 15,000 - 30,000 tokens

**Approximate Cost:**
| Model | Cost Range |
|-------|------------|
| Haiku | $0.02 - $0.04 |
| Sonnet | $0.05 - $0.09 |
| Opus | $0.45 - $0.90 |

**Examples:**
- scRNA-seq clustering workflow
- Variant calling pipeline (align → call → annotate)
- Multi-step data processing with QC

---

### Complex Skills (50+ steps)

**Characteristics:**
- Extensive workflow
- Many dependencies
- Detailed documentation
- Multiple analysis branches
- Comprehensive parameter specifications

**Token Usage:**
- Haiku: 30,000 - 60,000 tokens
- Sonnet: 30,000 - 60,000 tokens
- Opus: 30,000 - 60,000 tokens

**Approximate Cost:**
| Model | Cost Range |
|-------|------------|
| Haiku | $0.04 - $0.08 |
| Sonnet | $0.09 - $0.18 |
| Opus | $0.45 - $0.90 |

**Examples:**
- Complete scRNA-seq analysis (QC → normalization → clustering → DE → visualization)
- Genome assembly and annotation pipeline
- Multi-omics integration workflow

---

## Cost Breakdown by Layer

Token consumption varies by layer. Understanding this helps optimize with `--skip-layer`.

### Layer 0: Dependency Extraction
**Token usage:** ~2,000 - 3,000 tokens
**% of total:** ~12-15%
**Why low:** Simple pattern matching task, minimal reasoning

### Layer 1: Ambiguity Scoring
**Token usage:** ~4,000 - 6,000 tokens
**% of total:** ~25-30%
**Why moderate:** Requires evaluating each step for interpretations

### Layer 2: Simulated Execution Trace
**Token usage:** ~8,000 - 12,000 tokens
**% of total:** ~45-50%
**Why high:** Most complex task - traces data flow, infers types, predicts transformations

### Layer 3: Domain Constraint Checking
**Token usage:** ~3,000 - 5,000 tokens
**% of total:** ~15-20%
**Why moderate:** Depends on Layer 2 context but simpler validation task

**Optimization insight:** Skipping Layer 2 saves 40-50% of tokens but loses execution trace and makes Layer 3 less effective.

---

## Model Comparison

### Claude 3.5 Haiku
**Speed:** Fastest
**Quality:** Good for straightforward skills
**Cost:** Lowest

**Best for:**
- Batch processing many skills
- CI/CD pipelines
- Budget-constrained environments
- Simple skills with clear structure

**Trade-offs:**
- May miss subtle ambiguities
- Lower confidence in Layer 2 traces
- Fewer nuanced recommendations

---

### Claude Sonnet 4.5 (Default)
**Speed:** Moderate
**Quality:** High - best balance
**Cost:** Moderate

**Best for:**
- Production assessments
- Medium to complex skills
- Interactive review workflows
- General-purpose use

**Why default:**
- Excellent quality-to-cost ratio
- Handles ambiguity well
- Reliable execution traces
- Comprehensive findings

---

### Claude Opus 4.5
**Speed:** Slower
**Quality:** Highest
**Cost:** Highest (~5-10x Sonnet)

**Best for:**
- Critical skills requiring thorough review
- Research-grade documentation
- Complex multi-branch workflows
- When budget is not a constraint

**Trade-offs:**
- Significantly higher cost
- Longer execution time
- Marginal quality improvement over Sonnet for most skills

**Recommendation:** Reserve Opus for critical skills. Use Sonnet for routine assessments.

---

## Cost Optimization Strategies

### 1. Use Haiku for Batch Processing

```bash
# Process multiple skills with cost-effective model
for skill in skills/*.md; do
    crible assess "$skill" --model haiku --no-review --format json
done
```

**Savings:** ~50% compared to Sonnet
**Trade-off:** Slight quality reduction

---

### 2. Skip High-Token Layers

```bash
# Skip Layer 2 (execution trace) - saves 40-50% tokens
crible assess skill.md --skip-layer 2

# Skip Layer 0 (dependency extraction) if not needed - saves 12-15% tokens
crible assess skill.md --skip-layer 0
```

**Layer 2 considerations:**
- Highest token consumer
- Layer 3 becomes less effective without it
- Only skip if execution trace isn't needed

---

### 3. Simplify Before Assessment

**Break large skills into modules:**
```markdown
# Instead of one 100-step skill
skill_complete.md (100 steps) → ~$0.20

# Split into modules
skill_module1.md (30 steps) → ~$0.07
skill_module2.md (30 steps) → ~$0.07
skill_module3.md (40 steps) → ~$0.09
Total: ~$0.23 but easier to review
```

**Benefits:**
- More focused findings per module
- Easier to review smaller chunks
- Can assess modules independently

---

### 4. Use JSON Format for Batch Analysis

```bash
# JSON is lighter than annotated markdown rendering
crible assess skill.md --format json --no-review
```

**Savings:** Minimal (~5%) but adds up in batch processing

---

### 5. Conditional Layer Execution

```bash
# Quick first pass with Haiku, skip Layer 2
crible assess skill.md --model haiku --skip-layer 2 --no-review

# If issues found, full assessment with Sonnet
if [ $CRITICAL_COUNT -gt 0 ]; then
    crible assess skill.md --model sonnet
fi
```

---

## Budgeting for Projects

### Small Project (10-20 skills)
**Assumptions:** Mostly simple to medium complexity, Sonnet model

**Cost range:** $0.50 - $1.50
**Per skill average:** $0.05 - $0.075

---

### Medium Project (50-100 skills)
**Assumptions:** Mix of complexities, Sonnet model, some re-assessments

**Cost range:** $3.00 - $9.00
**Per skill average:** $0.06 - $0.09

**Optimization:**
- Use Haiku for initial pass: ~$1.50 - $4.50
- Use Sonnet for high-priority skills only

---

### Large Project (200+ skills)
**Assumptions:** Enterprise scale, CI/CD integration, regular re-assessment

**Cost range (one-time):** $12.00 - $36.00
**Monthly (with updates):** $5.00 - $15.00

**Optimization strategies:**
- Haiku for CI/CD: ~$4.00 - $12.00 one-time
- Sonnet for manual reviews only
- Skip Layer 0 for most skills (dependencies rarely change)
- Incremental assessment (only changed skills)

---

## Monitoring Costs

### Track Token Usage

Reports include execution metadata:
```json
{
  "execution_metadata": {
    "total_tokens": 12340,
    "duration_seconds": 18.3
  }
}
```

### Aggregate Across Assessments

```bash
# Total tokens consumed
jq -s 'map(.execution_metadata.total_tokens) | add' reports/*.json

# Estimate total cost (approximate: $6 per 1M tokens)
TOTAL_TOKENS=$(jq -s 'map(.execution_metadata.total_tokens) | add' reports/*.json)
echo "scale=4; $TOTAL_TOKENS / 1000000 * 6" | bc
```

### Set Budget Alerts

```bash
# Fail if token budget exceeded
MAX_TOKENS=50000  # ~$0.30
TOTAL=$(jq -s 'map(.execution_metadata.total_tokens) | add' reports/*.json)

if [ "$TOTAL" -gt "$MAX_TOKENS" ]; then
    echo "Budget exceeded: $TOTAL / $MAX_TOKENS tokens"
    exit 1
fi
```

---

## Cost Comparison: Crible vs Alternatives

### Manual Expert Review
**Cost:** $50-200 per skill (1-4 hours at $50/hr)
**Quality:** High
**Scalability:** Low

**When to use:**
- Critical production skills
- Final validation before deployment
- Complex domain-specific requirements

**Crible's role:** Pre-filter issues before expensive manual review

---

### Automated Testing
**Cost:** Infrastructure + maintenance (~$10-50/month for CI/CD)
**Quality:** Tests only what's written
**Scalability:** High

**When to use:**
- Execution validation
- Regression testing
- Output verification

**Crible's role:** Complements testing by catching ambiguities and domain issues testing can't

---

### Peer Review
**Cost:** Developer time (1-2 hours per skill)
**Quality:** Variable (depends on reviewer expertise)
**Scalability:** Low

**When to use:**
- Team collaboration
- Knowledge sharing
- Second opinions

**Crible's role:** Provides structured checklist for reviewers to focus on

---

## Real-World Cost Examples

### Example 1: scRNA-seq Clustering Skill
**Complexity:** Medium (35 steps)
**Model:** Sonnet
**Tokens:** 18,420
**Cost:** $0.055
**Time:** 22 seconds
**Findings:** 8 (2 critical, 3 warnings, 3 info)

---

### Example 2: Simple DESeq2 Workflow
**Complexity:** Simple (15 steps)
**Model:** Haiku
**Tokens:** 9,140
**Cost:** $0.011
**Time:** 11 seconds
**Findings:** 5 (1 critical, 2 warnings, 2 info)

---

### Example 3: Complex Multi-Omics Pipeline
**Complexity:** Complex (78 steps)
**Model:** Sonnet
**Tokens:** 42,680
**Cost:** $0.128
**Time:** 38 seconds
**Findings:** 23 (4 critical, 9 warnings, 10 info)

---

## Pricing Updates

Anthropic API pricing may change. Check current rates:
- **API Pricing:** https://www.anthropic.com/pricing

**Update frequency:** Review costs quarterly or when Anthropic announces pricing changes

**Cost calculator:**
```bash
# Calculate cost with current pricing
INPUT_PRICE=3.00    # per 1M tokens
OUTPUT_PRICE=15.00  # per 1M tokens

# Approximate: 70% input, 30% output
TOTAL_TOKENS=20000
INPUT_TOKENS=$(echo "$TOTAL_TOKENS * 0.7" | bc)
OUTPUT_TOKENS=$(echo "$TOTAL_TOKENS * 0.3" | bc)

INPUT_COST=$(echo "scale=4; $INPUT_TOKENS / 1000000 * $INPUT_PRICE" | bc)
OUTPUT_COST=$(echo "scale=4; $OUTPUT_TOKENS / 1000000 * $OUTPUT_PRICE" | bc)
TOTAL_COST=$(echo "$INPUT_COST + $OUTPUT_COST" | bc)

echo "Estimated cost: \$$TOTAL_COST"
```

---

## Summary

**Typical cost per skill:** $0.02 - $0.18 (Sonnet)

**Cost optimization:**
1. Use Haiku for batch processing (~50% savings)
2. Skip Layer 2 when execution trace not needed (~45% savings)
3. Break large skills into modules
4. Use JSON format for CI/CD
5. Reserve Opus for critical skills only

**Budget rule of thumb:** $0.05 - $0.10 per skill for routine Sonnet assessments

**ROI consideration:** Crible costs $0.05/skill vs $50-200 for manual expert review. Even catching one major issue justifies the cost.

---

## See Also

- [README.md](README.md#expected-costs) - Brief cost overview
- [CI_CD.md](CI_CD.md) - Cost management in automation pipelines
- [USAGE_EXAMPLE.md](USAGE_EXAMPLE.md) - Cost optimization examples

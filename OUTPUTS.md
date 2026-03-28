# Output Examples

Crible produces reports in two formats: **annotated markdown** (default) and **JSON** (for automation).

## Annotated Markdown Format

The default format creates a report that includes a copy of your skill file with findings embedded as inline annotations.

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

### Review Statistics
- **Accepted:** 6 findings
- **Dismissed:** 1 finding
- **Annotated:** 1 finding

### Execution Metadata
- **Total Tokens:** 12,340
- **Duration:** 18.3s
```

## JSON Format

Structured output for programmatic processing and CI/CD integration.

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
      "description": "Ambiguity level: HIGH. Plausible interpretations: 5+. Ambiguous aspects: Which 10x chemistry version? Which CellRanger output structure?",
      "recommendation": "Specify 10x chemistry version (3' v2/v3, 5', multiome) and CellRanger output structure (filtered vs raw, h5 vs mtx)",
      "confidence": null,
      "review_decision": "accepted",
      "review_note": null
    },
    {
      "layer_id": 2,
      "layer_name": "Simulated Execution",
      "category": "execution_discrepancy",
      "severity": "warning",
      "location": "step 3",
      "description": "Step performs normalization but method is unspecified. Could be library size, log-normalization, SCTransform, etc.",
      "recommendation": "Specify normalization method explicitly (e.g., 'scanpy.pp.normalize_total followed by scanpy.pp.log1p')",
      "confidence": 0.65,
      "review_decision": "annotated",
      "review_note": "Valid but our lab uses SCTransform by default - this is acceptable for us."
    }
  ],
  "summary": {
    "total_findings": 8,
    "by_severity": {
      "critical": 2,
      "warning": 3,
      "info": 3
    },
    "by_layer": {
      "0": 3,
      "1": 2,
      "2": 2,
      "3": 1
    },
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

## Key Report Features

### Finding Fields

Each finding includes:
- **layer_id** / **layer_name**: Which analysis layer produced it
- **category**: Type of issue (e.g., methodological_ambiguity, execution_discrepancy)
- **severity**: critical / warning / info
- **location**: Where in the skill file (step number, section name)
- **description**: What the issue is
- **recommendation**: How to fix it
- **confidence** (when applicable): 0.0-1.0 certainty score (Layer 2 only)
- **review_decision**: accepted / dismissed / annotated (after interactive review)
- **review_note**: User's explanation (for dismissed/annotated findings)

### Summary Statistics

Reports include aggregated metrics:
- Total findings by severity and layer
- Review statistics (accepted/dismissed/annotated counts)
- Token usage and execution time
- Layer-specific summaries for context

### Use Cases

**Annotated Markdown:**
- Human-readable review of skill files
- Documentation of quality assessment
- Sharing findings with collaborators

**JSON:**
- CI/CD integration (fail builds on critical findings)
- Batch analysis across multiple skill files
- Programmatic filtering and aggregation
- Prompt refinement (analyze dismissed findings)

## Real Example

See [examples/scrna_clustering_crible_report.md](examples/scrna_clustering_crible_report.md) for a complete example output.

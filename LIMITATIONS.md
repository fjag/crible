# Known Limitations

> **⚠️ IMPORTANT:** Crible is a best-effort quality linter, not a definitive bug detector. All findings should be manually reviewed by domain experts.

## Quick Summary

- ❌ Layer 0 catalogs but does NOT validate dependencies (no live registry checks)
- ⚠️ Layer 2 execution traces are predictions, not actual runs (confidence scores indicate uncertainty)
- 🔍 LLM-based findings may include false positives (use interactive review to dismiss)
- 🚫 Cannot check execution environment (RAM, installed software, file system)
- 🧬 Prompts optimized for bioinformatics (may underperform on other domains)
- 💰 Token costs accumulate with complex skill files (use `--model haiku` or `--skip-layer` to reduce)

---

## 1. Layer 0 Does Not Validate Dependencies (CRITICAL)

Layer 0 extracts dependencies but **does not validate them**. It cannot:
- Check if packages exist in Bioconda/PyPI/CRAN
- Detect deprecated tools
- Verify database URLs or genome assemblies
- Confirm version compatibility

**Why:** LLMs cannot reliably validate package registries from training knowledge alone. This requires live API calls to:
- Bioconda/Conda channels
- PyPI (Python Package Index)
- CRAN (R package repository)
- Bioconductor
- Tool-specific registries

**What Layer 0 Actually Does:**
- Catalogs mentioned dependencies (tools, packages, databases, files)
- Notes specified versions
- Clearly states "Validation requires live registry integration (not implemented)"

**Current Scope (v1):**
Dependency extraction is useful for:
- Creating a catalog of what's used in a skill
- Identifying missing version specifications
- Understanding external dependencies

But it **cannot** tell you:
- ✗ Whether `bwa-mem2` version 2.2.1 exists
- ✗ Whether `scanpy` 1.10.0 is deprecated
- ✗ Whether GRCh38.p14 is a valid genome assembly

**Future Work (v2):**
- Integration with Conda/Bioconda API
- PyPI package validation
- CRAN/Bioconductor checks
- URL validation (database links, genome references)
- Version compatibility checking

**Workaround:**
Manually verify dependencies using:
```bash
# Check if package exists
conda search bwa-mem2
pip search scanpy
```

---

## 2. Layer 2 Execution Trace is Best-Effort

Layer 2 attempts to trace data flow without executing code. This is inherently challenging.

**Works Well For:**
- Simple linear pipelines (step 1 → step 2 → step 3)
- Well-documented steps with explicit inputs/outputs
- Skills with clear data type specifications
- Standard bioinformatics workflows (align → filter → call variants)

**Struggles With:**
- Complex branching logic (if/else conditions)
- Loops and iteration
- Dynamic file path generation
- Ambiguous or underspecified steps
- Skills lacking context about data type
- Multi-file workflows with unclear dependencies

**Mitigation Strategy:**

1. **Confidence Scores (0.0-1.0):**
   - Each traced step includes a confidence score
   - `confidence > 0.7` = High confidence
   - `confidence 0.4-0.7` = Medium confidence (review carefully)
   - `confidence < 0.4` = Low confidence (flagged as uncertain)

2. **Warnings for Low Confidence:**
   - Steps with `confidence < 0.5` trigger warnings
   - Findings are marked "uncertain trace"

3. **Downstream Impact:**
   - Layer 3 receives Layer 2's average confidence
   - If `avg_confidence < 0.5`, Layer 3 findings are prefixed "Tentative (execution trace was uncertain)"

**Example Confident Trace:**
```
Step 1: Load 10x CellRanger output → AnnData object
Confidence: 0.95 (explicit format, standard tool)

Step 2: Filter cells with <200 genes → Filtered AnnData
Confidence: 0.90 (clear threshold specified)
```

**Example Uncertain Trace:**
```
Step 3: Normalize data → Normalized AnnData (?)
Confidence: 0.40 (method unspecified - could be library size, log, SCTransform, etc.)

Step 4: Cluster cells → Clustered AnnData (?)
Confidence: 0.35 (algorithm unspecified - Leiden/Louvain? Resolution?)
```

**User Action:**
When you see low-confidence traces, the skill file likely needs more detail. Crible flags these as areas to clarify.

---

## 3. LLM-Based Assessment Has Inherent Uncertainty

Crible uses LLMs to analyze skill files. LLMs are powerful but imperfect.

**Common Issues:**

1. **False Positives:**
   - Flagging valid patterns as problems
   - Missing context that makes ambiguity acceptable
   - Overly strict interpretations

2. **False Negatives:**
   - Missing subtle issues
   - Accepting patterns that are actually problematic
   - Insufficient domain knowledge in edge cases

3. **Context Limitations:**
   - Cannot see related files or surrounding project structure
   - Doesn't know your lab's conventions
   - May not understand field-specific norms

**How Crible Mitigates This:**

### Interactive Review
After assessment, you review each finding and can:
- **Accept:** Keep as-is (it's a valid issue)
- **Dismiss:** Mark as false positive (with reason)
- **Annotate:** Add context note (valid but acceptable for your use case)

### Audit Trail
All review decisions are preserved in reports:
```json
{
  "description": "Step uses DESeq2 on single-cell data",
  "review_decision": "dismissed",
  "review_note": "False positive - this skill is for pseudo-bulk analysis, not true single-cell"
}
```

### Prompt Refinement Signal
Dismissed findings help improve Crible:
- Collect dismissed findings across projects
- Analyze patterns (which categories overfire?)
- Refine prompts to reduce false positives
- Regression test on previous skill files

**Best Practice:**
Treat Crible findings as **code review suggestions**, not compiler errors. Always apply domain expertise when reviewing.

---

## 4. No Execution Environment Validation

Crible analyzes skill files in isolation. It cannot check:

**System Resources:**
- Available RAM / disk space
- CPU cores / GPU availability
- Network bandwidth

**Installed Software:**
- Which tools are actually installed
- Software versions on target system
- Library dependencies (system-level)

**File System:**
- Whether input files exist
- File permissions
- Directory structure

**Runtime Configuration:**
- Environment variables
- Shell configuration (PATH, LD_LIBRARY_PATH)
- Container/VM settings

**What Crible Can Do:**
- Flag when a skill assumes specific resources (e.g., "requires 64GB RAM")
- Note when file paths are hardcoded vs parameterized
- Identify when environment variables are referenced

**What It Cannot Do:**
- Verify those resources actually exist
- Check if files are present
- Validate environment setup

**Why This Matters:**
A skill might pass Crible's quality checks but still fail at runtime due to missing dependencies, insufficient resources, or file system issues.

**Recommendation:**
Combine Crible with:
- Runtime environment checks (Docker container validation)
- Dependency management (Conda environment.yml)
- Smoke tests (run on small test dataset)

---

## 5. Bioinformatics-Tuned Prompts

Crible's prompts are optimized for **bioinformatics workflows**:
- Genomics (alignment, variant calling, annotation)
- Transcriptomics (bulk RNA-seq, single-cell RNA-seq)
- Epigenomics (ChIP-seq, ATAC-seq)
- Metagenomics

**Expected Performance:**
- ✅ High quality for standard bioinformatics pipelines
- ⚠️ Moderate quality for related fields (proteomics, metabolomics)
- ❓ Unknown quality for distant domains (cheminformatics, image analysis, finance)

**Domain-Specific Knowledge Embedded:**
- Common tools (STAR, bwa, DESeq2, Seurat, Scanpy)
- Data formats (FASTQ, BAM, VCF, AnnData)
- Analysis patterns (QC → align → quantify → DE)
- Domain constraints (bulk vs single-cell methods)

**Adaptation Required For:**
- **Proteomics:** Mass spec workflows, peptide identification
- **Cheminformatics:** Molecular modeling, docking simulations
- **Image Analysis:** Segmentation, feature extraction pipelines
- **Clinical Data:** Patient records, cohort analysis

**How to Adapt:**
1. Review prompt templates in `crible/prompts/`
2. Add domain-specific examples
3. Update tool/format vocabularies
4. Test on representative skill files from target domain
5. Iterate based on false positive rates

**Future Work:**
- Pluggable prompt systems for different domains
- Domain detection (auto-select appropriate prompts)
- Community-contributed prompt libraries

---

## 6. Token Costs Can Accumulate

Crible makes multiple LLM API calls per assessment (one per layer). Token usage scales with:

**Skill File Complexity:**
- Simple (10-20 steps): ~8K-15K tokens
- Medium (20-50 steps): ~15K-30K tokens
- Complex (50+ steps): ~30K-60K tokens

**Context Passing:**
- Each layer receives a summary from upstream layers
- Summaries are condensed (not full output) to reduce cost
- Layer 2 (execution trace) is the highest token consumer

**Cost Examples (Sonnet model):**
- Simple skill: $0.02-$0.05
- Medium skill: $0.05-$0.09
- Complex skill: $0.09-$0.18

**Cost Optimization Strategies:**

1. **Use Haiku Model for Batch Processing:**
   ```bash
   crible assess skill.md --model haiku
   ```
   - ~50% cost reduction
   - Slight quality trade-off

2. **Skip Expensive Layers:**
   ```bash
   # Skip Layer 2 (execution trace - highest token use)
   crible assess skill.md --skip-layer 2

   # Skip Layer 0 (dependency extraction) if not needed
   crible assess skill.md --skip-layer 0
   ```

3. **Simplify Before Assessment:**
   - Break complex skills into smaller modules
   - Assess modules individually

4. **Use JSON Format for Batch Analysis:**
   - Reduces report rendering overhead
   - Easier to aggregate costs across runs

**Token Tracking:**
Final reports include token usage:
```
Execution Metadata:
- Total Tokens: 12,340
- Duration: 18.3s
```

**Budgeting Tips:**
- Set aside $0.10-$0.20 per skill assessment (Sonnet)
- Use Haiku for initial passes, Sonnet for final reviews
- Skip layers that don't apply to your use case

---

## 7. Reference Documentation vs Executable Skills

Crible was designed for **executable skill files** (step-by-step workflows). Performance varies on **reference documentation**.

**Executable Skill (Ideal):**
```markdown
## Workflow: Single-cell RNA-seq Analysis

1. Load 10x CellRanger output
2. Filter cells with <200 genes
3. Normalize with scanpy.pp.normalize_total
4. Run PCA on top 2000 variable genes
5. Cluster with Leiden algorithm (resolution=0.5)
```

**Reference Documentation (Suboptimal):**
```markdown
## DESeq2 Documentation

### Creating DESeqDataSet

From count matrix:
dds <- DESeqDataSetFromMatrix(...)

From SummarizedExperiment:
dds <- DESeqDataSet(se, ...)

From tximport:
dds <- DESeqDataSetFromTximport(...)
```

**Challenge:**
Reference docs contain multiple variations/options but no single workflow to trace. Crible may:
- Generate excessive findings (flagging every variation)
- Struggle to infer a single execution flow
- Report high ambiguity scores for intentionally flexible patterns

**Mitigation (Implemented):**
Prompts now include:
- "For reference documentation skills, focus on workflow patterns rather than every example variation"
- "Summarize groups of similar steps rather than enumerating all"

But performance on reference docs is still lower than on executable workflows.

**Recommendation:**
- Use Crible primarily on **procedural skill files** (scripts, workflows, SOPs)
- Reference documentation benefits less from Crible's analysis
- If assessing reference docs, expect more false positives

---

## Summary

Crible is a **research tool** designed to surface potential issues in skill files. It excels at:
- Finding ambiguous instructions
- Identifying missing specifications
- Highlighting methodological mismatches

But it has clear boundaries:
- Not a validator (Layer 0)
- Not an executor (Layer 2 is predictive)
- Not infallible (LLM uncertainty)
- Not environment-aware (no system checks)
- Domain-tuned (bioinformatics focus)

**Use Crible as part of a quality workflow:**
1. ✅ Crible assessment (automated checks)
2. ✅ Manual expert review (domain knowledge)
3. ✅ Smoke testing (run on test data)
4. ✅ Peer review (collaborative validation)

No single tool replaces expert judgment. Crible amplifies it.

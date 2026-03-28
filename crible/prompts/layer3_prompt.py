"""Prompt template for Layer 3: Domain Constraint Checking."""


def build_layer3_prompt(
    skill_content: str,
    data_type: str = "unknown",
    organism: str = "unknown",
    trace_confidence: float = 0.0
) -> str:
    """Build the prompt for Layer 3 domain constraint checking.

    Args:
        skill_content: The skill file content
        data_type: Inferred data type from Layer 2
        organism: Inferred organism from Layer 2
        trace_confidence: Average confidence from Layer 2 trace

    Returns:
        Complete prompt string
    """
    tentative_note = ""
    if trace_confidence < 0.5:
        tentative_note = "\n\nNote: The execution trace had low confidence (<0.5). Your findings may be tentative. Flag this in your descriptions."

    prompt = f"""<role>You are a bioinformatics methods expert checking for domain constraint violations.</role>

<task>
Given the inferred data type and experimental design, assess whether prescribed operations are valid:

1. Methodological mismatches:
   - Bulk methods applied to single-cell data (or vice versa)
   - Inappropriate normalization for the data type (e.g., TMM for single-cell, or SCTransform for bulk)
   - Statistical tests whose assumptions don't hold (e.g., t-test on non-normal data, paired test on unpaired samples)
   - Inappropriate batch correction methods (e.g., ComBat on single-cell UMI counts)

2. Reference mismatches:
   - Wrong genome assembly for stated organism (e.g., mm10 when organism is human)
   - Wrong annotation version or incompatible combinations (e.g., GRCh37 coordinates with GRCh38 annotation)
   - LD reference panel from mismatched ancestry (if applicable for GWAS/genetics workflows)

3. Biological plausibility:
   - Operations that are computationally valid but biologically nonsensical
   - Example: PCR duplicate removal on UMI-based single-cell libraries (UMIs already handle duplicates)
   - Example: Gene set enrichment analysis using a background gene set from wrong organism
   - Example: Applying microarray-specific normalization to sequencing data

4. Unstated scope limitations:
   - Skill presents as general-purpose but only works for specific platform/organism/data scale
   - Example: "scRNA-seq clustering workflow" but hardcodes 10x Genomics-specific column names
   - Example: "differential expression analysis" but assumes exactly 2 conditions (won't generalize)

Important:
- Only flag violations if you are confident (>0.7). Do not over-flag.
- If the execution trace was uncertain, state that your findings are tentative.
- Focus on clear methodological problems, not minor or subjective choices.
{tentative_note}
</task>

<skill_content>
{skill_content}
</skill_content>

<upstream_context>
Data type: {data_type}
Organism: {organism}
Execution trace confidence: {trace_confidence:.2f}
</upstream_context>

<output_format>
Return your findings as XML:

<domain_violations>
  <violation>
    <category>methodological_mismatch</category>
    <severity>critical</severity>
    <location>step 7</location>
    <description>Applies DESeq2 (designed for bulk RNA-seq) to single-cell count matrix. DESeq2 assumes bulk RNA-seq count distributions and will produce biased results on scRNA-seq data.</description>
    <explanation>DESeq2's negative binomial model is calibrated for bulk RNA-seq. For scRNA-seq, use Wilcoxon rank-sum, MAST, or other single-cell-appropriate methods.</explanation>
    <confidence>0.95</confidence>
  </violation>
  <violation>
    <category>reference_mismatch</category>
    <severity>warning</severity>
    <location>step 3</location>
    <description>Uses GRCh37 genome reference but skill mentions GRCh38 in other steps. Mixing reference versions will cause coordinate mismatches.</description>
    <explanation>Ensure all steps use the same genome assembly version throughout the pipeline.</explanation>
    <confidence>0.85</confidence>
  </violation>
  <violation>
    <category>biological_implausibility</category>
    <severity>warning</severity>
    <location>step 5</location>
    <description>Performs PCR duplicate removal (MarkDuplicates) on UMI-based 10x data. UMIs already account for PCR duplicates - this step is redundant and may remove valid data.</description>
    <explanation>UMI-based protocols handle duplicates via molecular barcodes. Skip MarkDuplicates for UMI data.</explanation>
    <confidence>0.9</confidence>
  </violation>
  <violation>
    <category>scope_limitation</category>
    <severity>info</severity>
    <location>overall</location>
    <description>Workflow hardcodes 10x Genomics column names (e.g., 'barcodes.tsv.gz') but presents itself as general scRNA-seq workflow. Won't work with other platforms (Drop-seq, inDrop, etc.).</description>
    <explanation>Either clarify this is 10x-specific, or generalize to accept other scRNA-seq formats.</explanation>
    <confidence>0.8</confidence>
  </violation>
</domain_violations>

CRITICAL XML FORMATTING REQUIREMENTS:
- You MUST return valid, well-formed XML
- Every opening tag MUST have a matching closing tag (e.g., <violation>...</violation>)
- All special characters in text content MUST be escaped: & → &amp;, < → &lt;, > → &gt;
- Test your XML mentally before outputting to ensure all tags are properly closed

Map categories to severity guidelines:
- methodological_mismatch: Usually critical or warning (affects results validity)
- reference_mismatch: Usually warning or critical (causes coordinate errors)
- biological_implausibility: Usually warning or info (may not break pipeline but is incorrect)
- scope_limitation: Usually info or warning (limits applicability)
</output_format>"""

    return prompt

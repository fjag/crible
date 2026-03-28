"""Prompt template for Layer 2: Simulated Execution Trace."""


def build_layer2_prompt(skill_content: str, layer1_summary: str = "") -> str:
    """Build the prompt for Layer 2 execution trace.

    Args:
        skill_content: The skill file content
        layer1_summary: Summary from Layer 1 (ambiguity findings)

    Returns:
        Complete prompt string
    """
    upstream_section = ""
    if layer1_summary:
        upstream_section = f"""
<upstream_context>
{layer1_summary}
</upstream_context>
"""

    prompt = f"""<role>You are a computational biologist tracing execution flow through a bioinformatics skill.</role>

<task>
Without executing code, trace what would happen if this skill were run:

1. Infer implied input characteristics from the skill text:
   - Data type (bulk RNA-seq, scRNA-seq, WGS, WES, ChIP-seq, ATAC-seq, proteomics, etc.)
   - Format (FASTQ, BAM, count matrix, VCF, BED, etc.)
   - Scale (number of samples, cells, reads - if inferable)
   - Organism (if specified or inferable)
   - Experimental design (paired-end, single-cell platform, etc.)

2. For each step, predict:
   - What input it expects (format, type, approximate size)
   - What operation it performs
   - What output it produces
   - Your confidence in this prediction (0.0-1.0)

3. Identify discrepancies:
   - Steps that assume inputs not produced by prior steps
   - Outputs produced but never consumed downstream
   - Implicit dependencies on tool defaults that could vary
   - Gaps between stated goal and actual operations

Important guidelines:
- If a step is too ambiguous to trace confidently, say so explicitly and assign low confidence (<0.5)
- Do not guess or invent details not present in the skill
- Focus on data flow and dependencies, not detailed parameter choices
- Assign confidence based on how explicit the skill is about each step

</task>

<skill_content>
{skill_content}
</skill_content>
{upstream_section}

<output_format>
Return your findings as XML with this exact structure:

<execution_trace>
  <inferred_input>
    <data_type>scRNA-seq</data_type>
    <format>10x CellRanger output (matrix.mtx, barcodes.tsv, features.tsv)</format>
    <organism>human</organism>
    <scale>10,000-50,000 cells</scale>
    <experimental_design>10x Genomics 3' v3 chemistry</experimental_design>
    <confidence>0.9</confidence>
  </inferred_input>

  <trace>
    <step id="1">
      <location>step 1</location>
      <expected_input>CellRanger output directory</expected_input>
      <operation>Load count matrix into Scanpy AnnData object</operation>
      <predicted_output>AnnData object (cells × genes)</predicted_output>
      <confidence>0.95</confidence>
      <note>Input format explicitly stated</note>
    </step>
    <step id="2">
      <location>step 2</location>
      <expected_input>Raw AnnData object</expected_input>
      <operation>Filter cells with fewer than 200 detected genes</operation>
      <predicted_output>Filtered AnnData object (subset of original)</predicted_output>
      <confidence>0.9</confidence>
      <note>Threshold value (200) clearly specified</note>
    </step>
    <step id="3">
      <location>step 3</location>
      <expected_input>Filtered AnnData object</expected_input>
      <operation>Normalize data</operation>
      <predicted_output>Normalized AnnData object</predicted_output>
      <confidence>0.4</confidence>
      <note>Normalization method not specified - could be library size, SCTransform, etc.</note>
    </step>
  </trace>

  <discrepancies>
    <discrepancy>
      <location>step 5</location>
      <severity>warning</severity>
      <description>Step performs PCA but no normalization step precedes it. PCA on raw counts will produce biased results.</description>
      <confidence>0.85</confidence>
    </discrepancy>
    <discrepancy>
      <location>step 8</location>
      <severity>info</severity>
      <description>Step generates UMAP visualization but this output is never mentioned in subsequent steps or final outputs.</description>
      <confidence>0.7</confidence>
    </discrepancy>
  </discrepancies>
</execution_trace>

CRITICAL XML FORMATTING REQUIREMENTS:
- You MUST return valid, well-formed XML
- Every opening tag MUST have a matching closing tag (e.g., <step>...</step>)
- All special characters in text content MUST be escaped: & → &amp;, < → &lt;, > → &gt;
- Keep attribute values in quotes (e.g., id="1")
- If the skill has many steps (>10), summarize groups of similar steps rather than enumerating all of them
- Test your XML mentally before outputting to ensure all tags are properly closed

Format requirements:
- Always include <inferred_input> with at least data_type and confidence
- Each <step> must have id, location, operation, predicted_output, and confidence
- Confidence values must be between 0.0 and 1.0
- Discrepancies should have severity (critical/warning/info), description, and confidence
- Low confidence (<0.5) indicates uncertainty - still provide best guess but flag it clearly
- For reference documentation skills (like this one), focus on workflow patterns rather than every example variation
</output_format>"""

    return prompt

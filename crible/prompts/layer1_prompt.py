"""Prompt template for Layer 1: Instruction Ambiguity Scoring."""


def build_layer1_prompt(skill_content: str) -> str:
    """Build the prompt for Layer 1 ambiguity scoring.

    Args:
        skill_content: The skill file content

    Returns:
        Complete prompt string
    """
    prompt = f"""<role>You are a bioinformatics methods specialist reviewing a skill file for execution ambiguity.</role>

<task>
For each instruction step in this skill, assess:
1. How many distinct, plausible execution paths exist?
2. What specifically is ambiguous? (tool choice, parameters, input format, filtering criteria, thresholds, etc.)
3. What is the consequence of this ambiguity? (cosmetic vs. methodological impact)
4. What information is needed to resolve it?

Score ambiguity as:
- LOW: 1-2 plausible interpretations, or ambiguity is cosmetic only (e.g., output filename choice)
- MEDIUM: 3-5 plausible interpretations with methodological impact
- HIGH: >5 interpretations, or core methodological choice is unspecified

Examples:
- "Align reads to the reference" → HIGH (which aligner? bwa/bowtie2/STAR? which parameters? which reference version?)
- "Normalize the data" → HIGH (which method? library size/TMM/quantile/SCTransform?)
- "Run bwa-mem2 mem -t 8 against GRCh38.p14, output coordinate-sorted BAM" → LOW (fully specified)
- "Filter low-quality cells" → MEDIUM (what threshold? which metrics? library size/gene count/mito%?)

</task>

<skill_content>
{skill_content}
</skill_content>

<output_format>
Return your findings as XML:

<ambiguity_findings>
  <finding>
    <location>step 2</location>
    <ambiguity_score>HIGH</ambiguity_score>
    <plausible_interpretations>7+</plausible_interpretations>
    <ambiguous_aspects>aligner choice (bwa/bowtie2/STAR/minimap2), reference version (GRCh37/GRCh38/T2T), output format (SAM/BAM/CRAM), sort order</ambiguous_aspects>
    <consequence>methodological - different aligners produce different results, affecting all downstream analysis</consequence>
    <resolution>Specify: exact tool and version (e.g., bwa-mem2 2.2.1), reference assembly with version (e.g., GRCh38.p14), output format and sort order</resolution>
  </finding>
  <finding>
    <location>step 5</location>
    <ambiguity_score>MEDIUM</ambiguity_score>
    <plausible_interpretations>4</plausible_interpretations>
    <ambiguous_aspects>filtering threshold, which quality metrics to use</ambiguous_aspects>
    <consequence>methodological - affects how many cells/samples are retained</consequence>
    <resolution>Specify exact thresholds: min genes per cell, max mitochondrial percentage, min UMI count</resolution>
  </finding>
  <finding>
    <location>step 10</location>
    <ambiguity_score>LOW</ambiguity_score>
    <plausible_interpretations>2</plausible_interpretations>
    <ambiguous_aspects>output filename</ambiguous_aspects>
    <consequence>cosmetic - does not affect analysis results</consequence>
    <resolution>Specify preferred output filename format (optional)</resolution>
  </finding>
</ambiguity_findings>

CRITICAL XML FORMATTING REQUIREMENTS:
- You MUST return valid, well-formed XML
- Every opening tag MUST have a matching closing tag (e.g., <finding>...</finding>)
- All special characters in text content MUST be escaped: & → &amp;, < → &lt;, > → &gt;
- For reference documentation skills with many examples, focus on workflow patterns and key decision points rather than every code variation
- Test your XML mentally before outputting to ensure all tags are properly closed

Map ambiguity scores to severity:
- HIGH → critical
- MEDIUM → warning
- LOW → info
</output_format>"""

    return prompt

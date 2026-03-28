"""Prompt template for Layer 0: Dependency Extraction."""


def build_layer0_prompt(skill_content: str) -> str:
    """Build the prompt for Layer 0 dependency extraction.

    Args:
        skill_content: The skill file content

    Returns:
        Complete prompt string
    """
    prompt = f"""<role>You are a technical reviewer analyzing a bioinformatics skill file.</role>

<task>
Extract all external dependencies mentioned in this skill file:

1. Software tools and packages (e.g., bwa, Seurat, scanpy, DESeq2, STAR)
2. Package versions if explicitly specified
3. Databases and web resources (URLs, Ensembl releases, genome assemblies like GRCh38)
4. Required local files or directory structures that must pre-exist
5. Environment variables or configuration assumptions

Important:
- Do NOT attempt to validate whether these dependencies exist or are current
- Only identify what is referenced in the skill
- If a version is specified, note it; if not, mark as "unspecified"
- Include programming language dependencies (R packages, Python libraries)

This layer catalogs dependencies but does not validate them. Validation requires live registry integration (not implemented in v1).
</task>

<skill_content>
{skill_content}
</skill_content>

<output_format>
Return your findings as XML:

<dependencies>
  <dependency>
    <type>tool</type>
    <name>bwa-mem2</name>
    <version>2.2.1</version>
    <location>step 3</location>
    <note>Validation requires live registry integration (not implemented)</note>
  </dependency>
  <dependency>
    <type>python_package</type>
    <name>scanpy</name>
    <version>unspecified</version>
    <location>step 1</location>
    <note>Validation requires live registry integration (not implemented)</note>
  </dependency>
  <dependency>
    <type>database</type>
    <name>GRCh38.p14</name>
    <version>unspecified</version>
    <location>step 2</location>
    <note>Genome reference assembly. Validation requires live check of Ensembl/NCBI.</note>
  </dependency>
  <dependency>
    <type>file</type>
    <name>/data/reference/genome.fa</name>
    <version>N/A</version>
    <location>step 2</location>
    <note>Assumes pre-existing local file. Cannot validate without filesystem access.</note>
  </dependency>
  <dependency>
    <type>url</type>
    <name>https://example.com/data/sample.fastq.gz</name>
    <version>N/A</version>
    <location>step 1</location>
    <note>External URL. Validation requires live HTTP request (not implemented).</note>
  </dependency>
</dependencies>

CRITICAL XML FORMATTING REQUIREMENTS:
- You MUST return valid, well-formed XML
- Every opening tag MUST have a matching closing tag (e.g., <dependency>...</dependency>)
- All special characters in text content MUST be escaped: & → &amp;, < → &lt;, > → &gt;
- Test your XML mentally before outputting to ensure all tags are properly closed

Types:
- tool: Command-line tools, bioinformatics software
- python_package: Python libraries (pip/conda)
- r_package: R packages (CRAN/Bioconductor)
- database: Reference databases, genome assemblies
- file: Local file paths
- url: Web resources
- config: Environment variables or configuration files
</output_format>"""

    return prompt

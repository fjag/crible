# Architecture

## Overview

Crible uses a four-layer sequential assessment pipeline with selective context passing to reduce token costs while preserving essential information flow.

## Module Structure

```
crible/
├── cli.py                      # CLI entry point with Click framework
├── pipeline.py                 # Orchestrates layer execution and context management
├── review_interface.py         # Interactive review UI with Rich terminal formatting
├── layers/
│   ├── base.py                 # Abstract Layer class (template method pattern)
│   ├── layer0.py               # Dependency extraction
│   ├── layer1.py               # Ambiguity scoring
│   ├── layer2.py               # Simulated execution trace
│   └── layer3.py               # Domain constraint checking
├── models/
│   ├── finding.py              # Finding dataclass with validation
│   ├── report.py               # Report aggregate with summary methods
│   └── layer_result.py         # LayerResult dataclass for pipeline communication
├── prompts/
│   ├── layer0_prompt.py        # Dependency extraction prompt template
│   ├── layer1_prompt.py        # Ambiguity scoring prompt with examples
│   ├── layer2_prompt.py        # Execution trace prompt (most complex)
│   └── layer3_prompt.py        # Domain constraint prompt with context
├── output/
│   ├── json_output.py          # JSON renderer for automation
│   └── annotated_markdown.py   # Markdown renderer with inline annotations
└── utils/
    ├── llm_client.py           # Anthropic API wrapper with retry logic
    └── xml_parser.py           # XML response parser with cleaning
```

---

## Layer Pipeline

### Execution Flow

Layers run **sequentially** with **selective context passing**:

```
Layer 0 (Dependency Extraction)
    ↓ [summary: "Found 5 dependencies..."]
Layer 1 (Ambiguity Scoring)
    ↓ [summary: "2 high-ambiguity, 3 medium..."]
Layer 2 (Execution Trace) ← receives Layer 1 summary
    ↓ [summary: "Inferred scRNA-seq, confidence 0.85..."]
Layer 3 (Domain Constraints) ← receives Layer 2 summary
    ↓ [detailed findings]
Report Generation
```

### Layer Details

#### Layer 0: Dependency Extraction
**Purpose:** Catalog all external dependencies mentioned in the skill file

**Input:**
- Raw skill file content

**Process:**
- LLM identifies tools, packages, databases, files, URLs
- Notes specified versions
- **Does NOT validate** (no live registry checks)

**Output:**
- Findings: List of identified dependencies with type and location
- Summary: "Identified N dependencies: X tools, Y packages, Z databases"

**Limitations:**
- Cannot verify package existence
- Cannot check version availability
- Cannot validate URLs or database references

---

#### Layer 1: Ambiguity Scoring
**Purpose:** Assess how many plausible interpretations each instruction step has

**Input:**
- Raw skill file content
- (Independent of Layer 0)

**Process:**
- LLM scores each step: LOW (1-2 interpretations), MEDIUM (3-5), HIGH (5+)
- Categorizes ambiguity: tool choice, parameters, thresholds, methods
- Assesses consequence: cosmetic vs methodological impact

**Output:**
- Findings: Ambiguous steps with severity (HIGH→critical, MEDIUM→warning, LOW→info)
- Summary: "X high-ambiguity, Y medium, Z low-ambiguity steps"

**Example:**
- "Normalize data" → HIGH (library size? log? SCTransform? TPM?)
- "Run bwa-mem2 with default settings" → MEDIUM (defaults may vary by version)
- "Save output as results.csv" → LOW (filename is cosmetic)

---

#### Layer 2: Simulated Execution Trace (Highest Risk)
**Purpose:** Predict data flow through the pipeline without executing code

**Input:**
- Raw skill file content
- Layer 1 summary (for context on ambiguous steps)

**Process:**
- LLM infers input data type (scRNA-seq, bulk RNA-seq, WGS, etc.)
- Traces expected transformations step-by-step
- Assigns confidence (0.0-1.0) to each traced step
- Identifies discrepancies (missing inputs, unused outputs, gaps)

**Output:**
- Findings:
  - Inferred input (data type, format, organism, confidence)
  - Low-confidence trace steps (<0.5 confidence flagged as warnings)
  - Execution discrepancies
- Summary: "Inferred data type X (conf Y), traced N steps (avg conf Z), M discrepancies"

**Confidence Scoring:**
- `>0.7` = High confidence (explicit specification)
- `0.4-0.7` = Medium confidence (some ambiguity)
- `<0.4` = Low confidence (insufficient detail, flagged)

**Challenges:**
- Works well for linear pipelines
- Struggles with branching, loops, conditionals
- Quality depends on skill file detail level

---

#### Layer 3: Domain Constraint Checking (Depends on Layer 2)
**Purpose:** Validate methodological appropriateness given inferred data context

**Input:**
- Raw skill file content
- Layer 2 summary (inferred data type, organism, trace confidence)

**Process:**
- LLM checks for:
  - Methodological mismatches (e.g., bulk methods on single-cell data)
  - Reference mismatches (e.g.,wrong genome assembly)
  - Biological implausibility (e.g., PCR dedup on UMI data)
  - Scope limitations (e.g., 10x-specific code presented as general)
- If Layer 2 had low confidence, findings prefixed "Tentative"

**Output:**
- Findings: Domain violations with category and confidence
- Summary: "Found N domain issues: X critical, Y warnings"

**Dependency Handling:**
- If Layer 2 failed → Layer 3 skips with error message
- If Layer 2 had `avg_confidence < 0.5` → Layer 3 runs but flags findings as tentative

---

## Context Management Strategy

### Problem: Context Accumulation
Without summarization, passing full layer outputs creates exponential token growth:
- Layer 1: 10K tokens
- Layer 2: 10K + Layer 1 (10K) = 20K tokens
- Layer 3: 10K + Layer 2 (20K) = 30K tokens
- Total: 60K tokens (vs 30K if independent)

### Solution: Selective Context Passing
Each layer produces:
1. **Detailed findings** → Saved to report (full information preserved)
2. **Condensed summary** → Passed to downstream layers (key info only)

**Summary Format:**
- 50-150 words
- Key metrics (counts, severity distribution)
- Critical information for next layer (e.g., inferred data type for Layer 3)
- Confidence indicators

**Token Reduction:**
- ~60-70% reduction in cumulative context
- Layer 3 receives summaries, not full outputs from Layers 0, 1, 2

---

## Error Handling

### Layer Independence vs Dependency

**Independent Layers (0, 1, 2):**
- Can fail without affecting each other
- Errors logged as findings in report
- Pipeline continues to next layer

**Dependent Layer (3):**
- Requires Layer 2 to succeed (needs inferred data type)
- If Layer 2 fails → Layer 3 skipped with error finding
- If Layer 2 succeeds but low confidence → Layer 3 runs with "tentative" prefix on findings

### Error Types

**ParseError (XML malformed):**
- Layer catches ET.ParseError from LLM response
- Shows response snippet for debugging
- Creates error finding: "Layer X failed: XML parsing error"
- Suggests `--skip-layer X` to user

**APIError (Anthropic API):**
- Retry with exponential backoff (up to 3 attempts)
- If retries exhausted → Layer fails, pipeline continues

**ValidationError (invalid data):**
- Finding validation fails (e.g., invalid severity value)
- Layer fails, error logged as finding

---

## Design Patterns

### Template Method Pattern (Base Layer)

```python
class Layer(ABC):
    def execute(self, skill_content: str, upstream_context: Dict) -> LayerResult:
        """Template method - defines execution structure"""
        try:
            prompt = self.build_prompt(skill_content, upstream_context)
            response = self.llm_client.generate(prompt)
            findings, summary = self.parse_response(response)
            return LayerResult(success=True, findings=findings, summary=summary)
        except Exception as e:
            return LayerResult(success=False, error=str(e))

    @abstractmethod
    def build_prompt(self, skill_content: str, upstream_context: Dict) -> str:
        """Subclass implements prompt construction"""
        pass

    @abstractmethod
    def parse_response(self, response: str) -> Tuple[List[Finding], str]:
        """Subclass implements response parsing"""
        pass
```

**Benefits:**
- Shared error handling and execution logic
- Consistent layer interface
- Easy to add new layers (just implement build_prompt and parse_response)

---

## Data Models

### Finding

```python
@dataclass
class Finding:
    layer_id: int              # 0-3
    layer_name: str            # "Ambiguity Scoring", "Simulated Execution", etc.
    category: str              # "methodological_ambiguity", "execution_discrepancy", etc.
    severity: str              # "critical" | "warning" | "info"
    location: str              # "step 3", "line 45-52", "overall"
    description: str           # What the issue is
    recommendation: str        # How to fix it
    confidence: Optional[float] = None  # Layer 2 only: 0.0-1.0
    review_decision: Optional[str] = None  # "accepted" | "dismissed" | "annotated"
    review_note: Optional[str] = None      # User's explanation
```

**Validation:**
- Severity must be in {"critical", "warning", "info"}
- Confidence must be 0.0-1.0 if present
- Review decision must be in {"accepted", "dismissed", "annotated"} if present

---

### Report

```python
@dataclass
class Report:
    skill_file_path: str
    timestamp: datetime
    findings: List[Finding]
    layer_summaries: Dict[int, str]  # {layer_id: summary_text}
    execution_metadata: Dict[str, Any]  # model, tokens, duration

    def findings_by_severity(self) -> Dict[str, List[Finding]]:
        """Group findings: critical, warning, info"""

    def findings_by_layer(self) -> Dict[int, List[Finding]]:
        """Group findings by layer"""

    def get_review_statistics(self) -> Dict[str, int]:
        """Count accepted/dismissed/annotated findings"""
```

---

### LayerResult

```python
@dataclass
class LayerResult:
    success: bool
    findings: List[Finding] = field(default_factory=list)
    summary: str = ""
    error: Optional[str] = None
```

Used for layer-to-pipeline communication.

---

## Pipeline Orchestration

```python
class PipelineOrchestrator:
    def run(self, skill_file_path: str) -> Report:
        skill_content = read_file(skill_file_path)

        findings = []
        layer_summaries = {}
        upstream_context = {}

        for layer in self.layers:
            result = layer.execute(skill_content, upstream_context)

            if result.success:
                findings.extend(result.findings)
                layer_summaries[layer.layer_id] = result.summary
                upstream_context[layer.layer_id] = result.summary
            else:
                # Log error as finding
                error_finding = Finding(
                    layer_id=layer.layer_id,
                    layer_name=layer.layer_name,
                    category="layer_error",
                    severity="warning",
                    location="layer execution",
                    description=f"Layer {layer.layer_id} failed: {result.error}",
                    recommendation="Review logs or use --skip-layer"
                )
                findings.append(error_finding)

                # Check if downstream layers depend on this one
                if self._has_dependent_layers(layer.layer_id):
                    self._skip_dependent_layers(layer.layer_id, findings)
                    break

        return Report(...)
```

---

## Output Rendering

### Annotated Markdown

**Strategy:** Clone original skill file, inject inline annotations at finding locations

**Annotation Format:**
```markdown
> 🔴 **CRITICAL: Methodological Ambiguity** (Layer 1: Ambiguity Scoring)
> **Issue:** [description]
> **Recommendation:** [recommendation]
> **Review Status:** Accepted
```

**Challenges:**
- Mapping finding locations ("step 3") to skill file structure
- Handling unmappable locations → placed in "Overall" section

---

### JSON

**Strategy:** Serialize Report object with full structure

**Use Cases:**
- CI/CD integration (fail build on critical findings)
- Batch analysis (aggregate findings across many skills)
- Programmatic filtering
- Prompt refinement (analyze dismissed findings)

---

## LLM Client

### Anthropic API Integration

```python
class AnthropicClient:
    MODEL_MAPPING = {
        "sonnet": "claude-sonnet-4-5-20250929",
        "opus": "claude-opus-4-5-20251101",
        "haiku": "claude-3-5-haiku-20241022"
    }

    def generate(self, prompt: str, max_tokens: int = 4000) -> str:
        """Call Claude API with retry logic"""
        # Exponential backoff for rate limits
        # Token tracking
        # Error handling
```

**Features:**
- Model name resolution (shortnames → full IDs)
- Retry logic with exponential backoff
- Token counting for cost tracking
- Timeout handling

---

## XML Response Parsing

### Why XML?

LLMs generate structured output more reliably with XML than JSON:
- Clear start/end tags
- Forgiving of formatting inconsistencies
- Natural for hierarchical data

### Challenges

**LLMs sometimes generate malformed XML:**
- Unescaped special characters (`&`, `<`, `>`)
- Mismatched opening/closing tags
- Invalid nesting

**Solution:**
```python
def clean_xml_response(xml_string: str) -> str:
    """Clean common XML issues before parsing"""
    # Escape unescaped ampersands
    xml_string = re.sub(r'&(?!(amp|lt|gt|quot|apos);)', '&amp;', xml_string)
    return xml_string
```

**Prompt Engineering:**
```
CRITICAL XML FORMATTING REQUIREMENTS:
- You MUST return valid, well-formed XML
- Every opening tag MUST have a matching closing tag
- All special characters MUST be escaped: & → &amp;, < → &lt;, > → &gt;
- Test your XML mentally before outputting
```

This dual approach (cleaning + prompting) reduced XML parse failures from ~30% to <5% in testing.

---

## Security Considerations

### API Key Handling
- Loaded from environment variable or `~/.crible/config`
- Config file permissions set to `0o600` (user read/write only)
- Never logged or printed
- Not passed in command-line arguments

### No Code Execution
- Crible performs **static analysis only**
- Never executes skill file code
- LLM responses parsed as data, not code
- No `eval()`, `exec()`, or similar dangerous operations

### Input Sanitization
- XML cleaning before parsing (prevents injection)
- File path validation (Click's `Path(exists=True)`)
- LLM responses treated as untrusted input

---

## Performance Characteristics

### Token Usage by Layer

Typical skill file (30 steps):
- **Layer 0:** ~2K-3K tokens (dependency extraction is quick)
- **Layer 1:** ~4K-6K tokens (ambiguity scoring)
- **Layer 2:** ~8K-12K tokens (execution trace is expensive)
- **Layer 3:** ~3K-5K tokens (domain constraints)

**Total:** ~17K-26K tokens per assessment

### Execution Time

With Claude Sonnet 4.5:
- Simple skill: 10-15 seconds
- Medium skill: 20-30 seconds
- Complex skill: 30-45 seconds

Bottleneck: API round-trip time (4 sequential LLM calls)

### Cost Optimization

**Reduce token usage:**
- Use `--skip-layer 2` (saves 40-50% of tokens)
- Use Haiku model (faster, cheaper, slight quality reduction)
- Break large skills into smaller modules

**Parallel processing (future):**
- Layers 0 and 1 are independent → could run in parallel
- Would reduce wall-clock time by ~30%

---

## Future Architecture Enhancements

### Layer 0 Validation (v2)
- Integrate with Bioconda/PyPI/CRAN APIs
- Real-time package existence checks
- Version availability verification
- URL validation (check if databases are accessible)

### Pluggable Prompts
- Domain-specific prompt libraries (proteomics, image analysis)
- Auto-detect domain from skill content
- Community-contributed prompt templates

### Caching Layer
- Cache LLM responses for identical inputs
- Reduces cost for repeated assessments
- Invalidate on skill file changes

### Parallel Layer Execution
- Run independent layers (0, 1) concurrently
- Reduces wall-clock time
- Increases API throughput requirements

---

## See Also

- [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) - Original implementation notes
- [PROJECT_LEARNINGS.md](PROJECT_LEARNINGS.md) - Development challenges and lessons learned
- [Anthropic API Documentation](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)

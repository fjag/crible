# Project Learnings

**Date:** March 2026
**Purpose:** This document captures key challenges, roadblocks, and learnings encountered during Crible's development from initial specification to current implementation. These insights may benefit others building LLM-powered static analysis tools.

---

## Key Challenges and Learnings

1. **Design Challenge: Layer 0 Validation Scope** — Initial specification proposed LLM-based package registry validation using training knowledge. Critical assessment revealed this would systematically fail (LLMs cannot validate package versions, deprecation status, or URL availability from memory). Reframed Layer 0 as dependency extraction only, deferring validation to future versions with live API integration.

2. **Cost Management: Context Accumulation** — Four-layer pipeline with full context passing would create exponential token costs. Implemented selective context passing with condensed summaries between layers, reducing cumulative context by ~60-70% while preserving essential information flow.

3. **Highest-Risk Component: Layer 2 Execution Trace** — Simulated execution tracing without code execution is ambitious and inherently uncertain. Mitigated by implementing confidence scoring (0.0-1.0) per traced step and dependency-aware error handling for downstream layers. Works well for linear workflows; struggles with complex branching.

4. **XML Parsing Robustness** — LLM responses contained malformed XML (unescaped special characters, mismatched tags). Solved with dual approach: (1) XML cleaning function to escape special characters post-generation, (2) Enhanced prompts with explicit XML formatting requirements and mental validation instructions.

5. **Variable Scope Bug** — Early implementation had imports inside try blocks but exception handlers referenced those imports, causing UnboundLocalError. Lesson: imports must be at module level, not conditional.

6. **Output Format Usability** — Initial stdout-only output was difficult to review. User feedback drove shift to file-based output by default with auto-generated filenames, plus dual format support (annotated markdown for humans, JSON for automation).

7. **Interactive Review UX** — First iteration lacked clear instructions and keyboard shortcuts. Iteratively improved with upfront instructions, single-letter shortcuts (a/d/n/s), color-coded confirmations, and comprehensive findings list with review decisions in final report.

8. **Prompt Engineering for Structure** — Reference documentation skills (many examples, variations) overwhelmed LLMs with enumeration requests. Added guidance to "summarize groups of similar steps" and "focus on workflow patterns" to prevent XML structure collapse from excessive detail.

9. **Fail-Forward Dependency Awareness** — Initial design allowed all layers to fail independently. Recognized Layer 3 depends critically on Layer 2's inferred data type. Implemented dependency-aware skipping: independent layers fail forward, dependent layers skip gracefully with clear messaging when prerequisites fail.

---

**Current Status:** All four layers operational with robust error handling. Known limitations documented transparently in README.

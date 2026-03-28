# Crible Quality Assessment Report

**Skill File:** examples/scrna_clustering.md  
**Assessment Date:** 2026-03-28 13:33:31  
**Model:** claude-sonnet-4-5-20250929  
**Total Findings:** 29 
(2 critical, 
11 warnings, 
16 info)

---

## Original Skill File with Annotations

# Single-Cell RNA-seq Clustering Workflow

This skill performs clustering analysis on single-cell RNA-seq data from 10x Genomics.

## Prerequisites

- Python 3.8+
- scanpy library
- Input: CellRanger output directory

## Steps


### Step 1: Load Data

Load the count matrix from the CellRanger output directory. The data should be in the standard 10x format.

```python
import scanpy as sc

adata = sc.read_10x_mtx('data/sample/')
```



> ℹ️ **INFO: Dependency Identified** (Layer 0: Dependency Extraction)
> **Issue:** Dependency identified: data/sample/. Type: file.
> **Recommendation:** CellRanger output directory in 10x format. Assumes pre-existing local directory. Cannot validate without filesystem access.
> ℹ️ **INFO: Scope Limitation** (Layer 3: Domain Constraints)
> **Issue:** Workflow hardcodes 10x Genomics-specific input format (sc.read_10x_mtx) and presents itself as general "Single-Cell RNA-seq Clustering Workflow" but only works with 10x CellRanger output.
> **Recommendation:** The skill title suggests general applicability to scRNA-seq data, but Step 1 specifically requires 10x Genomics CellRanger output format. This won't work with other platforms like Drop-seq, Smart-seq2, or inDrop without modification. The skill should either clarify it's 10x-specific in the title or provide platform-agnostic loading options.
> **Confidence:** 0.95

### Step 2: Quality Control

Filter out low-quality cells based on the number of genes detected per cell.

```python
sc.pp.filter_cells(adata, min_genes=200)
```


### Step 3: Normalize Data

Normalize the count matrix.

```python
sc.pp.normalize_total(adata)
sc.pp.log1p(adata)
```



> ⚠️ **WARNING: Methodological Mismatch** (Layer 3: Domain Constraints)
> **Issue:** Uses basic log-normalization (normalize_total + log1p) without scaling, which may be suboptimal for heterogeneous single-cell datasets with high variability.
> **Recommendation:** While normalize_total and log1p are valid for scRNA-seq, the workflow doesn't include sc.pp.scale() before PCA. For datasets with high technical variation or batch effects, this may lead to suboptimal dimensionality reduction. However, this is a methodological choice rather than a clear violation, and some workflows intentionally skip scaling. Flagging as warning-level since it may affect clustering quality in certain datasets.
> **Confidence:** 0.72

### Step 4: Feature Selection

Identify highly variable genes for downstream analysis.

```python
sc.pp.highly_variable_genes(adata, n_top_genes=2000)
adata = adata[:, adata.var.highly_variable]
```


### Step 5: Dimensionality Reduction

Perform PCA to reduce dimensionality.

```python
sc.tl.pca(adata)
```


### Step 6: Neighborhood Graph

Compute the neighborhood graph of cells.

```python
sc.pp.neighbors(adata, n_pcs=40)
```



> ℹ️ **INFO: Scope Limitation** (Layer 3: Domain Constraints)
> **Issue:** Hardcodes n_pcs=40 without validation that 40 PCs are appropriate for the dataset, which may not generalize across different data scales.
> **Recommendation:** Using 40 principal components is a reasonable default, but the workflow doesn't include any step to determine the optimal number of PCs (e.g., elbow plot analysis). For smaller datasets or those with less complexity, 40 PCs may include noise. For very complex datasets, it may be insufficient. This limits the workflow's general applicability.
> **Confidence:** 0.73

### Step 7: Clustering

Cluster cells using the Leiden algorithm.

```python
sc.tl.leiden(adata, resolution=0.5)
```



> ℹ️ **INFO: Scope Limitation** (Layer 3: Domain Constraints)
> **Issue:** Hardcodes resolution parameter (0.5) without guidance on adjustment, limiting applicability across different dataset sizes and biological contexts.
> **Recommendation:** The Leiden clustering resolution of 0.5 is presented as a fixed parameter. Optimal resolution varies significantly based on dataset size, cell type heterogeneity, and biological question. The workflow presents as general-purpose but this hardcoded value may produce too few or too many clusters for many datasets. Users should be guided to adjust this parameter.
> **Confidence:** 0.75

### Step 8: UMAP Visualization

Generate UMAP embedding for visualization.

```python
sc.tl.umap(adata)
sc.pl.umap(adata, color='leiden')
```


### Step 9: Marker Gene Identification

Find marker genes for each cluster using differential expression.

```python
sc.tl.rank_genes_groups(adata, 'leiden', method='wilcoxon')
```


### Step 10: Save Results

Save the annotated data object.

```python
adata.write('results/clustered_data.h5ad')
```

## Expected Output

- Clustered AnnData object with cell type assignments
- UMAP visualization
- Marker genes for each cluster

## Notes

This workflow assumes the input data is from human samples and uses standard parameters that work well for most 10x datasets.



> ℹ️ **INFO: Dependency Identified** (Layer 0: Dependency Extraction)
> **Issue:** Dependency identified: results/. Type: file.
> **Recommendation:** Output directory for saving results. Assumes pre-existing local directory or write permissions. Cannot validate without filesystem access.


---

## General Findings

> ℹ️ **INFO: Inferred Input** (Layer 2: Simulated Execution)
> **Issue:** Inferred input: scRNA-seq (single-cell RNA-seq) (10x Genomics CellRanger output directory containing matrix.mtx (sparse count matrix), barcodes.tsv (cell barcodes), features.tsv/genes.tsv (gene identifiers)), organism: human (stated in Notes section)
> **Recommendation:** Verify this matches your intended input. Scale: Not specified, but typical 10x datasets range 1,000-100,000 cells; workflow parameters suggest moderate scale (2000 HVGs, 40 PCs typical for 5,000-50,000 cells), Design: 10x Genomics platform, single-cell 3' or 5' gene expression, likely droplet-based
> **Confidence:** 0.95


---

## All Findings (Detailed)


Complete list of all findings with review decisions:


### 🔴 CRITICAL (2 findings)


#### 1. Methodological Ambiguity

- **Layer:** 1 - Ambiguity Scoring
- **Location:** Step 2: Quality Control
- **Issue:** Ambiguity level: HIGH. Plausible interpretations: 10+. Ambiguous aspects: Only filters on min_genes=200, but standard QC includes multiple metrics: max genes per cell (doublet detection), mitochondrial percentage threshold, minimum UMI counts, ribosomal gene percentage. Also unclear whether to filter genes by minimum cell expression. No specification of whether to remove genes before or after cell filtering.. Consequence: methodological - incomplete QC can retain doublets, dying cells with high mitochondrial content, or ambient RNA contamination, fundamentally affecting cluster composition and biological interpretation.
- **Recommendation:** Specify complete QC criteria: min_genes (e.g., 200), max_genes (e.g., 2500 or 3*MAD), max mitochondrial % (e.g., 5-20%), min_counts (e.g., 500), and gene filtering (e.g., min_cells=3). Include code to calculate and visualize QC metrics before filtering.
- **Review Decision:** Not reviewed


#### 2. Methodological Ambiguity

- **Layer:** 1 - Ambiguity Scoring
- **Location:** Overall workflow
- **Issue:** Ambiguity level: HIGH. Plausible interpretations: 10+. Ambiguous aspects: No batch correction mentioned despite being critical for multi-sample datasets. No cell cycle scoring/regression. No doublet detection step. No integration with external reference datasets. No cell type annotation strategy beyond manual marker inspection. Missing data provenance tracking (parameters, versions).. Consequence: methodological - batch effects can create false clusters. Doublets appear as spurious intermediate cell types. Without annotation guidance, cluster interpretation is subjective. Lack of reproducibility metadata..
- **Recommendation:** Add conditional steps for batch correction (e.g., Harmony, scVI, Combat) when multiple samples present. Include doublet detection (Scrublet, DoubletFinder). Add cell type annotation options (automated tools like CellTypist, SingleR, or manual marker-based). Include version logging and parameter documentation.
- **Review Decision:** Not reviewed


### ⚠️ WARNING (11 findings)


#### 1. Methodological Ambiguity

- **Layer:** 1 - Ambiguity Scoring
- **Location:** Step 3: Normalize Data
- **Issue:** Ambiguity level: MEDIUM. Plausible interpretations: 4. Ambiguous aspects: sc.pp.normalize_total() called without target_sum parameter - default is 1e4 but this is not explicit. Alternative normalization methods exist (SCTransform, Pearson residuals, scran pooling). Unclear if normalization should be done on all genes or only after filtering.. Consequence: methodological - different target sums and normalization methods affect variance structure and downstream clustering. Default behavior may not be optimal for all datasets (e.g., very sparse data)..
- **Recommendation:** Specify target_sum explicitly (e.g., target_sum=1e4) and justify choice. State whether using raw counts or normalized for highly variable gene selection. Consider mentioning when alternative methods like SCTransform might be preferred.
- **Review Decision:** Not reviewed


#### 2. Methodological Ambiguity

- **Layer:** 1 - Ambiguity Scoring
- **Location:** Step 4: Feature Selection
- **Issue:** Ambiguity level: MEDIUM. Plausible interpretations: 5. Ambiguous aspects: Method for highly variable gene selection not specified (default is 'seurat' but could be 'cell_ranger', 'seurat_v3', or 'seurat_v3_paper'). The flavor parameter affects results. n_top_genes=2000 is arbitrary without justification. Unclear if should subset data immediately or retain full matrix with .raw attribute for later use.. Consequence: methodological - different HVG methods identify different gene sets, affecting PCA and clustering. Subsetting immediately loses information for marker gene analysis and visualization of non-HVG genes..
- **Recommendation:** Specify flavor parameter explicitly (e.g., flavor='seurat'). Recommend storing full normalized data in adata.raw before subsetting. Justify n_top_genes choice or make it dataset-dependent (e.g., based on saturation analysis).
- **Review Decision:** Not reviewed


#### 3. Methodological Ambiguity

- **Layer:** 1 - Ambiguity Scoring
- **Location:** Step 5: Dimensionality Reduction
- **Issue:** Ambiguity level: MEDIUM. Plausible interpretations: 4. Ambiguous aspects: Number of PCs to compute not specified (default is 50). No scaling/regression step before PCA. Unclear if should regress out technical covariates (cell cycle, mitochondrial percentage, batch effects). No guidance on determining optimal number of PCs.. Consequence: methodological - unscaled data gives higher weight to highly expressed genes. Not regressing technical variation can create spurious clusters. Number of PCs affects downstream neighbor graph and clustering resolution..
- **Recommendation:** Add sc.pp.scale() before PCA with max_value parameter. Specify n_comps explicitly. Consider sc.pp.regress_out() for technical covariates if needed. Include elbow plot or variance ratio analysis to justify n_pcs choice in Step 6.
- **Review Decision:** Not reviewed


#### 4. Methodological Ambiguity

- **Layer:** 1 - Ambiguity Scoring
- **Location:** Step 6: Neighborhood Graph
- **Issue:** Ambiguity level: MEDIUM. Plausible interpretations: 5. Ambiguous aspects: n_pcs=40 specified but no justification provided and may not match PCA output. n_neighbors parameter not specified (default is 15). Distance metric not specified (default is 'euclidean'). Method not specified (default is 'umap' but could be 'gauss').. Consequence: methodological - n_neighbors critically affects cluster granularity. Too few neighbors creates fragmented clusters, too many over-smooths. n_pcs choice affects which variance is captured. Mismatch with PCA dimensions causes error or suboptimal use of variance..
- **Recommendation:** Justify n_pcs=40 with elbow plot or variance explained threshold (e.g., 80% variance). Specify n_neighbors explicitly with rationale (typically 10-30 depending on dataset size). Consider making parameters dataset-size dependent.
- **Review Decision:** Not reviewed


#### 5. Methodological Ambiguity

- **Layer:** 1 - Ambiguity Scoring
- **Location:** Step 7: Clustering
- **Issue:** Ambiguity level: MEDIUM. Plausible interpretations: 4. Ambiguous aspects: resolution=0.5 is arbitrary without justification. No guidance on choosing resolution for different dataset sizes or biological questions. Alternative clustering methods not mentioned (Louvain, hierarchical). No mention of clustering stability assessment or parameter sweep.. Consequence: methodological - resolution parameter critically determines cluster number and granularity. Wrong resolution can over-split or under-split biological cell types. Single resolution may miss hierarchical structure..
- **Recommendation:** Provide guidance on resolution selection (e.g., try range 0.3-1.5, evaluate with silhouette scores or stability metrics). Mention that optimal resolution depends on dataset size and biological context. Consider multi-resolution clustering or parameter sweep.
- **Review Decision:** Not reviewed


#### 6. Methodological Ambiguity

- **Layer:** 1 - Ambiguity Scoring
- **Location:** Step 9: Marker Gene Identification
- **Issue:** Ambiguity level: MEDIUM. Plausible interpretations: 5. Ambiguous aspects: Statistical test specified (wilcoxon) but no multiple testing correction method specified. No filtering criteria for significant markers (p-value, log fold change, percentage expressed). Comparison strategy not specified (one-vs-rest is default but could be one-vs-one). No specification of whether to use raw or normalized data.. Consequence: methodological - different tests have different power and assumptions. Without filtering criteria, results include non-significant or low-effect genes. Multiple testing correction affects false positive rate. Choice affects marker gene lists used for biological interpretation..
- **Recommendation:** Specify corr_method parameter (e.g., 'bonferroni' or 'benjamini-hochberg'). Add filtering step with thresholds (e.g., padj < 0.05, log2FC > 0.5, pct_expressed > 0.25). Clarify if using .raw data for DE testing. Consider alternative methods (t-test, logreg) for different scenarios.
- **Review Decision:** Not reviewed


#### 7. Execution Discrepancy

- **Layer:** 2 - Simulated Execution
- **Location:** Step 2: Quality Control
- **Issue:** Incomplete quality control. Only filters on min_genes=200 but lacks critical QC steps: (1) no filtering on mitochondrial gene percentage (high mt% indicates dying cells), (2) no max_genes threshold (doublets often have high gene counts), (3) no total counts filtering, (4) no gene filtering by min_cells. Standard workflows calculate QC metrics first with sc.pp.calculate_qc_metrics() before filtering.
- **Recommendation:** Review the data flow and ensure all dependencies are satisfied.
- **Confidence:** 0.90
- **Review Decision:** Not reviewed


#### 8. Execution Discrepancy

- **Layer:** 2 - Simulated Execution
- **Location:** Step 4: Feature Selection
- **Issue:** Subsetting to only highly variable genes (adata = adata[:, adata.var.highly_variable]) permanently removes 80-90% of genes. This prevents examination of non-variable genes as potential markers in Step 9. Best practice is to store full data in adata.raw before subsetting, which is not done here.
- **Recommendation:** Review the data flow and ensure all dependencies are satisfied.
- **Confidence:** 0.85
- **Review Decision:** Not reviewed


#### 9. Execution Discrepancy

- **Layer:** 2 - Simulated Execution
- **Location:** Step 5: Dimensionality Reduction
- **Issue:** No scaling step (sc.pp.scale()) before PCA. PCA is sensitive to gene-wise variance, and standard workflows scale genes to unit variance and zero mean. Without scaling, high-variance genes dominate principal components regardless of biological relevance.
- **Recommendation:** Review the data flow and ensure all dependencies are satisfied.
- **Confidence:** 0.80
- **Review Decision:** Not reviewed


#### 10. Execution Discrepancy

- **Layer:** 2 - Simulated Execution
- **Location:** Step 9: Marker Gene Identification
- **Issue:** Marker gene analysis operates on only the 2000 highly variable genes selected in Step 4. Many biologically relevant markers (e.g., lowly expressed transcription factors, cell-type specific genes with moderate variance) may have been excluded. Results are not saved to file or displayed.
- **Recommendation:** Review the data flow and ensure all dependencies are satisfied.
- **Confidence:** 0.80
- **Review Decision:** Not reviewed


#### 11. Methodological Mismatch

- **Layer:** 3 - Domain Constraints
- **Location:** Step 3
- **Issue:** Uses basic log-normalization (normalize_total + log1p) without scaling, which may be suboptimal for heterogeneous single-cell datasets with high variability.
- **Recommendation:** While normalize_total and log1p are valid for scRNA-seq, the workflow doesn't include sc.pp.scale() before PCA. For datasets with high technical variation or batch effects, this may lead to suboptimal dimensionality reduction. However, this is a methodological choice rather than a clear violation, and some workflows intentionally skip scaling. Flagging as warning-level since it may affect clustering quality in certain datasets.
- **Confidence:** 0.72
- **Review Decision:** Not reviewed


### ℹ️ INFO (16 findings)


#### 1. Dependency Identified

- **Layer:** 0 - Dependency Extraction
- **Location:** Prerequisites
- **Issue:** Dependency identified: Python (version 3.8+). Type: python_package.
- **Recommendation:** Validation requires live registry integration (not implemented)
- **Review Decision:** Not reviewed


#### 2. Dependency Identified

- **Layer:** 0 - Dependency Extraction
- **Location:** Prerequisites, Step 1
- **Issue:** Dependency identified: scanpy. Type: python_package.
- **Recommendation:** Validation requires live registry integration (not implemented)
- **Review Decision:** Not reviewed


#### 3. Dependency Identified

- **Layer:** 0 - Dependency Extraction
- **Location:** Prerequisites, Step 1
- **Issue:** Dependency identified: CellRanger. Type: tool.
- **Recommendation:** 10x Genomics tool for processing single-cell data. Validation requires live registry integration (not implemented)
- **Review Decision:** Not reviewed


#### 4. Dependency Identified

- **Layer:** 0 - Dependency Extraction
- **Location:** Step 1
- **Issue:** Dependency identified: data/sample/. Type: file.
- **Recommendation:** CellRanger output directory in 10x format. Assumes pre-existing local directory. Cannot validate without filesystem access.
- **Review Decision:** Not reviewed


#### 5. Dependency Identified

- **Layer:** 0 - Dependency Extraction
- **Location:** Step 10
- **Issue:** Dependency identified: results/. Type: file.
- **Recommendation:** Output directory for saving results. Assumes pre-existing local directory or write permissions. Cannot validate without filesystem access.
- **Review Decision:** Not reviewed


#### 6. Methodological Ambiguity

- **Layer:** 1 - Ambiguity Scoring
- **Location:** Step 8: UMAP Visualization
- **Issue:** Ambiguity level: LOW. Plausible interpretations: 2. Ambiguous aspects: UMAP parameters not specified (min_dist, spread, n_neighbors use defaults). Output format/saving not specified for the plot.. Consequence: cosmetic to minor methodological - UMAP is for visualization only and doesn't affect clustering, but different parameters change visual interpretation. Not saving plot is workflow incompleteness..
- **Recommendation:** Optionally specify UMAP parameters if non-default visualization needed. Add plot saving command (e.g., plt.savefig() or save parameter in sc.pl.umap()).
- **Review Decision:** Not reviewed


#### 7. Methodological Ambiguity

- **Layer:** 1 - Ambiguity Scoring
- **Location:** Step 10: Save Results
- **Issue:** Ambiguity level: LOW. Plausible interpretations: 2. Ambiguous aspects: Output directory 'results/' may not exist. No specification of compression. No export of marker gene tables or plots to separate files.. Consequence: cosmetic to minor - workflow may fail if directory doesn't exist, but easily fixed. Missing exports of tables/figures means incomplete output package..
- **Recommendation:** Add directory creation check. Optionally specify compression parameter. Add exports for marker gene tables (CSV/TSV) and key plots (PDF/PNG).
- **Review Decision:** Not reviewed


#### 8. Inferred Input

- **Layer:** 2 - Simulated Execution
- **Location:** overall
- **Issue:** Inferred input: scRNA-seq (single-cell RNA-seq) (10x Genomics CellRanger output directory containing matrix.mtx (sparse count matrix), barcodes.tsv (cell barcodes), features.tsv/genes.tsv (gene identifiers)), organism: human (stated in Notes section)
- **Recommendation:** Verify this matches your intended input. Scale: Not specified, but typical 10x datasets range 1,000-100,000 cells; workflow parameters suggest moderate scale (2000 HVGs, 40 PCs typical for 5,000-50,000 cells), Design: 10x Genomics platform, single-cell 3' or 5' gene expression, likely droplet-based
- **Confidence:** 0.95
- **Review Decision:** Not reviewed


#### 9. Execution Discrepancy

- **Layer:** 2 - Simulated Execution
- **Location:** Step 6: Neighborhood Graph
- **Issue:** Uses n_pcs=40 but Step 5 doesn't specify how many PCs were computed (default 50). If fewer than 40 PCs exist, this would cause an error. Also, no justification for using 40 vs 30 or 50 PCs.
- **Recommendation:** Review the data flow and ensure all dependencies are satisfied.
- **Confidence:** 0.70
- **Review Decision:** Not reviewed


#### 10. Execution Discrepancy

- **Layer:** 2 - Simulated Execution
- **Location:** Step 8: UMAP Visualization
- **Issue:** sc.pl.umap() generates a plot but the workflow doesn't specify whether it's displayed interactively or saved to file. The Expected Output section mentions 'UMAP visualization' but Step 10 only saves the .h5ad file, not the plot image.
- **Recommendation:** Review the data flow and ensure all dependencies are satisfied.
- **Confidence:** 0.75
- **Review Decision:** Not reviewed


#### 11. Execution Discrepancy

- **Layer:** 2 - Simulated Execution
- **Location:** Overall workflow
- **Issue:** Expected Output mentions 'cell type assignments' but the workflow only produces cluster numbers (leiden clusters), not biological cell type annotations. Cell type annotation would require additional steps comparing markers to known cell type signatures.
- **Recommendation:** Review the data flow and ensure all dependencies are satisfied.
- **Confidence:** 0.90
- **Review Decision:** Not reviewed


#### 12. Execution Discrepancy

- **Layer:** 2 - Simulated Execution
- **Location:** Step 3: Normalize Data
- **Issue:** normalize_total() target_sum parameter not specified (defaults to 1e4). Different values affect downstream analysis. Also, raw counts are overwritten and not preserved in adata.raw, making it impossible to re-normalize or access original counts later.
- **Recommendation:** Review the data flow and ensure all dependencies are satisfied.
- **Confidence:** 0.75
- **Review Decision:** Not reviewed


#### 13. Execution Discrepancy

- **Layer:** 2 - Simulated Execution
- **Location:** Overall workflow
- **Issue:** Notes section states 'assumes the input data is from human samples' but no human-specific operations are performed (e.g., no mitochondrial gene filtering using 'MT-' prefix, no cell cycle scoring with human genes). The workflow would work identically for mouse or other organisms.
- **Recommendation:** Review the data flow and ensure all dependencies are satisfied.
- **Confidence:** 0.65
- **Review Decision:** Not reviewed


#### 14. Scope Limitation

- **Layer:** 3 - Domain Constraints
- **Location:** Step 1
- **Issue:** Workflow hardcodes 10x Genomics-specific input format (sc.read_10x_mtx) and presents itself as general "Single-Cell RNA-seq Clustering Workflow" but only works with 10x CellRanger output.
- **Recommendation:** The skill title suggests general applicability to scRNA-seq data, but Step 1 specifically requires 10x Genomics CellRanger output format. This won't work with other platforms like Drop-seq, Smart-seq2, or inDrop without modification. The skill should either clarify it's 10x-specific in the title or provide platform-agnostic loading options.
- **Confidence:** 0.95
- **Review Decision:** Not reviewed


#### 15. Scope Limitation

- **Layer:** 3 - Domain Constraints
- **Location:** Step 7
- **Issue:** Hardcodes resolution parameter (0.5) without guidance on adjustment, limiting applicability across different dataset sizes and biological contexts.
- **Recommendation:** The Leiden clustering resolution of 0.5 is presented as a fixed parameter. Optimal resolution varies significantly based on dataset size, cell type heterogeneity, and biological question. The workflow presents as general-purpose but this hardcoded value may produce too few or too many clusters for many datasets. Users should be guided to adjust this parameter.
- **Confidence:** 0.75
- **Review Decision:** Not reviewed


#### 16. Scope Limitation

- **Layer:** 3 - Domain Constraints
- **Location:** Step 6
- **Issue:** Hardcodes n_pcs=40 without validation that 40 PCs are appropriate for the dataset, which may not generalize across different data scales.
- **Recommendation:** Using 40 principal components is a reasonable default, but the workflow doesn't include any step to determine the optimal number of PCs (e.g., elbow plot analysis). For smaller datasets or those with less complexity, 40 PCs may include noise. For very complex datasets, it may be insufficient. This limits the workflow's general applicability.
- **Confidence:** 0.73
- **Review Decision:** Not reviewed


---

## Assessment Summary

### Findings by Layer

**Layer 0 (Dependency Extraction):** 5 findings

**Layer 1 (Ambiguity Scoring):** 10 findings

**Layer 2 (Simulated Execution):** 10 findings

**Layer 3 (Domain Constraints):** 4 findings


### Findings by Severity

🔴 **CRITICAL:** 2

⚠️ **WARNING:** 11

ℹ️ **INFO:** 16


### Execution Metadata

- **Total Tokens:** 13746

- **Duration:** 134.8s

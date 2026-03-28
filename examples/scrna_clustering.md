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

### Step 7: Clustering

Cluster cells using the Leiden algorithm.

```python
sc.tl.leiden(adata, resolution=0.5)
```

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

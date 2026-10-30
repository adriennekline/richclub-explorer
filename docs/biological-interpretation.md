# Optional biological interpretation (experimental)

The **Biological Interpretation** tab is an opt-in companion to the core
network-science workflow. It does not change the graph, null ensemble, or
rich-club coefficient.

## Inputs

1. Run the usual rich-club analysis using **gene symbols as node IDs**.
2. Select a threshold with reliable node count.
3. Upload a CSV of **directed, signed, evidence-supported** regulator-target
   relationships, for example:

```csv
regulator,target,effect,confidence
C3,IL1B,1,0.8
C3,TNF,1,0.7
APP,IL1B,-1,0.6
```

Effect means the known regulator-to-target relationship: **1** activation,
**-1** inhibition, **0** unknown. This is NOT a STRING protein interaction
or a WGCNA coexpression correlation. Do not infer direction/sign from them.
Confidence is optional and must lie in [0, 1]. When omitted it defaults to
1 (unweighted evidence), which does not imply high biological certainty.

Optional disease-versus-control expression:

```csv
gene,log2_fold_change
IL1B,1.8
TNF,1.1
```

Organism, symbol naming and isoform mapping must be consistent across files.
No identifier normalization or orthology conversion is done automatically.

## Outputs

For each regulator, the module calculates:
- **Coverage**: fraction of selected rich-club genes with at least one direct
  matching relationship in the uploaded evidence.
- **Predicted reversal**: fraction of evaluable target genes for which a
  hypothetical activation or inhibition would oppose disease log2 fold-change,
  assuming each supplied signed relationship applies in the studied context.
  Ambiguous, unknown-direction, missing or unchanged genes are not evaluated.
- **Evidence**: average of maximum supplied confidence per target.
- **Score**: 0.55 * coverage + 0.30 * reversal + 0.15 * evidence, renormalized
  over available components if reversal is absent. These weights are illustrative,
  not experimentally calibrated or validated for clinical target ranking.

The hypothetical action maximizing observed reversal is selected for display.
No treatment feasibility, toxicity, off-target effects, in-vivo compensation,
cell-specificity, or pharmacokinetics are modeled.

This first iteration **does not yet connect to external databases**. Curated
data can be exported from databases with suitable usage rights and formatted
into the directed signed CSV. Database provenance, publications, evidence
types, dates, versions, and identifier mapping should be retained externally
until full provenance-aware adapters are added.

This implementation is intentionally narrower than Ingenuity Pathway Analysis
and cannot reproduce IPA's proprietary upstream-regulator predictions or
causal simulation.

## Reproducibility and scope

Exported rankings are exploratory. Record the original interaction file,
expression data, organism, threshold, null-model settings, and chosen scoring
weights. Relationship confidence values may be heterogeneous across sources:
do not mix uncalibrated scores without documenting their interpretation.

Next steps: OmniPath/SIGNOR evidence adapters, source provenance, identifier
harmonization, overrepresentation significance, bootstrapped stability, and
more defensible multi-criterion ranking.

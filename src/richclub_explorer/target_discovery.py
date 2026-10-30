"""Optional, transparent ranking of upstream regulators for rich-club genes.

All biological relationships are USER-PROVIDED, signed and directed. This module
does not infer causal direction from undirected STRING or co-expression edges.
"""
from __future__ import annotations

from collections.abc import Collection
import math

import pandas as pd


REQUIRED_EDGES = {"regulator", "target", "effect"}
REQUIRED_EXPRESSION = {"gene", "log2_fold_change"}


def _check_columns(data: pd.DataFrame, required: set[str], label: str) -> None:
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"{label} missing required columns: {', '.join(sorted(missing))}")


def rank_upstream_regulators(
    rich_genes: Collection[str],
    relationships: pd.DataFrame,
    expression: pd.DataFrame | None = None,
    *,
    weights: tuple[float, float, float] = (0.55, 0.30, 0.15),
) -> pd.DataFrame:
    """Rank upstream regulators by coverage, predicted reversal, and evidence.

    Parameters
    ----------
    rich_genes: RC gene identifiers matched exactly to the relationship table.
    relationships: regulator,target,effect (+ optional confidence in [0,1]).
      effect is +1 (activation), -1 (inhibition), or 0 (unknown direction).
    expression: optional gene,log2_fold_change of disease vs control.
    weights: coverage, directional reversal, evidence; must sum to one.

    Scores are heuristic exploratory prioritization, NOT causal validation.
    Direct coverage is computed only over the supplied rich-club genes.
    Unknown-direction edges are included in coverage but excluded from reversal.
    """
    _check_columns(relationships, REQUIRED_EDGES, "Relationships")
    if expression is not None:
        _check_columns(expression, REQUIRED_EXPRESSION, "Expression")
    if len(weights) != 3 or any(not math.isfinite(float(w)) or w < 0 for w in weights):
        raise ValueError("Weights must be three finite nonnegative numbers.")
    if not math.isclose(sum(weights), 1.0, abs_tol=1e-8):
        raise ValueError("Weights must sum to 1.")
    genes = {str(x).strip() for x in rich_genes if str(x).strip()}
    if not genes:
        raise ValueError("Select at least one rich-club gene.")

    rel = relationships.copy()
    for col in ("regulator", "target"):
        rel[col] = rel[col].astype("string").str.strip()
    rel = rel.dropna(subset=["regulator", "target"])
    rel = rel.loc[(rel["regulator"] != "") & (rel["target"] != "")]
    rel["effect"] = pd.to_numeric(rel["effect"], errors="coerce")
    if rel["effect"].isna().any() or not rel["effect"].isin([-1, 0, 1]).all():
        raise ValueError("effect must be -1, 0, or 1 (inhibition, unknown, activation).")
    if "confidence" not in rel.columns:
        rel["confidence"] = 1.0
    rel["confidence"] = pd.to_numeric(rel["confidence"], errors="coerce")
    if rel["confidence"].isna().any() or (~rel["confidence"].between(0, 1)).any():
        raise ValueError("confidence must be numeric and between 0 and 1.")
    rel = rel.loc[rel["target"].isin(genes)].drop_duplicates()
    if rel.empty:
        return pd.DataFrame(columns=[
            "regulator", "direct_targets", "coverage", "reversal_fraction",
            "directional_targets", "mean_confidence", "proposed_action",
            "score", "targets",
        ])

    fold_changes: dict[str, float] = {}
    if expression is not None:
        exp = expression.copy()
        exp["gene"] = exp["gene"].astype("string").str.strip()
        exp["log2_fold_change"] = pd.to_numeric(exp["log2_fold_change"], errors="coerce")
        if exp["gene"].duplicated().any():
            raise ValueError("Expression table must contain at most one row per gene.")
        if exp["log2_fold_change"].isna().any():
            raise ValueError("Expression log2_fold_change must be numeric.")
        fold_changes = dict(zip(exp["gene"], exp["log2_fold_change"]))

    out = []
    for regulator, group in rel.groupby("regulator", sort=True):
        targets = sorted(set(group["target"]))
        coverage = len(targets) / len(genes)
        confidence = float(group.groupby("target")["confidence"].max().mean())
        # Evaluate both hypothetical regulator perturbations; never assume either
        # is clinically or experimentally possible.
        direction = []
        for action in (-1, 1):
            votes: list[bool] = []
            for target, tgroup in group.groupby("target"):
                fc = fold_changes.get(target)
                signs = set(tgroup.loc[tgroup["effect"] != 0, "effect"])
                if fc is None or fc == 0 or len(signs) != 1:
                    continue  # missing data or contradictory/unknown effect
                expected = action * next(iter(signs))
                votes.append(expected * fc < 0)
            fraction = sum(votes) / len(votes) if votes else None
            direction.append((fraction, len(votes), action))
        evaluated = [entry for entry in direction if entry[0] is not None]
        if evaluated:
            # Prefer inhibition in a tie only for deterministic ordering.
            best = max(evaluated, key=lambda x: (x[0], -x[2]))
            reversal, directional_count, action = best
            action_label = "inhibit" if action == -1 else "activate"
        else:
            reversal, directional_count, action_label = None, 0, "unresolved"
        # Missing expression evidence is not treated as zero reversal.
        # Renormalize over available scoring dimensions.
        values = [(coverage, weights[0]), (confidence, weights[2])]
        if reversal is not None:
            values.append((reversal, weights[1]))
        score = sum(value * weight for value, weight in values) / sum(w for _, w in values)
        out.append({
            "regulator": str(regulator),
            "direct_targets": len(targets),
            "coverage": coverage,
            "reversal_fraction": reversal,
            "directional_targets": directional_count,
            "mean_confidence": confidence,
            "proposed_action": action_label,
            "score": score,
            "targets": "; ".join(targets),
        })
    return pd.DataFrame(out).sort_values(
        ["score", "direct_targets", "regulator"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

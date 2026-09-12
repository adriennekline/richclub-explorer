"""Observed and null-model rich-club analysis."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import networkx as nx
import numpy as np
import pandas as pd

from .validation import validate_network

Richness = Literal["degree", "strength"]


@dataclass(frozen=True)
class RichClubResult:
    """Tabular results plus the null ensemble and reproducibility metadata."""

    table: pd.DataFrame
    null_coefficients: np.ndarray
    parameters: dict[str, object]
    warnings: tuple[str, ...]


def _richness_values(graph: nx.Graph, richness: Richness) -> dict[object, float]:
    if richness == "degree":
        return {node: float(value) for node, value in graph.degree()}
    if richness == "strength":
        return {node: float(value) for node, value in graph.degree(weight="weight")}
    raise ValueError("richness must be 'degree' or 'strength'.")


def default_thresholds(graph: nx.Graph, richness: Richness = "degree") -> np.ndarray:
    """Return thresholds for which at least one richer node can remain."""

    values = np.asarray(list(_richness_values(graph, richness).values()), dtype=float)
    if richness == "degree":
        maximum = int(values.max(initial=0))
        return np.arange(0, maximum, dtype=float)
    unique = np.unique(values)
    return unique[:-1]


def rich_club_curve(
    graph: nx.Graph,
    thresholds: Sequence[float],
    *,
    richness: Richness = "degree",
    weighted: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calculate coefficients, rich-node counts, and rich-edge counts.

    Binary coefficients are edge density among nodes with richness greater
    than the threshold. Weighted coefficients use the Opsahl-style ratio of
    rich-edge weight to the same number of globally strongest edge weights.
    """

    scores = _richness_values(graph, richness)
    all_weights = sorted(
        (float(data.get("weight", 1.0)) for _, _, data in graph.edges(data=True)),
        reverse=True,
    )
    coefficients: list[float] = []
    node_counts: list[int] = []
    edge_counts: list[int] = []

    for threshold in thresholds:
        nodes = [node for node, score in scores.items() if score > threshold]
        subgraph = graph.subgraph(nodes)
        n_rich = subgraph.number_of_nodes()
        e_rich = subgraph.number_of_edges()
        node_counts.append(n_rich)
        edge_counts.append(e_rich)
        if n_rich < 2:
            coefficients.append(np.nan)
        elif weighted:
            denominator = float(sum(all_weights[:e_rich]))
            numerator = float(
                sum(float(data.get("weight", 1.0)) for _, _, data in subgraph.edges(data=True))
            )
            coefficients.append(numerator / denominator if denominator > 0 else np.nan)
        else:
            coefficients.append((2.0 * e_rich) / (n_rich * (n_rich - 1)))
    return np.asarray(coefficients), np.asarray(node_counts), np.asarray(edge_counts)


def _degree_preserving_null(
    graph: nx.Graph,
    *,
    rng: np.random.Generator,
    swaps_per_edge: int,
    weighted: bool,
) -> nx.Graph:
    topology = nx.Graph()
    topology.add_nodes_from(graph.nodes())
    topology.add_edges_from(graph.edges())
    nswap = int(swaps_per_edge * topology.number_of_edges())
    if topology.number_of_nodes() >= 4 and topology.number_of_edges() >= 2 and nswap > 0:
        try:
            nx.double_edge_swap(
                topology,
                nswap=nswap,
                max_tries=max(100, nswap * 20),
                seed=int(rng.integers(0, 2**32 - 1)),
            )
        except nx.NetworkXAlgorithmError:
            # The partially rewired graph still preserves the degree sequence.
            pass
    if weighted:
        weights = np.asarray(
            [float(data.get("weight", 1.0)) for _, _, data in graph.edges(data=True)]
        )
        rng.shuffle(weights)
        for (u, v), weight in zip(topology.edges(), weights, strict=True):
            topology[u][v]["weight"] = float(weight)
    return topology


def _benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    adjusted = np.full_like(p_values, np.nan, dtype=float)
    finite = np.flatnonzero(np.isfinite(p_values))
    if finite.size == 0:
        return adjusted
    order = finite[np.argsort(p_values[finite])]
    ranked = p_values[order] * finite.size / np.arange(1, finite.size + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    adjusted[order] = np.minimum(ranked, 1.0)
    return adjusted


def analyze(
    graph: nx.Graph,
    *,
    richness: Richness = "degree",
    weighted: bool = False,
    n_random: int = 100,
    swaps_per_edge: int = 10,
    seed: int = 42,
    min_rich_nodes: int = 5,
) -> RichClubResult:
    """Compare an observed rich-club curve with a null-network ensemble."""

    if n_random < 1:
        raise ValueError("n_random must be at least 1.")
    if swaps_per_edge < 0:
        raise ValueError("swaps_per_edge cannot be negative.")
    if richness == "strength" and not weighted:
        raise ValueError("Strength-based richness requires weighted=True.")

    validation = validate_network(graph, weighted=weighted)
    clean = validation.graph
    thresholds = default_thresholds(clean, richness)
    observed, node_counts, edge_counts = rich_club_curve(
        clean, thresholds, richness=richness, weighted=weighted
    )

    rng = np.random.default_rng(seed)
    nulls = np.full((n_random, len(thresholds)), np.nan, dtype=float)
    for index in range(n_random):
        null_graph = _degree_preserving_null(
            clean,
            rng=rng,
            swaps_per_edge=swaps_per_edge,
            weighted=weighted,
        )
        nulls[index], _, _ = rich_club_curve(
            null_graph, thresholds, richness=richness, weighted=weighted
        )

    null_mean = np.full(len(thresholds), np.nan)
    lower = np.full(len(thresholds), np.nan)
    upper = np.full(len(thresholds), np.nan)
    for index in range(len(thresholds)):
        finite_nulls = nulls[:, index][np.isfinite(nulls[:, index])]
        if finite_nulls.size:
            null_mean[index] = float(np.mean(finite_nulls))
            lower[index], upper[index] = np.quantile(finite_nulls, [0.025, 0.975])
    with np.errstate(invalid="ignore", divide="ignore"):
        rho = observed / null_mean

    p_values = np.full(len(thresholds), np.nan)
    for index, value in enumerate(observed):
        valid_nulls = nulls[:, index][np.isfinite(nulls[:, index])]
        if np.isfinite(value) and valid_nulls.size:
            p_values[index] = (1 + np.sum(valid_nulls >= value)) / (valid_nulls.size + 1)
    q_values = _benjamini_hochberg(p_values)
    reliable = node_counts >= min_rich_nodes

    table = pd.DataFrame(
        {
            "threshold": thresholds,
            "n_rich_nodes": node_counts,
            "n_rich_edges": edge_counts,
            "phi_observed": observed,
            "phi_null_mean": null_mean,
            "phi_null_lower_95": lower,
            "phi_null_upper_95": upper,
            "rho": rho,
            "p_empirical": p_values,
            "q_bh": q_values,
            "reliable_node_count": reliable,
        }
    )
    table["exploratory_signal"] = (
        (table["rho"] > 1)
        & (table["p_empirical"] < 0.05)
        & table["reliable_node_count"]
    )

    warnings = list(validation.warnings)
    if weighted:
        warnings.append(
            "Weighted nulls preserve degree sequence and the global weight distribution, "
            "but not each node's strength. Treat weighted inference as exploratory."
        )
    if n_random < 1000:
        warnings.append(
            "Fewer than 1,000 null networks were used. Increase n_random for final inference."
        )

    parameters: dict[str, object] = {
        "richness": richness,
        "weighted": weighted,
        "n_random": n_random,
        "swaps_per_edge": swaps_per_edge,
        "seed": seed,
        "min_rich_nodes": min_rich_nodes,
        **validation.summary,
    }
    return RichClubResult(table, nulls, parameters, tuple(warnings))

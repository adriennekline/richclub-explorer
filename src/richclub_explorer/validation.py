"""Network validation and transparent, minimal preprocessing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import networkx as nx
import numpy as np


class NetworkValidationError(ValueError):
    """Raised when a network cannot be analyzed safely."""


@dataclass(frozen=True)
class ValidationReport:
    """Validated graph, descriptive summary, and non-fatal warnings."""

    graph: nx.Graph
    summary: dict[str, Any]
    warnings: tuple[str, ...]


def validate_network(graph: nx.Graph, *, weighted: bool = False) -> ValidationReport:
    """Validate an undirected simple graph for rich-club analysis.

    Self-loops are removed from a copy and reported. Other potentially
    consequential transformations are never performed silently.
    """

    if graph.is_directed():
        raise NetworkValidationError(
            "Version 0.1 supports undirected networks only. Convert a directed "
            "network using a scientifically justified rule before analysis."
        )
    if graph.is_multigraph():
        raise NetworkValidationError(
            "Parallel edges were detected. Aggregate them explicitly before analysis."
        )

    clean = nx.Graph(graph)
    warnings: list[str] = []
    loops = list(nx.selfloop_edges(clean))
    if loops:
        clean.remove_edges_from(loops)
        warnings.append(f"Removed {len(loops)} self-loop(s); rich-club statistics exclude loops.")

    if clean.number_of_nodes() < 3:
        raise NetworkValidationError("At least three nodes are required.")
    if clean.number_of_edges() == 0:
        raise NetworkValidationError("The network contains no analyzable edges.")

    if weighted:
        for u, v, data in clean.edges(data=True):
            value = data.get("weight", 1.0)
            try:
                weight = float(value)
            except (TypeError, ValueError) as exc:
                raise NetworkValidationError(f"Edge ({u!r}, {v!r}) has a non-numeric weight.") from exc
            if not np.isfinite(weight):
                raise NetworkValidationError(f"Edge ({u!r}, {v!r}) has a non-finite weight.")
            if weight < 0:
                raise NetworkValidationError(
                    "Weighted analysis currently requires non-negative edge weights."
                )
            data["weight"] = weight

    components = nx.number_connected_components(clean)
    isolates = list(nx.isolates(clean))
    if components > 1:
        warnings.append(
            f"The network has {components} connected components. Results describe the full network."
        )
    if isolates:
        warnings.append(f"The network contains {len(isolates)} isolate(s).")

    n = clean.number_of_nodes()
    m = clean.number_of_edges()
    summary = {
        "nodes": n,
        "edges": m,
        "density": nx.density(clean),
        "components": components,
        "isolates": len(isolates),
        "weighted": weighted,
        "mean_degree": (2.0 * m / n),
    }
    return ValidationReport(clean, summary, tuple(warnings))

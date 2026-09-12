"""Rich-club membership and edge-role classification."""

from __future__ import annotations

from typing import Literal

import networkx as nx
import pandas as pd


def rich_nodes(
    graph: nx.Graph,
    threshold: float,
    *,
    richness: Literal["degree", "strength"] = "degree",
) -> set[object]:
    """Return nodes whose richness is strictly greater than a threshold."""

    weight = "weight" if richness == "strength" else None
    return {node for node, score in graph.degree(weight=weight) if float(score) > threshold}


def classify_edges(
    graph: nx.Graph,
    threshold: float,
    *,
    richness: Literal["degree", "strength"] = "degree",
) -> pd.DataFrame:
    """Classify edges as rich-club, feeder, or local."""

    members = rich_nodes(graph, threshold, richness=richness)
    records: list[dict[str, object]] = []
    for u, v, data in graph.edges(data=True):
        u_rich, v_rich = u in members, v in members
        role = "rich-club" if u_rich and v_rich else "feeder" if u_rich or v_rich else "local"
        records.append(
            {
                "source": u,
                "target": v,
                "weight": float(data.get("weight", 1.0)),
                "edge_class": role,
            }
        )
    return pd.DataFrame.from_records(records)

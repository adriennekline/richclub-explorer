"""Input helpers for common scientific network tables."""

from __future__ import annotations

from pathlib import Path
from typing import IO, Any

import networkx as nx
import numpy as np
import pandas as pd

TableSource = str | Path | IO[Any]


def _read_table(source: TableSource) -> pd.DataFrame:
    return pd.read_csv(source, sep=None, engine="python")


def load_edge_list(
    source: TableSource,
    *,
    source_col: str = "source",
    target_col: str = "target",
    weight_col: str | None = "weight",
) -> nx.Graph:
    """Load an undirected edge list from CSV or TSV.

    The source and target columns are required. A missing weight column is
    interpreted as a binary network.
    """

    table = _read_table(source)
    missing = [column for column in (source_col, target_col) if column not in table.columns]
    if missing:
        raise ValueError(f"Missing required edge-list column(s): {', '.join(missing)}")
    if table[[source_col, target_col]].isna().any().any():
        raise ValueError("Source and target columns cannot contain missing values.")

    graph = nx.Graph()
    has_weight = weight_col is not None and weight_col in table.columns
    for row in table.itertuples(index=False, name=None):
        record = dict(zip(table.columns, row, strict=True))
        u, v = record[source_col], record[target_col]
        if graph.has_edge(u, v):
            raise ValueError(
                f"Duplicate undirected edge detected: ({u!r}, {v!r}). "
                "Aggregate duplicate measurements explicitly."
            )
        if has_weight:
            graph.add_edge(u, v, weight=float(record[weight_col]))
        else:
            graph.add_edge(u, v)
    return graph


def load_adjacency_matrix(source: TableSource, *, weighted: bool = False) -> nx.Graph:
    """Load a square, symmetric adjacency matrix with row labels in column one."""

    table = pd.read_csv(source, index_col=0)
    if table.shape[0] != table.shape[1]:
        raise ValueError("The adjacency matrix must be square.")
    if set(map(str, table.index)) != set(map(str, table.columns)):
        raise ValueError("Adjacency-matrix row and column labels must match.")
    table.index = table.index.map(str)
    table.columns = table.columns.map(str)
    table = table.loc[table.columns, table.columns]
    values = table.to_numpy(dtype=float)
    if not np.all(np.isfinite(values)):
        raise ValueError("The adjacency matrix contains missing or non-finite values.")
    if not np.allclose(values, values.T):
        raise ValueError("Version 0.1 requires a symmetric adjacency matrix.")
    if not np.allclose(np.diag(values), 0):
        raise ValueError("The adjacency-matrix diagonal must be zero.")

    if not weighted:
        values = (values != 0).astype(int)
    graph = nx.from_numpy_array(values, create_using=nx.Graph, edge_attr="weight")
    return nx.relabel_nodes(graph, dict(enumerate(table.columns)))

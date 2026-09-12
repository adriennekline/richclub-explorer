from io import StringIO

import networkx as nx
import pytest

from richclub_explorer import NetworkValidationError, load_adjacency_matrix, load_edge_list
from richclub_explorer.validation import validate_network


def test_edge_list_loader_supports_weights():
    graph = load_edge_list(StringIO("source,target,weight\nA,B,2.5\nB,C,1.0\n"))
    assert graph["A"]["B"]["weight"] == 2.5


def test_duplicate_edge_is_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        load_edge_list(StringIO("source,target\nA,B\nB,A\n"), weight_col=None)


def test_adjacency_loader_preserves_labels():
    text = ",A,B,C\nA,0,1,0\nB,1,0,1\nC,0,1,0\n"
    graph = load_adjacency_matrix(StringIO(text))
    assert set(graph.nodes) == {"A", "B", "C"}
    assert set(map(frozenset, graph.edges)) == {frozenset(("A", "B")), frozenset(("B", "C"))}


def test_directed_network_is_rejected():
    with pytest.raises(NetworkValidationError, match="undirected"):
        validate_network(nx.DiGraph([(0, 1), (1, 2)]))


def test_self_loops_are_removed_and_reported():
    graph = nx.Graph([(0, 0), (0, 1), (1, 2)])
    report = validate_network(graph)
    assert not list(nx.selfloop_edges(report.graph))
    assert "self-loop" in report.warnings[0]

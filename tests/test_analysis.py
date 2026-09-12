import networkx as nx
import numpy as np

from richclub_explorer import analyze, classify_edges, rich_club_curve, rich_nodes


def test_clique_has_unit_binary_coefficient():
    graph = nx.complete_graph(6)
    coefficients, nodes, edges = rich_club_curve(graph, [0, 4], weighted=False)
    assert np.allclose(coefficients, [1.0, 1.0])
    assert nodes.tolist() == [6, 6]
    assert edges.tolist() == [15, 15]


def test_analysis_is_reproducible():
    graph = nx.karate_club_graph()
    first = analyze(graph, n_random=8, swaps_per_edge=2, seed=7)
    second = analyze(graph, n_random=8, swaps_per_edge=2, seed=7)
    assert np.allclose(first.null_coefficients, second.null_coefficients, equal_nan=True)
    assert first.table.equals(second.table)


def test_empirical_p_values_use_plus_one_correction():
    result = analyze(nx.karate_club_graph(), n_random=9, swaps_per_edge=1, seed=2)
    finite = result.table["p_empirical"].dropna()
    assert (finite >= 0.1).all()
    assert (finite <= 1.0).all()


def test_membership_and_edge_classes():
    graph = nx.Graph([(0, 1), (0, 2), (1, 2), (2, 3)])
    members = rich_nodes(graph, 2)
    assert members == {2}
    classes = classify_edges(graph, 2).set_index(["source", "target"])["edge_class"]
    assert (classes == "feeder").sum() == 3
    assert (classes == "local").sum() == 1

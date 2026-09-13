"""Point-and-click interface for RichClub Explorer."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import networkx as nx
import pandas as pd
import streamlit as st

from richclub_explorer import (
    analyze,
    classify_edges,
    load_adjacency_matrix,
    load_edge_list,
    rich_nodes,
)
from richclub_explorer.plotting import plot_result
from richclub_explorer.reporting import methods_paragraph
from richclub_explorer.validation import NetworkValidationError, validate_network

st.set_page_config(page_title="RichClub Explorer", page_icon="🔬", layout="wide")
logo_path = Path(__file__).resolve().parents[1] / "assets" / "node_diagram.png"

header_logo_col, _ = st.columns([1, 8])
with header_logo_col:
    if logo_path.exists():
        st.image(str(logo_path), width=120)

st.title("RichClub Explorer")
st.caption(
    "Reproducible detection, characterization, and reporting of rich-club organization "
    "in scientific networks."
)


def example_graph() -> nx.Graph:
    graph = nx.karate_club_graph()
    return nx.relabel_nodes(graph, {node: f"node_{node + 1}" for node in graph.nodes})


def read_uploaded_graph(uploaded_file, table_format: str, weighted: bool) -> nx.Graph:
    raw = BytesIO(uploaded_file.getvalue())
    if table_format == "Edge list":
        return load_edge_list(raw, weight_col="weight" if weighted else None)
    return load_adjacency_matrix(raw, weighted=weighted)


with st.sidebar:
    st.header("1. Network")
    data_source = st.radio("Data source", ["Example network", "Upload CSV/TSV"])
    table_format = st.selectbox("Uploaded format", ["Edge list", "Adjacency matrix"])
    uploaded = None
    if data_source == "Upload CSV/TSV":
        uploaded = st.file_uploader("Choose a network table", type=["csv", "tsv", "txt"])
        st.caption("Edge lists require `source` and `target`; `weight` is optional.")

    st.header("2. Analysis")
    weighted = st.checkbox("Weighted analysis", value=False)
    richness = st.selectbox(
        "Richness measure",
        ["degree", "strength"] if weighted else ["degree"],
    )
    n_random = st.select_slider(
        "Null networks",
        options=[10, 25, 50, 100, 250, 500, 1000],
        value=100,
        help="Use 1,000 for final inference; smaller ensembles are useful for exploration.",
    )
    swaps_per_edge = st.slider("Attempted swaps per edge", 1, 25, 10)
    min_rich_nodes = st.slider("Minimum rich nodes", 3, 20, 5)
    seed = st.number_input("Random seed", min_value=0, value=42, step=1)
    run = st.button("Run rich-club analysis", type="primary", width="stretch")


if run:
    try:
        if data_source == "Example network":
            graph = example_graph()
        elif uploaded is None:
            st.warning("Upload a network table before running the analysis.")
            st.stop()
        else:
            graph = read_uploaded_graph(uploaded, table_format, weighted)

        with st.spinner(f"Generating {n_random} null networks…"):
            result = analyze(
                graph,
                richness=richness,
                weighted=weighted,
                n_random=n_random,
                swaps_per_edge=swaps_per_edge,
                seed=int(seed),
                min_rich_nodes=min_rich_nodes,
            )
        st.session_state["analysis_graph"] = graph
        st.session_state["analysis_result"] = result
    except (ValueError, NetworkValidationError) as exc:
        st.error(str(exc))


if "analysis_result" not in st.session_state:
    st.info("Choose a network and run the analysis. The built-in example is ready to use.")
    st.markdown(
        """
        **What this application reports**

        - The observed rich-club coefficient across richness thresholds
        - A degree-preserving null distribution and 95% null envelope
        - Normalized coefficients and empirical one-sided p-values
        - Rich-club membership plus rich-club, feeder, and local edges
        - Downloadable tables, figures, settings, and editable Methods text
        """
    )
    st.stop()


result = st.session_state["analysis_result"]
graph = st.session_state["analysis_graph"]
summary = validate_network(graph, weighted=bool(result.parameters["weighted"])).summary

cols = st.columns(5)
cols[0].metric("Nodes", f"{summary['nodes']:,}")
cols[1].metric("Edges", f"{summary['edges']:,}")
cols[2].metric("Density", f"{summary['density']:.3f}")
cols[3].metric("Components", summary["components"])
cols[4].metric("Null networks", result.parameters["n_random"])

for warning in result.warnings:
    st.warning(warning)

figure = plot_result(result)
st.pyplot(figure, width="content")
st.caption(
    "A normalized coefficient above one is not sufficient by itself. Interpret it with "
    "the null distribution, retained node count, threshold dependence, and domain context."
)

st.subheader("Threshold-level results")
st.dataframe(result.table, width="stretch", hide_index=True)

eligible = result.table.loc[result.table["reliable_node_count"], "threshold"].tolist()
if eligible:
    st.subheader("Membership and edge roles")
    threshold = st.selectbox("Inspect threshold", eligible, index=max(0, len(eligible) // 2))
    members = rich_nodes(graph, threshold, richness=result.parameters["richness"])
    degree_weight = "weight" if result.parameters["richness"] == "strength" else None
    node_table = pd.DataFrame(
        [
            {
                "node": node,
                "richness": float(graph.degree(node, weight=degree_weight)),
                "rich_club_member": node in members,
            }
            for node in graph.nodes
        ]
    ).sort_values(["rich_club_member", "richness"], ascending=[False, False])
    edge_table = classify_edges(graph, threshold, richness=result.parameters["richness"])
    left, right = st.columns(2)
    left.dataframe(node_table, width="stretch", hide_index=True)
    right.dataframe(edge_table, width="stretch", hide_index=True)

    left.download_button(
        "Download node membership CSV",
        node_table.to_csv(index=False),
        "richclub_nodes.csv",
        "text/csv",
        width="stretch",
    )
    right.download_button(
        "Download edge classification CSV",
        edge_table.to_csv(index=False),
        "richclub_edges.csv",
        "text/csv",
        width="stretch",
    )

st.subheader("Reproducible export")
methods = methods_paragraph(result)
st.text_area("Generated Methods text", methods, height=170)

image_buffer = BytesIO()
figure.savefig(image_buffer, format="svg", bbox_inches="tight")
download_cols = st.columns(3)
download_cols[0].download_button(
    "Download all thresholds",
    result.table.to_csv(index=False),
    "richclub_results.csv",
    "text/csv",
    width="stretch",
)
download_cols[1].download_button(
    "Download SVG figure",
    image_buffer.getvalue(),
    "richclub_figure.svg",
    "image/svg+xml",
    width="stretch",
)
download_cols[2].download_button(
    "Download Methods text",
    methods,
    "richclub_methods.txt",
    "text/plain",
    width="stretch",
)

st.divider()
st.caption(
    "RichClub Explorer v0.1.0 · Research software in beta · Results require scientific "
    "interpretation and sensitivity analysis."
)

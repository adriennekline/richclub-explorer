"""Point-and-click interface for RichClub Explorer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

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

logo_path = Path(__file__).resolve().parents[1] / "assets" / "richclub_explorer_icon.svg"
page_icon = str(logo_path) if logo_path.exists() else "🔬"
st.set_page_config(page_title="RichClub Explorer", page_icon=page_icon, layout="wide")

if logo_path.exists():
    title_col_icon, title_col_text = st.columns([0.08, 0.92], gap="small", vertical_alignment="center")
    title_col_icon.image(str(logo_path), width=46)
    title_col_text.title("RichClub Explorer")
else:
    st.title("RichClub Explorer")
st.caption(
    "Reproducible detection, characterization, and reporting of rich-club organization "
    "in scientific networks."
)

st.markdown(
    """
    <style>
    .stTabs [data-baseweb="tab-list"],
    .stTabs div[role="tablist"],
    div[role="tablist"] {
        gap: 0.45rem !important;
        background: transparent !important;
        border-bottom: 0 !important;
        padding: 0.2rem 0 0 0 !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        overflow: visible !important;
    }
    .stTabs [data-baseweb="tab"],
    .stTabs button[role="tab"],
    .stTabs [data-testid="stTab"],
    [data-testid="stTab"][role="tab"] {
        position: relative !important;
        top: 0 !important;
        height: auto !important;
        font-size: 1.04rem !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
        padding: 0.58rem 0.75rem 0.54rem 0.75rem !important;
        border: 1px solid #d4d4d8 !important;
        border-bottom: 0 !important;
        border-radius: 0.62rem 0.62rem 0 0 !important;
        background: #f8fafc !important;
        color: #374151 !important;
        opacity: 1 !important;
        box-shadow: none !important;
        transition: background 140ms ease, color 140ms ease, border-color 140ms ease !important;
        flex: 1 1 0 !important;
        min-width: 0 !important;
        justify-content: center !important;
    }
    .stTabs [data-baseweb="tab"] p,
    .stTabs button[role="tab"] p,
    .stTabs [data-testid="stTab"] p,
    [data-testid="stTab"][role="tab"] p {
        font-size: 1.04rem !important;
        font-weight: 700 !important;
        color: #374151 !important;
        opacity: 1 !important;
        margin: 0 !important;
    }
    .stTabs [data-baseweb="tab"]:hover,
    .stTabs button[role="tab"]:hover,
    .stTabs [data-testid="stTab"]:hover,
    [data-testid="stTab"][role="tab"]:hover {
        color: #111827 !important;
        background: #f1f5f9 !important;
        border-color: #a1a1aa !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"],
    .stTabs button[role="tab"][aria-selected="true"],
    .stTabs [data-testid="stTab"][aria-selected="true"],
    [data-testid="stTab"][role="tab"][aria-selected="true"] {
        background: #6d28d9 !important;
        color: #ffffff !important;
        opacity: 1 !important;
        border-color: #6d28d9 !important;
        box-shadow: 0 2px 8px rgba(109, 40, 217, 0.28) !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] p,
    .stTabs button[role="tab"][aria-selected="true"] p,
    .stTabs [data-testid="stTab"][aria-selected="true"] p,
    [data-testid="stTab"][role="tab"][aria-selected="true"] p {
        color: #ffffff !important;
        opacity: 1 !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"]::after,
    .stTabs button[role="tab"][aria-selected="true"]::after {
        content: none !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        border: 1px solid #e5e7eb !important;
        border-top: 0 !important;
        border-radius: 0 0.65rem 0.65rem 0.65rem !important;
        padding: 1rem 0.9rem 0.8rem 0.9rem !important;
        background: #ffffff !important;
    }
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-testid="stTabsTabHighlight"] {
        display: none !important;
        height: 0 !important;
    }
    .stTabs [data-testid="stTabsScrollRight"],
    .stTabs [data-testid="stTabsScrollLeft"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def example_graph() -> nx.Graph:
    graph = nx.karate_club_graph()
    return nx.relabel_nodes(graph, {node: f"node_{node + 1}" for node in graph.nodes})


def read_uploaded_graph(uploaded_file, table_format: str, weighted: bool) -> nx.Graph:
    raw = BytesIO(uploaded_file.getvalue())
    if table_format == "Edge list":
        return load_edge_list(raw, weight_col="weight" if weighted else None)
    return load_adjacency_matrix(raw, weighted=weighted)


def result_figure_svg(figure) -> bytes:
    image_buffer = BytesIO()
    figure.savefig(image_buffer, format="svg", bbox_inches="tight")
    return image_buffer.getvalue()


def to_csv_string(frame: pd.DataFrame) -> str:
    return frame.to_csv(index=False)


def settings_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


with st.sidebar:
    st.header("Analysis Control Panel")
    with st.form("analysis_controls"):
        st.subheader("Data Input")
        data_source = st.radio("Data source", ["Example network", "Upload CSV/TSV"])
        table_format = st.selectbox("Uploaded format", ["Edge list", "Adjacency matrix"])
        uploaded = None
        if data_source == "Upload CSV/TSV":
            uploaded = st.file_uploader("Choose a network table", type=["csv", "tsv", "txt"])
            st.caption("Edge lists require `source` and `target`; `weight` is optional.")

        st.subheader("Analysis Parameters")
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
        st.subheader("Plot Appearance")
        color_cols = st.columns(2)
        observed_color = color_cols[0].color_picker("Observed and rho", "#1F6F78")
        signal_color = color_cols[1].color_picker("Exploratory signal", "#C84A5A")
        null_cols = st.columns(2)
        null_mean_color = null_cols[0].color_picker("Null mean", "#6B5B95")
        null_envelope_color = null_cols[1].color_picker("Null envelope", "#B7A7D2")

        run_disabled = data_source == "Upload CSV/TSV" and uploaded is None
        if run_disabled:
            st.caption("Upload a file to enable analysis.")

        run = st.form_submit_button(
            "Run rich-club analysis",
            type="primary",
            width="stretch",
            disabled=run_disabled,
        )
        reset = st.form_submit_button("Clear current results", width="stretch")

if reset:
    st.session_state.pop("analysis_graph", None)
    st.session_state.pop("analysis_result", None)
    st.session_state.pop("analysis_context", None)
    st.rerun()


if run:
    try:
        if data_source == "Example network":
            graph = example_graph()
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
        st.session_state["analysis_context"] = {
            "run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "data_source": data_source,
            "uploaded_file": uploaded.name if uploaded is not None else None,
            "uploaded_format": table_format if uploaded is not None else None,
            "settings": {
                "weighted": weighted,
                "richness": richness,
                "n_random": n_random,
                "swaps_per_edge": swaps_per_edge,
                "min_rich_nodes": min_rich_nodes,
                "seed": int(seed),
            },
            "plot_colors": {
                "observed_color": observed_color,
                "signal_color": signal_color,
                "null_mean_color": null_mean_color,
                "null_envelope_color": null_envelope_color,
            },
        }
    except (ValueError, NetworkValidationError) as exc:
        st.error(str(exc))
    except Exception as exc:  # noqa: BLE001
        st.error("Unexpected analysis failure. Check your input format and try again.")
        with st.expander("Technical details"):
            st.exception(exc)


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
context = st.session_state.get("analysis_context", {})
summary = validate_network(graph, weighted=bool(result.parameters["weighted"])).summary
plot_colors = context.get("plot_colors", {})

source_label = context.get("data_source", "Unknown")
if source_label == "Upload CSV/TSV" and context.get("uploaded_file"):
    source_label = f"{source_label} ({context['uploaded_file']})"

st.caption(
    f"Last run (UTC): {context.get('run_at_utc', 'unknown')} · Source: {source_label}"
)

tab_results, tab_membership, tab_export = st.tabs(
    ["Results", "Membership & Roles", "Reproducible Export"]
)

with tab_results:
    cols = st.columns(5)
    cols[0].metric("Nodes", f"{summary['nodes']:,}")
    cols[1].metric("Edges", f"{summary['edges']:,}")
    cols[2].metric("Density", f"{summary['density']:.3f}")
    cols[3].metric("Components", summary["components"])
    cols[4].metric("Null networks", result.parameters["n_random"])

    for warning in result.warnings:
        st.warning(warning)
    if summary["components"] > 1:
        st.info(
            "This network has multiple connected components. Rich-club interpretation may "
            "depend on whether disconnected regions are scientifically meaningful."
        )

    figure = plot_result(
        result,
        observed_color=plot_colors.get("observed_color", "#1F6F78"),
        signal_color=plot_colors.get("signal_color", "#C84A5A"),
        null_mean_color=plot_colors.get("null_mean_color", "#6B5B95"),
        null_envelope_color=plot_colors.get("null_envelope_color", "#B7A7D2"),
    )
    st.pyplot(figure, width="stretch")
    st.caption(
        "A normalized coefficient above one is not sufficient by itself. Interpret it with "
        "the null distribution, retained node count, threshold dependence, and domain context."
    )

    st.subheader("Threshold-level results")
    st.dataframe(result.table, width="stretch", hide_index=True)

with tab_membership:
    eligible = result.table.loc[result.table["reliable_node_count"], "threshold"].tolist()
    if eligible:
        st.subheader("Membership and edge roles")
        threshold = st.selectbox(
            "Inspect threshold", eligible, index=max(0, len(eligible) // 2)
        )
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
            to_csv_string(node_table),
            "richclub_nodes.csv",
            "text/csv",
            width="stretch",
        )
        right.download_button(
            "Download edge classification CSV",
            to_csv_string(edge_table),
            "richclub_edges.csv",
            "text/csv",
            width="stretch",
        )
    else:
        st.info(
            "No thresholds met the reliability criterion for membership reporting. "
            "Try lowering minimum rich nodes or using a denser network."
        )

with tab_export:
    st.subheader("Reproducible export")
    methods = methods_paragraph(result)
    methods_text = st.text_area("Generated Methods text", methods, height=170)

    export_bundle = {
        "analysis_parameters": dict(result.parameters),
        "run_context": context,
        "network_summary": summary,
    }
    download_cols = st.columns(4)
    download_cols[0].download_button(
        "Download all thresholds",
        to_csv_string(result.table),
        "richclub_results.csv",
        "text/csv",
        width="stretch",
    )
    download_cols[1].download_button(
        "Download SVG figure",
        result_figure_svg(
            plot_result(
                result,
                observed_color=plot_colors.get("observed_color", "#1F6F78"),
                signal_color=plot_colors.get("signal_color", "#C84A5A"),
                null_mean_color=plot_colors.get("null_mean_color", "#6B5B95"),
                null_envelope_color=plot_colors.get("null_envelope_color", "#B7A7D2"),
            )
        ),
        "richclub_figure.svg",
        "image/svg+xml",
        width="stretch",
    )
    download_cols[2].download_button(
        "Download Methods text",
        methods_text,
        "richclub_methods.txt",
        "text/plain",
        width="stretch",
    )
    download_cols[3].download_button(
        "Download settings JSON",
        settings_json(export_bundle),
        "richclub_settings.json",
        "application/json",
        width="stretch",
    )

st.divider()
st.caption(
    "RichClub Explorer v0.1.0 · Research software in beta · Results require scientific "
    "interpretation and sensitivity analysis."
)

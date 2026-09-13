"""Publication-oriented plotting helpers."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from .analysis import RichClubResult


def plot_result(result: RichClubResult) -> Figure:
    """Plot observed/null coefficients and normalized rich-club values."""

    table = result.table
    x = table["threshold"].to_numpy()
    reliable = table["reliable_node_count"].to_numpy(dtype=bool)
    n_thresholds = len(x)
    # Scale figure size with threshold count so dense results stay readable.
    width = float(np.clip(8.2 + 0.1 * max(0, n_thresholds - 10), 8.2, 12.8))
    height = float(np.clip(3.1 + 0.015 * max(0, n_thresholds - 20), 3.1, 4.0))
    figure, axes = plt.subplots(1, 2, figsize=(width, height), constrained_layout=True)

    axes[0].fill_between(
        x,
        table["phi_null_lower_95"],
        table["phi_null_upper_95"],
        color="#B7A7D2",
        alpha=0.45,
        label="95% null envelope",
    )
    axes[0].plot(x, table["phi_null_mean"], color="#6B5B95", label="Null mean")
    axes[0].plot(x, table["phi_observed"], color="#1F6F78", linewidth=2.2, label="Observed")
    axes[0].set_xlabel(f"{str(result.parameters['richness']).capitalize()} threshold")
    axes[0].set_ylabel("Rich-club coefficient")
    axes[0].legend(frameon=False)

    axes[1].axhline(1.0, color="#666666", linestyle="--", linewidth=1)
    axes[1].plot(x, table["rho"], color="#1F6F78", linewidth=2.2)
    signal = table["exploratory_signal"].to_numpy(dtype=bool)
    axes[1].scatter(x[signal], table.loc[signal, "rho"], color="#C84A5A", label="Exploratory signal")
    if np.any(~reliable):
        axes[1].scatter(
            x[~reliable],
            table.loc[~reliable, "rho"],
            facecolors="none",
            edgecolors="#999999",
            label="Small rich set",
        )
    axes[1].set_xlabel(f"{str(result.parameters['richness']).capitalize()} threshold")
    axes[1].set_ylabel(r"Normalized coefficient $\rho$")
    axes[1].legend(frameon=False)
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", alpha=0.18)
    return figure

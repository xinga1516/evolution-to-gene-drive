#!/usr/bin/env python3
"""Redraw only Figure 6D using the final 20 weekly population records."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


WORKSPACE = Path(__file__).resolve().parents[1]
ROOT = WORKSPACE / "文章终稿数据" / "Figure6" / "retest_20rep_20260914_final"
PROCESSED = ROOT / "processed"
FIGURES = ROOT / "figures"
COPY = WORKSPACE / "single_panel_outputs" / "Figure6D_last20"
GENERATOR = ROOT / "scripts" / "analyze_draw_figure6.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("figure6_generator", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def calculate_last20() -> pd.DataFrame:
    outcomes = pd.read_csv(PROCESSED / "outcomes.csv")
    weekly = pd.read_csv(PROCESSED / "weekly_metrics.csv")
    persistent = outcomes[outcomes["outcome"].eq("long_term_persistence")].copy()
    keys = ["condition_id", "replicate", "seed"]
    eligible = persistent[keys + ["model", "drive_conversion", "load", "N_pre"]]
    values = weekly.merge(eligible[keys], on=keys, how="inner")
    values = values.sort_values(keys + ["tick"])
    last20 = values.groupby(keys, group_keys=False).tail(20)
    counts = last20.groupby(keys)["N_total"].count().rename("n_valid_N_long_term")
    means = last20.groupby(keys)["N_total"].mean().rename("N_last20")
    result = eligible.merge(means, on=keys, how="left").merge(counts, on=keys, how="left")
    if not result["n_valid_N_long_term"].eq(20).all():
        bad = result.loc[~result["n_valid_N_long_term"].eq(20), keys + ["n_valid_N_long_term"]]
        raise RuntimeError(f"Figure 6D last-20 window is incomplete:\n{bad}")
    result["N_long_term_relative"] = result["N_last20"] / result["N_pre"]
    result["group"] = result["condition_id"].str.split("_").str[0]
    columns = ["condition_id", "group", "model", "drive_conversion", "load",
               "replicate", "seed", "N_long_term_relative", "n_valid_N_long_term"]
    result = result[columns]
    result.to_csv(PROCESSED / "Figure6_panelD_source_data.csv", index=False)
    return result


def save_all(fig, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    stem = directory / "Figure 6 panel D"
    fig.savefig(stem.with_suffix(".png"), dpi=600, facecolor="white")
    fig.savefig(stem.with_suffix(".tiff"), dpi=600, facecolor="white",
                pil_kwargs={"compression": "tiff_lzw"})
    fig.savefig(stem.with_suffix(".svg"), facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white")


def main() -> None:
    g = load_generator()
    data = calculate_last20()
    plt.rcParams.update({
        "font.family": g.FONT_FAMILY,
        "font.size": g.FONT_SIZE,
        "axes.labelsize": g.LABEL_SIZE,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    })
    fig, ax = plt.subplots(figsize=g.PANEL_SIZE_INCH)
    ys = np.arange(len(g.GROUP_ORDER))[::-1]
    for i, (group, y0) in enumerate(zip(g.GROUP_ORDER, ys)):
        without = data[(data.group == group) & (data.load == "absent")].N_long_term_relative
        with_load = data[(data.group == group) & (data.load == "present")].N_long_term_relative
        if len(without) == 0 or len(with_load) == 0:
            continue
        g.violin_points(ax, without, y0, g.RAIN_LTP, 0.12, seed=700 + i, marker="o")
        g.violin_points(ax, with_load, y0, g.RAIN_LTP, -0.12, seed=800 + i, marker="x")

    ax.set_yticks(ys, [g.GROUP_LABEL[group] for group in g.GROUP_ORDER])
    ax.set_xlabel("Relative population size\nover the last 20 weeks")
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.5, 1.0])
    ax.scatter([], [], marker="o", facecolors="none", edgecolors="#222222",
               label="Without recessive\nload")
    ax.scatter([], [], marker="x", color="#222222", label="With recessive\nload")
    ax.legend(frameon=False, fontsize=g.LEGEND_SIZE, loc="lower center",
              bbox_to_anchor=(0.5, 1.01), ncol=2, columnspacing=1.2)
    g.style_ax(ax)
    g.fixed_panel_layout(ax)
    save_all(fig, FIGURES)
    save_all(fig, COPY)
    plt.close(fig)


if __name__ == "__main__":
    main()

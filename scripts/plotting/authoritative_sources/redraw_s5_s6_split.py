from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "supplementary_final" / "source_data" / "S3_S4_S5_trajectory_values.csv"
OUT = ROOT / "single_panel_outputs"
OUT.mkdir(exist_ok=True)

COLORS = {
    "P70": "#0072B2",
    "P85": "#56B4E9",
    "S70": "#D55E00",
    "S85": "#CC79A7",
}
NO_LOAD_COLORS = {
    "70": "#2A9D8F",
    "85": "#6A51A3",
}
LABELS = {
    "P70": "Panmictic 0.70",
    "P85": "Panmictic 0.85",
    "S70": "Spatial 0.70",
    "S85": "Spatial 0.85",
}


def style_axis(ax, tick_fontsize=10.5, label_fontsize=11.5):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)
    ax.tick_params(direction="out", width=0.9, length=4,
                   labelsize=tick_fontsize)
    for label in (*ax.get_xticklabels(), *ax.get_yticklabels()):
        label.set_fontfamily("Arial")
    ax.set_xlim(-75, 1575)
    ax.set_xticks(range(0, 1501, 200))
    ax.set_xlabel("Weeks after release", fontsize=label_fontsize,
                  fontfamily="Arial")


def panel_letter(ax, letter):
    ax.text(-0.16, 1.04, letter, transform=ax.transAxes,
            fontsize=13, fontweight="bold", va="bottom")


def summary(df, metric):
    return (
        df.groupby("week_relative_release")[metric]
        .agg(
            median="median",
            q25=lambda z: z.quantile(0.25),
            q75=lambda z: z.quantile(0.75),
            q05=lambda z: z.quantile(0.05),
            q95=lambda z: z.quantile(0.95),
        )
        .reset_index()
        .sort_values("week_relative_release")
    )


def ribbon(ax, df, metric, color, linestyle="-"):
    s = summary(df, metric)
    for column in ("median", "q25", "q75", "q05", "q95"):
        s[column] = s[column].rolling(
            window=20, center=True, min_periods=1
        ).mean()
    x = s["week_relative_release"].to_numpy()
    ax.fill_between(x, s["q05"].to_numpy(), s["q95"].to_numpy(),
                    color=color, alpha=0.08, linewidth=0)
    ax.fill_between(x, s["q25"].to_numpy(), s["q75"].to_numpy(),
                    color=color, alpha=0.20, linewidth=0)
    ax.plot(x, s["median"].to_numpy(), color=color, linewidth=1.65,
            linestyle=linestyle)


def base_data():
    use = [
        "condition_id", "model", "drive_conversion", "load", "replicate",
        "week_relative_release", "N_total", "B", "mean_Wload",
        "mutation_copies_per_individual", "occupied_site_count",
    ]
    d = pd.read_csv(DATA, usecols=use)
    return d[d["week_relative_release"].between(0, 1500)].copy()


def make_s5(d):
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.3), dpi=600)
    metrics = [
        ("B", "Virtual haploid load", (0.2, 2.0)),
        ("mutation_copies_per_individual", "Mutation copies per individual", (3.0, 27.0)),
        ("mean_Wload", "Recorded mean genetic viability", (0.87, 1.0)),
    ]
    for ax, (metric, ylabel, ylim), letter in zip(axes, metrics, "abc"):
        for base in ("P70", "S70", "S85"):
            ribbon(ax, d[d["condition_id"].eq(base + "_L")], metric, COLORS[base])
        style_axis(ax, tick_fontsize=12.5, label_fontsize=16.0)
        ax.set_ylim(*ylim)
        ax.set_ylabel(ylabel, fontsize=16.0, fontfamily="Arial")
        panel_letter(ax, letter)

    handles = [Line2D([0], [0], color=COLORS[k], lw=2.5, label=LABELS[k])
               for k in ("P70", "S70", "S85")]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.89),
               ncol=4, frameon=False, fontsize=11.5, handlelength=1.8,
               columnspacing=2.2)
    fig.suptitle(
        "Supplementary Fig. S5 | Post-release recessive-load trajectories",
        x=0.035, y=0.975, ha="left", fontsize=19, fontweight="bold",
    )
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.15, top=0.76, wspace=0.34)
    for ext in ("png", "svg", "pdf"):
        fig.savefig(OUT / f"Supplementary_Figure_S5_panels_A-C.{ext}",
                    dpi=600, facecolor="white")
    plt.close(fig)


def make_s6(d):
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.45), dpi=300)
    panel_specs = [
        ("Panmictic", "Panmictic population size", ("P70", "P85")),
        ("Spatial", "Spatial population size", ("S70", "S85")),
    ]
    for ax, (model_label, ylabel, bases), letter in zip(axes, panel_specs, "ab"):
        for base in bases:
            efficiency = base[-2:]
            ribbon(ax, d[d["condition_id"].eq(base + "_L")], "N_total",
                   COLORS[base], "-")
            ribbon(ax, d[d["condition_id"].eq(base + "_N")], "N_total",
                   NO_LOAD_COLORS[efficiency], "-")
        style_axis(ax)
        ax.set_ylabel(ylabel, fontsize=11.5)
        panel_letter(ax, letter)
        handles = [
            Line2D([0], [0], color=COLORS[bases[0]], lw=2.4,
                   label="0.70, with recessive load"),
            Line2D([0], [0], color=COLORS[bases[1]], lw=2.4,
                   label="0.85, with recessive load"),
            Line2D([0], [0], color=NO_LOAD_COLORS["70"], lw=2.4,
                   label="0.70, without recessive load"),
            Line2D([0], [0], color=NO_LOAD_COLORS["85"], lw=2.4,
                   label="0.85, without recessive load"),
        ]
        ax.legend(handles=handles, title=model_label, loc="lower center",
                  bbox_to_anchor=(0.5, 1.03), ncol=2, frameon=False,
                  fontsize=9.1, title_fontsize=10.4, handlelength=2.0,
                  columnspacing=1.4)
    fig.suptitle(
        "Supplementary Fig. S6 | Post-release population trajectories",
        x=0.045, y=0.975, ha="left", fontsize=19, fontweight="bold",
    )
    fig.subplots_adjust(left=0.09, right=0.985, bottom=0.15, top=0.69, wspace=0.32)
    for ext in ("png", "svg", "pdf"):
        fig.savefig(OUT / f"Supplementary_Figure_S6_panels_E-F.{ext}",
                    dpi=300, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    data = base_data()
    make_s5(data)
    make_s6(data)

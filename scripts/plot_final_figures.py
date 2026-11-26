#!/usr/bin/env python3
"""Render repository-native scientific figures from canonical Source Data.

These renders preserve the frozen data, endpoints, final-20 definitions,
grouping, colours and statistical labels. All inputs are read directly from
the published Source Data workbooks.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Patch
import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data" / "source_data"
STATS = REPO / "results" / "statistics"
OUT = REPO / "output" / "figures"

GREEN = "#67C5A3"
GREEN_DARK = "#2A9D8F"
ORANGE = "#F4A261"
ORANGE_DARK = "#D96B1B"
BLUE = "#4E79B7"
BLUE_LIGHT = "#56B4E9"
PURPLE = "#7B5DAE"
PINK = "#CC79A7"
GRAY = "#777777"
BLACK = "#222222"
S4_PAN = "#0072B2"
S4_SPATIAL = "#D55E00"
S6_P70_WITH = "#2E8592"
S6_P70_WITHOUT = "#A6DCC8"
S6_S85_WITH = "#0072B2"
S6_S85_WITHOUT = "#56B4E9"

mpl.rcParams.update({
    "font.family": "Arial", "font.size": 9, "axes.labelsize": 10,
    "axes.titlesize": 10, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "legend.fontsize": 7.5, "axes.linewidth": 0.8, "pdf.fonttype": 42,
    "ps.fonttype": 42, "savefig.facecolor": "white",
    "svg.hashsalt": "evolution-to-gene-drive-archive-v1",
})


def clean(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(width=.7, length=3)


def source(item: str, sheet: str) -> pd.DataFrame:
    """Read one published Source Data sheet."""
    return pd.read_excel(DATA / f"{item}.xlsx", sheet_name=sheet)


def label_panels(axes):
    for letter, ax in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", np.ravel(axes)):
        ax.text(-.15, 1.05, letter, transform=ax.transAxes, fontweight="bold", fontsize=11)


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    metadata = {"Creator": "evolution-to-gene-drive reproducibility archive", "Date": None}
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight", metadata=metadata)
    fig.savefig(OUT / f"{name}.png", dpi=300, bbox_inches="tight", metadata={"Software": metadata["Creator"]})
    plt.close(fig)


def _outcome_bar(ax, data, condition_cols, outcome_col="outcome"):
    order = ["Population elimination", "Drive loss", "Long-term persistence"]
    colors = [ORANGE, BLUE, GREEN]
    normalized = data.copy()
    outcome_key = normalized[outcome_col].astype(str).str.replace("_", " ").str.strip().str.lower()
    normalized[outcome_col] = outcome_key.map({
        "elimination": "Population elimination",
        "population elimination": "Population elimination",
        "drive loss": "Drive loss",
        "long-term persistence": "Long-term persistence",
    })
    paired = condition_cols[-1] if condition_cols and condition_cols[-1] in {"treatment", "load"} else None
    base_cols = condition_cols[:-1] if paired else condition_cols
    summary = normalized.groupby([*condition_cols, outcome_col]).size().unstack(fill_value=0)
    summary = summary.reindex(columns=order, fill_value=0)
    fractions = summary.div(summary.sum(axis=1), axis=0)
    if paired:
        bases = list(normalized.groupby(base_cols, sort=True).groups)
        pair_values = (["Neutral control", "Functional modifier"] if paired == "treatment" else ["absent", "present"])
        pair_labels = (["Neutral mutations", "Variable mutations"] if paired == "treatment" else ["Without recessive load", "With recessive load"])
        for yi, base in enumerate(bases):
            base_tuple = base if isinstance(base, tuple) else (base,)
            for pi, pair_value in enumerate(pair_values):
                index = (*base_tuple, pair_value)
                if len(condition_cols) == 1:
                    index = index[0]
                values = fractions.loc[index] if index in fractions.index else pd.Series(0, index=order)
                left = 0.0
                for outcome, color in zip(order, colors):
                    value = float(values[outcome])
                    ax.barh(yi + (-.16 if pi == 0 else .16), value, left=left, height=.27,
                            color=color, edgecolor="#444", linewidth=.35,
                            hatch=None if pi == 0 else "////")
                    left += value
        labels=[]
        for base in bases:
            values=base if isinstance(base,tuple) else (base,)
            text=[]
            for value in values:
                if isinstance(value,float): text.append("0.99/0.96" if np.isclose(value,.99) else f"{value:.2f}")
                else: text.append(str(value))
            labels.append("\n".join(text))
        ax.set_yticks(range(len(bases)), labels); ax.invert_yaxis()
        handles=[Patch(facecolor=color,edgecolor="#444",label=outcome) for outcome,color in zip(order,colors)]
        handles += [Patch(facecolor="white",edgecolor="#444",label=pair_labels[0]),
                    Patch(facecolor="white",edgecolor="#444",hatch="////",label=pair_labels[1])]
    else:
        y = np.arange(len(fractions)); left = np.zeros(len(fractions))
        for outcome, color in zip(order, colors):
            values = fractions[outcome].to_numpy()
            ax.barh(y, values, left=left, color=color, edgecolor="#444", linewidth=.35)
            left += values
        ax.set_yticks(y, [" | ".join(map(str, idx if isinstance(idx, tuple) else [idx])) for idx in fractions.index])
        handles=[Patch(facecolor=color,edgecolor="#444",label=outcome) for outcome,color in zip(order,colors)]
    ax.set(xlim=(0, 1), xlabel="Outcome probability")
    ax.legend(handles=handles, frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(.5, 1.01),
              columnspacing=.8, handletextpad=.4)
    clean(ax)


def _jitter_panel(ax, data, metric, ylabel=None):
    conditions = list(data.groupby(["model", "h"], sort=True).groups)
    rng = np.random.default_rng(20261124)
    for y, (model, h) in enumerate(conditions):
        group = data[(data.model.eq(model)) & (data.h.eq(h))]
        for treatment, marker, color, offset in [
            ("Neutral control", "o", GREEN, -.08),
            ("Functional modifier", "x", GREEN_DARK, .08),
        ]:
            values = group[group.treatment.eq(treatment)][metric].dropna().to_numpy(float)
            yy = y + offset + rng.normal(0, .018, len(values))
            if marker == "o":
                ax.scatter(values, yy, s=9, facecolors="none", edgecolors=color, linewidths=.5, alpha=.65)
                ax.scatter([values.mean()], [y + offset], s=34, facecolors="white", edgecolors=BLACK, linewidths=1.1, zorder=5)
            else:
                ax.scatter(values, yy, s=10, marker="x", color=color, linewidths=.55, alpha=.65)
                ax.scatter([values.mean()], [y + offset], s=34, marker="x", color=BLACK, linewidths=1.2, zorder=5)
    ax.set_yticks(range(len(conditions)), [f"{m}\n{h:g}" for m, h in conditions])
    ax.invert_yaxis()
    if ylabel:
        ax.set_ylabel(ylabel)
    clean(ax)


def figure1():
    endpoint = source("Figure1", "Panel_A")
    endpoint["outcome"] = np.select(
        [endpoint.elimination.astype(bool), endpoint.drive_loss.astype(bool)],
        ["Elimination", "Drive loss"], default="Long-term persistence")
    final = source("Figure1", "Panels_B_C")
    traj = source("Figure1", "Panel_D")
    fig, axes = plt.subplots(2, 2, figsize=(8.3, 6.1))
    _outcome_bar(axes[0, 0], endpoint, ["model", "conversion", "treatment"])
    _jitter_panel(axes[0, 1], final, "final20_attribute_weighted")
    axes[0, 1].set_xlabel("Final drive conversion\n(final 20 records; population-size weighted)")
    _jitter_panel(axes[1, 0], final, "final20_n_over_k")
    axes[1, 0].set_xlabel("Final relative population size\n(final 20 records)")
    for (conversion, treatment), group in traj.groupby(["conversion", "treatment"]):
        color = GREEN if treatment == "Neutral control" else GREEN_DARK
        ls = "-" if conversion == .70 else "--"
        axes[1, 1].plot(group.week, group["median"], color=color, ls=ls, lw=1.2, label=f"{conversion:g} {treatment}")
        axes[1, 1].fill_between(group.week, group.q25, group.q75, color=color, alpha=.08)
    axes[1, 1].set(xlabel="Weeks after release", ylabel="Nearest-neighbor index (NNI)")
    axes[1, 1].legend(frameon=False, ncol=2)
    clean(axes[1, 1]); label_panels(axes); fig.tight_layout(); save(fig, "Figure1")


def _association(ax, data, stats_row, ylabel):
    neutral = data[data.cohort.eq("Neutral mutations")].groupby("setting").agg(x=("final20_nni", "mean"), xse=("final20_nni", "sem"))
    variable = data[data.cohort.eq("Variable mutations")].groupby("setting").agg(y=("final20_attribute_weighted", "mean"), yse=("final20_attribute_weighted", "sem"))
    joined = neutral.join(variable)
    ax.errorbar(joined.x, joined.y, xerr=joined.xse, yerr=joined.yse, fmt="o", color="#A7B29A", ms=4, capsize=2, lw=.8)
    for setting, point in joined.iterrows():
        ax.text(point.x + .002, point.y + .005, f"{setting:g}", fontsize=7)
    ax.axhline(.5, color=GRAY, lw=.7, ls=(0, (3, 3)))
    ax.text(.98, .03, f"Spearman ρ={stats_row.estimate:.2f}\nP={stats_row.p_raw:.4g}", transform=ax.transAxes, ha="right", va="bottom")
    ax.set(xlabel="Mean NNI over final 20 records\n(Neutral mutations)", ylabel=ylabel)
    clean(ax)


def figure2():
    endpoint = source("Figure2", "Panel_A")
    endpoint["model"] = endpoint["model_std"]
    final = source("Figure2", "Panels_B_C")
    traj = source("Figure2", "Panel_D")
    stats_table = pd.read_csv(STATS / "all_inferential_tests.csv")
    fig = plt.figure(figsize=(10.5, 6.2)); grid = fig.add_gridspec(2, 3)
    axes = np.array([fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1]), fig.add_subplot(grid[0, 2]), fig.add_subplot(grid[1, :2]), fig.add_subplot(grid[1, 2])], dtype=object)
    _outcome_bar(axes[0], endpoint, ["model", "h", "treatment"])
    _jitter_panel(axes[1], final, "final20_attribute_weighted"); axes[1].set_xlabel("Final embryo resistance\n(final 20 records; population-size weighted)")
    _jitter_panel(axes[2], final, "final20_n_over_k"); axes[2].set_xlabel("Final relative population size\n(final 20 records)")
    summary = traj.rename(columns={"median": "nni"})
    for key, group in summary.groupby(["model", "h", "treatment"]):
        axes[3].plot(group.week, group.nni, lw=.8, alpha=.75, label=" | ".join(map(str,key)))
    axes[3].set(xlabel="Weeks after release", ylabel="NNI"); clean(axes[3])
    stat = stats_table[stats_table.test_id.eq("Figure2E_exact_spearman")].iloc[0]
    _association(axes[4], source("Figure2", "Panel_E"), stat, "Final embryo resistance\n(Variable mutations)")
    label_panels(axes); fig.tight_layout(); save(fig, "Figure2")


def figure3():
    final = source("Figure3", "Panels_A_C")
    traj = source("Figure3", "Panel_D")
    stats_table = pd.read_csv(STATS / "all_inferential_tests.csv")
    fig = plt.figure(figsize=(10.5, 6.2)); grid = fig.add_gridspec(2, 3)
    axes = np.array([fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1]), fig.add_subplot(grid[0, 2]), fig.add_subplot(grid[1, :2]), fig.add_subplot(grid[1, 2])], dtype=object)
    _outcome_bar(axes[0], final, ["model", "h", "treatment"])
    _jitter_panel(axes[1], final, "final20_attribute_weighted"); axes[1].set_xlabel("Final female heterozygote fitness\n(final 20 records; population-size weighted)")
    axes[1].text(.02, 1.02, "0.99/0.96 = female/male", transform=axes[1].transAxes,
                 ha="left", va="bottom", fontsize=7.5, fontweight="normal")
    _jitter_panel(axes[2], final, "final20_n_over_k"); axes[2].set_xlabel("Final relative population size\n(final 20 records)")
    summary = traj.rename(columns={"median": "nni"})
    for key, group in summary.groupby(["model", "h", "treatment"]):
        axes[3].plot(group.week, group.nni, lw=.8, alpha=.75, label=" | ".join(map(str,key)))
    axes[3].set(xlabel="Weeks after release", ylabel="NNI"); clean(axes[3])
    stat = stats_table[stats_table.test_id.eq("Figure3E_exact_spearman")].iloc[0]
    _association(axes[4], source("Figure3", "Panel_E"), stat, "Final female heterozygote fitness\n(Variable mutations)")
    label_panels(axes); fig.tight_layout(); save(fig, "Figure3")


def figure4():
    data = source("Figure4", "Panels_A_C")
    parts = data.group_id.str.extract(r"_(dc|er|sf)_.*_b([0-9p]+)_m(\d+)$")
    data["trait"] = parts[0]
    data["b"] = parts[1].str.replace("p", ".", regex=False).astype(float)
    data["m"] = parts[2].astype(int)
    data = data[data.is_ltp.astype(bool)]
    stat = pd.read_csv(STATS / "all_inferential_tests.csv")
    labels = {"dc":"Final drive conversion", "er":"Final embryo resistance", "sf":"Final female heterozygote fitness"}
    bmin = {"dc":.0048, "er":.0140, "sf":.0113}
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.3))
    for ax, trait in zip(axes, ["dc","er","sf"]):
        g = data[data.trait.eq(trait)].copy()
        paths = [("Fixed number of loci (m)", g[g.m.eq(50) & ~np.isclose(g.b,bmin[trait])], BLUE),
                 ("Fixed effect scale (b)", g[np.isclose(g.b,bmin[trait]) & ~g.m.eq(50)], PINK)]
        for name, q, color in paths:
            x=q.realised_initial_sd_last10_prerelease; y=q.final_attribute_mean_last10
            ax.scatter(x,y,s=5,alpha=.12,color=color,rasterized=True)
            ranges = g.assign(Path=np.where(g.m.eq(50), "fixed_m", "fixed_b")).groupby("Path").realised_initial_sd_last10_prerelease.agg(["min", "max"])
            lo, hi = float(ranges["min"].max()), float(ranges["max"].min())
            fit=q[x.between(lo,hi)].dropna(subset=["realised_initial_sd_last10_prerelease","final_attribute_mean_last10"])
            coef=np.polyfit(fit.realised_initial_sd_last10_prerelease,fit.final_attribute_mean_last10,1)
            xx=np.linspace(lo,hi,100); yy=np.polyval(coef,xx)
            residual=fit.final_attribute_mean_last10-np.polyval(coef,fit.realised_initial_sd_last10_prerelease)
            band=np.quantile(np.abs(residual),.75)
            ax.fill_between(xx,yy-band,yy+band,color=color,alpha=.12,lw=0)
            ax.plot(xx,yy,lw=1.4,color=color,label=name)
            means=q.groupby("group_id").agg(x=("realised_initial_sd_last10_prerelease","mean"),y=("final_attribute_mean_last10","mean"))
            ax.scatter(means.x,means.y,s=20,facecolors="white",edgecolors=color,zorder=4)
        shared=g[g.m.eq(50) & np.isclose(g.b,bmin[trait])]
        ax.scatter([shared.realised_initial_sd_last10_prerelease.mean()],
                   [shared.final_attribute_mean_last10.mean()],marker="D",s=42,
                   color=BLACK,label="Shared setting",zorder=6)
        p_sd=float(stat.loc[stat.test_id.eq(f"F4{dict(dc='A',er='B',sf='C')[trait]}_{trait}_realized_sd"),"p_adjusted"].iloc[0])
        p_arch=float(stat.loc[stat.test_id.eq(f"F4{dict(dc='A',er='B',sf='C')[trait]}_{trait}_architecture"),"p_adjusted"].iloc[0])
        p_sd_text="<0.0001" if p_sd < 1e-4 else f"={p_sd:.4f}"
        ax.text(.02,.98,f"Realized SD: Holm P {p_sd_text}\nArchitecture: Holm P={p_arch:.4f}",
                transform=ax.transAxes,va="top",fontsize=7.2)
        ax.set(xlabel="Realized pre-release attribute SD", ylabel=labels[trait]); clean(ax)
    axes[0].legend(frameon=False,fontsize=6.8)
    label_panels(axes); fig.tight_layout(); save(fig,"Figure4")


def figure5():
    data=source("Figure5", "Panels_A_B")
    fig,axes=plt.subplots(1,2,figsize=(8.2,3.5))
    outcomes=[("elimination",ORANGE),("drive loss",BLUE),("long-term persistence",GREEN)]
    modes=[("uniform",-.16,"Fixed dispersal",None),("evolving",.16,"Evolving dispersal","//")]
    for yi,conversion in enumerate([.75,.85,.95,.99]):
        for mode,off,_,hatch in modes:
            q=data[data.conversion.eq(conversion)&data["mode"].eq(mode)]
            left=0
            for outcome,color in outcomes:
                width=(q.outcome.str.lower().eq(outcome)).mean()
                axes[0].barh(yi+off,width,left=left,height=.27,color=color,edgecolor="#444",lw=.55,hatch=hatch)
                left+=width
    axes[0].set_yticks(range(4),["0.75","0.85","0.95","0.99"])
    axes[0].set(xlabel="Outcome probability",ylabel="Drive conversion",xlim=(0,1))
    axes[0].legend(handles=[Patch(fc=ORANGE,ec="#444",label="Population elimination"),Patch(fc=BLUE,ec="#444",label="Drive loss"),Patch(fc=GREEN,ec="#444",label="Long-term persistence"),Patch(fc="white",ec="#444",label="Fixed dispersal"),Patch(fc="white",ec="#444",hatch="//",label="Evolving dispersal")],frameon=False,fontsize=6.2,ncol=2)
    rng=np.random.default_rng(5); labels=["No drive","0.75","0.85","0.95","0.99"]
    point_colors={"long-term persistence":GREEN,"elimination":ORANGE,"drive loss":BLUE,"no drive":GREEN}
    groups=[data[data["mode"].eq("nodrive")]]+[data[data.conversion.eq(c)&data["mode"].eq("evolving")] for c in [.75,.85,.95,.99]]
    for yi,q in enumerate(groups):
        for outcome,z in q.groupby(q.outcome.str.lower()):
            face="none" if outcome=="no drive" else point_colors.get(outcome,GRAY)
            axes[1].scatter(z.dispersal_E_percent,yi+rng.normal(0,.035,len(z)),s=9,alpha=.55,
                            facecolors=face,edgecolors=point_colors.get(outcome,GRAY),lw=.6)
        ltp=q[q.outcome.str.lower().isin(["long-term persistence","no drive"])].dispersal_E_percent
        non=q[~q.outcome.str.lower().isin(["long-term persistence","no drive"])].dispersal_E_percent
        if len(ltp): axes[1].errorbar(ltp.mean(),yi,xerr=ltp.sem(),fmt="o",mfc="white",mec=BLACK,color=BLACK,capsize=2,zorder=5)
        if len(non): axes[1].errorbar(non.mean(),yi,xerr=non.sem(),fmt="o",mfc="white",mec=ORANGE_DARK,color=ORANGE_DARK,capsize=2,zorder=5)
    axes[1].set_yticks(range(5),labels); axes[1].set(xlabel="Adult dispersal change (%)",ylabel="Drive conversion"); axes[1].axvline(0,color=GRAY,ls="--",lw=.7); clean(axes[1])
    label_panels(axes); fig.tight_layout(); save(fig,"Figure5")


def figure6():
    a=source("Figure6", "Panel_A"); b=source("Figure6", "Panel_B")
    c=source("Figure6", "Panel_C"); d=source("Figure6", "Panel_D")
    fig,axes=plt.subplots(2,2,figsize=(8.2,6.1)); rng=np.random.default_rng(6)
    groups=["P70","P85","S70","S85"]
    for yi,g in enumerate(groups):
        q=a[a.group.eq(g)]
        for load,marker,off in [("absent","o",-.08),("present","x",.08)]:
            z=q[q.load.eq(load)].Nmin_relative
            if marker == "o":
                axes[0,0].scatter(z,yi+off+rng.normal(0,.02,len(z)),s=12,marker=marker,facecolors="none",edgecolors=GREEN)
            else:
                axes[0,0].scatter(z,yi+off+rng.normal(0,.02,len(z)),s=12,marker=marker,color=GREEN_DARK)
    axes[0,0].set_yticks(range(4),groups); axes[0,0].set_xlabel("Minimum post-release relative population size"); clean(axes[0,0])
    _outcome_bar(axes[0,1],a,["group","load"])
    summary=c[c.week_relative_release.between(0,1500)].rename(columns={"median":"B"})
    for condition,q in summary.groupby("condition_id"): axes[1,0].plot(q.week_relative_release,q.B,lw=1,label=condition)
    axes[1,0].set(xlabel="Weeks after release",ylabel="Haploid inbreeding load, B",ylim=(0,2.0)); axes[1,0].legend(frameon=False); clean(axes[1,0])
    for yi,g in enumerate(["P70","S70","S85"]):
        q=d[d.group.eq(g)]
        for load,marker,off in [("absent","o",-.08),("present","x",.08)]:
            z=q[q.load.eq(load)].N_long_term_relative
            if marker == "o":
                axes[1,1].scatter(z,yi+off+rng.normal(0,.02,len(z)),s=12,marker=marker,facecolors="none",edgecolors=GREEN)
            else:
                axes[1,1].scatter(z,yi+off+rng.normal(0,.02,len(z)),s=12,marker=marker,color=GREEN_DARK)
    axes[1,1].set_yticks(range(3),["P70","S70","S85"]); axes[1,1].set(xlabel="Relative population size over final 20 records",xlim=(0,1)); clean(axes[1,1])
    label_panels(axes); fig.tight_layout(); save(fig,"Figure6")


def figure_s1():
    fig,axes=plt.subplots(1,3,figsize=(10.5,3.4))
    for ax,panel,title in zip(axes,["A","B","C"],["Figure 1 spatial","Figure 2E","Figure 3E"]):
        d=source("Figure_S1", f"Panel_{panel}")
        for cohort,marker in [("Neutral mutations","o"),("Variable mutations","x")]:
            q=d[d.cohort.eq(cohort)]
            if marker == "o":
                ax.scatter(q.final20_nni,q.setting,s=10,marker=marker,facecolors="none",edgecolors=GREEN,alpha=.65,label=cohort)
            else:
                ax.scatter(q.final20_nni,q.setting,s=10,marker=marker,color=GREEN_DARK,alpha=.65,label=cohort)
            means=q.groupby("setting").final20_nni.mean(); ax.scatter(means,means.index,s=30,marker=marker,color=BLACK,zorder=5)
        ax.set(title=title,xlabel="Mean NNI over final 20 records",ylabel="Drive conversion efficiency"); ax.invert_yaxis(); clean(ax)
    axes[0].legend(frameon=False); label_panels(axes); fig.tight_layout(); save(fig,"Figure_S1")


def figure_s2():
    d=source("Figure_S2", "Panels_A_B")
    fig,axes=plt.subplots(1,2,figsize=(10.5,5.0))
    settings=["0.70","0.75","0.80","0.85","0.90","0.95","Emp"]
    for ax,(figure,q) in zip(axes,d.groupby("figure",sort=False)):
        for yi,setting in enumerate(settings):
            for cohort,off,hatch in [("Neutral mutations",-.18,None),("Variable mutations",.18,"//")]:
                z=q[(q.setting.eq(setting))&(q.cohort.eq(cohort))].iloc[0]
                total=z.long_term_persistence+z.population_elimination
                ltp=z.long_term_persistence/total
                ax.barh(yi+off,ltp,height=.30,color=GREEN,edgecolor="#555",lw=.7,hatch=hatch)
                if ltp<1: ax.barh(yi+off,1-ltp,left=ltp,height=.30,color=ORANGE,edgecolor="#555",lw=.7,hatch=hatch)
                ax.text(1.02,yi+off,f"{int(total)}/20",va="center",fontsize=7.5)
        ax.set_yticks(range(len(settings)),settings); ax.invert_yaxis(); ax.set_xlim(0,1.13)
        ax.set(xlabel="Outcome probability",ylabel="Drive conversion",title=f"{figure} settings"); clean(ax)
    axes[0].legend(handles=[Patch(fc=GREEN,label="Long-term persistence"),Patch(fc=ORANGE,label="Population elimination"),Patch(fc="white",ec="#555",label="Neutral mutations"),Patch(fc="white",ec="#555",hatch="//",label="Variable mutations")],frameon=False,ncol=2)
    label_panels(axes); fig.tight_layout(); save(fig,"Figure_S2")


def figure_s3():
    d=source("Figure_S3", "Panels_A_F")
    metrics=["dispersal_change_pct","dispersal_sd_ratio","he_over_initial","segregating_over_initial","adult_N_ratio","fertile_female_N_ratio"]
    labels=["Adult mean dispersal change (%)","Within-population dispersal SD ratio","Expected heterozygosity retained","Segregating modifier loci retained","Adult population ratio","Fertile adult female ratio"]
    fig,axes=plt.subplots(2,3,figsize=(10.5,5.9))
    for ax,metric,label in zip(axes.ravel(),metrics,labels):
        for arch,q in d[d.metric.eq(metric)].groupby("arch"):
            ax.plot(q.tick,q["median"],lw=1.4,color=GRAY,label=arch)
            ax.fill_between(q.tick,q.q05,q.q95,color=GRAY,alpha=.12,lw=0)
            ax.fill_between(q.tick,q.q25,q.q75,color=GRAY,alpha=.28,lw=0)
        ax.set(xlim=(0,1600),xlabel="Generation",ylabel=label); clean(ax)
    axes[0,0].legend(handles=[plt.Line2D([],[],color=GRAY,lw=1.4,label="Median across no-drive simulations"),Patch(fc=GRAY,alpha=.28,label="Interquartile range"),Patch(fc=GRAY,alpha=.12,label="5th–95th percentile range")],frameon=False,fontsize=6.7)
    label_panels(axes); fig.tight_layout(); save(fig,"Figure_S3")


def figure_s4():
    d=source("Figure_S4", "Panels_A_D")
    metrics=["virtual_haploid_load","copies_per_individual","population_N","mean_genetic_viability"]
    labels=["Virtual haploid load","Mutation copies per individual","Population size","Mean genetic viability (W_load)"]
    fig,axes=plt.subplots(2,2,figsize=(8.2,6))
    display = {"P70_L": ("Panmictic", S4_PAN), "S70_L": ("Spatial", S4_SPATIAL)}
    for ax,metric,label in zip(axes.ravel(),metrics,labels):
        for condition,q in d.groupby("condition_id"):
            legend_label, color = display[condition]
            summary=q.groupby("block")[metric].mean()
            ax.plot(summary.index,summary,"o-",lw=1,color=color,label=legend_label)
        ax.set(xticks=[1,2,3,4],xlabel="Pre-release 250-week block",ylabel=label); clean(ax)
    axes[0,0].legend(frameon=False); label_panels(axes); fig.tight_layout(); save(fig,"Figure_S4")


def figure_s5():
    d=pd.concat([source("Figure_S5", name) for name in ["Panel_A", "Panel_B", "Panel_C"]], ignore_index=True)
    metrics=["B","mutation_copies_per_individual","mean_Wload"]
    labels=["Virtual haploid load","Mutation copies per individual","Recorded mean genetic viability"]
    colors={"P70_L":"#0072B2","S70_L":"#D55E00","S85_L":"#CC79A7"}
    display={"P70_L":"Panmictic 0.70","S70_L":"Spatial 0.70","S85_L":"Spatial 0.85"}
    fig,axes=plt.subplots(1,3,figsize=(10.5,3.4))
    for ax,metric,label in zip(axes,metrics,labels):
        for condition,q in d[d.metric.eq(metric)].groupby("condition_id"):
            color=colors.get(condition,GRAY); ax.plot(q.week_relative_release,q["median"],color=color,lw=1.1,label=display[condition]); ax.fill_between(q.week_relative_release,q.q25,q.q75,color=color,alpha=.1)
        ax.set(xlabel="Weeks after release",ylabel=label); clean(ax)
    axes[0].legend(frameon=False); label_panels(axes); fig.tight_layout(); save(fig,"Figure_S5")


def figure_s6():
    d=source("Figure_S6", "Replicate_trajectories")
    fig,axes=plt.subplots(1,2,figsize=(8.4,3.7))
    panels=[
        ("pan",axes[0],[("P70_N",S6_P70_WITHOUT,"0.70, without recessive load"),("P70_L",S6_P70_WITH,"0.70, with recessive load")]),
        ("spatial",axes[1],[("S70_N",S6_P70_WITHOUT,"0.70, without recessive load"),("S70_L",S6_P70_WITH,"0.70, with recessive load"),("S85_N",S6_S85_WITHOUT,"0.85, without recessive load"),("S85_L",S6_S85_WITH,"0.85, with recessive load")]),
    ]
    for model,ax,series in panels:
        q=d[d.model.eq(model)]
        for condition,color,legend_label in series:
            first=True
            for _,run in q[q.condition_id.eq(condition)].groupby(["replicate","seed"]):
                ax.plot(run.week_relative_release,run.N_total,color=color,lw=.5,alpha=.58,
                        label=legend_label if first else None)
                first=False
        ax.set(xlabel="Weeks after release",ylabel=f"{model.title()} population size"); clean(ax)
        ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(.5,1.01), ncol=2)
    label_panels(axes); fig.tight_layout(); save(fig,"Figure_S6")


RENDERERS={
    "Figure1":figure1,"Figure2":figure2,"Figure3":figure3,"Figure4":figure4,
    "Figure5":figure5,"Figure6":figure6,"Figure_S1":figure_s1,"Figure_S2":figure_s2,
    "Figure_S3":figure_s3,"Figure_S4":figure_s4,"Figure_S5":figure_s5,"Figure_S6":figure_s6,
}


def main():
    global OUT
    parser=argparse.ArgumentParser(); parser.add_argument("--figure",choices=["all",*RENDERERS],default="all"); parser.add_argument("--output-dir",type=Path,default=OUT); args=parser.parse_args()
    OUT = args.output_dir.resolve()
    # Exact submitted typography requires Arial; fail instead of silently
    # substituting a metrically different font.
    font_manager.findfont("Arial", fallback_to_default=False)
    selected=RENDERERS if args.figure=="all" else {args.figure:RENDERERS[args.figure]}
    for name,renderer in selected.items():
        renderer(); print(f"rendered {name}")


if __name__=="__main__":
    main()

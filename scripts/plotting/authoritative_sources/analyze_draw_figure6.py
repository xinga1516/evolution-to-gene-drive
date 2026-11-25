#!/usr/bin/env python3
"""Statistics, source data and panel drawing for the final Figure 6 retest."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "processed"
FIG = ROOT / "figures"
QA = ROOT / "qa"
FIG.mkdir(exist_ok=True)

# User-editable figure typography and dimensions.
PANEL_SIZE_INCH = (5.0, 4.5)
DPI = 600
FONT_FAMILY = "Arial"
FONT_SIZE = 15
LABEL_SIZE = 17
TICK_SIZE = 15
LEGEND_SIZE = 13

GREY = "#7F7F7F"
BLUE = "#C29A3A"
BLUE_LIGHT = "#E6D2D5"
OUTCOME_ELIM = "#F4A261"
OUTCOME_LOSS = "#4E79B7"
OUTCOME_LTP = "#6CC4A1"
RAIN_LTP = OUTCOME_LTP
RAIN_ELIM = OUTCOME_ELIM
RAIN_LOSS = OUTCOME_LOSS
GROUP_ORDER = ["P70", "P85", "S70", "S85"]
GROUP_LABEL = {
    "P70": "0.70", "P85": "0.85",
    "S70": "0.70", "S85": "0.85",
}

RNG_SEED = 20260919
N_PERM = 200_000
N_BOOT = 20_000


def group_key(condition_id: str) -> str:
    return condition_id.split("_")[0]


def holm(pvals: list[float]) -> list[float]:
    out = [math.nan] * len(pvals)
    valid = [(i, p) for i, p in enumerate(pvals) if np.isfinite(p)]
    valid.sort(key=lambda x: x[1])
    running = 0.0
    m = len(valid)
    for rank, (idx, p) in enumerate(valid):
        running = max(running, min(1.0, (m - rank) * p))
        out[idx] = running
    return out


def p_symbol(p: float) -> str:
    if not np.isfinite(p): return "NA"
    if p < 0.001: return "***"
    if p < 0.01: return "**"
    if p < 0.05: return "*"
    return "ns"


def bootstrap_ci(x, stat=np.mean, n_boot=N_BOOT, seed=RNG_SEED):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) == 0: return (math.nan, math.nan)
    rng = np.random.default_rng(seed)
    vals = np.empty(n_boot)
    for start in range(0, n_boot, 2000):
        n = min(2000, n_boot - start)
        sample = x[rng.integers(0, len(x), (n, len(x)))]
        vals[start:start+n] = stat(sample, axis=1)
    return tuple(np.quantile(vals, [0.025, 0.975]))


def independent_permutation(x, y, seed, n_perm=N_PERM):
    x = np.asarray(x, float); y = np.asarray(y, float)
    x = x[np.isfinite(x)]; y = y[np.isfinite(y)]
    obs = float(y.mean() - x.mean())
    pooled = np.concatenate([x, y]); nx = len(x)
    rng = np.random.default_rng(seed)
    extreme = 0
    for _ in range(n_perm):
        z = rng.permutation(pooled)
        stat = z[nx:].mean() - z[:nx].mean()
        extreme += abs(stat) >= abs(obs) - 1e-15
    p = (extreme + 1) / (n_perm + 1)
    return obs, p


def exact_sign_flip(diff):
    d = np.asarray(diff, float)
    d = d[np.isfinite(d)]
    n = len(d); obs = float(d.mean())
    total = 1 << n; extreme = 0
    chunk = 1 << min(n, 16)
    bits = np.arange(n, dtype=np.uint64)
    for start in range(0, total, chunk):
        ids = np.arange(start, min(start + chunk, total), dtype=np.uint64)[:, None]
        signs = 1.0 - 2.0 * ((ids >> bits) & 1).astype(float)
        vals = signs.dot(d) / n
        extreme += int(np.count_nonzero(np.abs(vals) >= abs(obs) - 1e-15))
    return obs, extreme / total


def wilson(k, n, z=1.959963984540054):
    if n == 0: return (math.nan, math.nan)
    p = k/n; den = 1 + z*z/n
    center = (p + z*z/(2*n))/den
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return center-half, center+half


def violin_points(ax, values, y, color, offset=0.0, width=0.28, seed=1, marker="o"):
    values = np.asarray(values, float); values = values[np.isfinite(values)]
    if len(values) < 2: return
    parts = ax.violinplot(values, positions=[y+offset], vert=False, widths=width,
                          showmeans=False, showmedians=False, showextrema=False)
    for body in parts["bodies"]:
        # Keep only the outer half of each cloud: positive offsets above,
        # negative offsets below. This matches Figures 2–5.
        center = y + offset
        vertices = body.get_paths()[0].vertices
        if offset > 0:
            vertices[:, 1] = np.maximum(vertices[:, 1], center)
        elif offset < 0:
            vertices[:, 1] = np.minimum(vertices[:, 1], center)
        body.set_facecolor(color); body.set_edgecolor("none"); body.set_alpha(0.28)
    rng = np.random.default_rng(seed)
    if offset > 0:
        jitter = rng.uniform(0, width*0.22, len(values))
    elif offset < 0:
        jitter = rng.uniform(-width*0.22, 0, len(values))
    else:
        jitter = rng.uniform(-width*0.22, width*0.22, len(values))
    if marker == "o":
        ax.scatter(values, y+offset+jitter, s=12, marker="o", facecolors="none", edgecolors=color, alpha=0.72, linewidth=0.55, zorder=3)
    else:
        ax.scatter(values, y+offset+jitter, s=13, marker=marker, color=color, alpha=0.72, linewidth=0.65, zorder=3)
    lo, hi = bootstrap_ci(values, np.mean, seed=seed)
    mean = float(np.mean(values))
    ax.plot([lo, hi], [y+offset]*2, color="#222222", lw=1.4, zorder=4)
    ax.scatter([mean], [y+offset], s=35, marker=marker,
               facecolors="white" if marker == "o" else "#222222",
               edgecolors="#222222", linewidth=1.0, zorder=5)


def save_panel(fig, name):
    fig.savefig(FIG / f"Figure 6 panel {name}.png", dpi=DPI, facecolor="white")
    fig.savefig(FIG / f"Figure 6 panel {name}.tiff", dpi=DPI, facecolor="white", pil_kwargs={"compression":"tiff_lzw"})
    fig.savefig(FIG / f"Figure 6 panel {name}.svg", facecolor="white")
    fig.savefig(FIG / f"Figure 6 panel {name}.pdf", facecolor="white")
    plt.close(fig)


def style_ax(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=TICK_SIZE, width=0.8)
    ax.grid(False)


def fixed_panel_layout(ax):
    """Use one identical square plotting box in every Figure 6 panel."""
    ax.set_position([0.32, 0.22, 0.54, 0.54])


def main():
    plt.rcParams.update({"font.family": FONT_FAMILY, "font.size": FONT_SIZE,
                         "axes.labelsize": LABEL_SIZE, "svg.fonttype": "none",
                         "pdf.fonttype": 42})
    outcomes = pd.read_csv(DATA / "outcomes.csv")
    outcomes["group"] = outcomes.condition_id.map(group_key)
    outcomes["load_label"] = outcomes.load.map({"absent":"Without recessive load", "present":"With recessive load"})
    weekly = pd.read_csv(DATA / "weekly_metrics.csv")

    stat_rows = []

    # Panel A: all runs, independent load comparison within each model/conversion row.
    a = outcomes[["condition_id","group","model","drive_conversion","load","replicate","seed","Nmin_relative","outcome"]].copy()
    a.to_csv(DATA / "Figure6_panelA_source_data.csv", index=False)
    panel_a_stats = []
    for i,g in enumerate(GROUP_ORDER):
        x=a[(a.group==g)&(a.load=="absent")].Nmin_relative.to_numpy()
        y=a[(a.group==g)&(a.load=="present")].Nmin_relative.to_numpy()
        est,p=independent_permutation(x,y,RNG_SEED+i)
        panel_a_stats.append(dict(panel="A",group=g,test="two-sided independent permutation test",
                                  estimand="mean(with load)-mean(without load)",estimate=est,
                                  n_without=len(x),n_with=len(y),p_raw=p))
    adj=holm([r["p_raw"] for r in panel_a_stats])
    for r,p in zip(panel_a_stats,adj): r.update(p_holm=p,symbol=p_symbol(p))
    stat_rows.extend(panel_a_stats)

    fig,ax=plt.subplots(figsize=PANEL_SIZE_INCH)
    ys=np.arange(len(GROUP_ORDER))[::-1]
    outcome_colors={"elimination":RAIN_ELIM,"drive_loss":RAIN_LOSS,"long_term_persistence":RAIN_LTP}
    for i,(g,y0) in enumerate(zip(GROUP_ORDER,ys)):
        for oi,(outcome,color) in enumerate(outcome_colors.items()):
            violin_points(ax,a[(a.group==g)&(a.load=="absent")&(a.outcome==outcome)].Nmin_relative,
                          y0,color,0.12,seed=100+i*10+oi,marker="o")
            violin_points(ax,a[(a.group==g)&(a.load=="present")&(a.outcome==outcome)].Nmin_relative,
                          y0,color,-0.12,seed=200+i*10+oi,marker="x")
    ax.set_yticks(ys, [GROUP_LABEL[g] for g in GROUP_ORDER])
    ax.set_xlim(0,1); ax.set_xticks([0,0.5,1.0])
    ax.set_xlabel("Minimum post-release\nrelative population size")
    from matplotlib.lines import Line2D
    handles=[Line2D([],[],marker="o",mfc="none",ls="",color="#222222",label="Without recessive load"),
             Line2D([],[],marker="x",ls="",color="#222222",label="With recessive load")]
    ax.legend(handles=handles,frameon=False,fontsize=13,loc="lower center",bbox_to_anchor=(0.58,1.01),ncol=1,labelspacing=.12,handletextpad=.35)
    style_ax(ax); fixed_panel_layout(ax); save_panel(fig,"A")

    # Panel B: exact outcome counts, Wilson intervals and load-state comparisons.
    cats=["elimination","drive_loss","long_term_persistence"]
    colors=[OUTCOME_ELIM,OUTCOME_LOSS,OUTCOME_LTP]
    b_rows=[]
    for g in GROUP_ORDER:
        for load in ["absent","present"]:
            sub=outcomes[(outcomes.group==g)&(outcomes.load==load)]
            for cat in cats:
                k=int((sub.outcome==cat).sum()); lo,hi=wilson(k,len(sub))
                b_rows.append(dict(group=g,group_label=GROUP_LABEL[g],load=load,outcome=cat,
                                   count=k,n=len(sub),fraction=k/len(sub),wilson95_low=lo,wilson95_high=hi))
    b=pd.DataFrame(b_rows); b.to_csv(DATA/"Figure6_panelB_source_data.csv",index=False)
    # Manuscript-prespecified outcome contrast: elimination in Panmictic–0.70 only.
    # The comparison is exploratory and therefore reported without multiplicity adjustment.
    panel_b_stats=[]
    g="P70"
    tab=[]
    for load in ["absent","present"]:
        sub=outcomes[(outcomes.group==g)&(outcomes.load==load)]
        tab.append([int((sub.outcome=="elimination").sum()),int((sub.outcome!="elimination").sum())])
    _,p=fisher_exact(np.asarray(tab),alternative="two-sided")
    panel_b_stats.append(dict(panel="B",group=g,test="two-sided Fisher exact test",
                              estimand="elimination versus all other outcomes by load state",
                              p_raw=p,p_holm=math.nan,symbol=p_symbol(p)))
    stat_rows.extend(panel_b_stats)
    fig,ax=plt.subplots(figsize=PANEL_SIZE_INCH)
    ys=np.arange(len(GROUP_ORDER))[::-1]
    for g,y0 in zip(GROUP_ORDER,ys):
        for load,off,hatch in [("absent",0.12,"///"),("present",-0.12,None)]:
            left=0
            for cat,col in zip(cats,colors):
                frac=float(b[(b.group==g)&(b.load==load)&(b.outcome==cat)].fraction.iloc[0])
                ax.barh(y0+off,frac,left=left,height=0.20,color=col,edgecolor="#333333",linewidth=0.5,hatch=hatch)
                left+=frac
    ax.set_yticks(ys,[GROUP_LABEL[g] for g in GROUP_ORDER]); ax.set_xlim(0,1)
    ax.set_xlabel("Outcome probability")
    from matplotlib.patches import Patch
    handles=[Patch(facecolor=OUTCOME_ELIM,edgecolor="#333",label="Elimination"),
             Patch(facecolor=OUTCOME_LOSS,edgecolor="#333",label="Drive loss"),
             Patch(facecolor=OUTCOME_LTP,edgecolor="#333",label="Long-term\npersistence")]
    handles += [Patch(facecolor="white",edgecolor="#333",hatch="///",label="Without recessive\nload"),Patch(facecolor="white",edgecolor="#333",label="With recessive\nload")]
    ax.legend(handles=handles,frameon=False,fontsize=12.5,ncol=2,loc="lower center",bbox_to_anchor=(0.5,.98),columnspacing=0.75,handlelength=1.1,handletextpad=.35)
    style_ax(ax); fixed_panel_layout(ax); save_panel(fig,"B")

    # Panel C: release-aligned B trajectories among load-present LTP runs.
    c=outcomes[(outcomes.load=="present")&(outcomes.outcome=="long_term_persistence")].copy()
    c=c[["condition_id","group","model","drive_conversion","replicate","seed","B_pre","B_post","fraction_B_removed","n_valid_B_pre","n_valid_B_post"]]
    c.to_csv(DATA/"Figure6_panelC_source_data.csv",index=False)
    # Panel C is a descriptive release-aligned trajectory in the manuscript.
    # No formal hypothesis tests are applied to repeated trajectory observations.
    eligible=c[["condition_id","replicate","seed","group"]].drop_duplicates()
    traj=weekly.merge(eligible,on=["condition_id","replicate","seed"],how="inner")
    traj=traj[traj.week_relative_release.between(-10,1500)&traj.B.notna()].copy()
    traj.to_csv(DATA/"Figure6_panelC_trajectory_source_data.csv",index=False)
    fig,ax=plt.subplots(figsize=PANEL_SIZE_INCH)
    trajectory_styles={
        "P70":("#7F7F7F","Panmictic dc-0.70"),
        "S70":("#C29A3A","Spatial dc-0.70"),
        "S85":("#BE7E4A","Spatial dc-0.85"),
    }
    for i,(g,(color,label)) in enumerate(trajectory_styles.items()):
        sub=traj[traj.group==g]
        if sub.empty:
            continue
        for _,run in sub.groupby(["replicate","seed"]):
            run=run.sort_values("week_relative_release")
            run=run.copy(); run["B_smooth"]=run.B.rolling(20,center=True,min_periods=1).mean()
            ax.plot(run.week_relative_release,run.B_smooth,color=color,lw=.35,alpha=.08,zorder=1)
        summary=(sub.groupby("week_relative_release").B
                 .agg(median="median",q05=lambda x:x.quantile(.05),q25=lambda x:x.quantile(.25),
                      q75=lambda x:x.quantile(.75),q95=lambda x:x.quantile(.95)).reset_index())
        for stat in ["median","q05","q25","q75","q95"]:
            summary[stat]=summary[stat].rolling(20,center=True,min_periods=1).mean()
        x=summary.week_relative_release.to_numpy(); med=summary["median"].to_numpy()
        ax.fill_between(x,summary.q05,summary.q95,color=color,alpha=.08,lw=0,zorder=2)
        ax.fill_between(x,summary.q25,summary.q75,color=color,alpha=.18,lw=0,zorder=3)
        ax.plot(x,med,color=color,lw=1.35,label=label,zorder=4)
    ax.axvline(0,color="#777777",ls=(0,(3,3)),lw=.8,zorder=0)
    ax.set_xlim(-10,1500); ax.set_xticks([0,500,1000,1500])
    ax.set_ylim(0.2,2.0); ax.set_yticks([0.5,1.0,1.5,2.0])
    ax.set_xlabel("Weeks after release"); ax.set_ylabel("Haploid inbreeding load, B")
    ax.legend(frameon=False,fontsize=LEGEND_SIZE-1,loc="upper right",ncol=1,columnspacing=.7,handlelength=1.5)
    style_ax(ax); fixed_panel_layout(ax); save_panel(fig,"C")

    # Panel D: LTP only, independent load comparison.
    d=outcomes[outcomes.outcome=="long_term_persistence"][["condition_id","group","model","drive_conversion","load","replicate","seed","N_long_term_relative"]].copy()
    d.to_csv(DATA/"Figure6_panelD_source_data.csv",index=False)
    panel_d_stats=[]
    for i,g in enumerate(GROUP_ORDER):
        x=d[(d.group==g)&(d.load=="absent")].N_long_term_relative.dropna().to_numpy()
        y=d[(d.group==g)&(d.load=="present")].N_long_term_relative.dropna().to_numpy()
        if len(x)==0 or len(y)==0:
            panel_d_stats.append(dict(panel="D",group=g,test="two-sided independent permutation test",estimand="mean(with load)-mean(without load)",estimate=math.nan,n_without=len(x),n_with=len(y),p_raw=math.nan))
        else:
            est,p=independent_permutation(x,y,RNG_SEED+600+i)
            panel_d_stats.append(dict(panel="D",group=g,test="two-sided independent permutation test",estimand="mean(with load)-mean(without load)",estimate=est,n_without=len(x),n_with=len(y),p_raw=p))
    adj=holm([r["p_raw"] for r in panel_d_stats])
    for r,p in zip(panel_d_stats,adj): r.update(p_holm=p,symbol=p_symbol(p))
    stat_rows.extend(panel_d_stats)
    fig,ax=plt.subplots(figsize=PANEL_SIZE_INCH)
    ys=np.arange(len(GROUP_ORDER))[::-1]
    for i,(g,y0) in enumerate(zip(GROUP_ORDER,ys)):
        x=d[(d.group==g)&(d.load=="absent")].N_long_term_relative
        y=d[(d.group==g)&(d.load=="present")].N_long_term_relative
        if len(x)==0 or len(y)==0:
            continue
        violin_points(ax,x,y0,RAIN_LTP,0.12,seed=700+i,marker="o")
        violin_points(ax,y,y0,RAIN_LTP,-0.12,seed=800+i,marker="x")
    ax.set_yticks(ys,[GROUP_LABEL[g] for g in GROUP_ORDER]); ax.set_xlabel("Relative population size\nover the last 20 weeks")
    ax.set_xlim(0,1); ax.set_xticks([0,0.5,1.0])
    ax.scatter([],[],marker="o",facecolors="none",edgecolors="#222222",label="Without recessive\nload"); ax.scatter([],[],marker="x",color="#222222",label="With recessive\nload")
    ax.legend(frameon=False,fontsize=LEGEND_SIZE,loc="lower center",bbox_to_anchor=(0.5,1.01),ncol=2,columnspacing=1.2)
    style_ax(ax); fixed_panel_layout(ax); save_panel(fig,"D")

    stats=pd.DataFrame(stat_rows)
    stats.to_csv(DATA/"figure6_statistics.csv",index=False,na_rep="NA")

    # Simulation-level descriptive table for transparent effect reporting.
    desc=[]
    for (g,load),sub in outcomes.groupby(["group","load"]):
        for metric in ["Nmin_relative","N_long_term_relative","B_pre","B_post","fraction_B_removed"]:
            x=sub[metric].dropna().to_numpy()
            lo,hi=bootstrap_ci(x,np.mean,seed=RNG_SEED+len(desc)) if len(x) else (math.nan,math.nan)
            desc.append(dict(group=g,load=load,metric=metric,n=len(x),mean=np.mean(x) if len(x) else math.nan,
                             median=np.median(x) if len(x) else math.nan,bootstrap_mean_ci_low=lo,bootstrap_mean_ci_high=hi))
    pd.DataFrame(desc).to_csv(DATA/"figure6_descriptive_summary.csv",index=False,na_rep="NA")
    print("Wrote four panel source-data files, statistics, summaries and PNG/SVG/PDF/TIFF panels.")


if __name__ == "__main__":
    main()

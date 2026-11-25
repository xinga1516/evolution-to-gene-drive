from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "文章终稿数据"
OUT = Path(os.environ.get("PANEL_OUTPUT_DIR", DATA / "final_panels_20260908"))
STATS = Path(os.environ.get("PANEL_STATS_DIR", ROOT.parent / "文章figure终版" / "LATEST_FINAL_PACKAGE" / "source_tables"))
# ---- Manual appearance controls ----
FIGSIZE = tuple(float(x) for x in os.environ.get("PANEL_FIGSIZE", "4.50,4.00").split(","))
DPI = int(os.environ.get("PANEL_DPI", "600"))
FONT_FAMILY = os.environ.get("PANEL_FONT_FAMILY", "Arial")
BASE_FONT_SIZE = float(os.environ.get("PANEL_FONT_SIZE", "10.5"))
AXIS_LABEL_SIZE = float(os.environ.get("PANEL_AXIS_LABEL_SIZE", "12"))
TICK_LABEL_SIZE = float(os.environ.get("PANEL_TICK_LABEL_SIZE", "10.5"))
LEGEND_FONT_SIZE = float(os.environ.get("PANEL_LEGEND_FONT_SIZE", "9.5"))
ANNOTATION_FONT_SIZE = float(os.environ.get("PANEL_ANNOTATION_FONT_SIZE", "9.0"))
SIGNIFICANCE_FONT_SIZE = float(os.environ.get("PANEL_SIGNIFICANCE_FONT_SIZE", "10.5"))
OUTCOME_LEGEND_FONT_SIZE = float(os.environ.get("PANEL_OUTCOME_LEGEND_FONT_SIZE", "8.0"))
PANEL_LABEL_FONT_SIZE = float(os.environ.get("PANEL_LABEL_FONT_SIZE", "14"))
SHOW_PANEL_LABELS = os.environ.get("SHOW_PANEL_LABELS", "0") == "1"
NEUTRAL = "#8C8C8C"
VARIABLE = "#C29A3A"
NEUTRAL_LIGHT = "#C5C5C5"
VARIABLE_LIGHT = "#86B6D8"
GREEN = "#8C8C8C"
# Panel-C trajectory palette: parameter family is encoded by hue and
# treatment by saturation, matching the previously approved version.
TRAJ_LOW_CONTROL = "#86B6D8"
TRAJ_LOW_VARIATION = "#2878B5"
TRAJ_HIGH_CONTROL = "#F4B87A"
TRAJ_HIGH_VARIATION = "#E66B13"
OUTCOME_COLORS = {"Elimination":"#E66101", "Drive loss":"#CC79A7", "Long-term persistence":"#56B4E9"}
TREATMENT_DISPLAY = {"Neutral control":"Neutral mutations", "Functional modifier":"Variable mutations"}


mpl.rcParams.update({
    "font.family":FONT_FAMILY, "font.size":BASE_FONT_SIZE, "axes.labelsize":AXIS_LABEL_SIZE,
    "xtick.labelsize":TICK_LABEL_SIZE, "ytick.labelsize":TICK_LABEL_SIZE, "legend.fontsize":LEGEND_FONT_SIZE,
    "axes.linewidth":0.8, "pdf.fonttype":42, "ps.fonttype":42,
    "savefig.transparent":False,
})


def pstar(p):
    if not np.isfinite(p): return None
    if p < .001: return "***"
    if p < .01: return "**"
    if p < .05: return "*"
    return "ns"


def new_ax(letter):
    fig,ax=plt.subplots(figsize=FIGSIZE,dpi=DPI)
    fig.subplots_adjust(left=.23,right=.96,bottom=.20,top=.91)
    if SHOW_PANEL_LABELS:
        ax.text(-.20,1.055,letter,transform=ax.transAxes,fontsize=PANEL_LABEL_FONT_SIZE,fontweight="bold",ha="left",va="top")
    ax.spines[["top","right"]].set_visible(False)
    return fig,ax


def save(fig, fig_no, letter):
    d=OUT/f"Figure{fig_no}"; d.mkdir(parents=True,exist_ok=True)
    stem=d/f"Figure {fig_no} Panel {letter}"
    fig.savefig(stem.with_suffix(".png"),dpi=DPI,facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"),facecolor="white")
    fig.savefig(stem.with_suffix(".svg"),facecolor="white")
    plt.close(fig)


def bootstrap_mean(x,seed,b=10000):
    x=np.asarray(x,float); x=x[np.isfinite(x)]
    if len(x)==0:return np.nan,np.nan,np.nan
    if len(x)==1:return x[0],np.nan,np.nan
    rng=np.random.default_rng(seed); vals=[]
    for i in range(0,b,1000): vals.append(rng.choice(x,(min(1000,b-i),len(x)),replace=True).mean(1))
    return float(x.mean()),*map(float,np.percentile(np.concatenate(vals),[2.5,97.5]))


def half_violin_horizontal(ax, values, y, color, side, width=.31):
    values=np.asarray(values,float); values=values[np.isfinite(values)]
    if len(values)<2:return
    v=ax.violinplot(values,positions=[y],vert=False,widths=width,showextrema=False)
    body=v["bodies"][0]; body.set_facecolor(color); body.set_edgecolor("none"); body.set_alpha(.26)
    verts=body.get_paths()[0].vertices
    if side=="upper": verts[:,1]=np.maximum(verts[:,1],y)
    else: verts[:,1]=np.minimum(verts[:,1],y)


def raincloud_horizontal(ax, data, value, order, xlabel, stars=None, xline=None):
    rng=np.random.default_rng(20260908)
    for yi,cond in enumerate(order):
        for tr,off,side,col in [("Neutral control",-.12,"lower",NEUTRAL),("Functional modifier",.12,"upper",VARIABLE)]:
            vals=pd.to_numeric(data[(data.condition==cond)&(data.treatment==tr)][value],errors="coerce").dropna().to_numpy()
            half_violin_horizontal(ax,vals,yi+off,col,side)
            if len(vals):
                jitter=rng.uniform(-.045,.045,len(vals)); ax.scatter(vals,np.full(len(vals),yi+off)+jitter,s=7,c=col,alpha=.34,lw=0,zorder=2)
                mean,lo,hi=bootstrap_mean(vals,2026090800+yi+(tr=="Functional modifier"))
                if np.isfinite(lo): ax.errorbar(mean,yi+off,xerr=[[mean-lo],[hi-mean]],fmt="o",ms=4.5,mfc=col,mec="white",mew=.7,color=col,lw=1.0,capsize=2,zorder=4)
                else: ax.scatter([mean],[yi+off],s=22,c=col,edgecolor="white",lw=.7,zorder=4)
        if stars and stars.get(cond): ax.text(.985,yi,stars[cond],transform=ax.get_yaxis_transform(),ha="right",va="center",fontsize=SIGNIFICANCE_FONT_SIZE,fontweight="bold")
    if xline is not None: ax.axvline(xline,color="#777777",ls=(0,(3,3)),lw=.8,zorder=0)
    ax.set_yticks(range(len(order)),order); ax.invert_yaxis(); ax.set_xlabel(xlabel)
    ax.legend(handles=[Line2D([],[],marker="o",ls="",color=NEUTRAL,label="Neutral mutations"),Line2D([],[],marker="o",ls="",color=VARIABLE,label="Variable mutations")],frameon=False,loc="lower center",bbox_to_anchor=(.5,1.0),ncol=2,handletextpad=.3,columnspacing=.8)


def trajectory_panel(ax, summary, xlabel, ylabel, labels, colors, linestyles=None):
    linestyles=linestyles or {}
    for key,label in labels.items():
        h,tr=key; g=summary[np.isclose(summary.h,h)&(summary.treatment==tr)].sort_values("week")
        if g.empty: continue
        x=g.week.to_numpy(); med=g["median"].to_numpy(); lo=g.q25.to_numpy(); hi=g.q75.to_numpy()
        ax.fill_between(x,lo,hi,color=colors[key],alpha=.16,lw=0)
        ax.plot(x,med,color=colors[key],lw=1.4,ls=linestyles.get(key,"-"),label=label)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.legend(frameon=False,loc="best",handlelength=2.1)


def outcome_panel(ax, table, order, stars=None):
    ax.figure.subplots_adjust(top=.72)
    height=.27; offsets={"Neutral control":-.17,"Functional modifier":.17}
    for yi,cond in enumerate(order):
        for tr in ["Neutral control","Functional modifier"]:
            g=table[(table.condition==cond)&(table.treatment==tr)].set_index("outcome")
            left=0
            for outcome in ["Elimination","Drive loss","Long-term persistence"]:
                val=float(g.loc[outcome,"probability"]) if outcome in g.index else 0
                if val>0: ax.barh(yi+offsets[tr],val,left=left,height=height,color=OUTCOME_COLORS[outcome],edgecolor="#333333",lw=.35,hatch="///" if tr=="Neutral control" else None)
                left+=val
        if stars and stars.get(cond): ax.text(.985,yi,stars[cond],transform=ax.get_yaxis_transform(),ha="right",va="center",fontsize=SIGNIFICANCE_FONT_SIZE,fontweight="bold")
    ax.set_xlim(0,1.0); ax.set_yticks(range(len(order)),order); ax.invert_yaxis(); ax.set_xlabel("Outcome probability")
    handles=[Patch(facecolor=c,edgecolor="#333",label=o) for o,c in OUTCOME_COLORS.items()]
    handles += [Patch(facecolor="white",edgecolor="#333",hatch="///",label="Neutral mutations"),Patch(facecolor="white",edgecolor="#333",label="Variable mutations")]
    ax.legend(handles=handles,frameon=False,loc="lower center",bbox_to_anchor=(.5,1.01),ncol=2,columnspacing=.6,handlelength=1.1,fontsize=OUTCOME_LEGEND_FONT_SIZE)


def load_s1_stars(figure, panels):
    d=pd.read_csv(STATS/"S1_continuous_tests.csv"); out={}
    for display_panel,source_panel in panels.items():
        g=d[d["Figure/panel"]==f"Figure {figure}{source_panel}"]
        out[display_panel]={}
        for _,r in g.iterrows():
            cond=str(r.Regime).replace("Panmictic","Pan").replace("Spatial","Spa").replace(" ","–")
            sig=r.Significance
            out[display_panel][cond]=None if pd.isna(sig) or str(sig).strip().upper() in {"NA", "NAN", ""} else str(sig)
    return out


def load_outcome_stars(figure):
    d=pd.read_csv(STATS/"S2_outcome_global.csv"); g=d[d["Figure/panel"]==f"Figure {figure}D"]
    return {str(r.Regime).replace("Panmictic","Pan").replace("Spatial","Spa").replace(" ","–"):str(r.Significance) for _,r in g.iterrows()}


def draw_figure2():
    d=DATA/"Figure2"/"processed_source"; ep=pd.read_csv(d/"Figure2_source_endpoint_simulation_level.csv"); nni=pd.read_csv(d/"Figure2_source_panelB_NNI_summary.csv").rename(columns={"conversion":"h"}); out=pd.read_csv(d/"Figure2_source_panelD_outcomes.csv")
    ep["condition"]=ep.condition.str.replace("Spatial","Spa").str.replace("Pan-","Pan–",regex=False).str.replace("Spa-","Spa–",regex=False); out["condition"]=out.condition.str.replace("Spatial","Spa").str.replace("Pan-","Pan–",regex=False).str.replace("Spa-","Spa–",regex=False)
    order=["Pan–0.70","Pan–0.85","Spa–0.70","Spa–0.85"]; s=load_s1_stars(2,{"A":"A","B":"C"})
    fig,ax=new_ax("A"); raincloud_horizontal(ax,ep[ep.persistence.astype(bool)],"endpoint_modifier_clipped",order,"Final conversion",s["A"]); save(fig,2,"A")
    fig,ax=new_ax("B"); raincloud_horizontal(ax,ep[ep.persistence.astype(bool)],"n_over_k",order,"Relative long-term population size",s["B"]); save(fig,2,"B")
    fig,ax=new_ax("C"); labels={(.70,"Neutral control"):"0.70–Neutral",(.70,"Functional modifier"):"0.70–Variation",(.85,"Neutral control"):"0.85–Neutral",(.85,"Functional modifier"):"0.85–Variation"}; colors={(.70,"Neutral control"):TRAJ_LOW_CONTROL,(.70,"Functional modifier"):TRAJ_LOW_VARIATION,(.85,"Neutral control"):TRAJ_HIGH_CONTROL,(.85,"Functional modifier"):TRAJ_HIGH_VARIATION}; trajectory_panel(ax,nni,"Weeks after release","Nearest-neighbor index (NNI)",labels,colors); save(fig,2,"C")
    fig,ax=new_ax("D"); outcome_panel(ax,out,order,load_outcome_stars(2)); save(fig,2,"D")


def normalize_cond(s):
    return str(s).replace("Panmictic ","Pan–").replace("Spatial ","Spa–")


def scatter_association(ax, assoc, ptext, emp=False, ylabel="Final somatic fitness\n(Variable mutations)"):
    for _,r in assoc.iterrows():
        is_emp=emp and (str(r.get("parameter_source",""))=="Emp" or abs(float(r.h)-.99)<1e-9)
        marker="D" if is_emp else "o"; label="Emp" if is_emp else f"{float(r.h):.2f}"
        point_color=VARIABLE if is_emp else GREEN
        ax.errorbar(r.control_nni_mean,r.functional_final_attribute_mean,xerr=[[r.control_nni_mean-r.control_nni_lo],[r.control_nni_hi-r.control_nni_mean]],yerr=[[r.functional_final_attribute_mean-r.functional_final_attribute_lo],[r.functional_final_attribute_hi-r.functional_final_attribute_mean]],fmt=marker,ms=5.2,color=point_color,mec="white",mew=.7,capsize=2,lw=.8)
        bold=is_emp or abs(float(r.h)-.70)<1e-9
        ax.annotate(label,(r.control_nni_mean,r.functional_final_attribute_mean),xytext=(4,4),textcoords="offset points",fontsize=ANNOTATION_FONT_SIZE,fontweight="bold" if bold else "normal")
    ax.axhline(.5,color="#777",ls=(0,(3,3)),lw=.8)
    ax.set_xlabel("Mean final-100-week NNI\n(Neutral mutations)"); ax.set_ylabel(ylabel)
    ax.text(.98,.04 if emp else .98,ptext,transform=ax.transAxes,ha="right",va="bottom" if emp else "top",fontsize=ANNOTATION_FONT_SIZE)
    if emp: ax.legend(handles=[Line2D([],[],marker="o",ls="",color=GREEN,label="Systematic scan"),Line2D([],[],marker="D",ls="",color=VARIABLE,label="Emp")],frameon=False,loc="best")


def draw_figure3():
    d=DATA/"Figure3"/"processed_source"; ep=pd.read_csv(d/"Figure3_source_endpoint_simulation_level.csv"); nni=pd.read_csv(d/"Figure3_source_panelC_NNI_summary.csv"); out=pd.read_csv(d/"Figure3_source_panelD_outcomes.csv"); assoc=pd.read_csv(d/"Figure3_source_panelE_association.csv"); test=pd.read_csv(d/"Figure3_panelE_exact_spearman.csv").iloc[0]
    ep["condition"]=ep.condition.map(normalize_cond); out["condition"]=out.condition.map(normalize_cond); order=["Pan–0.70","Pan–0.85","Spa–0.70","Spa–0.85"]; s=load_s1_stars(3,{"A":"A","B":"B"})
    fig,ax=new_ax("A"); raincloud_horizontal(ax,ep[ep.persistent.astype(bool)],"endpoint_modifier_clipped",order,"Final embryo resistance",s["A"]); save(fig,3,"A")
    fig,ax=new_ax("B"); raincloud_horizontal(ax,ep[ep.persistent.astype(bool)],"n_over_k",order,"Relative long-term population size",s["B"]); save(fig,3,"B")
    fig,ax=new_ax("C"); labels={(.70,"Neutral control"):"0.70–Neutral",(.70,"Functional modifier"):"0.70–Variation",(.85,"Neutral control"):"0.85–Neutral",(.85,"Functional modifier"):"0.85–Variation"}; colors={(.70,"Neutral control"):TRAJ_LOW_CONTROL,(.70,"Functional modifier"):TRAJ_LOW_VARIATION,(.85,"Neutral control"):TRAJ_HIGH_CONTROL,(.85,"Functional modifier"):TRAJ_HIGH_VARIATION}; trajectory_panel(ax,nni,"Weeks after release","Nearest-neighbor index (NNI)",labels,colors); save(fig,3,"C")
    fig,ax=new_ax("D"); outcome_panel(ax,out,order,load_outcome_stars(3)); save(fig,3,"D")
    fig,ax=new_ax("E"); scatter_association(ax,assoc,f"Spearman ρ={test.rho:.2f}\nP={test.p_value:.4g}",ylabel="Final embryo resistance\n(Variable mutations)"); save(fig,3,"E")


def draw_figure4():
    d=DATA/"Figure4"/"processed_source_final"; ep=pd.read_csv(d/"Figure4_source_endpoint_simulation_level.csv"); nni=pd.read_csv(d/"Figure4_source_panelC_NNI_summary.csv"); out=pd.read_csv(d/"Figure4_source_panelD_outcomes.csv"); assoc=pd.read_csv(d/"Figure4_source_panelE_association.csv"); tests=pd.read_csv(d/"Figure4_continuous_tests.csv"); dt=pd.read_csv(d/"Figure4_panelD_tests.csv"); et=pd.read_csv(d/"Figure4_panelE_exact_spearman.csv").iloc[0]
    mapc={"Panmictic 0.70":"Pan–0.70","Panmictic Emp":"Pan–Emp","Spatial 0.70":"Spa–0.70","Spatial Emp":"Spa–Emp"}; ep["condition"]=ep.condition.map(mapc); out["condition"]=out.condition.map(mapc); order=list(mapc.values())
    stars={panel:{mapc.get(r.condition):pstar(r.raw_p) for _,r in tests[tests.panel==panel].iterrows() if mapc.get(r.condition)} for panel in ["A","B"]}; dstars={mapc.get(r.condition):pstar(r.raw_p) for _,r in dt.iterrows()}
    fig,ax=new_ax("A"); raincloud_horizontal(ax,ep[ep.persistent.astype(bool)],"endpoint_attribute_clipped",order,"Final somatic fitness",stars["A"],xline=.5); save(fig,4,"A")
    fig,ax=new_ax("B"); raincloud_horizontal(ax,ep[ep.persistent.astype(bool)],"n_over_k",order,"Relative long-term population size",stars["B"]); save(fig,4,"B")
    fig,ax=new_ax("C"); labels={(.70,"Neutral control"):"0.70–Neutral",(.70,"Functional modifier"):"0.70–Variation",(.99,"Neutral control"):"Emp–Neutral",(.99,"Functional modifier"):"Emp–Variation"}; colors={(.70,"Neutral control"):TRAJ_LOW_CONTROL,(.70,"Functional modifier"):TRAJ_LOW_VARIATION,(.99,"Neutral control"):TRAJ_HIGH_CONTROL,(.99,"Functional modifier"):TRAJ_HIGH_VARIATION}; trajectory_panel(ax,nni,"Weeks after release","Nearest-neighbor index (NNI)",labels,colors); save(fig,4,"C")
    fig,ax=new_ax("D"); outcome_panel(ax,out,order,dstars); save(fig,4,"D")
    fig,ax=new_ax("E"); scatter_association(ax,assoc,f"Spearman ρ={et.rho:.2f}\nP={et.p_value:.4g}",emp=True); save(fig,4,"E")


def half_violin_vertical(ax,vals,x,color,side,width=.34):
    vals=np.asarray(vals,float); vals=vals[np.isfinite(vals)]
    if len(vals)<2:return
    v=ax.violinplot(vals,positions=[x],widths=width,showextrema=False); b=v["bodies"][0]; b.set_facecolor(color); b.set_edgecolor("none"); b.set_alpha(.28); verts=b.get_paths()[0].vertices
    verts[:,0]=np.minimum(verts[:,0],x) if side=="left" else np.maximum(verts[:,0],x)


def draw_f5_panel(letter,trait,mode):
    d=DATA/"Figure5"/"processed_source_final"; sm=pd.read_csv(d/"Figure5_setting_summary.csv"); e=pd.read_csv(d/"Figure5_LTP_simulation_level_source.csv"); tests=pd.read_csv(d/"Figure5_statistical_tests.csv"); g=sm[sm.trait==trait].copy(); rng=np.random.default_rng(20260908); fig,ax=new_ax(letter)
    if mode=="magnitude":
        bmin=g.b.min(); left=g[g.m==50].sort_values("property_initial_sd").copy(); left["stratum"]=range(5); right=g[np.isclose(g.b,bmin)].sort_values("property_initial_sd").copy(); right["stratum"]=range(5)
        for k in range(5):
            for rr,side,col in [(left.iloc[k],"left",VARIABLE),(right.iloc[k],"right","#F28E72")]:
                vals=e[e.group_id==rr.group_id].final_attribute_mean_last10.dropna().to_numpy(); half_violin_vertical(ax,vals,k,col,side); jit=rng.uniform(-.08,.08,len(vals)); jit=np.minimum(jit,0) if side=="left" else np.maximum(jit,0); ax.scatter(k+jit,vals,s=5,c=col,alpha=.28,lw=0); mean,lo,hi=bootstrap_mean(vals,2026091400+k+(side=="right")); ax.errorbar(k,mean,yerr=[[mean-lo],[hi-mean]],fmt="o",ms=4.8,color=col,mfc=col,mec="white",mew=.7,capsize=2)
        ax.set_xticks(range(5),[f"{x:.3f}" for x in left.property_initial_sd]); ax.set_xlabel("Prespecified initial-SD stratum"); ax.legend(handles=[Line2D([],[],marker="o",ls="",color=VARIABLE,label="Fixed m=50"),Line2D([],[],marker="o",ls="",color="#F28E72",label="Fixed b=bmin")],frameon=False,loc="lower center",bbox_to_anchor=(.5,1),ncol=2)
    else:
        arch=g[g.is_highest_target_boundary.astype(bool)].sort_values("m")
        for k,(_,rr) in enumerate(arch.iterrows()):
            vals=e[e.group_id==rr.group_id].final_attribute_mean_last10.dropna().to_numpy(); v=ax.violinplot(vals,positions=[k],widths=.58,showextrema=False); v["bodies"][0].set_facecolor(GREEN); v["bodies"][0].set_edgecolor("none"); v["bodies"][0].set_alpha(.28); ax.scatter(k+rng.uniform(-.10,.10,len(vals)),vals,s=5,c=GREEN,alpha=.28,lw=0); mean,lo,hi=bootstrap_mean(vals,2026091500+k); ax.errorbar(k,mean,yerr=[[mean-lo],[hi-mean]],fmt="o",ms=5,color=GREEN,mec="white",mew=.7,capsize=2)
        ax.set_xticks(range(5),[f"m={int(r.m)}\nb={r.b:.4g}" for _,r in arch.iterrows()],rotation=28,ha="right"); ax.set_xlabel("Architecture gradient")
    ylabel={"dc":"Final conversion","er":"Final embryo resistance","sf":"Final somatic fitness"}[trait]; ax.set_ylabel(ylabel)
    p=float(tests[(tests.panel==letter)&(tests.test=="Permutation one-way ANOVA")].p_value.iloc[0]); ax.text(.98,.98,pstar(p),transform=ax.transAxes,ha="right",va="top",fontweight="bold",fontsize=SIGNIFICANCE_FONT_SIZE)
    save(fig,5,letter)


def draw_figure5():
    for letter,trait,mode in [("A","dc","magnitude"),("B","er","magnitude"),("C","sf","magnitude"),("D","dc","architecture"),("E","er","architecture"),("F","sf","architecture")]: draw_f5_panel(letter,trait,mode)


if __name__=="__main__":
    import sys
    requested = set(sys.argv[1:])
    if not requested or "2" in requested: draw_figure2()
    if not requested or "3" in requested: draw_figure3()
    if not requested or "4" in requested: draw_figure4()
    if not requested or "5" in requested: draw_figure5()
    print("Panels written to",OUT)

from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
F5 = ROOT / "文章终稿数据" / "figure2-5_final_panel_packages_20260908" / "Figure 5"
DATA = F5 / "data" / "Figure5_LTP_simulation_level_source.csv"
OUT = F5 / "common_support_replot"
PANELS, TABLES, DIAG = OUT / "panels", OUT / "statistics", OUT / "diagnostics"
for d in (OUT, PANELS, TABLES, DIAG): d.mkdir(parents=True, exist_ok=True)

TRAITS = {
    "dc": ("A", "Final drive conversion", 0.0048),
    "er": ("B", "Final embryo resistance", 0.0140),
    "sf": ("C", "Final female heterozygote fitness", 0.0113),
}
# Keep the established blue/red encoding while increasing saturation for
# projection and print legibility.
COLORS = {"fixed_m": "#5F8FCB", "fixed_b": "#D98A98"}
mpl.rcParams.update({"font.family":"Arial", "font.size":10, "axes.labelsize":11,
                     "xtick.labelsize":9, "ytick.labelsize":9, "legend.fontsize":9,
                     "axes.linewidth":.8, "pdf.fonttype":42, "ps.fonttype":42})


def fmt_p(p): return "P < 0.0001" if p < 1e-4 else f"P = {p:.4f}"

def holm(pvals):
    p=np.asarray(pvals,float); order=np.argsort(p); out=np.empty(len(p)); running=0.
    for rank,idx in enumerate(order):
        running=max(running,(len(p)-rank)*p[idx]); out[idx]=min(1.,running)
    return out


def select_paths(raw, trait, bmin):
    g = raw[raw.trait.eq(trait)].copy()
    # The shared m=50,b=bmin setting cannot identify a path effect. Exclude it
    # from both path-comparison arms, leaving four mutually exclusive settings
    # per path. It is plotted once as a separate shared anchor.
    fm = g[g.m.eq(50) & ~np.isclose(g.b, bmin)].copy(); fm["Path"] = "fixed_m"
    fb = g[np.isclose(g.b, bmin) & ~g.m.eq(50)].copy(); fb["Path"] = "fixed_b"
    d = pd.concat([fm, fb], ignore_index=True).rename(columns={
        "realised_initial_sd_last10_prerelease":"realized_sd",
        "final_attribute_mean_last10":"endpoint"}).dropna(subset=["realized_sd","endpoint"])
    assert not d.duplicated(["group_id","replicate"]).any()
    return d


def matrix(d, interaction=True):
    pb = d.Path.eq("fixed_b").astype(float)
    x = pd.DataFrame({"const":1., "SD_001":d.SD_001, "Path_fixed_b":pb})
    if interaction: x["SD_001_x_Path"] = d.SD_001 * pb
    return x


class HC3Result:
    def __init__(self, y, X):
        self.names=list(X.columns); xm=X.to_numpy(float); y=np.asarray(y,float)
        xtx_inv=np.linalg.inv(xm.T@xm); beta=xtx_inv@xm.T@y; fitted=xm@beta; resid=y-fitted
        hat=np.einsum("ij,jk,ik->i",xm,xtx_inv,xm); scaled=resid/(1-hat)
        meat=xm.T@((scaled[:,None]**2)*xm); cov=xtx_inv@meat@xtx_inv
        se=np.sqrt(np.diag(cov)); z=beta/se; p=2*stats.norm.sf(np.abs(z))
        self.params=pd.Series(beta,index=self.names); self._cov=cov; self.bse=pd.Series(se,index=self.names)
        self.pvalues=pd.Series(p,index=self.names); self.fittedvalues=pd.Series(fitted); self.resid=pd.Series(resid)
    def cov_params(self): return pd.DataFrame(self._cov,index=self.names,columns=self.names)
    def conf_int(self):
        return pd.DataFrame(np.column_stack([self.params-1.96*self.bse,self.params+1.96*self.bse]),index=self.names)

def fit(d, interaction=True): return HC3Result(d.endpoint, matrix(d, interaction))


def combo(model, w):
    w=np.asarray(w,float); beta=model.params.to_numpy(float); cov=np.asarray(model.cov_params(),float)
    est=float(w@beta); se=float(np.sqrt(w@cov@w)); p=float(2*stats.norm.sf(abs(est/se)))
    return est, est-1.96*se, est+1.96*se, p

def joint_wald(model, restrictions):
    R=np.asarray(restrictions,float); beta=model.params.to_numpy(float); cov=np.asarray(model.cov_params(),float)
    q=R@beta; middle=R@cov@R.T; stat=float(q.T@np.linalg.inv(middle)@q)
    df=int(R.shape[0]); p=max(float(stats.chi2.sf(stat,df)),1e-300)
    return stat,df,p


def predict(model, values, ref, path, interaction):
    z=(np.asarray(values)-ref)/.01; pb=float(path=="fixed_b")
    X=np.column_stack([np.ones_like(z),z,np.full_like(z,pb)] + ([z*pb] if interaction else []))
    mean=X@model.params.to_numpy(float); cov=np.asarray(model.cov_params(),float)
    se=np.sqrt(np.einsum("ij,jk,ik->i",X,cov,X))
    return mean,mean-1.96*se,mean+1.96*se


def cors(d,path):
    g=d[d.Path.eq(path)]; pr=stats.pearsonr(g.realized_sd,g.endpoint); sr=stats.spearmanr(g.realized_sd,g.endpoint)
    return len(g),float(pr.statistic),float(pr.pvalue),float(sr.statistic),float(sr.pvalue)

def descriptive_path(raw, trait, bmin, path):
    g=raw[raw.trait.eq(trait)].copy()
    g=g[g.m.eq(50)] if path=="fixed_m" else g[np.isclose(g.b,bmin)]
    return g.rename(columns={"realised_initial_sd_last10_prerelease":"realized_sd","final_attribute_mean_last10":"endpoint"}).dropna(subset=["realized_sd","endpoint"])


def main():
    raw=pd.read_csv(DATA); summaries=[]; contrasts=[]; coefficients=[]; sensitivities=[]; diagnostics=[]; payload={}
    for trait,(letter,ylabel,bmin) in TRAITS.items():
        full=select_paths(raw,trait,bmin); ranges=full.groupby("Path").realized_sd.agg(["min","max"])
        low=float(ranges["min"].max()); high=float(ranges["max"].min())
        common=full[full.realized_sd.between(low,high)].copy(); ref=float(common.realized_sd.median())
        for d in (full,common): d["SD_001"]=(d.realized_sd-ref)/.01
        im=fit(common,True); ip=float(im.pvalues["SD_001_x_Path"])
        # The biologically prespecified full interaction model remains primary
        # for every trait; no significance-driven model reduction is used.
        model=im; retain=True
        fm=combo(im,[0,1,0,0]); fb=combo(im,[0,1,0,1]); ds=combo(im,[0,0,0,1])
        pe,plo,phi,pp=combo(im,[0,0,1,0])
        rs_stat,rs_df,rs_p=joint_wald(im,[[0,1,0,0],[0,0,0,1]])
        ar_stat,ar_df,ar_p=joint_wald(im,[[0,0,1,0],[0,0,0,1]])
        dm=descriptive_path(raw,trait,bmin,"fixed_m"); dm["Path"]="fixed_m"
        db=descriptive_path(raw,trait,bmin,"fixed_b"); db["Path"]="fixed_b"
        cfm,cbr=cors(dm,"fixed_m"),cors(db,"fixed_b")
        nf=full.groupby("Path").size(); nc=common.groupby("Path").size()
        summaries.append(dict(trait=trait,n_fixed_m_full=int(nf.fixed_m),n_fixed_b_full=int(nf.fixed_b),
            fixed_m_sd_min=float(ranges.loc["fixed_m","min"]),fixed_m_sd_max=float(ranges.loc["fixed_m","max"]),
            fixed_b_sd_min=float(ranges.loc["fixed_b","min"]),fixed_b_sd_max=float(ranges.loc["fixed_b","max"]),
            common_support_min=low,common_support_max=high,n_fixed_m_common=int(nc.get("fixed_m",0)),
            n_fixed_b_common=int(nc.get("fixed_b",0)),pct_fixed_m_retained=100*nc.get("fixed_m",0)/nf.fixed_m,
            pct_fixed_b_retained=100*nc.get("fixed_b",0)/nf.fixed_b,SD_reference_median=ref,
            pearson_r_fixed_m=cfm[1],pearson_p_fixed_m=cfm[2],spearman_rho_fixed_m=cfm[3],spearman_p_fixed_m=cfm[4],
            pearson_r_fixed_b=cbr[1],pearson_p_fixed_b=cbr[2],spearman_rho_fixed_b=cbr[3],spearman_p_fixed_b=cbr[4],
            slope_fixed_m_per_0_01=fm[0],slope_fixed_m_CI_low=fm[1],slope_fixed_m_CI_high=fm[2],slope_fixed_m_p=fm[3],
            slope_fixed_b_per_0_01=fb[0],slope_fixed_b_CI_low=fb[1],slope_fixed_b_CI_high=fb[2],slope_fixed_b_p=fb[3],
            delta_slope=ds[0],delta_slope_CI_low=ds[1],delta_slope_CI_high=ds[2],interaction_p_raw=ip,
            delta_slope_p=ds[3],path_offset_reference_SD=pe,path_offset_CI_low=plo,path_offset_CI_high=phi,path_offset_p=pp,
            realized_SD_Wald_stat=rs_stat,realized_SD_Wald_df=rs_df,realized_SD_p_raw=rs_p,
            architecture_Wald_stat=ar_stat,architecture_Wald_df=ar_df,architecture_p_raw=ar_p,
            retained_model="full_interaction"))
        for term,v in (("fixed_m_slope_per_0.01",fm),("fixed_b_slope_per_0.01",fb),("fixed_b_minus_fixed_m_slope",ds)):
            coefficients.append(dict(trait=trait,model="interaction",term=term,estimate=v[0],CI_low=v[1],CI_high=v[2],p_value=v[3]))
        for term in model.params.index:
            ci=model.conf_int().loc[term]
            coefficients.append(dict(trait=trait,model="primary_full_interaction",term=term,
                estimate=float(model.params[term]),CI_low=float(ci.iloc[0]),CI_high=float(ci.iloc[1]),p_value=float(model.pvalues[term])))
        q=np.quantile(common.realized_sd,[.25,.5,.75]); vals=[]
        for name,x in zip(("low","mid","high"),q):
            z=(x-ref)/.01; w=[0,0,1,z]; v=combo(model,w); vals.append(v[3])
            contrasts.append(dict(trait=trait,quantile=name,realized_sd=x,fixed_b_minus_fixed_m=v[0],CI_low=v[1],CI_high=v[2],p_raw=v[3]))
        adj=holm(vals)
        for row,padj in zip(contrasts[-3:],adj): row["p_Holm"]=float(padj)
        fullm=fit(full,True); frs=joint_wald(fullm,[[0,1,0,0],[0,0,0,1]]); far=joint_wald(fullm,[[0,0,1,0],[0,0,0,1]])
        sensitivities.append(dict(trait=trait,slope_fixed_m=float(fullm.params.SD_001),
            slope_fixed_b=float(fullm.params.SD_001+fullm.params.SD_001_x_Path),delta_slope=float(fullm.params.SD_001_x_Path),
            interaction_p=float(fullm.pvalues.SD_001_x_Path),realized_SD_Wald_stat=frs[0],realized_SD_p=frs[2],
            architecture_Wald_stat=far[0],architecture_p=far[2]))
        resid=model.resid.to_numpy(); fitted=model.fittedvalues.to_numpy()
        diagnostics.append(dict(trait=trait,model_formula="endpoint ~ SD_001 * Path",covariance="HC3",
            n=len(common),design_rank=int(np.linalg.matrix_rank(matrix(common,True).to_numpy(float))),
            condition_number=float(np.linalg.cond(matrix(common,True).to_numpy(float))),
            common_support_min=low,common_support_max=high,SD_reference_median=ref))
        fig,a=plt.subplots(1,3,figsize=(10,3)); a[0].scatter(fitted,resid,s=7,alpha=.35); a[0].axhline(0,color="#555",ls="--",lw=.8)
        a[0].set(xlabel="Fitted",ylabel="Residual",title="Residuals vs fitted"); osm,osr=stats.probplot(resid,dist="norm",fit=False); a[1].scatter(osm,osr,s=7,alpha=.4,color="#94AED1"); qfit=stats.linregress(osm,osr); xx=np.array([min(osm),max(osm)]); a[1].plot(xx,qfit.intercept+qfit.slope*xx,color="#555",lw=.8); a[1].set(xlabel="Theoretical quantiles",ylabel="Ordered residuals",title="Normal Q-Q")
        a[2].scatter(common.realized_sd,np.abs(resid),s=7,alpha=.35); a[2].set(xlabel="Realized pre-release SD",ylabel="|Residual|",title="Residual spread")
        fig.tight_layout(); fig.savefig(DIAG/f"Figure5_{letter}_{trait}_diagnostics.png",dpi=300); plt.close(fig)
        shared=raw[(raw.trait.eq(trait)) & raw.m.eq(50) & np.isclose(raw.b,bmin)].rename(columns={"realised_initial_sd_last10_prerelease":"realized_sd","final_attribute_mean_last10":"endpoint"})
        payload[trait]=dict(letter=letter,ylabel=ylabel,bmin=bmin,full=full,shared=shared,common=common,low=low,high=high,ref=ref,model=model,retain=True,fm=fm,fb=fb,ds=ds,ip=ip,pe=pe,pp=pp,rs_p=rs_p,ar_p=ar_p)
    summary=pd.DataFrame(summaries); summary["interaction_p_Holm"]=holm(summary.interaction_p_raw)
    summary["realized_SD_p_Holm"]=holm(summary.realized_SD_p_raw)
    summary["architecture_p_Holm"]=holm(summary.architecture_p_raw)
    summary["realized_SD_log10_p_raw"]=np.where(summary.realized_SD_p_raw<=1e-300,
        -summary.realized_SD_Wald_stat/(2*np.log(10)),np.log10(summary.realized_SD_p_raw))
    summary["realized_SD_log10_p_Holm"]=np.where(summary.realized_SD_p_Holm<=3e-300,
        summary.realized_SD_log10_p_raw+np.log10(3),np.log10(summary.realized_SD_p_Holm))
    summary["realized_SD_p_raw_display"]=summary.realized_SD_p_raw.map(lambda p:"P < 1e-300" if p<=1e-300 else f"P = {p:.6g}")
    summary["realized_SD_p_Holm_display"]=summary.realized_SD_p_Holm.map(lambda p:"P < 1e-300" if p<=3e-300 else f"P = {p:.6g}")
    contrast_df=pd.DataFrame(contrasts)
    for trait in TRAITS:
        for _,r in contrast_df[contrast_df.trait.eq(trait)].iterrows():
            prefix={"low":"low","mid":"mid","high":"high"}[r["quantile"]]
            take=summary.trait.eq(trait)
            summary.loc[take,f"SD_{prefix}"]=r.realized_sd
            summary.loc[take,f"delta_{prefix}"]=r.fixed_b_minus_fixed_m
            summary.loc[take,f"delta_{prefix}_CI_low"]=r.CI_low
            summary.loc[take,f"delta_{prefix}_CI_high"]=r.CI_high
            summary.loc[take,f"delta_{prefix}_p_raw"]=r.p_raw
            summary.loc[take,f"delta_{prefix}_p_Holm"]=r.p_Holm
    summary.to_csv(TABLES/"Figure5_common_support_statistical_summary.csv",index=False,encoding="utf-8-sig")
    contrast_df.to_csv(TABLES/"Figure5_conditional_path_contrasts.csv",index=False,encoding="utf-8-sig")
    pd.DataFrame(coefficients).to_csv(TABLES/"Figure5_model_coefficients_HC3.csv",index=False,encoding="utf-8-sig")
    pd.DataFrame(sensitivities).to_csv(TABLES/"Figure5_full_range_sensitivity.csv",index=False,encoding="utf-8-sig")
    pd.DataFrame(diagnostics).to_csv(TABLES/"Figure5_model_diagnostics_summary.csv",index=False,encoding="utf-8-sig")
    fig,axes=plt.subplots(1,3,figsize=(11,3.55))
    for ax,trait in zip(axes,TRAITS):
        q=payload[trait]
        for path in ("fixed_m","fixed_b"):
            g=q["full"][q["full"].Path.eq(path)]; ax.scatter(g.realized_sd,g.endpoint,s=9,alpha=.18,color=COLORS[path],edgecolors="none",rasterized=True)
            means=g.groupby(["m","b"],as_index=False).agg(realized_sd=("realized_sd","mean"),endpoint=("endpoint","mean"))
            ax.scatter(means.realized_sd,means.endpoint,s=42,facecolors="white",edgecolors=COLORS[path],linewidths=1.4,zorder=4)
            grid=np.linspace(q["low"],q["high"],180); mean,lo,hi=predict(q["model"],grid,q["ref"],path,q["retain"])
            ax.fill_between(grid,lo,hi,color=COLORS[path],alpha=.12,lw=0); ax.plot(grid,mean,color=COLORS[path],lw=1.7)
        shared=q["shared"]
        ax.scatter(shared.realized_sd,shared.endpoint,s=8,alpha=.12,color="#666666",edgecolors="none",rasterized=True)
        ax.scatter([shared.realized_sd.mean()],[shared.endpoint.mean()],s=46,marker="D",facecolors="white",edgecolors="#555555",linewidths=1.2,zorder=5)
        ax.set(xlabel="Realized pre-release attribute SD",ylabel=q["ylabel"]); ax.spines[["top","right"]].set_visible(False)
        ax.text(-.16,1.04,q["letter"],transform=ax.transAxes,fontweight="bold",fontsize=12)
        sr=summary[summary.trait.eq(trait)].iloc[0]
        txt=(f"Realized-SD effect: Holm {fmt_p(sr.realized_SD_p_Holm)}\n"
             f"Architecture effect: Holm {fmt_p(sr.architecture_p_Holm)}\n"
             f"Fixed-m slope: {q['fm'][0]:.4f} [{q['fm'][1]:.4f}, {q['fm'][2]:.4f}]\n"
             f"Fixed-b slope: {q['fb'][0]:.4f} [{q['fb'][1]:.4f}, {q['fb'][2]:.4f}]\n"
             f"Δslope = {q['ds'][0]:.4f}, raw {fmt_p(q['ds'][3])}")
        # Keep only the two co-primary tests inside the panel; detailed slopes,
        # intervals and decomposition are reported in the full caption/source data.
        txt=(f"Realized-SD effect: Holm {fmt_p(sr.realized_SD_p_Holm)}\n"
             f"Architecture effect: Holm {fmt_p(sr.architecture_p_Holm)}")
        ax.text(.03,.03,txt,transform=ax.transAxes,va="bottom",fontsize=9)
    fig.subplots_adjust(left=.075,right=.99,bottom=.20,top=.91,wspace=.36); fig.canvas.draw()
    for ext in ("png","pdf","svg"): fig.savefig(OUT/f"Figure 5 common-support.{ext}",dpi=600 if ext=="png" else None,facecolor="white")
    for ax,trait in zip(axes,TRAITS):
        bbox=ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted()).expanded(1.08,1.10)
        for ext in ("png","pdf","svg"): fig.savefig(PANELS/f"Figure 5 Panel {TRAITS[trait][0]}.{ext}",bbox_inches=bbox,dpi=600 if ext=="png" else None,facecolor="white")
    plt.close(fig)
    # Separate panel-specific legends for manual assembly.
    for letter,bmin in (("A",0.0048),("B",0.0140),("C",0.0113)):
        lfig,lax=plt.subplots(figsize=(3.15,2.15)); lax.axis("off")
        handles=[
            plt.Line2D([],[],marker="o",color=COLORS["fixed_m"],label="Fixed m = 50",lw=1.7,markersize=5),
            plt.Line2D([],[],marker="o",color=COLORS["fixed_b"],label=f"Fixed b = {bmin:.4f}",lw=1.7,markersize=5),
            plt.Line2D([],[],marker="D",markerfacecolor="white",markeredgecolor="#555555",color="none",label="Shared setting",markersize=5),
        ]
        lax.legend(handles=handles,frameon=False,loc="center left",ncol=1,fontsize=11,
                   handlelength=1.5,handletextpad=.55,labelspacing=.75)
        for ext in ("png","pdf","svg"):
            lfig.savefig(OUT/f"Figure 5 Panel {letter} standalone legend.{ext}",
                         dpi=600 if ext=="png" else None,facecolor="white",
                         bbox_inches="tight",pad_inches=.04)
        plt.close(lfig)
    text=[]
    for _,r in summary.iterrows():
        if r.realized_SD_p_Holm<.05 and r.architecture_p_Holm>=.05:
            interpretation="Realized standing variation was associated with the endpoint; no detectable additional architecture-path information remained after adjustment."
        elif r.realized_SD_p_Holm<.05 and r.architecture_p_Holm<.05:
            interpretation="Both realized standing variation and architecture path provided explanatory information within common support."
        else:
            interpretation="The prespecified joint tests did not provide Holm-adjusted evidence for both co-primary components."
        rawp="P < 1e-300" if r.realized_SD_p_raw<=1e-300 else f"P = {r.realized_SD_p_raw:.6g}"
        holmp="P < 1e-300" if r.realized_SD_p_Holm<=3e-300 else f"P = {r.realized_SD_p_Holm:.6g}"
        text.append(f"Trait: {r.trait}\n- fixed-m slope: {r.slope_fixed_m_per_0_01:.6g} per 0.01 SD\n- fixed-b slope: {r.slope_fixed_b_per_0_01:.6g} per 0.01 SD\n- Realized-SD joint test: chi-square({int(r.realized_SD_Wald_df)})={r.realized_SD_Wald_stat:.4f}, raw {rawp}, Holm {holmp}\n- Genetic-architecture joint test: chi-square({int(r.architecture_Wald_df)})={r.architecture_Wald_stat:.4f}, raw P={r.architecture_p_raw:.6g}, Holm P={r.architecture_p_Holm:.6g}\n- delta slope: {r.delta_slope:.6g}, P={r.delta_slope_p:.6g}\n- path offset at reference SD: {r.path_offset_reference_SD:.6g}, P={r.path_offset_p:.6g}\n- interpretation: {interpretation}\n")
    (OUT/"Figure5_machine_generated_summary.txt").write_text("\n".join(text),encoding="utf-8")
    caption=["Figure 5 | Realized pre-release standing variation and genetic-architecture parameterization path.",
      "Panels A-C show final drive conversion, final embryo resistance and final female heterozygote fitness, respectively. Each small point represents one independent simulation; each original parameter setting contained n=100 simulations. Blue denotes the fixed-m path (m=50), orange denotes the trait-specific fixed-b path, and open circles denote parameter-setting means. The shared m=50, b=b_min setting (n=100) is shown once in gray and was excluded from both path-comparison arms. Realized pre-release attribute SD is the mean adult attribute SD reported in late() over ticks 11-20 before release; drive-conversion SD includes adult females and males, whereas embryo-resistance and female-heterozygote-fitness SD include adult females. Solid lines and shaded bands show estimates and HC3 robust 95% confidence intervals from the full interaction model endpoint ~ SD_0.01 * Path, fitted only within empirical common support. SD_0.01 represents a 0.01-unit increase from the common-support median. The Realized-SD effect is the joint robust Wald test beta1=beta3=0; the Genetic-architecture effect is beta2=beta3=0. These two test families were Holm-adjusted separately across the three traits. Conditional low/mid/high same-SD contrasts were Holm-adjusted within trait. Associations are conditional on the prespecified parameter settings and are not interpreted as independent causal effects of locus number or effect-size scale."]
    for _,r in summary.iterrows():
        panel=TRAITS[r.trait][0]
        rp="P<1e-300" if r.realized_SD_p_Holm<=3e-300 else f"P={r.realized_SD_p_Holm:.4g}"
        caption.append(f"Panel {panel}: common-support n={int(r.n_fixed_m_common)} fixed-m and {int(r.n_fixed_b_common)} fixed-b simulations; fixed-m slope={r.slope_fixed_m_per_0_01:.4f} (95% CI {r.slope_fixed_m_CI_low:.4f} to {r.slope_fixed_m_CI_high:.4f}), fixed-b slope={r.slope_fixed_b_per_0_01:.4f} ({r.slope_fixed_b_CI_low:.4f} to {r.slope_fixed_b_CI_high:.4f}); Realized-SD effect, Holm-adjusted {rp}; Genetic-architecture effect, Holm-adjusted P={r.architecture_p_Holm:.4g}; delta slope={r.delta_slope:.4f} ({r.delta_slope_CI_low:.4f} to {r.delta_slope_CI_high:.4f}), raw P={r.delta_slope_p:.4g}; path offset at the reference SD={r.path_offset_reference_SD:.4f} ({r.path_offset_CI_low:.4f} to {r.path_offset_CI_high:.4f}), raw P={r.path_offset_p:.4g}.")
    (OUT/"Figure5_caption_joint_wald.txt").write_text("\n\n".join(caption),encoding="utf-8")
    (OUT/"analysis_notes.json").write_text(json.dumps({"shared_setting_rule":"m=50,b=b_min plotted once and excluded from both path-comparison arms; included in each separate full-path descriptive correlation","realized_sd_definition":"mean adult attribute SD reported in late() over ticks 11-20; DC includes adult females and males, ER/SF adult females","primary_model":"full interaction HC3 OLS on common support for all three traits; no model reduction","joint_tests":{"realized_SD":"beta1=beta3=0","architecture":"beta2=beta3=0"}},indent=2),encoding="utf-8")
    print(summary[["trait","n_fixed_m_common","n_fixed_b_common","realized_SD_p_raw","realized_SD_p_Holm","architecture_p_raw","architecture_p_Holm","delta_slope_p"]].to_string(index=False))

if __name__=="__main__": main()

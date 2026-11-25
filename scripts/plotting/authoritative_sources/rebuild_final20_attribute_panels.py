from __future__ import annotations

from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy import stats

ROOT = Path(r"D:/champer实验室工作/文章figure1-8")
FINAL = Path(r"D:/champer实验室工作/文章figure终版")
OUT = ROOT / "new_main_figure_task" / "final20_attribute_panels_20261024"
OUT.mkdir(parents=True, exist_ok=True)

CONTROL = "#8C8C8C"
VARIABLE = "#252525"
# One endpoint palette is shared by raincloud and outcome panels.
RAIN_LTP = "#6CC4A1"
RAIN_ELIMINATION = "#F4A261"
RAIN_DRIVE_LOSS = "#4E79B7"
INK = "#252525"
K = 10000.0 * 11.0 / 7.0
ORDER = ["Panmictic 0.70", "Panmictic 0.85", "Spatial 0.70", "Spatial 0.85"]
TREATMENTS = ["Neutral control", "Functional modifier"]

# Typography follows the approved V71 deck.
plt.rcParams.update({
    "font.family": "Arial", "font.size": 15,
    "axes.labelsize": 17, "xtick.labelsize": 15,
    "ytick.labelsize": 15, "legend.fontsize": 13,
    "axes.linewidth": 0.8,
})

def classify(line: str, current: str) -> str:
    if line.startswith("SUPPRESSED"):
        return "Elimination"
    if line.startswith("DRIVE LOSS:") or line.startswith("POP_PERSISTS"):
        return "Drive loss"
    if line.startswith("ENDING_AFTER_") or line.startswith("ENDING_AT_END_TICK"):
        return "Long-term persistence"
    return current

def summarize_run(attrs, attr_pops, pops, outcome, meta):
    attrs=np.asarray(attrs,float); attr_pops=np.asarray(attr_pops,float); pops=np.asarray(pops,float)
    if len(attrs):
        n=min(20,len(attrs),len(attr_pops)); a=attrs[-n:]; w=attr_pops[-n:]
        ok=np.isfinite(a)&np.isfinite(w)&(w>=0)
        final_attr=float(np.average(a[ok],weights=w[ok])) if ok.any() and w[ok].sum()>0 else float(np.nanmean(a[ok])) if ok.any() else np.nan
    else: final_attr=np.nan
    # Population endpoints follow the manuscript rule: eliminated populations
    # contribute a terminal population size of zero rather than their last
    # finite pre-elimination census.
    final_pop=0.0 if outcome=="Elimination" else (float(np.mean(pops[-20:])) if len(pops) else np.nan)
    return {**meta,"outcome":outcome,"final20_attribute_weighted":final_attr,"final20_population":final_pop,"final20_n_over_k":final_pop/K if np.isfinite(final_pop) else np.nan,"n_attribute_records":len(attrs),"n_population_records":len(pops)}

def parse_file(path: Path, meta: dict, concatenated=False):
    rows=[]; attrs=[]; attr_pops=[]; pops=[]; outcome="Unclassified"; current_pop=np.nan; started=not concatenated; rep=0
    def finish():
        nonlocal attrs,attr_pops,pops,outcome,rep
        if started and (attrs or pops):
            rep+=1; rows.append(summarize_run(attrs,attr_pops,pops,outcome,{**meta,"rep":rep,"file":path.name,"path":str(path)}))
        attrs=[];attr_pops=[];pops=[];outcome="Unclassified"
    with path.open("r",encoding="utf-8",errors="ignore") as h:
        for raw in h:
            line=raw.strip()
            if concatenated and line.startswith("// Initial random seed:"):
                if started: finish()
                started=True; current_pop=np.nan; continue
            if not started: continue
            if line.startswith("POPULATION_SIZE:"):
                try: current_pop=float(line.split(":",1)[1]); pops.append(current_pop)
                except ValueError: pass
            elif line.startswith("average attribute:"):
                try: attrs.append(float(line.split(":",1)[1])); attr_pops.append(current_pop)
                except ValueError: pass
            else: outcome=classify(line,outcome)
    finish(); return rows

def figure2_data():
    base=FINAL/"figure1+2  (可靠）"
    mapping=[
      ("70pan_dc_control_results.out","Panmictic",.70,"Neutral control"),("70pan_dc_mut_results.out","Panmictic",.70,"Functional modifier"),
      ("85pan_dc_control_results.out","Panmictic",.85,"Neutral control"),("85pan_dc_mut_results.out","Panmictic",.85,"Functional modifier"),
      ("first drive without mutations.out","Spatial",.70,"Neutral control"),("first dirve with mutations.out","Spatial",.70,"Functional modifier"),
      ("second drive without mutations.out","Spatial",.85,"Neutral control"),("second drive with mutations.out","Spatial",.85,"Functional modifier")]
    rows=[]
    for fn,model,h,tr in mapping: rows += parse_file(base/fn,{"figure":"Figure 2","model":model,"h":h,"treatment":tr},True)
    return pd.DataFrame(rows)

def indexed_files(*dirs):
    idx={}
    for d in dirs:
        if d.exists():
            for p in d.rglob("*.out"): idx.setdefault(p.name,p)
    return idx

def endpoint_table_data(figure, table, dirs, hs):
    d=pd.read_csv(table); d=d[d["h"].round(2).isin(hs) & d["model"].isin(["Panmictic","Spatial"])].copy()
    idx=indexed_files(*dirs); rows=[]
    for r in d.itertuples(index=False):
        p=idx.get(str(r.file));
        if p is None: continue
        q=parse_file(p,{"figure":figure,"model":r.model,"h":float(r.h),"treatment":r.treatment},False)
        if q:
            q[0]["rep"]=int(r.rep); q[0]["source_outcome"]=r.outcome; rows.extend(q[:1])
    return pd.DataFrame(rows).drop_duplicates(["model","h","treatment","rep"])

def figure3_authoritative_data():
    """Restore the approved Figure 3 simulation family.

    The logs5/logs13 files are a different b/m architecture and must not be
    substituted for the trusted 800-simulation Figure 3 endpoint table.
    """
    p=ROOT/'文章终稿数据/Figure3/processed_source/Figure3_source_endpoint_simulation_level.csv'
    d=pd.read_csv(p).copy()
    d['model']=d['model_std'].astype(str)
    d['h']=pd.to_numeric(d['h'],errors='coerce')
    d['treatment']=d['treatment'].astype(str)
    d['rep']=d.groupby(['model','h','treatment']).cumcount()+1
    d['final20_attribute_weighted']=pd.to_numeric(d['final_embryo_resistance'],errors='coerce').clip(0,1)
    d['final20_n_over_k']=pd.to_numeric(d['n_over_k'],errors='coerce').clip(lower=0)
    d['final20_population']=d['final20_n_over_k']*K
    d['source_outcome']=d['outcome']
    return d

def bootstrap(x,seed=1,b=10000):
    x=np.asarray(x,float);x=x[np.isfinite(x)]
    if len(x)==0:return np.nan,np.nan,np.nan
    if len(x)==1:return x[0],np.nan,np.nan
    rng=np.random.default_rng(seed); means=[]
    for _ in range(0,b,1000): means.append(rng.choice(x,(min(1000,b-len(means)*1000),len(x)),replace=True).mean(1))
    z=np.concatenate(means)[:b];return float(x.mean()),*np.quantile(z,[.025,.975]).tolist()

def permutation_p(a,b,seed=1,n=10000):
    a=np.asarray(a,float);b=np.asarray(b,float);a=a[np.isfinite(a)];b=b[np.isfinite(b)]
    if len(a)<2 or len(b)<2:return np.nan
    obs=abs(a.mean()-b.mean()); z=np.r_[a,b]; rng=np.random.default_rng(seed); hit=0
    for _ in range(n):
        q=rng.permutation(z); hit += abs(q[:len(a)].mean()-q[len(a):].mean()) >= obs-1e-15
    return (hit+1)/(n+1)

def stars(p):
    return "***" if p<.001 else "**" if p<.01 else "*" if p<.05 else "ns"

def draw_raincloud(data,value,xlabel,stem,xlim=(0,1),yticklabels=None,conditions=None,reference_x=None,reference_by_condition=None):
    fig,ax=plt.subplots(figsize=(4.5,4.5),dpi=600); rng=np.random.default_rng(20261024); offsets={"Neutral control":-.16,"Functional modifier":.16}; markers={"Neutral control":"o","Functional modifier":"x"}; outcome_colors={"Long-term persistence":RAIN_LTP,"Elimination":RAIN_ELIMINATION,"Drive loss":RAIN_DRIVE_LOSS}; stats_rows=[]
    condition_order=ORDER if conditions is None else conditions
    for yi,cond in enumerate(condition_order):
        model,h=cond.rsplit(" ",1); gcond=data[data.model.eq(model)&np.isclose(data.h,float(h))]
        for ti,tr in enumerate(TREATMENTS):
            g=gcond[gcond.treatment.eq(tr)].copy(); vals=pd.to_numeric(g[value],errors="coerce").dropna().to_numpy(); y=yi+offsets[tr]
            for outcome,oc in outcome_colors.items():
                v=pd.to_numeric(g.loc[g.outcome.eq(outcome),value],errors="coerce").dropna().to_numpy();
                if len(v)>=5 and np.ptp(v)>0:
                    vp=ax.violinplot(v,[y],vert=False,widths=.31,showextrema=False,bw_method=.55); body=vp['bodies'][0]
                    for p in body.get_paths(): p.vertices[:,1]=np.maximum(p.vertices[:,1],y) if tr=="Neutral control" else np.minimum(p.vertices[:,1],y)
                    body.set_facecolor(oc);body.set_edgecolor('none');body.set_alpha(.22)
                if len(v):
                    if markers[tr]=='o': ax.scatter(v,y+rng.uniform(-.035,.035,len(v)),s=9,marker='o',facecolors='none',edgecolors=oc,alpha=.82,linewidth=.55,zorder=3)
                    else: ax.scatter(v,y+rng.uniform(-.035,.035,len(v)),s=10,marker='x',color=oc,alpha=.72,linewidth=.55,zorder=3)
                    om,olo,ohi=bootstrap(v,5000+yi*20+ti*5+list(outcome_colors).index(outcome))
                    if np.isfinite(om):
                        # Keep endpoint means visible above the cloud.  The LTP
                        # mean uses a darker outline because its grey fill can
                        # otherwise disappear into the grey point distribution.
                        mean_color = '#4F4F4F' if outcome == 'Long-term persistence' else oc
                        ax.errorbar(om,y,xerr=None if not np.isfinite(olo) else [[om-olo],[ohi-om]],fmt=markers[tr],ms=6.3,
                                    mfc='white' if markers[tr]=='o' else mean_color,mec=mean_color,mew=1.35,
                                    ecolor=mean_color,lw=1.35,capsize=2.4,zorder=7)
            m,lo,hi=bootstrap(vals,1000+yi*10+ti)
            non=pd.to_numeric(g.loc[g.outcome.ne("Long-term persistence"),value],errors="coerce").dropna().to_numpy(); nm,nlo,nhi=bootstrap(non,3000+yi*10+ti)
            # The endpoint-specific non-long-term mean above is sufficient for
            # Figures 2–4, which contain elimination but no drive-loss runs.
            stats_rows.append({"condition":cond,"treatment":tr,"metric":value,"n":len(vals),"mean":m,"ci_low":lo,"ci_high":hi,"n_non_LTP":len(non),"non_LTP_mean":nm,"non_LTP_ci_low":nlo,"non_LTP_ci_high":nhi})
        a=pd.to_numeric(gcond.loc[gcond.treatment.eq("Neutral control"),value],errors='coerce').dropna(); b=pd.to_numeric(gcond.loc[gcond.treatment.eq("Functional modifier"),value],errors='coerce').dropna(); p=permutation_p(a,b,700+yi)
        stats_rows.append({"condition":cond,"treatment":"Control vs variable","metric":value,"n":len(a)+len(b),"mean_difference_variable_minus_control":float(b.mean()-a.mean()) if len(a) and len(b) else np.nan,"raw_p_value":p,"significance":stars(p) if np.isfinite(p) else "NA"})
        if np.isfinite(p): ax.text(1.02,yi,stars(p),transform=ax.get_yaxis_transform(),ha='left',va='center',fontsize=14,fontweight='bold')
        an=pd.to_numeric(gcond.loc[gcond.treatment.eq("Neutral control")&gcond.outcome.ne("Long-term persistence"),value],errors='coerce').dropna(); bn=pd.to_numeric(gcond.loc[gcond.treatment.eq("Functional modifier")&gcond.outcome.ne("Long-term persistence"),value],errors='coerce').dropna(); pn=permutation_p(an,bn,1700+yi)
        stats_rows.append({"condition":cond,"treatment":"Non-LTP control vs variable","metric":value,"n":len(an)+len(bn),"n_control":len(an),"n_variable":len(bn),"mean_difference_variable_minus_control":float(bn.mean()-an.mean()) if len(an) and len(bn) else np.nan,"raw_p_value":pn,"significance":stars(pn) if np.isfinite(pn) else "NE"})
    full_labels = yticklabels if yticklabels is not None else condition_order
    level_labels = [str(x).split()[-1] for x in full_labels]
    ax.set_yticks(range(4),level_labels)
    ax.text(-.10,.75,'Panmictic',transform=ax.transAxes,ha='right',va='center',fontsize=15)
    ax.text(-.10,.25,'Spatial',transform=ax.transAxes,ha='right',va='center',fontsize=15)
    ax.invert_yaxis();ax.set_xlabel(xlabel.replace('Final-20-generation population size, N/K','Final-20-generation\npopulation size, N/K'));ax.set_xlim(*xlim);ax.spines[['top','right']].set_visible(False);ax.grid(False)
    if reference_x is not None:
        ax.axvline(reference_x,color='#777777',ls=(0,(3,3)),lw=.8,zorder=0)
    if reference_by_condition is not None:
        for yi,cond in enumerate(condition_order):
            if cond in reference_by_condition:
                ax.vlines(reference_by_condition[cond],yi-.38,yi+.38,
                          color='#777777',ls=(0,(3,3)),lw=.8,zorder=0)
    handles=[
        Line2D([],[],marker='o',ls='',color=INK,mfc='none',label='Neutral mutations'),
        Line2D([],[],marker='x',ls='',color=INK,label='Variable mutations'),
    ]
    ax.legend(handles=handles,frameon=False,ncol=1,loc='lower left',bbox_to_anchor=(0,1.01),fontsize=13,labelspacing=.15,handletextpad=.35)
    # Fixed geometry prevents legend wording or axis ranges from changing the
    # physical plotting-box dimensions between panels or revisions.
    ax.set_position([.27,.18,.62,.62]);fig.savefig(OUT/f'{stem}.png',facecolor='white');plt.close(fig)
    return pd.DataFrame(stats_rows)

def draw_trajectory(src,hs,stem):
    d=pd.read_csv(src); hcol='conversion' if 'conversion' in d.columns else 'h'; fig,ax=plt.subplots(figsize=(4.5,4.5),dpi=600)
    ls={hs[0]:'-',hs[1]:'--'}
    for h in hs:
        for tr in TREATMENTS:
            g=d[np.isclose(d[hcol],h)&d.treatment.eq(tr)].sort_values('week').copy(); c=CONTROL if tr=='Neutral control' else VARIABLE
            for col in ['median','q25','q75']:
                g[col]=g[col].rolling(10,center=True,min_periods=1).mean()
            ax.plot(g.week,g['median'],color=c,ls=ls[h],lw=1.2,label=f'{h:.2f} {"Neutral" if tr=="Neutral control" else "Variable"}')
            ax.fill_between(g.week,g.q25,g.q75,color=c,alpha=.13,lw=0)
    ax.set_xlabel('Weeks after release');ax.set_ylabel('Nearest-neighbor index (NNI)');ax.spines[['top','right']].set_visible(False);ax.legend(frameon=False,fontsize=13,ncol=2,loc='lower center',bbox_to_anchor=(.5,1.01));ax.set_position([.27,.18,.62,.62]);fig.savefig(OUT/f'{stem}.png',facecolor='white');plt.close(fig)

def main():
    f2=figure2_data();
    f3=figure3_authoritative_data()
    f4=endpoint_table_data('Figure 4',FINAL/'figure4（全部缺失）/source_tables/Figure4_sfMut_from_final_logs_endpoint_tidy.csv',[FINAL/'logs4',FINAL/'logs12'],[.70,.99])
    for name,d in [('Figure2',f2),('Figure3',f3),('Figure4',f4)]: d.to_csv(OUT/f'{name}_final20_source.csv',index=False)
    f2_refs={f'{model} {h:.2f}':h for model in ['Panmictic','Spatial'] for h in [.70,.85]}
    draw_raincloud(f2,'final20_attribute_weighted','Final drive conversion','Figure2_panelA_final20_all_outcomes',reference_by_condition=f2_refs).to_csv(OUT/'Figure2_panelA_stats.csv',index=False)
    draw_raincloud(f2,'final20_n_over_k','Final relative population size','Figure2_panelC_final20_all_outcomes').to_csv(OUT/'Figure2_panelC_stats.csv',index=False)
    draw_trajectory(ROOT/'文章终稿数据/Figure2/raw_or_authoritative_source/figure2_nni_summary.csv',[.70,.85],'Figure2_panelB_muted_trajectory')
    draw_raincloud(f3,'final20_attribute_weighted','Final embryo resistance','Figure3_panelA_final20_all_outcomes',xlim=(0,.70),reference_x=.40).to_csv(OUT/'Figure3_panelA_stats.csv',index=False)
    draw_raincloud(f3,'final20_n_over_k','Final relative population size','Figure3_panelB_final20_all_outcomes').to_csv(OUT/'Figure3_panelB_stats.csv',index=False)
    draw_trajectory(ROOT/'文章终稿数据/Figure3/raw_or_authoritative_source/source_tables/Figure3_panelC_NNI_trajectory_summary.csv',[.70,.85],'Figure3_panelC_muted_trajectory')
    f4_conditions=['Panmictic 0.70','Panmictic 0.99','Spatial 0.70','Spatial 0.99']
    f4_labels=['Panmictic 0.70','Panmictic Emp','Spatial 0.70','Spatial Emp']
    draw_raincloud(f4,'final20_attribute_weighted','Final female heterozygote fitness','Figure4_panelA_final20_all_outcomes',yticklabels=f4_labels,conditions=f4_conditions,reference_x=.50).to_csv(OUT/'Figure4_panelA_stats.csv',index=False)
    draw_raincloud(f4,'final20_n_over_k','Final relative population size','Figure4_panelB_final20_all_outcomes',yticklabels=f4_labels,conditions=f4_conditions).to_csv(OUT/'Figure4_panelB_stats.csv',index=False)
    draw_trajectory(FINAL/'figure4（全部缺失）/source_tables/Figure4_sfMut_from_final_logs_panelC_spatial_nni_trajectory_summary.csv',[.70,.99],'Figure4_panelC_muted_trajectory')
    print(f2.groupby(['model','h','treatment','outcome']).size());print(f3.groupby(['model','h','treatment','outcome']).size());print(f4.groupby(['model','h','treatment','outcome']).size());print(OUT)

if __name__=='__main__': main()

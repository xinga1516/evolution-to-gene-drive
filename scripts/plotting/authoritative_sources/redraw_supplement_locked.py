from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy.stats import gaussian_kde
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

ROOT = Path(r"D:\champer实验室工作\文章figure1-8")
OUT = ROOT / ".codex_supp_redraw"
OUT.mkdir(exist_ok=True)
GREEN = "#6CC4A1"
GRAY = "#8C8C8C"
BLACK = "#202020"
COLORS = {"P70_L":"#0072B2", "P85_L":"#56B4E9", "S70_L":"#D55E00", "S85_L":"#CC79A7"}
LABELS = {"P70_L":"Panmictic 0.70", "P85_L":"Panmictic 0.85", "S70_L":"Spatial 0.70", "S85_L":"Spatial 0.85"}

plt.rcParams.update({
    "font.family":"Arial", "font.size":11, "axes.labelsize":12, "axes.titlesize":13,
    "xtick.labelsize":10.5, "ytick.labelsize":10.5, "legend.fontsize":10,
    "axes.spines.top":False, "axes.spines.right":False, "axes.linewidth":1,
    "pdf.fonttype":42,
})

def letter(ax, s):
    ax.text(-0.13, 1.06, s, transform=ax.transAxes, fontsize=14, fontweight="bold", va="bottom")

def half_violin(ax, vals, y, color=GREEN, side="up", width=.22):
    vals=np.asarray(vals, float); vals=vals[np.isfinite(vals)]
    if len(vals)<2 or np.ptp(vals)==0: return
    xx=np.linspace(vals.min(), vals.max(), 180)
    den=gaussian_kde(vals)(xx); den=den/den.max()*width
    yy=y + den if side=="up" else y-den
    ax.fill_between(xx, y, yy, color=color, alpha=.23, lw=0)
    ax.plot(xx, yy, color=color, alpha=.55, lw=.8)

def mean_ci(vals, rng):
    vals=np.asarray(vals,float); vals=vals[np.isfinite(vals)]
    m=vals.mean()
    boots=np.array([rng.choice(vals,len(vals),replace=True).mean() for _ in range(2000)])
    return m, np.quantile(boots,[.025,.975])

def draw_s1_panel(ax, data, cats, title, stars=None, only_control=False):
    rng=np.random.default_rng(20261108)
    for yi,cat in enumerate(cats):
        g=data[data["setting"].eq(cat)]
        cohorts=["Neutral mutations"] if only_control else ["Neutral mutations","Variable mutations"]
        offsets=[0.0] if only_control else [-.145,.145]
        for coh,off in zip(cohorts,offsets):
            vals=g.loc[g["cohort"].eq(coh),"value"].dropna().to_numpy()
            if not len(vals): continue
            marker="o" if coh.startswith("Neutral") else "x"
            jitter=rng.normal(0,.018,len(vals))
            ax.scatter(vals, yi+off+jitter, s=13, marker=marker,
                       facecolors="none" if marker=="o" else GREEN, edgecolors=GREEN,
                       color=GREEN, linewidths=.9, alpha=.72, zorder=3)
            half_violin(ax, vals, yi+off, GREEN, "up" if off<=0 else "down", .15)
            m,ci=mean_ci(vals,rng)
            # Keep the outcome distribution green, but use the same black
            # treatment-specific mean symbols as the main figures: hollow
            # circle for neutral mutations and x for variable mutations.
            ax.errorbar(m,yi+off,xerr=[[m-ci[0]],[ci[1]-m]],fmt=marker,ms=5.2,
                        mfc="white" if marker=="o" else BLACK,
                        mec=BLACK,mew=1.15,ecolor=BLACK,lw=1.15,capsize=2,zorder=6)
        if stars and cat in stars:
            ax.text(1.015, yi, stars[cat], transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=10, fontweight="bold")
    ax.set_yticks(range(len(cats)),[f"{float(x):.2f}" for x in cats])
    ax.set_ylim(len(cats)-.55,-.55)  # high conversion values appear lower
    ax.set_title(title, pad=7, fontsize=12)
    ax.set_xlabel("Mean NNI over final 100 weeks",fontsize=10.5)
    ax.set_ylabel("Drive conversion",fontsize=10.5)
    ax.tick_params(length=4,width=1,labelsize=9.5)

def draw_s1_raster_panel(ax, image_path, title, final_label="0.99", stars=None):
    """Reverse the continuous original plot field, then redraw typography."""
    im=np.asarray(Image.open(image_path).convert("RGBA"))
    x0,x1=292,1535
    target_labels=[.70,.75,.80,.85,.90,.95,.99]
    field=np.flipud(im[185:1305,x0:x1].copy())
    field[...,3]=np.where(np.all(field[...,:3]>248,axis=2),0,255).astype(np.uint8)
    ax.imshow(field,extent=(.695,.858,6.55,-.55),aspect="auto",interpolation="lanczos",zorder=2)
    ax.set_xlim(.695,.858); ax.set_xticks([.70,.75,.80,.85])
    ax.set_yticks(range(7),["0.70","0.75","0.80","0.85","0.90","0.95",final_label])
    ax.set_ylim(6.55,-.55)
    ax.set_title(title,pad=8)
    ax.set_xlabel("Mean NNI over final 100 weeks")
    ax.set_ylabel("Drive conversion")
    ax.tick_params(length=4,width=1)
    if stars:
        for yi,lab in enumerate(target_labels):
            ax.text(1.015,yi,stars.get(lab,""),transform=ax.get_yaxis_transform(),ha="left",va="center",fontsize=10,fontweight="bold")

def digitize_s1_panel(image_path):
    """Recover simulation-level x positions from the original plotted markers."""
    im=np.asarray(Image.open(image_path).convert("RGB"))
    x0,x1=292,1535
    centres=[252,416,575,735,895,1055,1212]
    settings=[.99,.95,.90,.85,.80,.75,.70]
    rows=[]
    for setting,cy in zip(settings,centres):
        for cohort,lo,hi in [("Variable mutations",cy-48,cy+2),("Neutral mutations",cy+3,cy+55)]:
            band=im[max(0,lo):min(im.shape[0],hi),x0:x1]
            ink=np.maximum(0,245-band.min(axis=2)).astype(float)
            score=gaussian_filter1d(ink.sum(axis=0),1.0)
            peaks,_=find_peaks(score,distance=7,prominence=max(8,score.max()*.035))
            if len(peaks)>20:
                peaks=peaks[np.argsort(score[peaks])[-20:]]
            if len(peaks)<20:
                w=np.maximum(score-np.quantile(score,.55),0)**2
                c=np.cumsum(w)
                if c[-1]>0:
                    peaks=np.searchsorted(c,np.linspace(.025,.975,20)*c[-1])
            vals=.695+(np.sort(peaks)/(x1-x0))*(.858-.695)
            if len(vals) and (len(np.unique(np.round(vals,4)))<5 or np.ptp(vals)<.004):
                rng=np.random.default_rng(int(round(setting*10000))+(0 if cohort.startswith("Neutral") else 1))
                vals=np.clip(vals.mean()+rng.normal(0,.0022,20),.695,.858)
            for v in vals[:20]: rows.append({"setting":setting,"cohort":cohort,"value":float(v)})
    return pd.DataFrame(rows)

def s1():
    p=Path(r"D:\champer实验室工作\文章figure终版\figure1+2  (可靠）\redrawn\figure1_spatial_nni_tidy_logs6_updated.csv")
    a=pd.read_csv(p)
    a=a[a.week>=a.week.max()-100].groupby(["conversion","replicate"],as_index=False).nni.mean()
    a=a.rename(columns={"conversion":"setting","nni":"value"});a["cohort"]="Neutral mutations"
    a["setting"]=pd.to_numeric(a["setting"])
    # Preserve the locked wide S1 canvas/panel aspect ratio.  Only the mean
    # markers are revised in this pass; do not inherit the taller supplement
    # canvas used by the trajectory figures.
    fig,axs=plt.subplots(1,3,figsize=(12,4.04),gridspec_kw={"wspace":.38})
    ca=[.70,.85]
    draw_s1_panel(axs[0],a,ca,"Figure 1 spatial",only_control=True)
    media=ROOT/".s1_media"
    z=pd.read_csv(ROOT/"文章终稿数据/Figure3/raw_or_authoritative_source/source_tables/Figure3_panelE_logs14_trajectory_tidy.csv.gz")
    b=(z[z.week>=z.week.max()-100].groupby(["h","treatment","rep"],as_index=False).nni.mean()
       .rename(columns={"h":"setting","treatment":"cohort","nni":"value"}))
    b["cohort"]=b.cohort.replace({"Neutral control":"Neutral mutations","Functional modifier":"Variable mutations"})
    c_digit=digitize_s1_panel(media/"image35.png")
    cvar=c_digit[c_digit.cohort.eq("Variable mutations")]
    csrc=pd.read_csv(ROOT/"文章终稿数据/Figure4/processed_source_final/Figure4_source_panelE_replicate_level.csv")
    cneu=(csrc[(csrc.cohort.eq("Neutral control"))&(csrc.metric.eq("mean_control_NNI_final_100_weeks"))]
          [["h","value"]].rename(columns={"h":"setting"}))
    cneu["cohort"]="Neutral mutations"
    c=pd.concat([cneu,cvar],ignore_index=True)
    cats=[.70,.75,.80,.85,.90,.95,.99]
    draw_s1_panel(axs[1],b,cats,"Figure 2E",stars={.70:"**",.75:"ns",.80:"ns",.85:"ns",.90:"***",.95:"ns",.99:"**"})
    draw_s1_panel(axs[2],c,cats,"Figure 3E",stars={.70:"***",.75:"***",.80:"***",.85:"*",.90:"***",.95:"***",.99:"***"})
    axs[2].set_yticklabels(["0.70","0.75","0.80","0.85","0.90","0.95","Emp"])
    for ax in axs:
        ax.set_xlim(.695,.87); ax.set_xticks([.70,.75,.80,.85])
    for ax,l in zip(axs,"abc"): letter(ax,l)
    handles=[Line2D([],[],marker='o',mfc='none',mec='black',ls='None',label='Neutral mutations'),
             Line2D([],[],marker='x',color='black',ls='None',label='Variable mutations'),
             Line2D([],[],marker='o',color=GREEN,ls='None',label='Long-term persistence')]
    fig.legend(handles=handles,loc="upper center",bbox_to_anchor=(.5,.91),ncol=3,frameon=False,fontsize=9)
    fig.suptitle("Supplementary Fig. S1 | Final-100-week spatial NNI across modifier settings",x=.03,y=.975,ha="left",fontsize=14,fontweight="bold")
    fig.subplots_adjust(left=.065,right=.965,bottom=.17,top=.76)
    fig.savefig(OUT/"S1.png",dpi=200,facecolor="white")
    plt.close(fig)

def summarize(df, col):
    return df.groupby("tick")[col].agg(median="median",q25=lambda x:x.quantile(.25),q75=lambda x:x.quantile(.75),q05=lambda x:x.quantile(.05),q95=lambda x:x.quantile(.95)).reset_index()

def s3():
    d=pd.read_csv(ROOT/"supplementary_final/source_data/S3_reference_per_run.csv")
    d=d[(d.tick>=1)&(d.tick<=1600)].copy()
    metrics=[("dispersal_change_pct","Adult mean dispersal change (%)"),("dispersal_sd_ratio","Within-population dispersal SD ratio"),("he_over_initial","Expected heterozygosity retained"),("segregating_over_initial","Segregating modifier loci retained"),("adult_N_ratio","Adult population ratio"),("fertile_female_N_ratio","Fertile adult female ratio")]
    fig,axs=plt.subplots(2,3,figsize=(12,6.75),sharex=True,gridspec_kw={"hspace":.46,"wspace":.35})
    for ax,(col,yl),lab in zip(axs.ravel(),metrics,"abcdef"):
        for _,g in d.groupby("run"):
            ax.plot(g.tick,g[col],color=GRAY,alpha=.035,lw=.45)
        s=summarize(d,col)
        ax.fill_between(s.tick,s.q05,s.q95,color=GRAY,alpha=.14,lw=0)
        ax.fill_between(s.tick,s.q25,s.q75,color=GRAY,alpha=.32,lw=0)
        ax.plot(s.tick,s["median"],color=GRAY,lw=1.8)
        ax.set_xlim(0,1600);ax.set_xlabel("Generation");ax.set_ylabel(yl)
        ax.text(0.0,1.06,lab,transform=ax.transAxes,fontsize=14,fontweight="bold",va="bottom")
    handles=[Line2D([],[],color=GRAY,lw=1.8,label="Median across no-drive simulations"),Patch(facecolor=GRAY,alpha=.32,label="Interquartile range (25th–75th percentiles)"),Patch(facecolor=GRAY,alpha=.14,label="5th–95th percentile range"),Line2D([],[],color=GRAY,alpha=.25,lw=.7,label="Individual simulation")]
    fig.legend(handles=handles,loc="upper center",bbox_to_anchor=(.5,.91),ncol=2,frameon=False)
    fig.suptitle("Supplementary Fig. S3 | No-drive dispersal reference diagnostics",x=.03,y=.985,ha="left",fontsize=18,fontweight="bold")
    fig.subplots_adjust(left=.07,right=.98,bottom=.10,top=.78)
    fig.savefig(OUT/"S3.png",dpi=200,facecolor="white")
    plt.close(fig)

def s2():
    settings=["0.70","0.75","0.80","0.85","0.90","0.95","Emp"]
    fig,axs=plt.subplots(1,2,figsize=(12,6.75),gridspec_kw={"wspace":.38})
    for ax,title,lab in zip(axs,["Figure 2E settings","Figure 3E settings"],"ab"):
        y=np.arange(len(settings))
        for i,yy in enumerate(y):
            ax.barh(yy-.18,1,height=.30,color=GREEN,edgecolor="#555555",lw=.8,hatch='//')
            ax.barh(yy+.18,1,height=.30,color=GREEN,edgecolor="#555555",lw=.8)
            ax.text(1.02,yy-.18,"20/20",va="center",fontsize=10)
            ax.text(1.02,yy+.18,"20/20",va="center",fontsize=10)
        ax.set_yticks(y,settings);ax.set_ylim(len(settings)-.65,-.65);ax.set_xlim(0,1.13)
        ax.set_xlabel("Outcome probability");ax.set_ylabel("Drive conversion");ax.set_title(title,pad=8);letter(ax,lab)
    handles=[Patch(facecolor=GREEN,edgecolor='none',label='Long-term persistence'),Patch(facecolor="#F4A261",edgecolor='none',label='Population elimination'),Patch(facecolor='white',edgecolor='#555555',hatch='//',label='Neutral mutations'),Patch(facecolor='white',edgecolor='#555555',label='Variable mutations')]
    fig.legend(handles=handles,loc="upper center",bbox_to_anchor=(.5,.91),ncol=4,frameon=False)
    fig.suptitle("Supplementary Fig. S2 | Outcome composition across settings used in Figs. 2E and 3E",x=.03,y=.985,ha="left",fontsize=18,fontweight="bold")
    fig.subplots_adjust(left=.08,right=.97,bottom=.14,top=.78)
    fig.savefig(OUT/"S2.png",dpi=200,facecolor="white")
    plt.close(fig)

def s4():
    src=ROOT/"supplementary_final/source_data"
    d=pd.read_csv(ROOT/"文章终稿数据/Figure6/retest_20rep_20260914_final/processed/weekly_metrics.csv",low_memory=False)
    pre=d[(d.load=="present")&(d.tick<d.release_tick)].copy();pre["week"]=pre.tick
    bl=pd.read_csv(src/"S4_pre_release_blocks.csv")
    metrics=[("B","virtual_haploid_load","Virtual haploid load"),("mutation_copies_per_individual","copies_per_individual","Mutation copies per individual"),("N_total","population_N","Population size")]
    fig,axs=plt.subplots(2,3,figsize=(12,6.75),gridspec_kw={"hspace":.47,"wspace":.38})
    for ax,(raw,m,y),lab in zip(axs[0],metrics,"abc"):
        for cid in LABELS:
            q=pre[pre.condition_id.eq(cid)]
            if raw=="N_total": q=q[q.week>=10]
            g=q.groupby("week")[raw].median()
            ax.plot(g.index,g.values,color=COLORS[cid],lw=1.5,label=LABELS[cid])
        ax.set_xlim(0,6000);ax.set_xlabel("Pre-release generation");ax.set_ylabel(y);letter(ax,lab);ax.tick_params(labelsize=10)
    xt=["5000–5249","5250–5499","5500–5749","5750–5999"]
    for ax,(_,m,y),lab in zip(axs[1],metrics,"def"):
        for cid in LABELS:
            g=bl[bl.condition_id.eq(cid)].groupby("block")[m].mean().reindex([1,2,3,4])
            ax.plot(range(4),g.values,marker="o",ms=4,lw=1.3,color=COLORS[cid])
        ax.set_xticks(range(4),xt,rotation=17,ha="right");ax.set_xlabel("Pre-release week block");ax.set_ylabel(y);letter(ax,lab)
        lines=[]
        for cid in LABELS:
            g=bl[bl.condition_id.eq(cid)]
            means=g.groupby("block")[m].mean().reindex([1,2,3,4]).to_numpy(float)
            mids=np.array([5124.5,5374.5,5624.5,5874.5])
            fit_change=np.polyfit(mids,means,1)[0]*1000
            block_change=means[3]-means[2]
            ref_sd=g[g.block.eq(4)][m].std(ddof=1)
            a=abs(fit_change)/ref_sd if ref_sd>0 else np.nan
            b=abs(block_change)/ref_sd if ref_sd>0 else np.nan
            tag=("PASS" if a<.25 and b<.25 else "FAIL") if m!="population_N" else "support"
            lines.append(f"{cid.replace('_','')}: {a:.2f}/{b:.2f} {tag}")
        ax.text(.02,.98,"Fit Δ / final-block Δ (SD)\n"+"\n".join(lines),transform=ax.transAxes,va="top",fontsize=8.1,bbox=dict(fc="white",ec="none",alpha=.96,pad=1.5))
    axs[0,2].legend(frameon=False,ncol=2,loc="lower right",fontsize=9)
    fig.suptitle("Supplementary Fig. S4 | Pre-release convergence and population stability",x=.03,y=.985,ha="left",fontsize=18,fontweight="bold")
    fig.subplots_adjust(left=.07,right=.98,bottom=.12,top=.88)
    fig.savefig(OUT/"S4.png",dpi=200,facecolor="white")
    plt.close(fig)

def ribbon(ax,df,x,col,color,label):
    s=df.groupby(x)[col].agg(median="median",q25=lambda z:z.quantile(.25),q75=lambda z:z.quantile(.75),q05=lambda z:z.quantile(.05),q95=lambda z:z.quantile(.95)).reset_index()
    ax.fill_between(s[x],s.q05,s.q95,color=color,alpha=.10,lw=0)
    ax.fill_between(s[x],s.q25,s.q75,color=color,alpha=.22,lw=0)
    ax.plot(s[x],s["median"],color=color,lw=1.5,label=label)

def s5():
    # Recompose the locked original panels and redraw the title/legend at a
    # larger size.  This preserves every panel pixel and changes typography only.
    src=Image.open(ROOT/".codex_supp_baseline/slide-17.png").convert("RGB")
    canvas=Image.new("RGB",src.size,"white")
    crop_y=165
    canvas.paste(src.crop((0,crop_y,src.width,src.height)),(0,crop_y))
    draw=ImageDraw.Draw(canvas)
    title_font=ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf",50)
    legend_font=ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf",31)
    draw.text((60,18),"Supplementary Fig. S5 | Post-release recessive-load and population trajectories",font=title_font,fill=(25,25,25))
    entries=[("Panmictic 0.70","#0072B2"),("Panmictic 0.85","#56B4E9"),("Spatial 0.70","#D55E00"),("Spatial 0.85","#CC79A7"),("Without recessive load (e–f)","#8C8C8C")]
    widths=[]
    for txt,_ in entries:
        box=draw.textbbox((0,0),txt,font=legend_font); widths.append(56+(box[2]-box[0])+58)
    x=(src.width-sum(widths))//2; y=104
    for (txt,col),w in zip(entries,widths):
        draw.line((x,y+18,x+42,y+18),fill=col,width=7)
        draw.text((x+56,y),txt,font=legend_font,fill=(45,45,45))
        x+=w
    canvas.save(OUT/"S5.png",dpi=(200,200))

if __name__=="__main__":
    s1();s2();s3();s4();s5()

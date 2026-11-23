# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 09:42:36 2024

@author: Xinyue
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn
import os
import array_process_spatial
import array_process_pan
import re
import single_simulation as ss
import mmap
import json
import matplotlib.colors as mcolors
from scipy import stats
# import warnings
# warnings.filterwarnings('error')

# 通用白色背景配置
plt.rcParams.update({
    # 背景颜色设置
    'figure.facecolor': 'white',    # 图形背景白色
    'axes.facecolor': 'white',      # 坐标轴区域背景白色
    'savefig.facecolor': 'white',   # 保存图片背景白色
    
    # 坐标轴设置
    'axes.edgecolor': 'black',      # 坐标轴颜色黑色
    'axes.linewidth': 0.8,          # 坐标轴线宽
    'axes.labelcolor': 'black',     # 坐标轴标签颜色
    
    # 网格线设置（保持正常显示但很浅）
    'axes.grid': False,              # 开启网格线
    'grid.color': 'lightgray',      # 网格线颜色浅灰
    'grid.alpha': 0.3,              # 网格线透明度
    'grid.linestyle': '--',         # 网格线样式虚线
    
    # # 字体设置
    # 'font.size': 12,                # 全局字体大小
    # 'axes.titlesize': 14,           # 标题字号
    # 'axes.labelsize': 12,           # 坐标轴标签字号
    # 'xtick.labelsize': 11,          # x轴刻度字号
    # 'ytick.labelsize': 11,          # y轴刻度字号
    # 'legend.fontsize': 11,          # 图例字号
    
    # 刻度设置
    'xtick.color': 'black',         # x轴刻度颜色
    'ytick.color': 'black',         # y轴刻度颜色
    'xtick.direction': 'out',       # 刻度方向向外
    'ytick.direction': 'out',       # 刻度方向向外
    
    # 图形设置
    'figure.dpi': 300,              # 图形分辨率
})


def laplace(x,mu,b):
    return [1/2/b*np.exp((i-mu)/b) if i<mu else 1/2/b*np.exp((mu-i)/b) for i in x]

def smooth(l):
    '''
    smooth the list 'l' by averaging the value of 10 continue values.

    Parameters
    ----------
    l : TYPE list
        DESCRIPTION.

    Returns 
    -------
    None.

    '''
    length = len(l)
    new_l = [np.mean(l[i:i+20]) for i in range(length-20)]
    return new_l

def lines(folder):
    '''
    plot the total effect size changing trend with generations,
    each line represents one simulaiton
    
    or split a single simulation output from whole file
    or plot the mutation heatmap

    Returns
    -------
    None.

    '''
    fig = plt.figure(dpi=300)
    #colors = list(matplotlib.colors.CSS4_COLORS.keys())
    #colors = list(matplotlib.colors.BASE_COLORS.keys())
    colors = ['slategrey','cornflowerblue','sienna','sandybrown']
    color_no = 0
    special_sim = 0
    fontsize = 15
    for root,dirs,files in os.walk(folder):
        for file in files:
            filename = root+file
            initial_effectsize = []
            with open(filename,'r') as f:
                content = f.read()
                sims = content.split('// Initial random seed:')
                sims = sims[1:]
                line_no = 1
                for sim in sims:
                    sup,mutation_effectsize,freq_df = single_simulation(sim)
                    #total_effect_size1,effectvar_mean,effectvar_sd,drive_rate,r2_rate,population_size,I = ss.whole_situation(sim,"drive conversion",False,False)
                    # row is mutations, column is generation from the first generation
                    mutation_effectsize = [float(i) for i in mutation_effectsize] #from the first genertaion
                    # plt.hist(mutation_effectsize)
                    # plt.show()
                    generations = len(freq_df.columns) # from the first generation
                    total_effect_size = []
                    
                    for i in range(generations):
                        tmp = sum(freq_df.iloc[:,i]*mutation_effectsize*2)#*population_size[i]
                        total_effect_size.append(tmp)
                    initial_effectsize.append(total_effect_size[0])
                    # total_effect_size = smooth(I)
                    # generations = len(total_effect_size)+20 # from release generation
                    if total_effect_size[-1]>0:
                        special_sim = sim
                    if line_no==1:
                        plt.plot(range(generations),total_effect_size,color=colors[color_no],label=file.replace(".out",''),alpha=1.0)#colors[color_no]
                        # special_sim = sim
                        #break
                    else:
                        if line_no < 21:
                            plt.plot(range(generations),total_effect_size,color=colors[color_no],alpha=1.0)#colors[color_no]#'slategray'
                        else:
                            break
                        
                        #ss.whole_situation(sim, "embryo resistance",True,True)
                        # ss.ind_dis_movie(sim)
                        #ss.mut_dis_movie(sim)
                        #ss.mutation_heatmap(sim)
                        # s,es,freq_df = single_simulation(sim)
                        # plt.hist(es)
                        # plt.show()
                    line_no = line_no + 1
                    print(np.mean(initial_effectsize))
                color_no = color_no+1
                    
        plt.xlabel("Week",fontsize=fontsize)
        plt.ylabel("Total effect size",fontsize=fontsize)#Total effect size"
        plt.legend()
        #plt.title(file,fontsize=fontsize)
        plt.show()
    
    # with open(folder+"mutnum800.txt",'w') as fw:
    #     fw.write(special_sim)
    
def double_heatmap(A,B,title):
    fontsize = 12
    nA = min(A.shape[0],B.shape[0])
    nB = min(A.shape[1],B.shape[1])
    fig, ax = plt.subplots(figsize=(4.4, 6),dpi=300)
    ax.set_xlim(0, nA)
    ax.set_ylim(0, nB)
    ax.invert_yaxis()

    # 定义颜色映射
    cmap = plt.cm.YlGnBu#Blues
    print(list(A.values))
    Avalues = [];Bvalues = []
    for i in range(nA):
        for j in range(nB):
            # 取两边的颜色
            if not np.isnan(A.iloc[i, j]):
                Avalues = Avalues + [A.iloc[i,j]]
            if not np.isnan(B.iloc[i, j]):
                Bvalues = Bvalues + [B.iloc[i,j]]
    mi = min(min(Avalues),min(Bvalues));ma = max(max(Avalues),max(Bvalues))
    norm = mcolors.Normalize(vmin=mi, vmax=ma)
    
    # 绘制格子
    for i in range(nA):
        for j in range(nB):
            # 取两边的颜色
            if not np.isnan(A.iloc[i, j]):
                #print(A.iloc[i, j])
                colorA = cmap(norm(A.iloc[i, j]))
                #print(colorA)
    
                # 多边形：上三角和下三角
                tri_up = plt.Polygon([[j, i], [j+1, i], [j+1, i+1]], color=colorA)
                ax.add_patch(tri_up)
                # 画分隔对角线
                ax.plot([j, j+1], [i, i+1], color='white', lw=0.8)
            if not np.isnan(B.iloc[i, j]):
                
                colorB = cmap(norm(B.iloc[i, j]))
                tri_down = plt.Polygon([[j, i], [j, i+1], [j+1, i+1]], color=colorB)
    
                ax.add_patch(tri_down)
    

            # # 写文字
            # ax.text(j+0.15, i+0.35, f'{A.iloc[i,j]:.0f}', color='black', ha='left', va='top', fontsize=8)
            # ax.text(j+0.85, i+0.85, f'{B.iloc[i,j]:.2f}', color='black', ha='right', va='bottom', fontsize=8)

    # 设置网格与标签
    ax.set_xticks(np.arange(nA)+0.5)
    ax.set_yticks(np.arange(nB)+0.5)
    ax.set_xticklabels(A.columns,fontsize=fontsize)#A.columns
    ax.set_yticklabels(B.index,fontsize=fontsize)#B.index
    ax.set_yticklabels(['']*len(B.index),fontsize=fontsize)
    ax.set_aspect('equal')
    ax.set_xlabel('Mutation locus number',fontsize=15)#A.columns.name
    #ax.set_ylabel('Parameter b',fontsize=15)#B.index.name
    # ax.set_xlabel("Mutation locus number",fontsize=15)
    # ax.set_ylabel("Laplace b",fontsize=15)
    
    # colorbar
    fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap),ax=ax,
    orientation='horizontal',
    pad=0.15)

    plt.title('Final attribute standard deviation',fontsize=15)#"Final attribute standard deviation"
    plt.tight_layout()
    plt.show()


def single_simulation(sim_output):
    '''
    read slim output and return a mutation effectsize list and 
    a dataframe that contains all mutation frequency change,
    the row is mutation, and the column is each generation

    Parameters
    ----------
    filename : TYPE string
        the name of slim file

    Returns
    -------
    mutation_effectsize : np.array
    
    freq_df : TYPE pandas.DataFrame
        DESCRIPTION.

    '''
    lines = sim_output.split('\n')
    freq_mat = []
    population_size = []
    suppressed = 0
    for line in lines:
        if line.startswith("NUMBER_OF_MUTATION:"):
            mutation_number = int((line.strip()).replace("NUMBER_OF_MUTATION: ", ''))
            for i in range(mutation_number):
                freq_mat.append([])
        if line.startswith("POPULATION_SIZE:"):
            # from the first generation
            population_size.append(int((line.strip()).replace("POPULATION_SIZE: ", '')))
        if line.startswith("MUTATION_EFFECTSIZE:"):
            mutation_effectsize = (line.replace("MUTATION_EFFECTSIZE: ", '')).split()
        if line.startswith("mutation"):
            con = line.split()
            if con[3]!='NAN':
                freq_mat[int(con[1])-10].append(float(con[3]))
        if line.startswith("SUPPRESSED"):
            suppressed = 1
    freq_df = pd.DataFrame(freq_mat)
    mutation_effectsize = np.array([float(i) for i in mutation_effectsize]) #from the first genertaion
    return suppressed,mutation_effectsize,freq_df

def spatial_statistic_data(filename,variable,genDiver,inbreeding):
    '''
    count up the different outcome frequency and statistic data of multiple simulations 
    of generations after chasing in spatial model.
    if the results are from simulations with inbreeding mutations, then the first of 'variable' 
    need to be the recessive mutation number per individual, and the second one is 
    the mutation locus number.

    Parameters
    ----------
    filename : TYPE string
        the excel data with the sheet name is "raw"
    variable : TYPE list with string
        the changed parameters to group simulations
    genDiver : TYPE bool
        whether the results from genetic diversity model
    Returns
    -------
    None.

    '''
    #filename = "multiple mutations test/mutation numbers/different_random_seed/mut_num_results.xlsx"#"multiple mutations test/pop_size/pop_size_results.xlsx"
    raw_data = pd.read_excel(filename,sheet_name='raw',index_col=None)
    if genDiver:
        raw_data['attribute initial sd'] = np.sqrt(raw_data['mutation_locus']*raw_data['laplace_b']*raw_data['laplace_b'])
    #raw_data = raw_data.loc[raw_data['drive_conversion']==0.7]
    print(raw_data)
    
    results = pd.DataFrame()
    groups = raw_data.groupby(by=variable)
    for name,group in groups:
        ## process the drive outcome and population dynamic data
        no = float(len(group))
        suppressed_without_chasing = sum(group['suppressed_without_chasing'])
        suppressed_with_chasing = sum(group['suppressed_with_chasing'])
        suppressed_with_chasing_rate = suppressed_with_chasing/no
        suppression = suppressed_without_chasing+suppressed_with_chasing
        drive_loss_with_chasing = len(group.loc[(group['drive_loss']==1) & (group['pop_persist']-group['gen_chasing_start']>5)])
        long_term_chasing = len(group.loc[(group['chasing_or_equilibrium']==1)])
        #avg_fertile_females = sum(group['avg_fertile_female']*group['duration_of_chasing'])/sum(group['duration_of_chasing'])
        avg_fertile_females = np.mean(group['avg_fertile_female'])
        #pop_size = np.mean(group['pop size'])
        # process the chasing gen
        suppressed_with_chasing = 0
        chasing_gen = 0
        pop_size = 0
        pop_size_CI = 0
        pop_size_list = []
        weighted_I=0
        weighted_I_SD = 0
        weighted_I_CI = 0
        var=0
        var_I=0
        I_SD=0
        I_w_list = []
        chasing_gen_threshold = 80 # from this generation, regrad it as chasing generation
        total_generation = 1000
        for index,row in group.iterrows():
            if (row['gen_suppressed']>=chasing_gen_threshold*row['generation time']) and (row['gen_suppressed']!=10000):
                suppressed_with_chasing = suppressed_with_chasing + 1
                chasing_gen = chasing_gen + row['gen_suppressed']/row['generation time']-chasing_gen_threshold
                pop_size_list.append(row['pop_size'])
                # I_w = I_w + row['weighted I']*row['pop_size']*(row['gen_suppressed']-chasing_gen_threshold*row['generation time'])
                I_w_list = I_w_list + [row['weighted I']]
            if (row['chasing_or_equilibrium']==1):
                chasing_gen = chasing_gen + total_generation - chasing_gen_threshold
            if (row['drive_loss']==1) and (row['pop_persist']>=chasing_gen_threshold*row['generation time']):
                chasing_gen = chasing_gen + row['pop_persist']/row['generation time']-chasing_gen_threshold
        #chasing_gen = sum(group['duration_of_chasing'])
        # print(name)
        # print(chasing_gen)
        # print(suppressed_with_chasing)
        if (chasing_gen!=0):
            suppression_rate_when_chasing = suppressed_with_chasing/chasing_gen
            suppression_confidence_up = suppressed_with_chasing/chasing_gen + 1.96*np.sqrt(suppression_rate_when_chasing*(1-suppression_rate_when_chasing)/chasing_gen)
            suppression_confidence_down = suppressed_with_chasing/chasing_gen - 1.96*np.sqrt(suppression_rate_when_chasing*(1-suppression_rate_when_chasing)/chasing_gen)
            driveloss_rate_when_chasing = drive_loss_with_chasing/chasing_gen
            driveloss_confidence_up = drive_loss_with_chasing/chasing_gen + 1.96*np.sqrt(driveloss_rate_when_chasing*(1-driveloss_rate_when_chasing)/chasing_gen)
            driveloss_confidence_down = drive_loss_with_chasing/chasing_gen - 1.96*np.sqrt(driveloss_rate_when_chasing*(1-driveloss_rate_when_chasing)/chasing_gen)
        else:
            suppression_rate_when_chasing = -1
            suppression_confidence_up = -1
            suppression_confidence_down = -1
            driveloss_rate_when_chasing = -1
            driveloss_confidence_up = -1
            driveloss_confidence_down = -1
        drive_loss_rate = sum(group['drive_loss'])/no
        driveloss_without_chasing =sum(group['drive_loss'])-drive_loss_with_chasing
        coe = group.loc[group['chasing_or_equilibrium']==1]#group.loc[group['gen_chasing_start']!=0]#group.loc[group['chasing_or_equilibrium']==1]
        if (len(coe)!=0):
            I = np.mean(coe['I'])
            I_SD = np.std(coe['I'])
            I_CI = 1.96*np.std(coe['I'])/np.sqrt(len(coe))
            #weighted_I = np.mean(coe['weighted I'])
            weighted_I_SD = np.std(coe['weighted I'])
            #weighted_I_CI = 1.96*np.std(coe['weighted I'])/np.sqrt(len(coe))
            # I_w = I_w + sum(coe['weighted I']*coe['pop_size']*(total_generation-chasing_gen_threshold))*np.mean(group['generation time'])
            I_w_list = I_w_list + list(coe['weighted I'])
            
            var = np.mean(coe['var_nni_across_time'])
            var_I = np.mean(coe['var_I_across_time'])
            pop_size_list = pop_size_list + list(coe['pop_size'])
        else:
            I = 0
            I_SD = 0
            I_CI=0
            #weighted_I = 0
            var = 0
            var_I = 0
            weighted_I_SD = 0
            #weighted_I_CI = 0
        if (len(pop_size_list)!=0):
            weighted_I = np.mean(I_w_list)
            weighted_I_CI = 1.96*np.std(I_w_list)/np.sqrt(len(I_w_list))
            pop_size = np.mean(pop_size_list)
            pop_size_SD = np.std(pop_size_list)
            pop_size_CI = pop_size_SD/np.sqrt(len(pop_size_list))*1.96
        equ_drive_freq = np.mean(coe.loc[:,'avg_drive_freq'])
        drive_freq_CI = np.std(coe.loc[:,'avg_drive_freq'])/np.sqrt(len(coe))*1.96    
          
        ## process the genetic diversity data
        
        if genDiver:
            attribute_initial_sd = np.mean(np.sqrt(group['mutation_locus']*group['laplace_b']*group['laplace_b']/5.12))
            attribute_initial_sd = round(attribute_initial_sd,3)
            #coe = group.loc[(group['average_effect_size']!=-1) & (group['drive_loss']!=1)] # simulations persisting at least 3.167*200 time steps
            coe = group.loc[group['chasing_or_equilibrium']==1]
            total_effectsize = np.mean(coe.loc[:,'average_effect_size'])
            total_effectsize_SD = np.std(coe.loc[:,'average_effect_size'])
            total_effectsize_CI = total_effectsize_SD/np.sqrt(len(coe))*1.96
            effectsize_reduction_after200 = np.mean(coe.loc[:,'effect_size_reduction_last300'])
            es_reduction_after200_CI_up = effectsize_reduction_after200 + np.std(coe.loc[:,'effect_size_reduction_last300'])/np.sqrt(len(coe))*1.96
            es_reduction_after200_CI_down = effectsize_reduction_after200 - np.std(coe.loc[:,'effect_size_reduction_last300'])/np.sqrt(len(coe))*1.96
            effectsize_reduction_first200 = np.mean(coe.loc[:,'effect_size_reduction_first200'])
            es_reduction_first200_CI_up = effectsize_reduction_first200 + np.std(coe.loc[:,'effect_size_reduction_first200'])/np.sqrt(len(coe))*1.96
            es_reduction_first200_CI_down = effectsize_reduction_first200 - np.std(coe.loc[:,'effect_size_reduction_first200'])/np.sqrt(len(coe))*1.96
            ch1_effectsize_reduction = np.mean(coe.loc[:,'ch1 effectsize reduction'])
            ch1_effectsize_reduction_CI = np.std(coe.loc[:,'ch1 effectsize reduction'])/np.sqrt(len(coe))*1.96
            ch2_effectsize_reduction = np.mean(coe.loc[:,'ch2 effectsize reduction'])
            ch2_effectsize_reduction_CI = np.std(coe.loc[:,'ch2 effectsize reduction'])/np.sqrt(len(coe))*1.96
            ch1_effectsize_reduction_first200 = np.mean(coe.loc[:,'ch1_effectsize_reduction_first200'])
            ch1_first200_CI = np.std(coe.loc[:,'ch1_effectsize_reduction_first200'])/np.sqrt(len(coe))*1.96
            ch1_effectsize_reduction_last300 = np.mean(coe.loc[:,'ch1_effectsize_reduction_last300'])
            ch1_last300_CI = np.std(coe.loc[:,'ch1_effectsize_reduction_last300'])/np.sqrt(len(coe))*1.96
            ch2_effectsize_reduction_first200 = np.mean(coe.loc[:,'ch2_effectsize_reduction_first200'])
            ch2_first200_CI = np.std(coe.loc[:,'ch2_effectsize_reduction_first200'])/np.sqrt(len(coe))*1.96
            ch2_effectsize_reduction_last300 = np.mean(coe.loc[:,'ch2_effectsize_reduction_last300'])
            ch2_last300_CI = np.std(coe.loc[:,'ch2_effectsize_reduction_last300'])/np.sqrt(len(coe))*1.96
            final_avg_variable = 0.5 + total_effectsize
            final_ev_sd = np.mean(coe.loc[:,'final_effectvar_sd'])
            final_ev_sd_SDamongsims = np.std(np.array(coe.loc[:,'final_effectvar_sd']))
            ev_sd_CI = final_ev_sd_SDamongsims/np.sqrt(len(coe))*1.96
        
            #di = float(name)
            #di = 0.091/(1-di**(-0.484))-0.091*di**0.7/(di-di**0.516)
            results = pd.concat([results,pd.DataFrame([[name,suppressed_without_chasing/no,suppressed_with_chasing_rate,
                                suppression/no,long_term_chasing/no,suppression_rate_when_chasing,suppression_confidence_up,
                                suppression_confidence_down,I,I_SD,weighted_I,var,var_I,drive_loss_with_chasing/no,
                                driveloss_rate_when_chasing,driveloss_confidence_up,driveloss_confidence_down,
                                driveloss_without_chasing/no,drive_loss_rate,1-suppressed_without_chasing/no-driveloss_without_chasing/no,
                                chasing_gen,avg_fertile_females,I_CI,pop_size,pop_size_CI,pop_size_SD,weighted_I_SD,weighted_I_CI,
                                total_effectsize,total_effectsize_SD,final_avg_variable,effectsize_reduction_after200,equ_drive_freq,es_reduction_after200_CI_down,
                                es_reduction_after200_CI_up,effectsize_reduction_first200,es_reduction_first200_CI_down,
                                es_reduction_first200_CI_up,total_effectsize_CI,drive_freq_CI,ch1_effectsize_reduction,ch1_effectsize_reduction_CI,
                                ch2_effectsize_reduction,ch2_effectsize_reduction_CI,ch1_effectsize_reduction_first200,ch1_effectsize_reduction_last300,
                                ch2_effectsize_reduction_first200,ch2_effectsize_reduction_last300,ch1_first200_CI,ch1_last300_CI,ch2_first200_CI,ch2_last300_CI,
                                attribute_initial_sd,final_ev_sd,ev_sd_CI,final_ev_sd_SDamongsims]])])
        elif inbreeding:
            coe = group.loc[group['chasing_or_equilibrium']==1]
            I_first200 = np.mean(coe.loc[:,'weightedI_first200'])
            I_first200_CI = np.std(coe.loc[:,'weightedI_first200'])/np.sqrt(len(coe))*1.96
            I_after200 = np.mean(coe.loc[:,'weightedI_after200'])
            I_after200_CI = np.std(coe.loc[:,'weightedI_after200'])/np.sqrt(len(coe))*1.96
            fitness_first200 = np.mean(coe.loc[:,'fitness_first200'])
            fitness_first200_CI = np.std(coe.loc[:,'fitness_first200'])/np.sqrt(len(coe))*1.96
            fitness_after200 = np.mean(coe.loc[:,'fitness_after200'])
            fitness_after200_CI = np.std(coe.loc[:,'fitness_after200'])/np.sqrt(len(coe))*1.96
            final_mutno_per_ind = np.mean(coe.loc[:,'final_mutno_per_ind'])
            final_mutno_per_ind_CI = np.std(coe.loc[:,'final_mutno_per_ind'])/np.sqrt(len(coe))*1.96
            final_fitness = np.mean(coe.loc[:,'final_fitness'])
            final_fitness_CI = np.std(coe.loc[:,'final_fitness'])/np.sqrt(len(coe))*1.96
            final_mutlocus_num = np.mean(coe.loc[:,'final_mutlocus_num'])
            final_mutlocus_num_CI = np.std(coe.loc[:,'final_mutlocus_num'])/np.sqrt(len(coe))*1.96
            
            
            results = pd.concat([results,pd.DataFrame([list(name)+[suppressed_without_chasing/no,suppressed_with_chasing_rate,
                                suppression/no,long_term_chasing/no,suppression_rate_when_chasing,suppression_confidence_up,
                                suppression_confidence_down,I,I_SD,weighted_I,var,var_I,drive_loss_with_chasing/no,
                                driveloss_rate_when_chasing,driveloss_confidence_up,driveloss_confidence_down,
                                driveloss_without_chasing/no,drive_loss_rate,1-suppressed_without_chasing/no-driveloss_without_chasing/no,
                                chasing_gen,avg_fertile_females,I_CI,pop_size,pop_size_CI,weighted_I_SD,weighted_I_CI,
                                equ_drive_freq,drive_freq_CI,final_mutno_per_ind,final_mutno_per_ind_CI,final_fitness,final_fitness_CI,
                                final_mutlocus_num,final_mutlocus_num_CI,I_first200,I_first200_CI,I_after200,I_after200_CI,fitness_first200,
                                fitness_first200_CI,fitness_after200,fitness_after200_CI]])])
        else:
            results = pd.concat([results,pd.DataFrame([list(name)+[suppressed_without_chasing/no,suppressed_with_chasing_rate,
            suppression/no,long_term_chasing/no,suppression_rate_when_chasing,suppression_confidence_up,
            suppression_confidence_down,I,I_SD,weighted_I,var,var_I,drive_loss_with_chasing/no,
            driveloss_rate_when_chasing,driveloss_confidence_up,driveloss_confidence_down,
            driveloss_without_chasing/no,drive_loss_rate,1-suppressed_without_chasing/no-driveloss_without_chasing/no,
            chasing_gen,avg_fertile_females,I_CI,pop_size,pop_size_CI,weighted_I_SD,weighted_I_CI,equ_drive_freq,drive_freq_CI]])])
    if genDiver:
        results.columns = variable+['suppressed without chasing rate','suppressed with chasing rate','suppression rate','long term chasing or equilibrium rate',
                                 'suppression rate when chasing','suppression rate up confidence','suppression rate down confidence',
                    'I','I_SD','weighted I','var nni across time','var I across time','drive loss with chasing rate','drive loss rate when chasing','driveloss rate up confidence','driveloss rate down confidence',
                    'drive loss rate without chasing','drive loss rate','chasing rate','p sample size','average fertile females','I_CI','pop size','popsize_CI','popsize SDamongSIMS',
                    'weighted_I_SD','weighted_I_CI','average total effect size','average total effectsize SDamongSIMS','average properties','effect size reduction after200','average drive frequency',
                        'reduction_after200_CI_down','reduction_after200_CI_up','effect size reduction first200',
                            'reduction_first200_CI_down','reduction_first200_CI_up','total_effectsize_CI','drive_freq_CI',
                            'ch1_effectsize_reduction','ch1_effectsize_reduction_CI','ch2_effectsize_reduction','ch2_effectsize_reduction_CI',
                        'ch1_effectsize_reduction_first200','ch1_effectsize_reduction_last300','ch2_effectsize_reduction_first200','ch2_effectsize_reduction_last300',
                        'ch1_es_reduction_first200_CI','ch1_es_reduction_last300_CI','ch2_es_reduction_first200_CI','ch2_es_reduction_last300_CI',
                        'property_initial_sd','property_final_sd','property_final_sd_CI','property_final_sd SDamongSIMS']  
    elif inbreeding:
        results.columns = variable+['suppressed without chasing rate','suppressed with chasing rate','suppression rate','long term chasing or equilibrium rate',
                                 'suppression rate when chasing','suppression rate up confidence','suppression rate down confidence',
                    'I','I_SD','weighted I','var nni across time','var I across time','drive loss with chasing rate','drive loss rate when chasing','driveloss rate up confidence','driveloss rate down confidence',
                    'drive loss rate without chasing','drive loss rate','chasing rate','p sample size','average fertile females','I_CI','pop size','popsize_CI','weighted_I_SD','weighted_I_CI',
                        'average drive frequency','drive_freq_CI','final_mutnum_per_ind','final_mutnum_per_ind_CI','final_fitness',
                        'final_fitness_CI','final_mutlocus_num','final_mutlocus_num_CI','I_first200','I_first200_CI','I_after200','I_after200_CI','fitness_first200',
                        'fitness_first200_CI','fitness_after200','fitness_after200_CI'] 
    else:
        results.columns = variable+['suppressed without chasing rate','suppressed with chasing rate','suppression rate','long term chasing or equilibrium rate',
                 'suppression rate when chasing','suppression rate up confidence','suppression rate down confidence',
    'I','I_SD','weighted I','var nni across time','var I across time','drive loss with chasing rate','drive loss rate when chasing','driveloss rate up confidence','driveloss rate down confidence',
    'drive loss rate without chasing','drive loss rate','chasing rate','p sample size','average fertile females','I_CI','pop size','popsize_CI','weighted_I_SD','weighted_I_CI','average drive frequency','drive_freq_CI']  
    
    write = pd.ExcelWriter(filename,mode='a',if_sheet_exists='replace')
    results.to_excel(write,sheet_name='processed',index=False)
    write.save()
    write.close()
    
    #results = pd.read_excel(filename,sheet_name="processed",index_col=None)
    if len(variable)==1:
        plt.figure(dpi=300)
        plt.plot(results.loc[:,variable[0]],results.loc[:,'suppressed without chasing rate'],'o--',label='suppressed without chasing')
        plt.plot(results.loc[:,variable[0]],results.loc[:,'suppressed with chasing rate'],'o--',label='suppressed with chasing')
        plt.plot(results.loc[:,variable[0]],results.loc[:,'long term chasing or equilibrium rate'],'o--',label='longterm chasing or equilibrium')
        plt.plot(results.loc[:,variable[0]],results.loc[:,'drive loss rate without chasing'],'o--',label='driveloss without chasing')
        plt.plot(results.loc[:,variable[0]],results.loc[:,'drive loss with chasing rate'],'o--',label='driveloss with chasing')
        plt.xlabel(variable[0])
        plt.ylabel('Outcome fraction')
        plt.legend()
        plt.show()
        
        plt.figure(dpi=300)
        plt.plot(results.loc[:,variable[0]],results.loc[:,'suppression rate'],'o--')
        plt.xlabel(variable[0])
        plt.ylabel('suppression rate')
        plt.legend()
        plt.show()
        
        plt.figure(dpi=300)
        plt.plot(results.loc[:,variable[0]],results.loc[:,"suppression rate when chasing"],'o--',label='suppression rate when chasing')
        plt.fill_between(results.loc[:,variable[0]], results.loc[:,"suppression rate up confidence"],results.loc[:,"suppression rate down confidence"],alpha=0.5)
        plt.plot(results.loc[:,variable[0]],results.loc[:,"drive loss rate when chasing"],'o--',label='drive loss rate when chasing')
        plt.fill_between(results.loc[:,variable[0]], results.loc[:,"driveloss rate up confidence"],results.loc[:,"driveloss rate down confidence"],alpha=0.5)
        plt.xlabel(variable[0])
        plt.ylabel("Probability of different outcome per generation")
        plt.legend()
        plt.show()
        
        plt.figure(dpi=300)
        plt.plot(results.loc[:,variable[0]],results.loc[:,"pop size"],'o--')
        plt.fill_between(results.loc[:,variable[0]], results.loc[:,"pop size"]-results.loc[:,'popsize_CI'], results.loc[:,"pop size"]+results.loc[:,'popsize_CI'],alpha=0.5)
        plt.xlabel(variable[0])
        plt.ylabel("Population size")
        plt.show()
        
        plt.figure(dpi=300)
        seaborn.violinplot(x=variable[0], y="pop_size", data=raw_data) #violinplot
        plt.xlabel(variable[0])
        plt.ylabel("Population size")
        plt.show()
        
        plt.figure(dpi=300)
        seaborn.boxplot(x=variable[0], y="pop_size", data=raw_data) #violinplot
        plt.xlabel(variable[0])
        plt.ylabel("Population size")
        plt.show()
        
        plt.figure(dpi=300)
        plt.plot(results.loc[:,variable[0]],results.loc[:,"weighted I"],'o--')
        plt.fill_between(results.loc[:,variable[0]], results.loc[:,"weighted I"]-results.loc[:,'weighted_I_CI'], results.loc[:,"weighted I"]+results.loc[:,'weighted_I_CI'],alpha=0.5)
        plt.xlabel(variable[0])
        plt.ylabel("Weighted I")
        plt.show()
        
        plt.figure(dpi=300)
        seaborn.boxplot(x=variable[0], y="weighted I", data=raw_data) #violinplot
        plt.xlabel(variable[0])
        plt.ylabel("weighted I")
        plt.show()
        
        if genDiver:
            plt.figure(dpi=300)
            plt.plot(results.loc[:,variable[0]],results.loc[:,"effect size reduction after200"],'o--',label='last 300 generations')
            plt.fill_between(results.loc[:,variable[0]], results.loc[:,"reduction_after200_CI_down"], results.loc[:,"reduction_after200_CI_up"],alpha=0.5)   
            plt.plot(results.loc[:,variable[0]],results.loc[:,"effect size reduction first200"],'o--',label='first 200 generations')
            plt.fill_between(results.loc[:,variable[0]], results.loc[:,"reduction_first200_CI_down"], results.loc[:,"reduction_first200_CI_up"],alpha=0.5)   
            plt.xlabel(variable[0])
            plt.ylabel("Effectsize reduction per generation")
            plt.legend()
            plt.show()
            
            plt.figure(dpi=300)
            plt.plot(results.loc[:,variable[0]],results.loc[:,"average total effect size"],'o--')
            plt.fill_between(results.loc[:,variable[0]], results.loc[:,"average total effect size"]-results.loc[:,'total_effectsize_CI'], results.loc[:,"average total effect size"]+results.loc[:,'total_effectsize_CI'],alpha=0.5)
            plt.xlabel(variable[0])
            plt.ylabel("Total effect size")
            plt.show()
            
            plt.figure(dpi=300)
            seaborn.violinplot(x=variable[0], y="average_effect_size", data=raw_data) #violinplot
            plt.xlabel(variable[0])
            plt.ylabel("Total effect size")
            plt.show()
            
            plt.figure(dpi=300)
            seaborn.boxplot(x=variable[0], y="average_effect_size", data=raw_data) #violinplot
            plt.xlabel(variable[0])
            plt.ylabel("Total effect size")
            plt.show()
            
            # x axis is total effect size, y axis is population size
            exp_data = raw_data.loc[raw_data.loc[:,'laplace_b']!=0]
            plt.figure(dpi=300)
            plt.scatter(exp_data.loc[:,'average_effect_size'],exp_data.loc[:,'pop_size'])
            plt.xlabel("Total effect size")
            plt.ylabel("Population size")
            plt.show()
            
            plt.figure(dpi=300)
            plt.plot(results.loc[:,variable[0]],results.loc[:,"average properties"],'o--')
            plt.fill_between(results.loc[:,variable[0]], results.loc[:,"average properties"]-results.loc[:,'total_effectsize_CI'], results.loc[:,"average properties"]+results.loc[:,'total_effectsize_CI'],alpha=0.5)
            plt.xlabel(variable[0])
            plt.ylabel("Average property")
            plt.show()
            
            plt.figure(dpi=300)
            plt.plot(results.loc[:,variable[0]],results.loc[:,"property_final_sd"],'o--')
            plt.fill_between(results.loc[:,variable[0]], results.loc[:,"property_final_sd"]-results.loc[:,'property_final_sd_CI'], results.loc[:,"property_final_sd"]+results.loc[:,'property_final_sd_CI'],alpha=0.5)
            plt.xlabel(variable[0])
            plt.ylabel("Final variance of population property")
            plt.show()
            
            plt.figure(dpi=300)
            seaborn.violinplot(x=variable[0], y="property_final_sd", data=raw_data) #violinplot
            plt.xlabel(variable[0])
            plt.ylabel("Variance reduction of population property")
            plt.show()
            
            plt.figure(dpi=300)
            seaborn.boxplot(x=variable[0], y="property_final_sd", data=raw_data) #violinplot
            plt.xlabel(variable[0])
            plt.ylabel("Variance reduction of population property")
            plt.show()
            
            plt.figure(dpi=300)
            plt.errorbar(results.loc[:,variable[0]],results.loc[:,"ch1_effectsize_reduction"],yerr=results.loc[:,"ch1_es_reduction_CI"],label='chromosome1')
            plt.errorbar(results.loc[:,variable[0]],results.loc[:,"ch2_effectsize_reduction"],yerr=results.loc[:,"ch2_es_reduction_CI"],label='chromosome2')
            #plt.errorbar(results.loc[:,variable[0]],results.loc[:,"ch3_effectsize_reduction"],yerr=results.loc[:,"ch3_es_reduction_CI"],label='chromosome3')
            plt.xlabel(variable[0])
            plt.ylabel("Effect size reduction per generation")
            plt.legend()
            plt.show()
        if inbreeding:
            plt.figure(dpi=300)
            plt.plot(results.loc[:,variable[0]],results.loc[:,"total mutfreq"],'o--')
            plt.fill_between(results.loc[:,variable[0]], results.loc[:,"total mutfreq"]-results.loc[:,"total_mutfreq_CI"], results.loc[:,"total mutfreq"]+results.loc[:,"total_mutfreq_CI"],alpha=0.5)
            plt.xlabel(variable[0])
            plt.ylabel("Average mutation frequency")
            plt.show()
        
    else:
        # plot heatmap 
        plt.figure(dpi=300)
        df_pivot = results.pivot(index=variable[1], columns=variable[0], values='pop size')
        df_sorted = df_pivot.sort_index(ascending=False)
        seaborn.heatmap(df_sorted, annot=True, fmt='.0f',cmap='YlGnBu')
        plt.title("Population size")
        plt.ylabel(variable[1])
        plt.xlabel(variable[0])
        plt.tight_layout()
        plt.show()
        
        plt.figure(dpi=300)
        df_pivot = results.pivot(index=variable[1], columns=variable[0], values='popsize SDamongSIMS')
        df_sorted = df_pivot.sort_index(ascending=False)
        seaborn.heatmap(df_sorted, annot=True,cmap='YlGnBu')
        plt.title("Population size sd among simulations")
        plt.ylabel(variable[1])
        plt.xlabel(variable[0])
        plt.tight_layout()
        plt.show()
        
        plt.figure(dpi=300)
        df_pivot = results.pivot(index=variable[1], columns=variable[0], values='average total effect size')
        df_sorted = df_pivot.sort_index(ascending=False)
        seaborn.heatmap(df_sorted, annot=True,cmap='YlGnBu')
        plt.title("average total effect size")
        plt.ylabel(variable[1])
        plt.xlabel(variable[0])
        plt.tight_layout()
        plt.show()
        
        plt.figure(dpi=300)
        df_pivot = results.pivot(index=variable[1], columns=variable[0], values='average total effectsize SDamongSIMS')
        df_sorted = df_pivot.sort_index(ascending=False)
        seaborn.heatmap(df_sorted, annot=True,cmap='YlGnBu')
        plt.title("average total effectsize SD among SIMS")
        plt.ylabel(variable[1])
        plt.xlabel(variable[0])
        plt.tight_layout()
        plt.show()
        
        plt.figure(dpi=300)
        df_pivot = results.pivot(index=variable[1], columns=variable[0], values='effect size reduction first200')
        df_sorted = df_pivot.sort_index(ascending=False)
        seaborn.heatmap(df_sorted, annot=True,cmap='YlGnBu')
        plt.title("effect size reduction first200")
        plt.ylabel(variable[1])
        plt.xlabel(variable[0])
        plt.tight_layout()
        plt.show()
        
        plt.figure(dpi=300)
        df_pivot = results.pivot(index=variable[1], columns=variable[0], values='effect size reduction after200')
        df_sorted = df_pivot.sort_index(ascending=False)
        seaborn.heatmap(df_sorted, annot=True,cmap='YlGnBu')
        plt.title("effect size reduction after200")
        plt.ylabel(variable[1])
        plt.xlabel(variable[0])
        plt.tight_layout()
        plt.show()
        
        plt.figure(dpi=300)
        df_pivot = results.pivot(index=variable[1], columns=variable[0], values='ch1_effectsize_reduction_first200')
        df_sorted = df_pivot.sort_index(ascending=False)
        seaborn.heatmap(df_sorted, annot=True,cmap='YlGnBu')
        plt.title("ch1_effectsize_reduction_first200")
        plt.ylabel(variable[1])
        plt.xlabel(variable[0])
        plt.tight_layout()
        plt.show()
        
        plt.figure(dpi=300)
        df_pivot = results.pivot(index=variable[1], columns=variable[0], values='ch1_effectsize_reduction_last300')
        df_sorted = df_pivot.sort_index(ascending=False)
        seaborn.heatmap(df_sorted, annot=True,cmap='YlGnBu')
        plt.title("ch1_effectsize_reduction_last300")
        plt.ylabel(variable[1])
        plt.xlabel(variable[0])
        plt.tight_layout()
        plt.show()
        
        plt.figure(dpi=300)
        df_pivot = results.pivot(index=variable[1], columns=variable[0], values='ch2_effectsize_reduction_first200')
        df_sorted = df_pivot.sort_index(ascending=False)
        seaborn.heatmap(df_sorted, annot=True,cmap='YlGnBu')
        plt.title("ch2_effectsize_reduction_first200")
        plt.ylabel(variable[1])
        plt.xlabel(variable[0])
        plt.tight_layout()
        plt.show()
        
        plt.figure(dpi=300)
        df_pivot = results.pivot(index=variable[1], columns=variable[0], values='ch2_effectsize_reduction_last300')
        df_sorted = df_pivot.sort_index(ascending=False)
        seaborn.heatmap(df_sorted, annot=True,cmap='YlGnBu')
        plt.title("ch2_effectsize_reduction_last300")
        plt.ylabel(variable[1])
        plt.xlabel(variable[0])
        plt.tight_layout()
        plt.show()
        
        plt.figure(dpi=300)
        df_pivot = results.pivot(index=variable[1], columns=variable[0], values='property_sd_reduction')
        df_sorted = df_pivot.sort_index(ascending=False)
        seaborn.heatmap(df_sorted, annot=True,cmap='YlGnBu')
        plt.title("property_sd_reduction")
        plt.ylabel(variable[1])
        plt.xlabel(variable[0])
        plt.tight_layout()
        plt.show()
        
        plt.figure(dpi=300)
        df_pivot = results.pivot(index=variable[1], columns=variable[0], values='property_sd_reduction SDamongSIMS')
        df_sorted = df_pivot.sort_index(ascending=False)
        seaborn.heatmap(df_sorted, annot=True,cmap='YlGnBu')
        plt.title("property_sd_reduction SD among simulations")
        plt.ylabel(variable[1])
        plt.xlabel(variable[0])
        plt.tight_layout()
        plt.show()
        
        # plot the same variance group
        
        
        # have two variable, plot line figure for single variable and heatmap
        groups = results.groupby(by=variable[0]) # seprerate according to the mutnum per individual
        # plt.figure(dpi=300)
        # for name,group in groups:
        #     group = group.sort_values(by=variable[1])
        #     plt.errorbar(group.loc[:,variable[1]],group.loc[:,'mutnum_per_ind'],yerr=group.loc[:,'mutnum_per_ind_CI'],label="mutnum per ind: "+str(name))
        # plt.xlabel(variable[1])
        # plt.ylabel('mutation number per individual')
        # plt.legend()
        # plt.show()
        for name,group in groups:
            group = group.sort_values(by=variable[0])
            # plt.figure(dpi=300)
            # plt.plot(group.loc[:,variable[1]],group.loc[:,'suppressed without chasing rate'],'o--',label='suppressed without chasing')
            # plt.plot(group.loc[:,variable[1]],group.loc[:,'suppressed with chasing rate'],'o--',label='suppressed with chasing')
            # plt.plot(group.loc[:,variable[1]],group.loc[:,'long term chasing or equilibrium rate'],'o--',label='longterm chasing or equilibrium')
            # plt.plot(group.loc[:,variable[1]],group.loc[:,'drive loss rate without chasing'],'o--',label='driveloss without chasing')
            # plt.plot(group.loc[:,variable[1]],group.loc[:,'drive loss with chasing rate'],'o--',label='driveloss with chasing')
            # plt.xlabel(variable[1])
            # plt.ylabel('Outcome fraction')
            # plt.title(variable[0]+" = "+str(name))
            # plt.legend()
            # plt.show()
            
            # plt.figure(dpi=300)
            # plt.plot(group.loc[:,variable[1]],group.loc[:,"suppression rate when chasing"],'o--',label='suppression rate when chasing')
            # plt.fill_between(group.loc[:,variable[1]], group.loc[:,"suppression rate up confidence"],group.loc[:,"suppression rate down confidence"],alpha=0.5)
            # plt.plot(group.loc[:,variable[1]],group.loc[:,"drive loss rate when chasing"],'o--',label='drive loss rate when chasing')
            # plt.fill_between(group.loc[:,variable[1]], group.loc[:,"driveloss rate up confidence"],group.loc[:,"driveloss rate down confidence"],alpha=0.5)
            # plt.xlabel(variable[1])
            # plt.ylabel("Probability of different outcome per generation")
            # plt.title(variable[0]+" = "+str(name))
            # plt.legend()
            # plt.show()
            
            plt.figure(dpi=300)
            plt.plot(group.loc[:,variable[1]],group.loc[:,"pop size"],'o--')
            plt.fill_between(group.loc[:,variable[1]], group.loc[:,"pop size"]-group.loc[:,'popsize_CI'], group.loc[:,"pop size"]+group.loc[:,'popsize_CI'],alpha=0.5)
            plt.xlabel(variable[1])
            plt.ylabel("Population size")
            plt.title(variable[0]+" = "+str(name))
            plt.show()
            
            plt.figure(dpi=300)
            plt.plot(group.loc[:,variable[1]],group.loc[:,"weighted I"],'o--')
            plt.fill_between(group.loc[:,variable[1]], group.loc[:,"weighted I"]-group.loc[:,'weighted_I_CI'], group.loc[:,"weighted I"]+group.loc[:,'weighted_I_CI'],alpha=0.5)
            plt.xlabel(variable[1])
            plt.ylabel("Weighted I")
            plt.title(variable[0]+" = "+str(name))
            plt.show()
            
            plt.figure(dpi=300)
            plt.plot(group.loc[:,variable[1]],group.loc[:,"average total effect size"],'o--',label='total')
            plt.fill_between(group.loc[:,variable[1]], group.loc[:,"average total effect size"]-group.loc[:,'total_effectsize_CI'], group.loc[:,"average total effect size"]+group.loc[:,'total_effectsize_CI'],alpha=0.5)
            plt.plot(group.loc[:,variable[1]],group.loc[:,"ch1_effectsize_reduction"],'o--',label='ch1')
            plt.fill_between(group.loc[:,variable[1]], group.loc[:,"ch1_effectsize_reduction"]-group.loc[:,'ch1_effectsize_reduction_CI'], group.loc[:,"ch1_effectsize_reduction"]+group.loc[:,'ch1_effectsize_reduction_CI'],alpha=0.5)
            plt.plot(group.loc[:,variable[1]],group.loc[:,"ch2_effectsize_reduction"],'o--',label='ch2')
            plt.fill_between(group.loc[:,variable[1]], group.loc[:,"ch2_effectsize_reduction"]-group.loc[:,'ch2_effectsize_reduction_CI'], group.loc[:,"ch2_effectsize_reduction"]+group.loc[:,'ch2_effectsize_reduction_CI'],alpha=0.5)
            plt.xlabel(variable[1])
            plt.ylabel("Effect size reduction")
            plt.title(variable[0]+" = "+str(name))
            plt.legend()
            plt.show()
            
            plt.figure(dpi=300)
            plt.plot(group.loc[:,variable[1]],group.loc[:,"effect size reduction first200"],'o--',label='first200')
            plt.fill_between(group.loc[:,variable[1]], group.loc[:,"reduction_first200_CI_down"], group.loc[:,"reduction_first200_CI_up"],alpha=0.5)
            plt.plot(group.loc[:,variable[1]],group.loc[:,"effect size reduction after200"],'o--',label='after200')
            plt.fill_between(group.loc[:,variable[1]], group.loc[:,"reduction_after200_CI_down"], group.loc[:,"reduction_after200_CI_up"],alpha=0.5)
            plt.xlabel(variable[1])
            plt.ylabel("Effect size reduction per generation")
            plt.title(variable[0]+" = "+str(name))
            plt.legend()
            plt.show()
        
        
        # seperate them according to one variable
        groups = results.groupby(by=variable[1]) # seprerate according to the mutation locus number
        # plt.figure(dpi=300)
        # for name,group in groups:
        #     group = group.sort_values(by=variable[0])
        #     plt.errorbar(group.loc[:,variable[0]],group.loc[:,'mutnum_per_ind'],yerr=group.loc[:,'mutnum_per_ind_CI'],label="mutation locus: "+str(name))
        # plt.xlabel(variable[0])
        # plt.ylabel('mutation number per individual')
        # plt.legend()
        # plt.show()
        
        for name,group in groups:
            group = group.sort_values(by=variable[1])
            # plt.figure(dpi=300)
            # plt.plot(group.loc[:,variable[0]],group.loc[:,'suppressed without chasing rate'],'o--',label='suppressed without chasing')
            # plt.plot(group.loc[:,variable[0]],group.loc[:,'suppressed with chasing rate'],'o--',label='suppressed with chasing')
            # plt.plot(group.loc[:,variable[0]],group.loc[:,'long term chasing or equilibrium rate'],'o--',label='longterm chasing or equilibrium')
            # plt.plot(group.loc[:,variable[0]],group.loc[:,'drive loss rate without chasing'],'o--',label='driveloss without chasing')
            # plt.plot(group.loc[:,variable[0]],group.loc[:,'drive loss with chasing rate'],'o--',label='driveloss with chasing')
            # plt.xlabel(variable[0])
            # plt.ylabel('Outcome fraction')
            # plt.title(variable[1]+" = "+str(name))
            # plt.legend()
            # plt.show()
            
            # plt.figure(dpi=300)
            # plt.plot(group.loc[:,variable[0]],group.loc[:,"suppression rate when chasing"],'o--',label='suppression rate when chasing')
            # plt.fill_between(group.loc[:,variable[0]], group.loc[:,"suppression rate up confidence"],group.loc[:,"suppression rate down confidence"],alpha=0.5)
            # plt.plot(group.loc[:,variable[0]],group.loc[:,"drive loss rate when chasing"],'o--',label='drive loss rate when chasing')
            # plt.fill_between(group.loc[:,variable[0]], group.loc[:,"driveloss rate up confidence"],group.loc[:,"driveloss rate down confidence"],alpha=0.5)
            # plt.xlabel(variable[0])
            # plt.ylabel("Probability of different outcome per generation")
            # plt.title(variable[1]+" = "+str(name))
            # plt.legend()
            # plt.show()
            
            plt.figure(dpi=300)
            plt.plot(group.loc[:,variable[0]],group.loc[:,"pop size"],'o--')
            plt.fill_between(group.loc[:,variable[0]], group.loc[:,"pop size"]-group.loc[:,'popsize_CI'], group.loc[:,"pop size"]+group.loc[:,'popsize_CI'],alpha=0.5)
            plt.xlabel(variable[0])
            plt.ylabel("Population size")
            plt.title(variable[1]+" = "+str(name))
            plt.show()
            
            plt.figure(dpi=300)
            plt.plot(group.loc[:,variable[0]],group.loc[:,"weighted I"],'o--')
            plt.fill_between(group.loc[:,variable[0]], group.loc[:,"weighted I"]-group.loc[:,'weighted_I_CI'], group.loc[:,"weighted I"]+group.loc[:,'weighted_I_CI'],alpha=0.5)
            plt.xlabel(variable[0])
            plt.ylabel("Weighted I")
            plt.title(variable[1]+" = "+str(name))
            plt.show()
            
            plt.figure(dpi=300)
            plt.plot(group.loc[:,variable[0]],group.loc[:,"average total effect size"],'o--',label='total')
            plt.fill_between(group.loc[:,variable[0]], group.loc[:,"average total effect size"]-group.loc[:,'total_effectsize_CI'], group.loc[:,"average total effect size"]+group.loc[:,'total_effectsize_CI'],alpha=0.5)
            plt.plot(group.loc[:,variable[0]],group.loc[:,"ch1_effectsize_reduction"],'o--',label='ch1')
            plt.fill_between(group.loc[:,variable[0]], group.loc[:,"ch1_effectsize_reduction"]-group.loc[:,'ch1_effectsize_reduction_CI'], group.loc[:,"ch1_effectsize_reduction"]+group.loc[:,'ch1_effectsize_reduction_CI'],alpha=0.5)
            plt.plot(group.loc[:,variable[0]],group.loc[:,"ch2_effectsize_reduction"],'o--',label='ch2')
            plt.fill_between(group.loc[:,variable[0]], group.loc[:,"ch2_effectsize_reduction"]-group.loc[:,'ch2_effectsize_reduction_CI'], group.loc[:,"ch2_effectsize_reduction"]+group.loc[:,'ch2_effectsize_reduction_CI'],alpha=0.5)
            plt.xlabel(variable[0])
            plt.ylabel("Effect size reduction")
            plt.title(variable[1]+" = "+str(name))
            plt.legend()
            plt.show()
            
            plt.figure(dpi=300)
            plt.plot(group.loc[:,variable[0]],group.loc[:,"effect size reduction first200"],'o--',label='first200')
            plt.fill_between(group.loc[:,variable[0]], group.loc[:,"reduction_first200_CI_down"], group.loc[:,"reduction_first200_CI_up"],alpha=0.5)
            plt.plot(group.loc[:,variable[0]],group.loc[:,"effect size reduction after200"],'o--',label='after200')
            plt.fill_between(group.loc[:,variable[0]], group.loc[:,"reduction_after200_CI_down"], group.loc[:,"reduction_after200_CI_up"],alpha=0.5)
            plt.xlabel(variable[0])
            plt.ylabel("Effect size reduction per generation")
            plt.title(variable[1]+" = "+str(name))
            plt.legend()
            plt.show()


        
            
def genDiver_vs_control_plot(genDiver,control,variable,title):
    '''

    Parameters
    ----------
    genDiver : dataframe
        DESCRIPTION.
    control : dataframe
        DESCRIPTION.
    variable : string
        DESCRIPTION.
    title : string
        DESCRIPTION.

    Returns
    -------
    None.

    '''
    
    '''
    plt.figure(dpi=300)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,'suppressed without chasing rate'],'o--',label='suppressed without chasing')
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,'suppressed with chasing rate'],'o--',label='suppressed with chasing')
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,'long term chasing or equilibrium rate'],'o--',label='longterm chasing or equilibrium')
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,'drive loss rate without chasing'],'o--',label='driveloss without chasing')
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,'drive loss with chasing rate'],'o--',label='driveloss with chasing')
    plt.xlabel(variable)
    plt.ylabel('Outcome fraction')
    plt.title(title + '/ With '+variable+' mutations')
    plt.legend()
    plt.show()
    plt.figure(dpi=300)
    plt.plot(control.loc[:,variable],control.loc[:,'suppressed without chasing rate'],'o--',label='suppressed without chasing')
    plt.plot(control.loc[:,variable],control.loc[:,'suppressed with chasing rate'],'o--',label='suppressed with chasing')
    plt.plot(control.loc[:,variable],control.loc[:,'long term chasing or equilibrium rate'],'o--',label='longterm chasing or equilibrium')
    plt.plot(control.loc[:,variable],control.loc[:,'drive loss rate without chasing'],'o--',label='driveloss without chasing')
    plt.plot(control.loc[:,variable],control.loc[:,'drive loss with chasing rate'],'o--',label='driveloss with chasing')
    plt.xlabel(variable)
    plt.ylabel('Outcome fraction')
    plt.title(title + '/ Control')
    plt.legend()
    plt.show()
    
    plt.figure(dpi=300)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,'suppressed without chasing rate'],'o--',label='genDiver: suppressed without chasing')
    plt.plot(control.loc[:,variable],control.loc[:,'suppressed without chasing rate'],'o--',label='control: suppressed without chasing')
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,'suppressed with chasing rate'],'o--',label='genDiver: suppressed with chasing')
    plt.plot(control.loc[:,variable],control.loc[:,'suppressed with chasing rate'],'o--',label='control: suppressed with chasing')
    plt.xlabel(variable)
    plt.ylabel('Outcome fraction')
    plt.title(title)
    plt.legend()
    plt.show()
    
    plt.figure(dpi=300)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,'suppression rate'],'o--',label='genDiver')
    plt.plot(control.loc[:,variable],control.loc[:,'suppression rate'],'o--',label='control')
    plt.xlabel(variable)
    plt.ylabel('Suppression rate')
    plt.title(title)
    plt.legend()
    plt.show()
    
    plt.figure(dpi=300)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,'long term chasing or equilibrium rate'],'o--',label='genDiver: longterm chasing or equilibrium')
    plt.plot(control.loc[:,variable],control.loc[:,'long term chasing or equilibrium rate'],'o--',label='control: longterm chasing or equilibrium')
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,'drive loss rate'],'o--',label='genDiver: driveloss')
    plt.plot(control.loc[:,variable],control.loc[:,'drive loss rate'],'o--',label='control: driveloss')
    plt.xlabel(variable)
    plt.ylabel('Outcome fraction')
    plt.title(title)
    plt.legend()
    plt.show()

    plt.figure(dpi=300)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,"suppression rate when chasing"],'o--',label='genDiver swc')
    plt.fill_between(genDiver.loc[:,variable], genDiver.loc[:,"suppression rate up confidence"],genDiver.loc[:,"suppression rate down confidence"],alpha=0.5)
    plt.plot(control.loc[:,variable],control.loc[:,"suppression rate when chasing"],'o--',label='control swc')
    plt.fill_between(control.loc[:,variable], control.loc[:,"suppression rate up confidence"],control.loc[:,"suppression rate down confidence"],alpha=0.5)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,"drive loss rate when chasing"],'o--',label='genDiver lwc')
    plt.fill_between(genDiver.loc[:,variable], genDiver.loc[:,"driveloss rate up confidence"],genDiver.loc[:,"driveloss rate down confidence"],alpha=0.5)
    plt.plot(control.loc[:,variable],control.loc[:,"drive loss rate when chasing"],'o--',label='control lwc')
    plt.fill_between(control.loc[:,variable], control.loc[:,"driveloss rate up confidence"],control.loc[:,"driveloss rate down confidence"],alpha=0.5)
    plt.xlabel(variable)
    plt.ylabel("Probability of different outcome per generation")
    plt.title(title)
    plt.legend()
    plt.show()
    
    '''
    
    plt.figure(dpi=300)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,"pop size"],'o--',label='genDiver')
    plt.fill_between(genDiver.loc[:,variable], genDiver.loc[:,"pop size"]-genDiver.loc[:,'popsize_CI'], genDiver.loc[:,"pop size"]+genDiver.loc[:,'popsize_CI'],alpha=0.5)
    plt.plot(control.loc[:,variable],control.loc[:,"pop size"],'o--',label='control')
    plt.fill_between(control.loc[:,variable], control.loc[:,"pop size"]-control.loc[:,'popsize_CI'], control.loc[:,"pop size"]+control.loc[:,'popsize_CI'],alpha=0.5)
    plt.xlabel(variable)
    plt.ylabel("Population size")
    plt.title(title)
    plt.legend()
    plt.show()
    
    plt.figure(dpi=300)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,"popsize SDamongSIMS"],'o--',label='genDiver')
    plt.plot(control.loc[:,variable],control.loc[:,"popsize SDamongSIMS"],'o--',label='control')
    plt.xlabel(variable)
    plt.ylabel("popsize SD among simulations")
    plt.title(title)
    plt.legend()
    plt.show()
    
    plt.figure(dpi=300)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,"weighted I"],'o--',label='genDiver')
    plt.fill_between(genDiver.loc[:,variable], genDiver.loc[:,"weighted I"]-genDiver.loc[:,'weighted_I_CI'], genDiver.loc[:,"weighted I"]+genDiver.loc[:,'weighted_I_CI'],alpha=0.5)
    plt.plot(control.loc[:,variable],control.loc[:,"weighted I"],'o--',label='control')
    plt.fill_between(control.loc[:,variable], control.loc[:,"weighted I"]-control.loc[:,'weighted_I_CI'], control.loc[:,"weighted I"]+control.loc[:,'weighted_I_CI'],alpha=0.5)
    plt.xlabel(variable)
    plt.ylabel("Weighted I")
    plt.title(title)
    plt.legend()
    plt.show()
    
    plt.figure(dpi=300)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,"average total effect size"],'o--',label='genDiver')
    plt.fill_between(genDiver.loc[:,variable], genDiver.loc[:,"average total effect size"]-genDiver.loc[:,'total_effectsize_CI'], genDiver.loc[:,"average total effect size"]+genDiver.loc[:,'total_effectsize_CI'],alpha=0.5)
    plt.plot(control.loc[:,variable],control.loc[:,"average total effect size"],'o--',label='control')
    plt.fill_between(control.loc[:,variable], control.loc[:,"average total effect size"]-control.loc[:,'total_effectsize_CI'], control.loc[:,"average total effect size"]+control.loc[:,'total_effectsize_CI'],alpha=0.5)
    plt.xlabel(variable)
    plt.ylabel("average total effect size")
    plt.title(title)
    plt.legend()
    plt.show()

    
    plt.figure(dpi=300)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,"effect size reduction first200"],'o--',label='genDiver: first 200 gens')
    plt.fill_between(genDiver.loc[:,variable], genDiver.loc[:,"reduction_first200_CI_down"],genDiver.loc[:,'reduction_first200_CI_up'],alpha=0.5)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,"effect size reduction after200"],'o--',label='genDiver: after 200 gens')
    plt.fill_between(genDiver.loc[:,variable], genDiver.loc[:,"reduction_after200_CI_down"],genDiver.loc[:,'reduction_after200_CI_up'],alpha=0.5)
    plt.plot(control.loc[:,variable],control.loc[:,"effect size reduction first200"],'o--',label='control: first 200 gens')
    plt.fill_between(control.loc[:,variable], control.loc[:,"reduction_first200_CI_down"],control.loc[:,'reduction_first200_CI_up'],alpha=0.5)
    plt.plot(control.loc[:,variable],control.loc[:,"effect size reduction after200"],'o--',label='control: after 200 gens')
    plt.fill_between(control.loc[:,variable], control.loc[:,"reduction_after200_CI_down"],control.loc[:,'reduction_after200_CI_up'],alpha=0.5)
    plt.xlabel(variable)
    plt.ylabel("effect size reduction per generation")
    plt.title(title)
    plt.legend()
    plt.show()
    
    plt.figure(dpi=300)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,"average total effectsize SDamongSIMS"],'o--',label='genDiver')
    plt.plot(control.loc[:,variable],control.loc[:,"average total effectsize SDamongSIMS"],'o--',label='control')
    plt.xlabel(variable)
    plt.ylabel("average total effectsize SD among simulations")
    plt.title(title)
    plt.legend()
    plt.show()
    
    plt.figure(dpi=300)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,"ch1_effectsize_reduction_first200"],'o--',label='genDiver: ch1 first 200 gens')
    plt.fill_between(genDiver.loc[:,variable], genDiver.loc[:,"ch1_effectsize_reduction_first200"]-genDiver.loc[:,'ch1_es_reduction_first200_CI'],genDiver.loc[:,"ch1_effectsize_reduction_first200"]+genDiver.loc[:,'ch1_es_reduction_first200_CI'],alpha=0.5)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,"ch2_effectsize_reduction_first200"],'o--',label='genDiver: ch2 first 200 gens')
    plt.fill_between(genDiver.loc[:,variable], genDiver.loc[:,"ch2_effectsize_reduction_first200"]-genDiver.loc[:,'ch2_es_reduction_first200_CI'],genDiver.loc[:,"ch2_effectsize_reduction_first200"]+genDiver.loc[:,'ch2_es_reduction_first200_CI'],alpha=0.5)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,"ch1_effectsize_reduction_last300"],'o--',label='genDiver: ch1 last 300 gens')
    plt.fill_between(genDiver.loc[:,variable], genDiver.loc[:,"ch1_effectsize_reduction_last300"]-genDiver.loc[:,'ch1_es_reduction_last300_CI'],genDiver.loc[:,"ch1_effectsize_reduction_last300"]+genDiver.loc[:,'ch1_es_reduction_last300_CI'],alpha=0.5)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,"ch2_effectsize_reduction_last300"],'o--',label='genDiver: ch2 last 300 gens')
    plt.fill_between(genDiver.loc[:,variable], genDiver.loc[:,"ch2_effectsize_reduction_last300"]-genDiver.loc[:,'ch2_es_reduction_last300_CI'],genDiver.loc[:,"ch2_effectsize_reduction_last300"]+genDiver.loc[:,'ch2_es_reduction_last300_CI'],alpha=0.5)

    plt.plot(control.loc[:,variable],control.loc[:,"ch1_effectsize_reduction_first200"],'o--',label='control: ch1 first 200 gens')
    plt.fill_between(control.loc[:,variable], control.loc[:,"ch1_effectsize_reduction_first200"]-control.loc[:,'ch1_es_reduction_first200_CI'],control.loc[:,"ch1_effectsize_reduction_first200"]+control.loc[:,'ch1_es_reduction_first200_CI'],alpha=0.5)
    plt.plot(control.loc[:,variable],control.loc[:,"ch2_effectsize_reduction_first200"],'o--',label='control: ch2 first 200 gens')
    plt.fill_between(control.loc[:,variable], control.loc[:,"ch2_effectsize_reduction_first200"]-control.loc[:,'ch2_es_reduction_first200_CI'],control.loc[:,"ch2_effectsize_reduction_first200"]+control.loc[:,'ch2_es_reduction_first200_CI'],alpha=0.5)
    plt.plot(control.loc[:,variable],control.loc[:,"ch1_effectsize_reduction_last300"],'o--',label='control: ch1 last 300 gens')
    plt.fill_between(control.loc[:,variable], control.loc[:,"ch1_effectsize_reduction_last300"]-control.loc[:,'ch1_es_reduction_last300_CI'],control.loc[:,"ch1_effectsize_reduction_last300"]+control.loc[:,'ch1_es_reduction_last300_CI'],alpha=0.5)
    plt.plot(control.loc[:,variable],control.loc[:,"ch2_effectsize_reduction_last300"],'o--',label='control: ch2 last 300 gens')
    plt.fill_between(control.loc[:,variable], control.loc[:,"ch2_effectsize_reduction_last300"]-control.loc[:,'ch2_es_reduction_last300_CI'],control.loc[:,"ch2_effectsize_reduction_last300"]+control.loc[:,'ch2_es_reduction_last300_CI'],alpha=0.5)
    plt.xlabel(variable)
    plt.ylabel("effect size reduction per generation")
    plt.title(title)
    plt.legend()
    plt.show()
    
    plt.figure(dpi=300)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,"property_sd_reduction"],'o--',label='genDiver')
    plt.fill_between(genDiver.loc[:,variable], genDiver.loc[:,"property_sd_reduction"]-genDiver.loc[:,'property_sd_reduction_CI'], genDiver.loc[:,"weighted I"]+genDiver.loc[:,'property_sd_reduction_CI'],alpha=0.5)
    plt.plot(control.loc[:,variable],control.loc[:,"property_sd_reduction"],'o--',label='control')
    plt.fill_between(control.loc[:,variable], control.loc[:,"property_sd_reduction"]-control.loc[:,'property_sd_reduction_CI'], control.loc[:,"weighted I"]+control.loc[:,'property_sd_reduction_CI'],alpha=0.5)
    plt.xlabel(variable)
    plt.ylabel("property_sd_reduction")
    plt.title(title)
    plt.legend()
    plt.show()
    
    plt.figure(dpi=300)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,"property_sd_reduction SDamongSIMS"],'o--',label='genDiver')
    plt.plot(control.loc[:,variable],control.loc[:,"property_sd_reduction SDamongSIMS"],'o--',label='control')
    plt.xlabel(variable)
    plt.ylabel("property reduction SD among simulations")
    plt.title(title)
    plt.legend()
    plt.show()

def genDiver_vs_control():
    variable = ['mutation_locus','laplace_b']#,'mutation_locus']#"drive_conversion" "embryo_resistance"
    # genDiver = pd.read_excel("multiple mutations test/drive conversion/mosquito model/mutnum_b/new_results.xlsx",sheet_name="processed",index_col=None)
    # control = pd.read_excel("multiple mutations test/drive conversion/mosquito model/mutnum_b/control/new_results_control.xlsx",sheet_name="processed",index_col=None)
    
    # genDiver = pd.read_excel("multiple mutations test/embryo resistance/mosquito model/control/noncontrol_results.xlsx",sheet_name="processed",index_col=None)
    # control = pd.read_excel("multiple mutations test/embryo resistance/mosquito model/control/results.xlsx",sheet_name="processed",index_col=None)
    
    # genDiver = pd.read_excel("multiple mutations test/embryo resistance/mosquito model/old results/70_new_results.xlsx",sheet_name="processed",index_col=None)
    # control = pd.read_excel("multiple mutations test/embryo resistance/mosquito model/old results/70control_mutnum_b_er_results.xlsx",sheet_name="processed",index_col=None)
    
    #data = pd.read_excel("multiple mutations test/pan vs spa/spatial/dc heatmap/mutnum_b_dc_spa_results.xlsx",sheet_name="processed",index_col=None)
    data = pd.read_excel("multiple mutations test/pan vs spa/panmictic/er heatmap/mutnum_b_er_pan_results.xlsx",sheet_name="processed",index_col=None)
    genDiver = data.loc[data['control']==False]
    control = data.loc[data['control']==True]
    
    if len(variable)==2:
        # plot heatmap
        ys = ['suppressed rate','suppressed gen','pop size','average total effect size','popsize SDamongSIMS','average total effectsize SDamongSIMS','property_final_sd']#'I',
        for y in ys:
            genDiver_pivot = genDiver.pivot(index=variable[1], columns=variable[0], values=y)
            genDiver_sorted = genDiver_pivot.sort_index(ascending=False)
            control_pivot = control.pivot(index=variable[1], columns=variable[0], values=y)
            control_sorted = control_pivot.sort_index(ascending=False)
            double_heatmap(genDiver_sorted, control_sorted,y)
        
        # seperately plot each variable
        genDiver_groups = genDiver.groupby('property_initial_sd')
        plt.figure(dpi=300)
        colors = ['#BFDFD2','#51999F','#7BC0CD','#ECB66C','#ED8D5A','#BFDFD2']#'#BFDFD2',
        i=0
        for sd,g in genDiver_groups:
            if sd!=0.015:
                # plt.plot(g.loc[:,'mutation_locus'],g.loc[:,"average total effect size"],'o--',label=sd,color=colors[i])
                # plt.fill_between(g.loc[:,'mutation_locus'], g.loc[:,"average total effect size"]-g.loc[:,'total_effectsize_CI'], g.loc[:,"average total effect size"]+g.loc[:,'total_effectsize_CI'],alpha=0.3,color=colors[i])
                plt.errorbar(g.loc[:,'mutation_locus'],sd-g.loc[:,"property_final_sd"],yerr=g.loc[:,'property_final_sd_CI'],fmt='o--',label="SD="+str(sd),color=colors[i],capsize=3)
                i = i+1
            

        plt.xlabel("Mutation locus number",fontsize=15)
        plt.ylabel("Final attribute standard deviation",fontsize=15)
        #plt.title(title)
        plt.legend()
        plt.show()
        
        # # for each single variable
        # control_groups = control.groupby('property_initial_sd')
        # for d_name,genDiver_group in genDiver_groups:
        #     for c_name,control_group in control_groups:
        #         if d_name == c_name:
        #             genDiver_vs_control_plot(genDiver_group, control_group, variable[0], 'property_initial_sd:'+str(d_name))
        # # next groupby the mutation locus number
        # genDiver_groups = genDiver.groupby(variable[1])
        # control_groups = control.groupby(variable[1])
        # for d_name,genDiver_group in genDiver_groups:
        #     for c_name,control_group in control_groups:
        #         if d_name == c_name:
        #             genDiver_vs_control_plot(genDiver_group, control_group, variable[0], variable[1]+":"+str(d_name))
                    
    else:
        genDiver_vs_control_plot(genDiver, control, variable[0],'inbreeding')
    return

def genDiver_vs_control_violin(file,figure_group_var,group_var,variable,title):
    fontsize = 15
    # genDiver = pd.read_excel("multiple mutations test/drive conversion/mosquito model/mutnum_b/new_results.xlsx",sheet_name="raw",index_col=None)
    # control = pd.read_excel("multiple mutations test/drive conversion/mosquito model/mutnum_b/control/new_results_control.xlsx",sheet_name="raw",index_col=None)
    # genDiver = pd.read_excel("multiple mutations test/embryo resistance/mosquito model/dc70/70mutnum_b_er_results.xlsx",sheet_name="raw",index_col=None)
    # control = pd.read_excel("multiple mutations test/embryo resistance/mosquito model/control/70control_mutnum_b_er_results.xlsx",sheet_name="raw",index_col=None)
    data = pd.read_excel(file,sheet_name="raw",index_col=None)
    data = data.loc[data['drive_conversion']!=0.9]
    
    if (variable=='pop_size'):
        data = data.loc[(data['suppressed']!=1) & (data['drive_loss']!=1)]
    if variable=='gen_suppressed':
        data = data.loc[data[variable]!=0]
    # genDiver = data.loc[data['control']==False]
    # control = data.loc[data['control']==True]
    genDiver = data.loc[data['inbreeding_mutation']==1]
    control = data.loc[data['inbreeding_mutation']==0]

    
    genDiver['group'] = 'with mutations'
    control['group'] = 'without mutations'
    # genDiver['property_initial_sd'] = round(np.sqrt(genDiver['mutation_locus']*genDiver['laplace_b']*genDiver['laplace_b']/5.12),3)
    # control['property_initial_sd'] = round(np.sqrt(control['mutation_locus']*control['laplace_b']*control['laplace_b']/5.12),3)
    color_map = {
        'with mutations': 'cornflowerblue',
        'without mutations': 'slategrey'
    }
    
    var='property_initial_sd'
    y = 'average_effect_size'#"weighted I"#"pop_size"#'average_effect_size'
    genDiver_groups = genDiver.groupby(figure_group_var)
    control_groups = control.groupby(figure_group_var)
    for d_name,genDiver_group in genDiver_groups:
        for c_name,control_group in control_groups:
            if d_name == c_name: # same variance
                if False:#variable == "suppressed":
                    plt.figure(figsize=(4,4),dpi=300)#figsize=(6,4) figsize=(3,4)
                    seaborn.set_style("ticks")
                    var_df = pd.concat([genDiver_group, control_group])
                    #var_df = var_df.loc[var_df[group_var]=="panmictic0.7"]
                    color_map = {
                        'with mutations': 'cornflowerblue',
                        'without mutations': 'slategrey'
                    }
        
                    # ===== 分组顺序 =====
                    x_levels = sorted(var_df[group_var].unique())
                    hue_levels = ['with mutations', 'without mutations']   # ⚠️ 确保顺序一致
                    offset = 0.12
                    print(x_levels)
        
                    x_base = np.arange(len(x_levels))
        
                    for i, hue in enumerate(hue_levels):
                        means = []
                        lower = []
                        upper = []
        
                        for x in x_levels:
                            vals = var_df[
                                (var_df[group_var] == x) &
                                (var_df['group'] == hue)
                            ][variable].dropna().values
        
                            mean = np.mean(vals)
                            sem = stats.sem(vals)
                            ci = stats.t.interval(
                                0.95, len(vals)-1, loc=mean, scale=sem
                            )
        
                            means.append(mean)
                            lower.append(mean - ci[0])
                            upper.append(ci[1] - mean)
                        print(means)
                        if len(x_levels) == 1:
                            x_pos = np.array([
                                x_base[0] + (-0.14 if hue == 'with mutations' else 0.14)
                            ])
                        else:
                            x_pos = x_base + (i - 0.5) * offset * 2
                        print(x_pos)
                        plt.errorbar(
                            x_pos, means,
                            yerr=[lower, upper],
                            fmt='o',
                            capsize=5,
                            markersize=6,
                            linewidth=2,color=color_map[hue],
                            label=hue
                        )
                    plt.xlabel("Drive conversion", fontsize=fontsize)#group_var
                    plt.ylabel('Drive loss rate', fontsize=fontsize)#variable
                    plt.xticks(x_base, x_levels, fontsize=12)
                    plt.yticks(fontsize=12)
                    plt.xlim(-0.5, 1.5)
                    if variable == 'average_effect_size':
                        plt.axhline(y=0.0, color='green', linestyle='--', linewidth=2)
                    plt.legend(title=None, loc='upper center',fontsize=9)
                    plt.show()
                if True:
                    plt.figure(dpi=300)#figsize=(5,4),
                    var_df = pd.concat([genDiver_group,control_group])
                    var_df = var_df.loc[var_df[group_var]!="panmictic0.85"]
                    seaborn.set_style("ticks")
                    ax = seaborn.violinplot(x=group_var,y=variable,hue='group',data = var_df,palette=color_map)
                    if variable == 'average_effect_size':
                        plt.axhline(y=0.0, color='green', linestyle='--', linewidth=2)
                    #plt.title("Population property standard deviation = "+str(d_name),fontsize=fontsize)
                    #plt.title(title + '  ' + figure_group_var + "=" + str(d_name))
                    #plt.title(title)
                    plt.xlabel(group_var,fontsize=fontsize)#group_var
                    plt.ylabel("Population size",fontsize=fontsize)#variable
                    plt.xticks(fontsize=12)
                    plt.yticks(fontsize=12)
                    #plt.ylim(0,20000)
                    ax.legend(title=None,loc='lower right',fontsize=11,frameon=False)#loc='lower center'
                    plt.show()
    return
    
def ch1_vs_ch2(file,group_var,var1,var2):
    # # plot heatmap
    # variable = ['mutation_locus','laplace_b']#,'mutation_locus']#"drive_conversion" "embryo_resistance"
    # data = pd.read_excel("multiple mutations test/drive conversion/mosquito model/mutnum_b/new_results.xlsx",sheet_name="processed",index_col=None)
        
    # y1 = 'ch1_effectsize_reduction'#'average total effect size'
    # y2 = 'ch2_effectsize_reduction'
    # # y1 = 'effect size reduction first200'
    # # y2 = 'effect size reduction after200'
    # ch1_pivot = data.pivot(index=variable[1], columns=variable[0], values=y1)
    # ch1_sorted = ch1_pivot.sort_index(ascending=False)
    # ch2_pivot = data.pivot(index=variable[1], columns=variable[0], values=y2)
    # ch2_sorted = ch2_pivot.sort_index(ascending=False)
    # double_heatmap(ch1_sorted, ch2_sorted,"ch1/ch2 effectsize reduction")
    # #double_heatmap(ch1_sorted, ch2_sorted,"first200/after200 effectsize reduction")
    
    
    
    # plot group errorbar
    plt.figure(dpi=300)#figsize=(6,4) figsize=(3,4)
    fontsize = 15
    seaborn.set_style("ticks")
    var_df = pd.read_excel(file,sheet_name='raw')
    var_df = var_df.loc[var_df['inbreeding_mutation']==1]
    var_df = var_df.loc[var_df['drive_conversion']!=0.9]
    #var_df = var_df.loc[var_df[var1]!=0]
    var_df = var_df.loc[(var_df['suppressed']!=1) & (var_df['drive_loss']!=1)]
    color_map = {
        var1: 'cornflowerblue',
        var2: 'slategrey'
    }

    # ===== 分组顺序 =====
    x_levels = sorted(var_df[group_var].unique())
    hue_levels = [var1,var2]   # ⚠️ 确保顺序一致
    offset = 0.05
    print(x_levels)

    x_base = np.arange(len(x_levels))

    for i, hue in enumerate(hue_levels):
        means = []
        lower = []
        upper = []

        for x in x_levels:
            vals = var_df[
                (var_df[group_var] == x)
            ][hue].dropna().values

            mean = np.mean(vals)
            sem = stats.sem(vals)
            ci = stats.t.interval(
                0.95, len(vals)-1, loc=mean, scale=sem
            )

            means.append(mean)
            lower.append(mean - ci[0])
            upper.append(ci[1] - mean)
        print(means)
        if len(x_levels) == 1:
            x_pos = np.array([
                x_base[0] + (-0.14 if hue == 'with mutations' else 0.14)
            ])
        else:
            x_pos = x_base + (i - 0.5) * offset * 2
        print(x_pos)
        plt.errorbar(
            x_pos, means,
            yerr=[lower, upper],
            fmt='o',
            capsize=5,
            markersize=6,
            linewidth=2,color=color_map[hue],
            label=hue
        )
        #plt.violinplot(vals)
    plt.xlabel(group_var, fontsize=fontsize)
    plt.ylabel("Fitness", fontsize=fontsize)
    plt.xticks(x_base, x_levels, fontsize=12)
    plt.yticks(fontsize=12)
    #plt.xlim(-0.3, 0.3)
    # if variable == 'average_effect_size':
    #     plt.axhline(y=0.0, color='green', linestyle='--', linewidth=2)
    plt.legend(title=None, loc='upper right',fontsize=9.5)
    plt.show()
    
    # plot group violin
    plot_df = var_df.melt(
    id_vars=[group_var],
    value_vars=[var1, var2],
    var_name="condition",
    value_name="value"
    )
    plt.figure(dpi=300)
    fontsize = 15
    seaborn.set_style("ticks")
    
    ax = seaborn.violinplot(
        data=plot_df,
        x=group_var,
        y="value",
        hue="condition",
        order=x_levels,
        hue_order=[var1, var2],
        palette=color_map,
        cut=0,
        inner="box",      # 或 "quartile" / None
        linewidth=1
    )
    
    plt.xlabel(group_var, fontsize=fontsize)
    plt.ylabel("Mutation number per individual", fontsize=fontsize)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    
    # set labels
    handles, labels = ax.get_legend_handles_labels()
    new_labels = ["equilibrium before drive release", "equilibrium after drive release"]
    ax.legend(
        handles,
        new_labels,
        title=None,
        loc="upper right",
        fontsize=11
    )
    #plt.legend(title=None, loc='upper right', fontsize=11)
    plt.show()
    return 

def single_genDiver_vs_control(genDiver_file,control_file,isPanmictic=False,effectvar='',genDiver_file1='',control_file1=''):
    fontsize=15
    # genDiver_file = "multiple mutations test/drive conversion/mosquito model/mutnum_b/raw_results/m400b0.0068.out"
    # control_file = "multiple mutations test/drive conversion/mosquito model/mutnum_b/control/raw_results/m400b0.0068.out"
    # genDiver_file = "multiple mutations test/embryo resistance/mosquito model/test/dc80mutnum100b0.04.out"
    # control_file = "multiple mutations test/embryo resistance/mosquito model/test/dc80mutnum100b0.04.out"

    #effectvar = "embryo resistance"
    with open(genDiver_file,'r') as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        positions = []
        pos = mm.find(b'// Initial random seed:')
        while pos != -1:
            positions.append(pos)
            pos = mm.find(b'// Initial random seed:', pos + 1)
        positions.append(len(mm))  # 结束位置
        i=46
        start = positions[i]
        end = positions[i + 1]
        genDiver_sim = mm[start:end].decode('utf-8', errors='replace')
        #ss.mutation_heatmap(genDiver_sim)
        total_effect_size,effectvar_mean,effectvar_sd,drive_rate,r2_rate,population_size,I = ss.whole_situation(genDiver_sim,effectvar,isPanmictic,False)
    with open(control_file,'r') as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        positions = []
        pos = mm.find(b'// Initial random seed:')
        while pos != -1:
            positions.append(pos)
            pos = mm.find(b'// Initial random seed:', pos + 1)
        positions.append(len(mm))  # 结束位置
        i=45
        start = positions[i]
        end = positions[i + 1]
        control_sim = mm[start:end].decode('utf-8', errors='replace')
        #ss.mutation_heatmap(control_sim)
        total_effect_size1,effectvar_mean1,effectvar_sd1,drive_rate1,r2_rate1,population_size1,I1 = ss.whole_situation(control_sim,effectvar,isPanmictic,False)
    # with open(genDiver_file1,'r') as f:
    #     mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    #     pos = mm.find(b'// Initial random seed:')
    #     pos1 = mm.find(b'// Initial random seed:', pos + 1)
    #     pos2 = mm.find(b'// Initial random seed:', pos1 + 1)
    #     pos3 = mm.find(b'// Initial random seed:', pos2 + 1)
    #     genDiver_sim = mm[pos2:pos3].decode('utf-8', errors='replace')
    #     #ss.mutation_heatmap(genDiver_sim)
    #     total_effect_size2,effectvar_mean2,effectvar_sd2,drive_rate2,r2_rate2,population_size2,I2 = ss.whole_situation(genDiver_sim,effectvar,False,False)
    # with open(control_file1,'r') as f:
    #     mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    #     pos = mm.find(b'// Initial random seed:')
    #     pos1 = mm.find(b'// Initial random seed:', pos + 1)
    #     pos2 = mm.find(b'// Initial random seed:', pos1 + 1)
    #     pos3 = mm.find(b'// Initial random seed:', pos2 + 1)
    #     control_sim = mm[pos1:pos2].decode('utf-8', errors='replace')
    #     #ss.mutation_heatmap(control_sim)
    #     total_effect_size3,effectvar_mean3,effectvar_sd3,drive_rate3,r2_rate3,population_size3,I3 = ss.whole_situation(control_sim,effectvar,False,False)
   

    plt.figure(dpi=300,facecolor='white')
    population_size = smooth(population_size[10:])
    population_size1 = smooth(population_size1[10:])
    # population_size2 = smooth(population_size2[10:])
    # population_size3 = smooth(population_size3[10:])
    plt.plot(range(len(population_size1)),population_size1,label="without mutations")
    plt.plot(range(len(population_size)),population_size,label="with mutations")
    # plt.plot(range(len(population_size3)),population_size3,label="dc70 without mutations")
    # plt.plot(range(len(population_size2)),population_size2,label="dc70 with mutations")
    plt.title("drive conversion = 0.70")
    plt.legend()
    plt.xlabel("Week",fontsize=fontsize)
    plt.ylabel("Population size",fontsize=fontsize)
    plt.show()
    
    if not isPanmictic:
        plt.figure(dpi=300)
        I = smooth(I)
        I1 = smooth(I1)
        # I3 = smooth(I3)
        # I2 = smooth(I2)
        plt.plot(range(len(I1)),I1,label="without mutations")
        plt.plot(range(len(I)),I,label="with mutations")
        # plt.plot(range(len(I3)),I3,label="dc70 without mutations")
        # plt.plot(range(len(I2)),I2,label="dc70 with mutations")
        plt.title("drive conversion = 0.70")
        plt.legend()
        plt.xlabel("Week",fontsize=fontsize)
        plt.ylabel("Nearest Neighbor Index",fontsize=fontsize)
        plt.show()

    plt.figure(dpi=300)#figsize=(6.5,5.7),
    drive_rate = smooth(drive_rate)
    drive_rate1 = smooth(drive_rate1)
    plt.plot(range(len(drive_rate1)),drive_rate1,label="drive allele: without mutations",color='slategrey')
    plt.plot(range(len(drive_rate)),drive_rate,label="drive allele: with mutations",color='cornflowerblue')
    r2_rate = smooth(r2_rate)
    r2_rate1 = smooth(r2_rate1)
    plt.plot(range(len(r2_rate1)),r2_rate1,label="resistance allele: without mutations",color='sandybrown')
    plt.plot(range(len(r2_rate)),r2_rate,label="resistance allele: with mutations",color='sienna')
    plt.legend(loc='center',fontsize=9)
    #plt.title("drive conversion = 0.70")
    # plt.set_xticks()
    # plt.set_yticks()
    plt.xlabel("Week",fontsize=fontsize)
    plt.ylabel("Allele frequency",fontsize=fontsize)
    plt.show()
    
    plt.figure(dpi=300)

    drive_rate = smooth(drive_rate)
    drive_rate1 = smooth(drive_rate1)
    plt.plot(range(len(drive_rate1)), drive_rate1,
             label="drive allele: without mutations", color='slategrey')
    plt.plot(range(len(drive_rate)), drive_rate,
             label="drive allele: with mutations", color='cornflowerblue')
    
    r2_rate = smooth(r2_rate)
    r2_rate1 = smooth(r2_rate1)
    plt.plot(range(len(r2_rate1)), r2_rate1,
             label="resistance allele: without mutations", color='sandybrown')
    plt.plot(range(len(r2_rate)), r2_rate,
             label="resistance allele: with mutations", color='sienna')
    
    plt.legend(loc='center', fontsize=9)
    
    plt.xlabel("Week", fontsize=fontsize)
    plt.ylabel("Allele frequency", fontsize=fontsize)
    
    # 🔑 强制显示 ticks（关键）
    ax = plt.gca()
    ax.tick_params(
    axis='both',
    which='both',
    direction='out',
    length=4,
    width=1,
    labelsize=fontsize,
    bottom=True,
    left=True
    )
    
    plt.show()
    
    ss.mutation_heatmap(genDiver_sim) 

    plt.figure(dpi=300)
    total_effect_size = smooth(total_effect_size)
    total_effect_size1 = smooth(total_effect_size1)
    plt.plot(range(len(total_effect_size1)),total_effect_size1,label="without functional mutations")
    plt.plot(range(len(total_effect_size)),total_effect_size,label="with functional mutations")
    plt.legend()
    plt.xlabel("Week",fontsize=fontsize)
    plt.ylabel("Total effect size",fontsize=fontsize)
    plt.title("drive conversion = 0.70")
    plt.show()
    
    # plt.figure(dpi=300)
    # effectvar_sd = smooth(effectvar_sd)
    # effectvar_sd1 = smooth(effectvar_sd1)
    # plt.plot(range(len(effectvar_sd1)),effectvar_sd1,label="without functional mutations")
    # plt.plot(range(len(effectvar_sd)),effectvar_sd,label="with functional mutations")
    # plt.legend()
    # plt.xlabel("Week",fontsize=fontsize)
    # plt.ylabel("Variance of drive conversion",fontsize=fontsize)
    # plt.title("drive conversion = 0.70")
    # plt.show()
    
    if not isPanmictic:
        fig, ax1 = plt.subplots(figsize=(6, 5),dpi=400)
        population_size = smooth(population_size[10:])
        population_size1 = smooth(population_size1[10:])
        ax1.plot(range(len(population_size1)),population_size1,color='royalblue',label="without functional mutations")
        ax1.plot(range(len(population_size)),population_size,color='orange',label="with functional mutations")
        #ax1.set_ylim(-100,0)#(2000,18000)
        ax2 = ax1.twinx()
        I = smooth(I)
        I1 = smooth(I1)
        ax2.plot(range(len(I1)),I1,color='mediumseagreen',label="without functional mutations")
        ax2.plot(range(len(I)),I,color='sienna',label="with functional mutations")
        #ax2.set_ylim(-1,0)#(0.55,0.87)
        ax1.set_xlabel("Week",fontsize=fontsize)
        ax1.set_ylabel("Population size",fontsize=fontsize)
        ax2.set_ylabel("Nearest Neighbor Index",fontsize=fontsize)
        ax1.legend(loc='best')
        ax2.legend(loc='center right')
        plt.title("drive conversion = 0.70")
        plt.show()
    
    
    
def lost_mutation(filefolder):
    '''
    statistic the ratio of loss mutation in all mutations grouped by the scale of effect size

    Returns
    -------
    None.

    '''
    lost_mutation_data = []
    mutation_frequency_data = []
    plt.figure(dpi=300)
    for root,dirs,files in os.walk(filefolder):
        for file in files:
            bino = 30
            lost_number = np.array([0]*bino)
            mutation_freq = np.array([0]*bino)
            # mean = float(file.replace('.out',''))
            # sd = -1760/2419*mean**2+1760/2419*mean
            # b = sd/np.sqrt(2*400*initial_frequency*2)
            pars = re.split(r'm|b|.out',file)
            print(pars)
            # b = float(pars[2])
            # mutnum = int(pars[1])
            b = float(pars[3])
            mutnum = int(pars[2])
            # initial_freq = 0.000002356225 / b**2
            # print(b)
            
            filename = root+file
            with open(filename,'r') as f:
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                positions = []
                pos = mm.find(b'// Initial random seed:')
                while pos != -1:
                    positions.append(pos)
                    pos = mm.find(b'// Initial random seed:', pos + 1)
                positions.append(len(mm))  # 结束位置
                print(positions)
                
                sim_no = 0
                for i in range(len(positions) - 1):
                    start = positions[i]
                    end = positions[i + 1]
                    sim = mm[start:end].decode('utf-8', errors='replace')
                    
                    suppressed,mutation_effectsize,freq_df = single_simulation(sim)
                    # plot total effect size change with generations
                    ss.whole_situation(sim,"drive conversion", False, False,file)
                    
                    if suppressed ==1:
                        continue
                    
                    sim_no = sim_no + 1
                    # compute lost mutations ratio
                    lost_effectsize = mutation_effectsize[freq_df.iloc[:,-1] < 0.0000005]
                    pe = 0.2
                    hist,binedges = np.histogram(lost_effectsize,bins=bino,range=(-pe/2,pe/2))
                    #n,bins,patch = plt.hist(lost_effectsize,bins=50,range=(-0.035,0.035),density=True,label="sd"+"{:.2f}".format(sd))
                    # plt.plot(bins,laplace(bins,0,sd/np.sqrt(2*400)))
                    # print(bins)
                    # print(patch)
                    # plt.show()
                    # print(hist)
                    lost_number = lost_number+np.array(hist)
                    
                    # compute the average mutation frequency in a certain range
                    freq = np.array(freq_df.iloc[:,-1])
                    interval = pe/bino
                    avg_freq_list = []
                    effect_size = []
                    for i in range(bino):
                        start = -pe/2 + i*interval
                        end = start + interval
                        avg_freq = freq[(mutation_effectsize > start) & (mutation_effectsize < end)]
                        if len(avg_freq)!=0:
                            avg_freq = np.mean(avg_freq)
                        else:
                            avg_freq = 0
                        effect_size = effect_size + [start+interval/2]
                        avg_freq_list = avg_freq_list + [avg_freq]
                    mutation_freq = mutation_freq + np.array(avg_freq_list)
                    
                lost_number = lost_number / sim_no
                mutation_freq = mutation_freq / sim_no
                print(lost_number)
                # compute the average mutation number of each range in population, total=400(m)
                # using the middlemost value as the average
                x = np.array(binedges[:-1])+pe/bino/2
                expected = mutnum * pe/bino * np.array(laplace(x,0,b))
                print(expected)
                loss_rate = lost_number/expected
                loss_rate = np.array([i if i<1 else 1 for i in loss_rate])
                lost_mutation_data.append(loss_rate)
                mutation_frequency_data.append(mutation_freq)
                plot_no = (expected > 0)
                plt.plot(x[plot_no],loss_rate[plot_no],label=file.replace('.out',''))
                #plt.plot(x[plot_no],loss_rate[plot_no],label="sd = "+"{:.2f}".format(sd))
                plt.plot(x[plot_no],mutation_freq[plot_no],label="mutfreq"+file.replace('.out',''))
                # plt.axhline(initial_freq)
        plt.xlabel("effect size")
        plt.ylabel("mutation loss rate")
        #plt.ylabel("mutation frequency")
        #plt.title(file)
        plt.legend()
        plt.show()  
        # with open("loss_rate.json", "w") as f:
        #     json.dump(lost_mutation_data, f)
        # with open("mutation_frequency.json", "w") as f:
        #     json.dump(mutation_frequency_data, f)
    return          
                

def main(folder):
    '''
    reprocess the raw slim output txt files, and delete the simulations with wrong output

    Returns
    -------
    None.

    '''
    #output_file = "multiple mutations test/drive conversion/mosquito model/mutnum_b/control/new_results.csv"
    output_file = folder + "results.csv"
    for root,dirs,files in os.walk(folder):
        for file in files:
            filename = root+file
            print(filename)
            
            with open(filename,'r') as f:
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                positions = []
                pos = mm.find(b'// Initial random seed:')
                while pos != -1:
                    positions.append(pos)
                    pos = mm.find(b'// Initial random seed:', pos + 1)
                positions.append(len(mm))  # 结束位置
                print(positions)
                
                sims = 0
                for i in range(len(positions) - 1):
                    start = positions[i]
                    end = positions[i + 1]
                    content = mm[start:end].decode('utf-8', errors='replace')
                    try:
                        dynamic_results = array_process_spatial.parse_slim(content)
                        gendiver_results = array_process_spatial.parse_inbreeding_slim(content)
                        # dynamic_results = array_process_pan.parse_slim(content)
                        # gendiver_results = array_process_pan.parse_inbreeding_slim(content)
                        
                        # if gendiver_results[1]==0:
                        #     with open(root+'error_candidate'+str(sims)+'.txt','w') as f0:
                        #         f0.write(content)
                        # else:
                        #     with open(root+'good'+str(sims)+'.txt','w') as f0:
                        #         f0.write(content)
                        with open(output_file,'a') as fo:
                            params = re.split('_|.out',file)#b|mutnum|.out
                            fo.write(params[0]+","+params[1]+","+params[2]+",")
                            for i in dynamic_results:
                                fo.write(str(i)+",")
                            for i in gendiver_results:
                                fo.write(str(i)+",")
                            fo.write("\n")
                    except RuntimeWarning as e:
                        print(e)
                    #print(sims)
                    sims = sims + 1
                mm.close()
            
                    
            # f = open(filename,'r')
            # content = f.read()
            # sims = content.split('// Initial random seed:')
            # sims = sims[1:]
            # wrong_index = []
            # print(len(sims))
            # for no in range(len(sims)):
            #     sim = str(sims[no])
            #     # purge the raw slim output file
            #     try:
            #         dynamic_results = array_process_spatial.parse_slim(sim)
            #         #gendiver_results = array_process_spatial.parse_gendiver_slim(sim)
            #         #inbred_results = array_process_spatial.parse_inbreeding_slim(sim)
            #         with open(output_file,'a') as fo:
            #             # params = re.split('nl|m|\.out',file)
            #             # fo.write(params[1]+","+params[2]+",")
            #             params = re.split('b|mutnum|.out',file)
            #             fo.write(params[0]+","+params[1]+","+params[2]+",")
            #             for i in dynamic_results:
            #                 fo.write(str(i)+",")
            #             # for i in gendiver_results:
            #             #     fo.write(str(i)+",")
            #             fo.write("\n")
            #     except Exception as e:
            #         wrong_index.append(no)
            #         print(e)
            #     continue
            
            # #     # plot single simulation
            # #     ss.inbreeding_test(sim)
            # # f.close()
            # # print(len(sims))
            # # purge and rewrite the raw slim output file
            # with open(filename,'w') as f0:
            #     for no in range(len(sims)):
            #         if no not in wrong_index:
            #             f0.write('// Initial random seed:\n'+sims[no]+'\n')
    return    
    

if __name__ == "__main__":
    #main("multiple mutations test/inbreeding/pan vs spa/new/raw_results/")
    #spatial_statistic_data("multiple mutations test/drive conversion/standard deviation/sd_results.xlsx",['distribution concave degree'],True)#"multiple mutations test/mutation numbers/different_random_seed/last100_results.xlsx")
    #spatial_statistic_data("multiple mutations test/drive conversion/mosquito model/mutnum_b/control/mutnum_b_results_control.xlsx",['mutation_locus','laplace_b'],True,False)
    #spatial_statistic_data("multiple mutations test/drive conversion/mosquito model/mutnum_b/control/new_results_control.xlsx",['mutation_locus','laplace_b'],True,False)
    #spatial_statistic_data("multiple mutations test/embryo resistance/mosquito model/old results/70_new_results.xlsx",['mutation_locus','laplace_b'],True,False)
    #spatial_statistic_data("multiple mutations test/embryo resistance/mosquito model/control/results.xlsx",['mutation_locus','laplace_b'],True,False)
    #spatial_statistic_data("multiple mutations test/embryo resistance/mosquito model/control/noncontrol_results.xlsx",['mutation_locus','laplace_b'],True,False)
    # spatial_statistic_data("multiple mutations test/inbreeding/mosquito model/zpg2/in_results.xlsx",['mutnum_per_individual'],False,True)
    # spatial_statistic_data("multiple mutations test/inbreeding/mosquito model/zpg2/in_control_results.xlsx",['mutnum_per_individual'],False,True)
    spatial_statistic_data("multiple mutations test/fitness/fit_results.xlsx",['somatic_fitness'],True,False)#"multiple mutations test/mutation numbers/different_random_seed/last100_results.xlsx")

    
    #lines("multiple mutations test/drive conversion/panmictic model/anoph_pan/test/")
    #lines("multiple mutations test/pan vs spa/spatial/dc heatmap/raw_results/test/")
    #genDiver_vs_control()
    #genDiver_vs_control_violin()
    #single_genDiver_vs_control()
    #ch1_vs_ch2()
    #lost_mutation("multiple mutations test/drive conversion/mosquito model/mutnum_b/test/")
    #lost_mutation("multiple mutations test/embryo resistance/mosquito model/test/70/")
    
    #ss.whole_situation("multiple mutations test/drive conversion/mosquito model/mutnum_b/test/increase sim.txt",'drive conversion',False,True)
    #ss.whole_situation("multiple mutations test/embryo resistance/mosquito model/control/control_raw_results/test/mutnum100b0.04.out",'embryo resistance',False,True)
    #ss.mutation_heatmap("multiple mutations test/drive conversion/mosquito model/mutnum_b/test/increase sim.txt")
    #ss.ind_dis_movie(special_sim)
    
    # # plot initial mutation frequency distribution
    # fontsize=15
    # # effectvar = "drive conversion"
    # # folder = "multiple mutations test/drive conversion/mosquito model/mutnum_b/single test/"
    # effectvar = "embryo resistance"
    # folder = "multiple mutations test/embryo resistance/mosquito model/test/70/"
    # for root,dirs,files in os.walk(folder):
    #     for file in files:
    #         filename = root+file
    #         # plot loss mutations
    #         mutnum = 400#int(file.replace('.out','').replace('mutnum',''))
    #         with open(filename,'r') as f:
    #             mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    #             positions = []
    #             pos = mm.find(b'// Initial random seed:')
    #             while pos != -1:
    #                 positions.append(pos)
    #                 pos = mm.find(b'// Initial random seed:', pos + 1)
    #             positions.append(len(mm))  # 结束位置
    #             #print(positions)
                
    #             for i in range(len(positions) - 1):
    #                 start = positions[i]
    #                 end = positions[i + 1]
    #                 sim = mm[start:end].decode('utf-8', errors='replace')
    #                 #ss.whole_situation(sim,effectvar,False,True)
    #                 #ss.ind_dis_movie(sim)
                    
    #                 #array_process_spatial.parse_slim(sim)
                    
    #                 suppressed,mutation_effectsize,freq_df = single_simulation(sim)
    #                 initial_freqs = freq_df.iloc[:,0]
    #                 final_freqs = freq_df.iloc[:,-1]
                    
    #                 gens = len(freq_df.columns)
    #                 lost_rate = []
    #                 for i in range(gens):
    #                     lost_rate = lost_rate + [sum(freq_df.iloc[:,i]==0)/mutnum]
    #                 plt.figure(dpi=300)
    #                 plt.plot(range(gens),lost_rate)
    #                 plt.xlabel("generations")
    #                 plt.ylabel("mutation loss rate")
    #                 plt.title(file)
    #                 plt.show()
    #                 plt.figure(dpi=300)
    #                 range_up = 0.5
    #                 counts, bins, patches = plt.hist(initial_freqs, bins=40, range=(0.00001,range_up),density=True, alpha=0.3,color='blue', edgecolor='black',label="Simulated distribution")
    #                 print(counts)
    #                 #counts, bins, patches = plt.hist(final_freqs, bins=20, range=(0.00001,0.5),density=True, alpha=0.3,color='red', edgecolor='black',label="after 500 gens")
    #                 print(counts)
    #                 #seaborn.kdeplot(initial_freqs, color="red", linewidth=2, label="KDE",clip=(0,0.5))
    #                 x = np.linspace(0,range_up,271)
    #                 plt.plot(x,0.1/x,label='theory frequency',color='peru',linewidth=2)
    #                 plt.xlim(-0.01,range_up)
    #                 x = [round(i,2) for i in np.linspace(0,0.5,11)]
    #                 plt.xticks(x,x)
    #                 plt.xlabel("Mutation frequency",fontsize=fontsize)
    #                 plt.ylabel("Density",fontsize=fontsize)
    #                 #plt.title(file)
    #                 plt.legend()
                
    #                 # # 设置 xticks 为 bin 的右边界
    #                 # tick_positions = np.round(bins[1:-1:4], 2)  # 只用右端（或中间点也可）
    #                 # plt.xticks(tick_positions, labels=tick_positions,fontsize=10, rotation=0, color='green')
                
    #                 plt.tight_layout()
    #                 plt.show()

# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 19:58:48 2024

@author: xinyue
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import imageio
import os
from scipy.stats import gaussian_kde

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
    'figure.dpi': 100,              # 图形分辨率
})


def norm(x, mu, sigma):
    return ((1/(np.sqrt(2*np.pi)*sigma))*np.exp(-0.5*(1/sigma*(x-mu))**2))
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
    new_l = [np.mean(l[i:i+10]) for i in range(length-10)]
    return new_l

def ind_dis_movie(filename):
    '''
    draw the gif of change of distribution of all individuals' attribute.

    Returns
    -------
    None.

    '''
    fontsize=25
    if os.path.exists(filename):
        with open(filename,'r') as f:#equilibrium_after_chasing.txt
            content = f.readlines()
    else:
        content = (str(filename)).split('\n')
    image_list = []
    gen = 0
    average_dc = []
    for line in content:
        if line.startswith("EFFECTSIZE_OF_INDIVIDUALS:"):
            gen = gen + 1
            if (gen % 100 ==1010 and gen<=500) or gen==11:#gen > 10:
                # from the first generation
                fig = plt.figure(figsize=(10,8),dpi=100)
                dcs = (line.strip()).replace("EFFECTSIZE_OF_INDIVIDUALS: ", '')
                dcs = [float(i) for i in dcs.split()]
                #print(dcs)
                plt.hist(dcs,bins=30,density=True)#range=(0,1)
                plt.xlim(0.0, 1.0)
                #plt.ylim(0,250)
                plt.xlabel('Attribute',fontsize=fontsize)
                plt.ylabel('Frequency density',fontsize=fontsize)
                plt.title("Generation "+str(gen),fontsize=fontsize)
                plt.savefig('temp.png')
                plt.show()
                plt.close()
                image_list.append(imageio.imread('temp.png'))
                average_dc = average_dc + [np.mean(dcs)]
    # imageio.mimsave('original_ind.gif', image_list, duration=0.1)
    # plt.plot(range(len(average_dc)),average_dc)
    # plt.show()
        
def mut_dis_movie(filename):
    '''
    draw the gif of change of distribution of mutation frequency

    Parameters
    ----------
    filename : TYPE string
        the raw slim output file

    Returns
    -------
    None.

    '''
    fontsize = 25
    if os.path.exists(filename):
        with open(filename,'r') as f:#equilibrium_after_chasing.txt
            content = f.readlines()
    else:
        content = (str(filename)).split('\n')
        
    freq_mat = []
    for line in content:
        if line.startswith("NUMBER_OF_MUTATION:"):
            mutation_number = int((line.strip()).replace("NUMBER_OF_MUTATION: ", ''))
            for i in range(mutation_number):
                freq_mat.append([])
        if line.startswith("mutation"):
            con = line.split()
            if con[3]!='NAN':
                freq_mat[int(con[1])-10].append(float(con[3]))
            
    freq_df = pd.DataFrame(freq_mat)
    # row is mutations, column is generation from the first generation
    columns = len(freq_df.columns)
    image_list = []
    generation = 0
    for col in range(columns):
        gen = list(freq_df.iloc[:,col])
        fig = plt.figure(figsize=(10,8),dpi=100)
        #plt.hist(gen,bins=50,range=(0.0,0.01),density=True)#range=(0,1)
        # KDE 拟合
        kde = gaussian_kde(gen)
        x_vals = np.linspace(min(gen), max(gen), 100)
        plt.plot(x_vals, kde(x_vals), color="red", linewidth=2, label="KDE密度曲线")
        plt.xlim(0.0, 0.5)
        #plt.ylim(0,15)
        plt.xlabel('mutation frequency',fontsize=fontsize)
        plt.ylabel('Frequency density',fontsize=fontsize)
        plt.title("Generation "+str(generation),fontsize=fontsize)
        generation = generation + 1 
        #plt.savefig('temp.png')
        plt.show()
    #     plt.close()
    #     image_list.append(imageio.imread('temp.png'))
    # imageio.mimsave('pic1_fitcr.gif', image_list, duration=0.03)
    # plt.show()
    return
    
        
def dgrp_dis():
    '''
    experiment data from 'CRISPR Gene Drive Efficiency and Resistance Rate 
    Is Highly Heritable with No Common Genetic Loci of Large Effect'
    and simulated distribution of different drive conversion rate.

    Returns
    -------
    None.

    '''
    fontsize = 15
    colors = ['cornflowerblue','salmon','slategray','yellowgreen','sandybrown','firebrick']
    # the experimental data
    df = pd.read_excel('Supplemental Material for Champer et al, 2019.xlsx',sheet_name='Data S1 DGRP Line Totals')#Data S1 DGRP Line Totals
    dependent_variable = ["drive conversion","embryo resistance"]
    dependent_index = 0
    if (dependent_index == 0):
        # for drive conversion
        # mean of dc is 0.516
        # plt.hist(df['Drive Conversion Efficiency'],bins=15,density=True,label='128 DGRP lines')
        # plt.title('drive converison of 128 DGRP lines')
        # plt.show()
    
        # the simulation distribution -- the sum of Laplace distribution of number of n
        # mutation_numbers = 400*0.1*2
        # means = np.linspace(0.6,0.95,2)
        # means = [0.516]+list(means)
        # sds = []
        # for mean in means:
        #     di = 100 # the concave degree of the changing curve
        #     sd = 0.091/(1-di**(-0.484))-0.091*di**mean/(di-di**0.516)
        #     sds = sds+[sd]
        #     b = sd/np.sqrt(2*mutation_numbers)#np.sqrt(1/500/625)
            
        #     repeats = 1000
        #     ind_dcs = []
        #     for i in range(repeats):
        #         effect_sizes = np.random.laplace(0,b,int(mutation_numbers))
        #         ind_dcs = ind_dcs + [mean+sum(effect_sizes)]
        #     plt.hist(ind_dcs,bins=30,density=True,alpha=0.5,label='mean = '+"{:.2f}".format(mean))
        # plt.title("distribution of drive conversion")
        # plt.legend()
        # plt.show()
        
        # plt.figure(dpi=300)
        # plt.plot(means,sds)
        # plt.xlabel("mean of drive conversion")
        # plt.ylabel("standard deviation of distribution")
        
        #bs = [0.0048,0.0068,0.0096,0.0136,0.0192] # for drive conversion
        #bs = [0.014,0.020,0.028,0.040,0.056] # for embryo resistance
        bs = [0.016,0.0226,0.0453] # for somatic fitness
        #ms = []
        plt.figure(dpi=300)
        color_no =0
        range_up = 0.06
        for b in bs:
            # for the distribution of single effect size (part 1)
            effectsizes = np.random.laplace(0,b,10000)
            n,bins,patch = plt.hist(effectsizes,bins=50,density=True,alpha=0.0,range=(-range_up,range_up))#,label='sd = '+"{:.2f}".format(sd))
            #print(bins)
            plt.plot(bins,laplace(bins,np.mean(effectsizes),b),color=colors[color_no],label='b = '+"{:.4f}".format(b))
            color_no = color_no + 1
            
        # (part 1)
        plt.xlim(-range_up,range_up)
        plt.xlabel("Mutation effect size (c)",fontsize=fontsize)
        plt.ylabel("Mutation density",fontsize=fontsize)
        plt.title("Mutations affecting drive conversion",fontsize=fontsize)
        plt.legend()
        plt.show()
        
        plt.figure(dpi=300)
        mean=0.5#0.41
        color_no =0
        for b in bs:
            mutation_number = 0.1414**2/2/b/b# mutation number per individual
            print(mutation_number)
            repeats = 1000
            ind_dcs = []
            for i in range(repeats):
                effect_sizes = np.random.laplace(0,b,int(mutation_number))
                ind_dcs = ind_dcs + [mean+sum(effect_sizes)] # for dc, er, inbreeding
                #ind_dcs = ind_dcs + [(mean+sum(effect_sizes))/mean*0.038] # for dispersal ability
            n,bins,patch = plt.hist(ind_dcs,bins=40,density=True,alpha=0.0)#,label='sd = '+"{:.2f}".format(sd))
            plt.plot(bins,norm(bins,np.mean(ind_dcs),np.std(ind_dcs)),color=colors[color_no],label='b = '+"{:.4f}".format(b))
            color_no = color_no + 1
        # # for drive conversion
        # n,bins,patch = plt.hist(df['Drive Conversion Efficiency'],bins=15,density=True,range=(0.2,0.8),alpha=0.5,label='128 DGRP lines')
        # plt.plot(bins,norm(bins,np.mean(df['Drive Conversion Efficiency']),np.std(df['Drive Conversion Efficiency'])),color=colors[color_no],label="128 DGRP lines")
        # plt.xlim(0.25,1.0)
        # plt.ylim(0,28)
        plt.xlabel("Drive conversion", fontsize=fontsize)
        plt.ylabel("Density in popultaion",fontsize=fontsize)
        plt.title("Distribution of drive conversion",fontsize=fontsize)
        
        # for embryo resistance
        # x = df['Embryo r2 Formation Rate (in flies with the drive)']
        # n,bins,patch = plt.hist(x,bins=25,density=True,alpha=0.5,label="128 DGRP lines")
        # plt.plot(bins,norm(bins,np.mean(x),np.std(x)),color=colors[color_no],label="128 DGRP lines")
        # plt.xlim(0.0,0.9)
        # plt.ylim(0,10)
        # # plt.xticks(fontsize=fontsize)
        # # plt.yticks(fontsize=fontsize)
        # plt.xlabel("Embryo resistance", fontsize=fontsize)
        # plt.ylabel("Density in popultaion",fontsize=fontsize)
        # plt.title("Distribution of embryo resistance",fontsize=fontsize)
        plt.legend()
        plt.show()
    else:
        # for embryo resistance
        fig = plt.figure(dpi=300)
        # mean of er is 0.41
        x = df['Embryo r2 Formation Rate (in flies with the drive)']
        n,bins,patch = plt.hist(x,bins=25,density=True,label="128 DGRP")
        plt.plot(bins,norm(bins,np.mean(x),np.std(x)),label="128 DGRP")
        plt.title('embryo resistance of 128 DGRP lines')
        plt.show()
        # the simulation distribution -- the sum of Laplace distribution of number of n
        mutation_numbers = int(400*0.1*2)
        means = np.linspace(0.125,0.875,7)
        means = list(means)
        sds = []
        for mean in means:
            sd = -1760/2419*mean**2+1760/2419*mean
            sds = sds+[sd]
            b = sd/np.sqrt(2*mutation_numbers)#np.sqrt(1/500/625)
            repeats = 1000 # 
            ind_dcs = []
            print(b)
            # # for the distribution of single effect size (part 1)
            # effectsizes = np.random.laplace(0,b,10000)
            # n,bins,patch = plt.hist(effectsizes,bins=50,density=True,alpha=0.5,range=(-0.03,0.03))#,label='sd = '+"{:.2f}".format(sd))
            # #print(bins)
            # plt.plot(bins,laplace(bins,np.mean(effectsizes),b),label='sd = '+"{:.2f}".format(sd))
            
            # for the distribution of total effect size
            for i in range(repeats):
                effect_sizes = np.random.laplace(0,b,mutation_numbers)
                ind_dcs = ind_dcs + [mean+sum(effect_sizes)]
            ind_dcs = [0 if i<0 else i for i in ind_dcs]
            ind_dcs = [1 if i>1 else i for i in ind_dcs]
            n,bins,patch = plt.hist(ind_dcs,bins=30,density=True,alpha=0.5)#,label='sd = '+"{:.2f}".format(sd))
            plt.plot(bins,norm(bins,np.mean(ind_dcs),np.std(ind_dcs)),label='sd = '+"{:.2f}".format(sd))
    
        # (part 1)
        plt.xlabel("effect size")
        plt.ylabel("mutation numbers")
        plt.title("distribution of embryo resistance")
        plt.legend()
        plt.show()
        
        # plt.figure(dpi=300)
        # plt.plot(means,sds)
    

def single_inbreeding_sim(filename,title):
    '''
    plot the outcome of a single simulation with generations
    for inbreeding slim output in anopholes gambia spatial model

    Parameters
    ----------
    filename : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    '''
    #mutation_heatmap(filename)
    fontsize = 15
    freq_mat = []
    
        
    df1 = pd.DataFrame()
    df2 = pd.DataFrame()        
        
    for line in content:
        if line.startswith("NUMBER_OF_MUTATION:"):
            mutation_number = int((line.strip()).replace("NUMBER_OF_MUTATION: ", ''))
            for i in range(mutation_number):
                freq_mat.append([])
        if line.startswith("POPULATION_SIZE:"):
            # from the first generation
            pop_size = int((line.strip()).replace("POPULATION_SIZE: ", ''))
        if line.startswith("MUTATION_POSITIONS:"):
            mutation_positions = (line.replace("MUTATION_POSITIONS: ", '')).split()
        if line.startswith("mutation"):
            con = line.split()
            if con[3]!='NAN':
                freq_mat[int(con[1])-10].append(float(con[3]))
        if line.startswith('GEN:'):
            line1 = line.strip()
            line1 = line1.split(' ')
            df1 = pd.concat([df1,pd.DataFrame([[int(line1[1]),float(line1[3]),pop_size,float(line1[5])]])])#,float(line1[5])
        if line.startswith('WT_AL'):
            line2 = line.strip()
            line2 = line2.split(' ')
            df2 = pd.concat([df2,pd.DataFrame([[int(line2[1]),int(line2[2]),int(line2[3]),float(line2[4]),float(line2[6]),float(line2[8])]])])
    
    freq_df = pd.DataFrame(freq_mat)
    # row is mutations, column is generation from the first generation
    mutation_positions = [int(i) for i in mutation_positions]
    generations = len(freq_mat[0])
    average_mutation_frequency = []
    for i in range(len(freq_df.columns)):
        average_mutation_frequency.append(np.mean(freq_df.iloc[:,i]))
        
    if (len(df1)!=0):
        df1.columns = ['gen','drive frequency','pop size','r2 frequency']
    if (len(df2)!=0):
        # print(df1)
        # print(df2)
        df2.columns = ['wt allele number','gen','pop size','rate drive carriers','average nni','var nni']
        df = df2#pd.merge(df1,df2,how='right')# how='right',on=['gen','pop size']
        # plt.figure(dpi=300)
        # plt.plot(df['gen'],df['average nni'])
        # try:
        #     lostall_gen = average_mutation_frequency.index(0.0)
        #     plt.axvline(lostall_gen,color='orange')  
        # except:
        #     pass
        # plt.xlabel("Generation")
        # plt.ylabel("Average NNI")
        # plt.show()
    else:
        df = df1
    
    # plt.figure(dpi=300)
    # plt.plot(range(generations),average_mutation_frequency)
    # plt.ylabel("mean of all mutations frequency",fontsize=fontsize)
    # plt.xlabel("Generation",fontsize=fontsize)
    # plt.title(title)
    # plt.show()
    
    # plt.figure(dpi=300)
    # plt.plot(df['gen'],df['pop size'])
    # plt.ylabel("population size",fontsize=fontsize)
    # plt.xlabel("Generation",fontsize=fontsize)
    # plt.title(title)
    # plt.show()
    
    # plt.figure(dpi=300)
    # plt.plot(range(9,len(df)+9),df['drive frequency'],label="drive")
    # plt.plot(range(9,len(df)+9),df['r2 frequency'],label="r2")
    # plt.plot(range(9,len(df)+9),1-df['drive frequency']-df['r2 frequency'],label="wt")
    # plt.ylabel("Allele frequency",fontsize=fontsize)
    # plt.xlabel("Generation",fontsize=fontsize)
    # plt.legend()
    # plt.show()
        
    return average_mutation_frequency

def whole_situation(filename,effectvar,isPanmictic,Plot,title="figure"):
    '''
    process a raw slim output file to get the effect size change on each chromosome,
    population size change, and drive, r2 allele frequency change
    for drive conversion and embryo resistance

    Parameters
    ----------
    filename : TYPE string
        DESCRIPTION.
    effectvar : TYPE string
        the variable name which mutation affects
    isPanmictic : TYPE bool
        is the slim file from a panmictic model
    Plot : TYPE bool
        whether visualize the results

    Returns
    -------
    TYPE
        DESCRIPTION.

    '''
    # row is mutations, column is generations, value is mutation frequency
    freq_mat = []
    population_size = []
    drive_rate = []
    r2_rate = []
    I = []
    effectvar_sd = []
    effectvar_mean = []
    df2 = pd.DataFrame()
    if os.path.exists(filename):
        with open(filename,'r') as f:#equilibrium_after_chasing.txt
            content = f.readlines()
    else:
        content = (str(filename)).split('\n')
    for line in content:
        if line.startswith("NUMBER_OF_MUTATION:"):
            mutation_number = int((line.strip()).replace("NUMBER_OF_MUTATION: ", ''))
            print(mutation_number)
            for i in range(mutation_number):
                freq_mat.append([])
        if line.startswith("NUMBER_OF_GENEELEMENT:"):
            geneelement_number = int((line.strip()).replace("NUMBER_OF_GENEELEMENT: ",''))
            ch_sep = int(geneelement_number*6907/(6907+5071))
        if line.startswith("POPULATION_SIZE:"):
            # from the first generation
            population_size.append(int((line.strip()).replace("POPULATION_SIZE: ", '')))
        if not isPanmictic and line.startswith("WT_ALLELES::"):
            # ANN from 10th generation
            cons = (line.strip()).split()
            ex = 0.5/np.sqrt(population_size[-1])
            I.append(float(cons[6])/ex)
        if line.startswith("GEN:"):
            # drive rate from 10th generation
            cons = (line.strip()).split()
            if cons[3]!='NAN':
                drive_rate.append(float(cons[3]))
            if cons[5]!='NAN':
                r2_rate.append(float(cons[5]))
        # if line.startswith('WT_AL'):
        #     line2 = line.strip()
        #     line2 = line2.split(' ')
        #     df2 = pd.concat([df2,pd.DataFrame([[int(line2[1]),int(line2[2]),int(line2[3]),float(line2[4]),float(line2[6]),float(line2[8])]])])
        if line.startswith("EFFECTSIZE_OF_INDIVIDUALS:"):
            # the distribution of effectsize from the first generation
            dcs = (line.strip()).replace("EFFECTSIZE_OF_INDIVIDUALS: ", '')
            dcs = [float(i) for i in dcs.split()]
            effectvar_sd.append(np.std(dcs))
            effectvar_mean.append(np.mean(dcs))
        if line.startswith("MUTATION_POSITIONS:"):
            mutation_positions = (line.replace("MUTATION_POSITIONS: ", '')).split()
        if line.startswith("MUTATION_EFFECTSIZE:"):
            mutation_effectsize = (line.replace("MUTATION_EFFECTSIZE: ", '')).split()
        if line.startswith("mutation"):
            con = line.split()
            if con[3]!='NAN':
                freq_mat[int(con[1])-10].append(float(con[3]))
    wt_rate = 1-np.array(drive_rate)-np.array(r2_rate)
    # df2.columns = ['wt allele number','gen','pop size','rate drive carriers','average nni','var nni']
    # df2['normalized nni'] = df2['average nni']/(0.5/np.sqrt(df2['pop size']))
    
    freq_df = pd.DataFrame(freq_mat)
    # row is mutations, column is generation from the first generation
    #print(mutation_effectsize)
    mutation_positions = [int(i) for i in mutation_positions]
    mutation_effectsize = np.array([float(i) for i in mutation_effectsize]) #from the first genertaion
    mutation_chromosome = np.array([0 if int(i)<=ch_sep else 1 for i in mutation_positions])
    #print(mutation_chromosome)
    generations = len(freq_mat[0])
    total_effect_size = []
    total_es_ch1 = []
    total_es_ch2 = []
    d_popsize = []
    
    for i in range(generations):
        # print(freq_df.iloc[:,i])
        # print(mutation_effectsize)
        # print(freq_df.iloc[:,i]*mutation_effectsize)
        tmp = sum(freq_df.iloc[:,i]*mutation_effectsize*2)#*population_size[i]
        total_effect_size.append(tmp)
        
        ch1 = (mutation_chromosome==0)
        tmp = sum(freq_df.iloc[ch1,i]*mutation_effectsize[ch1]*2)
        total_es_ch1.append(tmp)
        ch2 = (mutation_chromosome==1)
        tmp = sum(freq_df.iloc[ch2,i]*mutation_effectsize[ch2]*2)
        total_es_ch2.append(tmp)

    for i in range(generations-1):
        d_popsize.append(population_size[i+1]-population_size[i])
    
    if Plot:
        # plot the total effect size and ANN
        fontsize = 15
        # plt.figure(dpi=300)
        # plt.plot(range(generations),total_effect_size,label="total")
        # plt.plot(range(generations),total_es_ch1,label='chromosome1')
        # plt.plot(range(generations),total_es_ch2,label='chromosome2')
        # plt.ylabel("Population total effect size",fontsize=fontsize)
        # plt.xlabel("Generation",fontsize=fontsize)
        # plt.title(title)
        # plt.legend()
        # plt.show()
        
        # # plt.figure(dpi=300)
        # # plt.plot(range(len(df2)),df2['normalized nni'])
        # # plt.ylabel("nni ",fontsize=fontsize)
        # # plt.xlabel("Generation",fontsize=fontsize)
        # # plt.title(title)
        # # plt.show()
        
        # plt.figure(dpi=300)
        # plt.plot(range(generations),effectvar_mean)
        # plt.ylabel("mean of "+effectvar,fontsize=fontsize)
        # plt.xlabel("Generation",fontsize=fontsize)
        # plt.title(title)
        # plt.show()
        
        # plt.figure(dpi=300)
        # plt.plot(range(generations),effectvar_sd)
        # plt.ylabel("standard deviation of "+effectvar,fontsize=fontsize)
        # plt.xlabel("Generation",fontsize=fontsize)
        # plt.title(title)
        # plt.show()
        
        plt.figure(dpi=300)
        plt.plot(range(9,len(drive_rate)+9),drive_rate,label="drive")
        plt.plot(range(9,len(r2_rate)+9),r2_rate,label="r2")
        plt.plot(range(9,len(wt_rate)+9),wt_rate,label="wt")
        plt.ylabel("Allele frequency",fontsize=fontsize)
        plt.xlabel("Generation",fontsize=fontsize)
        plt.title(title)
        plt.legend()
        plt.show()
        
        # plt.figure(dpi=300)
        # plt.plot(range(len(population_size)),population_size)
        # plt.ylabel("Population size",fontsize=fontsize)
        # plt.xlabel("Generation",fontsize=fontsize)
        # plt.title(title)
        # plt.show()
        
        # fig, ax1 = plt.subplots(figsize=(6, 5),dpi=400)
        # population_size = smooth(population_size[10:])
        # ax1.plot(range(len(population_size)),population_size,color='royalblue',label='popsize')
        # #ax1.set_ylim(-100,0)#(2000,18000)
        # ax2 = ax1.twinx()
        # total_effect_size = smooth(total_effect_size[10:])
        # ax2.plot(range(len(total_effect_size)),total_effect_size,color='sienna',label="total effect size")
        # #ax2.set_ylim(-1,0)#(0.55,0.87)
        # ax1.set_xlabel("Ticks",fontsize=fontsize)
        # ax1.set_ylabel("Population size",fontsize=fontsize)
        # ax2.set_ylabel("Total effect size",fontsize=fontsize)
        # # ax1.legend(loc='best')
        # # ax2.legend(loc='center right')
        # plt.show()
        
        
        if not isPanmictic:
            plt.figure(dpi=300)
            plt.plot(range(len(I)),I)
            plt.ylabel("ANN",fontsize=fontsize)
            plt.xlabel("Generation",fontsize=fontsize)
            plt.title(title)
            plt.show()
            
            fig, ax1 = plt.subplots(figsize=(6, 5),dpi=400)
            I = smooth(I[10:])
            ax1.plot(range(len(I)),I,color='royalblue',label='popsize')
            #ax1.set_ylim(-100,0)#(2000,18000)
            ax2 = ax1.twinx()
            total_effect_size = smooth(total_effect_size[10:])
            ax2.plot(range(len(total_effect_size)),total_effect_size,color='sienna',label="total effect size")
            #ax2.set_ylim(-1,0)#(0.55,0.87)
            ax1.set_xlabel("Ticks",fontsize=fontsize)
            ax1.set_ylabel("Nearest Neighbor Index",fontsize=fontsize)
            ax2.set_ylabel("Total effect size",fontsize=fontsize)
            ax1.legend(loc='best')
            ax2.legend(loc='center right')
            plt.show()
            
        # plt.figure(dpi=300)
        # plt.scatter(effectvar_sd[100:-1],d_popsize[100:])
        # plt.ylabel("d_pop_size",fontsize=fontsize)
        # plt.xlabel("std of "+effectvar,fontsize=fontsize)
        # plt.show()
        
        
        # # plot the frequency of each mutation
        # plt.figure(dpi=300)
        # for i in range(mutation_number):
        #     if True:#float(mutation_effectsize[i])>0:
        #         plt.plot(range(generations),freq_mat[i],label=str(mutation_effectsize[i])+" "+str(np.floor(int(mutation_positions[i])/29)))
        # plt.ylabel("mutation frequency")
        # plt.xlabel("generation")
        # plt.title(title)
        # plt.show()
        # #plt.legend()
    
    
    # # compute the s=1/d for all combinations of mutions
    # ldm = np.zeros((mutation_number,mutation_number))
    # for i in range(mutation_number):
    #     for j in range(mutation_number):
    #         if i!=j and mutation_chromosome[i]==mutation_chromosome[j]:
    #             ldm[i][j] = 1/(abs(mutation_positions[i] - mutation_positions[j])+1)
    #             ldm[j][i] = ldm[i][j]
    # #plot several mutations with increasing frequency
    # freq_df=freq_df.sort_values(by=generations-1,ascending=False)
    # print(freq_df)
    # es = [mutation_effectsize[j] for j in freq_df.index]
    # for index,row in freq_df.iterrows():
    #     # print(row[generations-1])
    #     if mutation_effectsize[index]>0 and row[generations-1]>0.6:
    #         # find its nearest negative mutation
    #         nn = (ldm[index].tolist()).index(max(ldm[index]))
    #         print(mutation_positions[index])
    #         print(mutation_positions[nn])
    #         plt.figure(dpi=300)
    #         plt.plot(range(generations),freq_df.loc[nn],label="nearest neighbor es="+str(mutation_effectsize[nn]))
    #         plt.plot(range(generations),freq_df.loc[index],label="m es="+str(mutation_effectsize[index]))
    #         plt.ylabel("Mutation frequncy",fontsize=fontsize)
    #         plt.xlabel("Generation",fontsize=fontsize)
    #         plt.title(row[generations-1])
    #         plt.legend()
    #         plt.show()
    
    
    # plt.figure(dpi=300)
    # plt.plot(es,freq_df[generations-1])
    # plt.ylabel("mutation frequncy",fontsize=fontsize)
    # plt.xlabel("effect size",fontsize=fontsize)
    # plt.show()
    
    # drive rate, I from the release gens, 
    if mutation_number==1:
        return total_effect_size,freq_mat[0],effectvar_mean,effectvar_sd,drive_rate,population_size,I
    else:
        return total_effect_size,effectvar_mean,effectvar_sd,drive_rate,r2_rate,population_size,I
    
    
def mutation_heatmap(filename):
    '''
    plot the frequency change of all mutations sorted by positions or effectsize
    try to find the evolution units that linked and inherited together

    Parameters
    ----------
    filename : TYPE string
        the slim output file name.

    Returns
    -------
    None.

    '''
    fontsize=13
    # row is mutations, column is generations, value is mutation frequency
    freq_mat = []
    if os.path.exists(filename):
        with open(filename,'r') as f:#equilibrium_after_chasing.txt
            content = f.readlines()
    else:
        content = (str(filename)).split('\n')
        
    for line in content:
        if line.startswith("NUMBER_OF_MUTATION:"):
            mutation_number = int((line.strip()).replace("NUMBER_OF_MUTATION: ", ''))
            for i in range(mutation_number):
                freq_mat.append([])
        if line.startswith("MUTATION_POSITIONS:"):
            mutation_positions = (line.replace("MUTATION_POSITIONS: ", '')).split()
        if line.startswith("MUTATION_EFFECTSIZE:"):
            mutation_effectsize = (line.replace("MUTATION_EFFECTSIZE: ", '')).split()
        if line.startswith("mutation"):
            con = line.split()
            if con[3]!='NAN':
                freq_mat[int(con[1])-10].append(float(con[3]))
    freq_df = pd.DataFrame(freq_mat)
    mutation_positions = np.array([int(i) for i in mutation_positions])
    mutation_effectsize = np.array([float(i) for i in mutation_effectsize])
    generations = len(freq_df.columns)
    total_effect_size = []
    for i in range(generations):
        tmp = sum(freq_df.iloc[:,i]*mutation_effectsize*2)#*population_size[i]
        total_effect_size.append(tmp)
    
    # # plot heatmap according to the positions
    # freq_df.index = mutation_positions
    # generations = len(freq_mat[0])
    # freq_df.columns = list(range(generations))
    # freq_df = freq_df.sort_index(axis = 0) # freq_df sort according to positions
    # sns.set()
    # plt.figure(dpi = 300)
    # sns.heatmap(freq_df,cmap=plt.cm.YlGnBu)
    # plt.xlabel("Generation")
    # plt.ylabel("Mutations (Position)")
    # plt.show()
    
    # plt.figure(dpi=300,figsize=(10,1))
    # sorted_index = (np.argsort(mutation_positions)) # from small to big
    # sorted_effectsize = mutation_effectsize[sorted_index]
    # #plt.barh(range(len(mutation_effectsize)),sorted_effectsize[::-1],color='blue',edgecolor='blue')
    # plt.plot(range(len(mutation_effectsize)),sorted_effectsize)
    # plt.show()
    
    # # classify the evolution groups
    # final_freq = freq_df.iloc[:,generations-1]>0.5
    # class_no = 1
    # mutation_evolution_class = []
    # initial_state = final_freq.iloc[0]
    # for i in final_freq:
    #     if i==initial_state:
    #         mutation_evolution_class.append(class_no)
    #     else:
    #         class_no = class_no + 1
    #         mutation_evolution_class.append(class_no)
    #     initial_state = i
    # mutation_evolution_class = np.array(mutation_evolution_class)
    # group_effectsize = np.array(mutation_evolution_class)
    # group_effectsize = group_effectsize.astype(np.float_)
    # for i in range(1,class_no+1):
    #     group_es = sum(sorted_effectsize[mutation_evolution_class==i])
    #     group_effectsize[mutation_evolution_class==i] = group_es
    # print(group_effectsize)
    # plt.figure(dpi=300,figsize=(10,1))
    # plt.plot(range(len(group_effectsize)),group_effectsize)
    # plt.show()
        
    
    # plot heatmap according to the effectsize
    gen_upthreshold = 1500
    freq_df = freq_df.iloc[:,:gen_upthreshold]
    freq_df.index = mutation_effectsize
    freq_df = freq_df.sort_index(axis = 0,ascending=False)
    sns.set()
    plt.figure(dpi = 300,figsize=(6.5,4.5))
    ax = sns.heatmap(freq_df,cmap=plt.cm.YlGnBu,fmt='.3f',cbar_kws={
               'shrink': 1.0,           # 缩小colorbar高度
               'pad': 0.20,             # 设置与主图的间距
               'aspect': 30,            # colorbar的长宽比
               'location': 'left',      # colorbar位置
           })
    cbar = ax.collections[0].colorbar
    cbar.set_label('Mutation frequency', fontsize=fontsize)  # 设置字号和粗细

    xticks = [round(i) for i in np.linspace(0,gen_upthreshold,6)]
    current_labels = [tick.get_text() for tick in ax.get_yticklabels()]
    new_labels = [f'{float(label):.3f}' for label in current_labels if label]
    current_positions = ax.get_yticks()
    new_positions = current_positions[::2]
    ax.set_yticks(ticks=new_positions)
    ax.set_yticklabels(new_labels[::2])
    # ax.set_xticks(ticks=ax.get_xticks()[::3])
    # ax.set_xticklabels(xticks)
    plt.xticks(ticks=xticks,labels=xticks,rotation=0)
    
    ax1 = ax.twinx()
    ax1.plot(range(generations),total_effect_size,color='orange')
    ax1.set_ylabel("Total effect size",fontsize=fontsize)
    ax.set_xlabel("Week",fontsize=fontsize)
    ax.set_ylabel("Mutations (Effect size)",fontsize=fontsize)
    #plt.title(mutation_number)
    plt.show()
    
    # plt.figure(dpi=300)
    # sorted_index = (np.argsort(mutation_positions))[::-1]
    # sorted_effectsize = mutation_effectsize[sorted_index]
    # plt.barh(range(len(mutation_effectsize)),sorted_effectsize,color='blue',edgecolor='blue')
    # plt.show()
    
    return

def linked_relation(filename):
    with open(filename,'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("MUTATION_POSITIONS:"):
                mutation_positions = (line.replace("MUTATION_POSITIONS: ", '')).split()
            if line.startswith("MUTATION_EFFECTSIZE:"):
                mutation_effectsize = (line.replace("MUTATION_EFFECTSIZE: ", '')).split()
        mutation_positions = np.array([int(i) for i in mutation_positions])
        mutation_effectsize = np.array([float(i) for i in mutation_effectsize]) #from the first genertaion
        ch1_effectsize = mutation_effectsize[mutation_positions<1000]
        linked_effectsize_neg = sum(ch1_effectsize[np.array(ch1_effectsize)<0])
    return linked_effectsize_neg

def panmictic_mutation():
    '''
    plot for the single mutation evolution test in panmictic model
    variable : mutation numbers

    Returns
    -------
    None.

    '''
    filename = "multiple mutations test/m500.txt"#"equ_after_chasing_example/85highvar.txt"
    isPanmictic = 1
    mutation_number = 2
    Plot = False
    if mutation_number==1:
        fig,ax = plt.subplots(dpi=300)
        total_effect_size,mutation_freq,dc_mean,dc_sd,drive_rate,population_size,ANN = whole_situation("one mutation test/panmictic/unlinked10.txt",isPanmictic,Plot)
        ax.plot(range(len(mutation_freq)),mutation_freq,label="unlinked+10")
        total_effect_size,mutation_freq,dc_mean,dc_sd,drive_rate,population_size,ANN = whole_situation("one mutation test/panmictic/unlinked05.txt",isPanmictic,Plot)
        ax.plot(range(len(mutation_freq)),mutation_freq,label="unlinked+05")
        total_effect_size,mutation_freq,dc_mean,dc_sd,drive_rate,population_size,ANN = whole_situation("one mutation test/panmictic/unlinked-05.txt",isPanmictic,Plot)
        ax.plot(range(len(mutation_freq)),mutation_freq,label="unlinked-05")
        total_effect_size,mutation_freq,dc_mean,dc_sd,drive_rate,population_size,ANN = whole_situation("one mutation test/panmictic/unlinked-10.txt",isPanmictic,Plot)
        ax.plot(range(len(mutation_freq)),mutation_freq,label="unlinked-10")
        total_effect_size,mutation_freq,dc_mean,dc_sd,drive_rate,population_size,ANN = whole_situation("one mutation test/panmictic/linked10.txt",isPanmictic,Plot)
        ax.plot(range(len(mutation_freq)),mutation_freq,label="linked+10")
        total_effect_size,mutation_freq,dc_mean,dc_sd,drive_rate,population_size,ANN = whole_situation("one mutation test/panmictic/linked05.txt",isPanmictic,Plot)
        ax.plot(range(len(mutation_freq)),mutation_freq,label="linked+05")
        total_effect_size,mutation_freq,dc_mean,dc_sd,drive_rate,population_size,ANN = whole_situation("one mutation test/panmictic/linked-05.txt",isPanmictic,Plot)
        ax.plot(range(len(mutation_freq)),mutation_freq,label="linked-05")
        total_effect_size,mutation_freq,dc_mean,dc_sd,drive_rate,population_size,ANN = whole_situation("one mutation test/panmictic/linked-10.txt",isPanmictic,Plot)
        ax.plot(range(len(mutation_freq)),mutation_freq,label="linked-10")
        total_effect_size,mutation_freq,dc_mean,dc_sd,drive_rate,population_size,ANN = whole_situation("one mutation test/panmictic/linked_rec25_-10.txt",isPanmictic,Plot)
        ax.plot(range(len(mutation_freq)),mutation_freq,label="linked-10_recom")
        total_effect_size,mutation_freq,dc_mean,dc_sd,drive_rate,population_size,ANN = whole_situation("one mutation test/panmictic/linked_rec25_10.txt",isPanmictic,Plot)
        ax.plot(range(len(mutation_freq)),mutation_freq,label="linked+10_recom")
        ax.set_ylabel("Mutation frequency",fontsize=15)
        ax.set_xlabel("Generation",fontsize=15)
        plt.legend()
        plt.show()
    else:
        # test the different factors, the number of mutations
        fig,ax = plt.subplots(dpi=300)
        ax.set_title("mutation numbers")
        total_effect_size,dc_mean,dc_sd,drive_rate,population_size,I = whole_situation("multiple mutations test/m100.txt",isPanmictic,Plot)
        linked_effectsize = linked_relation("multiple mutations test/m100.txt")
        ax.plot(range(len(total_effect_size)),total_effect_size,label="100 "+str(linked_effectsize))
        total_effect_size,dc_mean,dc_sd,drive_rate,population_size,I = whole_situation("multiple mutations test/different_random_seed/m100_1.txt",isPanmictic,Plot)
        linked_effectsize = linked_relation("multiple mutations test/different_random_seed/m100_1.txt")
        ax.plot(range(len(total_effect_size)),total_effect_size,label="100_ "+str(linked_effectsize))
        total_effect_size,dc_mean,dc_sd,drive_rate,population_size,I = whole_situation("multiple mutations test/m150.txt",isPanmictic,Plot)
        linked_effectsize = linked_relation("multiple mutations test/m150.txt")
        ax.plot(range(len(total_effect_size)),total_effect_size,label="150 "+str(linked_effectsize))
        total_effect_size,dc_mean,dc_sd,drive_rate,population_size,I = whole_situation("multiple mutations test/m300.txt",isPanmictic,Plot)
        linked_effectsize = linked_relation("multiple mutations test/m300.txt")
        ax.plot(range(len(total_effect_size)),total_effect_size,label="300 "+str(linked_effectsize))
        total_effect_size,dc_mean,dc_sd,drive_rate,population_size,I = whole_situation("multiple mutations test/m500.txt",isPanmictic,Plot)
        linked_effectsize = linked_relation("multiple mutations test/m500.txt")
        ax.plot(range(len(total_effect_size)),total_effect_size,label="500 "+str(linked_effectsize))

        ax.set_ylabel("Total effect size",fontsize=15)
        ax.set_xlabel("Generation",fontsize=15)
        plt.legend()
        plt.show()
        
    #ind_dis_movie(filename)
    
def main():
    # single simulation test
    filename = "multiple mutations test/drive conversion/mosquito model/no drop test/test.txt/"
    #total_effect_size,dc_mean,dc_sd,drive_rate,population_size,I = whole_situation(filename,"drive conversion",True,True)
    # print(linked_relation("multiple mutations test/m150.txt"))
    # print(linked_relation("multiple mutations test/different_random_seed/m150.txt"))
    
    mutation_heatmap(filename)
    
    return

if __name__ == "__main__":
    #main()
    dgrp_dis()
    #panmictic_mutation()
    #mutation_heatmap("multiple mutations test/drive conversion/mosquito model/no drop test/m320.txt")
    
    # fig,ax = plt.subplots(dpi=300)
    # for root,dirs,files in os.walk("multiple mutations test/inbreeding/mosquito model/no drive drop/raw_results/"):
    #     for file in files:
    #         filename = root+file
    #         with open(filename,'r') as f:
    #             contents = f.read()
    #             contents = contents.split('// Initial random seed:')
    #             contents = contents[1:]
    #             for con in contents:
    #                 # with open(root+"wrong.txt",'w') as w:
    #                 #     w.write(con)
    #                 y = inbreeding_test(con,file)
    #                 ax.plot(range(len(y)),y,label=file.replace('.out',''))
    # ax.set_ylabel("mean of all mutations frequency",fontsize=15)
    # ax.set_xlabel("Time step",fontsize=15)
    # plt.ylim(0,0.0052)
    # plt.legend()
    # plt.show()
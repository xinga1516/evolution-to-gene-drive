# -*- coding: utf-8 -*-
"""
Created on Thu Oct  9 17:40:04 2025

@author: HP
"""

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib
import array_process_spatial
import single_simulation
import seaborn as sns
from scipy.stats import gamma
from scipy.stats import gaussian_kde
from scipy.optimize import curve_fit
import imageio
import mmap
import re
import spatial_data_process

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
    
    # 字体设置
    'font.size': 14,                # 全局字体大小
    'font.sans-serif': 'Times New Roman',
    'axes.titlesize': 14,           # 标题字号
    'axes.labelsize': 14,           # 坐标轴标签字号
    'xtick.labelsize': 12,          # x轴刻度字号
    'xtick.bottom': True,
    'ytick.labelsize': 12,          # y轴刻度字号
    'ytick.left': True,
    'legend.fontsize': 12,          # 图例字号
    
    # 刻度设置
    'xtick.color': 'black',         # x轴刻度颜色
    'ytick.color': 'black',         # y轴刻度颜色
    'xtick.direction': 'out',       # 刻度方向向外
    'ytick.direction': 'out',       # 刻度方向向外
    
    # 图形设置
    'figure.dpi': 300,              # 图形分辨率
})

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
    if length > 20:
        new_l = [np.mean(l[i:i+20]) for i in range(length-20)]
    else:
        new_l = l
    return new_l


def lines(folder):
    '''
    plot population size, or weighted NNI changing trend with generations,
    each line represents one simulaiton
    
    or split a single simulation output from whole file
    or plot the mutation heatmap

    Returns
    -------
    None.

    '''
    plt.figure(dpi=300)#figsize=(4,4.5)
    #colors = list(matplotlib.colors.CSS4_COLORS.keys())
    #colors = list(matplotlib.colors.BASE_COLORS.keys())
    colors = colors = ['#BFDFD2','#51999F','slategrey','#ECB66C','cornflowerblue','#ED8D5A','#BFDFD2']#['cornflowerblue','slategrey','sandybrown','']#'#7BC0CD',
    #colors = colors = ['#51999F','#BFDFD2','slategrey','#ECB66C','cornflowerblue','#ED8D5A','#BFDFD2']
    color_no = 0
    special_sim = 0
    fontsize = 15
    var = 'pop size'#'normalized nni'#
    
    
    for root,dirs,files in os.walk(folder):
        files = sorted(files,reverse=True)
        for file in files:
            filename = root+file
            with open(filename,'r') as f:
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                if file=="with mutations.out":#(file.split('_'))[1] == 'in':#'dc0.8mu0.00024.out' or file== '85 with deleterious muations.txt':#'mu17e6mutno8000.out':#test.out
                    start_gen = 2485
                    time = 1.08
                    #positions = [0, 3069129207, 6187230078, 9365731557, 12523046103, 15742126773, 18777501097, 21783992179, 24771931071, 27940523983, 31096593653]
                else:
                    start_gen = 5
                    time = 1.0
                positions = []
                pos = mm.find(b'// Initial random seed:')
                while pos != -1:
                    positions.append(pos)
                    pos = mm.find(b'// Initial random seed:', pos + 1)
                positions.append(len(mm))  # 结束位置
                print(positions)
                
                line_no = 1
                for i in range(min(40,len(positions) - 1)):
                    if np.random.rand()<0.25: # random plot, control plot rate
                        # each single slim output
                        start = positions[i]
                        end = positions[i + 1]
                        sim = mm[start:end].decode('utf-8', errors='replace')
                        try:
                            #df,statistic_results,pop_size,mut_per_ind,mutlocus_no,avg_fitness= in_single_simulation(sim,False,False)
                            df,statistic_results,pop_size,mut_per_ind,mutlocus_no,avg_fitness= in_single_simulation(sim,True,False)
                            # row is mutations, column is generation from the first generation
                            generations = len(df.index) # from the 21th generation
                            
                            suppressed = statistic_results[0] | statistic_results[1]
                            if True:#not suppressed:
                                #y = smooth((df[var])[start_gen:])
                                y = smooth(pop_size[start_gen:])
                                #y = smooth(avg_fitness[start_gen:])
                                #y = smooth(mut_per_ind[start_gen:])
                                #y = smooth(mutlocus_no[start_gen:])
                                if y!= []:
                                    if line_no==1:
                                        plt.plot(range(len(y)),y,color=colors[color_no],label=file.replace(".out",''),alpha=1.0)#file.replace("",''))#colors[color_no]
                                        special_sim = sim
                                        #break
                                    else:
                                        plt.plot(range(len(y)),y,color=colors[color_no],alpha=1.0)#colors[color_no]#'slategray'
                                        # s,es,freq_df = single_simulation(sim)
                                        # plt.hist(es)
                                        # plt.show()
                                    line_no = 0
                        except Exception as e:
                            print(e)
                        
                color_no = color_no+1
    plt.axvline(10,linestyle='--',color='chocolate')#'#ED8D5A'    
    plt.axhline(0,linestyle='--',color='chocolate')    
    plt.xlim(-10,610)        
    plt.xlabel("Week",fontsize=15)
    plt.ylabel("Populations size",fontsize=15)#Nearest neighbor index,Population average fitness, Mutation number per individual, Number of loci with mutations
    plt.legend(fontsize=11,loc="upper right",frameon=False)
    #plt.title(file,fontsize=fontsize)
    plt.show()
    
    # with open(folder+"mutnum800.txt",'w') as fw:
    #     fw.write(special_sim)

def lines_nor(folder,outputfile):
    '''
    plot population size, or weighted NNI changing trend with generations,
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
    colors = ['slategrey','cornflowerblue']
    color_no = 0
    special_sim = 0
    fontsize = 15
    var = 'normalized nni'#'pop size'
    results = pd.DataFrame()
    
    for root,dirs,files in os.walk(folder):
        for file in files:
            filename = root+file
            with open(filename,'r') as f:
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                if (file == 'spatial 85 without mutations.out'):
                    start_gen = 985
                else:
                    start_gen = 5
                    
                positions = []
                pos = mm.find(b'// Initial random seed:')
                while pos != -1:
                    positions.append(pos)
                    pos = mm.find(b'// Initial random seed:', pos + 1)
                positions.append(len(mm))  # 结束位置
                print(positions)
                
                line_no = 1
                for i in range(len(positions) - 1):
                    # each single slim output
                    start = positions[i]
                    print(start)
                    end = positions[i + 1]
                    sim = mm[start:end].decode('utf-8', errors='replace')
                    df,mut_per_ind,avg_fitness,statistic_results,mut_locus_num = in_single_simulation(sim)
                    
                    if (len(mut_per_ind)>100):
                        results = pd.concat([results,pd.DataFrame([[np.mean(mut_per_ind[-100:]),
                                        np.mean(avg_fitness[-100:]),np.mean(mut_locus_num[-100:])]
                                                               +statistic_results])])
                    else:
                        results = pd.concat([results,pd.DataFrame([statistic_results])])
                    
                    generations = len(df.index) # from the 21th generation
                    
                    y = smooth((df[var])[start_gen:])
                    if line_no==1:
                        plt.plot(range(len(y)),y,color=colors[color_no],label=file.replace(".out",''))#colors[color_no]
                        # special_sim = sim
                        # break
                    else:
                        plt.plot(range(len(y)),y,color=colors[color_no])#colors[color_no]#'slategray'
                        # s,es,freq_df = single_simulation(sim)
                        # plt.hist(es)
                        # plt.show()
                    line_no = 0
                        
                color_no = color_no+1
                    
        plt.xlabel("Week",fontsize=fontsize)
        plt.ylabel("Normalized Nearest Neighbor Index",fontsize=fontsize)
        plt.legend()
        #plt.title(file,fontsize=fontsize)
        plt.show()
    results.columns = ['mut per ind','avg fitness','mut locus number','suppressed without chasing',
                       'suppressed with chasing','nni first200','nni after200','popsize first200','popsize after200']
    results.to_csv(outputfile)
    # with open(folder+"mutnum800.txt",'w') as fw:
    #     fw.write(special_sim)


def gamma_dis(a,b):
    x = np.linspace(0,1,100)
    pdf = gamma.pdf(x, a=a, scale=b)

    plt.figure(figsize=(8, 4))
    plt.plot(-x, pdf, label=f'Gamma PDF\nα={a}, β={b}', color='darkorange')
    plt.title('Gamma Distribution PDF')
    plt.xlabel('Selection Coefficient')
    plt.ylabel('Probability Density')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
    return

def func(x, a, b, c, d):
    return a * np.exp(b*x+c) + d

def in_single_simulation(filename,Panmictic,Plot):
    if os.path.exists(filename):
        with open(filename,'r') as f:
            lines = f.readlines()
    else:
        lines = (str(filename)).split('\n')
    #lines = f.readlines()
    colors = ['slategrey','cornflowerblue']#'slategrey',
    population_size = []
    mut_per_ind = []
    mut_locus_num = []
    avg_fitness = []
    statistic_results = [0,0,-1,-1,-1,-1]
    df = pd.DataFrame()
    paras = re.split(r'mu|no|es|.out',filename)
    effectsize = -0.3#float(paras[2])
    gen=0
    suppressed_without_chasing = 0
    suppressed_with_chasing = 0
    no=0
    if Panmictic:
        for line in lines:
            if line.startswith("Deleterious mutations per ind: "):
                mut = float((line.strip()).replace("Deleterious mutations per ind: ", ''))
                mut_per_ind = mut_per_ind + [mut]
            if line.startswith("Locus number with mutations: "):  
                mut = float((line.strip()).replace("Locus number with mutations: ", ''))
                mut_locus_num = mut_locus_num + [mut]
            if line.startswith("Average fitness: "):  
                mut = float((line.strip()).replace("Average fitness: ", ''))
                avg_fitness = avg_fitness + [mut]
            if line.startswith("POPULATION_SIZE:"):
                # from the first generation
                population_size.append(int((line.strip()).replace("POPULATION_SIZE: ", '')))
    else:
        for line in lines:
            if line.startswith('SUPPRESSED WITHOUT CHASING'):
                suppressed_without_chasing = 1
                gen_suppressed = int(line.replace('SUPPRESSED WITHOUT CHASING:: ',''))
            if line.startswith('SUPPRESSED WITH CHASING'):
                suppressed_with_chasing = 1
                gen_suppressed = int(line.replace('SUPPRESSED WITH CHASING:: ',''))
            if line.startswith("Deleterious mutations per ind: ") and gen>0:
                # from which tick is decided by gen; -1 first tick
                mut = float((line.strip()).replace("Deleterious mutations per ind: ", ''))
                mut_per_ind = mut_per_ind + [mut]
            if line.startswith("Locus number with mutations: "):  
                mut = float((line.strip()).replace("Locus number with mutations: ", ''))
                mut_locus_num = mut_locus_num + [mut]
            if line.startswith("Average fitness: "):  
                mut = float((line.strip()).replace("Average fitness: ", ''))
                avg_fitness = avg_fitness + [mut]
            if line.startswith('WT_AL'):
                # from 20th tick
                line2 = line.strip()
                line2 = line2.split(' ')
                df = pd.concat([df,pd.DataFrame([[int(line2[1]),int(line2[2]),int(line2[3]),float(line2[4]),float(line2[6]),float(line2[8])]])])
                gen = int(line2[2])
                pop_size = int(line2[3])
            if line.startswith("EFFECTSIZE OF ALL MUTATIONS: "):
                if gen>1500 and gen<1320:
                    muts = (line.strip()).replace("EFFECTSIZE OF ALL MUTATIONS: ",'')
                    muts = [float(i) for i in muts.split()]
                    # plot the effectsize distribution of all mutations
                    unique_muts = list(set(muts))
                    kde = gaussian_kde(unique_muts)
                    fig, ax1 = plt.subplots(figsize=(5, 3))
                    x = np.linspace(-1.0, 0,400)
                    #ax1.plot(x,kde(x),color='orange',label="curve: new drawn mutations")
                    ax1.plot(x,gamma.pdf(-x,a=2,scale=abs(effectsize/2)),color='orange',label="Gamma: new drawn mutations")#'gamma distribution
                    #ax1.hist(unique_muts,bins=40,range=(-1.0,0),alpha=0.5,density=True,color='blue',label="hist: new drawn mutations")
                    
                    kde = gaussian_kde(muts)
                    ax1.plot(x,kde(x),color='blue',label="observed mutations")
                    ax1.hist(muts,bins=30,range=(-1.0,0),alpha=0.5,density=True,color='grey')#label="hist:all mutations in population"
                    ax1.set_xlabel("Mutation effectsize")
                    ax1.set_ylabel("Density")
                    plt.title("Week "+str(gen))
                    ax1.legend(loc='best',fontsize=11)
                    plt.show()
                if gen==1021 or gen==1303:
                    muts = (line.strip()).replace("EFFECTSIZE OF ALL MUTATIONS: ",'')
                    muts = [float(i) for i in muts.split()]
                    #plt.plot(x,gamma.pdf(-x,a=2,scale=abs(effectsize/2)),color='orange',label="Gamma: new drawn mutations")#'gamma distribution
                    #ax1.hist(unique_muts,bins=40,range=(-1.0,0),alpha=0.5,density=True,color='blue',label="hist: new drawn mutations")
                    
                    #kde = gaussian_kde(muts)
                    #ax1.plot(x,kde(x),color='white',label="mutations at equilibrium")
                    plt.hist(muts,bins=40,range=(-1.0,0),alpha=0.5,density=False,color=colors[no],label="Week"+str(gen-1000))#label="hist:all mutations in population"
                    plt.xlabel("Mutation effectsize")
                    plt.ylabel("Density")
                    # plt.title("Week "+str(gen))
                    # ax1.legend(loc='best')
                   # plt.show()
                    
                    # # plot frequency of each mutation
                    # mut_count = {}
                    # for mut in muts:
                    #     mut_count[mut] = mut_count.get(mut,0) + 1
                    # mut_count = dict(sorted(mut_count.items(),key=lambda x: x[1]))
                    # boundary_points = np.linspace(-1.0,0.0,101)
                    # above_mut = {}
                    # for i in range(len(boundary_points)-1):
                    #     orkeys = np.array(list(mut_count.keys()))
                    #     keys = orkeys[(orkeys>boundary_points[i]) & (orkeys<boundary_points[i+1])]
                    #     items = {k:mut_count[k] for k in keys}
                    #     items = dict(sorted(items.items(),key=lambda x: x[1],reverse=True))
                    #     if (len(items)<5):
                    #         above_mut = {**items,**above_mut}
                    #     else:
                    #         low_thres = list(items.values())[0]*0
                    #         high_thres = list(items.values())[0]*1.0
                    #         tmp = {k:v for k,v in items.items() if v > low_thres and v < high_thres}
                    #         above_mut = {**tmp,**above_mut}
                
                    # #plt.scatter(above_mut.keys(), above_mut.values())
                    # plt.hist(above_mut.values(),alpha=0.5,color=colors[no],label="Week"+str(gen))#"hist:all mutations in population")
                    # u = 2.4*10**(-4)
                    no = no+1
                    # plt.plot(boundary_points,np.sqrt(u/(u+1)/(-boundary_points))*2*3400,color='orange',label='equilibrium')
                    # popt, pcov = curve_fit(func, list(above_mut.keys()), list(above_mut.values()), maxfev=40000,p0=(4,2,3,-14))
                    # a, b, c,d = popt
                    # #print("generation " + str(gen) + str(popt))
                    # plt.plot(boundary_points,func(boundary_points,a, b, c,d),color='green')
                    # plt.xlim(-1,0,0)
                    # plt.ylim(0,500)
                    plt.xlabel("Frequency")
                    plt.xlabel("Mutation effectsize")
                    plt.ylabel("Frequency density")
                    #plt.title("Week "+str(gen))
                    #plt.show()
            if line.startswith("INDIVIDUAL FITNESS CAUSED BY MUTATIONS: ") and gen>0:
                # from which tick is decided by gen; -1 first tick
                # 结果先输出个体fitness再输出population size,所以这里的pop_size是上一代的种群数量
                fits = (line.strip()).replace("INDIVIDUAL FITNESS CAUSED BY MUTATIONS:",'')
                if fits != '':
                    fits = np.array([float(i) for i in (fits.split())[1:]])
                    avg_fitness.append(sum(fits)-len(fits))
                    #avg_fitness.append(np.mean(fits))
                else:
                    avg_fitness.append(0)
                if gen>1520 and gen<1320:#gen==1021 or gen==1127 or gen==1303:
                    # fits = list(fits[fits!=1])
                    print("number of changed fitness: "+str(len(fits)))
                    
                    fig, ax1 = plt.subplots(figsize=(5, 3))
                    kde = gaussian_kde(fits)
                    x = np.linspace(0.0, 0.99,400)
                    ax1.plot(x,kde(x),color='dimgrey')
                    ax1.hist(fits,bins=40,range=(0.0,1.0),alpha=0.5,density=True,color='grey',label=str(len(fits)/pop_size))
                    ax1.set_xlabel("Individual fitness")
                    plt.ylabel("Density")
                    plt.title("Week "+str(gen-1000))
                    #plt.legend()
                    plt.show()
        df.columns = ['wt allele number','gen','pop size','rate drive carriers','average nni','var nni']
        df['normalized nni'] = df['average nni']/(0.5/np.sqrt(df['pop size']))
        print(len(avg_fitness))
        print(len(df))
        initial_popsize = np.mean((df['pop size'])[979:999])
        # if (len(avg_fitness)!=0):
        #     ex = 1
        #     avg_fitness = (np.array(avg_fitness[:])+(df['pop size'])[1:]*ex)/((df['pop size'])[1:]*ex)
        if gen > 1300:
            start = 1099; mid=1299
            weighted_I_first200 = sum((df['pop size'])[start:mid]*(df['normalized nni'])[start:mid])/sum((df['pop size'])[start:mid])
            weighted_I_after200 = sum((df['pop size'])[mid:]*(df['normalized nni'])[mid:])/sum((df['pop size'])[mid:])
            popsize_first200 = np.mean((df['pop size'])[start:mid])
            popsize_after200 = np.mean((df['pop size'])[mid:])
            final_popsize = np.mean((df['pop size'])[-100:])
            final_mpi = np.mean(mut_per_ind[-100:])
            final_mln = np.mean(mut_locus_num[-100:])
            statistic_results = [suppressed_without_chasing,suppressed_with_chasing,initial_popsize,final_popsize,weighted_I_first200,weighted_I_after200,popsize_first200,popsize_after200,final_mpi,final_mln]
        
    
    # plt.legend()
    # plt.show()
    
    if Plot:
        pop_size = [np.mean((df['pop size'])[i:(i+10)]) for i in range(len(df)-10)]
        print(pop_size[0])
        print(pop_size[-1])
        plt.plot(range(len(pop_size)),pop_size)
        plt.xlabel("Ticks")
        plt.ylabel("Population size")
        plt.show()
                
        plt.figure(dpi=300)
        plt.plot(range(len(mut_per_ind)),mut_per_ind)
        plt.xlabel("Ticks")
        plt.ylabel("Deleterious mutations per ind")
        plt.show()
        
        fig, ax1 = plt.subplots(figsize=(7.5, 4.5),dpi=400)
        ax1.plot(range(len(mut_per_ind)),mut_per_ind,label="mut_per_ind")
        ax2 = ax1.twinx()
        ax2.plot(range(len(avg_fitness)),avg_fitness,color='orange')
        ax1.set_xlabel("Week")
        ax1.set_ylabel("Deleterious mutations per individual")
        ax2.set_ylabel("Relative fitness of population")
        plt.axvline(980,color='black',ls='--')
        #plt.legend()
        plt.show()
        
        plt.figure(dpi=300)
        plt.plot(range(len(avg_fitness)),avg_fitness)
        plt.xlabel("Ticks")
        plt.ylabel("Average fitness of population")
        plt.show()
        
        plt.figure(dpi=300)
        plt.plot(range(len(mut_locus_num)),mut_locus_num)
        plt.xlabel("Ticks")
        plt.ylabel("Locus number with mutations")
        #plt.title(file)
        plt.show()
        
    return df,statistic_results,population_size,mut_per_ind,mut_locus_num,avg_fitness
    

def process_slim_output(file,output_filename,ifsingle):
    '''
    process raw slim results and plot the change of popsize, mutation distribution
    (use this function if multiple slim raw outputs are in one file)

    Parameters
    ----------
    file : TYPE
        DESCRIPTION.
    output_filename : TYPE
        DESCRIPTION.
    ifsingle : TYPE logistic
        if true, process and return a result of a simulation
        if false, process all simulations and return the last simulation
    c: the line color

    Returns
    -------
    df2 : TYPE
        DESCRIPTION.

    '''
    with open(file,'r') as f:
        paras = re.split(r'mu|no|es|.out',file)
        
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        positions = []
        pos = mm.find(b'// Initial random seed:')
        if ifsingle:
            pos1 = mm.find(b'// Initial random seed:', pos + 1)
            # pos2 = mm.find(b'// Initial random seed:', pos1 + 1)
            # pos3 = mm.find(b'// Initial random seed:', pos2 + 1)
            # pos4 = mm.find(b'// Initial random seed:', pos3 + 1)
            positions = [pos,pos1]
        else:
            while pos != -1:
                positions.append(pos)
                pos = mm.find(b'// Initial random seed:', pos + 1)
            positions.append(len(mm))  # 结束位置
        print(positions)
        
        for i in range(len(positions) - 1):
            # each single slim output
            start = positions[i]
            end = positions[i + 1]
            sim = mm[start:end].decode('utf-8', errors='replace')
            
            df,statistic_results = in_single_simulation(sim,False)
            
            
            
            
            if output_filename!=False:
                with open(output_filename,'a') as fo:
                    #fo.write(",".join(paras))
                    for j in statistic_results:
                        fo.write(str(j)+",")
                    fo.write('\n')
                
            
        return 

def process_cr_slim(file,output_filename,ifsingle):
     with open(file,'r') as f:
         mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
         positions = []
         pos = mm.find(b'// Initial random seed:')
         if ifsingle:
             pos1 = mm.find(b'// Initial random seed:', pos + 1)
             # pos2 = mm.find(b'// Initial random seed:', pos1 + 1)
             # pos3 = mm.find(b'// Initial random seed:', pos2 + 1)
             # pos4 = mm.find(b'// Initial random seed:', pos3 + 1)
             positions = [pos,pos1]
         else:
             while pos != -1:
                 positions.append(pos)
                 pos = mm.find(b'// Initial random seed:', pos + 1)
             positions.append(len(mm))  # 结束位置
         print(positions)
         
         for i in range(len(positions) - 1):
             # each single slim output
             start = positions[i]
             end = positions[i + 1]
             sim = mm[start:end].decode('utf-8', errors='replace')
             # lines = sim.split('\n')
             # #lines = f.readlines()
             # avg_fitness = []
             # df = pd.DataFrame()
             # paras = re.split(r'mu|no|es|.out',file)
             # effectsize = -0.3#float(paras[2])
             # gen=0
             # for line in lines:
             #     if line.startswith('WT_AL'):
             #         line2 = line.strip()
             #         line2 = line2.split(' ')
             #         df = pd.concat([df,pd.DataFrame([[int(line2[1]),int(line2[2]),int(line2[3]),float(line2[4]),float(line2[6]),float(line2[8])]])])
             #         gen = int(line2[2])
             #         pop_size = int(line2[3]) 
             # df.columns = ['wt allele number','gen','pop size','rate drive carriers','average nni','var nni']
             # df['normalized nni'] = df['average nni']/(0.5/np.sqrt(df['pop size']))
                     
             # if gen > 800:
             #     start = 99; mid=299
             #     weighted_I_first200 = (df['pop size'])[start:mid]*(df['normalized nni'])[start:mid]/sum((df['pop size'])[start:mid])
             #     weighted_I_after200 = (df['pop size'])[mid:]*(df['normalized nni'])[mid:]/sum((df['pop size'])[mid:])
             #     popsize_first200 = np.mean((df['pop size'])[start:mid])
             #     popsize_after200 = np.mean((df['pop size'])[mid:])
             
             
             # if output_filename!=False:
             #     initial_popsize = np.mean((df['pop size'])[10:30])
             #     popsize = np.mean((df['pop size'])[-100:])
             #     with open(output_filename,'a') as fo:
             #         fo.write(",".join(paras))
             #         fo.write(","+str(popsize)+","+str(initial_popsize)+
             #                  ","+str(weighted_I_first200)+","+str(weighted_I_after200)+
             #                  ","+str(popsize_first200)+","+str(popsize_after200)+",\n")
            
             results = array_process_spatial.parse_slim(sim)
             if output_filename!=False:
                 with open(output_filename,'a') as fo:
                     for i in results:
                         fo.write(str(i)+",")
                     fo.write('\n')
             
         return #df
                 
        
def mut_dis_mv(filename1,filename2):
    natural_evolve = []
    initial_evolve = []
    image_list=[]
    with open(filename1,'r') as f:
        lines = f.readlines()
        gen=0
        image_list = []
        for line in lines:
            if line.startswith('WT_AL'):
                line2 = line.strip()
                line2 = line2.split(' ')
                gen = int(line2[2])
            if line.startswith("EFFECTSIZE OF ALL MUTATIONS: ") and line!="EFFECTSIZE OF ALL MUTATIONS: \n":
                muts = (line.strip()).replace("EFFECTSIZE OF ALL MUTATIONS: ",'')
                muts = [float(i) for i in muts.split()]
                # unique_muts = list(set(muts))
                # kde = gaussian_kde(unique_muts)
                # fig, ax1 = plt.subplots(figsize=(5, 3))
                # x = np.linspace(-1.0, 0,400)
                # ax1.plot(x,kde(x),color='orange',label="curve: new drawn mutations")
                # ax2 = ax1.twinx()
                # ax2.hist(muts,bins=40,range=(-1.0,0),alpha=0.5,color='blue',label="hist: new drawn mutations")
               
                # kde = gaussian_kde(muts)
                # ax1.plot(x,kde(x),color='green',label="curve: all mutations in population")
                # ax2.hist(muts,bins=40,range=(-1.0,0),alpha=0.5,color='grey',label="hist: all mutations in population")
                # ax1.set_xlabel("Mutation effectsize")
                # ax1.set_ylabel("KDE Density")
                # ax2.set_ylabel("hist number")
                # plt.title("generation "+str(gen))
                
                
                # plot frequency of each mutation
                mut_count = {}
                for mut in muts:
                    mut_count[mut] = mut_count.get(mut,0) + 1
                mut_count = dict(sorted(mut_count.items(),key=lambda x: x[1]))
                boundary_points = np.linspace(-1.0,0.0,101)
                above_mut = {}
                for i in range(len(boundary_points)-1):
                    orkeys = np.array(list(mut_count.keys()))
                    keys = orkeys[(orkeys>boundary_points[i]) & (orkeys<boundary_points[i+1])]
                    items = {k:mut_count[k] for k in keys}
                    items = dict(sorted(items.items(),key=lambda x: x[1],reverse=True))
                    if (len(items)<5):
                        above_mut = {**items,**above_mut}
                    else:
                        low_thres = list(items.values())[0]*0.6
                        high_thres = list(items.values())[0]*1.0
                        tmp = {k:v for k,v in items.items() if v > low_thres and v < high_thres}
                        above_mut = {**tmp,**above_mut}
                
                # plt.scatter(above_mut.keys(), above_mut.values())
                # u = 2.4*10**(-4)
                # plt.plot(boundary_points,np.sqrt(u/(u+1)/(-boundary_points))*2*3400,color='orange',label='equilibrium')
                popt, pcov = curve_fit(func, list(above_mut.keys()), list(above_mut.values()), maxfev=40000,p0=(4,2,3,-14))
                a, b, c,d = popt
                natural_evolve.append((a,b,c,d))
        #         #print("generation " + str(gen) + str(popt))
        #         plt.plot(boundary_points,func(boundary_points,a, b, c,d),color='green')
        #         plt.xlim(-1,0,0)
        #         plt.ylim(0,500)
        #         plt.xlabel("Mutation effectsize")
        #         plt.ylabel("Number")
        #         plt.title("generation "+str(gen))
                
        #         plt.legend()
        #         plt.savefig('img.png')
        #         plt.close()
        #         image_list = image_list.append(imageio.imread('img.png'))
        # imageio.mimsave('imbreeding_dis.gif', image_list, duration=0.1)
        
    with open(filename2,'r') as f:
        lines = f.readlines()
        gen=0
        image_list = []
        for line in lines:
            if line.startswith('WT_AL'):
                line2 = line.strip()
                line2 = line2.split(' ')
                gen = int(line2[2])
            if line.startswith("EFFECTSIZE OF ALL MUTATIONS: ") and line!="EFFECTSIZE OF ALL MUTATIONS: \n":
                muts = (line.strip()).replace("EFFECTSIZE OF ALL MUTATIONS: ",'')
                muts = [float(i) for i in muts.split()]
                
                mut_count = {}
                for mut in muts:
                    mut_count[mut] = mut_count.get(mut,0) + 1
                mut_count = dict(sorted(mut_count.items(),key=lambda x: x[1]))
                boundary_points = np.linspace(-1.0,0.0,101)
                above_mut = {}
                for i in range(len(boundary_points)-1):
                    orkeys = np.array(list(mut_count.keys()))
                    keys = orkeys[(orkeys>boundary_points[i]) & (orkeys<boundary_points[i+1])]
                    items = {k:mut_count[k] for k in keys}
                    items = dict(sorted(items.items(),key=lambda x: x[1],reverse=True))
                    if (len(items)<5):
                        above_mut = {**items,**above_mut}
                    else:
                        low_thres = list(items.values())[0]*0.6
                        high_thres = list(items.values())[0]*1.0
                        tmp = {k:v for k,v in items.items() if v > low_thres and v < high_thres}
                        above_mut = {**tmp,**above_mut}
                
                popt, pcov = curve_fit(func, list(above_mut.keys()), list(above_mut.values()), maxfev=40000,p0=(4,2,3,-14))
                a, b, c,d = popt
                initial_evolve.append((a,b,c,d))
    gen=11
    c = natural_evolve[800:]
    a0,b0,c0,d0 = np.mean(list(map(lambda x:x[0],c))),np.mean(list(map(lambda x:x[1],c))),np.mean(list(map(lambda x:x[2],c))),np.mean(list(map(lambda x:x[3],c)))
    for i in range(min(len(natural_evolve),len(initial_evolve))-1):
        a,b,c,d = natural_evolve[i]
        a1,b1,c1,d1 = initial_evolve[i]
        plt.plot(boundary_points,func(boundary_points,a, b, c,d),color='green',label='natural evolve')
        plt.plot(boundary_points,func(boundary_points,a1, b1, c1,d1),color='orange',label='initial evolve')
        plt.plot(boundary_points,func(boundary_points,a0, b0, c0,d0),color='blue',label='equilibrium,initial evolve')
        plt.xlim(-1,0,0)
        plt.ylim(0,300)
        plt.xlabel("Mutation effectsize")
        plt.ylabel("Number")
        plt.title("generation "+str(gen))
        gen = gen+1
        
        plt.legend()
        plt.savefig('img.png')
        plt.close()
        image_list.append(imageio.imread('img.png'))
    imageio.mimsave('imbreeding_dis.gif', image_list, duration=0.1)

def single_inVScontrol(infilename,crfilename):
    indf,inmut,infit = process_slim_output(infilename,"E:/code/raw_results/results.csv",True)
    crdf = process_cr_slim(crfilename,"E:/code/raw_results/crresults.csv",True)
    fig, ax1 = plt.subplots(figsize=(7.5, 4.5),dpi=400)
    start_gen = 0#979
    pop_size = [np.mean((indf['pop size'])[i:(i+10)]) for i in range(start_gen,1989)]
    ax1.plot(range(len(pop_size)),pop_size,label='with deleterious mutations')
    pop_size = [np.mean((crdf['pop size'])[i:(i+10)]) for i in range(989)]
    ax1.plot(range(1000,len(pop_size)+1000),pop_size,label='without mutations')
    ax2 = ax1.twinx()
    #infit = smooth(infit[start_gen:])
    infit = smooth(infit)
    ax2.plot(range(len(infit)),infit,label='average fitness',color='mediumseagreen')
    ax2.set_ylim(0.84,1)
    ax1.set_xlabel("Week")
    ax1.set_ylabel("Population size")
    ax2.set_ylabel("Relative fitness")
    #ax1.legend(loc='center left')
    ax2.legend(loc='center left')
    #plt.title(infilename)
    plt.show()
    
    plt.figure(dpi=300,figsize=(6,4.5))
    nni = smooth((indf['normalized nni'])[979:])
    plt.plot(range(len(nni)),nni,label='with deleterious mutations')
    nni = smooth(crdf['normalized nni'])
    plt.plot(range(len(nni)),nni,label='without mutations')
    plt.xlabel("Week")
    plt.ylabel("Normalized nearest neighbor index")
    plt.legend()
    #plt.title(infilename)
    plt.show()
    return

def inVScontrol(infolder):
    return

def main():
    #spatial_data_process.main("E:/code/raw_results/drive with mutations/right fit/80invscon/dai/")
    
    #inVScontrol("E:/code/raw_results/drive with mutations/dc0.7mu0.00024.out","E:/code/raw_results/drive without mutations/dc0.7mu0.out")
    # for root,dirs,files in os.walk("multiple mutations test/inbreeding/gamma deleterious genes/drive/cr/"):
    #     for fi in files:
    #         file = root + fi
    #         process_slim_output(file,"multiple mutations test/inbreeding/gamma deleterious genes/control/results.csv")
    #process_slim_output("E:/code/raw_results/drive with mutations/dc0.8mu0.00024.out","multiple mutations test/inbreeding/gamma deleterious genes/control/results.csv",True)
    #mut_dis_mv("multiple mutations test/inbreeding/gamma deleterious genes/control/test.txt/","multiple mutations test/inbreeding/gamma deleterious genes/control/multiple_initial.txt/")
    #gamma_dis(2,0.2/2)
    #process_slim_output("E:/code/raw_results/drive with mutations/test.txt","multiple mutations test/inbreeding/gamma deleterious genes/control/results.csv",True)
    #process_slim_output("E:/code/raw_results/drive with mutations/dc0.8mu0.00024.out","E:/code/raw_results/drive with mutations/results.csv",False)
    #process_slim_output("E:/code/raw_results/drive with mutations/right fit/80invscon/mu17e6mutno8000.out","E:/code/raw_results/drive with mutations/right fit/80invscon/results.csv",False)
    #lines("E:/code/raw_results/drive with mutations/right fit/80invscon/")
    #lines_nor("E:/code/raw_results/drive with mutations/raw results/","E:/code/raw_results/drive with mutations/new_results.csv/")
    #in_single_simulation("E:/code/raw_results/drive with mutations/80invscon/111/mutnum800.txt")
    #in_single_simulation("E:/code/raw_results/drive with mutations/80invscon/111/right.txt")
    #in_single_simulation("E:/code/raw_results/drive with mutations/right fit/80invscon/mu17e6mutno8000.out")

    #single_inVScontrol("E:/code/raw_results/drive with mutations/test.txt","E:/code/raw_results/drive without mutations/dc0.8mu0.out")
    #process_cr_slim("multiple mutations test/inbreeding/pan vs spa/raw_results/con_spa.out", "conspare.csv", False)
    
    lines("multiple mutations test/inbreeding/pan vs spa/new/panmictic/85/")

if __name__ == "__main__":
    main()
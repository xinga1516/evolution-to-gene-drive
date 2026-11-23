# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 09:42:36 2024

@author: Xinyue
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import os
import array_process_pan

def laplace(x,mu,b):
    return [1/2/b*np.exp((i-mu)/b) if i<mu else 1/2/b*np.exp((mu-i)/b) for i in x]

def lines():
    fig = plt.figure(dpi=300)
    colors = list(matplotlib.colors.BASE_COLORS.keys())
    color_no = 0
    for root,dirs,files in os.walk("multiple mutations test/mutation numbers/different_random_seed/mut_num_results/"):
        for file in files:
            filename = root+file
            initial_effectsize = []
            with open(filename,'r') as f:
                content = f.read()
                sims = content.split('// Initial random seed:')
                sims = sims[1:]
                line_no = 1
                for sim in sims:
                    lines = sim.split('\n')
                    freq_mat = []
                    population_size = []
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
                    freq_df = pd.DataFrame(freq_mat)
                    # row is mutations, column is generation from the first generation
                    mutation_effectsize = [float(i) for i in mutation_effectsize] #from the first genertaion
                    generations = len(freq_mat[0]) # from the first generation
                    total_effect_size = []
                    
                    for i in range(generations):
                        tmp = sum(freq_df.iloc[:,i]*mutation_effectsize*2)#*population_size[i]
                        total_effect_size.append(tmp)
                    initial_effectsize.append(total_effect_size[0])
                    if line_no==1:
                        plt.plot(range(generations),total_effect_size,color=colors[color_no],label=file.replace(".out",''))
                    else:
                        plt.plot(range(generations),total_effect_size,color=colors[color_no])
                    line_no = 0
                print(np.mean(initial_effectsize))
                color_no = color_no+1
                    
    plt.xlabel("Generation")
    plt.ylabel("Total effect size")
    plt.legend()
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
    freq_df = pd.DataFrame(freq_mat)
    mutation_effectsize = np.array([float(i) for i in mutation_effectsize]) #from the first genertaion
    return mutation_effectsize,freq_df

def process_statistic_data(filename,variable,genDiver,inbreeding):
    '''
    count up the different outcome frequency and statistic data of multiple simulations 
    of panmictic model
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
    
    results = pd.DataFrame()
    groups = raw_data.groupby(by=variable)
    for name,group in groups:
        repeats = len(group)
        suppressed_rate = sum(group.loc[:,'suppressed'])/float(repeats)
        loss_rate = sum(group.loc[:,'drive_loss'])/float(repeats)
        suppress_records = group.loc[group.loc[:,'suppressed']==1]
        suppress_gen = np.mean(suppress_records.loc[:,'gen_suppressed'])
        loss_records = group.loc[group.loc[:,'drive_loss']==1]
        loss_gen = np.mean(loss_records.loc[:,'pop_persist'])
        longterm_records = group.loc[(group['suppressed']==0) & (group['drive_loss']==0)]
        if genDiver:
           coe = longterm_records
           attribute_initial_sd = np.mean(np.sqrt(group['mutation_locus']*group['laplace_b']*group['laplace_b']/5.12))
           attribute_initial_sd = round(attribute_initial_sd,3)
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
           final_avg_variable = 0.8 + total_effectsize
           final_ev_sd = np.mean(coe.loc[:,'final_effectvar_sd'])
           final_ev_sd_SDamongsims = np.std(np.array(coe.loc[:,'final_effectvar_sd']))
           ev_sd_CI = final_ev_sd_SDamongsims/np.sqrt(len(coe))*1.96
       
        if inbreeding:
            final_mutno_per_ind = np.mean(longterm_records.loc[:,'final_mutno_per_ind'])
            final_mutno_per_ind_CI = np.std(longterm_records.loc[:,'final_mutno_per_ind'])/np.sqrt(len(longterm_records))*1.96
            final_fitness = np.mean(longterm_records.loc[:,'final_fitness'])
            final_fitness_CI = np.std(longterm_records.loc[:,'final_fitness'])/np.sqrt(len(longterm_records))*1.96
            final_mutlocus_num = np.mean(longterm_records.loc[:,'final_mutlocus_num'])
            final_mutlocus_num_CI = np.std(longterm_records.loc[:,'final_mutlocus_num'])/np.sqrt(len(longterm_records))*1.96
        
        if len(longterm_records)!=0:
            pop_size = np.mean(longterm_records.loc[:,'pop_size'])
            pop_size_SD = np.std(longterm_records.loc[:,'pop_size'])
            pop_size_CI = np.std(longterm_records.loc[:,'pop_size'])/np.sqrt(len(longterm_records))*1.96
            equ_drive_freq = np.mean(longterm_records.loc[:,'avg_drive_freq'])
            drive_freq_CI = np.std(longterm_records.loc[:,'avg_drive_freq'])/np.sqrt(len(longterm_records))*1.96
        
        if genDiver:
            final_avg_variable = -1#float(name) + total_effectsize
            #di = float(name)
            #di = 0.091/(1-di**(-0.484))-0.091*di**0.7/(di-di**0.516)
            results = pd.concat([results,pd.DataFrame([list(name)+[suppressed_rate,loss_rate,suppress_gen,loss_gen,pop_size,equ_drive_freq,pop_size_SD,
                                                        pop_size_CI,drive_freq_CI, total_effectsize,total_effectsize_SD,final_avg_variable,effectsize_reduction_after200,equ_drive_freq,es_reduction_after200_CI_down,
                                                         es_reduction_after200_CI_up,effectsize_reduction_first200,es_reduction_first200_CI_down,
                                                         es_reduction_first200_CI_up,total_effectsize_CI,drive_freq_CI,ch1_effectsize_reduction,ch1_effectsize_reduction_CI,
                                                         ch2_effectsize_reduction,ch2_effectsize_reduction_CI,ch1_effectsize_reduction_first200,ch1_effectsize_reduction_last300,
                                                         ch2_effectsize_reduction_first200,ch2_effectsize_reduction_last300,ch1_first200_CI,ch1_last300_CI,ch2_first200_CI,ch2_last300_CI,
                                                         attribute_initial_sd,final_ev_sd,ev_sd_CI,final_ev_sd_SDamongsims]])])
        elif inbreeding:
            results = pd.concat([results,pd.DataFrame([list(name)+[suppressed_rate,loss_rate,suppress_gen,loss_gen,pop_size,equ_drive_freq,
                                                        final_mutno_per_ind,final_mutno_per_ind_CI,final_fitness,final_fitness_CI,
                                                        final_mutlocus_num,final_mutlocus_num_CI]])])
        else:
            results = pd.concat([results,pd.DataFrame([[float(name),suppressed_rate,loss_rate,suppress_gen,loss_gen,
                                                        pop_size,equ_drive_freq,pop_size_CI,drive_freq_CI]])])
    if genDiver:
        results.columns = variable+['suppressed rate','drive loss rate','suppressed gen','drive loss gen',
                        'pop size','average drive frequency','popsize SDamongSIMS','popsize_CI','drive_freq_CI',
                        'average total effect size','average total effectsize SDamongSIMS','average properties','effect size reduction after200','average drive frequency',
                            'reduction_after200_CI_down','reduction_after200_CI_up','effect size reduction first200',
                                'reduction_first200_CI_down','reduction_first200_CI_up','total_effectsize_CI','drive_freq_CI',
                                'ch1_effectsize_reduction','ch1_effectsize_reduction_CI','ch2_effectsize_reduction','ch2_effectsize_reduction_CI',
                            'ch1_effectsize_reduction_first200','ch1_effectsize_reduction_last300','ch2_effectsize_reduction_first200','ch2_effectsize_reduction_last300',
                            'ch1_es_reduction_first200_CI','ch1_es_reduction_last300_CI','ch2_es_reduction_first200_CI','ch2_es_reduction_last300_CI',
                            'property_initial_sd','property_final_sd','property_final_sd_CI','property_final_sd SDamongSIMS']  
    elif inbreeding:
        results.columns = variable+['suppressed rate','drive loss rate','suppressed gen','drive loss gen',
                        'pop size','average drive frequency','final_mutnum_per_ind',
                        'final_mutnum_per_ind_CI','final_fitness','final_fitness_CI','final_mutlocus_num','final_mutlocus_num_CI'] 
    else:
        results.columns = variable+['suppressed rate','drive loss rate','suppressed gen','drive loss gen',
                        'pop size','average drive frequency','popsize_CI','drive_freq_CI']  
    write = pd.ExcelWriter(filename,mode='a',if_sheet_exists='replace')
    results.to_excel(write,sheet_name='processed',index=False)
    write.save()
    write.close()
    
    #results = pd.read_excel(filename,sheet_name="processed",index_col=None)
    
    # plt.figure(dpi=300)
    # plt.plot(results.loc[:,variable[0]],results.loc[:,'suppressed rate'],'o--')
    # plt.xlabel(variable[0])
    # plt.ylabel('suppressed rate')
    # plt.show()
    
    # plt.figure(dpi=300)
    # plt.plot(results.loc[:,variable[0]],results.loc[:,"pop size"],'o--')
    # plt.fill_between(results.loc[:,variable[0]], results.loc[:,"pop size"]-results.loc[:,'popsize_CI'], results.loc[:,"pop size"]+results.loc[:,'popsize_CI'],alpha=0.5)
    # plt.xlabel(variable[0])
    # plt.ylabel("Population size")
    # plt.show()
    
    # plt.figure(dpi=300)
    # plt.plot(results.loc[:,variable[0]],results.loc[:,"average drive frequency"],'o--')
    # plt.fill_between(results.loc[:,variable[0]], results.loc[:,"average drive frequency"]-results.loc[:,'drive_freq_CI'], results.loc[:,"average drive frequency"]+results.loc[:,'drive_freq_CI'],alpha=0.5)
    # plt.xlabel(variable[0])
    # plt.ylabel("Drive frequency")
    # plt.show()
    
    if False:#genDiver:
        plt.figure(dpi=300)
        plt.plot(results.loc[:,variable[0]],results.loc[:,"effect size reduction"],'o--')
        plt.fill_between(results.loc[:,variable[0]], results.loc[:,"reduction_CI_down"], results.loc[:,"reduction_CI_up"],alpha=0.5)
        plt.xlabel(variable[0])
        plt.ylabel("Effectsize reduction per generation")
        plt.show()
        
        plt.figure(dpi=300)
        plt.plot(results.loc[:,variable[0]],results.loc[:,"average total effect size"],'o--')
        plt.fill_between(results.loc[:,variable[0]], results.loc[:,"average total effect size"]-results.loc[:,'total_effectsize_CI'], results.loc[:,"average total effect size"]+results.loc[:,'total_effectsize_CI'],alpha=0.5)
        plt.xlabel(variable[0])
        plt.ylabel("Total effect size")
        plt.show()
        
        plt.figure(dpi=300)
        plt.plot(results.loc[:,variable[0]],results.loc[:,"average properties"],'o--')
        plt.fill_between(results.loc[:,variable[0]], results.loc[:,"average properties"]-results.loc[:,'total_effectsize_CI'], results.loc[:,"average properties"]+results.loc[:,'total_effectsize_CI'],alpha=0.5)
        plt.xlabel(variable[0])
        plt.ylabel("Average "+variable[0])
        plt.show()
        
        plt.figure(dpi=300)
        plt.errorbar(results.loc[:,variable[0]],results.loc[:,"ch1_effectsize_reduction"],yerr=results.loc[:,"ch1_es_reduction_CI"],label='chromosome1')
        plt.errorbar(results.loc[:,variable[0]],results.loc[:,"ch2_effectsize_reduction"],yerr=results.loc[:,"ch2_es_reduction_CI"],label='chromosome2')
        plt.errorbar(results.loc[:,variable[0]],results.loc[:,"ch3_effectsize_reduction"],yerr=results.loc[:,"ch3_es_reduction_CI"],label='chromosome3')
        plt.xlabel(variable[0])
        plt.ylabel("Effect size reduction per generation")
        plt.legend()
        plt.show()
        
    if inbreeding:
        groups = results.groupby(by=variable[0]) # seprerate according to the mutnum per individual
        plt.figure(dpi=300)
        for name,group in groups:
            group = group.sort_values(by=variable[1])
            plt.errorbar(group.loc[:,variable[1]],group.loc[:,'mutnum_per_ind'],yerr=group.loc[:,'mutnum_per_ind_CI'],label=name[0])
        plt.xlabel(variable[1])
        plt.ylabel('mutation number per individual')
        plt.legend()
        plt.show()
        
        groups = results.groupby(by=variable[1]) # seprerate according to the mutation locus number
        plt.figure(dpi=300)
        for name,group in groups:
            group = group.sort_values(by=variable[0])
            plt.errorbar(group.loc[:,variable[0]],group.loc[:,'mutnum_per_ind'],yerr=group.loc[:,'mutnum_per_ind_CI'],label=name[0])
        plt.xlabel(variable[0])
        plt.ylabel('mutation number per individual')
        plt.legend()
        plt.show()
            

def genDiver_vs_control():
    variable = "embryo_resistance"#"drive_conversion"
    genDiver = pd.read_excel("multiple mutations test/embryo resistance/panmictic model/er_results.xlsx",sheet_name="processed",index_col=None)
    control = pd.read_excel("multiple mutations test/embryo resistance/panmictic model/control/er_results.xlsx",sheet_name="processed",index_col=None)
    #print(genDiver)
    plt.figure(dpi=300)
    plt.fill_between(genDiver.loc[:,variable],genDiver.loc[:,'pop size']-genDiver.loc[:,'popsize_CI'],genDiver.loc[:,'pop size']+genDiver.loc[:,'popsize_CI'],alpha=0.8,edgecolor="face",label='with mutations')
    plt.fill_between(control.loc[:,variable],control.loc[:,'pop size']-control.loc[:,'popsize_CI'],control.loc[:,'pop size']+control.loc[:,'popsize_CI'],alpha=0.9,edgecolor="face",label='without mutations')
    plt.xlabel(variable)
    plt.ylabel("population size")
    plt.legend()
    
    plt.figure(dpi=300)
    plt.fill_between(genDiver.loc[:,variable],genDiver.loc[:,'average drive frequency']-genDiver.loc[:,'drive_freq_CI'],genDiver.loc[:,'average drive frequency']+genDiver.loc[:,'drive_freq_CI'],alpha=0.8,edgecolor="face",label='with mutations')
    plt.fill_between(control.loc[:,variable],control.loc[:,'average drive frequency']-control.loc[:,'drive_freq_CI'],control.loc[:,'average drive frequency']+control.loc[:,'drive_freq_CI'],alpha=0.9,edgecolor="face",label='without mutations')
    plt.xlabel(variable)
    plt.ylabel("average drive frequency")
    plt.legend()
    
    plt.figure(dpi=300)
    plt.plot(genDiver.loc[:,variable],genDiver.loc[:,'suppressed rate'],label="with mutations")
    plt.plot(control.loc[:,variable],control.loc[:,'suppressed rate'],label="without mutations")
    plt.xlabel(variable)
    plt.ylabel("suppressed rate")
    plt.legend()

    
def lost_mutation():
    plt.figure(dpi=300)
    for root,dirs,files in os.walk("multiple mutations test/embryo resistance/standard deviation/raw_results/"):
    #for root,dirs,files in os.walk("multiple mutations test/drive conversion/standard deviation/sd_results/"):
        for file in files:
            bino = 10 # the smooth of the line
            filename = root+file
            lost_number = np.array([0]*bino)
            mean = float(file.replace('.out',''))
            sd = -1760/2419*mean**2+1760/2419*mean # for embryo resistance
            # mean = 0.7
            # di = float((file.replace('.out','')).replace('sd',''))
            # sd = 0.091/(1-di**(-0.484))-0.091*di**mean/(di-di**0.516) # for drive conversion
            with open(filename,'r') as f:
                content = f.read()
                sims = content.split('// Initial random seed:')
                sims = sims[1:]
                for sim in sims:
                    mutation_effectsize,freq_df = single_simulation(sim)
                    lost_effectsize = mutation_effectsize[freq_df.iloc[:,-1] < 0.05]
                    max_effectsize = 0.03
                    hist,binedges = np.histogram(lost_effectsize,bins=bino,range=(-max_effectsize,max_effectsize))
                    #n,bins,patch = plt.hist(lost_effectsize,bins=50,range=(-0.035,0.035),density=True,label="sd"+"{:.2f}".format(sd))
                    # plt.plot(bins,laplace(bins,0,sd/np.sqrt(2*400)))
                    # print(bins)
                    # print(patch)
                    # plt.show()
                    #print(hist)
                    lost_number = lost_number+np.array(hist)
                lost_number = lost_number / len(sims)
                x = np.array(binedges[:-1])+max_effectsize/bino
                locus_number = 400
                expected = locus_number*max_effectsize*2/bino*np.array(laplace(x,0,sd/np.sqrt(2*locus_number)))
                loss_rate = lost_number/expected
                loss_rate = np.array([i if i<1 else 1 for i in loss_rate])
                # when the expected number is less than 10, it may be not very accurate, so exclude them
                numfilter = np.array(expected) >= 1
                plt.plot(x[numfilter],loss_rate[numfilter],label="sd = "+"{:.2f}".format(sd))
        plt.xlabel("effect size")
        plt.ylabel("mutation loss rate")
        plt.legend()
        plt.show()            
                

def main():
    output_file = "multiple mutations test/fitness/refer/pan_results.csv"#"multiple mutations test/mutation numbers/different_random_seed/last100_results.xlsx"
    for root,dirs,files in os.walk("multiple mutations test/fitness/refer/panmictic/"):#"multiple mutations test/mutation numbers/different_random_seed/mut_num_results/"):
        for file in files:
            filename = root+file
            print(file)
            wrong_index = []
            with open(filename,'r') as f:
                content = f.read()
                sims = content.split('// Initial random seed:')
                sims = sims[1:]
                for no in range(len(sims)):
                    sim = str(sims[no])
                    try:
                        results = array_process_pan.parse_gendiver_slim(sim)
                        with open(output_file,'a') as fo:
                            #fo.write((file.replace("mutnum",'')).replace(".out",'')+",")
                            #fo.write((file.replace("dc",'')).replace(".out",'')+",")
                            paras = file.split('_')
                            results = paras + list(results)
                            for i in results:
                                fo.write(str(i)+",")
                            fo.write("\n")
                    except Exception as e:
                        wrong_index.append(no)
                        #print(e)
                    continue
                    
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
    main()
    #process_statistic_data("multiple mutations test/drive conversion/standard deviation/sd_results.xlsx",['distribution concave degree'],True)#"multiple mutations test/mutation numbers/different_random_seed/last100_results.xlsx")
    #process_statistic_data("multiple mutations test/drive conversion/panmictic model/dc_results.xlsx",['drive_conversion'],True,False)
    # process_statistic_data("multiple mutations test/embryo resistance/panmictic model/er_results.xlsx",['embryo_resistance'],True,False)#"multiple mutations test/mutation numbers/different_random_seed/last100_results.xlsx")
    # process_statistic_data("multiple mutations test/embryo resistance/control/er_results.xlsx",['embryo_resistance'],False)
    #process_statistic_data("multiple mutations test/embryo resistance/standard deviation/er_results.xlsx",['distribution standard deviation'],True)#"multiple mutations test/mutation numbers/different_random_seed/last100_results.xlsx")
    #lines()
    # genDiver_vs_control()
    #lost_mutation()

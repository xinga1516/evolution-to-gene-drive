# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 20:14:41 2024

@author: Xinyue
"""

from argparse import ArgumentParser
import subprocess
import pandas as pd
import numpy as np
import os
# import warnings
# warnings.filterwarnings('error')

SLIM = "slim"

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

def parse_gendiver_slim(out):
    '''
    release drive at 20th generation, test the effect size change in 500 generations.

    Parameters
    ----------
    out : TYPE
        DESCRIPTION.

    Returns
    -------
    param_b : TYPE
        DESCRIPTION.
    average_total_es : float
        the average total effect size of last 100 generations.
    total_es_reduction_first200 : TYPE
        DESCRIPTION.
    ch1_es_reduction_first200 : TYPE
        DESCRIPTION.
    ch2_es_reduction_first200 : TYPE
        DESCRIPTION.
    total_es_reduction_after200 : TYPE
        DESCRIPTION.
    ch1_es_reduction_after200 : TYPE
        DESCRIPTION.
    ch2_es_reduction_after200 : TYPE
        DESCRIPTION.
    final_effectvar_sd : TYPE
        DESCRIPTION.

    '''
    out = str(out)
    out = out.split('\n')
    # row is mutations, column is generations, value is mutation frequency
    freq_mat = []
    mutation_effectsize = []
    mutation_positions = []
    effectvar_sd = []
    attribute_list = []
    param_b = -1
    complex_output = False
    release_gen = 21
    for line in out:
        if line.startswith("RELEASE_TICK: "):
            release_gen = int((line.strip()).replace("RELEASE_TICK: ", ''))
        if line.startswith("NUMBER_OF_MUTATION:"):
            mutation_number = int((line.strip()).replace("NUMBER_OF_MUTATION: ", ''))
            for i in range(mutation_number):
                freq_mat.append([])
        if line.startswith("NUMBER_OF_GENEELEMENT:"):
            geneelement_number = int((line.strip()).replace("NUMBER_OF_GENEELEMENT: ",''))
            ch_sep = int(geneelement_number*6907/(6907+5071))
        if line.startswith("MUTATION LAPLACE DISTRIBUTION PARAMETER b:"):
            param_b = float((line.strip()).replace("MUTATION LAPLACE DISTRIBUTION PARAMETER b: ",''))
        if line.startswith("EFFECTSIZE_OF_INDIVIDUALS:"):
            # the distribution of effectsize from the first generation
            complex_output = True
            dcs = (line.strip()).replace("EFFECTSIZE_OF_INDIVIDUALS: ", '')
            dcs = [float(i) for i in dcs.split()]
            attribute_list.append(np.mean(dcs))
            effectvar_sd.append(np.std(dcs))
        if line.startswith("average attribute: ") and complex_output==False:
            attribute = float((line.strip()).replace("average attribute: ",''))
            attribute_list.append(attribute)
        if line.startswith("attribute standard deviation: ") and complex_output==False:
            attribute_sd = float((line.strip()).replace("attribute standard deviation: ",''))
            effectvar_sd.append(attribute_sd)
        if line.startswith("MUTATION_POSITIONS:"):
            mutation_positions = (line.replace("MUTATION_POSITIONS: ", '')).split()
        if line.startswith("MUTATION_EFFECTSIZE:"):
            mutation_effectsize = (line.replace("MUTATION_EFFECTSIZE: ", '')).split()
        if line.startswith("mutation"):
            con = line.split()
            if con[3]!='NAN':
                freq_mat[int(con[1])-10].append(float(con[3]))
            
    property_initial_sd = round(np.sqrt(mutation_number * param_b * param_b / 5.12),3)
    
    freq_df = pd.DataFrame(freq_mat)
    # row is mutations, column is generation from the first generation
    mutation_effectsize = np.array([float(i) for i in mutation_effectsize]) #from the first genertaion
    mutation_chromosome = np.array([0 if int(i)<=ch_sep else 1 for i in mutation_positions])
    generations = len(freq_mat[0]) # from the first generation
    #print(generations)
    total_effect_size = []
    total_es_ch1 = []
    total_es_ch2 = []
    
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
    
    #print(total_effect_size)
    #attribute_list = 0.038*(np.array(total_effect_size)+0.745092)/0.745092
    #total_effect_size = smooth(attribute_list)
    average_attribute = np.mean(attribute_list)
    total_effect_size = smooth(np.array(total_effect_size))
    effectvar_sd = smooth(effectvar_sd)
    total_es_ch1 = smooth(total_es_ch1)
    total_es_ch2 = smooth(total_es_ch2)
    average_total_es = -1
    final_effectvar_sd = -1
    ch1_es_reduction = total_es_ch1[-1] - total_es_ch1[9]
    ch2_es_reduction = total_es_ch2[-1] - total_es_ch2[9]
    total_es_reduction_first200 = -1
    ch1_es_reduction_first200 = -1
    ch2_es_reduction_first200 = -1
    total_es_reduction_after200 = -1
    ch1_es_reduction_after200 = -1
    ch2_es_reduction_after200 = -1
    relative_ratio_first200 = -1
    effectvar_sd_reduction = 0
    start_gen = int(3.167*200)+ release_gen
    if generations>start_gen: #== 1604:
        average_total_es = np.mean(total_effect_size[-100:])#[-317:])
        total_es_reduction_first200 = (total_effect_size[start_gen]-total_effect_size[9])#/200
        relative_ratio_first200 = attribute_list[start_gen]/attribute_list[9]
        ch1_es_reduction_first200 = (total_es_ch1[start_gen]-total_es_ch1[release_gen-1])/(start_gen-release_gen+1)
        ch2_es_reduction_first200 = (total_es_ch2[start_gen]-total_es_ch2[release_gen-1])/(start_gen-release_gen+1)
        total_es_reduction_after200 = (total_effect_size[-1]-total_effect_size[start_gen])#/(generations-start_gen)
        ch1_es_reduction_after200 = (total_es_ch1[-1]-total_es_ch1[start_gen])/(generations-start_gen)
        ch2_es_reduction_after200 = (total_es_ch2[-1]-total_es_ch2[start_gen])/(generations-start_gen)
        final_effectvar_sd = effectvar_sd[-1]
        effectvar_sd_reduction = effectvar_sd[-1]/effectvar_sd[9]
    #return attribute_list,effectvar_sd,attribute_list[8],total_effect_size[-1]/total_effect_size[9],total_effect_size[-1]-total_effect_size[9],param_b,average_total_es,total_es_reduction_first200,relative_ratio_first200,ch1_es_reduction_first200,ch2_es_reduction_first200,total_es_reduction_after200,ch1_es_reduction_after200,ch2_es_reduction_after200#,final_effectvar_sd
    return attribute_list[8],total_es_ch1[9],total_es_ch2[9],attribute_list[-1]/attribute_list[9],total_effect_size[-1],param_b,property_initial_sd,average_attribute,ch1_es_reduction,ch2_es_reduction,total_es_reduction_first200,relative_ratio_first200,ch1_es_reduction_first200,ch2_es_reduction_first200,total_es_reduction_after200,ch1_es_reduction_after200,ch2_es_reduction_after200,final_effectvar_sd,effectvar_sd_reduction

def parse_inbreeding_slim(out):
    out = str(out)
    out = out.split('\n')
    mut_per_ind = []
    mut_locus_num = []
    avg_fitness = []
    df = pd.DataFrame()
    area = 1
    release_gen = 21
    for line in out:
        if line.startswith("RELEASE_TICK: "):
            release_gen = int((line.strip()).replace("RELEASE_TICK: ", ''))
        if line.startswith("SIM BOUND:"):
            area = float(line.replace('SIM BOUND: ',''))
        if line.startswith("Deleterious mutations per ind: "):
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
    df.columns = ['wt allele number','gen','pop size','rate drive carriers','average nni','var nni']
    df['normalized nni'] = df['average nni']/(0.5/np.sqrt(df['pop size'])*area)
    
    generations = len(mut_per_ind) # from the first generation
    initial_popsize = np.mean((df['pop size'])[release_gen-50:release_gen-1])
    
    weighted_I_first200=-1;weighted_I_after200=-1;popsize_first200=-1;popsize_after200=-1
    initial_fitness = np.mean(avg_fitness[release_gen-50:release_gen-1])
    initial_mutno_ind = np.mean(mut_per_ind[release_gen-50:release_gen-1])
    initial_mutlocus_num = np.mean(mut_locus_num[release_gen-50:release_gen-1])

    if generations > int(release_gen+300):
        weighted_I_first200 = sum((df['pop size'])[release_gen:release_gen+200]*(df['normalized nni'])[release_gen:release_gen+200])/sum((df['pop size'])[release_gen:release_gen+200])
        weighted_I_after200 = sum((df['pop size'])[release_gen+201:]*(df['normalized nni'])[release_gen+201:])/sum((df['pop size'])[release_gen+201:])
        popsize_first200 = np.mean((df['pop size'])[release_gen:release_gen+200])
        popsize_after200 = np.mean((df['pop size'])[release_gen+201:])
        # record the average mutation frequency of last 100 generations on each chromosome
        final_mutno_ind = np.mean(mut_per_ind[-100:])
        final_mutlocus_num = np.mean(mut_locus_num[-100:])
        final_fitness = np.mean(avg_fitness[-100:])
        fitness_first200 = np.mean(avg_fitness[release_gen:release_gen+200])
        fitness_after200 = np.mean(avg_fitness[release_gen+201:])
    else:
        final_mutno_ind = -1
        final_mutlocus_num = -1
        final_fitness = -1
        fitness_first200 = -1
        fitness_after200 = -1
    return initial_popsize,weighted_I_first200,weighted_I_after200,popsize_first200,popsize_after200,fitness_first200,fitness_after200,initial_mutno_ind,initial_fitness,initial_mutlocus_num,final_mutno_ind,final_fitness,final_mutlocus_num

def parse_slim(slim_out):
    """
    read the slim output and got the wt, dr, and gc data.
    the spatial record file contains the data of 20 simulations.

    Parameters
    ----------
    filepath : TYPE
        DESCRIPTION.

    Returns dataframe contains wt, dr, gc data.
    -------
    None.

    """
    suppressed_with_chasing = 0
    suppressed_without_chasing = 0
    chasing_or_equilibrium = 0
    long_term_chasing = 0
    equilibrium = 0
    gen_suppressed = 10000
    gen_chasing_start = 0
    duration_of_chasing = 0
    drive_loss = 0
    pop_persist = 10000
    avg_fertile_female = 1000000
    is_persist = 0
    number_of_fertile_females = []
    generation_time = 3.167
    area = 1
    release_gen = 21
    
    # chasing dynamic test variables
    I = -1
    I_w = -1
    var_nni_across_time = -1
    var_I_across_time = -1
    pop_size = -1
    average_drive_frequency = -1
    average_r2_frequency = -1
    
    chasing_gen_threshold = 80
    df1 = pd.DataFrame()
    df2 = pd.DataFrame()
    slim_out = slim_out.split('\n')
    #print(slim_out[0:10])
    for line in slim_out:
        if line.startswith("RELEASE_TICK: "):
            release_gen = int((line.strip()).replace("RELEASE_TICK: ", ''))
        # collect the population dynamics
        if line.startswith('POPULATION_SIZE:'):
            # from the first generation
            pop_size = int((line.strip()).replace("POPULATION_SIZE: ", ''))
        if line.startswith('GEN:'):
            line1 = line.strip()
            line1 = line1.split(' ')
            df1 = pd.concat([df1,pd.DataFrame([[int(line1[1]),float(line1[3]),pop_size,float(line1[5])]])])#,float(line1[5])
        if line.startswith('WT_AL'):
            line2 = line.strip()
            line2 = line2.split(' ')
            df2 = pd.concat([df2,pd.DataFrame([[int(line2[1]),int(line2[2]),int(line2[3]),float(line2[4]),float(line2[6]),float(line2[8])]])])
        
        # direct outcome collect
        if line.startswith('POP_PERSISTS'):
            drive_loss = 1
            pop_persist = int(line.replace('POP_PERSISTS:: ',''))
        if line.startswith('CHASING START'):
            gen_chasing_start = int(line.replace('CHASING START:: ',''))
        if line.startswith('SUPPRESSED WITHOUT CHASING'):
            suppressed_without_chasing = 1
            gen_suppressed = int(line.replace('SUPPRESSED WITHOUT CHASING:: ',''))
        if line.startswith('SUPPRESSED WITH CHASING'):
            suppressed_with_chasing = 1
            gen_suppressed = int(line.replace('SUPPRESSED WITH CHASING:: ',''))
        if line.startswith('ENDING_AFTER_1000_WEEKS'):
            is_persist = 1
        if line.startswith("FERTILE_FEMALES:: "):
            spaced_line = line.split()
            number_of_fertile_females.append(int(spaced_line[1]))
        if line.startswith("GENERATION TIME:"):
            generation_time = float(line.replace('GENERATION TIME: ',''))
        if line.startswith("SIM BOUND:"):
            area = float(line.replace('SIM BOUND: ',''))
        
    if (len(df1)!=0):
        df1.columns = ['gen','drive frequency','pop size','r2 frequency']
    if (len(df1)!=0 and len(df2)!=0):
        # release drive and detect chasing
        df2.columns = ['wt allele number','gen','pop size','rate drive carriers','average nni','var nni']
        df = pd.merge(df1,df2,how='right')# how='right',on=['gen','pop size']
        df['normalized nni'] = df['average nni']/(0.5/np.sqrt(df['pop size'])*area)
        '''parse the outcome of drive'''
        record = df
        #standard_var = (0.26136/np.sqrt(record['pop size']))**2
        # weighted chasing aggregation
        record = record.loc[record['average nni']!= 0]
        #record['average nni'] = [float(i) for i in record['average nni']]
        # the random distribution var and mean 
        standard_mean = 0.5/np.sqrt(record['pop size'])*area
        # what we need is the I during chasing
        if (record.iloc[-1])['gen']>chasing_gen_threshold*generation_time+release_gen:
            chasing_record = record.loc[record['gen']>chasing_gen_threshold*generation_time+release_gen]  
            chasing_standard_mean = 0.5/np.sqrt(chasing_record['pop size'])*area
            I = chasing_record['average nni']/chasing_standard_mean
            I = np.mean(I[-100:])
            I_w = sum(chasing_record['pop size']*chasing_record['average nni']/chasing_standard_mean)/sum(chasing_record['pop size'])
            var_nni_across_time = np.var(chasing_record['average nni'])
            var_I_across_time = np.var(chasing_record['average nni']/chasing_standard_mean)
        else:
            I = np.mean(record['average nni']/standard_mean)
            I_w = sum(record['pop size']*record['average nni']/standard_mean)/sum(record['pop size'])
            var_nni_across_time = np.var(record['average nni'])
            var_I_across_time = np.var(record['average nni']/standard_mean)
            
        # # plot the change of I with generations
        # plt.plot(record['gen'],record['average nni']/standard_mean)
        # plt.show()nihao
    elif (len(df2)!=0):
        # no drop (temporary)
        df2.columns = ['wt allele number','gen','pop size','rate drive carriers','average nni','var nni']
        df = df2
    else:
        # non-wt frequency don't reach 20% 
        df = df1
         
    if(len(df)>chasing_gen_threshold*generation_time):
        pop_size = np.mean(df['pop size'].iloc[-100:])
        average_drive_frequency = np.mean(df['drive frequency'].iloc[-100:])
        average_r2_frequency = np.mean(df['r2 frequency'].iloc[-100:])
     
        
    if is_persist == 1:
        chasing_or_equilibrium = 1
        if gen_chasing_start == 0:
            equilibrium = 1
        else:
            long_term_chasing = 1
    
    if (gen_chasing_start!=0):
        avg_fertile_female = np.mean(number_of_fertile_females[gen_chasing_start:])
        duration_of_chasing = df.iloc[-1]['gen']+1-gen_chasing_start
        # if chasing gen is too short, then see it as no chasing
        if duration_of_chasing<5:
            if suppressed_with_chasing==1:
                suppressed_without_chasing=1
                suppressed_with_chasing=0
                gen_chasing_start = 0
                duration_of_chasing=0
                avg_fertile_female = np.mean(number_of_fertile_females)
            if drive_loss==1:
                gen_chasing_start = 0
                duration_of_chasing = 0
                avg_fertile_female = np.mean(number_of_fertile_females)
    else:
        avg_fertile_female = np.mean(number_of_fertile_females)
    
    
    return [generation_time,suppressed_without_chasing,suppressed_with_chasing,gen_suppressed,gen_chasing_start,
            duration_of_chasing,chasing_or_equilibrium,I,I_w,var_nni_across_time,var_I_across_time,
            long_term_chasing,equilibrium,avg_fertile_female,drive_loss,pop_persist,pop_size,
            average_drive_frequency,average_r2_frequency]
    #return df,I




def run_slim(command_line_args,filename):
    """
    Runs SLiM using subprocess.
    Args:
        command_line_args: list; a list of command line arguments.
    return: The entire SLiM output as a string.
    """
    slim = subprocess.Popen(command_line_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True)
    out, err = slim.communicate()
    with open(filename,'a') as f:
        f.write(out)
    print(err)
    print(out)
    return out


def configure_slim_command_line(args_dict):
    """
    Sets up a list of command line arguments for running SLiM.
    Args:
        args_dict: a dictionary of arg parser arguments.
    Return
        clargs: A formated list of the arguments.
    """
# We're running SLiM, so the first arg is simple:
    clargs = SLIM + " "
# The filename of the source file must be the last argument:
    source = args_dict.pop("source")
# Add each argument from arg parser to the command line arguemnts for SLiM:
    for arg in args_dict:
        if isinstance(args_dict[arg], bool):
            clargs += f"-d {arg}={'T' if args_dict[arg] else 'F'} " #字符串前加f可以解析大括号中的表达式
        elif isinstance(args_dict[arg],str):
            clargs += f"-d {arg}='{args_dict[arg]}' "
        else:
            clargs += f"-d {arg}={args_dict[arg]} "
    print(clargs)
# Add the source file, and return the string split into a list.
    clargs += source
    return clargs.split()

def main():
    parser = ArgumentParser()
    parser.add_argument('-src', '--source', default="anoph_spatial.slim", type=str,
    help=r"SLiM file to be run. Default 'generic_spatial.slim'") #字符串前加r可以去掉有特殊意义的字符（忽略转义）
    parser.add_argument('-o', '--outputfile', default="0-0results.csv", type=str,
    help=r"output file.")
    parser.add_argument('-rawoutput', '--rawoutputfile', default="mut_num_results.out", type=str,
    help=r"output file.")
    parser.add_argument('-header', '--print_header', action='store_true', default=False,
    help='If this is set, python prints a header for a csv file.')
    #parser.add_argument('-migrationvalue','--SPEED', default=0.05*math.sqrt(2/math.pi), type=float,help='value')
    parser.add_argument('-side','--SIM_BOUND',default=1.0,type=float)
    parser.add_argument('-nodrop','--NO_DROP',action="store_true",default=False,help='if release drive')
    parser.add_argument('-complexOutput','--COMPLEX_OUTPUT',action="store_true",default=False,help='if output genetic diversity attribute')
    parser.add_argument('-gambiae','--ZPG_STEPHENSI', action="store_true",default=False,help='if the species is Anopheles gambiae')
    parser.add_argument('-genDiver','--GENETIC_DIVERSITY', action="store_true",default=False,help='if contains genetic diversity')
    parser.add_argument('-control','--GENETIC_DIVERSITY_CONTROL', action="store_true",default=False,help='if the control of mutations')
    parser.add_argument('-dcMut','--DRIVE_CONVERSION_MUTATION', action="store_true",default=False,help='mutations affect drive conversion')
    parser.add_argument('-erMut','--EMBRYO_RESISTANCE_MUTATION', action="store_true",default=False,help='mutations affect embryo resistance')
    parser.add_argument('-sfMut','--SOMATIC_FITNESS_MUTATION', action="store_true",default=False,help='mutations affect somatic fitness')
    parser.add_argument('-diMut','--MIGRATION_RATE_MUTATION', action="store_true",default=False,help='mutations affect embryo resistance')
    parser.add_argument('-inbreedMut','--INBREEDING_MUTATION', action="store_true",default=False,help='if contatins inbreeding recessive lethal mutations')
    parser.add_argument('-releaseTick', '--RELEASE_TICK',default=21,type=int)
    parser.add_argument('-endTick', '--END_TICK',default=1021,type=int)
    parser.add_argument('-ie','--DELETERIOUS_MEAN_EFFECTSIZE',default=-0.2,type=float)
    parser.add_argument('-mu','--MUTATION_RATE',default=0.000006,type=float)
    parser.add_argument('-inbredExp','--OFFSPRING_EXPANDER',default=1.075,type=float)
    parser.add_argument('-mutnum','--NUMBER_OF_MUTATION',default=8000,type=int)
    parser.add_argument('-dispar', '--CONCAVE_DEGREE',default=100.0,type=float)
    parser.add_argument('-b', '--MUTATION_DISTRIBUTION_B',default=-1,type=float)
    parser.add_argument('-lowdensity','--LOW_DENSITY_GROWTH_RATE', default=6.0, type=float)
    parser.add_argument('-popdensity','--EFFECTIVE_FEMALE_NUMBER', default=10000, type=int)
    parser.add_argument('-video','--OUTPUT_SPATIAL_DATA',default=False,type=bool)
    parser.add_argument('-embryo','--EMBRYO_RESISTANCE_CUT_RATE_F_INPUT', default=0.08, type=float)
    parser.add_argument('-germline','--WHOLE_GERMLINE_RESISTANCE_CUT_RATE_F', default=0.01, type=float)
    parser.add_argument('-fitness','--SOMATIC_FITNESS_MULTIPLIER_F', default=0.5, type=float)
    parser.add_argument('-conversion','--DRIVE_CONVERSION', default=0.85, type=float)
    parser.add_argument("-migdis",'--DISTANCE',default=0.03,type=float)
    parser.add_argument("-disfitSlope",'--DIS_FIT_SLOPE',default=-2.165,type=float)
    parser.add_argument("-dendis",'--COMPETITION_DIST',default=0.01,type=float)
    parser.add_argument('-r','--runs', default=1, type=int) # without changing normally
    
    args_dict = vars(parser.parse_args()) #vars()转换成字典
    # print(args_dict)
    model = (args_dict['source']).replace(".slim",'')
    output_file = args_dict.pop("outputfile")
    raw_output_file = args_dict.pop("rawoutputfile")
    germline_resistance = args_dict['WHOLE_GERMLINE_RESISTANCE_CUT_RATE_F']
    embryo_resistance = args_dict['EMBRYO_RESISTANCE_CUT_RATE_F_INPUT']
    drive_conversion = args_dict['DRIVE_CONVERSION']
    somatic_fitness = args_dict['SOMATIC_FITNESS_MULTIPLIER_F']
    low_density_growth_rate = args_dict['LOW_DENSITY_GROWTH_RATE']
    migdis = args_dict['DISTANCE']
    competition_dis = args_dict['COMPETITION_DIST']
    side = args_dict['SIM_BOUND']
    pop_density = args_dict['EFFECTIVE_FEMALE_NUMBER']
    control = args_dict['GENETIC_DIVERSITY_CONTROL']
    gambiae = args_dict['ZPG_STEPHENSI']
    drive_conversion_diversity = int(args_dict['DRIVE_CONVERSION_MUTATION'])
    embryo_resistance_diversity = int(args_dict['EMBRYO_RESISTANCE_MUTATION'])
    somatic_fitness_diversity = int(args_dict['SOMATIC_FITNESS_MUTATION'])
    dispersal_diversity = int(args_dict['MIGRATION_RATE_MUTATION'])
    inbreeding_mutation = int(args_dict['INBREEDING_MUTATION'])
    deleterious_mean_effectsize = args_dict['DELETERIOUS_MEAN_EFFECTSIZE']
    mu = args_dict["MUTATION_RATE"]
    mutation_number = args_dict['NUMBER_OF_MUTATION']
    disfit_slope = args_dict['DIS_FIT_SLOPE']
    concave_degree = args_dict['CONCAVE_DEGREE']
    runs = int(args_dict.pop("runs"))
    args_dict['seed'] = (np.random.default_rng().integers(low=0,high=2**62-1,size=1))[0]
# The '-header' argument prints a header for the output. This can
# help generate a nice CSV by adding this argument to the first SLiM run:
    f = open(output_file, 'a')
    if args_dict.pop("print_header",None):
        f.write("model,migration rate,low density growth rate,remate chance,lifespan,drive_conversion,somatic_fitness,embryo_resistance,growth curve,sim bound,population density,competition distance,generation time,suppressed_without_chasing,suppressed_with_chasing,gen_suppressed,gen_chasing_start,\
                duration_of_chasing,chasing_or_equilibrium,I,weighted I,var_nni_across_time,var_I_across_time,long_term_chasing,equilibrium,avg_fertile_female,drive_loss,pop_persist,pop_size")
        f.write('\n')
    f.close()
# Next, assemble the command line arguments in the way we want to for SLiM:
# Run the file with the desired arguments.
    clargs = configure_slim_command_line(args_dict)
    for i in range(runs):
        out = run_slim(clargs,raw_output_file)
        dynamic_results = parse_slim(out)
        if (drive_conversion_diversity | embryo_resistance_diversity | somatic_fitness_diversity | dispersal_diversity):
            mutation_results = parse_gendiver_slim(out)
        if (inbreeding_mutation):
            mutation_results = parse_inbreeding_slim(out)
        
        with open(output_file,'a') as fo:
            fo.write(model+","+str(migdis)+","+str(low_density_growth_rate)+","+str(drive_conversion)+","
                     +str(somatic_fitness)+","+str(germline_resistance)+","+str(embryo_resistance)+','+str(side)+","+str(pop_density)+","
                     +str(competition_dis)+","+str(gambiae)+","+str(control)+","+str(drive_conversion_diversity)+","+str(embryo_resistance_diversity)+","
                     +str(somatic_fitness_diversity)+","+str(dispersal_diversity)+","+str(inbreeding_mutation)+","+str(deleterious_mean_effectsize)+","
                     +str(mu)+","+str(mutation_number)+","+str(concave_degree)+","+str(disfit_slope)+",")
            for i in dynamic_results:
                fo.write(str(i)+",")
            
            if (drive_conversion_diversity | embryo_resistance_diversity | somatic_fitness_diversity | inbreeding_mutation | dispersal_diversity):
                for i in mutation_results:
                    fo.write(str(i)+",")
            fo.write('\n')
        # fig = relation_plot(df)
        # fig.savefig("0-0results"+'/'+file_name+'.png')
        # make video
        # video(file_name+'_movie')#file_name+'_movie')
        

if __name__ =="__main__":
    main()
    


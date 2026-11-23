# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 20:24:28 2024

@author: Xinyue
"""
from argparse import ArgumentParser
import subprocess
import math
import pandas as pd
import numpy as np


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

def parse_inbreeding_slim(out):
    out = str(out)
    out = out.split('\n')
    population_size = []
    mut_per_ind = []
    mut_locus_num = []
    avg_fitness = []
    release_gen = 21
    for line in out:
        if line.startswith("RELEASE_TICK: "):
            release_gen = int((line.strip()).replace("RELEASE_TICK: ", ''))
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
    
    generations = len(mut_per_ind) # from the first generation
    initial_popsize = np.mean(population_size[release_gen-50:release_gen-1])
    
    popsize_first200=-1;popsize_after200=-1
    initial_fitness = np.mean(avg_fitness[release_gen-50:release_gen-1])
    initial_mutno_ind = np.mean(mut_per_ind[release_gen-50:release_gen-1])
    initial_mutlocus_num = np.mean(mut_locus_num[release_gen-50:release_gen-1])

    if generations > int(release_gen+300):
        popsize_first200 = np.mean(population_size[release_gen:release_gen+200])
        popsize_after200 = np.mean(population_size[release_gen+201:])
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
    return initial_popsize,popsize_first200,popsize_after200,fitness_first200,fitness_after200,initial_mutno_ind,initial_fitness,initial_mutlocus_num,final_mutno_ind,final_fitness,final_mutlocus_num


def parse_gendiver_slim(out):
    out = str(out)
    out = out.split('\n')
    #print(out)
    # row is mutations, column is generations, value is mutation frequency
    freq_mat = []
    population_size = []
    drive_rate = []
    r2_rate = []
    suppressed = 0
    suppress_gen = 0
    drive_loss = 0
    drive_loss_gen = 0
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
            attribute_sd = (line.strip()).replace("attribute standard deviation: ",'')
            if attribute_sd != "NULL":
                attribute_sd = float(attribute_sd)
                effectvar_sd.append(attribute_sd)
        if line.startswith("POPULATION_SIZE:"):
            # from the first generation
            population_size.append(int((line.strip()).replace("POPULATION_SIZE: ", '')))
        if line.startswith("GEN:"):
            # drive rate from 10th generation
            cons = (line.strip()).split()
            if cons[3]!='NAN':
                drive_rate.append(float(cons[3]))
            if cons[5]!='NAN':
                r2_rate.append(float(cons[5]))
        # if line.startswith("EFFECTSIZE_OF_INDIVIDUALS:"):
        #     # the distribution of effectsize from the first generation
        #     dcs = (line.strip()).replace("EFFECTSIZE_OF_INDIVIDUALS: ", '')
        #     dcs = [float(i) for i in dcs.split()]
        #     effectvar_sd.append(np.std(dcs))
        #     effectvar_mean.append(np.mean(dcs))
        if line.startswith("MUTATION_POSITIONS:"):
            mutation_positions = (line.replace("MUTATION_POSITIONS: ", '')).split()
        if line.startswith("MUTATION_EFFECTSIZE:"):
            mutation_effectsize = (line.replace("MUTATION_EFFECTSIZE: ", '')).split()
        if line.startswith("mutation"):
            con = line.split()
            if con[3]!='NAN':
                freq_mat[int(con[1])-10].append(float(con[3]))
        if line.startswith("SUPPRESSED:"):
            # after the release, from the 10th gens
            suppressed = 1
            suppress_gen = int((line.strip()).replace("SUPPRESSED: ",''))
        if line.startswith("DRIVE LOSS:"):
            # after the release, from the 10th gens
            drive_loss = 1
            drive_loss_gen = int((line.strip()).replace("DRIVE LOSS: ",''))
            
    
    
    average_popsize = 0
    average_drive_freq = 0
    average_r2_freq = 0
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
    print(generations)
    
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
    final_effectvar_sd = -1
    #print(total_es_ch1)
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
    start_gen = int(3.167*200)+release_gen
    
    if generations>start_gen: #== 1604:
        total_es_reduction_first200 = (total_effect_size[start_gen]-total_effect_size[9])#/200
        relative_ratio_first200 = attribute_list[start_gen]/attribute_list[9]
        ch1_es_reduction_first200 = (total_es_ch1[start_gen]-total_es_ch1[release_gen-1])/(start_gen-release_gen+1)
        ch2_es_reduction_first200 = (total_es_ch2[start_gen]-total_es_ch2[release_gen-1])/(start_gen-release_gen+1)
        total_es_reduction_after200 = (total_effect_size[-1]-total_effect_size[start_gen])#/(generations-start_gen)
        ch1_es_reduction_after200 = (total_es_ch1[-1]-total_es_ch1[start_gen])/(generations-start_gen)
        ch2_es_reduction_after200 = (total_es_ch2[-1]-total_es_ch2[start_gen])/(generations-start_gen)
        final_effectvar_sd = effectvar_sd[-1]
        effectvar_sd_reduction = effectvar_sd[-1]/effectvar_sd[9]
        average_drive_freq = np.mean(drive_rate[-100:])
        average_r2_freq = np.mean(r2_rate[-100:])
        average_popsize = np.mean(population_size[-100:])
    #return attribute_list,effectvar_sd,attribute_list[8],total_effect_size[-1]/total_effect_size[9],total_effect_size[-1]-total_effect_size[9],param_b,average_total_es,total_es_reduction_first200,relative_ratio_first200,ch1_es_reduction_first200,ch2_es_reduction_first200,total_es_reduction_after200,ch1_es_reduction_after200,ch2_es_reduction_after200#,final_effectvar_sd
    return suppressed,suppress_gen,drive_loss,drive_loss_gen,average_drive_freq,average_r2_freq,average_popsize,attribute_list[8],total_es_ch1[9],total_es_ch2[9],attribute_list[-1]/attribute_list[9],total_effect_size[-1],param_b,property_initial_sd,average_attribute,ch1_es_reduction,ch2_es_reduction,total_es_reduction_first200,relative_ratio_first200,ch1_es_reduction_first200,ch2_es_reduction_first200,total_es_reduction_after200,ch1_es_reduction_after200,ch2_es_reduction_after200,final_effectvar_sd,effectvar_sd_reduction


def parse_slim(out):
    out = str(out)
    out = out.split('\n')
    suppressed = 0
    suppress_gen = 0
    drive_loss = 0
    drive_loss_gen = 0
    population_size = []
    drive_rate = []
    r2_rate = []
    release_gen = 21
    for line in out:
        if line.startswith("RELEASE_TICK: "):
            release_gen = int((line.strip()).replace("RELEASE_TICK: ", ''))
        if line.startswith("SUPPRESSED:"):
            # after the release, from the 10th gens
            suppressed = 1
            suppress_gen = int((line.strip()).replace("SUPPRESSED: ",''))
        if line.startswith("DRIVE LOSS:"):
            # after the release, from the 10th gens
            drive_loss = 1
            drive_loss_gen = int((line.strip()).replace("DRIVE LOSS: ",''))
        if line.startswith("POPULATION_SIZE:"):
            # from the first generation
            population_size.append(int((line.strip()).replace("POPULATION_SIZE: ", '')))
        if line.startswith("GEN:"):
            # drive rate from 10th generation
            cons = (line.strip()).split()
            if cons[3]!='NAN':
                drive_rate.append(float(cons[3]))
            if cons[5]!='NAN':
                r2_rate.append(float(cons[5]))
    generations = len(population_size)
    average_popsize = 0
    average_drive_freq = 0
    average_r2_freq = 0
    capacity = np.mean(population_size[10:20])
    if generations > release_gen+200:
        average_drive_freq = np.mean(drive_rate[-100:])
        average_popsize = np.mean(population_size[-100:])
        average_r2_freq = np.mean(r2_rate[-100:])

    return capacity,suppressed,suppress_gen,drive_loss,drive_loss_gen,average_drive_freq,average_r2_freq,average_popsize

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
    #print(clargs)
# Add the source file, and return the string split into a list.
    clargs += source
    return clargs.split()

def main():
    parser = ArgumentParser()
    parser.add_argument('-src', '--source', default="discrete_pan.slim", type=str,
    help=r"SLiM file to be run. Default 'generic_spatial.slim'") #字符串前加r可以去掉有特殊意义的字符（忽略转义）
    parser.add_argument('-o', '--outputfile', default="mut_num_results.csv", type=str,
    help=r"output file.")
    parser.add_argument('-rawoutput', '--rawoutputfile', default="mut_num_results.out", type=str,
    help=r"output file.")
    parser.add_argument('-header', '--print_header', action='store_true', default=False,
    help='If this is set, python prints a header for a csv file.')    
    parser.add_argument('-complexOutput','--COMPLEX_OUTPUT',action="store_true",default=False,help='if output genetic diversity attribute')
    parser.add_argument('-stephensi','--ZPG_STEPHENSI', action="store_true",default=False,help='if the species is Anopheles gambiae')
    parser.add_argument('-genDiver','--GENETIC_DIVERSITY', action="store_true",default=False,help='if contains genetic diversity')
    parser.add_argument('-control','--GENETIC_DIVERSITY_CONTROL', action="store_true",default=False,help='if the control of mutations')
    parser.add_argument('-dcMut','--DRIVE_CONVERSION_MUTATION', action="store_true",default=False,help='mutations affect drive conversion')
    parser.add_argument('-erMut','--EMBRYO_RESISTANCE_MUTATION', action="store_true",default=False,help='mutations affect embryo resistance')
    parser.add_argument('-sfMut','--SOMATIC_FITNESS_MUTATION', action="store_true",default=False,help='mutations affect somatic fitness')
    parser.add_argument('-inbreedMut','--INBREEDING_MUTATION', action="store_true",default=False,help='if contatins inbreeding recessive lethal mutations')
    parser.add_argument('-releaseTick', '--RELEASE_TICK',default=21,type=int)
    parser.add_argument('-endTick', '--END_TICK',default=1021,type=int)
    parser.add_argument('-ie','--DELETERIOUS_MEAN_EFFECTSIZE',default=-0.2,type=float)
    parser.add_argument('-mu','--MUTATION_RATE',default=0.000006,type=float)
    parser.add_argument('-inbredExp','--OFFSPRING_EXPANDER',default=1.075,type=float)
    parser.add_argument('-mutnum','--NUMBER_OF_MUTATION',default=100,type=int)
    parser.add_argument('-dispar', '--CONCAVE_DEGREE',default=100.0,type=float)
    parser.add_argument('-b', '--MUTATION_DISTRIBUTION_B',default=-1,type=float)
    parser.add_argument('-lowdensity','--LOW_DENSITY_GROWTH_RATE', default=6.0, type=float)
    parser.add_argument('-popdensity','--EFFECTIVE_FEMALE_NUMBER', default=10000, type=int)
    parser.add_argument('-embryo','--EMBRYO_RESISTANCE_CUT_RATE_F_INPUT', default=0.08, type=float)
    parser.add_argument('-germline','--WHOLE_GERMLINE_RESISTANCE_CUT_RATE_F', default=0.01, type=float)
    parser.add_argument('-fitness','--SOMATIC_FITNESS_MULTIPLIER_F', default=0.5, type=float)
    parser.add_argument('-conversion','--DRIVE_CONVERSION', default=0.85, type=float)
    parser.add_argument('-r','--runs', default=1, type=int) # without changing normally
    args_dict = vars(parser.parse_args()) #vars()转换成字典
    
    model = (args_dict['source']).replace(".slim",'')
    gambiae = args_dict['ZPG_STEPHENSI']
    output_file = args_dict.pop("outputfile")
    raw_output_file = args_dict.pop("rawoutputfile")
    germline_resistance = args_dict['WHOLE_GERMLINE_RESISTANCE_CUT_RATE_F']
    embryo_resistance = args_dict['EMBRYO_RESISTANCE_CUT_RATE_F_INPUT']
    drive_conversion = args_dict['DRIVE_CONVERSION']
    somatic_fitness = args_dict['SOMATIC_FITNESS_MULTIPLIER_F']
    low_density_growth_rate = args_dict['LOW_DENSITY_GROWTH_RATE']
    pop_density = args_dict['EFFECTIVE_FEMALE_NUMBER']
    control = args_dict['GENETIC_DIVERSITY_CONTROL']
    drive_conversion_diversity = int(args_dict['DRIVE_CONVERSION_MUTATION'])
    embryo_resistance_diversity = int(args_dict['EMBRYO_RESISTANCE_MUTATION'])
    somatic_fitness_diversity = int(args_dict['SOMATIC_FITNESS_MUTATION'])
    inbreeding_mutation = int(args_dict['INBREEDING_MUTATION'])
    deleterious_mean_effectsize = args_dict['DELETERIOUS_MEAN_EFFECTSIZE']
    mu = args_dict["MUTATION_RATE"]
    mutation_number = args_dict['NUMBER_OF_MUTATION']
    concave_degree = args_dict['CONCAVE_DEGREE']
    release_gen = int(args_dict['RELEASE_TICK'])
    runs = int(args_dict.pop("runs"))
    args_dict['seed'] = (np.random.default_rng().integers(low=0,high=2**62-1,size=1))[0]
# The '-header' argument prints a header for the output. This can
# help generate a nice CSV by adding this argument to the first SLiM run:
    f = open(output_file, 'a')
    if args_dict.pop("print_header",None):
        f.write("model,low density growth rate,drive_conversion,somatic_fitness,\
                embryo_resistance,population density,distribution concave degree,\
                    mutation number,suppressed,suppressed_gen,drive_loss,gen_drive_loss,\
                        average_drive_frequency,pop_size,average_effect_size,\
                            total_effect_size_reduction,ch1_es_reduction,ch2_es_reduction,\
                                ch3_es_reduction")
        f.write('\n')
    f.close()
# Next, assemble the command line arguments in the way we want to for SLiM:
# Run the file with the desired arguments.
    clargs = configure_slim_command_line(args_dict)
    for i in range(runs):
        out = run_slim(clargs,raw_output_file)
        if (drive_conversion_diversity | embryo_resistance_diversity | somatic_fitness_diversity):
            results = parse_gendiver_slim(out)
            with open(output_file,'a') as fo:
                fo.write(model+","+str(low_density_growth_rate)+","+str(drive_conversion)+","
                         +str(somatic_fitness)+","+str(germline_resistance)+","+str(embryo_resistance)+
                         ","+str(pop_density)+","+str(drive_conversion_diversity)+","+str(embryo_resistance_diversity)+
                         ","+str(somatic_fitness_diversity)+","+str(gambiae)
                         +","+str(control)+","+str(inbreeding_mutation)+","+str(deleterious_mean_effectsize)+","
                         +str(mu)+","+str(mutation_number)+","+str(concave_degree)+",")
                for i in results:
                    fo.write(str(i)+",")
                fo.write("\n")
        elif inbreeding_mutation:
            results = parse_slim(out)
            in_results = parse_inbreeding_slim(out)
            with open(output_file,'a') as fo:
                fo.write(model+","+str(low_density_growth_rate)+","+str(drive_conversion)+","
                         +str(somatic_fitness)+","+str(germline_resistance)+","+str(embryo_resistance)+
                         ","+str(pop_density)+","+str(drive_conversion_diversity)+","+str(embryo_resistance_diversity)
                         +","+str(control)+","+str(inbreeding_mutation)+","+str(deleterious_mean_effectsize)+","
                         +str(mu)+","+str(mutation_number)+","+str(concave_degree)+",")
                for i in results:
                    fo.write(str(i)+",")
                for i in in_results:
                    fo.write(str(i)+",")
                fo.write("\n")
        else:
            results = parse_slim(out)
            with open(output_file,'a') as fo:
                fo.write(model+","+str(low_density_growth_rate)+","+str(drive_conversion)+","
                         +str(somatic_fitness)+","+str(germline_resistance)+","+str(embryo_resistance)+
                         ","+str(pop_density)+","+str(drive_conversion_diversity)+","+str(embryo_resistance_diversity)
                         +","+str(control)+","+str(inbreeding_mutation)+","+str(deleterious_mean_effectsize)+","
                         +str(mu)+","+str(mutation_number)+","+str(concave_degree)+",")
                for i in results:
                    fo.write(str(i)+",")
                fo.write("\n")
        

if __name__ =="__main__":
    main()
    # with open("multiple mutations test/test.txt",'r') as f:
    #     out = f.read()
    #     print(parse_slim(out))
        




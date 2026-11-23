# -*- coding: utf-8 -*-
"""
Created on Wed Jan 14 18:31:36 2026

@author: HP
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import os
import array_process_pan
import pan_data_process
import spatial_data_process


if __name__ == "__main__":
    figure_group_var='property_initial_sd'
    
    # ### spatial data comparsion
    # population dynamics
    # spatial_data_process.single_genDiver_vs_control("multiple mutations test/pan vs spa/spatial/drive conversion results/85/85spaital_dc_mut_results.out", "multiple mutations test/pan vs spa/spatial/drive conversion results/85/85spaital_dc_control_results.out","drive conversion","multiple mutations test/pan vs spa/spatial/drive conversion results/70/70spaital_dc_mut_results.out", "multiple mutations test/pan vs spa/spatial/drive conversion results/70/70spaital_dc_control_results.out")
    # spatial_data_process.single_genDiver_vs_control("multiple mutations test/pan vs spa/spatial/drive conversion results/85/85spaital_dc_mut_results.out", "multiple mutations test/pan vs spa/spatial/drive conversion results/85/85spaital_dc_control_results.out","drive conversion")
    #spatial_data_process.single_genDiver_vs_control("multiple mutations test/pan vs spa/spatial/drive conversion results/70/70spaital_dc_mut_results.out", "multiple mutations test/pan vs spa/spatial/drive conversion results/70/70spaital_dc_control_results.out","drive conversion")
    
    # spatial_data_process.spatial_statistic_data("multiple mutations test/pan vs spa/spatial/dc_results.xlsx",['drive_conversion','control'],True,False)
    # spatial_data_process.spatial_statistic_data("multiple mutations test/pan vs spa/spatial/er_results.xlsx",['drive_conversion','control'],True,False)
    # ## inside comparison
    # #drive conversion part
    #spatial_data_process.lines("multiple mutations test/pan vs spa/spatial/refer/drive conversion results/70/")
    #spatial_data_process.lines("multiple mutations test/pan vs spa/spatial/refer/drive conversion results/85/")
    #spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/dc_results.xlsx",figure_group_var,'g','average_effect_size','mutations affecting drive conversion')
    #spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/dc_results.xlsx",figure_group_var,'g','pop_size','mutations affecting drive conversion')
    #spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/spatial/refer/dc_results.xlsx",figure_group_var,'drive_conversion','I','mutations affecting drive conversion')
    
    #spatial_data_process.spatial_statistic_data("multiple mutations test/pan vs spa/spatial/dc heatmap/mutnum_b_dc_spa_results.xlsx",['laplace_b','mutation_locus','control'],True,False)
    #spatial_data_process.genDiver_vs_control() # for heatmap
    #spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/spatial/dc heatmap/mutnum_b_dc_spa_results.xlsx",figure_group_var,'mutation_locus','average_effect_size','mutations affecting drive conversion')

    # #embryo resistance part
    # spatial_data_process.lines("multiple mutations test/pan vs spa/spatial/refer/embryo resistance results/70/")
    # spatial_data_process.lines("multiple mutations test/pan vs spa/spatial/refer/embryo resistance results/85/")
    # spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/spatial/refer/er_results.xlsx",figure_group_var,'drive_conversion','average_effect_size','mutations affecting embryo resistance')
    # spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/spatial/refer/er_results.xlsx",figure_group_var,'drive_conversion','pop_size','mutations affecting embryo resistance')
    
    
    # ### panmictic data comparsion
    # #pan_data_process.main() # process raw slim output
    # pan_data_process.process_statistic_data("multiple mutations test/pan vs spa/panmictic/refer/dc_pan_results.xlsx",['drive_conversion','control'],True,False)
    #pan_data_process.process_statistic_data("multiple mutations test/pan vs spa/panmictic/refer/er_pan_result.xlsx",['drive_conversion','control'],True,False)
    # drive conversion part
    #spatial_data_process.lines("multiple mutations test/pan vs spa/panmictic/refer/drive conversion results/70/")
    # spatial_data_process.lines("multiple mutations test/pan vs spa/panmictic/drive conversion results/85/")
    # spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/panmictic/refer/dc_pan_results.xlsx",figure_group_var,'drive_conversion','average_effect_size','mutations affecting drive conversion')
    # spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/panmictic/refer/dc_pan_results.xlsx",figure_group_var,'drive_conversion','pop_size','mutations affecting drive conversion')
    # spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/panmictic/refer/dc_pan_results.xlsx",figure_group_var,'drive_conversion','gen_suppressed','mutations affecting drive conversion')
    #spatial_data_process.single_genDiver_vs_control("multiple mutations test/pan vs spa/panmictic/refer/drive conversion results/70/70pan_dc_mut_results.out", "multiple mutations test/pan vs spa/panmictic/refer/drive conversion results/70/70pan_dc_control_results.out",' effectvar')



    # embryo resistance part
    #spatial_data_process.lines("multiple mutations test/pan vs spa/panmictic/refer/embryo resistance results/70/test/")
    # spatial_data_process.lines("multiple mutations test/pan vs spa/panmictic/embryo resistance results/85/")
    #spatial_data_process.single_genDiver_vs_control("multiple mutations test/pan vs spa/panmictic/refer/embryo resistance results/70/70pan_er_mut_results.out", "multiple mutations test/pan vs spa/panmictic/refer/embryo resistance results/70/70pan_er_control_results.out",True,"embryo resistance")
    #spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/er_results.xlsx",figure_group_var,'g','average_effect_size','mutations affecting embryo resistance')
    #spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/er_results.xlsx",figure_group_var,'g','pop_size','mutations affecting drive conversion')
    #spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/er_results.xlsx",figure_group_var,'g','suppressed','mutations affecting drive conversion')
    
    # spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/panmictic/refer/er_pan_result.xlsx",figure_group_var,'drive_conversion','average_effect_size','mutations affecting embryo resistance')
    # spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/panmictic/refer/er_pan_result.xlsx",figure_group_var,'drive_conversion','pop_size','mutations affecting embryo resistance')
    # spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/panmictic/refer/er_pan_result.xlsx",figure_group_var,'drive_conversion','gen_suppressed','mutations affecting embryo resistance')


    #pan_data_process.process_statistic_data("multiple mutations test/pan vs spa/panmictic/er heatmap/mutnum_b_er_pan_results.xlsx",['laplace_b','mutation_locus','control'],True,False)
    #spatial_data_process.genDiver_vs_control() # for heatmap

    
    # ### spatial vs panmictic
    # # drive conversion part
    # spatial_data_process.lines("multiple mutations test/pan vs spa/panmictic/drive conversion results/70/")
    # spatial_data_process.lines("multiple mutations test/pan vs spa/panmictic/drive conversion results/85/")
    # spatial_data_process.lines("multiple mutations test/pan vs spa/panmictic/embryo resistance results/70/")
    # spatial_data_process.lines("multiple mutations test/pan vs spa/panmictic/embryo resistance results/85/")
    # spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/dc_results.xlsx",'drive_conversion','model','average_effect_size','mutations affecting drive conversion')
    # spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/dc_results.xlsx",'drive_conversion','model','pop_size','mutations affecting drive conversion')

    # # embryo resistance part
    #spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/er_results.xlsx",'drive_conversion','model','average_effect_size','mutations affecting embryo resistance')
    #spatial_data_process.genDiver_vs_control_violin("multiple mutations test/pan vs spa/er_results.xlsx",'drive_conversion','model','pop_size','mutations affecting embryo resistance')



    # heatmap
    #spatial_data_process.genDiver_vs_control()
    
    
    # inbreeding
    #spatial_data_process.spatial_statistic_data("multiple mutations test/inbreeding/pan vs spa/new/spa_results.xlsx",['drive_conversion','inbreeding_mutation'],False,True)
    #pan_data_process.process_statistic_data("multiple mutations test/inbreeding/pan vs spa/new/pan_results.xlsx",['drive_conversion','inbreeding_mutation'],False,True)
    #spatial_data_process.genDiver_vs_control_violin("multiple mutations test/inbreeding/pan vs spa/new/spa_results.xlsx", 'model', 'g','pop_size','panmictic')
    # spatial_data_process.genDiver_vs_control_violin("multiple mutations test/inbreeding/pan vs spa/new/spa_results.xlsx", 'model', 'drive_conversion','suppressed','spaital model')
    # spatial_data_process.genDiver_vs_control_violin("multiple mutations test/inbreeding/pan vs spa/new/pan_results.xlsx", 'model', 'drive_conversion','suppressed','panmictic')
    #spatial_data_process.genDiver_vs_control_violin("multiple mutations test/inbreeding/pan vs spa/new/spa_results.xlsx", 'model', 'drive_conversion','drive_loss','spatial')
    #spatial_data_process.genDiver_vs_control_violin("multiple mutations test/inbreeding/pan vs spa/new/pan_results.xlsx", 'model', 'drive_conversion','drive_loss','panmictic')

    #spatial_data_process.genDiver_vs_control_violin("multiple mutations test/inbreeding/pan vs spa/new/total_results.xlsx", 'distribution concave degree', 'g','pop_size','panmictic')
    # spatial_data_process.genDiver_vs_control_violin("multiple mutations test/inbreeding/pan vs spa/new/spa_results.xlsx", 'distribution concave degree', 'model','pop_size','panmictic')
    #spatial_data_process.ch1_vs_ch2("multiple mutations test/inbreeding/pan vs spa/new/total_results.xlsx", 'g', 'initial_mutno_per_ind', 'final_mutno_per_ind')



    # somatic fitness part
    #spatial_data_process.lines("multiple mutations test/fitness/raw_results/")
    spatial_data_process.spatial_statistic_data("multiple mutations test/fitness/fit_results.xlsx",['control'],True,False)
    
    
    
    
    
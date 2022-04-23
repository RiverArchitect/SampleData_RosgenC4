#############################################################################################
# RA_input.py prepares input for River Architect from tuflow simulation result files
#   Written by Anzy Lee, Postdoctoral Scholar, Utah State University
#   Date: 10/21/2020
#############################################################################################

import os
import shutil as sl
import numpy as np
import arcpy
import sys
import csv
import subprocess
import matplotlib.pyplot as plt

#############################################################################################
# 1 Input variables: case_name, create_folders, copy_depths_velocities, copy_terrain,
#                    [create_dmean, dmean], Q_all
case_name = 'OutphaseC4' # 'VanillaC4', 'InphaseC4', 'OutphaseC4'
create_folders = 1
copy_depths_velocities = 1
copy_terrain = 1
[create_dmean, dmean] = [1, 0.001] # dmean = grain size in meters, 0.001m for sand bed
Q_all = np.array([1,2,3,4,5,6,7,8,9,10,12,15,20,30,40,50,60,70,80,90,100]) # From tuflow_run.

#############################################################################################

if case_name == 'VanillaC4':
    S0 = 0.00325 # dx = 770m , dz = 1004 - 1001.5
    grid_name = 'vanillaC4.asc'
elif case_name == 'InphaseC4':
    S0 = 0.00329 # dx = 770 m, dz = 1004.75 - 1002.22
    grid_name = 'rpinphasec4_dem_1m.asc'
elif case_name == 'OutphaseC4':
    S0 = 0.00331 # dx = 770 m, dz = 1003.3 - 1000.75
    grid_name = 'rpoutphasec4_dem_1m.asc'

#############################################################################################

if create_folders == 1:
    os.mkdir('./01_Conditions/'+case_name)
    os.mkdir('./01_Conditions/' + case_name+'/depth')
    os.mkdir('./01_Conditions/' + case_name+'/velocity')

for ii in range(0,Q_all.__len__()): #np.array([9,19]): # range(0,Q_all.__len__())
    zero1 = ''
    zero2 = ''

    s = str(ii+1)
    s_len = s.__len__()

    for ind in range(0,3-s_len):
        zero1 = zero1 + '0'
    Q_num = zero1 + s

    s = f'{Q_all[ii]:09.3f}'
    s = s.replace('.', '_')
    s_len = s.__len__()

    for ind in range(0, 10 - s_len):
        zero2 = zero2 + '0'
    Q_value = zero2 + s

    if copy_depths_velocities == 1:

        # depth: flt to tif
        in_flt = os.path.abspath("./RosgenC4_"+case_name+"/results/"+Q_num+"/grids/"+case_name+"_"+Q_num+"_d_Max.flt")
        out_raster = os.path.abspath("./01_Conditions/"+case_name+"/depth/h"+Q_value+".tif")
        arcpy.FloatToRaster_conversion(in_flt, out_raster)

        # velocity: flt to tif
        in_flt = os.path.abspath("./RosgenC4_"+case_name+"/results/"+Q_num+"/grids/"+case_name+"_"+Q_num+"_d_Max.flt")
        out_raster = os.path.abspath("./01_Conditions/"+case_name+"/velocity/u"+Q_value+".tif")
        arcpy.FloatToRaster_conversion(in_flt, out_raster)

if copy_terrain == 1:
    in_ascii = os.path.abspath("./RosgenC4_"+case_name+"/model/grid/"+grid_name)
    out_raster = os.path.abspath("./01_Conditions/"+case_name+"/dem.tif")
    rasterType = "FLOAT"
    arcpy.ASCIIToRaster_conversion(in_ascii, out_raster, rasterType)

if create_dmean == 1:
    in_raster = os.path.abspath("./01_Conditions/"+case_name+"/dem.tif")
    out_raster = os.path.abspath("./01_Conditions/"+case_name+"/dmean0.tif")
    arcpy.CopyRaster_management(in_raster, out_raster)

    #arcpy.gp.CheckOutExtension("Spatial")
    #arcpy.gp.workspace = os.path.abspath("./01_Conditions/"+case_name)
    from arcpy.sa import *
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.workspace = os.path.abspath("./01_Conditions/"+case_name)
    in_raster = "dmean0.tif"
    out_raster = "dmean.tif"
    out_minus = Minus(in_raster, in_raster)
    out_dmean = Plus(out_minus,dmean)
    out_dmean.save(out_raster)
    arcpy.Delete_management(in_raster)
#############################################################################################
# tuflow_run.py is an automated python script to run tuflow simulations for various flow conditions
#   Written by Anzy Lee, Postdoctoral Scholar, Utah State University
#   Date: 10/21/2020
#############################################################################################

import os
import shutil as sl
import numpy as np
import sys
import csv
import subprocess
import matplotlib.pyplot as plt

sys.path.append(r'./py_modules')
from mannings_hfromQ_downstream import mannings_hfromQ_downstream

#############################################################################################
# 1 Input variables: case_name, Q_all, create_folders, cell_size
case_name = 'OutphaseC4' # 'VanillaC4', 'InphaseC4', 'OutphaseC4'
Q_all = np.array([1,2,3,4,5,6,7,8,9,10,12,15,20,30,40,50,60,70,80,90,100])
create_folders = 1
cell_size = '1'

#############################################################################################
if os.path.isdir(os.curdir+'/RosgenC4_'+case_name) == 0:
    os.mkdir(os.curdir+'/RosgenC4_'+case_name)
os.chdir(os.curdir+'/RosgenC4_'+case_name)
timestep = str(float(cell_size) / 4)

if case_name == 'VanillaC4':
    S0 = 0.00325 # dx = 770m , dz = 1004 - 1001.5
    grid_name = 'vanillaC4.asc'
elif case_name == 'InphaseC4':
    S0 = 0.00329 # dx = 770 m, dz = 1004.75 - 1002.22
    grid_name = 'rpinphasec4_dem_1m.asc'
elif case_name == 'OutphaseC4':
    S0 = 0.00331 # dx = 770 m, dz = 1003.3 - 1000.75
    grid_name = 'rpoutphasec4_dem_1m.asc'

n = 0.035 # Sand bed, straight, uniform channel

#############################################################################################
if create_folders == 1:
    os.mkdir('./bc_dbase')
    os.mkdir('./check')
    os.mkdir('./model')
    os.mkdir('./results')
    os.mkdir('./runs')
    sl.copytree('../RosgenC4_tuflow//model/gis',
            './model/gis')
    sl.copytree('../RosgenC4_tuflow//model/grid',
             './model/grid')
    sl.copyfile('../RosgenC4_tuflow//model/VanillaC4_materials.csv',
                './model/materials.csv')

#############################################################################################
# Model
tbc_file = './model/' + case_name + '.tbc'
tgc_file = './model/' + case_name + '.tgc'
sl.copyfile('../RosgenC4_tuflow/model/VanillaC4_002.tbc', tbc_file)
sl.copyfile('../RosgenC4_tuflow//model/VanillaC4_002.tgc', tgc_file)

with open(tgc_file, 'r+') as myfile:
    text = myfile.read()
    text = text.replace("Cell Size == 10", "Cell Size == " + cell_size)
    text = text.replace("Read GRID Zpts == ..\model\grid\VanillaC4.asc",
                        "Read GRID Zpts ==..\\model\\grid\\" + grid_name)
    myfile.seek(0)
    myfile.write(text)
    myfile.truncate()

zero = ''
for ii in range(0,Q_all.__len__()): #np.array([9,19]): # range(0,Q_all.__len__())
    zero1 = ''
    s = str(ii+1)
    s_len = s.__len__()

    for ind in range(0,3-s_len):
        zero1 = zero1 + '0'
    Q_num = zero1 + s

    # BCs
    path_down_xsect = './model/gis/2d_bc_VanillaC4_HT_L.shp'
    path_terrain = './model/grid/'+grid_name
    Q = Q_all[ii]
    path_figure = './results/' + case_name + '_' + Q_num + '_WSE.png'
    h, A, P, R = mannings_hfromQ_downstream(path_down_xsect, path_terrain, path_figure, Q, n, S0, 1, 1)
    down_WSE = h


    # Boundary condition
    bc_file = './bc_dbase/2d_bc_'+case_name+'_'+Q_num+'.csv'
    bc_file_content = [['Name', 'Source', 'Column 1', 'Column 2'],
                       ['RPin', case_name + '_bc_data_' + Q_num + '.csv', 'Time', 'RPin'],
                       ['RPout', case_name + '_bc_data_' + Q_num + '.csv', 'Time', 'RPout']]

    bc_data_file = './bc_dbase/'+case_name+'_bc_data_' + Q_num + '.csv'
    bc_data_file_content = [['Time', 'RPin', 'RPout'],
                            [0, Q, h],
                            [0.25, Q, h]]
    #sl.copyfile('../RosgenC4_tuflow/bc_dbase/2d_bc_VanillaC4.csv', bc_file)
    #sl.copyfile('../RosgenC4_tuflow//bc_dbase/VanillaC4_bc_data.csv', bc_data_file)

    with open(bc_file, 'w', newline='') as f:
        writer = csv.writer(f)
        for row in bc_file_content:
            writer.writerow(row)

    with open(bc_data_file, 'w', newline='') as f:
        writer = csv.writer(f)
        for row in bc_data_file_content:
            writer.writerow(row)

    # Material
    material_data = './model/materials.csv'
    material_data_content = [['Material ID', 'Manning\'s n', 'Infiltration Parameters',
                              'Land Use Hazard ID', '! Description'],
                            [1, n],
                            [4, n]]
    with open(material_data, 'w', newline='') as f:
        writer = csv.writer(f)
        for row in material_data_content:
            writer.writerow(row)
    f.close()

    # Run
    tcf_file = os.path.abspath("runs") + '\\'+case_name+'_' + Q_num + '.tcf'
    #sl.copyfile('../RosgenC4_tuflow/runs/VanillaC4_002.tcf', tcf_file)
    f = open(tcf_file, "w+")
    f.write("\n" +
            # "\nUnits == US Customary" +
            "\nGeometry Control File  == " + '..\\model\\' + case_name + '.tgc' +
            "\nBC Control File == " + '..\\model\\' + case_name + '.tbc' +
            "\nBC Database == " + '..\\bc_dbase\\2d_bc_'+case_name+'_'+Q_num+'.csv' +
            "\nRead Materials File == ..\\model\\materials.csv" + "     ! This provides the link between the material ID defined in the .tgc and the Manning's roughess" +
            "\nRead GIS PO == ..\\model\\gis\\2d_po_VanillaC4_P.shp" + "     ! velocity monitoring point locations" +
            "\nRead GIS PO == ..\\model\\gis\\2d_po_VanillaC4_L.shp" + "     ! flow monitoring xs lines" +
            "\nSolution Scheme == HPC  !This command specifies that you want to run TUFLOW using the HPC solution scheme or engine." +
            "\nHardware == GPU  !CPU is default. The hardware command instructs TUFLOW HPC to run using GPU hardware. This is typically orders of magnitude faster than on CPU." +
            "\n" +
            "\nViscosity Formulation == SMAGORINSKY" +
            "\nViscosity Coefficients == 0.5, 0.005" +
            "\nSET IWL == " + str(down_WSE) + "   ! matches the downstream WSE" +
            # "\nCell Wet/Dry Depth == " + cell_depth + "     ! Forces cells to be dry if their depth is < 0.1 m" +
            "\n" +
            "\nStart Time == 0" + "     ! Start Simulation at 0 hours" +
            "\nEnd Time == 6   ! End Simulation (hrs)" +
            "\nTimestep == " + timestep + "     ! Use a 2D time step that is ~1/4 of the grid size in m (10 m * 0.25 -> 2.5 s)" +
            "\n" +
            "\nLog Folder == Log" + "   ! Redirects log output (eg. .tlf and _messages GIS layers to the folder log" +
            "\nOutput Folder == ..\\results\\" + Q_num + "\\" + "     ! Redirects results files to TUFLOW\Results\RUN" +
            "\nWrite Check Files == ..\\check\\" + Q_num + "\\" + "   ! Specifies check files to be written to TUFLOW\check\RUN" +
            "\nMap Output Format == GRID XMDF" + "  ! Output directly to GIS (grid) as well as SMS (xmdf compact) format" +
            "\nMap Output Data Types == h d n V BSS" + "    ! wse depth Manning's n velocity bed shear stress" +
            "\nStart Map Output == 4   ! Start map output at 4 hours" +
            "\nGrid Output Cell Size == " + str(float(cell_size)/2) +
            "\nMap Output Interval == 1800    ! Output every 1800 seconds (30 minutes)" +
            "\nGRID Map Output Data Types == h d n V BSS" +
            "\nTime Series Output Interval  == 30    ! time interval of output in seconds"
            )
    f.close()

    #sl.copyfile('../RosgenC4_tuflow/runs/Vanilla_run_002_TUFLOW.bat',
    #            './runs/'+case_name+'C4_run_'+ Q_num + '_TUFLOW.bat')
    bat_file = './runs/'+ case_name + '_run_' + Q_num + '_TUFLOW.bat'
    f = open(bat_file, "w+")
    f.write("Set TF_Exe=\"C:\Program Files\Tuflow_w64\TUFLOW_iSP_w64.exe\"" +
            "\nSet RUN=start \"TUFLOW\" %TF_Exe%" +
            "\n" +
            "\n%RUN% -b \""+ tcf_file + "\""
            "\npause")
    f.close()

    # Run TUFLOW
    print("Running TUFLOW")
    #subprocess.call('.\\runs\\'+case_name+'_run_'+ Q_num + '_TUFLOW.bat')
    bat_file = '.\\runs\\'+case_name+'_run_'+ Q_num + '_TUFLOW.bat'
    p = subprocess.Popen(bat_file, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    print(case_name+'_'+Q_num+" complete")

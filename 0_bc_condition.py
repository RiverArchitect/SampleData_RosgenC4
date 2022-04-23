#############################################################################################

import os
import shutil as sl
import numpy as np
import pandas as pd

cases = ['VanillaC4', 'InphaseC4', 'OutphaseC4']
Q_all = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 30, 40, 50, 60, 70, 80, 90, 100])

Q_stage = []
default_dir = os.getcwd()
for case in cases:
    working_dir = os.path.join(default_dir, "RosgenC4_"+ case)
    #Q_stage.append(case)
    for ii in range(0,Q_all.__len__()):
        zero1 = ''
        s = str(ii+1)
        s_len = s.__len__()

        for ind in range(0,3-s_len):
            zero1 = zero1 + '0'
        Q_num = zero1 + s

        bc_file = working_dir + '\\bc_dbase\\'+case+'_bc_data_'+Q_num+'.csv'
        bc = pd.read_csv(bc_file)

        Q_stage.append([case, bc["RPin"][0], bc["RPout"][0]])


Q_s = pd.DataFrame(Q_stage, columns = ['Case','Q_cms','Stage_m'])

Q_s.to_csv('out.csv', index=False)
import os
import simpledbf
import arcpy
import _thread
import matplotlib.pyplot as plt
import numpy as np

def mannings_Qfromh_upstream(path_up_xsect, path_terrain, water_stage, n, S0, Execute_StackProfile_3d, figure_xsect):
    # This python script calculate the water stage at the downstream
    # The required inputs are:
    #   NAME                    - the string that corresponds with the TUFLOW run name from main script
    #   water_stage             - the water stage at the xsect interested (e.g. 1st riffle-crest)
    #   n                       - manning's n
    #   S0                      - Slope of the channel
    #   Execute_StackProfile_3d - 1 if you need to generate xsect profile in xlsx
    #   figure_xsect            - 1 if you want to see the xsect profile and water stage
    #
    # The output is:
    #   Q                       - Calculated discharge for the site

    # path to upstream xsect shp file
    xsectshp1 = path_up_xsect

    # Load Raster DEM
    terrain = path_terrain

    # Define projection
    dsc = arcpy.Describe(xsectshp1)
    coord_sys = dsc.spatialReference
    arcpy.DefineProjection_management(terrain, coord_sys)

    # Stack Profile
    # upstream: at the first riffle-crest
    xsecttab1 = './input_folder_orig/xsect/2d_xsect_' + NAME + '_table_upstream.dbf'

    if Execute_StackProfile_3d:
        if not (os.path.isfile(xsectshp1)):
            print(xsectshp1 + ' is not found. Please create a polyline in arcGIS and save it in this location.')
            _thread.interrupt_main()
        #    _thread.interrupt_main()

        if os.path.isfile(xsecttab1):
            os.remove(xsecttab1)

        # Execute Stack Profile
        arcpy.CheckOutExtension("3D")
        arcpy.StackProfile_3d(xsectshp1, profile_targets=[terrain], out_table=xsecttab1)

    xsectdbf1 = simpledbf.Dbf5(xsecttab1)
    xsectdfst1 = xsectdbf1.to_dataframe()
    xsectdf1 = xsectdfst1


    # Construct a functional relationship between A and h
    x = np.array(xsectdf1['FIRST_DIST'])
    z = np.array(xsectdf1['FIRST_Z'])
    z0 = z - water_stage
    ind = []

    for ii in range(0,z.__len__()-1):
        if np.sign(z0[ii]*z0[ii+1]) < 0:
            ind.append(ii)
    A = 0
    P = 0

    for ii in range(0, ind.__len__(), 2):

        m1 = (z0[ind[ii]] - z0[ind[ii] + 1]) / (x[ind[ii]] - x[ind[ii] + 1])
        xi1 = (-z0[ind[ii]] + m1 * x[ind[ii]]) / m1

        m2 = (z0[ind[ii+1]] - z0[ind[ii+1] + 1]) / (x[ind[ii+1]] - x[ind[ii+1] + 1])
        xi2 = (-z0[ind[ii+1]] + m2 * x[ind[ii+1]]) / m2

        X = np.hstack((xi1, x[ind[ii] + 1:ind[ii+1]], xi2))
        Z = -np.hstack((0, z0[ind[ii] + 1:ind[ii+1]], 0))
        dA = np.trapz(Z, x=X)
        dx = X[1:] - X[:-1]
        dz = Z[1:] - Z[:-1]
        dP = np.sum((dx ** 2 + dz ** 2) ** (1 / 2))
        print('dA='+str(dA))
        A = A + dA
        P = P + dP

    R = A/P
    Q = (1/n)*A*R**(2/3)*(S0)**(1/2)

    if figure_xsect == 1:

        # Figure, at the first riffle-crest
        plt.figure(1)
        plt.plot(x, z, '-')
        plt.plot([np.min(x), np.max(x)], [water_stage, water_stage], '-')
        plt.xlabel('Lateral Distance (m)')
        plt.ylabel('Elevation (m)')
        plt.title('Cross-sectional profile at the upstream')
        plt.show()

    return Q, A, P, R

import os
import simpledbf
import arcpy
import _thread
import matplotlib.pyplot as plt
import numpy as np

def mannings_hfromQ_downstream(path_down_xsect, path_terrain, path_figure, Q, n, S0, Execute_StackProfile_3d, figure_xsect):
    # This python script calculate the water stage at the downstream
    # The required inputs are:
    #   NAME                    - the string that corresponds with the TUFLOW run name from main script
    #   Q                       - discharge
    #   n                       - manning's n
    #   S0                      - Slope of the channel
    #   Execute_StackProfile_3d - 1 if you need to generate xsect profile in xlsx
    #   figure_xsect            - 1 if you want to see the xsect profile and water stage
    #
    # The output is:
    #   h                       - Calculated water stage at the downstream

    ## path to downstream xsect shp file
    xsectshp2 = path_down_xsect

    # Load Raster DEM
    terrain = path_terrain

    # Define projection
    dsc = arcpy.Describe(xsectshp2)
    coord_sys = dsc.spatialReference
    arcpy.DefineProjection_management(terrain, coord_sys)

    # Stack Profile
    # downstream: at the outlet
    xsecttab2 = './bc_dbase/table_downstream.dbf'

    if Execute_StackProfile_3d:

        if not (os.path.isfile(xsectshp2)):
            print(xsectshp2 + ' is not found. Please create a polyline in arcGIS and save it in this location.')
            _thread.interrupt_main()

        if os.path.isfile(xsecttab2):
            os.remove(xsecttab2)

        # Execute Stack Profile
        arcpy.CheckOutExtension("3D")
        arcpy.StackProfile_3d(xsectshp2, profile_targets=[terrain], out_table=xsecttab2)

    xsectdbf2 = simpledbf.Dbf5(xsecttab2)
    xsectdfst2 = xsectdbf2.to_dataframe()
    xsectdf2 = xsectdfst2


    # Construct a functional relationship between A and h
    x = np.array(xsectdf2['FIRST_DIST'])
    z = np.array(xsectdf2['FIRST_Z'])
    h0 = (np.max(z)+np.min(z))/2
    tol = 0.001
    jj = 0
    J = 1
    maxIter = 1000

    while np.abs(J) > tol:
        ind = []
        z0 = z - h0
        for ii in range(0,z.__len__()-1):
            if np.sign(z0[ii]*z0[ii+1]) < 0:
                ind.append(ii)
        A = 0
        P = 0

        print(ind)
        for ii in range(0, ind.__len__(), 2):

            m1 = (z0[ind[ii]] - z0[ind[ii] + 1]) / (x[ind[ii]] - x[ind[ii] + 1])
            xi1 = (-z0[ind[ii]] + m1 * x[ind[ii]]) / m1

            m2 = (z0[ind[ii + 1]] - z0[ind[ii + 1] + 1]) / (x[ind[ii + 1]] - x[ind[ii + 1] + 1])
            xi2 = (-z0[ind[ii + 1]] + m2 * x[ind[ii + 1]]) / m2

            X = np.hstack((xi1, x[ind[ii] + 1:ind[ii + 1]], xi2))
            Z = -np.hstack((0, z0[ind[ii] + 1:ind[ii + 1]], 0))
            dA = np.trapz(Z, x=X)
            dx = X[1:] - X[:-1]
            dz = Z[1:] - Z[:-1]
            dP = np.sum((dx ** 2 + dz ** 2) ** (1 / 2))

            A = A + dA
            P = P + dP

        R = A/P
        J_curr = (1/n)*A*R**(2/3)*(S0)**(1/2) - Q

        if jj == 0:
            h0_curr = h0
            J = J_curr
            h0_new = h0 + 0.01
        else:
            if jj > maxIter:
                tol = 0.1
            h0_curr = h0
            J = J_curr
            dJdh = (J_curr-J_pre)/(h0_curr-h0_pre)
            h0_new = h0_curr-(J_curr)/dJdh

            if h0_new > np.max(z):
                print('Calculated WSE is higher than the maximum bed elevation. Abort')
                os.abort()

        h0 = h0_new
        h0_pre = h0_curr
        J_pre = J_curr

        jj = jj + 1

    print('error =  ', str(J))
    if figure_xsect == 1:
        # Figure, at the downstream outlet
        plt.figure(3)
        plt.plot(x, z, '-')
        plt.plot([np.min(x), np.max(x)], [h0, h0], '-')
        #plt.plot([xi1, xi2], [h0, h0], '*')
        plt.xlabel('Lateral Distance (m)')
        plt.ylabel('Elevation (m)')
        plt.title('Cross-sectional profile at the downstream,\n Q='+str(round(Q,2))+
                  ' m3/s, h='+str(round(h0,2))+' m')
        plt.savefig(path_figure)
        plt.close(3)
    h = h0
    print('final h = ' + str(h))
    return h, A, P, R
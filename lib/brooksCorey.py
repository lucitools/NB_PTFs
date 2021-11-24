import arcpy
import os
import sys
import csv

from NB_PTFs.lib.external import six # Python 2/3 compatibility module
import configuration
import NB_PTFs.lib.log as log
import NB_PTFs.lib.common as common

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log, common])

def calcBrooksCoreyFXN(pressure, hb_BC, theta_r, theta_s, lambda_BC):

    # log.info('DEBUG: pressure: ' + str(pressure))
    # log.info('DEBUG: hb_BC: ' + str(hb_BC))
    # log.info('DEBUG: theta_r: ' + str(theta_r))
    # log.info('DEBUG: theta_s: ' + str(theta_s))
    # log.info('DEBUG: lambda_BC: ' + str(lambda_BC))

    bcArray = []

    for i in range(0, len(pressure)):

        pressureVal = pressure[i]

        # Calculate the WC @ pressure using Brooks-Corey
        if pressure[i] < hb_BC:
            # if pressure is less than to hb_BC
            bc_WC = theta_s
            bcArray.append(bc_WC)

        else:
            # if pressure is greater than hb_BC
            # bc_WC = theta_r + (((theta_s - theta_r) * (hb_BC ** lambda_BC)) / (pressure[i] ** lambda_BC))
            
            # if pressure is greater than hb_BC
            # bc_WC = theta_r + ((theta_s - theta_r) * (hb_BC / float(pressureVal)) ** lambda_BC)
            # bc_WC = theta_r + (theta_s - theta_r) * (hb_BC / float(pressureVal) ** lambda_BC)

            bc_WC = theta_r + (theta_s - theta_r) * (hb_BC / float(pressureVal)) ** lambda_BC

            bcArray.append(bc_WC)

    return bcArray

def writeBCParams(outputShp, warning, WC_res, WC_sat, lambda_BC, hb_BC):

    # Write BC Params to shapefile

    # Add fields
    arcpy.AddField_management(outputShp, "warning", "TEXT")
    arcpy.AddField_management(outputShp, "WC_res", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_sat_BC", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "lambda_BC", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "hb_BC", "DOUBLE", 10, 6)

    outputFields = ["warning", "WC_res", "WC_sat_BC", "lambda_BC", "hb_BC"]

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
        for row in cursor:
            row[0] = warning[recordNum]
            row[1] = WC_res[recordNum]
            row[2] = WC_sat[recordNum]
            row[3] = lambda_BC[recordNum]
            row[4] = hb_BC[recordNum]

            cursor.updateRow(row)
            recordNum += 1

def plotBrooksCorey(outputFolder, WC_resArray, WC_satArray, hbArray, lambdaArray, nameArray, fcValue, sicValue, pwpValue):
    # Create Brooks-Corey plots
    import matplotlib.pyplot as plt
    import numpy as np

    # Check what unit the user wants to output
    PTFUnit = common.getInputValue(outputFolder, 'Pressure_units_plot')

    # Check what axis was chosen
    AxisChoice = common.getInputValue(outputFolder, 'Plot_axis')

    # Check for any soils that we were not able to calculate BC parameters for    
    errors = []
    for i in range(0, len(lambdaArray)):
        if lambdaArray[i] == -9999:
            log.warning('Invalid lambda found for ' + str(nameArray[i]))
            errors.append(i)

    # Define output folder for CSVs
    outFolder = os.path.join(outputFolder, 'BC_waterContents')
    if not os.path.exists(outFolder):
        os.mkdir(outFolder)

    ################################
    ### Plot 0: individual plots ###
    ################################

    # Plot 0: pressure on the y-axis and water content on the x-axis
    for i in [x for x in range(0, len(nameArray)) if x not in errors]:

        outName = 'bc_' + str(nameArray[i]) + '.png'
        outPath = os.path.join(outputFolder, outName)
        title = 'Brooks-Corey plot for ' + str(nameArray[i])

        # Set pressure vector
        psi_kPa = np.linspace(0.0, 1500.0, 1501)

        # Calculate WC over that pressure vector
        bc_WC = calcBrooksCoreyFXN(psi_kPa, hbArray[i], WC_resArray[i], WC_satArray[i], lambdaArray[i])
        
        common.writeWCCSV(outFolder, nameArray[i], psi_kPa, bc_WC, 'Pressures_kPa', 'WaterContents')

        ## Figure out what to do about multipliers
        if PTFUnit == 'kPa':
            pressureUnit = 'kPa'
            psi_plot = psi_kPa

            fc_plot = float(fcValue) * -1.0
            sic_plot = float(sicValue) * -1.0
            pwp_plot = float(pwpValue) * -1.0

        elif PTFUnit == 'cm':
            pressureUnit = 'cm'
            psi_plot = 10.0 * psi_kPa

            fc_plot = float(fcValue) * -10.0
            sic_plot = float(sicValue) * -10.0
            pwp_plot = float(pwpValue) * -10.0

        elif PTFUnit == 'm':
            pressureUnit = 'm'
            psi_plot = 0.1 * psi_kPa

            fc_plot = float(fcValue) * -0.1
            sic_plot = float(sicValue) * -0.1
            pwp_plot = float(pwpValue) * -0.1

        # Convert psi_plot to negative for plotting
        psi_neg = -1.0 * psi_plot

        if AxisChoice == 'Y-axis':
            plt.plot(psi_neg, bc_WC, label=str(nameArray[i]))        
            plt.xscale('symlog')
            plt.axvline(x=fc_plot, color='g', linestyle='dashed', label='FC')
            plt.axvline(x=sic_plot, color='m', linestyle='dashed', label='SIC')
            plt.axvline(x=pwp_plot, color='r', linestyle='dashed', label='PWP')
            plt.legend(loc="best")
            plt.title(title)
            plt.xlabel('Pressure (' + str(pressureUnit) + ')')
            plt.ylabel('Volumetric water content')
            plt.savefig(outPath, transparent=False)
            plt.close()
            log.info('Plot created for soil ' + str(nameArray[i]))

        elif AxisChoice == 'X-axis':
            plt.plot(bc_WC, psi_neg, label=str(nameArray[i]))        
            plt.yscale('symlog')
            plt.axhline(y=fc_plot, color='g', linestyle='dashed', label='FC')
            plt.axhline(y=sic_plot, color='m', linestyle='dashed', label='SIC')
            plt.axhline(y=pwp_plot, color='r', linestyle='dashed', label='PWP')
            plt.legend(loc="best")
            plt.title(title)
            plt.ylabel('Pressure (' + str(pressureUnit) + ')')
            plt.xlabel('Volumetric water content')
            plt.savefig(outPath, transparent=False)
            plt.close()
            log.info('Plot created for soil ' + str(nameArray[i]))

        else:
            log.error('Invalid choice for axis plotting, please select Y-axis or X-axis')
            sys.exit()

    #########################
    ### Plot 1: all soils ###
    #########################

    outPath = os.path.join(outputFolder, 'plotBC_logPressure.png')
    title = 'Brooks-Corey plots of ' + str(len(nameArray)) + ' soils (log scale)'

    # Define pressure vector 
    psi_kPa = np.linspace(0.0, 1500.0, 1501)

    for i in [x for x in range(0, len(nameArray)) if x not in errors]:

        # Calculate WC over pressure vector 
        bc_WC = calcBrooksCoreyFXN(psi_kPa, hbArray[i], WC_resArray[i], WC_satArray[i], lambdaArray[i])
        
        if PTFUnit == 'kPa':
            pressureUnit = 'kPa'
            psi_plot = psi_kPa

        elif PTFUnit == 'cm':
            pressureUnit = 'cm'
            psi_plot = 10.0 * psi_kPa

        elif PTFUnit == 'm':
            pressureUnit = 'm'
            psi_plot = 0.1 * psi_kPa

        # Convert psi to negative for plotting purposes
        psi_neg = -1.0 * psi_plot

        plt.plot(psi_neg, bc_WC, label=str(nameArray[i]))
    
    if AxisChoice == 'Y-axis':
        plt.xscale('symlog')
        plt.title(title)
        plt.axvline(x=fc_plot, color='g', linestyle='dashed', label='FC')
        plt.axvline(x=sic_plot, color='m', linestyle='dashed', label='SIC')
        plt.axvline(x=pwp_plot, color='r', linestyle='dashed', label='PWP')
        plt.ylabel('Water content')
        plt.xlabel('Pressure (' + str(pressureUnit) + ')')
        plt.legend(ncol=2, fontsize=12, loc="best")
        plt.savefig(outPath, transparent=False)
        plt.close()
        log.info('Plot created with water content on the y-axis')

    elif AxisChoice == 'X-axis':
        plt.yscale('symlog')
        plt.title(title)
        plt.axhline(y=fc_plot, color='g', linestyle='dashed', label='FC')
        plt.axhline(y=sic_plot, color='m', linestyle='dashed', label='SIC')
        plt.axhline(y=pwp_plot, color='r', linestyle='dashed', label='PWP')
        plt.xlabel('Water content')
        plt.ylabel('Pressure (' + str(pressureUnit) + ')')
        plt.legend(ncol=2, fontsize=12, loc="best")
        plt.savefig(outPath, transparent=False)
        plt.close()
        log.info('Plot created with water content on the y-axis')

    else:
        log.error('Invalid choice for axis plotting, please select Y-axis or X-axis')
        sys.exit()
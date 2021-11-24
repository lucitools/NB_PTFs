import arcpy
import os
import sys
import csv

from NB_PTFs.lib.external import six # Python 2/3 compatibility module
import configuration
import NB_PTFs.lib.log as log
import NB_PTFs.lib.common as common
import NB_PTFs.lib.PTFdatabase as PTFdatabase

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log, common, PTFdatabase])

def calcVGfxn(pressure, theta_res, theta_sat, alpha, n, m):
    
    # Function to calculate the water content at a given pressure
    # or vector/range of pressures
    # Pressure is being taken in internally as kPa

    vg_WC = theta_res + ((theta_sat - theta_res) / ((1.0 + ((alpha * pressure) ** n))) ** m)

    # Return WC    
    return vg_WC

def calcMVGfxn(pressure, K_sat, alpha, n, m, l):

    # Calculate Mualem-van Genuchten

    # Calc Se
    Se_MVG = 1.0 / float((1.0 + (alpha * pressure) ** n) ** m)

    # Calc K_Se
    K_Se_MVG = K_sat * Se_MVG ** l * (1.0 - (1.0 - Se_MVG ** (1.0 / m)) ** m) ** 2.0

    return Se_MVG, K_Se_MVG

def calcKhfxn(pressure, K_sat, alpha, n, m, l):

    # Calculate K(h)
    Kh = K_sat * (((((1.0 + (alpha * pressure)**n)**m) - (alpha * pressure)**(n - 1.0))**2.0) / (((1.0 + (alpha * pressure)**n))**(m * (l + 2.0))))

    return Kh

def calcthetaHKfxn(pressure, WC_res, WC_sat, alpha, n, m, K_sat, l):

    # Calculate thetaH and Ktheta for MVG
    thetaH = calcVGfxn(pressure, WC_res, WC_sat, alpha, n, m)            
    Ktheta = K_sat * (((thetaH - WC_res) / float(WC_sat - WC_res))**l) * (1.0 - (1.0 - ((thetaH - WC_res) / float(WC_sat - WC_res))**(1.0/m))**m)**2.0
            
    return thetaH, Ktheta

def writeVGParams(outputShp, WC_residualArray, WC_satArray, alpha_VGArray, n_VGArray, m_VGArray):
    # Write VG parameters to the shapefile

    # Add fields
    arcpy.AddField_management(outputShp, "WC_res", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_sat", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "alpha_VG", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "n_VG", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "m_VG", "DOUBLE", 10, 6)

    outputFields = ["WC_res", "WC_sat", "alpha_VG", "n_VG", "m_VG"]

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
        for row in cursor:
            row[0] = WC_residualArray[recordNum]
            row[1] = WC_satArray[recordNum]
            row[2] = alpha_VGArray[recordNum]
            row[3] = n_VGArray[recordNum]
            row[4] = m_VGArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

def plotVG(outputFolder, WC_residualArray,
           WC_satArray, alpha_VGArray, n_VGArray,
           m_VGArray, nameArray, fcValue, sicValue, pwpValue):
    
    # Create Van Genuchten plots
    import matplotlib.pyplot as plt
    import numpy as np

    # Check what unit the user wants to output
    PTFUnit = common.getInputValue(outputFolder, 'Pressure_units_plot')

    # Check what axis was chosen
    AxisChoice = common.getInputValue(outputFolder, 'Plot_axis')

    if PTFUnit == 'kPa':
        pressureUnit = 'kPa'
        alphaMult = 1.0        

    elif PTFUnit == 'cm':
        pressureUnit = 'cm'
        alphaMult = 0.1

    elif PTFUnit == 'm':
        pressureUnit = 'm'
        alphaMult = 10.0

    else:
        log.error('Pressure unit for PTF not recognised')

    # Define output folder for CSVs
    outFolder = os.path.join(outputFolder, 'VG_waterContents')
    if not os.path.exists(outFolder):
        os.mkdir(outFolder)

    # Plot 1: pressure on the x-axis and water content on the y-axis
    for i in range(0, len(nameArray)):
        outName = 'vg_' + str(nameArray[i]) + '.png'
        outPath = os.path.join(outputFolder, outName)
        title = 'Van Genuchten plot for ' + str(nameArray[i])

        # Set pressure vector
        psi_kPa = np.linspace(0.0, 1500.0, 1501)

        # Calculate WC over the pressure vector above
        vg_WC = calcVGfxn(psi_kPa, WC_residualArray[i], WC_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i])

        common.writeWCCSV(outFolder, nameArray[i], psi_kPa, vg_WC, 'Pressures_kPa', 'WaterContents')

        # For plotting purposes, adjust psi_plot based on user-input
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

        # Call check for theta at 0 vs theta_sat + 1%        
        theta_0kPa = calcVGfxn(0, WC_residualArray[i], WC_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i])
        theta_sat_threshold = WC_satArray[i] * 1.1

        if theta_0kPa > theta_sat_threshold:
            log.warning('Water content at 0kPa is larger than theta(saturation) + 1 percent')

        # Limits ased on the WCsat and 1500kPa of the curve
        theta_1500kPa = calcVGfxn(1500, WC_residualArray[i], WC_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i])
        wcBottom = max(theta_1500kPa - 0.01, 0)
        wcTop = min(WC_satArray[i] + 0.1, 1)

        # Convert psi_plot to negative for plotting
        psi_neg = -1.0 * psi_plot

        if AxisChoice == 'Y-axis':
            # Plotting
            plt.plot(psi_neg, vg_WC, label=str(nameArray[i]))
            plt.xscale('symlog')
            plt.axvline(x=fc_plot, color='g', linestyle='dashed', label='FC')
            plt.axvline(x=sic_plot, color='m', linestyle='dashed', label='SIC')
            plt.axvline(x=pwp_plot, color='r', linestyle='dashed', label='PWP')
            plt.xlabel('Pressure (' + str(pressureUnit) + ')')
            plt.ylabel('Volumetric water content')
            plt.ylim([wcBottom, wcTop])
            plt.title(title)
            plt.legend(loc="best")
            plt.savefig(outPath, transparent=False)
            plt.close()
            log.info('Plot created for soil ' + str(nameArray[i]))

        elif AxisChoice == 'X-axis':
            plt.plot(vg_WC, psi_neg, label=str(nameArray[i]))
            plt.yscale('symlog')
            plt.axhline(y=fc_plot, color='g', linestyle='dashed', label='FC')
            plt.axhline(y=sic_plot, color='m', linestyle='dashed', label='SIC')
            plt.axhline(y=pwp_plot, color='r', linestyle='dashed', label='PWP')
            plt.ylabel('Pressure (' + str(pressureUnit) + ')')
            plt.xlabel('Volumetric water content')
            plt.xlim([wcBottom, wcTop])
            plt.title(title)
            plt.legend(loc="best")
            plt.savefig(outPath, transparent=False)
            plt.close()
            log.info('Plot created for soil ' + str(nameArray[i]))

        else:
            log.error('Invalid choice for axis plotting, please select Y-axis or X-axis')
            sys.exit()

    # Plot 2: log pressure on the x-axis, WC on the y-axis
    outPath = os.path.join(outputFolder, 'plotVG_logPressure.png')
    title = 'Van Genuchten plots of ' + str(len(nameArray)) + ' soils (log scale)'

    # Define pressure vector 
    psi_kPa = np.linspace(0.0, 1500.0, 1501)

    labels = []
    for i in range(0, len(nameArray)):

        # Calculate WC 
        vg_WC = calcVGfxn(psi_kPa, WC_residualArray[i], WC_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i])
        
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

        if AxisChoice == 'Y-axis':
            plt.plot(psi_neg, vg_WC, label=str(nameArray[i]))

        elif AxisChoice == 'X-axis':
            plt.plot(vg_WC, psi_neg, label=str(nameArray[i]))

        else:
            log.error('Invalid choice for axis plotting, please select Y-axis or X-axis')
            sys.exit()
    
    if AxisChoice == 'Y-axis':
        plt.xscale('symlog')
        plt.axvline(x=fc_plot, color='g', linestyle='dashed', label='FC')
        plt.axvline(x=sic_plot, color='m', linestyle='dashed', label='SIC')
        plt.axvline(x=pwp_plot, color='r', linestyle='dashed', label='PWP')
        plt.title(title)
        plt.ylabel('Water content')
        plt.xlabel('Pressure (' + str(pressureUnit) + ')')
        plt.legend(ncol=2, fontsize=12, loc="best")
        plt.savefig(outPath, transparent=False)
        plt.close()
        log.info('Plot created with water content on the y-axis')

    elif AxisChoice == 'X-axis':
        plt.yscale('symlog')
        plt.axhline(y=fc_plot, color='g', linestyle='dashed', label='FC')
        plt.axhline(y=sic_plot, color='m', linestyle='dashed', label='SIC')
        plt.axhline(y=pwp_plot, color='r', linestyle='dashed', label='PWP')
        plt.title(title)
        plt.xlabel('Water content')
        plt.ylabel('Pressure (' + str(pressureUnit) + ')')
        plt.legend(ncol=2, fontsize=12, loc="best")
        plt.savefig(outPath, transparent=False)
        plt.close()
        log.info('Plot created with water content on the x-axis')

    else:
        log.error('Invalid choice for axis plotting, please select Y-axis or X-axis')
        sys.exit()

    # Plot 3: pressure on the x-axis, WC on the y-axis
    outPath = os.path.join(outputFolder, 'plotVG_Pressure.png')
    title = 'Van Genuchten plots of ' + str(len(nameArray)) + ' soils'

    # Define pressure vector 
    psi_kPa = np.linspace(0.0, 1500.0, 1501)

    labels = []
    for i in range(0, len(nameArray)):

        # Calculate WC 
        vg_WC = calcVGfxn(psi_kPa, WC_residualArray[i], WC_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i])
        
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

        if AxisChoice == 'Y-axis':
            plt.plot(psi_neg, vg_WC, label=str(nameArray[i]))

        elif AxisChoice == 'X-axis':
            plt.plot(vg_WC, psi_neg, label=str(nameArray[i]))

        else:
            log.error('Invalid choice for axis plotting, please select Y-axis or X-axis')
            sys.exit()
    
    if AxisChoice == 'Y-axis':
    
        plt.axvline(x=fc_plot, color='g', linestyle='dashed', label='FC')
        plt.axvline(x=sic_plot, color='m', linestyle='dashed', label='SIC')
        plt.axvline(x=pwp_plot, color='r', linestyle='dashed', label='PWP')
        plt.title(title)
        plt.ylabel('Water content')
        plt.xlabel('Pressure (' + str(pressureUnit) + ')')
        plt.legend(ncol=2, fontsize=12, loc="best")
        plt.savefig(outPath, transparent=False)
        plt.close()
        log.info('Plot created with water content on the y-axis')

    elif AxisChoice == 'X-axis':
        plt.axhline(y=fc_plot, color='g', linestyle='dashed', label='FC')
        plt.axhline(y=sic_plot, color='m', linestyle='dashed', label='SIC')
        plt.axhline(y=pwp_plot, color='r', linestyle='dashed', label='PWP')
        plt.title(title)
        plt.xlabel('Water content')
        plt.ylabel('Pressure (' + str(pressureUnit) + ')')
        plt.legend(ncol=2, fontsize=12, loc="best")
        plt.savefig(outPath, transparent=False)
        plt.close()
        log.info('Plot created with water content on the x-axis')

    else:
        log.error('Invalid choice for axis plotting, please select Y-axis or X-axis')
        sys.exit()
    
def calcPressuresVG(name, WC_residual, WC_sat, alpha_VG, n_VG, m_VG, vgPressures):

    # Calculates water content at user-input pressures
    wcValues = [name]

    for pressure in vgPressures:

        waterContent = calcVGfxn(pressure, WC_residual, WC_sat, alpha_VG, n_VG, m_VG)
        wcValues.append(waterContent)

    return wcValues

def writeWaterContent(outputFolder, record, headings, wcArrays):

    outCSV = os.path.join(outputFolder, 'WaterContent.csv')

    with open(outCSV, 'wb') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headings)

        for i in range(0, len(record)):
            row = wcArrays[i]
            writer.writerow(row)

        msg = 'Output CSV with water content saved to: ' + str(outCSV)
        log.info(msg)

    csv_file.close()

def calcMVG(K_sat, alpha_VG, n_VG, m_VG, l_MvG):

    # Initialise empty arrays
    Se_1kPaArray = []
    Se_3kPaArray = []
    Se_10kPaArray = []
    Se_33kPaArray = []
    Se_100kPaArray = []
    Se_1500kPaArray = []

    K_Se_1kPaArray = []
    K_Se_3kPaArray = []
    K_Se_10kPaArray = []
    K_Se_33kPaArray = []
    K_Se_100kPaArray = []
    K_Se_1500kPaArray = []
    
    for x in range(0, len(alpha_VG)):

        # Calculate Se and K_Se at different pressures
        Se_1kPa, K_Se_1kPa = calcMVGfxn(1.0, K_sat[x], alpha_VG[x], n_VG[x], m_VG[x], l_MvG[x])
        Se_3kPa, K_Se_3kPa = calcMVGfxn(3.0, K_sat[x], alpha_VG[x], n_VG[x], m_VG[x], l_MvG[x])
        Se_10kPa, K_Se_10kPa = calcMVGfxn(10.0, K_sat[x], alpha_VG[x], n_VG[x], m_VG[x], l_MvG[x])
        Se_33kPa, K_Se_33kPa = calcMVGfxn(33.0, K_sat[x], alpha_VG[x], n_VG[x], m_VG[x], l_MvG[x])
        Se_100kPa, K_Se_100kPa = calcMVGfxn(100.0, K_sat[x], alpha_VG[x], n_VG[x], m_VG[x], l_MvG[x])
        Se_1500kPa, K_Se_1500kPa = calcMVGfxn(1500.0, K_sat[x], alpha_VG[x], n_VG[x], m_VG[x], l_MvG[x])

        Se_1kPaArray.append(Se_1kPa)
        Se_3kPaArray.append(Se_3kPa)
        Se_10kPaArray.append(Se_10kPa)
        Se_33kPaArray.append(Se_33kPa)
        Se_100kPaArray.append(Se_100kPa)
        Se_1500kPaArray.append(Se_1500kPa)

        K_Se_1kPaArray.append(K_Se_1kPa)
        K_Se_3kPaArray.append(K_Se_3kPa)
        K_Se_10kPaArray.append(K_Se_10kPa)
        K_Se_33kPaArray.append(K_Se_33kPa)
        K_Se_100kPaArray.append(K_Se_100kPa)
        K_Se_1500kPaArray.append(K_Se_1500kPa)

    return Se_1kPaArray, Se_3kPaArray, Se_10kPaArray, Se_33kPaArray, Se_100kPaArray, Se_1500kPaArray, K_Se_1kPaArray, K_Se_3kPaArray, K_Se_10kPaArray, K_Se_33kPaArray, K_Se_100kPaArray, K_Se_1500kPaArray

def writeOutputMVG(outputShp, Se_1kPaArray, Se_3kPaArray, Se_10kPaArray, Se_33kPaArray, Se_100kPaArray, Se_1500kPaArray, K_Se_1kPaArray, K_Se_3kPaArray, K_Se_10kPaArray, K_Se_33kPaArray, K_Se_100kPaArray, K_Se_1500kPaArray):
    # Write the outputs to the output shapefile

    # Add fields
    arcpy.AddField_management(outputShp, "Se1kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "Se3kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "Se10kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "Se33kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "Se100kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "Se1500kPa", "DOUBLE", 10, 6)

    arcpy.AddField_management(outputShp, "KSe1kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "KSe3kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "KSe10kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "KSe33kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "KSe100kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "KSe1500kPa", "DOUBLE", 10, 6)

    outputFields = ["Se1kPa", "Se3kPa", "Se10kPa", "Se33kPa", "Se100kPa", "Se1500kPa", "KSe1kPa", "KSe3kPa", "KSe10kPa", "KSe33kPa", "KSe100kPa", "KSe1500kPa"]

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
        for row in cursor:
            row[0] = Se_1kPaArray[recordNum]
            row[1] = Se_3kPaArray[recordNum]
            row[2] = Se_10kPaArray[recordNum]
            row[3] = Se_33kPaArray[recordNum]
            row[4] = Se_100kPaArray[recordNum]
            row[5] = Se_1500kPaArray[recordNum]
            row[6] = K_Se_1kPaArray[recordNum]
            row[7] = K_Se_3kPaArray[recordNum]
            row[8] = K_Se_10kPaArray[recordNum]
            row[9] = K_Se_33kPaArray[recordNum]
            row[10] = K_Se_100kPaArray[recordNum]
            row[11] = K_Se_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

def plotMVG(outputFolder, K_satArray, alpha_VGArray, n_VGArray, m_VGArray, l_MvGArray, WC_satArray, WC_residualArray, nameArray):
    # Create Van Genuchten plots
    import matplotlib.pyplot as plt
    import numpy as np

    # Check what axis was chosen
    AxisChoice = common.getInputValue(outputFolder, 'Plot_axis')

    # Define output folder for CSVs
    outFolder = os.path.join(outputFolder, 'MVG')
    if not os.path.exists(outFolder):
        os.mkdir(outFolder)

    ################################
    ### Plot 0: individual plots ###
    ################################

    # Plot 0: individual plots of K(h) on the y-axis and h on the x-axis
    for i in range(0, len(nameArray)):
        outName = 'MVG_' + str(nameArray[i]) + '.png'
        outPath = os.path.join(outputFolder, outName)
        title = 'Mualem-Van Genuchten plot for ' + str(nameArray[i])

        # h
        h = np.linspace(0.0, 1500.0, 1501)

        # K(h)
        k_h = calcKhfxn(h, K_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i], l_MvGArray[i])
        
        common.writeWCCSV(outFolder, nameArray[i], h, k_h, 'Pressure_kPa', 'Ksat')

        if AxisChoice == 'Y-axis':
            plt.plot(h, k_h, label=str(nameArray[i]))
            plt.legend()
            plt.yscale('log')
            plt.xscale('log')
            plt.title(title)
            plt.xlabel('- kPa')
            plt.ylabel('K(h)')
            plt.savefig(outPath, transparent=False)
            plt.close()
            log.info('MVG plot created for soil ' + str(nameArray[i]))

        elif AxisChoice == 'X-axis':
            plt.plot(k_h, h, label=str(nameArray[i]))
            plt.legend()
            plt.xscale('log')
            plt.yscale('log')
            plt.title(title)
            plt.ylabel('- kPa')
            plt.xlabel('K(h)')
            plt.savefig(outPath, transparent=False)
            plt.close()
            log.info('MVG plot created for soil ' + str(nameArray[i]))

        else:
            log.error('Invalid choice for axis plotting, please select Y-axis or X-axis')
            sys.exit()

    #########################################
    ### Plot 1: one plot with all records ###
    #########################################

    # Plot 1: K(h) on the y-axis, h on the x-axis
    outPath = os.path.join(outputFolder, 'plotMVG.png')
    title = 'Mualem-van Genuchten plots of ' + str(len(nameArray)) + ' soils'

    x = np.linspace(0.0, 1500.0, 1500)
    labels = []
    for i in range(0, len(nameArray)):
        y = calcKhfxn(x, K_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i], l_MvGArray[i])
        
        if AxisChoice == 'Y-axis':
            plt.plot(x, y, label=str(nameArray[i]))

        elif AxisChoice == 'X-axis':
            plt.plot(y, x, label=str(nameArray[i]))
        
        else:
            log.error('Invalid choice for axis plotting, please select Y-axis or X-axis')
            sys.exit()

    if AxisChoice == 'Y-axis':
        plt.yscale('log')
        plt.xscale('log')
        plt.title(title)
        plt.ylabel('k(h)')
        plt.xlabel('- kPa')
        plt.legend(ncol=2, fontsize=12)
        plt.xlim([1, 150000])
        plt.savefig(outPath, transparent=False)
        plt.close()
        log.info('Plot created')

    elif AxisChoice == 'X-axis':
        plt.yscale('log')
        plt.xscale('log')
        plt.title(title)
        plt.xlabel('k(h)')
        plt.ylabel('- kPa')
        plt.legend(ncol=2, fontsize=12)
        plt.ylim([1, 150000])
        plt.savefig(outPath, transparent=False)
        plt.close()
        log.info('Plot created')

    else:
        log.error('Invalid choice for axis plotting, please select Y-axis or X-axis')
        sys.exit()
        
    #########################################
    ### Plot 2: one plot with all records ###
    #########################################

    # Plot 2: k(theta) vs theta(h)
    outPath2 = os.path.join(outputFolder, 'plotMVG_Ktheta.png')
    title = 'Mualem-van Genuchten plots of ' + str(len(nameArray)) + ' soils'

    pressureVal = np.linspace(0.0, 1500.0, 1500)
    for i in range(0, len(nameArray)):
        thetaH, Ktheta = calcthetaHKfxn(pressureVal, WC_residualArray[i], WC_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i], K_satArray[i], l_MvGArray[i])          
        
        if AxisChoice == 'Y-axis':
            plt.plot(thetaH, Ktheta, label=str(nameArray[i]))

        elif AxisChoice == 'X-axis':
            plt.plot(Ktheta, thetaH, label=str(nameArray[i]))

        else:
            log.error('Invalid choice for axis plotting, please select Y-axis or X-axis')
            sys.exit()

    if AxisChoice == 'Y-axis':
        plt.title(title)
        plt.yscale('log')
        plt.ylabel('k(theta)')
        plt.xlabel('theta(h)')
        plt.legend(ncol=2, fontsize=12)
        plt.xlim([0, 1])
        plt.savefig(outPath2, transparent=False)
        plt.close()
        log.info('Plot created')

    elif AxisChoice == 'X-axis':
        plt.title(title)
        plt.xscale('log')
        plt.xlabel('k(theta)')
        plt.ylabel('theta(h)')
        plt.legend(ncol=2, fontsize=12)
        plt.ylim([0, 1])
        plt.savefig(outPath2, transparent=False)
        plt.close()
        log.info('Plot created')

    else:
        log.error('Invalid choice for axis plotting, please select Y-axis or X-axis')
        sys.exit()

    #########################################
    ### Plot 3: one plot with all records ###
    #########################################

    # Plot 3: k(theta) vs h
    outPath3 = os.path.join(outputFolder, 'plotMVG_Ktheta_h.png')
    title = 'Mualem-van Genuchten plots of ' + str(len(nameArray)) + ' soils'

    pressureVal = np.linspace(1.0, 1500.0, 1500)
    for i in range(0, len(nameArray)):
        thetaH, Ktheta = calcthetaHKfxn(pressureVal, WC_residualArray[i], WC_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i], K_satArray[i], l_MvGArray[i])
        
        if AxisChoice == 'Y-axis':
            plt.plot(pressureVal, Ktheta, label=str(nameArray[i]))

        elif AxisChoice == 'X-axis':
            plt.plot(Ktheta, pressureVal, label=str(nameArray[i]))

        else:
            log.error('Invalid choice for axis plotting, please select Y-axis or X-axis')
            sys.exit()

    if AxisChoice == 'Y-axis':
        plt.title(title)
        plt.yscale('log')
        plt.xscale('log')
        plt.ylabel('k(theta)')
        plt.xlabel('h (- cm)')
        plt.legend(ncol=2, fontsize=12)
        plt.xlim([1, 150000])
        plt.savefig(outPath3, transparent=False)
        plt.close()
        log.info('Plot created')

    elif AxisChoice == 'X-axis':
        plt.title(title)
        plt.yscale('log')
        plt.xscale('log')
        plt.xlabel('k(theta)')
        plt.ylabel('h (- cm)')
        plt.legend(ncol=2, fontsize=12)
        plt.ylim([1, 150000])
        plt.savefig(outPath3, transparent=False)
        plt.close()
        log.info('Plot created')

    else:
        log.error('Invalid choice for axis plotting, please select Y-axis or X-axis')
        sys.exit()


def calcPressuresMVG(name, K_sat, alpha_VG, n_VG, m_VG, l_MvG, vgPressures):

    # Calculates K at user-input pressures
    kValues = [name]

    for pressure in vgPressures:
        k_h = calcKhfxn(pressure, K_sat, alpha_VG, n_VG, m_VG, l_MvG)
        kValues.append(k_h)

    return kValues
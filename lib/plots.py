'''
Nature Braid PTFs Database
'''

import sys
import os
import configuration
import numpy as np
import arcpy
import math
import NB_PTFs.lib.log as log
import NB_PTFs.lib.progress as progress
import NB_PTFs.lib.common as common
import NB_PTFs.lib.vanGenuchten as vanGenuchten
import NB_PTFs.lib.thresholds as thresholds
import NB_PTFs.lib.PTFdatabase as PTFdatabase
from NB_PTFs.lib.external import six # Python 2/3 compatibility module

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log, common, vanGenuchten, thresholds, PTFdatabase])

def plotPTF(outputFolder, outputShp, PTFOption, nameArray, results):

    # For plotting point PTFs
    import matplotlib.pyplot as plt
    import numpy as np

    PTFInfo = PTFdatabase.checkPTF(PTFOption)
    PTFPressures = PTFInfo.PTFPressures
    PTFUnit = PTFInfo.PTFUnit

    # Remove warning
    results.pop(0)

    waterContents = []

    # Rearrange arrays
    for j in range(0, len(nameArray)):
        WC = []
        for i in range(0, len(PTFPressures)):
            water = results[i][j]
            WC.append(water)

        waterContents.append(WC)

    # log.info('DEBUG: waterContents: ')
    # log.info(waterContents)

    PTFInfo = PTFdatabase.checkPTF(PTFOption)
    WCheadings = PTFInfo.PTFFields
    WCheadings.pop(0) # remove warning

    for j in range(0, len(waterContents)):
        WC = waterContents[j]

        firstWCName = WCheadings[0]
        firstWCVal = WC[0]

        for i in range(1, len(WC)):
            if WC[i] > firstWCVal:
                log.warning('Water content in field ' + str(WCheadings[i]) + ' is higher than pressure at lowest water content (' + str(firstWCName) + ')')
                log.warning('Check this soil: ' + str(nameArray[j]))

    # Get units for plot
    unitPlots = common.getInputValue(outputFolder, "Pressure_units_plot")
    
    # Get critical thresholds
    fcValue = common.getInputValue(outputFolder, "FieldCapacity")
    sicValue = common.getInputValue(outputFolder, "SIC")
    pwpValue = common.getInputValue(outputFolder, "PWP")

    # Set up pressure vector
    psiArray = np.array(PTFPressures)
    psi_kPa = psiArray.astype(np.float)

    if unitPlots == 'kPa':
        psi_plot = psi_kPa
        fc_plot = float(fcValue) * -1.0
        sic_plot = float(sicValue) * -1.0
        pwp_plot = float(pwpValue) * -1.0
        xLimits = [-1600.0, 0.1]

    elif unitPlots == 'cm':
        psi_plot = 10.0 * psi_kPa
        fc_plot = float(fcValue) * -10.0
        sic_plot = float(sicValue) * -10.0
        pwp_plot = float(pwpValue) * -10.0
        xLimits = [-16000.0, 0.1]

    elif unitPlots == 'm':
        psi_plot = 0.1 * psi_kPa
        fc_plot = float(fcValue) * -0.1
        sic_plot = float(sicValue) * -0.1
        pwp_plot = float(pwpValue) * -0.1
        xLimits = [-160.0, 0.1]

    # Convert psi_plot to negative for plotting purposes
    psi_neg = -1.0 * psi_plot
 
    for i in range(0, len(nameArray)):
        outName = 'pointPTF_'  + str(nameArray[i]) + '.png'
        outPath = os.path.join(outputFolder, outName)
        title = 'Point-PTF plot for ' + str(nameArray[i])

        plt.scatter(psi_neg, waterContents[i], label=str(nameArray[i]), c='b')
        plt.xscale('symlog')
        plt.title(title)
        plt.xlabel('log Pressure (' + str(unitPlots) + ')')
        plt.ylabel('Volumetric water content')
        plt.xlim(xLimits)
        plt.axvline(x=fc_plot, color='g', linestyle='dashed', label='FC')
        plt.axvline(x=sic_plot, color='m', linestyle='dashed', label='SIC')
        plt.axvline(x=pwp_plot, color='r', linestyle='dashed', label='PWP')
        plt.legend(loc="upper left")
        plt.savefig(outPath, transparent=False)
        plt.close()
        log.info('Plot created for soil ' + str(nameArray[i]))


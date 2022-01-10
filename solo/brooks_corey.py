import configuration
import arcpy
import math
import os
import sys
import numpy as np
import csv
import NB_PTFs.lib.log as log
import NB_PTFs.lib.common as common
import NB_PTFs.lib.thresholds as thresholds
import NB_PTFs.lib.PTFdatabase as PTFdatabase
import NB_PTFs.lib.brooksCorey as brooksCorey
import NB_PTFs.lib.bc_PTFs as bc_PTFs
import NB_PTFs.lib.checks_PTFs as checks_PTFs
from NB_PTFs.lib.external import six # Python 2/3 compatibility module

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log, common, thresholds, PTFdatabase, brooksCorey, bc_PTFs, checks_PTFs])

def function(outputFolder, inputShp, PTFOption, BCPressArray, fcVal, sicVal, pwpVal, carbContent, carbonConFactor):

    try:
        # Set temporary variables
        prefix = os.path.join(arcpy.env.scratchGDB, "bc_")

        tempSoils = prefix + "tempSoils"

        # Set output filename
        outputShp = os.path.join(outputFolder, "BrooksCorey.shp")

        # Copy the input shapefile to the output folder
        arcpy.CopyFeatures_management(inputShp, outputShp)

        # Get the nameArray
        nameArray = []
        with arcpy.da.SearchCursor(outputShp, "soilname") as searchCursor:
            for row in searchCursor:
                name = row[0]
                nameArray.append(name)

        # PTFs should return: WC_res, WC_sat, lambda_BC, hb_BC

        if PTFOption == "Cosby_1984_SandC_BC":
            warning, WC_res, WC_sat, lambda_BC, hb_BC = bc_PTFs.Cosby_1984_SandC_BC(outputShp, PTFOption)

        elif PTFOption == "Cosby_1984_SSC_BC":
            warning, WC_res, WC_sat, lambda_BC, hb_BC = bc_PTFs.Cosby_1984_SSC_BC(outputShp, PTFOption)

        elif PTFOption == "RawlsBrakensiek_1985_BC":
            warning, WC_res, WC_sat, lambda_BC, hb_BC = bc_PTFs.RawlsBrakensiek_1985_BC(outputShp, PTFOption)

        elif PTFOption == "CampbellShiozawa_1992_BC":
            warning, WC_res, WC_sat, lambda_BC, hb_BC = bc_PTFs.CampbellShiozawa_1992_BC(outputShp, PTFOption)

        elif PTFOption == "Saxton_1986_BC":
            warning, WC_res, WC_sat, lambda_BC, hb_BC = bc_PTFs.Saxton_1986_BC(outputShp, PTFOption)

        elif PTFOption == "SaxtonRawls_2006_BC":
            warning, WC_res, WC_sat, lambda_BC, hb_BC = bc_PTFs.SaxtonRawls_2006_BC(outputShp, PTFOption, carbonConFactor, carbContent)

        else:
            log.error("Brooks-Corey option not recognised: " + str(PTFOption))
            sys.exit()

        # Write to shapefile
        brooksCorey.writeBCParams(outputShp, warning, WC_res, WC_sat, lambda_BC, hb_BC)

        log.info("Brooks-Corey parameters written to output shapefile")
            
        # Create plots
        brooksCorey.plotBrooksCorey(outputFolder, WC_res, WC_sat, hb_BC, lambda_BC, nameArray, fcVal, sicVal, pwpVal)

        ###############################################
        ### Calculate water content using BC params ###
        ###############################################

        # Check for any soils that we were not able to calculate BC parameters for
        # lambda_BC[i] == -9999
        
        errors = []
        for i in range(0, len(lambda_BC)):
            if lambda_BC[i] == -9999:
                log.warning('Invalid lambda found for ' + str(nameArray[i]))
                errors.append(i)

        # Calculate water content at default pressures
        WC_1kPaArray = []
        WC_3kPaArray = []
        WC_10kPaArray = []
        WC_33kPaArray = []
        WC_100kPaArray = []
        WC_200kPaArray = []
        WC_1000kPaArray = []
        WC_1500kPaArray = []

        for i in range(0, len(nameArray)):

            pressures = [1.0, 3.0, 10.0, 33.0, 100.0, 200.0, 1000.0, 1500.0]

            if lambda_BC[i] != -9999:
                bc_WC = brooksCorey.calcBrooksCoreyFXN(pressures, hb_BC[i], WC_res[i], WC_sat[i], lambda_BC[i])

            else:
                bc_WC = [-9999] * len(pressures)

            WC_1kPaArray.append(bc_WC[0])
            WC_3kPaArray.append(bc_WC[1])
            WC_10kPaArray.append(bc_WC[2])
            WC_33kPaArray.append(bc_WC[3])
            WC_100kPaArray.append(bc_WC[4])
            WC_200kPaArray.append(bc_WC[5])
            WC_1000kPaArray.append(bc_WC[6])
            WC_1500kPaArray.append(bc_WC[7])

        common.writeOutputWC(outputShp, WC_1kPaArray, WC_3kPaArray, WC_10kPaArray, WC_33kPaArray, WC_100kPaArray, WC_200kPaArray, WC_1000kPaArray, WC_1500kPaArray)

        # Write water content at user-input pressures

        # Initialise the pressure head array
        x = np.array(BCPressArray)
        bcPressures = x.astype(np.float)

        # For the headings
        headings = ['Name']

        for pressure in bcPressures:
            headName = 'WC_' + str(pressure) + "kPa"
            headings.append(headName)

        wcHeadings = headings[1:]

        wcArrays = []

        # Calculate soil moisture content at custom VG pressures
        for i in range(0, len(nameArray)):

            if lambda_BC[i] != -9999:
                wcValues = brooksCorey.calcBrooksCoreyFXN(bcPressures, hb_BC[i], WC_res[i], WC_sat[i], lambda_BC[i])
            else:
                wcValues = [-9999] * len(bcPressures)

            wcValues.insert(0, nameArray[i])

            wcArrays.append(wcValues)

        # Write to output CSV
        outCSV = os.path.join(outputFolder, 'WaterContent.csv')

        with open(outCSV, 'w') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headings)

            for i in range(0, len(nameArray)):
                row = wcArrays[i]
                writer.writerow(row)

            msg = 'Output CSV with water content saved to: ' + str(outCSV)
            log.info(msg)

        csv_file.close()

        ##################################################
        ### Calculate water content at critical points ###
        ##################################################

        # Initialise water content arrays
        wc_satCalc = []
        wc_fcCalc = []
        wc_sicCalc = []
        wc_pwpCalc = []

        wc_DW = []
        wc_RAW = []
        wc_NRAW = []
        wc_PAW = []

        wcCriticalPressures = [0.0, fcVal, sicVal, pwpVal]

        for x in range(0, len(nameArray)):

            if lambda_BC[x] != -9999:
                wcCriticals = brooksCorey.calcBrooksCoreyFXN(wcCriticalPressures, hb_BC[x], WC_res[x], WC_sat[x], lambda_BC[x])

                wc_sat = wcCriticals[0]
                wc_fc = wcCriticals[1]
                wc_sic = wcCriticals[2]
                wc_pwp = wcCriticals[3]

                drainWater = wc_sat - wc_fc
                readilyAvailWater = wc_fc - wc_sic
                notRAW = wc_sic - wc_pwp
                PAW = wc_fc - wc_pwp

                checks_PTFs.checkNegValue("Drainable water", drainWater, nameArray[i])
                checks_PTFs.checkNegValue("Readily available water", readilyAvailWater, nameArray[i])
                checks_PTFs.checkNegValue("Not readily available water", notRAW, nameArray[i])
                checks_PTFs.checkNegValue("Not readily available water", PAW, nameArray[i])

            else:
                wc_sat = -9999
                wc_fc = -9999
                wc_sic = -9999
                wc_pwp = -9999
                drainWater = -9999
                readilyAvailWater = -9999
                notRAW = -9999
                PAW = -9999

            wc_satCalc.append(wc_sat)
            wc_fcCalc.append(wc_fc)
            wc_sicCalc.append(wc_sic)
            wc_pwpCalc.append(wc_pwp)
            wc_DW.append(drainWater)
            wc_RAW.append(readilyAvailWater)
            wc_NRAW.append(notRAW)
            wc_PAW.append(PAW)

        common.writeOutputCriticalWC(outputShp, wc_satCalc, wc_fcCalc, wc_sicCalc, wc_pwpCalc, wc_DW, wc_RAW, wc_NRAW, wc_PAW)

    except Exception:
        arcpy.AddError("Brooks-Corey function failed")
        raise

    finally:
        # Remove feature layers from memory
        try:
            for lyr in common.listFeatureLayers(locals()):
                arcpy.Delete_management(locals()[lyr])
                exec(lyr + ' = None') in locals()
        except Exception:
            pass
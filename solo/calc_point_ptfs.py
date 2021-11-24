'''
Function to calculate WC using point-PTFs
'''

import sys
import os
import configuration
import numpy as np
import arcpy
import math
import NB_PTFs.lib.log as log
import NB_PTFs.lib.common as common
import NB_PTFs.lib.point_PTFs as point_PTFs
import NB_PTFs.lib.checks_PTFs as checks_PTFs
import NB_PTFs.lib.plots as plots
from NB_PTFs.lib.external import six # Python 2/3 compatibility module

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log, common, point_PTFs, checks_PTFs, plots])

def function(outputFolder, inputShp, PTFOption, fcVal, sicVal, pwpVal, carbContent, carbonConFactor):

    try:
        # Set temporary variables
        prefix = os.path.join(arcpy.env.scratchGDB, "soil_")

        # Set output filename
        outputShp = os.path.join(outputFolder, "soil_point_ptf.shp")

        # Copy the input shapefile to the output folder
        arcpy.CopyFeatures_management(inputShp, outputShp)

        ####################################
        ### Calculate the water contents ###
        ####################################

        # Get the nameArray
        nameArray = []
        with arcpy.da.SearchCursor(outputShp, "soilname") as searchCursor:
            for row in searchCursor:
                name = row[0]

                nameArray.append(name)

        # Get PTF fields
        PTFxml = os.path.join(outputFolder, "ptfinfo.xml")
        PTFFields = common.readXML(PTFxml, 'PTFFields')
        PTFPressures = common.readXML(PTFxml, 'PTFPressures')
        PTFUnit = common.readXML(PTFxml, 'PTFUnit')

        # Call point-PTF here depending on PTFOption
        if PTFOption == "Nguyen_2014":
            results = point_PTFs.Nguyen_2014(outputFolder, outputShp, carbonConFactor, carbContent)

        elif PTFOption == "Adhikary_2008":
            results = point_PTFs.Adhikary_2008(outputFolder, outputShp)
        
        elif PTFOption == "Rawls_1982":
            results = point_PTFs.Rawls_1982(outputFolder, outputShp, carbonConFactor, carbContent)

        elif PTFOption == "Hall_1977_top":
            results = point_PTFs.Hall_1977_top(outputFolder, outputShp, carbonConFactor, carbContent)

        elif PTFOption == "Hall_1977_sub":
            results = point_PTFs.Hall_1977_sub(outputFolder, outputShp, carbonConFactor, carbContent)

        elif PTFOption == "GuptaLarson_1979":
            results = point_PTFs.GuptaLarson_1979(outputFolder, outputShp, carbonConFactor, carbContent)

        elif PTFOption == "Batjes_1996":
            results = point_PTFs.Batjes_1996(outputFolder, outputShp, carbonConFactor, carbContent)

        elif PTFOption == "SaxtonRawls_2006":
            results = point_PTFs.SaxtonRawls_2006(outputFolder, outputShp, carbonConFactor, carbContent)

        elif PTFOption == "Pidgeon_1972":
            results = point_PTFs.Pidgeon_1972(outputFolder, outputShp, carbonConFactor, carbContent)

        elif str(PTFOption[0:8]) == "Lal_1978":            
            results = point_PTFs.Lal_1978(outputFolder, outputShp, PTFOption)

        elif PTFOption == "AinaPeriaswamy_1985":
            results = point_PTFs.AinaPeriaswamy_1985(outputFolder, outputShp)

        elif PTFOption == "ManriqueJones_1991":
            results = point_PTFs.ManriqueJones_1991(outputFolder, outputShp)

        elif PTFOption == "vanDenBerg_1997":
            results = point_PTFs.vanDenBerg_1997(outputFolder, outputShp, carbonConFactor, carbContent)

        elif PTFOption == "TomasellaHodnett_1998":
            results = point_PTFs.TomasellaHodnett_1998(outputFolder, outputShp, carbonConFactor, carbContent)

        elif PTFOption == "Reichert_2009_OM":
            results = point_PTFs.Reichert_2009_OM(outputFolder, outputShp, carbonConFactor, carbContent)

        elif PTFOption == "Reichert_2009":
            results = point_PTFs.Reichert_2009(outputFolder, outputShp)

        elif PTFOption == "Botula_2013":
            results = point_PTFs.Botula_2013(outputFolder, outputShp)

        elif PTFOption == "ShwethaVarija_2013":
            results = point_PTFs.ShwethaVarija_2013(outputFolder, outputShp)

        elif PTFOption == "Dashtaki_2010_point":
            results = point_PTFs.Dashtaki_2010(outputFolder, outputShp)

        elif PTFOption == "Santra_2018_OC":
            results = point_PTFs.Santra_2018_OC(outputFolder, outputShp, carbonConFactor, carbContent)

        elif PTFOption == "Santra_2018":
            results = point_PTFs.Santra_2018(outputFolder, outputShp)

        else:
            log.error("PTF option not recognised")
            sys.exit()

        # Plots
        plots.plotPTF(outputFolder, outputShp, PTFOption, nameArray, results)
                
        ######################################################
        ### Calculate water content at critical thresholds ###
        ######################################################
        
        satStatus = False
        fcStatus = False
        sicStatus = False
        pwpStatus = False

        wc_satCalc = []
        wc_fcCalc = []
        wc_sicCalc = []
        wc_pwpCalc = []

        if PTFOption == "Reichert_2009_OM":
            log.info('For Reichert et al. (2009) - Sand, silt, clay, OM, BD saturation is at 6kPa')
            satField = "WC_6kPa"

        else:
            satField = "WC_0" + str(PTFUnit)
        
        fcField = "WC_" + str(int(fcVal)) + str(PTFUnit)
        sicField = "WC_" + str(int(sicVal)) + str(PTFUnit)
        pwpField = "WC_" + str(int(pwpVal)) + str(PTFUnit)

        wcFields = []
        wcArrays = []

        if satField in PTFFields:
            # Saturation set to 0kPa
            # PTFs with 0kPa:
            ## Saxton_1986, Batjes_1996, SaxtonRawls_2006
            ## Lal_1978_Group1, Lal_1978_Group2
            ## TomasellaHodnett_1998

            log.info('Field with WC at saturation found!')

            with arcpy.da.SearchCursor(outputShp, satField) as searchCursor:
                for row in searchCursor:
                    wc_sat = row[0]

                    if wc_sat > 1.0:
                        log.warning('Water content at saturation over 1.0')

                    wc_satCalc.append(wc_sat)

            satStatus = True

            wcFields.append("wc_satCalc")
            wcArrays.append(wc_satCalc)

            # Add sat field to output shapefile
            arcpy.AddField_management(outputShp, "wc_satCalc", "DOUBLE", 10, 6)

            recordNum = 0
            with arcpy.da.UpdateCursor(outputShp, "wc_satCalc") as cursor:
                for row in cursor:
                    row[0] = wc_satCalc[recordNum]

                    cursor.updateRow(row)
                    recordNum += 1

        else:
            log.warning('Field with WC at saturation not found')
            satStatus = False

        if fcField in PTFFields:
            log.info('Field with WC at field capacity found!')

            with arcpy.da.SearchCursor(outputShp, fcField) as searchCursor:
                for row in searchCursor:
                    wc_fc = row[0]
                    wc_fcCalc.append(wc_fc)

            fcStatus = True

            wcFields.append("wc_fcCalc")
            wcArrays.append(wc_fcCalc)

            # Add FC field to output shapefile
            arcpy.AddField_management(outputShp, "wc_fcCalc", "DOUBLE", 10, 6)

            recordNum = 0
            with arcpy.da.UpdateCursor(outputShp, "wc_fcCalc") as cursor:
                for row in cursor:
                    row[0] = wc_fcCalc[recordNum]

                    cursor.updateRow(row)
                    recordNum += 1

        else:
            log.warning('Field with WC at field capacity not found')
            fcStatus = False

        if sicField in PTFFields:
            log.info('Field with WC at water stress-induced stomatal closure found!')

            with arcpy.da.SearchCursor(outputShp, sicField) as searchCursor:
                for row in searchCursor:
                    wc_sic = row[0]
                    wc_sicCalc.append(wc_sic)

            sicStatus = True

            wcFields.append("wc_sicCalc")
            wcArrays.append(wc_sicCalc)

            # Add sic field to output shapefile
            arcpy.AddField_management(outputShp, "wc_sicCalc", "DOUBLE", 10, 6)

            recordNum = 0
            with arcpy.da.UpdateCursor(outputShp, "wc_sicCalc") as cursor:
                for row in cursor:
                    row[0] = wc_sicCalc[recordNum]

                    cursor.updateRow(row)
                    recordNum += 1

        else:
            log.warning('Field with WC at water stress-induced stomatal closure not found')
            
            sicStatus = False          

        if pwpField in PTFFields:
            log.info('Field with WC at permanent wilting point found!')

            with arcpy.da.SearchCursor(outputShp, pwpField) as searchCursor:
                for row in searchCursor:
                    wc_pwp = row[0]

                    if wc_pwp < 0.01:
                        log.warning('WARNING: Water content at PWP is below 0.01')
                    
                    elif wc_pwp < 0.05:
                        log.warning('Water content at PWP is below 0.05')

                    wc_pwpCalc.append(wc_pwp)

            pwpStatus = True

            wcFields.append("wc_pwpCalc")
            wcArrays.append(wc_pwpCalc)

            # Add pwp field to output shapefile
            arcpy.AddField_management(outputShp, "wc_pwpCalc", "DOUBLE", 10, 6)

            recordNum = 0
            with arcpy.da.UpdateCursor(outputShp, "wc_pwpCalc") as cursor:
                for row in cursor:
                    row[0] = wc_pwpCalc[recordNum]

                    cursor.updateRow(row)
                    recordNum += 1

        else:
            log.warning('Field with WC at permanent wilting point not found')
            
            pwpStatus = False        

        drainWater = []
        PAW = []
        RAW = []
        NRAW = []

        if satStatus == True and fcStatus == True:
            # drainWater = wc_sat - wc_fc

            drainWater = point_PTFs.calcWaterContent(wc_satCalc, wc_fcCalc, 'drainable water', nameArray)
            log.info('Drainable water calculated')

            wcFields.append("wc_DW")
            wcArrays.append(drainWater)

            # Add DW field to output shapefile
            arcpy.AddField_management(outputShp, "wc_DW", "DOUBLE", 10, 6)

            recordNum = 0
            with arcpy.da.UpdateCursor(outputShp, "wc_DW") as cursor:
                for row in cursor:
                    row[0] = drainWater[recordNum]

                    cursor.updateRow(row)
                    recordNum += 1

        if fcStatus == True and pwpStatus == True:
            # PAW = wc_fc - wc_pwp
            PAW = point_PTFs.calcWaterContent(wc_fcCalc, wc_pwpCalc, 'plant available water', nameArray)
            log.info('Plant available water calculated')

            wcFields.append("wc_PAW")
            wcArrays.append(PAW)

            # Add PAW field to output shapefile
            arcpy.AddField_management(outputShp, "wc_PAW", "DOUBLE", 10, 6)

            recordNum = 0
            with arcpy.da.UpdateCursor(outputShp, "wc_PAW") as cursor:
                for row in cursor:
                    row[0] = PAW[recordNum]

                    cursor.updateRow(row)
                    recordNum += 1

            pawStatus = True

        if fcStatus == True and sicStatus == True:
            # readilyAvailWater = wc_fc - wc_sic
            RAW = point_PTFs.calcWaterContent(wc_fcCalc, wc_sicCalc, 'readily available water', nameArray)
            log.info('Readily available water calculated')

            wcFields.append("wc_RAW")
            wcArrays.append(RAW)

            # Add wc_RAW field to output shapefile
            arcpy.AddField_management(outputShp, "wc_RAW", "DOUBLE", 10, 6)

            recordNum = 0
            with arcpy.da.UpdateCursor(outputShp, "wc_RAW") as cursor:
                for row in cursor:
                    row[0] = RAW[recordNum]

                    cursor.updateRow(row)
                    recordNum += 1

        elif pawStatus == True:
            # If PAW exists, get RAW = 0.5 * RAW
            PAW = point_PTFs.calcWaterContent(wc_fcCalc, wc_pwpCalc, 'plant available water', nameArray)
            
            RAW = [(float(i) * 0.5) for i in PAW]
            log.info('Readily available water calculated based on PAW')

            wcFields.append("wc_RAW")
            wcArrays.append(RAW)

            # Add wc_RAW field to output shapefile
            arcpy.AddField_management(outputShp, "wc_RAW", "DOUBLE", 10, 6)

            recordNum = 0
            with arcpy.da.UpdateCursor(outputShp, "wc_RAW") as cursor:
                for row in cursor:
                    row[0] = RAW[recordNum]

                    cursor.updateRow(row)
                    recordNum += 1
        else:
            log.info('Readily available water not calculated')

        if sicStatus == True and pwpStatus == True:
            # notRAW = wc_sic - wc_pwp
            NRAW = point_PTFs.calcWaterContent(wc_sicCalc, wc_pwpCalc, 'not readily available water', nameArray)
            log.info('Not readily available water calculated')

            wcFields.append("wc_NRAW")
            wcArrays.append(NRAW)

            # Add sat field to output shapefile
            arcpy.AddField_management(outputShp, "wc_NRAW", "DOUBLE", 10, 6)

            recordNum = 0
            with arcpy.da.UpdateCursor(outputShp, "wc_NRAW") as cursor:
                for row in cursor:
                    row[0] = NRAW[recordNum]

                    cursor.updateRow(row)
                    recordNum += 1

        log.info('Water contents at critical thresholds written to output shapefile')

    except Exception:
        arcpy.AddError("Point-PTFs function failed")
        raise

    finally:
        # Remove feature layers from memory
        try:
            for lyr in common.listFeatureLayers(locals()):
                arcpy.Delete_management(locals()[lyr])
                exec(lyr + ' = None') in locals()
        except Exception:
            pass
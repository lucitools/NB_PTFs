import configuration
import arcpy
import math
import os
import sys
import NB_PTFs.lib.log as log
import NB_PTFs.lib.common as common
import NB_PTFs.lib.checks_PTFs as checks_PTFs
import NB_PTFs.lib.PTFdatabase as PTFdatabase
import NB_PTFs.lib.ksat_PTFs as ksat_PTFs
from NB_PTFs.lib.external import six # Python 2/3 compatibility module

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log, common, checks_PTFs, PTFdatabase, ksat_PTFs])

def function(outputFolder, inputFolder, KsatOption, carbContent, carbonConFactor):

    try:
        # Set temporary variables
        prefix = os.path.join(arcpy.env.scratchGDB, "moist_")

        # Set output filename
        outputShp = os.path.join(outputFolder, "Ksat.shp")

        ## From the input folder, pull the PTFinfo
        PTFxml = os.path.join(inputFolder, "ptfinfo.xml")

        if not os.path.exists(PTFxml):
            log.error('Please run the point-PTF or vg-PTF tool first before running this tool')
            sys.exit()

        else:
            PTFType = common.readXML(PTFxml, 'PTFType')

        if PTFType == "pointPTF":
            inputShp = os.path.join(inputFolder, "soil_point_ptf.shp")

        elif PTFType == "vgPTF":
            inputShp = os.path.join(inputFolder, "soil_vg.shp")

        else:
            log.error('Please run the point-PTF or vg-PTF tool first before running this tool')
            sys.exit()

        # Copy the input shapefile to the output folder
        arcpy.CopyFeatures_management(inputShp, outputShp)

        # Check if the K_sat field already exists in the shapefile
        if common.CheckField(outputShp, "K_sat"):
            log.error('K_sat field already present in the output shapefile')
            sys.exit()

        if KsatOption == 'Cosby_1984':
            warningArray, K_satArray = ksat_PTFs.Cosby_1984(outputFolder, outputShp)

        elif KsatOption == 'Puckett_1985':
            warningArray, K_satArray = ksat_PTFs.Puckett_1985(outputFolder, outputShp)

        elif KsatOption == 'Jabro_1992':
            warningArray, K_satArray = ksat_PTFs.Jabro_1992(outputFolder, outputShp)

        elif KsatOption == 'CampbellShiozawa_1994':
            warningArray, K_satArray = ksat_PTFs.CampbellShiozawa_1994(outputFolder, outputShp)

        elif KsatOption == 'FerrerJulia_2004_1':
            warningArray, K_satArray = ksat_PTFs.FerrerJulia_2004_1(outputFolder, outputShp)

        elif KsatOption == 'FerrerJulia_2004_2':
            warningArray, K_satArray = ksat_PTFs.FerrerJulia_2004_2(outputFolder, outputShp, carbonConFactor, carbContent)

        elif KsatOption == 'Ahuja_1989':
            warningArray, K_satArray = ksat_PTFs.Ahuja_1989(outputFolder, outputShp)

        elif KsatOption == 'MinasnyMcBratney_2000':
            warningArray, K_satArray = ksat_PTFs.MinasnyMcBratney_2000(outputFolder, outputShp)

        elif KsatOption == 'Brakensiek_1984':
            warningArray, K_satArray = ksat_PTFs.Brakensiek_1984(outputFolder, outputShp)

        else:
            log.error("Invalid KsatOption: " + str(KsatOption))
            sys.exit()

        # Write results to output shapefile
        arcpy.AddField_management(outputShp, "warning", "TEXT")
        arcpy.AddField_management(outputShp, "K_sat", "DOUBLE", 10, 6)

        outputFields = ["warning", "K_sat"]
        
        recordNum = 0
        with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
            for row in cursor:
                row[0] = warningArray[recordNum]
                row[1] = K_satArray[recordNum]

                cursor.updateRow(row)
                recordNum += 1

        log.info("Results written to the output shapefile inside the output folder")

    except Exception:
        arcpy.AddError("Saturated hydraulic conductivity function failed")
        raise

    finally:
        # Remove feature layers from memory
        try:
            for lyr in common.listFeatureLayers(locals()):
                arcpy.Delete_management(locals()[lyr])
                exec(lyr + ' = None') in locals()
        except Exception:
            pass

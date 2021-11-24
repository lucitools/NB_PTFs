'''
point_PTFs: contains all the point-PTF functions for calculating WC
'''

import sys
import os
import configuration
import numpy as np
import arcpy
import math
import NB_PTFs.lib.log as log
import NB_PTFs.lib.common as common
import NB_PTFs.lib.checks_PTFs as checks_PTFs
import NB_PTFs.lib.PTFdatabase as PTFdatabase
from NB_PTFs.lib.external import six # Python 2/3 compatibility module

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log, common, checks_PTFs, PTFdatabase])

def calcWaterContent(WCArray1, WCArray2, WCName, nameArray):

    # Returns a water content array (WCArray1 - WCArray2)
    wcArray = []

    for i in range(0, len(nameArray)):
        wcCalc = WCArray1[i] - WCArray2[i]

        if wcCalc < 0.0:
            log.warning('Negative ' + str(WCName) + ' calculated for ' + str(nameArray[i]))

        wcArray.append(wcCalc)

    return wcArray

def Nguyen_2014(outputFolder, outputShp, carbonConFactor, carbContent):

    log.info('Calculating water content at points using Nguyen et al. (2014)')

    PTFInfo = PTFdatabase.checkPTF("Nguyen_2014")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Returns these arrays
    warningArray = []
    WC_1kPaArray = []
    WC_3kPaArray = []
    WC_6kPaArray = []
    WC_10kPaArray = []
    WC_20kPaArray = []
    WC_33kPaArray = []
    WC_100kPaArray = []
    WC_1500kPaArray = []

    # Requirements: sand, silt, clay, OC, and BD

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    if carbContent == 'OC':
        reqFields = [OIDField, "Sand", "Silt", "Clay", "OC", "BD"]
        carbonConFactor = 1.0

    elif carbContent == 'OM':
        reqFields = [OIDField, "Sand", "Silt", "Clay", "OM", "BD"]

    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    siltPerc = []
    clayPerc = []
    carbPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            silt = row[2]
            clay = row[3]
            carbon = row[4]
            BD = row[5]

            record.append(objectID)
            sandPerc.append(sand)
            siltPerc.append(silt)
            clayPerc.append(clay)
            carbPerc.append(carbon)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkSSC(sandPerc[x], siltPerc[x], clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkCarbon(carbPerc[x], carbContent, record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        
        warningArray.append(warningFlag)

        # Calculate water content using Nguyen et al. (2014)
        WC_1kPa = (0.002 * clayPerc[x]) + (0.055 * math.log((carbPerc[x] * float(carbonConFactor)), 10.0)) - (0.144 * BDg_cm3[x]) + 0.575
        WC_3kPa = (0.002 * clayPerc[x]) + (0.067 * math.log((carbPerc[x] * float(carbonConFactor)), 10.0)) - (0.125 * BDg_cm3[x]) + 0.527
        WC_6kPa = (0.001 * siltPerc[x]) + (0.003 * clayPerc[x]) + (0.12 * math.log((carbPerc[x] * float(carbonConFactor)), 10.0)) - (0.062 * BDg_cm3[x]) + 0.367
        WC_10kPa = (0.001 * siltPerc[x]) + (0.003 * clayPerc[x]) + (0.127 * math.log((carbPerc[x] * float(carbonConFactor)), 10.0)) + 0.228 
        WC_20kPa = (- 0.002 * sandPerc[x]) + (0.002 * clayPerc[x]) + (0.066 * math.log((carbPerc[x] * float(carbonConFactor)), 10.0)) - (0.058 * BDg_cm3[x]) + 0.415
        WC_33kPa = (- 0.002 * sandPerc[x]) + (0.001 * clayPerc[x]) - (0.118 * BDg_cm3[x]) + 0.493
        WC_100kPa = (- 0.003 * sandPerc[x]) - (0.107 * BDg_cm3[x]) + 0.497
        WC_1500kPa = (- 0.002 * sandPerc[x]) + (0.002 * clayPerc[x]) - (0.032 * BDg_cm3[x]) + 0.234
        
        outValues = [WC_1kPa, WC_3kPa, WC_6kPa, WC_10kPa, WC_20kPa, WC_33kPa, WC_100kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_1kPaArray.append(WC_1kPa)
        WC_3kPaArray.append(WC_3kPa)
        WC_6kPaArray.append(WC_6kPa)
        WC_10kPaArray.append(WC_10kPa)
        WC_20kPaArray.append(WC_20kPa)
        WC_33kPaArray.append(WC_33kPa)
        WC_100kPaArray.append(WC_100kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_1kPaArray[recordNum]
            row[2] = WC_3kPaArray[recordNum]
            row[3] = WC_6kPaArray[recordNum]
            row[4] = WC_10kPaArray[recordNum]
            row[5] = WC_20kPaArray[recordNum]
            row[6] = WC_33kPaArray[recordNum]
            row[7] = WC_100kPaArray[recordNum]
            row[8] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")

    results = []
    results.append(warningArray)
    results.append(WC_1kPaArray)
    results.append(WC_3kPaArray)
    results.append(WC_6kPaArray)
    results.append(WC_10kPaArray)
    results.append(WC_20kPaArray)
    results.append(WC_33kPaArray)
    results.append(WC_100kPaArray)
    results.append(WC_1500kPaArray)

    return results

def Adhikary_2008(outputFolder, outputShp):

    log.info('Calculating water content at points using Adhikary et al. (2008)')

    PTFInfo = PTFdatabase.checkPTF("Adhikary_2008")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Returns these arrays
    warningArray = []
    WC_10kPaArray = []
    WC_33kPaArray = []
    WC_100kPaArray = []
    WC_300kPaArray = []
    WC_500kPaArray = []
    WC_1000kPaArray = []
    WC_1500kPaArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: sand, silt, clay
    reqFields = [OIDField, "Sand", "Silt", "Clay"]
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    siltPerc = []
    clayPerc = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            silt = row[2]
            clay = row[3]

            record.append(objectID)
            sandPerc.append(sand)
            siltPerc.append(silt)
            clayPerc.append(clay)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkSSC(sandPerc[x], siltPerc[x], clayPerc[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Adhikary et al. (2008) m3m-3
        WC_10kPa = 0.625 - (0.0058 * sandPerc[x]) - (0.0021 * siltPerc[x])
        WC_33kPa = 0.5637 - (0.0051 * sandPerc[x]) - (0.0027 * siltPerc[x])
        WC_100kPa = 0.1258 - (0.0009 * sandPerc[x]) + (0.004 * clayPerc[x])
        WC_300kPa = 0.085 - (0.0007 * sandPerc[x]) + (0.0038 * clayPerc[x])
        WC_500kPa = 0.0473 - (0.0004 * sandPerc[x])  + (0.0042 * clayPerc[x])
        WC_1000kPa = 0.0035 + (0.0045 * clayPerc[x])
        WC_1500kPa = 0.0071 + (0.0044 * clayPerc[x])

        outValues = [WC_10kPa, WC_33kPa, WC_100kPa, WC_300kPa, WC_500kPa, WC_1000kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_10kPaArray.append(WC_10kPa)
        WC_33kPaArray.append(WC_33kPa)
        WC_100kPaArray.append(WC_100kPa)
        WC_300kPaArray.append(WC_300kPa)
        WC_500kPaArray.append(WC_500kPa)
        WC_1000kPaArray.append(WC_1000kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_10kPaArray[recordNum]
            row[2] = WC_33kPaArray[recordNum]
            row[3] = WC_100kPaArray[recordNum]
            row[4] = WC_300kPaArray[recordNum]
            row[5] = WC_500kPaArray[recordNum]
            row[6] = WC_1000kPaArray[recordNum]
            row[7] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")

    results = []
    results.append(warningArray)
    results.append(WC_10kPaArray)
    results.append(WC_33kPaArray)
    results.append(WC_100kPaArray)
    results.append(WC_300kPaArray)
    results.append(WC_500kPaArray)
    results.append(WC_1000kPaArray)
    results.append(WC_1500kPaArray)

    return results

def Rawls_1982(outputFolder, outputShp, carbonConFactor, carbContent):

    log.info('Calculating water content at points using Rawls et al. (1982)')

    PTFInfo = PTFdatabase.checkPTF("Rawls_1982")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Returns these arrays
    warningArray = []
    WC_10kPaArray = []
    WC_20kPaArray = []
    WC_33kPaArray = []
    WC_60kPaArray = []
    WC_100kPaArray = []
    WC_200kPaArray = []
    WC_400kPaArray = []
    WC_700kPaArray = []
    WC_1000kPaArray = []
    WC_1500kPaArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: sand, silt, clay, OC, and BD
    if carbContent == 'OC':
        reqFields = [OIDField, "Sand", "Silt", "Clay", "OC", "BD"]                    

    elif carbContent == 'OM':
        reqFields = [OIDField, "Sand", "Silt", "Clay", "OM", "BD"]
        carbonConFactor = 1.0
    
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    siltPerc = []
    clayPerc = []
    carbPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            silt = row[2]
            clay = row[3]
            carbon = row[4]
            BD = row[5]

            record.append(objectID)
            sandPerc.append(sand)
            siltPerc.append(silt)
            clayPerc.append(clay)
            carbPerc.append(carbon)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkSSC(sandPerc[x], siltPerc[x], clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkCarbon(carbPerc[x], carbContent, record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Rawls et al. (1982) cm3cm-3
        WC_10kPa = 0.4188 - (0.0030 * sandPerc[x]) + (0.0023 * clayPerc[x]) + (0.0317 * (carbPerc[x] * float(carbonConFactor)))
        WC_20kPa = 0.3121 - (0.0024 * sandPerc[x]) + (0.0032 * clayPerc[x]) + (0.0314 * (carbPerc[x] * float(carbonConFactor)))
        WC_33kPa = 0.2576 - (0.002 * sandPerc[x]) + (0.0036 * clayPerc[x]) + (0.0299 * (carbPerc[x] * float(carbonConFactor)))
        WC_60kPa = 0.2065 - (0.0016 * sandPerc[x]) + (0.0040 * clayPerc[x]) + (0.0275 * (carbPerc[x] * float(carbonConFactor)))
        WC_100kPa = 0.0349 + (0.0014 * siltPerc[x]) + (0.0055 * clayPerc[x]) + (0.0251 * (carbPerc[x] * float(carbonConFactor)))
        WC_200kPa = 0.0281 + (0.0011 * siltPerc[x]) + (0.0054 * clayPerc[x]) + (0.0220 * (carbPerc[x] * float(carbonConFactor)))
        WC_400kPa = 0.0238 + (0.0008 * siltPerc[x]) + (0.0052 * clayPerc[x]) + (0.0190 * (carbPerc[x] * float(carbonConFactor)))
        WC_700kPa = 0.0216 + (0.0006 * siltPerc[x]) + (0.0050 * clayPerc[x]) + (0.0167 * (carbPerc[x] * float(carbonConFactor)))
        WC_1000kPa = 0.0205 + (0.0005 * siltPerc[x]) + (0.0049 * clayPerc[x]) + (0.0154 * (carbPerc[x] * float(carbonConFactor)))
        WC_1500kPa = 0.026 + (0.005 * clayPerc[x]) + (0.0158 * (carbPerc[x] * float(carbonConFactor)))
        
        outValues = [WC_10kPa, WC_20kPa, WC_33kPa, WC_60kPa, WC_100kPa, WC_200kPa, WC_400kPa, WC_700kPa, WC_1000kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_10kPaArray.append(WC_10kPa)
        WC_20kPaArray.append(WC_20kPa)
        WC_33kPaArray.append(WC_33kPa)
        WC_60kPaArray.append(WC_60kPa)
        WC_100kPaArray.append(WC_100kPa)
        WC_200kPaArray.append(WC_200kPa)
        WC_400kPaArray.append(WC_400kPa)
        WC_700kPaArray.append(WC_700kPa)
        WC_1000kPaArray.append(WC_1000kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_10kPaArray[recordNum]
            row[2] = WC_20kPaArray[recordNum]
            row[3] = WC_33kPaArray[recordNum]
            row[4] = WC_60kPaArray[recordNum]
            row[5] = WC_100kPaArray[recordNum]
            row[6] = WC_200kPaArray[recordNum]
            row[7] = WC_400kPaArray[recordNum]
            row[8] = WC_700kPaArray[recordNum]
            row[9] = WC_1000kPaArray[recordNum]
            row[10] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    results = []
    results.append(warningArray)
    results.append(WC_10kPaArray)
    results.append(WC_20kPaArray)
    results.append(WC_33kPaArray)
    results.append(WC_60kPaArray)
    results.append(WC_100kPaArray)
    results.append(WC_200kPaArray)
    results.append(WC_400kPaArray)
    results.append(WC_700kPaArray)
    results.append(WC_1000kPaArray)
    results.append(WC_1500kPaArray)

    return results

def Hall_1977_top(outputFolder, outputShp, carbonConFactor, carbContent):

    log.info('Calculating water content at points using Hall et al. (1977) for topsoil')

    PTFInfo = PTFdatabase.checkPTF("Hall_1977_top")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Returns these arrays
    warningArray = []
    WC_5kPaArray = []
    WC_10kPaArray = []
    WC_33kPaArray = []
    WC_200kPaArray = []
    WC_1500kPaArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: silt, clay, OC, and BD
    if carbContent == 'OC':
        reqFields = [OIDField, "Clay", "Silt", "OC", "BD"]
        carbonConFactor = 1.0

    elif carbContent == 'OM':
        reqFields = [OIDField, "Clay", "Silt", "OM", "BD"]

    checks_PTFs.checkInputFields(reqFields, outputShp)                   

    # Retrieve info from input
    record = []
    clayPerc = []
    siltPerc = []
    carbPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            clay = row[1]
            silt = row[2]
            carbon = row[3]
            BD = row[4]

            record.append(objectID)
            clayPerc.append(clay)
            siltPerc.append(silt)
            carbPerc.append(carbon)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Silt", siltPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Topsoil
        WC_5kPa = (47 + (0.25 * clayPerc[x]) + (0.1 * siltPerc[x]) + (1.12 * carbPerc[x] * float(carbonConFactor)) - (16.52 * BDg_cm3[x])) *10**(-2)
        WC_10kPa =  (37.47 + (0.32 * clayPerc[x]) + (0.12 * siltPerc[x]) + (1.15 * carbPerc[x] * float(carbonConFactor)) - (1.25 * BDg_cm3[x])) *10**(-2)
        WC_33kPa = (22.66 + (0.36 * clayPerc[x]) + (0.12 * siltPerc[x]) + (1 * carbPerc[x] * float(carbonConFactor)) - (7.64 * BDg_cm3[x])) *10**(-2)
        WC_200kPa = (8.7 + (0.45 * clayPerc[x]) + (0.11 * siltPerc[x]) + (1.03 * carbPerc[x] * float(carbonConFactor))) *10**(-2)
        WC_1500kPa = (2.94 + (0.83 * clayPerc[x]) - (0.0054 * (clayPerc[x]**2))) * 10**(-2)

        outValues = [WC_5kPa, WC_10kPa, WC_33kPa, WC_200kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_5kPaArray.append(WC_5kPa)
        WC_10kPaArray.append(WC_10kPa)
        WC_33kPaArray.append(WC_33kPa)
        WC_200kPaArray.append(WC_200kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_5kPaArray[recordNum]
            row[2] = WC_10kPaArray[recordNum]
            row[3] = WC_33kPaArray[recordNum]
            row[4] = WC_200kPaArray[recordNum]
            row[5] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")

    results = []
    results.append(warningArray)
    results.append(WC_5kPaArray)
    results.append(WC_10kPaArray)
    results.append(WC_33kPaArray)
    results.append(WC_200kPaArray)
    results.append(WC_1500kPaArray)

    return results

def Hall_1977_sub(outputFolder, outputShp, carbonConFactor, carbContent):

    log.info('Calculating water content at points using Hall et al. (1977) for topsoil')

    PTFInfo = PTFdatabase.checkPTF("Hall_1977_sub")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Returns these arrays
    warningArray = []
    WC_5kPaArray = []
    WC_10kPaArray = []
    WC_33kPaArray = []
    WC_200kPaArray = []
    WC_1500kPaArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: silt, clay, OC, and BD
    if carbContent == 'OC':
        reqFields = [OIDField, "Clay", "Silt", "OC", "BD"]
        carbonConFactor = 1.0

    elif carbContent == 'OM':
        reqFields = [OIDField, "Clay", "Silt", "OM", "BD"]

    checks_PTFs.checkInputFields(reqFields, outputShp)                   

    # Retrieve info from input
    record = []
    clayPerc = []
    siltPerc = []
    carbPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            clay = row[1]
            silt = row[2]
            carbon = row[3]
            BD = row[4]

            record.append(objectID)
            clayPerc.append(clay)
            siltPerc.append(silt)
            carbPerc.append(carbon)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Silt", siltPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Subsoil
        WC_5kPa = (37.20 + (0.35 * clayPerc[x]) + (0.12 * siltPerc[x]) - (11.73 * BDg_cm3[x])) * 10**(-2)
        WC_10kPa = (27.87 + (0.41 * clayPerc[x]) + (0.15 * siltPerc[x]) - (8.32 * BDg_cm3[x])) * 10**(-2)
        WC_33kPa = (20.81 + (0.45 * clayPerc[x]) + (0.13 * siltPerc[x]) - (5.96 * BDg_cm3[x])) * 10**(-2)
        WC_200kPa = (7.57 + (0.48 * clayPerc[x]) + (0.11 * siltPerc[x])) * 10**(-2)
        WC_1500kPa = (1.48 + (0.84 * clayPerc[x]) - (0.0054 * clayPerc[x]**2)) * 10**(-2)
        
        outValues = [WC_5kPa, WC_10kPa, WC_33kPa, WC_200kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_5kPaArray.append(WC_5kPa)
        WC_10kPaArray.append(WC_10kPa)
        WC_33kPaArray.append(WC_33kPa)
        WC_200kPaArray.append(WC_200kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_5kPaArray[recordNum]
            row[2] = WC_10kPaArray[recordNum]
            row[3] = WC_33kPaArray[recordNum]
            row[4] = WC_200kPaArray[recordNum]
            row[5] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")
    
    results = []
    results.append(warningArray)
    results.append(WC_5kPaArray)
    results.append(WC_10kPaArray)
    results.append(WC_33kPaArray)
    results.append(WC_200kPaArray)
    results.append(WC_1500kPaArray)

    return results

def GuptaLarson_1979(outputFolder, outputShp, carbonConFactor, carbContent):

    log.info('Calculating water content at points using Gupta and Larson (1979)')

    PTFInfo = PTFdatabase.checkPTF("GuptaLarson_1979")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Returns these arrays
    warningArray = []
    WC_4kPaArray = []
    WC_7kPaArray = []
    WC_10kPaArray = []
    WC_20kPaArray = []
    WC_33kPaArray = []
    WC_60kPaArray = []
    WC_100kPaArray = []
    WC_200kPaArray = []
    WC_400kPaArray = []
    WC_700kPaArray = []
    WC_1000kPaArray = []
    WC_1500kPaArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: sand, silt, clay, OM, and BD
    if carbContent == 'OC':
        reqFields = [OIDField, "Sand", "Silt", "Clay", "OC", "BD"]                    

    elif carbContent == 'OM':
        reqFields = [OIDField, "Sand", "Silt", "Clay", "OM", "BD"]
        carbonConFactor = 1.0
    
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    siltPerc = []
    clayPerc = []
    carbPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            silt = row[2]
            clay = row[3]
            carbon = row[4]
            BD = row[5]

            record.append(objectID)
            sandPerc.append(sand)
            siltPerc.append(silt)
            clayPerc.append(clay)
            carbPerc.append(carbon)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkSSC(sandPerc[x], siltPerc[x], clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkCarbon(carbPerc[x], carbContent, record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Gupta and Larson (1979)- Salt, Silt, Clay, OM, BD
        WC_4kPa = (7.053 * 10**(-3) * sandPerc[x]) + (10.242 * 10**(-3) * siltPerc[x]) + (10.07 * 10**(-3) * clayPerc[x]) + (6.333 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (32.12 * 10**(-2) * BDg_cm3[x])
        WC_7kPa = (5.678 * 10**(-3) * sandPerc[x]) + (9.228 * 10**(-3) * siltPerc[x]) + (9.135 * 10**(-3) * clayPerc[x]) + (6.103 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (26.96 * 10**(-2) * BDg_cm3[x])
        WC_10kPa = (5.018 * 10**(-3) * sandPerc[x]) + (8.548 * 10**(-3) * siltPerc[x]) + (8.833 * 10**(-3) * clayPerc[x]) + (4.966 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (24.23 * 10**(-2) * BDg_cm3[x])
        WC_20kPa = (3.89 * 10**(-3) * sandPerc[x]) + (7.066 * 10**(-3) * siltPerc[x]) + (8.408 * 10**(-3) * clayPerc[x]) + (2.817 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (18.78 * 10**(-2) * BDg_cm3[x])
        WC_33kPa = (3.075 * 10**(-3) * sandPerc[x]) + (5.886 * 10**(-3) * siltPerc[x]) + (8.039 * 10**(-3) * clayPerc[x]) + (2.208 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (14.34 * 10**(-2) * BDg_cm3[x])
        WC_60kPa = (2.181 * 10**(-3) * sandPerc[x]) + (4.557 * 10**(-3) * siltPerc[x]) + (7.557 * 10**(-3) * clayPerc[x]) + (2.191 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (9.276 * 10**(-2) * BDg_cm3[x])
        WC_100kPa = (1.563 * 10**(-3) * sandPerc[x]) + (3.62 * 10**(-3) * siltPerc[x]) + (7.154 * 10**(-3) * clayPerc[x]) + (2.388 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (5.759 * 10**(-2) * BDg_cm3[x])
        WC_200kPa = (0.932 * 10**(-3) * sandPerc[x]) + (2.643 * 10**(-3) * siltPerc[x]) + (6.636 * 10**(-3) * clayPerc[x]) + (2.717 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (2.214 * 10**(-2) * BDg_cm3[x])
        WC_400kPa = (0.483 * 10**(-3) * sandPerc[x]) + (1.943 * 10**(-3) * siltPerc[x]) + (6.128 * 10**(-3) * clayPerc[x]) + (2.925 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) - (0.204 * 10**(-2) * BDg_cm3[x])
        WC_700kPa = (0.214 * 10**(-3) * sandPerc[x]) + (1.538 * 10**(-3) * siltPerc[x]) + (5.908 * 10**(-3) * clayPerc[x]) + (2.855 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) + (1.53 * 10**(-2) * BDg_cm3[x])
        WC_1000kPa = (0.076 * 10**(-3) * sandPerc[x]) + (1.334 * 10**(-3) * siltPerc[x]) + (5.802 * 10**(-3) * clayPerc[x]) + (2.653 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) + (2.145 * 10**(-2) * BDg_cm3[x])
        WC_1500kPa = (-0.059 * 10**(-3) * sandPerc[x]) + (1.142 * 10**(-3) * siltPerc[x]) + (5.766 * 10**(-3) * clayPerc[x]) + (2.228 * 10**(-3) * carbPerc[x]*float(carbonConFactor)) + (2.671 * 10**(-2) * BDg_cm3[x])

        outValues = [WC_4kPa, WC_7kPa, WC_10kPa, WC_20kPa, WC_33kPa, WC_60kPa, WC_100kPa, WC_200kPa, WC_400kPa, WC_700kPa, WC_1000kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_4kPaArray.append(WC_4kPa)
        WC_7kPaArray.append(WC_7kPa)
        WC_10kPaArray.append(WC_10kPa)
        WC_20kPaArray.append(WC_20kPa)
        WC_33kPaArray.append(WC_33kPa)
        WC_60kPaArray.append(WC_60kPa)
        WC_100kPaArray.append(WC_100kPa)
        WC_200kPaArray.append(WC_200kPa)
        WC_400kPaArray.append(WC_400kPa)
        WC_700kPaArray.append(WC_700kPa)
        WC_1000kPaArray.append(WC_1000kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_4kPaArray[recordNum]
            row[2] = WC_7kPaArray[recordNum]
            row[3] = WC_10kPaArray[recordNum]
            row[4] = WC_20kPaArray[recordNum]
            row[5] = WC_33kPaArray[recordNum]
            row[6] = WC_60kPaArray[recordNum]
            row[7] = WC_100kPaArray[recordNum]
            row[8] = WC_200kPaArray[recordNum]
            row[9] = WC_400kPaArray[recordNum]
            row[10] = WC_700kPaArray[recordNum]
            row[11] = WC_1000kPaArray[recordNum]
            row[12] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")

    results = []
    results.append(warningArray)
    results.append(WC_4kPaArray)
    results.append(WC_7kPaArray)
    results.append(WC_10kPaArray)
    results.append(WC_20kPaArray)
    results.append(WC_33kPaArray)
    results.append(WC_60kPaArray)
    results.append(WC_100kPaArray)
    results.append(WC_200kPaArray)
    results.append(WC_400kPaArray)
    results.append(WC_700kPaArray)
    results.append(WC_1000kPaArray)
    results.append(WC_1500kPaArray)

    return results

def Batjes_1996(outputFolder, outputShp, carbonConFactor, carbContent):

    log.info('Calculating water content at points using Batjes (1996)')

    PTFInfo = PTFdatabase.checkPTF("Batjes_1996")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Returns these arrays
    warningArray = []
    WC_0kPaArray = []
    WC_1kPaArray = []
    WC_3kPaArray = []
    WC_5kPaArray = []
    WC_10kPaArray = []
    WC_20kPaArray = []
    WC_33kPaArray = []
    WC_50kPaArray = []
    WC_250kPaArray = []
    WC_1500kPaArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: silt, clay, and OC
    if carbContent == 'OC':
        reqFields = [OIDField, "Silt", "Clay", "OC"]
        carbonConFactor = 1.0

    elif carbContent == 'OM':
        reqFields = [OIDField, "Silt", "Clay", "OM"]                    
    
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    siltPerc = []
    clayPerc = []
    carbPerc = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            silt = row[1]
            clay = row[2]
            carbon = row[3]

            record.append(objectID)
            siltPerc.append(silt)
            clayPerc.append(clay)
            carbPerc.append(carbon)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkCarbon(carbPerc[x], carbContent, record[x])
        warningFlag = checks_PTFs.checkValue("Silt", siltPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Batjes (1996) - Silt, Clay, OC
        WC_0kPa = ((0.6903 * clayPerc[x]) + (0.5482 * siltPerc[x]) + (4.2844 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
        WC_1kPa = ((0.6463 * clayPerc[x]) + (0.5436 * siltPerc[x]) + (3.7091 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
        WC_3kPa = ((0.5980 * clayPerc[x]) + (0.3745 * siltPerc[x]) + (3.7611 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
        WC_5kPa = ((0.6681 * clayPerc[x]) + (0.2614 * siltPerc[x]) + (2.2150 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
        WC_10kPa = ((0.5266 * clayPerc[x]) + (0.3999 * siltPerc[x]) + (3.1752 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
        WC_20kPa = ((0.5082 * clayPerc[x]) + (0.4197 * siltPerc[x]) + (2.5043 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
        WC_33kPa = ((0.4600 * clayPerc[x]) + (0.3045 * siltPerc[x]) + (2.0703 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
        WC_50kPa = ((0.5032 * clayPerc[x]) + (0.3636 * siltPerc[x]) + (2.4461 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
        WC_250kPa = ((0.4611 * clayPerc[x]) + (0.2390 * siltPerc[x]) + (1.5742 * carbPerc[x] * float(carbonConFactor)))*10**(-2)
        WC_1500kPa = ((0.3624 * clayPerc[x]) + (0.1170 * siltPerc[x]) + (1.6054 * carbPerc[x] * float(carbonConFactor)))*10**(-2)

        outValues = [WC_0kPa, WC_1kPa, WC_3kPa, WC_5kPa, WC_10kPa, WC_20kPa, WC_33kPa, WC_50kPa, WC_250kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_0kPaArray.append(WC_0kPa)
        WC_1kPaArray.append(WC_1kPa)
        WC_3kPaArray.append(WC_3kPa)
        WC_5kPaArray.append(WC_5kPa)
        WC_10kPaArray.append(WC_10kPa)
        WC_20kPaArray.append(WC_20kPa)
        WC_33kPaArray.append(WC_33kPa)
        WC_50kPaArray.append(WC_50kPa)
        WC_250kPaArray.append(WC_250kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_0kPaArray[recordNum]
            row[2] = WC_1kPaArray[recordNum]
            row[3] = WC_3kPaArray[recordNum]
            row[4] = WC_5kPaArray[recordNum]
            row[5] = WC_10kPaArray[recordNum]
            row[6] = WC_20kPaArray[recordNum]
            row[7] = WC_33kPaArray[recordNum]
            row[8] = WC_50kPaArray[recordNum]
            row[9] = WC_250kPaArray[recordNum]
            row[10] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    results = []
    results.append(warningArray)
    results.append(WC_0kPaArray)
    results.append(WC_1kPaArray)
    results.append(WC_3kPaArray)
    results.append(WC_5kPaArray)
    results.append(WC_10kPaArray)
    results.append(WC_20kPaArray)
    results.append(WC_33kPaArray)
    results.append(WC_50kPaArray)
    results.append(WC_250kPaArray)
    results.append(WC_1500kPaArray)

    return results

def SaxtonRawls_2006(outputFolder, outputShp, carbonConFactor, carbContent):

    log.info('Calculating water content at points using Saxton and Rawls (2006)')

    PTFInfo = PTFdatabase.checkPTF("SaxtonRawls_2006")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Returns these arrays
    warningArray = []    
    WC_0kPaArray = []
    WC_33kPaArray = []
    WC_1500kPaArray = []

    K_satArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: sand, clay, and OM
    if carbContent == 'OC':
        reqFields = [OIDField, "Sand", "Clay", "OC"]                    

    elif carbContent == 'OM':
        reqFields = [OIDField, "Sand", "Clay", "OM"]
        carbonConFactor = 1.0
    
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    clayPerc = []
    carbPerc = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            clay = row[2]
            carbon = row[3]

            record.append(objectID)
            sandPerc.append(sand)
            clayPerc.append(clay)
            carbPerc.append(carbon)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkCarbon(carbPerc[x], carbContent, record[x])
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Saxton and Rawls (2006) - Sand, Clay, OM
        WC_33tkPa = (-0.00251 * sandPerc[x]) + (0.00195 * clayPerc[x]) + (0.00011 * carbPerc[x]*float(carbonConFactor)) + (0.0000006 * sandPerc[x] * carbPerc[x]*float(carbonConFactor)) - (0.0000027 * clayPerc[x] * carbPerc[x]*float(carbonConFactor)) + (0.0000452 * sandPerc[x] * clayPerc[x]) + 0.299
        WC_33kPa = (1.283 * (WC_33tkPa)**(2)) + (0.626 * (WC_33tkPa)) - 0.015
        WC_sat_33tkPa = (0.00278 * sandPerc[x]) + (0.00034 * clayPerc[x]) + (0.00022 * carbPerc[x]*float(carbonConFactor)) - (0.0000018 * sandPerc[x] * carbPerc[x]*float(carbonConFactor)) - (0.0000027 * clayPerc[x] * carbPerc[x]*float(carbonConFactor)) - (0.0000584 * sandPerc[x] * clayPerc[x]) + 0.078
        WC_sat_33kPa = 1.636*WC_sat_33tkPa - 0.107
        WC_sat = WC_33kPa + WC_sat_33kPa - (0.00097 * sandPerc[x]) + 0.043                    
        WC_1500tkPa = (-0.00024 * sandPerc[x]) + (0.00487 * clayPerc[x]) + (0.00006 * carbPerc[x]*float(carbonConFactor)) + (0.0000005 * sandPerc[x] * carbPerc[x]*float(carbonConFactor)) - (0.0000013 * clayPerc[x] * carbPerc[x]*float(carbonConFactor)) + (0.0000068 * sandPerc[x] * clayPerc[x]) + 0.031
        WC_1500kPa = 1.14*WC_1500tkPa - 0.02

        outValues = [WC_33kPa, WC_1500kPa, WC_sat]
        checks_PTFs.checkNegOutput(outValues, x)

        B_SR = (math.log(1500.0) - math.log(33.0)) / (math.log(WC_33kPa) - math.log(WC_1500kPa))
        lamda_SR = 1.0 / float(B_SR)
        K_sat = 1930.0 * ((WC_sat - WC_33kPa)**(3 - lamda_SR))

        WC_0kPaArray.append(WC_sat)
        WC_33kPaArray.append(WC_33kPa)        
        WC_1500kPaArray.append(WC_1500kPa)
        K_satArray.append(K_sat)

    # Write K_sat to output shapefile
    arcpy.AddField_management(outputShp, "K_sat", "DOUBLE", 10, 6)

    outputFields = ["K_sat"]
    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
        for row in cursor:
            row[0] = K_satArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_0kPaArray[recordNum]
            row[2] = WC_33kPaArray[recordNum]
            row[3] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")

    results = []
    results.append(warningArray)
    results.append(WC_0kPaArray)
    results.append(WC_33kPaArray)
    results.append(WC_1500kPaArray)

    return results

def Pidgeon_1972(outputFolder, outputShp, carbonConFactor, carbContent):

    log.info('Calculating water content at points using Pidgeon (1972)')

    PTFInfo = PTFdatabase.checkPTF("Pidgeon_1972")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Returns these arrays
    warningArray = []
    WC_10kPaArray = []
    WC_33kPaArray = []
    WC_1500kPaArray = []

    WC_FCArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: silt, clay, BD, and OM
    if carbContent == 'OC':
        reqFields = [OIDField, "Silt", "Clay", "OC", "BD"]                    

    elif carbContent == 'OM':
        reqFields = [OIDField, "Silt", "Clay", "OM", "BD"]
        carbonConFactor = 1.0
    
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    siltPerc = []
    clayPerc = []
    carbPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            silt = row[1]
            clay = row[2]
            carbon = row[3]
            BD = row[4]

            record.append(objectID)
            siltPerc.append(silt)
            clayPerc.append(clay)
            carbPerc.append(carbon)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkCarbon(carbPerc[x], carbContent, record[x])
        warningFlag = checks_PTFs.checkValue("Silt", siltPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Pidgeon (1972) - Silt, Clay, OM, BD
        WC_FC = (7.38 + (0.16 * siltPerc[x]) + (0.3 * clayPerc[x]) + (1.54 * carbPerc[x]*float(carbonConFactor))) * BDg_cm3[x] * 10**(-2)
        WC_10kPa = ((WC_FC * 100) - 2.54)/91.0
        WC_33kPa = ((WC_FC * 100) - 3.77)/95.0
        WC_1500kPa = (-4.19 + (0.19 * siltPerc[x]) + (0.39 * clayPerc[x]) + (0.9 * carbPerc[x]*float(carbonConFactor))) * BDg_cm3[x] * 10**(-2)

        outValues = [WC_FC, WC_10kPa, WC_33kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_FCArray.append(WC_FC)
        WC_10kPaArray.append(WC_10kPa)
        WC_33kPaArray.append(WC_33kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_10kPaArray[recordNum]
            row[2] = WC_33kPaArray[recordNum]
            row[3] = WC_1500kPaArray[recordNum]
            
            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")
    
    results = []
    results.append(warningArray)
    results.append(WC_10kPaArray)
    results.append(WC_33kPaArray)
    results.append(WC_1500kPaArray)

    return results

def Lal_1978(outputFolder, outputShp, PTFOption):

    log.info('Calculating water content at points using Lal (1978)')

    PTFInfo = PTFdatabase.checkPTF("Lal_1978")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Returns these arrays
    warningArray = []
    WC_0kPaArray = []
    WC_10kPaArray = []
    WC_33kPaArray = []
    WC_1500kPaArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: Clay and BD
    reqFields = [OIDField, "Clay", "BD"]
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    clayPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            clay = row[1]
            BD = row[2]

            record.append(objectID)
            clayPerc.append(clay)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        if PTFOption == "Lal_1978_Group1":

            # Calculate water content using Lal (1978)- Clay, BD
            WC_0kPa = (0.289 + (0.004 * clayPerc[x])) * BDg_cm3[x]
            WC_10kPa = (0.102 + (0.003 * clayPerc[x])) * BDg_cm3[x]
            WC_33kPa = (0.065 + (0.004 * clayPerc[x])) * BDg_cm3[x] 
            WC_1500kPa = (0.006 + (0.003 * clayPerc[x])) * BDg_cm3[x] 

        elif PTFOption == "Lal_1978_Group2":

            # Calculate water content using Lal (1978) Group II- Clay, BD
            WC_0kPa = (0.296 + (0.004 * clayPerc[x])) * BDg_cm3[x]
            WC_10kPa = (0.080 + (0.003 * clayPerc[x])) * BDg_cm3[x]
            WC_33kPa = (0.047 + (0.003 * clayPerc[x])) * BDg_cm3[x] 
            WC_1500kPa = (0.025 + (0.0022* clayPerc[x])) * BDg_cm3[x]

        outValues = [WC_0kPa, WC_10kPa, WC_33kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_0kPaArray.append(WC_0kPa)
        WC_10kPaArray.append(WC_10kPa)
        WC_33kPaArray.append(WC_33kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_0kPaArray[recordNum]
            row[2] = WC_10kPaArray[recordNum]
            row[3] = WC_33kPaArray[recordNum]
            row[4] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")

    results = []
    results.append(warningArray)
    results.append(WC_0kPaArray)
    results.append(WC_10kPaArray)
    results.append(WC_33kPaArray)
    results.append(WC_1500kPaArray)

    return results

def AinaPeriaswamy_1985(outputFolder, outputShp):

    log.info('Calculating water content at points using Aina and Periaswamy (1985)')

    PTFInfo = PTFdatabase.checkPTF("AinaPeriaswamy_1985")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Returns these arrays
    warningArray = []
    WC_33kPaArray = []
    WC_1500kPaArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: Sand, clay and BD
    reqFields = [OIDField, "Sand", "Clay", "BD"]
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    clayPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            clay = row[2]
            BD = row[3]

            record.append(objectID)
            sandPerc.append(sand)
            clayPerc.append(clay)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Aina and Periaswamy (1985)- Sand, Clay, BD
        WC_33kPa = 0.6788 - (0.0055 * sandPerc[x]) - (0.0013 * BDg_cm3[x])
        WC_1500kPa = 0.00213 + (0.0031 * clayPerc[x])

        outValues = [WC_33kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_33kPaArray.append(WC_33kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_33kPaArray[recordNum]
            row[2] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")

    results = []
    results.append(warningArray)
    results.append(WC_33kPaArray)
    results.append(WC_1500kPaArray)

    return results

def ManriqueJones_1991(outputFolder, outputShp):

    log.info('Calculating water content at points using Manrique and Jones (1991)')

    PTFInfo = PTFdatabase.checkPTF("ManriqueJones_1991")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Returns these arrays
    warningArray = []
    WC_33kPaArray = []
    WC_1500kPaArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: Sand, clay and BD
    reqFields = [OIDField, "Sand", "Clay", "BD"]
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    clayPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            clay = row[2]
            BD = row[3]

            record.append(objectID)
            sandPerc.append(sand)
            clayPerc.append(clay)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Manrique and Jones (1991) - Sand, Clay, BD
        if sandPerc[x] >= 75.0:
            WC_33kPa = 0.73426 - (sandPerc[x] * 0.00145) - (BDg_cm3[x] * 0.29176)
        else:
            WC_33kPa = 0.5784 + (clayPerc[x] * 0.002227) - (BDg_cm3[x] * 0.28438)

        WC_1500kPa = 0.02413 + (clayPerc[x] * 0.00373)

        outValues = [WC_33kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_33kPaArray.append(WC_33kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_33kPaArray[recordNum]
            row[2] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")

    results = []
    results.append(warningArray)
    results.append(WC_33kPaArray)
    results.append(WC_1500kPaArray)

    return results

def vanDenBerg_1997(outputFolder, outputShp, carbonConFactor, carbContent):

    log.info('Calculating water content at points using van Den Berg et al. (1997)')

    PTFInfo = PTFdatabase.checkPTF("vanDenBerg_1997")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Returns these arrays
    warningArray = []
    WC_10kPaArray = []
    WC_1500kPaArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: Silt, clay, OC
    if carbContent == 'OC':
        reqFields = [OIDField, "Silt", "Clay", "OC", "BD"]
        carbonConFactor = 1.0

    elif carbContent == 'OM':
        reqFields = [OIDField, "Silt", "Clay", "OM", "BD"]
                        
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    siltPerc = []
    clayPerc = []
    carbPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            silt = row[1]
            clay = row[2]
            carbon = row[3]
            BD = row[4]

            record.append(objectID)
            siltPerc.append(silt)
            clayPerc.append(clay)
            carbPerc.append(carbon)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkCarbon(carbPerc[x], carbContent, record[x])
        warningFlag = checks_PTFs.checkValue("Silt", siltPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using van Den Berg et al. (1997) - Silt, Clay, OC, BD
        WC_10kPa = (10.88 + (0.347 * clayPerc[x]) + (0.211 * siltPerc[x]) + (1.756 * carbPerc[x]*float(carbonConFactor))) * 10**(-2)
        WC_1500kPa = ((0.334 * clayPerc[x] * BDg_cm3[x]) + (0.104 * siltPerc[x] * BDg_cm3[x])) * 10**(-2)

        outValues = [WC_10kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_10kPaArray.append(WC_10kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_10kPaArray[recordNum]
            row[2] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")
    
    results = []
    results.append(warningArray)
    results.append(WC_10kPaArray)
    results.append(WC_1500kPaArray)

    return results

def TomasellaHodnett_1998(outputFolder, outputShp, carbonConFactor, carbContent):

    log.info('Calculating water content at points using Tomasella and Hodnett (1998)')

    PTFInfo = PTFdatabase.checkPTF("TomasellaHodnett_1998")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Returns these arrays
    warningArray = []    
    WC_0kPaArray = []
    WC_1kPaArray = []
    WC_3kPaArray = []
    WC_6kPaArray = []
    WC_10kPaArray = []
    WC_33kPaArray = []
    WC_100kPaArray = []
    WC_500kPaArray = []
    WC_1500kPaArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: Silt, clay, OC
    if carbContent == 'OC':
        reqFields = [OIDField, "Silt", "Clay", "OC"]
        carbonConFactor = 1.0                   

    elif carbContent == 'OM':
        reqFields = [OIDField, "Silt", "Clay", "OM"]
                        
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    siltPerc = []
    clayPerc = []
    carbPerc = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            silt = row[1]
            clay = row[2]
            carbon = row[3]

            record.append(objectID)
            siltPerc.append(silt)
            clayPerc.append(clay)
            carbPerc.append(carbon)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkCarbon(carbPerc[x], carbContent, record[x])
        warningFlag = checks_PTFs.checkValue("Silt", siltPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Tomasella and Hodnett (1998) - Silt, Clay, OC
        WC_0kPa = 0.01 * ((2.24 * carbPerc[x]*float(carbonConFactor)) + (0.298 * siltPerc[x]) + (0.159 * clayPerc[x]) + 37.937)
        WC_1kPa = 0.01 * ((0.53 * siltPerc[x]) + (0.255 * clayPerc[x]) + 23.839)
        WC_3kPa = 0.01 * ((0.552 * siltPerc[x]) + (0.262 * clayPerc[x]) + 18.495)
        WC_6kPa = 0.01 * ((0.576 * siltPerc[x]) + (0.3 * clayPerc[x]) + 12.333)
        WC_10kPa = 0.01 * ((0.543 * siltPerc[x]) + (0.321 * clayPerc[x]) + 9.806)
        WC_33kPa = 0.01 * ((0.426 * siltPerc[x]) + (0.404 * clayPerc[x]) + 4.046)
        WC_100kPa = 0.01 * ((0.369 * siltPerc[x]) + (0.351 * clayPerc[x]) + 3.198)
        WC_500kPa = 0.01 * ((0.258 * siltPerc[x]) + (0.361 * clayPerc[x]) + 1.567)
        WC_1500kPa = 0.01 * ((0.15 * siltPerc[x]) + (0.396 * clayPerc[x]) + 0.91)

        outValues = [WC_0kPa, WC_1kPa, WC_3kPa, WC_6kPa, WC_10kPa, WC_33kPa, WC_100kPa, WC_500kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_0kPaArray.append(WC_0kPa)
        WC_1kPaArray.append(WC_1kPa)
        WC_3kPaArray.append(WC_3kPa)
        WC_6kPaArray.append(WC_6kPa)
        WC_10kPaArray.append(WC_10kPa)
        WC_33kPaArray.append(WC_33kPa)
        WC_100kPaArray.append(WC_100kPa)
        WC_500kPaArray.append(WC_500kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write results back to the shapefile

    # Add fields
    arcpy.AddField_management(outputShp, "warning", "TEXT")
    arcpy.AddField_management(outputShp, "WC_0kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_1kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_3kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_6kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_500kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

    outputFields = ["warning", "WC_0kPa", "WC_1kPa", "WC_3kPa", "WC_6kPa", "WC_10kPa", "WC_33kPa", "WC_100kPa", "WC_500kPa", "WC_1500kPa"]
    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_0kPaArray[recordNum]
            row[2] = WC_1kPaArray[recordNum]
            row[3] = WC_3kPaArray[recordNum]
            row[4] = WC_6kPaArray[recordNum]
            row[5] = WC_10kPaArray[recordNum]
            row[6] = WC_33kPaArray[recordNum]
            row[7] = WC_100kPaArray[recordNum]
            row[8] = WC_500kPaArray[recordNum]
            row[9] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")

    results = []
    results.append(warningArray)
    results.append(WC_0kPaArray)
    results.append(WC_1kPaArray)
    results.append(WC_3kPaArray)
    results.append(WC_6kPaArray)
    results.append(WC_10kPaArray)
    results.append(WC_33kPaArray)
    results.append(WC_100kPaArray)
    results.append(WC_500kPaArray)
    results.append(WC_1500kPaArray)

    return results

def Reichert_2009_OM(outputFolder, outputShp, carbonConFactor, carbContent):

    log.info('Calculating water content at points using Reichert et al. (2009) - Sand, silt, clay, OM, BD')

    PTFInfo = PTFdatabase.checkPTF("Reichert_2009_OM")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Returns these arrays
    warningArray = []    
    WC_6kPaArray = []
    WC_10kPaArray = []
    WC_33kPaArray = []
    WC_100kPaArray = []
    WC_500kPaArray = []
    WC_1500kPaArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: Sand, silt, clay, OM, and BD
    if carbContent == 'OC':
        reqFields = [OIDField, "Sand", "Silt", "Clay", "OC", "BD"]

    elif carbContent == 'OM':
        reqFields = [OIDField, "Sand", "Silt", "Clay", "OM", "BD"]
        carbonConFactor = 1.0
                        
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    siltPerc = []
    clayPerc = []
    carbPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            silt = row[2]
            clay = row[3]
            carbon = row[4]
            BD = row[5]

            record.append(objectID)
            sandPerc.append(sand)
            siltPerc.append(silt)
            clayPerc.append(clay)
            carbPerc.append(carbon)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkSSC(sandPerc[x], siltPerc[x], clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkCarbon(carbPerc[x], carbContent, record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Reichert et al. (2009) (1) - Sand, Silt, Clay, OM, BD
        WC_6kPa = BDg_cm3[x] * (0.415 + (0.26 * 10**(-2) * (clayPerc[x] + siltPerc[x])) + (0.61 * 10**(-2) * carbPerc[x]*float(carbonConFactor)) - 0.207 * BDg_cm3[x])
        WC_10kPa = BDg_cm3[x] * (0.268 + (0.05 * 10**(-2) * clayPerc[x]) + (0.24 * 10**(-2) * (clayPerc[x] + siltPerc[x])) + (0.85 * 10**(-2) * carbPerc[x]*float(carbonConFactor)) - (0.127 * BDg_cm3[x]))
        WC_33kPa = BDg_cm3[x] * (0.106 + (0.29 * 10**(-2) * (clayPerc[x] + siltPerc[x])) + (0.93 * 10**(-2) * carbPerc[x]*float(carbonConFactor)) - (0.048 * BDg_cm3[x]))
        WC_100kPa = BDg_cm3[x] * (0.102 + (0.23 * 10**(-2) * (clayPerc[x] + siltPerc[x])) - (0.08 * 10**(-2) * (siltPerc[x] + sandPerc[x])) + (1.08 * 10**(-2) * carbPerc[x]*float(carbonConFactor)))
        WC_500kPa = BDg_cm3[x] * (0.268 - (0.11 * 10**(-2) * siltPerc[x]) - (0.31 * 10**(-2) * sandPerc[x]) + (1.28 *  10**(-2) * carbPerc[x]*float(carbonConFactor)) + (0.031 * BDg_cm3[x]))
        WC_1500kPa = BDg_cm3[x] * (-0.04 + (0.15 * 10**(-2) * clayPerc[x]) + (0.17 * 10**(-2) * (clayPerc[x] + siltPerc[x])) + (0.91 * 10**(-2)* carbPerc[x]*float(carbonConFactor)) + (0.026 * BDg_cm3[x]))

        outValues = [WC_6kPa, WC_10kPa, WC_33kPa, WC_100kPa, WC_500kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_6kPaArray.append(WC_6kPa)
        WC_10kPaArray.append(WC_10kPa)
        WC_33kPaArray.append(WC_33kPa)
        WC_100kPaArray.append(WC_100kPa)
        WC_500kPaArray.append(WC_500kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]            
            row[1] = WC_6kPaArray[recordNum]
            row[2] = WC_10kPaArray[recordNum]
            row[3] = WC_33kPaArray[recordNum]
            row[4] = WC_100kPaArray[recordNum]
            row[5] = WC_500kPaArray[recordNum]
            row[6] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")
    
    results = []
    results.append(warningArray)    
    results.append(WC_6kPaArray)
    results.append(WC_10kPaArray)
    results.append(WC_33kPaArray)
    results.append(WC_100kPaArray)
    results.append(WC_500kPaArray)
    results.append(WC_1500kPaArray)

    return results

def Reichert_2009(outputFolder, outputShp):

    log.info('Calculating water content at points using Reichert et al. (2009) - Sand, silt, clay, BD')

    PTFInfo = PTFdatabase.checkPTF("Reichert_2009")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Returns these arrays
    warningArray = []
    WC_10kPaArray = []
    WC_33kPaArray = []
    WC_1500kPaArray = []   

    # Requirements: Sand, silt, clay, and BD                
    reqFields = [OIDField, "Sand", "Silt", "Clay", "BD"]           
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    siltPerc = []
    clayPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            silt = row[2]
            clay = row[3]
            BD = row[4]

            record.append(objectID)
            sandPerc.append(sand)
            siltPerc.append(silt)
            clayPerc.append(clay)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkSSC(sandPerc[x], siltPerc[x], clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Reichert et al. (2009) (2)- Sand, Silt, Clay, BD
        WC_10kPa =  BDg_cm3[x] * (0.037 + (0.38 * 10**(-2) * (clayPerc[x] + siltPerc[x])))
        WC_33kPa = BDg_cm3[x] * (0.366 - (0.34 * 10**(-2) * sandPerc[x]))
        WC_1500kPa = BDg_cm3[x] * (0.236 + (0.045 * 10**(-2) * clayPerc[x]) - (0.21 * 10**(-2) * sandPerc[x]))

        outValues = [WC_10kPa, WC_33kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_10kPaArray.append(WC_10kPa)
        WC_33kPaArray.append(WC_33kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_10kPaArray[recordNum]
            row[2] = WC_33kPaArray[recordNum]
            row[3] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")
    
    results = []
    results.append(warningArray)
    results.append(WC_10kPaArray)
    results.append(WC_33kPaArray)
    results.append(WC_1500kPaArray)

    return results

def Botula_2013(outputFolder, outputShp):

    log.info('Calculating water content at points using Botula-Manyala (2013)')

    PTFInfo = PTFdatabase.checkPTF("Botula_2013")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Returns these arrays
    warningArray = []
    WC_1kPaArray = []
    WC_3kPaArray = []
    WC_6kPaArray = []
    WC_10kPaArray = []
    WC_20kPaArray = []
    WC_33kPaArray = []
    WC_100kPaArray = []
    WC_1500kPaArray = []

    # Requirements: Sand, clay, and BD                
    reqFields = [OIDField, "Sand", "Clay", "BD"]           
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    clayPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            clay = row[2]
            BD = row[3]

            record.append(objectID)
            sandPerc.append(sand)
            clayPerc.append(clay)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Botula Manyala (2013) - Sand, Clay, BD
        WC_1kPa = (67.228 + (0.089 * clayPerc[x]) - (20.057* BDg_cm3[x])) * 10**(-2)
        WC_3kPa = (48.080 - (0.081 * sandPerc[x]) + (0.067 * clayPerc[x]) -  (6.344 * BDg_cm3[x])) * 10**(-2)
        WC_6kPa =  (44.196 -  (0.252* sandPerc[x])) * 10**(-2)
        WC_10kPa  = (43.520 -  (0.296* sandPerc[x])) * 10**(-2)
        WC_20kPa = (42.302 -  (0.344 * sandPerc[x])) * 10**(-2)        
        WC_33kPa = (41.929 -  (0.349* sandPerc[x])) * 10**(-2)        
        WC_100kPa  = (26.478 -  (0.276* sandPerc[x]) + (0.091* clayPerc[x]) + (4.720* BDg_cm3[x])) * 10**(-2)
        WC_1500kPa = (8.405 -  (0.159* sandPerc[x]) + (0.207 * clayPerc[x]) + (7.789** BDg_cm3[x])) * 10**(-2)

        outValues = [WC_1kPa, WC_3kPa, WC_6kPa, WC_10kPa, WC_20kPa, WC_33kPa, WC_100kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_1kPaArray.append(WC_1kPa)
        WC_3kPaArray.append(WC_3kPa)
        WC_6kPaArray.append(WC_6kPa)
        WC_10kPaArray.append(WC_10kPa)
        WC_20kPaArray.append(WC_20kPa)
        WC_33kPaArray.append(WC_33kPa)
        WC_100kPaArray.append(WC_100kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_1kPaArray[recordNum]
            row[2] = WC_3kPaArray[recordNum]
            row[3] = WC_6kPaArray[recordNum]
            row[4] = WC_10kPaArray[recordNum]
            row[5] = WC_20kPaArray[recordNum]
            row[6] = WC_33kPaArray[recordNum]
            row[7] = WC_100kPaArray[recordNum]
            row[8] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")

    results = []
    results.append(warningArray)
    results.append(WC_1kPaArray)
    results.append(WC_3kPaArray)
    results.append(WC_6kPaArray)
    results.append(WC_10kPaArray)
    results.append(WC_20kPaArray)
    results.append(WC_33kPaArray)
    results.append(WC_100kPaArray)
    results.append(WC_1500kPaArray)

    return results

def ShwethaVarija_2013(outputFolder, outputShp):

    log.info('Calculating water content at points using Shwetha and Varija (2013)')

    PTFInfo = PTFdatabase.checkPTF("ShwethaVarija_2013")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Returns these arrays
    warningArray = []
    WC_33kPaArray = []
    WC_100kPaArray = []
    WC_300kPaArray = []
    WC_500kPaArray = []
    WC_1000kPaArray = []
    WC_1500kPaArray = []

    # Requirements: Sand, silt, clay, and BD
    reqFields = [OIDField, "Sand", "Silt", "Clay","BD"]           
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    siltPerc = []
    clayPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            silt = row[2]
            clay = row[3]
            BD = row[4]

            record.append(objectID)
            sandPerc.append(sand)
            siltPerc.append(silt)
            clayPerc.append(clay)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkSSC(sandPerc[x], siltPerc[x], clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Shwetha and Varija (2013) - Sand, Silt, Clay, BD
        WC_33kPa = - 4.263 + (0.00194 * sandPerc[x]) + (0.02839 * siltPerc[x]) + (5.568 * BDg_cm3[x]) - (0.00005 * sandPerc[x]**2) - (0.00011 * sandPerc[x] * siltPerc[x]) + (0.00106 * sandPerc[x] * BDg_cm3[x]) - (0.00005 * siltPerc[x]**2) - (0.01158 * siltPerc[x] * BDg_cm3[x]) - (1.78 * BDg_cm3[x]**2)
        WC_100kPa = - 2.081 - (0.00776 * sandPerc[x]) + (0.00589 * siltPerc[x]) + (3.452 * BDg_cm3[x]) - (0.00007 * sandPerc[x]**2)  - (0.00018 * sandPerc[x] * siltPerc[x]) + (0.01047 * sandPerc[x] * BDg_cm3[x]) + (0.0000003 * siltPerc[x]**2) + (0.00402 * siltPerc[x] * BDg_cm3[x]) - (1.4 * BDg_cm3[x]**2)
        WC_300kPa  = - 2.029 - (0.00039 * sandPerc[x]) + (0.02393 * siltPerc[x]) + (2.859 * BDg_cm3[x]) - (0.00007 * sandPerc[x]**2) - (0.000178 * sandPerc[x] * siltPerc[x]) + (0.00614 * sandPerc[x] * BDg_cm3[x]) - (0.000150 * siltPerc[x]**2) - (0.00352 * siltPerc[x] * BDg_cm3[x]) - (1.092 * BDg_cm3[x]**2)
        WC_500kPa = - 1.079 + (0.01539 * sandPerc[x]) + (0.02272 * siltPerc[x]) + (0.961 * BDg_cm3[x]) - (0.00009 * sandPerc[x]**2) - (0.00021 * sandPerc[x] * siltPerc[x]) - (0.00275 * sandPerc[x] * BDg_cm3[x]) - (0.000171 * siltPerc[x]**2) - (0.00146 * siltPerc[x] * BDg_cm3[x]) - (0.287 * BDg_cm3[x]**2)
        WC_1000kPa = - 2.488 - (0.01215 * sandPerc[x]) + (0.00750 * siltPerc[x]) + (4.051 * BDg_cm3[x]) - (0.00007 * sandPerc[x]**2) - (0.00016 * sandPerc[x] * siltPerc[x]) + (0.01333 * sandPerc[x] * BDg_cm3[x]) + (0.00002 * siltPerc[x]**2) + (0.00131 * siltPerc[x] * BDg_cm3[x]) - (1.633 * BDg_cm3[x]**2)
        WC_1500kPa = - 1.076 - (0.00234 * sandPerc[x]) - (0.00334 * siltPerc[x]) + (1.920 * BDg_cm3[x]) - (0.00003 * sandPerc[x]**2) + (0.00003 * sandPerc[x] * siltPerc[x]) + (0.00101 * sandPerc[x] * BDg_cm3[x]) + (0.00006 * siltPerc[x]**2) - (0.00077 * siltPerc[x] * BDg_cm3[x]) - (0.666 * BDg_cm3[x]**2)

        outValues = [WC_33kPa, WC_100kPa, WC_300kPa, WC_500kPa, WC_1000kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_33kPaArray.append(WC_33kPa)
        WC_100kPaArray.append(WC_100kPa)
        WC_300kPaArray.append(WC_300kPa)
        WC_500kPaArray.append(WC_500kPa)
        WC_1000kPaArray.append(WC_1000kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_33kPaArray[recordNum]
            row[2] = WC_100kPaArray[recordNum]
            row[3] = WC_300kPaArray[recordNum]
            row[4] = WC_500kPaArray[recordNum]
            row[5] = WC_1000kPaArray[recordNum]
            row[6] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")
    
    results = []
    results.append(warningArray)
    results.append(WC_33kPaArray)
    results.append(WC_100kPaArray)
    results.append(WC_300kPaArray)
    results.append(WC_500kPaArray)
    results.append(WC_1000kPaArray)
    results.append(WC_1500kPaArray)

    return results

def Dashtaki_2010(outputFolder, outputShp):

    log.info('Calculating water content at points using Dashtaki et al. (2010)')

    PTFInfo = PTFdatabase.checkPTF("Dashtaki_2010_point")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Returns these arrays
    warningArray = []
    WC_10kPaArray = []
    WC_30kPaArray = []
    WC_100kPaArray = []
    WC_300kPaArray = []
    WC_500kPaArray = []
    WC_1500kPaArray = []

    # Requirements: Sand, silt, clay, and BD
    reqFields = [OIDField, "Sand", "Silt", "Clay","BD"]           
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    siltPerc = []
    clayPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            silt = row[2]
            clay = row[3]
            BD = row[4]

            record.append(objectID)
            sandPerc.append(sand)
            siltPerc.append(silt)
            clayPerc.append(clay)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkSSC(sandPerc[x], siltPerc[x], clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Dashtaki et al. (2010) - Sand, Silt, Clay, BD
        WC_10kPa = (34.3 - (0.38 * sandPerc[x]) + (12.4 * BDg_cm3[x])) * 10**(-2) 
        WC_30kPa = (14.1 - (0.283 * sandPerc[x]) + (17.1 * BDg_cm3[x])) * 10**(-2) 
        WC_100kPa = (12.2 - (0.31 * sandPerc[x]) + (14.3 * BDg_cm3[x])) * 10**(-2)  
        WC_300kPa = (12 - (0.22 * sandPerc[x]) + (8.41 * BDg_cm3[x]) + (4.3 * clayPerc[x]/siltPerc[x])) * 10**(-2)  
        WC_500kPa = (9.4 + (0.32 * clayPerc[x])) * 10**(-2)  
        WC_1500kPa = (6.2 + (0.33 * clayPerc[x])) * 10**(-2)

        outValues = [WC_10kPa, WC_30kPa, WC_100kPa, WC_300kPa, WC_500kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_10kPaArray.append(WC_10kPa)
        WC_30kPaArray.append(WC_30kPa)
        WC_100kPaArray.append(WC_100kPa)
        WC_300kPaArray.append(WC_300kPa)
        WC_500kPaArray.append(WC_500kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_10kPaArray[recordNum]
            row[2] = WC_30kPaArray[recordNum]
            row[3] = WC_100kPaArray[recordNum]
            row[4] = WC_300kPaArray[recordNum]
            row[5] = WC_500kPaArray[recordNum]
            row[6] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")

    results = []
    results.append(warningArray)
    results.append(WC_10kPaArray)
    results.append(WC_30kPaArray)
    results.append(WC_100kPaArray)
    results.append(WC_300kPaArray)
    results.append(WC_500kPaArray)
    results.append(WC_1500kPaArray)

    return results

def Santra_2018_OC(outputFolder, outputShp, carbonConFactor, carbContent):

    log.info('Calculating water content at points using Santra et al. (2018)')

    PTFInfo = PTFdatabase.checkPTF("Santra_2018_OC")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Returns these arrays
    warningArray = []
    WC_33kPaArray = []
    WC_1500kPaArray = []

    # Requirements: Sand, Clay, OC, and BD
    if carbContent == 'OC':
        reqFields = [OIDField, "Sand", "Clay", "OC", "BD"]
        carbonConFactor = 1.0

    elif carbContent == 'OM':
        reqFields = [OIDField, "Sand", "Clay", "OM", "BD"]
                          
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    clayPerc = []
    carbPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            clay = row[2]
            carbon = row[3]
            BD = row[4]

            record.append(objectID)
            sandPerc.append(sand)
            clayPerc.append(clay)
            carbPerc.append(carbon)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkCarbon(carbPerc[x], carbContent, record[x])
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Santra et al. (2018) - Sand, Clay, OC, BD
        WC_33kPa = (24.98 - (0.205 * sandPerc[x]) + (0.28 * clayPerc[x]) + (0.192 * carbPerc[x]*float(carbonConFactor) * 10)) * BDg_cm3[x] * 10**(-2)
        WC_1500kPa = (4.341 + (0.435 * clayPerc[x]) - (0.00431 * sandPerc[x] * clayPerc[x]) + (0.00190 * sandPerc[x] * carbPerc[x]*float(carbonConFactor) * 10) + (0.00169 * clayPerc[x] * carbPerc[x]*float(carbonConFactor) * 10)) * BDg_cm3[x] * 10**(-2)

        outValues = [WC_33kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_33kPaArray.append(WC_33kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_33kPaArray[recordNum]
            row[2] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")
    
    results = []
    results.append(warningArray)
    results.append(WC_33kPaArray)
    results.append(WC_1500kPaArray)

    return results

def Santra_2018(outputFolder, outputShp):

    log.info('Calculating water content at points using Santra et al. (2018)')

    PTFInfo = PTFdatabase.checkPTF("Santra_2018_OC")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Returns these arrays
    warningArray = []
    WC_33kPaArray = []
    WC_1500kPaArray = []

    # Requirements: Sand, Clay, and BD

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: Sand, Clay, OC, and BD
    reqFields = [OIDField, "Sand", "Clay", "BD"]
                       
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    clayPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            clay = row[2]
            BD = row[3]

            record.append(objectID)
            sandPerc.append(sand)
            clayPerc.append(clay)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Santra et al. (2018) - Sand, Clay, BD
        WC_33kPa = (27.80 - (0.231 * sandPerc[x]) + (0.262 * clayPerc[x])) * BDg_cm3[x] * 10**(-2)
        WC_1500kPa = (10.06 - (0.0847 * sandPerc[x]) + (0.303 * clayPerc[x]) - (0.00186 * sandPerc[x] * clayPerc[x])) * BDg_cm3[x] * 10**(-2)

        outValues = [WC_33kPa, WC_1500kPa]
        checks_PTFs.checkNegOutput(outValues, x)

        WC_33kPaArray.append(WC_33kPa)
        WC_1500kPaArray.append(WC_1500kPa)

    # Write results back to the shapefile
    # Write fields to output shapefile
    common.writeFields(outputShp, PTFFields)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, PTFFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]
            row[1] = WC_33kPaArray[recordNum]
            row[2] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Results written to the output shapefile inside the output folder")
    
    results = []
    results.append(warningArray)
    results.append(WC_33kPaArray)
    results.append(WC_1500kPaArray)

    return results
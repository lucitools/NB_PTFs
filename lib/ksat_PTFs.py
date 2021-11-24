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

def Cosby_1984(outputFolder, outputShp):

    # Returns these arrays
    warningArray = []
    K_satArray = []

    log.info('Calculating saturated hydraulic conductivity using Cosby et al. (1984)')

    PTFInfo = PTFdatabase.checkPTF("Cosby_1984")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Requirements: sand and clay

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    reqFields = [OIDField, "Sand", "Clay"]

    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    clayPerc = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            clay = row[2]

            record.append(objectID)
            sandPerc.append(sand)
            clayPerc.append(clay)

    for x in range(0, len(record)):
        # Data checks
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningArray.append(warningFlag)

        K_sat = 25.4 * 10**(-0.6 + (0.0126 * sandPerc[x]) - (0.0064 * clayPerc[x]))

        checks_PTFs.checkValue("Ksat", K_sat, record[x])

        K_satArray.append(K_sat)

    return warningArray, K_satArray

def Puckett_1985(outputFolder, outputShp):

    # Returns these arrays
    warningArray = []
    K_satArray = []

    log.info('Calculating saturated hydraulic conductivity using Puckett et al. (1985)')

    PTFInfo = PTFdatabase.checkPTF("Puckett_1985")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Requirements: Clay

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    reqFields = [OIDField, "Clay"]

    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    clayPerc = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            clay = row[1]

            record.append(objectID)
            clayPerc.append(clay)

    for x in range(0, len(record)):
        # Data checks
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningArray.append(warningFlag)

        K_sat = 156.96 * math.exp(-0.1975 * clayPerc[x])

        checks_PTFs.checkValue("Ksat", K_sat, record[x])

        K_satArray.append(K_sat)

    return warningArray, K_satArray

def Jabro_1992(outputFolder, outputShp):

    # Returns these arrays
    warningArray = []
    K_satArray = []

    log.info('Calculating saturated hydraulic conductivity using Jabro (1992)')

    PTFInfo = PTFdatabase.checkPTF("Jabro_1992")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Requirements: sand and clay

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    reqFields = [OIDField, "Silt", "Clay", "BD"]

    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    siltPerc = []
    clayPerc = []
    BDg_cm3 = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            silt = row[1]
            clay = row[2]
            BD = row[3]

            record.append(objectID)
            siltPerc.append(silt)
            clayPerc.append(clay)
            BDg_cm3.append(BD)

    for x in range(0, len(record)):
        # Data checks
        warningFlag = checks_PTFs.checkValue("Silt", siltPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        K_sat = 10**(9.56 - (0.81 * math.log(siltPerc[x], 10.0)) - (1.09 * math.log(clayPerc[x], 10.0)) - (4.64 * BDg_cm3[x])) * 10.0

        checks_PTFs.checkValue("Ksat", K_sat, record[x])

        K_satArray.append(K_sat)

    return warningArray, K_satArray

def CampbellShiozawa_1994(outputFolder, outputShp):

    # Returns these arrays
    warningArray = []
    K_satArray = []

    log.info('Calculating saturated hydraulic conductivity using Campbell and Shiozawa (1994)')

    PTFInfo = PTFdatabase.checkPTF("CampbellShiozawa_1994")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Requirements: silt and clay

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    reqFields = [OIDField, "Silt", "Clay"]

    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    siltPerc = []
    clayPerc = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            silt = row[1]
            clay = row[2]

            record.append(objectID)
            siltPerc.append(silt)
            clayPerc.append(clay)

    for x in range(0, len(record)):
        # Data checks
        warningFlag = checks_PTFs.checkValue("Silt", siltPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningArray.append(warningFlag)

        K_sat = 54.0 * math.exp((- 0.07 * siltPerc[x]) - (0.167 * clayPerc[x]))

        checks_PTFs.checkValue("Ksat", K_sat, record[x])

        K_satArray.append(K_sat)

    return warningArray, K_satArray

def FerrerJulia_2004_1(outputFolder, outputShp):

    # Returns these arrays
    warningArray = []
    K_satArray = []

    log.info('Calculating saturated hydraulic conductivity using Ferrer Julia et al. (2004) - Sand')

    PTFInfo = PTFdatabase.checkPTF("FerrerJulia_2004_1")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Requirements: sand

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    reqFields = [OIDField, "Sand"]

    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]

            record.append(objectID)
            sandPerc.append(sand)

    for x in range(0, len(record)):
        # Data checks
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningArray.append(warningFlag)

        K_sat = 0.920 * math.exp(0.0491 * sandPerc[x])

        checks_PTFs.checkValue("Ksat", K_sat, record[x])

        K_satArray.append(K_sat)

    return warningArray, K_satArray

def FerrerJulia_2004_2(outputFolder, outputShp, carbonConFactor, carbContent):

    # Returns these arrays
    warningArray = []
    K_satArray = []

    log.info('Calculating saturated hydraulic conductivity using Ferrer Julia et al. (2004) - Sand, clay, OM')

    PTFInfo = PTFdatabase.checkPTF("FerrerJulia_2004_2")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: sand, clay, OM, BD
    if carbContent == 'OC':
        reqFields = [OIDField, "Sand", "Clay", "OC", "BD"]
        carbonConFactor = 1.724

    elif carbContent == 'OM':
        reqFields = [OIDField, "Sand", "Clay", "OM", "BD"]
        carbonConFactor = 1.0
        
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

        K_sat = - 4.994 + (0.56728 * sandPerc[x]) - (0.131 * clayPerc[x]) - (0.0127 * carbPerc[x]*float(carbonConFactor))

        checks_PTFs.checkValue("Ksat", K_sat, record[x])

        K_satArray.append(K_sat)

    return warningArray, K_satArray

def Ahuja_1989(outputFolder, outputShp):

    # Returns these arrays
    warningArray = []
    K_satArray = []

    log.info('Calculating saturated hydraulic conductivity using Ahuja et al. (1989)')

    PTFInfo = PTFdatabase.checkPTF("Ahuja_1989")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: WC @ Sat and WC @ FC
    reqFields = [OIDField, "wc_satCalc", "wc_fcCalc"]

    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    WC_satArray = []
    WC_FCArray = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            WC_sat = row[1]
            WC_FC = row[2]

            record.append(objectID)
            WC_satArray.append(WC_sat)
            WC_FCArray.append(WC_FC)

    for x in range(0, len(record)):
        # Data checks
        warningFlag = checks_PTFs.checkValue("WC at sat", WC_satArray[x], record[x])
        warningFlag = checks_PTFs.checkValue("WC at FC", WC_FCArray[x], record[x])
        warningArray.append(warningFlag)

        Eff_porosity = WC_satArray[x] - WC_FCArray[x]
        K_sat = 7645.0 * Eff_porosity **3.29

        checks_PTFs.checkValue("Ksat", K_sat, record[x])
        
        K_satArray.append(K_sat)

    return warningArray, K_satArray

def MinasnyMcBratney_2000(outputFolder, outputShp):

    # Returns these arrays
    warningArray = []
    K_satArray = []

    log.info('Calculating saturated hydraulic conductivity using Minasny and McBratney (2000)')

    PTFInfo = PTFdatabase.checkPTF("MinasnyMcBratney_2000")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: WC @ Sat and WC @ FC
    reqFields = [OIDField, "wc_satCalc", "wc_fcCalc"]

    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    WC_satArray = []
    WC_FCArray = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            WC_sat = row[1]
            WC_FC = row[2]

            record.append(objectID)
            WC_satArray.append(WC_sat)
            WC_FCArray.append(WC_FC)

    for x in range(0, len(record)):
        # Data checks
        warningFlag = checks_PTFs.checkValue("WC at sat", WC_satArray[x], record[x])
        warningFlag = checks_PTFs.checkValue("WC at FC", WC_FCArray[x], record[x])
        warningArray.append(warningFlag)

        Eff_porosity = WC_satArray[x] - WC_FCArray[x]
        K_sat = 23190.55 * Eff_porosity ** 3.66

        checks_PTFs.checkValue("Ksat", K_sat, record[x])
        
        K_satArray.append(K_sat)

    return warningArray, K_satArray

def Brakensiek_1984(outputFolder, outputShp):

    # Returns these arrays
    warningArray = []
    K_satArray = []

    log.info('Calculating saturated hydraulic conductivity using Brakensiek et al. (1984)')

    PTFInfo = PTFdatabase.checkPTF("Brakensiek_1984")
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures
    PTFFields = PTFInfo.PTFFields

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: Clay, sand, WC @ Sat
    reqFields = [OIDField, "Sand", "Clay", "wc_satCalc"]

    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    clayPerc = []
    WC_satArray = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            clay = row[2]
            WC_sat = row[3]

            record.append(objectID)
            sandPerc.append(sand)
            clayPerc.append(clay)
            WC_satArray.append(WC_sat)

    for x in range(0, len(record)):
        # Data checks
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("WC at sat", WC_satArray[x], record[x])
        warningArray.append(warningFlag)

        K_sat = 10 * math.exp((19.52348 * WC_satArray[x]) - 8.96847 - (0.028212 * clayPerc[x]) + (0.00018107 * sandPerc[x]**2) - (0.0094125 * clayPerc[x]**2) - (8.395215 * WC_satArray[x]**2) + (0.077718 * sandPerc[x] * WC_satArray[x]) - (0.00298 * sandPerc[x]**2 * WC_satArray[x]**2) - (0.019492 * clayPerc[x]**2 * WC_satArray[x]**2) + (0.0000173 * sandPerc[x]**2 * clayPerc[x]) + (0.02733 * clayPerc[x]**2 * WC_satArray[x]) + (0.001434 * sandPerc[x]**2 * WC_satArray[x]) - (0.0000035 * clayPerc[x]**2 * sandPerc[x]))

        checks_PTFs.checkValue("Ksat", K_sat, record[x])

        K_satArray.append(K_sat)

    return warningArray, K_satArray
'''
bc_PTFs: contains all the PTF functions for calculating BC parameters
'''

import sys
import os
import configuration
import arcpy
import math
import NB_PTFs.lib.log as log
import NB_PTFs.lib.common as common
import NB_PTFs.lib.checks_PTFs as checks_PTFs
from NB_PTFs.lib.external import six # Python 2/3 compatibility module

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log, common, checks_PTFs])

def Cosby_1984_SandC_BC(outputShp, PTFOption):
    
    log.info("Calculating Brooks-Corey using Cosby et al. (1984) - Sand and Clay")

    # Arrays to output
    warningArray = []
    WC_resArray = []
    WC_satArray = []
    lambda_BCArray = []
    hb_BCArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    reqFields = [OIDField, "Sand", "Clay"]
    checks_PTFs.checkInputFields(reqFields, outputShp)

    record = []
    sandPerc = []
    clayPerc = []

    # Required: sand and clay
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
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningArray.append(warningFlag)

        # Calculate values
        WC_res = 0
        WC_sat = 0.489 - (0.00126 * sandPerc[x])
        lambda_BC = 1.0 / (2.91 + (0.159 * clayPerc[x]))

        # Originally in cm
        hb_cm = 10.0 ** (1.88 - (0.013 * sandPerc[x]))
        hb_BC = hb_cm / 10.0 # Convert to kPa

        outValues = [WC_res, WC_sat]
        checks_PTFs.checkNegOutput(outValues, x)

        # Append to arrays
        WC_resArray.append(WC_res)
        WC_satArray.append(WC_sat)
        lambda_BCArray.append(lambda_BC)
        hb_BCArray.append(hb_BC)

    return warningArray, WC_resArray, WC_satArray, lambda_BCArray, hb_BCArray

def Cosby_1984_SSC_BC(outputShp, PTFOption):

    log.info("Calculating Brooks-Corey using Cosby et al. (1984) - Sand, Silt and Clay")

    # Arrays to output
    warningArray = []
    WC_resArray = []
    WC_satArray = []
    lambda_BCArray = []
    hb_BCArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

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

        # Calculate values
        WC_res = 0
        WC_sat = (50.5 - (0.037 * clayPerc[x]) - (0.142 * sandPerc[x])) / 100.0
        lambda_BC = 1.0 / (3.10 + (0.157 * clayPerc[x]) - (0.003 * sandPerc[x]))
        
        # Originally in cm
        hb_cm = 10.0 ** (1.54 - (0.0095 * sandPerc[x]) + (0.0063 * siltPerc[x]))
        hb_BC = hb_cm / 10.0 # Convert to kPa

        outValues = [WC_res, WC_sat]
        checks_PTFs.checkNegOutput(outValues, x)

        # Append to arrays
        WC_resArray.append(WC_res)
        WC_satArray.append(WC_sat)
        lambda_BCArray.append(lambda_BC)
        hb_BCArray.append(hb_BC)

    return warningArray, WC_resArray, WC_satArray, lambda_BCArray, hb_BCArray

def RawlsBrakensiek_1985_BC(outputShp, PTFOption):

    log.info("Calculating Brooks-Corey using Rawls and Brakensiek (1985)")

    # Arrays to output
    warningArray = []
    WC_resArray = []
    lambda_BCArray = []
    hb_BCArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    reqFields = [OIDField, "Sand", "Clay", "WC_sat"]
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
            WCsat = row[3]

            record.append(objectID)
            sandPerc.append(sand)
            clayPerc.append(clay)
            WC_satArray.append(WCsat)

    for x in range(0, len(record)):
        # Data checks
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Input saturation", WC_satArray[x], record[x])
        warningArray.append(warningFlag)

        # Calculate values
        WC_residual = -0.0182482 + (0.00087269 * sandPerc[x]) + (0.00513488 * clayPerc[x]) + (0.02939286 * WC_satArray[x]) - (0.00015395 * clayPerc[x]**2) - (0.0010827 * sandPerc[x] * WC_satArray[x]) - (0.00018233 * clayPerc[x]**2 * WC_satArray[x]**2) + (0.00030703 * clayPerc[x]**2 * WC_satArray[x]) - (0.0023584 * WC_satArray[x]**2 * clayPerc[x])
        
        # Originally in cm
        hb_cm = math.exp(5.3396738 + (0.1845038 * clayPerc[x]) - (2.48394546 * WC_satArray[x]) - (0.00213853 * clayPerc[x]**2) - (0.04356349 * sandPerc[x] * WC_satArray[x]) - (0.61745089 * clayPerc[x] * WC_satArray[x]) + (0.00143598 * sandPerc[x]**2 * WC_satArray[x]**2) - (0.00855375 * clayPerc[x]**2 * WC_satArray[x]**2) - (0.00001282 * sandPerc[x]**2 * clayPerc[x]) + (0.00895359 * clayPerc[x]**2 * WC_satArray[x]) - (0.00072472 * sandPerc[x]**2 * WC_satArray[x]) + (0.0000054 * clayPerc[x]**2 * sandPerc[x]) + (0.50028060 * WC_satArray[x]**2 * clayPerc[x]))
        hb_BC = hb_cm / 10.0 # Convert to kPa

        lambda_BC = math.exp(-0.7842831 + (0.0177544 * sandPerc[x]) - (1.062498 * WC_satArray[x]) - (0.00005304 * sandPerc[x]**2) - (0.00273493 * clayPerc[x]**2) + (1.11134946 * WC_satArray[x]**2) - (0.03088295 * sandPerc[x] * WC_satArray[x])  + (0.00026587 * sandPerc[x]**2 * WC_satArray[x]**2)  - (0.00610522 * clayPerc[x]**2 * WC_satArray[x]**2) - (0.00000235 * sandPerc[x]**2 * clayPerc[x]) + (0.00798746 * clayPerc[x]**2 * WC_satArray[x]) - (0.00674491 * WC_satArray[x]**2 * clayPerc[x]))

        checks_PTFs.checkNegOutput([WC_residual], x)

        WC_resArray.append(WC_residual)
        hb_BCArray.append(hb_BC)
        lambda_BCArray.append(lambda_BC)

    return warningArray, WC_resArray, WC_satArray, lambda_BCArray, hb_BCArray

def CampbellShiozawa_1992_BC(outputShp, PTFOption):

    log.info("Calculating Brooks-Corey using Campbell and Shiozawa (1992)")

    # Arrays to output
    warningArray = []
    WC_resArray = []
    lambda_BCArray = []
    hb_BCArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    reqFields = [OIDField, "Silt", "Clay", "BD", "WC_sat"]
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    siltPerc = []
    clayPerc = []
    BDg_cm3 = []
    WC_satArray = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            silt = row[1]
            clay = row[2]
            BD = row[3]
            WCsat = row[4]

            record.append(objectID)
            siltPerc.append(silt)
            clayPerc.append(clay)
            BDg_cm3.append(BD)
            WC_satArray.append(WCsat)

    dg_CSArray = []
    Sg_CSArray = []
    hes_CSArray = []
    b_CSArray = []

    for x in range(0, len(record)):
        # Data checks
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Silt", siltPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningFlag = checks_PTFs.checkValue("Input saturation", WC_satArray[x], record[x])
        warningArray.append(warningFlag)

        # Calculate values
        WC_residual = 0
        dg_CS = math.exp(-0.8 - (0.0317 * siltPerc[x]) - (0.0761 * clayPerc[x]))
        Sg_CS = (math.exp((0.133 * siltPerc[x]) + (0.477 * clayPerc[x]) - ((math.log(dg_CS))**2)))**0.5
        hes_CS = 0.05/float((math.sqrt(dg_CS)))
        b_CS = (-20.0 * (-hes_CS)) + (0.2 * Sg_CS)
        
        # Originally in cm
        hb_cm = 100.0 * (hes_CS * ((BDg_cm3[x] / 1.3) ** (0.67* b_CS)))
        hb_BC = hb_cm / 10.0 # Convert to kPa

        lambda_BC = 1.0 /float(b_CS)

        checks_PTFs.checkNegOutput([WC_residual], x)

        WC_resArray.append(WC_residual)
        dg_CSArray.append(dg_CS)
        Sg_CSArray.append(Sg_CS)
        hes_CSArray.append(hes_CS)
        b_CSArray.append(b_CS)
        hb_BCArray.append(hb_BC)
        lambda_BCArray.append(lambda_BC)

    return warningArray, WC_resArray, WC_satArray, lambda_BCArray, hb_BCArray

def Saxton_1986_BC(outputShp, PTFOption):

    log.info("Calculating Brooks-Corey using Saxton et al. (1986)")

    # Arrays to output
    warningArray = []
    WC_resArray = []
    WC_satArray = []
    lambda_BCArray = []
    hb_BCArray = []

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

    A_Array = []
    B_Array = []

    for x in range(0, len(record)):
        # Data checks
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningArray.append(warningFlag)

        # Calculate values
        # WC_0kPa = WC_sat
        WC_sat = 0.332 - (7.251 * 10**(-4) * sandPerc[x]) + (0.1276 * math.log(clayPerc[x], 10.0))
        WC_residual = 0
        A_Saxton = 100 * math.exp(-4.396 - (0.0715 * clayPerc[x])- (0.000488 * sandPerc[x]**2) - (0.00004285 * sandPerc[x]**2 * clayPerc[x])) 
        B_Saxton = -3.140 - (0.00222 * clayPerc[x]**2) - (0.00003484 * sandPerc[x]**2 * clayPerc[x])
        hb_BC = A_Saxton * (WC_sat** B_Saxton)  
        lambda_BC = -1.0 / float(B_Saxton)

        checks_PTFs.checkNegOutput([WC_sat, WC_residual], x)

        WC_satArray.append(WC_sat)
        WC_resArray.append(WC_residual)
        A_Array.append(A_Saxton)
        B_Array.append(B_Saxton)
        hb_BCArray.append(hb_BC)
        lambda_BCArray.append(lambda_BC)

    return warningArray, WC_resArray, WC_satArray, lambda_BCArray, hb_BCArray

def SaxtonRawls_2006_BC(outputShp, PTFOption, carbonConFactor, carbContent):

    log.info("Calculating Brooks-Corey using Saxton and Rawls (2006)")

    # Arrays to output
    warningArray = []
    WC_resArray = []
    WC_satArray = []
    lambda_BCArray = []
    hb_BCArray = []
    K_satArray = []

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: sand, clay, and OM
    if carbContent == 'OC':
        reqFields = [OIDField, "Sand", "Clay", "OC", "soilname"]

    elif carbContent == 'OM':
        reqFields = [OIDField, "Sand", "Clay", "OM", "soilname"]
        carbonConFactor = 1.0
    
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    clayPerc = []
    carbPerc = []
    name = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            clay = row[2]
            carbon = row[3]
            recName = row[4]

            record.append(objectID)
            sandPerc.append(sand)
            clayPerc.append(clay)
            carbPerc.append(carbon)
            name.append(recName)

    for x in range(0, len(record)):
        # Data checks
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Carbon", carbPerc[x], record[x])
        warningArray.append(warningFlag)

        # Calculate values
        WC_residual = 0

        WC_33tkPa = (-0.00251 * sandPerc[x]) + (0.00195 * clayPerc[x]) + (0.00011 * carbPerc[x]*float(carbonConFactor)) + (0.0000006 * sandPerc[x] * carbPerc[x]*float(carbonConFactor)) - (0.0000027 * clayPerc[x] * carbPerc[x]*float(carbonConFactor)) + (0.0000452 * sandPerc[x] * clayPerc[x]) + 0.299
        WC_33kPa = (1.283 * (WC_33tkPa)**(2)) + (0.626 * (WC_33tkPa)) - 0.015
        WC_sat_33tkPa = (0.00278 * sandPerc[x]) + (0.00034 * clayPerc[x]) + (0.00022 * carbPerc[x]*float(carbonConFactor)) - (0.0000018 * sandPerc[x] * carbPerc[x]*float(carbonConFactor)) - (0.0000027 * clayPerc[x] * carbPerc[x]*float(carbonConFactor)) - (0.0000584 * sandPerc[x] * clayPerc[x]) + 0.078
        WC_sat_33kPa = 1.636 * WC_sat_33tkPa - 0.107
        
        ## WC_0kPa is now WC_sat
        WC_sat = WC_33kPa + WC_sat_33kPa - (0.00097 * sandPerc[x]) + 0.043                    
        
        WC_1500tkPa = (-0.00024 * sandPerc[x]) + (0.00487 * clayPerc[x]) + (0.00006 * carbPerc[x]*float(carbonConFactor)) + (0.0000005 * sandPerc[x] * carbPerc[x]*float(carbonConFactor)) - (0.0000013 * clayPerc[x] * carbPerc[x]*float(carbonConFactor)) + (0.0000068 * sandPerc[x] * clayPerc[x]) + 0.031
        WC_1500kPa = 1.14 * WC_1500tkPa - 0.02

        # Need checks on WC_33kPa and WC_1500kPa

        wcError = False

        if WC_33kPa < 0.0:
            log.warning('WARNING: water content at 33kPa is negative for ' + str(name[x]))
            log.warning('WARNING: Cannot calculate lambda, setting it to -9999 for error catching')
            wcError = True

        if WC_1500kPa < 0.0:
            log.warning('WARNING: Water content at 1500kPa is negative for ' + str(name[x]))
            log.warning('WARNING: Cannot calculate lambda, setting it to -9999 for error catching')
            wcError = True

        if wcError == True:
            lambda_BC = -9999
            hb_BC = -9999

        else:

            B_SR = (math.log(1500.0) - math.log(33.0)) / (math.log(WC_33kPa) - math.log(WC_1500kPa))
            lambda_BC = 1.0 / float(B_SR)
            hbt_BC = - (0.2167 * sandPerc[x]) - (0.2793 * clayPerc[x])  -  (81.97 * WC_sat_33kPa) + (0.7112 * sandPerc[x] * WC_sat_33kPa)  + (0.0829 * clayPerc[x]  * WC_sat_33kPa) + (0.001405 * sandPerc[x] * clayPerc[x])   + 27.16
            hb_BC = hbt_BC + (0.02 * hbt_BC  ** 2)  - (0.113 * hbt_BC) - 0.7

        # If there is a valid lambda value
        if lambda_BC != -9999:
            K_sat = 1930.0 * ((WC_sat - WC_33kPa)**(3 - lambda_BC)) 
        else:
            # If not valid, set K_sat to -9999
            K_sat = -9999

        WC_resArray.append(WC_residual)
        WC_satArray.append(WC_sat)
        lambda_BCArray.append(lambda_BC)
        hb_BCArray.append(hb_BC)
        K_satArray.append(K_sat)

    # Write K_sat to the output shapefile
    arcpy.AddField_management(outputShp, "K_sat", "DOUBLE", 10, 6)

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, "K_sat") as cursor:
        for row in cursor:
            row[0] = K_satArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    return warningArray, WC_resArray, WC_satArray, lambda_BCArray, hb_BCArray

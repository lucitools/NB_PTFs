'''
vg_PTFs: contains all the PTF functions for calculating VG parameters
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
from NB_PTFs.lib.external import six # Python 2/3 compatibility module

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log, common, checks_PTFs])

def Wosten_1999(outputShp, VGOption, carbonConFactor, carbContent, MVGChoice):

    # Arrays to write to shapefile    
    warningArray = []
    K_satArray = []
    WC_satArray = []
    WC_residualArray = []
    alpha_VGArray = []
    n_VGArray = []
    m_VGArray = []
    l_MvGArray = []

    log.info("Calculating van Genuchten parameters using Wosten et al. (1999)")

    # Requirements: sand, silt, clay, OM, and BD

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    if carbContent == 'OC':
        reqFields = [OIDField, "Sand", "Silt", "Clay", "OC", "BD", "soilname", "texture"]

    elif carbContent == 'OM':
        reqFields = [OIDField, "Sand", "Silt", "Clay", "OM", "BD", "soilname", "texture"]
        carbonConFactor = 1.0

    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    siltPerc = []
    clayPerc = []
    carbPerc = []
    BDg_cm3 = []
    nameArray = []
    textureArray = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            silt = row[2]
            clay = row[3]
            carbon = row[4]
            BD = row[5]
            name = row[6]
            texture = row[7]

            record.append(objectID)
            sandPerc.append(sand)
            siltPerc.append(silt)
            clayPerc.append(clay)
            carbPerc.append(carbon)
            BDg_cm3.append(BD)
            nameArray.append(name)
            textureArray.append(texture)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkSSC(sandPerc[x], siltPerc[x], clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkCarbon(carbPerc[x], carbContent, record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Calculate VG parameters                    
        if clayPerc[x] < 18.0 and sandPerc[x] > 65.0:
            WC_residual = 0.025
        else:
            WC_residual = 0.01

        if VGOption == 'Wosten_1999_top':

            K_sat = (10.0 / 24.0) * math.exp(7.755 + (0.0352 * siltPerc[x]) + (0.93 * 1) - (0.976 * BDg_cm3[x]**2) - (0.000484 * clayPerc[x]**2) - (0.000322 * siltPerc[x]**2) + (0.001 * siltPerc[x]**(-1)) - (0.0748 * (carbPerc[x]*float(carbonConFactor))**(-1)) - (0.643 * math.log(siltPerc[x])) - (0.0139 * BDg_cm3[x] * clayPerc[x]) - (0.167 * BDg_cm3[x] * carbPerc[x]*float(carbonConFactor)) + (0.0298 * 1 * clayPerc[x]) - (0.03305 * 1 * siltPerc[x]))

            WC_sat = 0.7919 + (0.001691 * clayPerc[x]) - (0.29619 * BDg_cm3[x]) - (0.000001491 * siltPerc[x]**2) + (0.0000821 * ((carbPerc[x] * float(carbonConFactor)))**2) + (0.02427 * clayPerc[x] **(-1.0) + (0.01113 * siltPerc[x]**(-1.0)) +  (0.01472 * math.log(siltPerc[x])) - 0.0000733 * ((carbPerc[x] * float(carbonConFactor))) * clayPerc[x]) - (0.000619 * BDg_cm3[x] * clayPerc[x]) - (0.001183 * BDg_cm3[x] * (carbPerc[x] * float(carbonConFactor))) - (0.0001664 * 1.0 * siltPerc[x])
                        
            # Alpha with 10.0 multiplier (convert alpha in cm-1 to kPa-1)
            alpha_cm = math.exp(- 14.96 + (0.03135 * clayPerc[x]) + (0.0351 * siltPerc[x]) + (0.646 * (carbPerc[x] * float(carbonConFactor))) + (15.29 * BDg_cm3[x]) - (0.192 * 1.0) - (4.671 * BDg_cm3[x] ** 2.0) - (0.000781 * clayPerc[x] ** 2) - (0.00687 * (carbPerc[x] * float(carbonConFactor)) ** 2.0) + (0.0449 * ((carbPerc[x] * float(carbonConFactor)))**(-1.0)) + (0.0663 * math.log(siltPerc[x])) + (0.1482 * math.log((carbPerc[x] * float(carbonConFactor)))) - (0.04546 * BDg_cm3[x] * siltPerc[x]) - (0.4852 * BDg_cm3[x] * (carbPerc[x] * float(carbonConFactor))) + (0.00673 * 1.0 * clayPerc[x]))
            alpha_VG = 10.0 * alpha_cm # Converted from cm-1 to kPa-1 for internal consistency

            n_VG = 1.0 + math.exp(-25.23 - (0.02195 * clayPerc[x]) + (0.0074 * siltPerc[x]) - (0.1940 * (carbPerc[x] * float(carbonConFactor))) + (45.5 * BDg_cm3[x]) - (7.24 * BDg_cm3[x] ** 2.0) +  (0.0003658 * clayPerc[x] **2.0) + (0.002885 * ((carbPerc[x] * float(carbonConFactor)))**2.0) - (12.81 * (BDg_cm3[x])**(-1.0)) - (0.1524 * (siltPerc[x])**(-1.0)) - (0.01958 * ((carbPerc[x] * float(carbonConFactor)))** (-1.0)) - (0.2876 * math.log(siltPerc[x])) - (0.0709 * math.log((carbPerc[x] * float(carbonConFactor)))) - (44.6 * math.log(BDg_cm3[x])) - (0.02264 * BDg_cm3[x] * clayPerc[x]) + (0.0896 * BDg_cm3[x] * (carbPerc[x] * float(carbonConFactor))) + (0.00718 * 1.0 * clayPerc[x]))
            m_VG = 1.0 - (1.0 / float(n_VG))

            l_MvG_norm = 0.0202 + (0.0006193 * clayPerc[x]**2) - (0.001136 * (carbPerc[x]*float(carbonConFactor))**2) - (0.2316 * math.log(carbPerc[x]*float(carbonConFactor))) - (0.03544 * BDg_cm3[x] * clayPerc[x]) + (0.00283 * BDg_cm3[x] * siltPerc[x]) + (0.0488 * BDg_cm3[x] * (carbPerc[x] * float(carbonConFactor)))
            l_MvG =  10 * (math.exp(l_MvG_norm) - 1) / (math.exp(l_MvG_norm)+1)

        elif VGOption == 'Wosten_1999_sub':

            K_sat = (10.0 / 24.0) * math.exp(7.755 + (0.0352 * siltPerc[x]) + (0.93 * 0) - (0.976 * BDg_cm3[x]**2) - (0.000484 * clayPerc[x]**2) - (0.000322 * siltPerc[x]**2) + (0.001 * siltPerc[x]**(-1)) - (0.0748 * (carbPerc[x]*float(carbonConFactor))**(-1)) - (0.643 * math.log(siltPerc[x])) - (0.0139 * BDg_cm3[x] * clayPerc[x]) - (0.167 * BDg_cm3[x] * carbPerc[x]*float(carbonConFactor)) + (0.0298 * 0* clayPerc[x]) - (0.03305 * 0 * siltPerc[x]))

            WC_sat = 0.7919 + (0.001691 * clayPerc[x]) - (0.29619 * BDg_cm3[x]) - (0.000001491 * siltPerc[x]**2) + (0.0000821 * ((carbPerc[x] * float(carbonConFactor)))**2) + (0.02427 * clayPerc[x] **(-1.0) + (0.01113 * siltPerc[x]**(-1.0)) +  (0.01472 * math.log(siltPerc[x])) - 0.0000733 * ((carbPerc[x] * float(carbonConFactor))) * clayPerc[x]) - (0.000619 * BDg_cm3[x] * clayPerc[x]) - (0.001183 * BDg_cm3[x] * (carbPerc[x] * float(carbonConFactor))) - (0.0001664 * 0.0 * siltPerc[x])
            
            # Wosten originally has alpha in cm-1
            alpha_cm = math.exp(- 14.96 + (0.03135 * clayPerc[x]) + (0.0351 * siltPerc[x]) + (0.646 * (carbPerc[x] * float(carbonConFactor))) + (15.29 * BDg_cm3[x]) - (0.192 * 0.0) - (4.671 * BDg_cm3[x] ** 2.0) - (0.000781 * clayPerc[x] ** 2) - (0.00687 * (carbPerc[x] * float(carbonConFactor)) ** 2.0) + (0.0449 * ((carbPerc[x] * float(carbonConFactor)))**(-1.0)) + (0.0663 * math.log(siltPerc[x])) + (0.1482 * math.log((carbPerc[x] * float(carbonConFactor)))) - (0.04546 * BDg_cm3[x] * siltPerc[x]) - (0.4852 * BDg_cm3[x] * (carbPerc[x] * float(carbonConFactor))) + (0.00673 * 0.0 * clayPerc[x]))
            alpha_VG = 10.0 * alpha_cm # Converted from cm-1 to kPa-1 for internal consistency
            
            n_VG = 1.0 + math.exp(-25.23 - (0.02195 * clayPerc[x]) + (0.0074 * siltPerc[x]) - (0.1940 * (carbPerc[x] * float(carbonConFactor))) + (45.5 * BDg_cm3[x]) - (7.24 * BDg_cm3[x] ** 2.0) +  (0.0003658 * clayPerc[x] **2.0) + (0.002885 * ((carbPerc[x] * float(carbonConFactor)))**2.0) - (12.81 * (BDg_cm3[x])**(-1.0)) - (0.1524 * (siltPerc[x])**(-1.0)) - (0.01958 * ((carbPerc[x] * float(carbonConFactor)))** (-1.0)) - (0.2876 * math.log(siltPerc[x])) - (0.0709 * math.log((carbPerc[x] * float(carbonConFactor)))) - (44.6 * math.log(BDg_cm3[x])) - (0.02264 * BDg_cm3[x] * clayPerc[x]) + (0.0896 * BDg_cm3[x] * (carbPerc[x] * float(carbonConFactor))) + (0.00718 * 0.0 * clayPerc[x]))
            m_VG = 1.0 - (1.0 / float(n_VG))

            l_MvG_norm = 0.0202 + (0.0006193 * clayPerc[x]**2) - (0.001136 * (carbPerc[x]*float(carbonConFactor))**2) - (0.2316 * math.log(carbPerc[x]*float(carbonConFactor))) - (0.03544 * BDg_cm3[x] * clayPerc[x]) + (0.00283 * BDg_cm3[x] * siltPerc[x]) + (0.0488 * BDg_cm3[x] * (carbPerc[x] * float(carbonConFactor)))
            l_MvG =  10 * (math.exp(l_MvG_norm) - 1) / (math.exp(l_MvG_norm)+1)

        WC_satArray.append(WC_sat)
        WC_residualArray.append(WC_residual)
        alpha_VGArray.append(alpha_VG)
        n_VGArray.append(n_VG)
        m_VGArray.append(m_VG)
        l_MvGArray.append(l_MvG)
        
        K_satArray.append(K_sat)
            
    # Write K_sat and warning results to output shapefile
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

    return WC_residualArray, WC_satArray, alpha_VGArray, n_VGArray, m_VGArray, l_MvGArray, K_satArray

def Vereecken_1989(outputShp, VGOption, carbonConFactor, carbContent):

    # Arrays to write to shapefile    
    warningArray = []
    WC_satArray = []
    WC_residualArray = []
    alpha_VGArray = []
    n_VGArray = []
    m_VGArray = []

    log.info("Calculating van Genuchten parameters using Vereecken et al. (1989)")

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    if carbContent == 'OC':
        reqFields = [OIDField, "Sand", "Clay", "OC", "BD", "soilname", "texture"]                    
        carbonConFactor = 1.0

    elif carbContent == 'OM':
        reqFields = [OIDField, "Sand", "Clay", "OM", "BD", "soilname", "texture"]
        
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    clayPerc = []
    carbPerc = []
    BDg_cm3 = []
    nameArray = []
    textureArray = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            clay = row[2]
            carbon = row[3]
            BD = row[4]
            name = row[5]
            texture = row[6]

            record.append(objectID)
            sandPerc.append(sand)
            clayPerc.append(clay)
            carbPerc.append(carbon)
            BDg_cm3.append(BD)
            nameArray.append(name)
            textureArray.append(texture)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkCarbon(carbPerc[x], carbContent, record[x])
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        WC_sat = 0.81 - (0.283 * BDg_cm3[x]) + (0.001 * clayPerc[x])
        WC_residual = 0.015 + (0.005 * clayPerc[x]) + (0.014 * carbPerc[x]*float(carbonConFactor))
        
        # Vereecken et al. (1989) calculates alpha in cm-1
        alpha_cm = math.exp(-2.486 + (0.025 * sandPerc[x]) - (0.351 * carbPerc[x]*float(carbonConFactor)) - (2.617 * BDg_cm3[x]) - (0.023*clayPerc[x]))
        alpha_VG = 10.0 * alpha_cm # Converted from cm-1 to kPa-1

        n_VG = math.exp(0.053 - (0.009 * sandPerc[x]) - (0.013 * clayPerc[x]) + (0.00015 * sandPerc[x]**2))
        m_VG = 1.0

        WC_satArray.append(WC_sat)
        WC_residualArray.append(WC_residual)
        alpha_VGArray.append(alpha_VG)
        n_VGArray.append(n_VG)
        m_VGArray.append(m_VG)

    common.writeWarning(outputShp, warningArray)

    return WC_residualArray, WC_satArray, alpha_VGArray, n_VGArray, m_VGArray

def ZachariasWessolek_2007(outputShp, VGOption, carbonConFactor, carbContent):

    # Arrays to write to shapefile    
    warningArray = []
    WC_satArray = []
    WC_residualArray = []
    alpha_VGArray = []
    n_VGArray = []
    m_VGArray = []

    log.info("Calculating van Genuchten parameters using Zacharias and Wessolek (2007)")

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    # Requirements: Sand, clay, and BD
    reqFields = [OIDField, "Sand", "Clay", "BD", "soilname", "texture"]
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    clayPerc = []
    BDg_cm3 = []
    nameArray = []
    textureArray = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            clay = row[2]                        
            BD = row[3]
            name = row[4]
            texture = row[5]

            record.append(objectID)
            sandPerc.append(sand)
            clayPerc.append(clay)
            BDg_cm3.append(BD)
            nameArray.append(name)
            textureArray.append(texture)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        if sandPerc[x] < 66.5:
            WC_residual = 0
            WC_sat = 0.788 + (0.001 * clayPerc[x]) - (0.263 * BDg_cm3[x])
            
            # Alpha in kPa-1
            alpha_VG = math.exp(-0.648 + (0.023 * sandPerc[x]) + (0.044 * clayPerc[x]) - (3.168 * BDg_cm3[x]))
            
            n_VG = 1.392 - (0.418 * sandPerc[x]**(-0.024)) + (1.212 * clayPerc[x]**(-0.704))
            m_VG = 1.0 - (1.0 / float(n_VG))

        else:
            WC_residual = 0 
            WC_sat = 0.89 - (0.001 * clayPerc[x]) - (0.322 * BDg_cm3[x])
            
            # Alpha in kPa-1
            alpha_VG = math.exp(- 4.197 + (0.013 * sandPerc[x]) + (0.076 * clayPerc[x]) - (0.276 * BDg_cm3[x]))
            
            n_VG = - 2.562 + (7 * 10**(-9) * sandPerc[x]**4.004) + (3.75 * clayPerc[x]**(-0.016))
            m_VG = 1.0 - (1.0 / float(n_VG))

        WC_satArray.append(WC_sat)
        WC_residualArray.append(WC_residual)
        alpha_VGArray.append(alpha_VG)
        n_VGArray.append(n_VG)
        m_VGArray.append(m_VG)

    common.writeWarning(outputShp, warningArray)

    return WC_residualArray, WC_satArray, alpha_VGArray, n_VGArray, m_VGArray

def Weynants_2009(outputShp, VGOption, carbonConFactor, carbContent, MVGChoice):

    # Arrays to write to shapefile    
    warningArray = []
    K_satArray = []
    WC_satArray = []
    WC_residualArray = []
    alpha_VGArray = []
    n_VGArray = []
    m_VGArray = []
    l_MvGArray = []

    log.info("Calculating van Genuchten parameters using Weynants et al. (2009)")

    # Requirements: sand, clay, OC, and BD

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    if carbContent == 'OC':
        reqFields = [OIDField, "Sand", "Clay", "OC", "BD", "soilname", "texture"]
        carbonConFactor = 1.0

    elif carbContent == 'OM':
        reqFields = [OIDField, "Sand", "Clay", "OM", "BD", "soilname", "texture"]
        
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    clayPerc = []
    carbPerc = []
    BDg_cm3 = []
    nameArray = []
    textureArray = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            clay = row[2]
            carbon = row[3]
            BD = row[4]
            name = row[5]
            texture = row[6]

            record.append(objectID)
            sandPerc.append(sand)
            clayPerc.append(clay)
            carbPerc.append(carbon)
            BDg_cm3.append(BD)
            nameArray.append(name)
            textureArray.append(texture)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkCarbon(carbPerc[x], carbContent, record[x])
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        WC_residual = 0
        WC_sat = 0.6355 + (0.0013 * clayPerc[x]) - (0.1631 * BDg_cm3[x])
        
        # Alpha in cm-1
        alpha_cm = math.exp(- 4.3003 - (0.0097 * clayPerc[x]) + (0.0138 * sandPerc[x]) - (0.0992 * carbPerc[x]*float(carbonConFactor)))
        alpha_VG = 10.0 * alpha_cm # Convert to kPa-1

        n_VG = math.exp(- 1.0846 - (0.0236 * clayPerc[x]) - (0.0085 * sandPerc[x]) + (0.0001 * sandPerc[x]**2)) + 1 
        m_VG = 1.0 - (1.0 / float(n_VG))

        l_MvG = - 1.8642 - (0.1317 * clayPerc[x]) + (0.0067 * sandPerc[x])

        K_sat = math.exp(1.9582 + (0.0308 * sandPerc[x]) - (0.6142 * BDg_cm3[x]) - (0.1566 * (carbPerc[x] * float(carbonConFactor)))) * (10.0 / 24.0)

        WC_satArray.append(WC_sat)
        WC_residualArray.append(WC_residual)
        alpha_VGArray.append(alpha_VG)
        n_VGArray.append(n_VG)
        m_VGArray.append(m_VG)
        l_MvGArray.append(l_MvG)
        K_satArray.append(K_sat)

    common.writeWarning(outputShp, warningArray)

    return WC_residualArray, WC_satArray, alpha_VGArray, n_VGArray, m_VGArray, l_MvGArray, K_satArray

def Dashtaki_2010(outputShp, VGOption, carbonConFactor, carbContent):

    # Arrays to write to shapefile    
    warningArray = []
    K_satArray = []
    WC_satArray = []
    WC_residualArray = []
    alpha_VGArray = []
    n_VGArray = []
    m_VGArray = []

    log.info("Calculating van Genuchten parameters using Dashtaki et al. (2010)")

    # Requirements: Sand, clay, and BD

    # Get OID field
    OIDField = common.getOIDField(outputShp)

    reqFields = [OIDField, "Sand", "Clay", "BD", "soilname", "texture"]
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    clayPerc = []
    BDg_cm3 = []
    nameArray = []
    textureArray = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            clay = row[2]
            BD = row[3]
            name = row[4]
            texture = row[5]

            record.append(objectID)
            sandPerc.append(sand)
            clayPerc.append(clay)
            BDg_cm3.append(BD)
            nameArray.append(name)
            textureArray.append(texture)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkValue("Sand", sandPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Clay", clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningArray.append(warningFlag)

        # Calculate water content using Dashtaki et al. (2010) - Sand, Clay, BD
        WC_residual = 0.034 + (0.0032 * clayPerc[x])
        WC_sat = 0.85 - (0.00061 * sandPerc[x]) - (0.258 * BDg_cm3[x])
        
        # Alpha in cm-1
        alpha_cm = abs(1/(- 476 - (4.1 * sandPerc[x]) + (499 * BDg_cm3[x])))
        alpha_VG = 10.0 * alpha_cm # Converted from cm-1 to kPa-1 for internal consistency
        
        n_VG = 1.56 - (0.00228 * sandPerc[x])
        m_VG = 1.0 - (1.0 / float(n_VG))

        WC_satArray.append(WC_sat)
        WC_residualArray.append(WC_residual)
        alpha_VGArray.append(alpha_VG)
        n_VGArray.append(n_VG)
        m_VGArray.append(m_VG)

    common.writeWarning(outputShp, warningArray)

    return WC_residualArray, WC_satArray, alpha_VGArray, n_VGArray, m_VGArray

def HodnettTomasella_2002(outputShp, VGOption, carbonConFactor, carbContent):

    # Arrays to write to shapefile    
    warningArray = []
    WC_satArray = []
    WC_residualArray = []
    alpha_VGArray = []
    n_VGArray = []
    m_VGArray = []

    log.info("Calculating van Genuchten parameters using Hodnett and Tomasella (2002)")

    # Requirements: Sand, Silt, Clay, OC, BD, CEC, pH
    
    # Get OID field
    OIDField = common.getOIDField(outputShp)

    if carbContent == 'OC':
        reqFields = [OIDField, "Sand", "Silt", "Clay", "OC", "BD", "CEC", "pH", "soilname", "texture"]
        carbonConFactor = 1.0

    elif carbContent == 'OM':
        reqFields = [OIDField, "Sand", "Silt", "Clay", "OC", "BD", "CEC", "pH", "soilname", "texture"]
        
    checks_PTFs.checkInputFields(reqFields, outputShp)

    # Retrieve info from input
    record = []
    sandPerc = []
    siltPerc = []
    clayPerc = []
    carbPerc = []
    BDg_cm3 = []
    CECcmol_kg = []
    pH = []
    nameArray = []
    textureArray = []

    with arcpy.da.SearchCursor(outputShp, reqFields) as searchCursor:
        for row in searchCursor:
            objectID = row[0]
            sand = row[1]
            silt = row[2]
            clay = row[3]  
            carbon = row[4]                      
            BD = row[5]
            CEC = row[6]
            pHValue = row[7]
            name = row[8]
            texture = row[9]

            record.append(objectID)
            sandPerc.append(sand)
            siltPerc.append(silt)
            clayPerc.append(clay)
            carbPerc.append(carbon)
            BDg_cm3.append(BD)
            CECcmol_kg.append(CEC)
            pH.append(pHValue)
            nameArray.append(name)
            textureArray.append(texture)

    for x in range(0, len(record)):

        # Data checks
        warningFlag = checks_PTFs.checkSSC(sandPerc[x], siltPerc[x], clayPerc[x], record[x])
        warningFlag = checks_PTFs.checkCarbon(carbPerc[x], carbContent, record[x])
        warningFlag = checks_PTFs.checkValue("Bulk density", BDg_cm3[x], record[x])
        warningFlag = checks_PTFs.checkValue("CEC", CECcmol_kg[x], record[x])
        warningFlag = checks_PTFs.checkValue("pH", pH[x], record[x])
        warningArray.append(warningFlag)

        WC_sat = 0.81799 + (9.9 * 10**(-4) * clayPerc[x]) - (0.3142 * BDg_cm3[x]) + (1.8 * 10**(-4) * CECcmol_kg[x]) + (0.00451 * pH[x]) - (5 * 10**(-6) * sandPerc[x] * clayPerc[x])
        WC_residual = 0.22733 - (0.00164 * sandPerc[x]) + (0.00235 * CECcmol_kg[x]) - (0.00831 * pH[x]) + (1.8 * 10**(-5) * clayPerc[x]**2) + (2.6 * 10**(-5) * sandPerc[x] * clayPerc[x])
        
        # Original equation had values in kPa-1
        # No internal conversion needed
        alpha_VG = math.exp(- 0.02294 - (0.03526 * siltPerc[x]) + (0.024 * carbPerc[x]*float(carbonConFactor)) - (0.00076 * CECcmol_kg[x]) - (0.11331 * pH[x]) + (0.00019 * siltPerc[x]**2))                    
        
        n_VG = math.exp(0.62986 - (0.00833 * clayPerc[x]) - (0.00529 * carbPerc[x]*float(carbonConFactor)) + (0.00593 * pH[x]) + (7 * 10**(-5) * clayPerc[x]**2) - (1.4 * 10**(-4) * sandPerc[x] * siltPerc[x]))
        m_VG = 1.0 - (1.0 / float(n_VG))

        WC_satArray.append(WC_sat)
        WC_residualArray.append(WC_residual)
        alpha_VGArray.append(alpha_VG)
        n_VGArray.append(n_VG)
        m_VGArray.append(m_VG)

    common.writeWarning(outputShp, warningArray)

    return WC_residualArray, WC_satArray, alpha_VGArray, n_VGArray, m_VGArray

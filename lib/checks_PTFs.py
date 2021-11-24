'''
Functions that help check fields and values for PTFs
'''

import sys
import os
import configuration
import numpy as np
import arcpy
import math
import NB_PTFs.lib.log as log
import NB_PTFs.lib.common as common
import NB_PTFs.lib.PTFdatabase as PTFdatabase
from NB_PTFs.lib.external import six # Python 2/3 compatibility module

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log, common, PTFdatabase])

def checkInputFields(inputFields, inputShp):

    log.info('Checking if all required input fields are present in ' + str(inputShp))

    # Checks if the input fields are present in the shapefile
    for param in inputFields:        

        fieldPresent = False
        
        if common.CheckField(inputShp, param):
            fieldPresent = True

        else:
            log.error("Field " + str(param) + " not found in the input shapefile")
            log.error("Please ensure this field present in the input shapefile")
            sys.exit()

def checkValue(name, value, record):
    warningFlag = ''

    # log.info('DEBUG: checking ' + str(name) + ' is not negative or over 100')

    if value < 0.0:
        warningFlag = str(name) + ' is negative'
        log.warning(str(name) + ' is negative, please check record: ' + str(record))

    if value > 100.0:
        warningFlag = str(name) + ' is over 100'
        log.warning(str(name) + ' is over 100, please check record: ' + str(record))

    return warningFlag

def checkSSC(sand, silt, clay, record):
    warningFlag = ''

    # log.info('DEBUG: checking sand, silt, clay (negative and sum)')

    if sand < 0.0:
        warningFlag ='Sand is negative'
        log.warning('Sand content is negative')
        log.warning('Please check record: ' + str(record))

    if silt < 0.0:
        warningFlag ='Silt is negative'
        log.warning('Silt content is negative')
        log.warning('Please check record: ' + str(record))

    if clay < 0.0:
        warningFlag ='Clay is negative'
        log.warning('Clay content is negative')
        log.warning('Please check record: ' + str(record))

    SSC = sand + silt + clay

    # log.info('DEBUG: SSC: ' + str(SSC))

    if SSC < 99.0:
        warningFlag = 'SSC less than 99'
        log.warning('Sand, silt, clay sum up to less than 99 percent')
        log.warning('Please check record: ' + str(record))

    if SSC > 101.0:
        warningFlag = 'SSC more than 101'
        log.warning('Sand, silt, clay sum up to more than 100')
        log.warning('Please check record: ' + str(record))

    return warningFlag

def checkCarbon(carbon, carbContent, record):
    warningFlag = ''

    # log.info('DEBUG: checking if carbon is negative or over 100')

    if carbon < 0.0:
        warningFlag = 'Carbon negative'

        if carbContent == 'OC':
            msg = 'Organic carbon '
            field = 'OC'
        elif carbContent == 'OM':
            msg = 'Organic matter '
            field = 'OM'

        warningMsg1 = str(msg) + "content (percentage) is negative"
        log.warning(warningMsg1)
        warningMsg2 = "Please check the field " + str(field) + " in record " + str(record)
        log.warning(warningMsg2)

    ## ADD WARNING for carbon > 40

    ## ADD ERROR for carbon > 100

    if carbon > 100.0:

        warningFlag = 'OC or OM over 100'

        if carbContent == 'OC':
            msg = 'Organic carbon '
            field = 'OC'
        elif carbContent == 'OM':
            msg = 'Organic matter '
            field = 'OM'

        warningMsg1 = str(msg) + "content (percentage) is higher than 100 percent"
        log.warning(warningMsg1)
        warningMsg2 = "Please check the field " + str(field) + " in record " + str(record)
        log.warning(warningMsg2)

    return warningFlag

# Checks for Batjes (1996): Sand, silt, clay should not be smaller than 5; OC should not be smaller than 0.1%
def checkBatjes(sand, silt, clay, carbon, carbContent, record):
    warningFlag = ''

    # log.info('DEBUG: checking for Batjes')

    if sand < 5.0:
        warningFlag = 'Sand less than 5'
        log.warning('Batjes (1996) requires sand content to be at least 5 percent, check record: ' + str(record))

    if silt < 5.0:
        warningFlag = 'Silt less than 5'
        log.warning('Batjes (1996) requires silt content to be at least 5 percent, check record: ' + str(record))

    if clay < 5.0:
        warningFlag = 'Clay less than 5'
        log.warning('Batjes (1996) requires clay content to be at least 5 percent, check record: ' + str(record))

    if carbon < 0.1:
        warningFlag = 'Carbon less than 0.1'
        log.warning('Batjes (1996) requires carbon content to be at least 0.1 percent, check record: ' + str(record))

    return warningFlag

def checkNegValue(nameValue, value, nameSoil):
    # Checks if the output is negative and returns a warning

    if value < 0.0:
        warningMsg = str(nameValue) + " is negative for " + str(nameSoil)
        log.warning(warningMsg)

        warningMsg2 = "Please check the results for " + str(nameSoil)
        log.warning(warningMsg2)

def pressureFields(outputFolder, inputShp, fieldFC, fieldSIC, fieldPWP):

    # Check PTF information
    PTFxml = os.path.join(outputFolder, "ptfinfo.xml")
    PTFOption = common.readXML(PTFxml, 'VGOption')

    PTFInfo = PTFdatabase.checkPTF(PTFOption)
    PTFType = PTFInfo.PTFType
    PTFPressures = PTFInfo.PTFPressures

    # Get OIDField
    OIDField = arcpy.Describe(inputShp).OIDFieldName

    fcArray = []
    sicArray = []
    pwpArray = []

    # Check the field capacity field
    if common.CheckField(inputShp, fieldFC):

        with arcpy.da.SearchCursor(inputShp, [fieldFC, OIDField]) as searchCursor:
            for row in searchCursor:
                fc_kPa = row[0]

                if PTFType == 'vgPTF':
                    if fc_kPa < 6 or fc_kPa > 33:
                        log.warning("Field capacity for soil in row " + str(OIDField) + " should be between 6 to 33 kPa")

                    fcArray.append(fc_kPa)

                elif PTFType == 'pointPTF':
                    # Check if this pressure point is inside the array

                    if fc_kPa in PTFPressures:
                        fcArray.append(fc_kPa)

                    else:
                        log.error("Pressure for field capacity NOT present in point-PTF pressures")
                        log.error("Cannot calculate water content at this pressure for field capacity")
                        sys.exit()

                else:
                    log.error("PTF type not recognised: " + str(PTFType))

    else:
        log.error("Field for field capacity not found in input shapefle: " + str(fieldFC))
        sys.exit()

    if fieldSIC is not None:
        if common.CheckField(inputShp, fieldSIC):

            with arcpy.da.SearchCursor(inputShp, [fieldSIC, OIDField]) as searchCursor:
                for row in searchCursor:
                    sic_kPa = row[0]                    

                    if PTFType == 'vgPTF':
                        ## TODO: Put in a check for the stoma closure pressure
                        ## TODO: Need to know what is a realistic range for the SIC presusre
                        
                        sicArray.append(sic_kPa)

                    elif PTFType == 'pointPTF':
                        # Check if this pressure point is inside the array

                        if sic_kPa in PTFPressures:
                            sicArray.append(sic_kPa)

                        else:
                            log.error("Pressure for stoma closure due to water stress NOT present in point-PTF pressures")
                            log.error("Cannot calculate water content at this pressure for stoma closure due to water stress")
                            sys.exit()

                    else:
                        log.error("PTF type not recognised: " + str(PTFType))

        else:
            log.error("Field for water stress-induced stomatal closure not found in input shapefle: " + str(fieldFC))

    else:
        log.warning("Field for water stress-induced stomatal closure not specified")
        log.warning("Using default value of 100 kPa")
        defaultSIC = 100.0

        # Populate sicArray
        for i in range(0, len(fcArray)):
            sicArray.append(defaultSIC)

    if fieldPWP is not None:
        if common.CheckField(inputShp, fieldPWP):

            with arcpy.da.SearchCursor(inputShp, [fieldPWP, OIDField]) as searchCursor:
                for row in searchCursor:
                    pwp_kPa = row[0]

                    if PTFType == 'vgPTF':

                        if pwp_kPa > 1500:
                            log.warning("Permanent wilting point for soil in row " + str(OIDField) + " exceeds 1500 kPa")

                            ## ASK B: vg not valid for over 1500 kPa?
                            log.warning("The van Genuchten equation is not valid for pressures greater than 1500 kPa")

                        pwpArray.append(pwp_kPa)

                    elif PTFType == 'pointPTF':
                        # Check if this pressure point is inside the array

                        if pwp_kPa in pwp_kPa:
                            pwpArray.append(pwp_kPa)

                        else:
                            log.error("Pressure for permanent wilting point NOT present in point-PTF pressures")
                            log.error("Cannot calculate water content at this pressure for permanent wilting point")
                            sys.exit()

                    else:
                        log.error("PTF type not recognised: " + str(PTFType))


        else:
            log.error("Field for permanent wilting point not found in input shapefle: " + str(fieldFC))

    else:
        log.warning("Field for permanent wilting point not specified")
        log.warning("Using default value of 1500 kPa")
        defaultPWP = 1500.0

        # Populate pwpArray
        for i in range(0, len(fcArray)):
            pwpArray.append(defaultPWP)

    # log.info('DEBUG: fcArray: ' + str(fcArray))
    # log.info('DEBUG: sicArray: ' + str(sicArray))
    # log.info('DEBUG: pwpArray: ' + str(pwpArray))

    return fcArray, sicArray, pwpArray


## Checks for:
## FC (between 6 and 33)
## PWP
## SIC?
## theta >= theta_sat + 1% (ok) but theta > theta_sat + 1% (error!)

def checkNegOutput(array, record):
    # Checks if the output is negative and returns a warning

    for output in array:

        if output < 0.0:
            warningFlag = 'Soil moisture value is negative for record ' + str(record)
            log.warning(warningFlag)
# Holds the threshold checks for PTFs

import arcpy
import os
import sys

from NB_PTFs.lib.external import six # Python 2/3 compatibility module
import configuration
import NB_PTFs.lib.log as log

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log])

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

def checkNegOutput(array, record):
    # Checks if the output is negative and returns a warning

    for output in array:

        if output < 0.0:
            warningFlag = 'Soil moisture value is negative for record ' + str(record)
            log.warning(warningFlag)
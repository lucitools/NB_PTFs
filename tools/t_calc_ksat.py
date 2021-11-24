import arcpy
import os
import sys

import NB_PTFs.lib.log as log
import NB_PTFs.lib.common as common
import NB_PTFs.lib.progress as progress
import NB_PTFs.solo.calc_ksat as CalcKsat
import NB_PTFs.lib.PTFdatabase as PTFdatabase

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log, common, CalcKsat, PTFdatabase])

def function(params):

    try:
        pText = common.paramsAsText(params)

        # Get inputs
        runSystemChecks = common.strToBool(pText[1])
        outputFolder = pText[2]
        inputFolder = pText[3]

        # Get equation of choice
        Ksat = pText[4]

        carbonContent = pText[5]
        carbonConFactor = pText[6]

        # Create output folder
        if not os.path.exists(outputFolder):
            os.mkdir(outputFolder)

        # System checks and setup
        if runSystemChecks:
            common.runSystemChecks(outputFolder)

        # Set up logging output to file
        log.setupLogging(outputFolder)

        # Write input params to XML
        common.writeParamsToXML(params, outputFolder)

        # Set saturated hydraulic conductivity option
        if Ksat == 'Cosby et al. (1984)':
            KsatOption = 'Cosby_1984'

        elif Ksat == 'Puckett et al. (1985)':
            KsatOption = 'Puckett_1985'

        elif Ksat == 'Jabro (1992)':
            KsatOption = 'Jabro_1992'

        elif Ksat == 'Campbell and Shiozawa (1994)':
            KsatOption = 'CampbellShiozawa_1994'

        elif Ksat == 'Ferrer Julia et al. (2004) - Sand':
            KsatOption = 'FerrerJulia_2004_1'

        elif Ksat == 'Ferrer Julia et al. (2004) - Sand, clay, OM':
            KsatOption = 'FerrerJulia_2004_2'

        elif Ksat == 'Ahuja et al. (1989)':
            KsatOption = 'Ahuja_1989'

        elif Ksat == 'Minasny and McBratney (2000)':
            KsatOption = 'MinasnyMcBratney_2000'

        elif Ksat == 'Brakensiek et al. (1984)':
            KsatOption = 'Brakensiek_1984'

        elif Ksat == 'Wosten et al. (1999)':
            KsatOption = 'Wosten_1999'
            log.info('===========================================================================')
            log.info('Wosten et al. (1999) already calculated Ksat in the previous step')
            log.info('Please check the output shapefile of the previous step for the K_sat field')
            log.info('===========================================================================')
            sys.exit()

        else:
            log.error('Invalid Ksat option')
            sys.exit()

        # Set carbon content choice
        if carbonContent == 'Organic carbon':
            carbContent = 'OC'

        elif carbonContent == 'Organic matter':
            carbContent = 'OM'

        else:
            log.error('Invalid carbon content option')
            sys.exit()

        # Pull out PTFinfo
        PTFInfo = PTFdatabase.checkPTF(KsatOption)
        PTFType = PTFInfo.PTFType
        PTFUnit = PTFInfo.PTFUnit

        PTFOut = [("KsatOption", KsatOption),
                  ("PTFType", PTFType),
                  ("carbContent", carbContent)]

        # Write to XML file
        PTFXML = os.path.join(outputFolder, "ksat_ptfinfo.xml")
        common.writeXML(PTFXML, PTFOut)

        CalcKsat.function(outputFolder, inputFolder, KsatOption,
                          carbContent, carbonConFactor)

        # Set output filename for display
        KsatOut = os.path.join(outputFolder, "Ksat.shp")
        arcpy.SetParameter(7, KsatOut)

        log.info("Saturated hydraulic conductivity operations completed successfully")

    except Exception:
        log.exception("Saturated hydraulic conductivity tool failed")
        raise

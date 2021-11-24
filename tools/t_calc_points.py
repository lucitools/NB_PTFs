import arcpy
import os
import sys

import NB_PTFs.lib.log as log
import NB_PTFs.lib.common as common
import NB_PTFs.lib.progress as progress
import NB_PTFs.solo.calc_point_ptfs as calc_point_ptfs
import NB_PTFs.lib.PTFdatabase as PTFdatabase

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log, common, calc_point_ptfs, PTFdatabase])

def function(params):

    try:
        pText = common.paramsAsText(params)

        # Get inputs
        runSystemChecks = common.strToBool(pText[1])
        outputFolder = pText[2]
        inputShapefile = pText[3]
        PTF = pText[4]
        fcVal = float(pText[5])
        sicVal = float(pText[6])
        pwpVal = float(pText[7])
        carbonContent = pText[8]
        carbonConFactor = pText[9]
        unitsPlot = pText[10]

        # Create output folder
        if not os.path.exists(outputFolder):
            os.mkdir(outputFolder)

        common.runSystemChecks(outputFolder)

        # Set up logging output to file
        log.setupLogging(outputFolder)

        # Write input params to XML
        common.writeParamsToXML(params, outputFolder)

        # Simplify PTFOption
        if PTF == 'Nguyen et al. (2014)':
            PTFOption = 'Nguyen_2014'

        elif PTF == 'Adhikary et al. (2008)':
            PTFOption = 'Adhikary_2008'

        elif PTF == 'Rawls et al. (1982)':
            PTFOption = 'Rawls_1982'

        elif PTF == 'Hall et al. (1977) topsoil':
            PTFOption = 'Hall_1977_top'

        elif PTF == 'Hall et al. (1977) subsoil':
            PTFOption = 'Hall_1977_sub'

        elif PTF == 'Gupta and Larson (1979)':
            PTFOption = 'GuptaLarson_1979'

        elif PTF == 'Batjes (1996)':
            PTFOption = 'Batjes_1996'

        elif PTF == 'Saxton and Rawls (2006)':
            PTFOption = 'SaxtonRawls_2006'

        elif PTF == 'Pidgeon (1972)':
            PTFOption = 'Pidgeon_1972'

        elif PTF == 'Lal (1978) Group I - Clay, BD':
            PTFOption = 'Lal_1978_Group1'

        elif PTF == 'Lal (1978) Group II - Clay, BD':
            PTFOption = 'Lal_1978_Group2'

        elif PTF == 'Aina and Periaswamy (1985)':
            PTFOption = 'AinaPeriaswamy_1985'

        elif PTF == 'Manrique and Jones (1991)':
            PTFOption = 'ManriqueJones_1991'

        elif PTF == 'van Den Berg et al. (1997)':
            PTFOption = 'vanDenBerg_1997'

        elif PTF == 'Tomasella and Hodnett (1998)':
            PTFOption = 'TomasellaHodnett_1998'

        elif PTF == 'Reichert et al. (2009) - Sand, silt, clay, OM, BD':
            PTFOption = 'Reichert_2009_OM'

        elif PTF == 'Reichert et al. (2009) - Sand, silt, clay, BD':
            PTFOption = 'Reichert_2009'

        elif PTF == 'Botula Manyala (2013)':
            PTFOption = 'Botula_2013'

        elif PTF == 'Shwetha and Varija (2013)':
            PTFOption = 'ShwethaVarija_2013'

        elif PTF == 'Dashtaki et al. (2010)':
            PTFOption = 'Dashtaki_2010_point'

        elif PTF == 'Santra et al. (2018) - Sand, Clay, OC, BD':
            PTFOption = 'Santra_2018_OC'

        elif PTF == 'Santra et al. (2018) - Sand, Clay, BD':
            PTFOption = 'Santra_2018'

        else:
            log.error('Invalid PTF option')
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
        PTFInfo = PTFdatabase.checkPTF(PTFOption)
        PTFType = PTFInfo.PTFType
        PTFUnit = PTFInfo.PTFUnit

        PTFType = PTFInfo.PTFType
        PTFPressures = PTFInfo.PTFPressures
        PTFUnit = PTFInfo.PTFUnit
        PTFFields = PTFInfo.PTFFields

        PTFOut = [("PTFOption", PTFOption),
                  ("PTFType", PTFType),
                  ("PTFPressures", str(PTFPressures)),
                  ("PTFUnit", PTFUnit),
                  ("PTFFields", str(PTFFields))]

        # Write to XML file
        PTFXML = os.path.join(outputFolder, "ptfinfo.xml")
        common.writeXML(PTFXML, PTFOut)

        # Call calc_point_ptfs
        calc_point_ptfs.function(outputFolder, inputShapefile, PTFOption, fcVal, sicVal, pwpVal, carbContent, carbonConFactor)

        # Loading shapefile automatically
        soilParamOut = os.path.join(outputFolder, "soil_point_ptf.shp")
        arcpy.SetParameter(11, soilParamOut)

        log.info("Point-PTF operations completed successfully")

    except Exception:
        log.exception("Point-PTF tool failed")
        raise

import arcpy
import os

import NB_PTFs.lib.log as log
import NB_PTFs.lib.common as common
import NB_PTFs.lib.progress as progress
import NB_PTFs.solo.brooks_corey as brooks_corey
import NB_PTFs.lib.PTFdatabase as PTFdatabase

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log, common, brooks_corey, PTFdatabase])

def function(params):

    try:
        pText = common.paramsAsText(params)

        # Get inputs
        runSystemChecks = common.strToBool(pText[1])
        outputFolder = pText[2]
        inputShapefile = pText[3]
        PTFChoice = pText[4]
        BCPressures = pText[5]
        fcVal = pText[6]
        sicVal = pText[7]
        pwpVal = pText[8]
        carbonContent = pText[9]
        carbonConFactor = pText[10]
        unitsPlot = pText[11]
        axisChoice = pText[12]

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

        if PTFChoice == 'Cosby et al. (1984) - Sand and Clay':
            PTFOption = 'Cosby_1984_SandC_BC'

        elif PTFChoice == 'Cosby et al. (1984) - Sand, Silt and Clay':
            PTFOption = 'Cosby_1984_SSC_BC'

        elif PTFChoice == 'Rawls and Brakensiek (1985)':
            PTFOption = 'RawlsBrakensiek_1985_BC'
            log.warning("Rawls and Brakensiek (1985) requires water content at saturation")
            log.warning("Please ensure the WC_sat field is present in the shapefile")

        elif PTFChoice == 'Campbell and Shiozawa (1992)':
            PTFOption = 'CampbellShiozawa_1992_BC'
            log.warning("Campbell and Shiozava (1992) requires water content at saturation")
            log.warning("Please ensure the WC_sat field is present in the shapefile")

        elif PTFChoice == 'Saxton et al. (1986)':
            PTFOption = 'Saxton_1986_BC'
            
        elif PTFChoice == 'Saxton and Rawls (2006)':
            PTFOption = 'SaxtonRawls_2006_BC'

        else:
            log.error('Choice for Brooks-Corey calculation not recognised')
            sys.exit()

        # Set carbon content choice
        if carbonContent == 'Organic carbon':
            carbContent = 'OC'

        elif carbonContent == 'Organic matter':
            carbContent = 'OM'

        else:
            log.error('Invalid carbon content option')
            sys.exit()

        # Unpack 'BC pressure heads' parameter
        if BCPressures is None:
            BCPressArray = []
        else:
            BCPressArray = BCPressures.split(' ')

        # Pull out PTFinfo
        PTFInfo = PTFdatabase.checkPTF(PTFOption)
        PTFType = PTFInfo.PTFType
        PTFUnit = PTFInfo.PTFUnit

        PTFOut = [("BCOption", PTFOption),
                  ("PTFType", PTFType),
                  ("UserUnitPlot", unitsPlot),
                  ("carbContent", carbContent)]

        # Write to XML file
        PTFXML = os.path.join(outputFolder, "ptfinfo.xml")
        common.writeXML(PTFXML, PTFOut)

        # Call Brooks-Corey function
        brooks_corey.function(outputFolder, inputShapefile, PTFOption,
                              BCPressArray, fcVal, sicVal, pwpVal,
                              carbContent, carbonConFactor)

        # Set output filename for display
        BCOut = os.path.join(outputFolder, "BrooksCorey.shp")
        arcpy.SetParameter(13, BCOut)

        log.info("Brooks-Corey operations completed successfully")

    except Exception:
        log.exception("Brooks-Corey tool failed")
        raise

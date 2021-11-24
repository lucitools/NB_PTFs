import arcpy
import os
import sys

import NB_PTFs.lib.log as log
import NB_PTFs.lib.common as common
import NB_PTFs.lib.progress as progress
import NB_PTFs.solo.calc_vg as calc_vg
import NB_PTFs.lib.PTFdatabase as PTFdatabase

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log, common, calc_vg, PTFdatabase])

def function(params):

    try:
        pText = common.paramsAsText(params)

        # Get inputs
        runSystemChecks = common.strToBool(pText[1])
        outputFolder = pText[2]
        inputShapefile = pText[3]
        VGChoice = pText[4]
        VGPressures = pText[5]
        fcVal = pText[6]
        sicVal = pText[7]
        pwpVal = pText[8]
        carbonContent = pText[9]
        carbonConFactor = pText[10]
        unitsPlot = pText[11]
        plotAxis = pText[12]
        MVGChoice =  common.strToBool(pText[13])

        # Create output folder
        if not os.path.exists(outputFolder):
            os.mkdir(outputFolder)

        common.runSystemChecks(outputFolder)

        # Set up logging output to file
        log.setupLogging(outputFolder)

        # Write input params to XML
        common.writeParamsToXML(params, outputFolder)

        # Simplify VGOption
        if VGChoice == "Wosten et al. (1999) topsoil":
            VGOption = "Wosten_1999_top"

        elif VGChoice == "Wosten et al. (1999) subsoil":
            VGOption = "Wosten_1999_sub"

        elif VGChoice == "Vereecken et al. (1989)":
            VGOption = "Vereecken_1989"

        elif VGChoice == "Zacharias and Wessolek (2007)":
            VGOption = "ZachariasWessolek_2007"

        elif VGChoice == "Weynants et al. (2009)":
            VGOption = "Weynants_2009"

        elif VGChoice == "Dashtaki et al. (2010)":
            VGOption = 'Dashtaki_2010_vg'

        elif VGChoice == "Hodnett and Tomasella (2002)":
            VGOption = 'HodnettTomasella_2002'

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

        # Unpack 'VG pressure heads' parameter
        if VGPressures is None:
            VGPressArray = []
        else:
            VGPressArray = VGPressures.split(' ')

        # Pull out PTFinfo
        PTFInfo = PTFdatabase.checkPTF(VGOption)
        PTFType = PTFInfo.PTFType
        PTFUnit = PTFInfo.PTFUnit

        PTFOut = [("VGOption", VGOption),
                  ("PTFType", PTFType),
                  ("UserUnitPlot", unitsPlot),
                  ("carbContent", carbContent)]

        # Write to XML file
        PTFXML = os.path.join(outputFolder, "ptfinfo.xml")
        common.writeXML(PTFXML, PTFOut)

        # Call van Genuchten function
        calc_vg.function(outputFolder, inputShapefile, VGOption, VGPressArray,
                         MVGChoice, fcVal, sicVal, pwpVal,
                         carbContent, carbonConFactor)

        # Loading shapefile automatically
        if MVGChoice == True:
            soilParamOut = os.path.join(outputFolder, "soil_mvg.shp")
        else:
            soilParamOut = os.path.join(outputFolder, "soil_vg.shp")
        

        arcpy.SetParameter(14, soilParamOut)

        log.info("van Genuchten operations completed successfully")

    except Exception:
        log.exception("van Genuchten tool failed")
        raise

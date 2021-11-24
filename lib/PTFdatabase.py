'''
Nature Braid PTFs Database
'''

import sys
import os
import configuration
import numpy as np
import arcpy
import math
import NB_PTFs.lib.log as log
import NB_PTFs.lib.common as common
from NB_PTFs.lib.external import six # Python 2/3 compatibility module

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log, common])

def setOutputFields(pressureArray, unit):
    # Returns an array of field names

    fields = ["warning"]

    for pressure in pressureArray:
        name = "WC_" + str(pressure) + str(unit)
        fields.append(name)

    return fields

def checkPTF(PTFOption):

    class PTF:
        def __init__(self, PTFType, PTFPressures, PTFUnit, PTFFields=None):
            self.PTFType = PTFType
            self.PTFPressures = PTFPressures
            self.PTFUnit = PTFUnit
            self.PTFFields = PTFFields

    if PTFOption == "Nguyen_2014":
        PTFType = "pointPTF"
        PTFPressures = [1, 3, 6, 10, 20, 33, 100, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "Adhikary_2008":
        PTFType = "pointPTF"
        PTFPressures = [10, 33, 100, 300, 500, 1000, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "Rawls_1982":
        PTFType = "pointPTF"
        PTFPressures = [10, 20, 33, 50, 100, 200, 400, 700, 1000, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "Hall_1977_top":
        PTFType = "pointPTF"
        PTFPressures = [5, 10, 33, 200, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "Hall_1977_sub":
        PTFType = "pointPTF"
        PTFPressures = [5, 10, 33, 200, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "GuptaLarson_1979":
        PTFType = "pointPTF"
        PTFPressures = [4, 7, 10, 20, 33, 60, 100, 200, 400, 700, 1000, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "Batjes_1996":
        PTFType = "pointPTF"
        PTFPressures = [0, 1, 3, 5, 10, 20, 33, 50, 250, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "SaxtonRawls_2006":
        PTFType = "pointPTF"
        PTFPressures = [0, 33, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "Pidgeon_1972":
        PTFType = "pointPTF"
        PTFPressures = [10, 33, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif str(PTFOption[0:8]) == "Lal_1978":
        PTFType = "pointPTF"
        PTFPressures = [0, 10, 33, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "AinaPeriaswamy_1985":
        PTFType = "pointPTF"
        PTFPressures = [33, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "ManriqueJones_1991":
        PTFType = "pointPTF"
        PTFPressures = [33, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "vanDenBerg_1997":
        PTFType = "pointPTF"
        PTFPressures = [10, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "TomasellaHodnett_1998":
        PTFType = "pointPTF"
        PTFPressures = [0, 1, 3, 6, 10, 33, 100, 500, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "Reichert_2009_OM":
        PTFType = "pointPTF"
        PTFPressures = [6, 10, 33, 100, 500, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "Reichert_2009":
        PTFType = "pointPTF"
        PTFPressures = [10, 33, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "Botula_2013":
        PTFType = "pointPTF"
        PTFPressures = [1, 3, 6, 10, 20, 33, 100, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "ShwethaVarija_2013":
        PTFType = "pointPTF"
        PTFPressures = [33, 100, 300, 500, 1000, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "Dashtaki_2010_point":
        PTFType = "pointPTF"
        PTFPressures = [10, 30, 100, 300, 500, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "Santra_2018_OC":
        PTFType = "pointPTF"
        PTFPressures = [33, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif PTFOption == "Santra_2018":
        PTFType = "pointPTF"
        PTFPressures = [33, 1500]
        PTFUnit = "kPa"
        PTFFields = setOutputFields(PTFPressures, PTFUnit)

    elif str(PTFOption[0:11]) == "Wosten_1999":
        PTFType = "vgPTF"
        PTFPressures = "SMRC"
        PTFUnit = "cm" # original units of Wosten et al. (1999)
        PTFFields = ["warning"]

    elif PTFOption == "Vereecken_1989":
        PTFType = "vgPTF"
        PTFPressures = "SMRC"
        PTFUnit = "cm" # original units of Vereecken et al. (1989)
        PTFFields = ["warning"]

    elif PTFOption == "ZachariasWessolek_2007":
        PTFType = "vgPTF"
        PTFPressures = "SMRC"
        PTFUnit = "kPa" # original units of Zacharias and Wessolek (2007)
        PTFFields = ["warning"]

    elif PTFOption == "Weynants_2009":
        PTFType = "vgPTF"
        PTFPressures = "SMRC"
        PTFUnit = "cm" # original units of Weynants et al. (2009)
        PTFFields = ["warning"]

    elif PTFOption == "Dashtaki_2010_vg":
        PTFType = "vgPTF"
        PTFPressures = "SMRC"
        PTFUnit = "cm" # original units of Dashtaki et al. (2010)
        PTFFields = ["warning"]

    elif PTFOption == "HodnettTomasella_2002":
        PTFType = "vgPTF"
        PTFPressures = "SMRC"
        PTFUnit = "kPa" # original units of Hodnett and Tomasella (2002)
        PTFFields = ["warning"]

    elif PTFOption == "Cosby_1984":
        PTFType = "ksatPTF"
        PTFPressures = "Ksat"
        PTFUnit = "mmhr"
        PTFFields = ["warning", "K_sat"]

    elif PTFOption == "Puckett_1985":
        PTFType = "ksatPTF"
        PTFPressures = "Ksat"
        PTFUnit = "mmhr"
        PTFFields = ["warning", "K_sat"]

    elif PTFOption == "Jabro_1992":
        PTFType = "ksatPTF"
        PTFPressures = "Ksat"
        PTFUnit = "mmhr"
        PTFFields = ["warning", "K_sat"]

    elif PTFOption == "CampbellShiozawa_1994":
        PTFType = "ksatPTF"
        PTFPressures = "Ksat"
        PTFUnit = "mmhr"
        PTFFields = ["warning", "K_sat"]

    elif PTFOption == "FerrerJulia_2004_1":
        PTFType = "ksatPTF"
        PTFPressures = "Ksat"
        PTFUnit = "mmhr"
        PTFFields = ["warning", "K_sat"]

    elif PTFOption == "FerrerJulia_2004_2":
        PTFType = "ksatPTF"
        PTFPressures = "Ksat"
        PTFUnit = "mmhr"
        PTFFields = ["warning", "K_sat"]

    elif PTFOption == "Ahuja_1989":
        PTFType = "ksatPTF"
        PTFPressures = "Ksat"
        PTFUnit = "mmhr"
        PTFFields = ["warning", "K_sat"]

    elif PTFOption == "MinasnyMcBratney_2000":
        PTFType = "ksatPTF"
        PTFPressures = "Ksat"
        PTFUnit = "mmhr"
        PTFFields = ["warning", "K_sat"]

    elif PTFOption == "Brakensiek_1984":
        PTFType = "ksatPTF"
        PTFPressures = "Ksat"
        PTFUnit = "mmhr"
        PTFFields = ["warning", "K_sat"]

    elif PTFOption == "Cosby_1984_SandC_BC":
        PTFType = "bcPTF"
        PTFPressures = "bc"
        PTFUnit = "cm"
        PTFFields = ["warning", "WC_res", "WC_sat", "lambda_BC", "hb_BC"]

    elif PTFOption == "Cosby_1984_SSC_BC":
        PTFType = "bcPTF"
        PTFPressures = "bc"
        PTFUnit = "cm"
        PTFFields = ["warning", "WC_res", "WC_sat", "lambda_BC", "hb_BC"]

    elif PTFOption == "RawlsBrakensiek_1985_BC":
        PTFType = "bcPTF"
        PTFPressures = "bc"
        PTFUnit = "cm"
        PTFFields = ["warning", "WC_res", "WC_sat", "lambda_BC", "hb_BC"]

    elif PTFOption == "CampbellShiozawa_1992_BC":
        PTFType = "bcPTF"
        PTFPressures = "bc"
        PTFUnit = "cm"
        PTFFields = ["warning", "WC_res", "WC_sat", "lambda_BC", "hb_BC"]

    elif PTFOption == "Saxton_1986_BC":
        PTFType = "bcPTF"
        PTFPressures = "bc"
        PTFUnit = "kPa"
        PTFFields = ["warning", "WC_res", "WC_sat", "lambda_BC", "hb_BC"]

    elif PTFOption == "SaxtonRawls_2006_BC":
        PTFType = "bcPTF"
        PTFPressures = "bc"
        PTFUnit = "kPa"
        PTFFields = ["warning", "WC_res", "WC_sat", "lambda_BC", "hb_BC"]

    else:
        log.error("PTF option not recognised: " + str(PTFOption))

    return PTF(PTFType, PTFPressures, PTFUnit, PTFFields)

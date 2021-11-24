'''
configuration.py adds the parent directory of the NB_PTFs repo in sys.path so that modules can be imported using "from NB_PTFs..."
'''

import arcpy
import sys
import os

try:
    toolbox = "NB_PTFs"

    currentPath = os.path.dirname(os.path.abspath(__file__)) # should go to <base path>\NB_SEEA
    basePath = os.path.dirname(currentPath)

    nbPTFsPath = os.path.normpath(os.path.join(basePath, "NB_PTFs"))

    libPath = os.path.join(nbPTFsPath, "lib")
    logPath = os.path.join(nbPTFsPath, "logs")
    tablesPath = os.path.join(nbPTFsPath, "tables")
    displayPath = os.path.join(nbPTFsPath, "display")
    mxdsPath = os.path.join(displayPath, "mxds")
    dataPath = os.path.join(nbPTFsPath, "data")
    stylesheetsPath = os.path.join(nbPTFsPath, "stylesheets")

    oldScratchPath = os.path.join(nbPTFsPath, "NBscratch")
    scratchPath = os.path.join(basePath, "NBscratch")

    userSettingsFile = os.path.join(nbPTFsPath, "user_settings.xml")
    filenamesFile = os.path.join(nbPTFsPath, "filenames.xml")
    labelsFile = os.path.join(nbPTFsPath, "labels.xml")

    # Add basePath to sys.path so that modules can be imported using "import NB_PTFs.scripts.modulename" etc.
    if os.path.normpath(basePath) not in sys.path:
        sys.path.append(os.path.normpath(basePath))

    # Tolerance
    clippingTolerance = 0.00000000001

except Exception:
    arcpy.AddError("Configuration file not read successfully")
    raise

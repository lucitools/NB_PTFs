import arcpy
import os
import sys
import shutil
import datetime # For writing current date/time to inputs.xml
import time # For logging warnings that are very close together
import xml.etree.cElementTree as ET

from NB_PTFs.lib.external import six # Python 2/3 compatibility module
import configuration
import NB_PTFs.lib.log as log

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log])

def strToBool(s):
    ''' Converts a true/false string to an actual Boolean'''
    
    if s == "True" or s == "true":
         return True
    elif s == "False" or s == "false":
         return False
    else:
         raise ValueError


def runSystemChecks(folder=None, rerun=False):

    import NB_PTFs.lib.progress as progress

    # Set overwrite output
    arcpy.env.overwriteOutput = True

    ### Set workspaces so that temporary files are written to the scratch geodatabase ###
    if arcpy.ProductInfo() == "ArcServer":
        log.info('arcpy.env.scratchWorkspace on server: ' + str(arcpy.env.scratchWorkspace))

        # Set current workspace
        arcpy.env.workspace = arcpy.env.scratchGDB
    else:

        # If rerunning a tool, check if scratch workspace has been set. If it has, use it as it is (with temporary rasters and feature classes from the previous run).
        scratchGDB = None

        if rerun:
            xmlFile = progress.getProgressFilenames(folder).xmlFile

            if os.path.exists(xmlFile):
                scratchGDB = readXML(xmlFile, 'ScratchGDB')

                if not arcpy.Exists(scratchGDB):
                    log.error('Previous scratch GDB ' + str(scratchGDB) + ' does not exist. Tool cannot be rerun.')
                    log.error('Exiting tool')
                    sys.exit()

        if scratchGDB is None:

            # Set scratch path from values in user settings file if values present
            scratchPath = None
            try:
                if os.path.exists(configuration.userSettingsFile):

                    tree = ET.parse(configuration.userSettingsFile)
                    root = tree.getroot()
                    scratchPath = root.find("scratchPath").text

            except Exception:
                pass # If any errors occur, ignore them. Just use the default scratch path.

            # Set scratch path if needed
            if scratchPath is None:
                scratchPath = configuration.scratchPath

            # Create scratch path folder
            if not os.path.exists(scratchPath):
                os.makedirs(scratchPath)

            # Remove old date/time stamped scratch folders if they exist and if they do not contain lock ArcGIS lock files.
            for root, dirs, files in os.walk(scratchPath):
                for dir in dirs:

                    # Try to rename folder. If this is possible then no locks are held on it and it can then be removed.
                    try:
                        fullDirPath = os.path.join(scratchPath, dir)
                        renamedDir = os.path.join(scratchPath, 'ready_for_deletion')
                        os.rename(fullDirPath, renamedDir)
                    except Exception:
                        # import traceback
                        # log.warning(traceback.format_exc())
                        pass
                    else:
                        try:
                            shutil.rmtree(renamedDir)
                        except Exception:
                            # import traceback
                            # log.warning(traceback.format_exc())
                            pass

            # Create new date/time stamped scratch folder for the scratch GDB to live in
            dateTimeStamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            scratchGDBFolder = os.path.join(scratchPath, 'scratch_' + dateTimeStamp)
            if not os.path.exists(scratchGDBFolder):
                os.mkdir(scratchGDBFolder)

            # Create scratch GDB
            scratchGDB = os.path.join(scratchGDBFolder, 'scratch.gdb')
            if not os.path.exists(scratchGDB):
                arcpy.CreateFileGDB_management(os.path.dirname(scratchGDB), os.path.basename(scratchGDB))

            # Try to remove old scratch path if still exists
            try:
                shutil.rmtree(configuration.oldScratchPath, ignore_errors=True)
            except Exception:
                pass

        # Set scratch and current workspaces
        arcpy.env.scratchWorkspace = scratchGDB
        arcpy.env.workspace = scratchGDB

        # Scratch folder
        scratchFolder = arcpy.env.scratchFolder
        if not os.path.exists(scratchFolder):
            os.mkdir(scratchFolder)

        # Remove all in_memory data sets
        arcpy.Delete_management("in_memory")    

    # Check disk space for disk with scratch workspace
    freeSpaceGb = 3
    if getFreeDiskSpaceGb(arcpy.env.scratchWorkspace) < freeSpaceGb:
        log.warning("Disk containing scratch workspace has less than " + str(freeSpaceGb) + "Gb free space. This may cause this tool to fail.")


def getFreeDiskSpaceGb(dirname):

    """Return folder/drive free space (in megabytes)."""

    import ctypes
    import platform

    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(dirname), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value / 1024 / 1024 / 1024
    else:
        st = os.statvfs(dirname)
        return st.f_bavail * st.f_frsize / 1024 / 1024 / 1024

def paramsAsText(params):

    paramsText = []
    for param in params:
        paramsText.append(param.valueAsText)

    return paramsText


def listFeatureLayers(localVars):

    layersToDelete = []
    for v in localVars:
        if isinstance(localVars[v], arcpy.mapping.Layer):
            layersToDelete.append(v)

    return layersToDelete

def indentXML(elem, level=0, more_sibs=False):

    ''' Taken from https://stackoverflow.com/questions/749796/pretty-printing-xml-in-python '''

    i = "\n"
    if level:
        i += (level - 1) * '  '
    num_kids = len(elem)
    if num_kids:
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
            if level:
                elem.text += '  '
        count = 0
        for kid in elem:
            indentXML(kid, level + 1, count < num_kids - 1)
            count += 1
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
            if more_sibs:
                elem.tail += '  '
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
            if more_sibs:
                elem.tail += '  '


def addPath(obj, folder):

    ''' Joins the folder path onto each of the objects' properties '''

    for attr, filename in six.iteritems(obj.__dict__):

        # Add file name to folder path
        filename = os.path.join(folder, filename)
        
        # Re-set the object's attribute value
        setattr(obj, attr, filename)

    return obj

def readXML(XMLfile, nodeNameList, showErrors=True):

    ''' 
    Fetches values of nodes from an XML file.
    These nodes must live as children of the top level node (typically <data>).

    nodeNameList can either be a list of node names (strings) or a single node name (i.e. a string, no list brackets needed).
    '''

    try:
        # Open file for reading
        try:
            tree = ET.parse(XMLfile)
        except IOError:
            if showErrors:
                arcpy.AddError("XML File \"" + XMLfile + "\" does not exist or cannot be opened")
            raise

        root = tree.getroot()

        # Handle nodeNameList being a single node name (a string)
        if type(nodeNameList) is not list:
            nodeNameList = [nodeNameList]

        valueList = []
        for nodeName in nodeNameList:

            # Find value of node in XML file
            node = root.find(nodeName)
            if node is None:
                value = ''
            else:
                value = node.text
            valueList.append(value)

        if len(valueList) == 0:
            return None
        elif len(valueList) == 1:
            return valueList[0]
        else:
            return valueList

    except Exception:
        if showErrors:
            arcpy.AddError("Data not read from XML file")
        raise

def writeXML(XMLfile, nodeNameValueList):

    ''' 
    Writes nodename/value pairs to an XML file. The file is created if it does not alredy exist.
    These nodes must live as children of the top level node (typically <data>).

    nodeNameValueList should have the format [(nodename, value), (nodename, value), ...]
    '''

    def createElement(parent, name):

        try:
            found = False
            for child in parent.getchildren():
                if child.tag == name:
                    found = True
            if not found:
                parent.append(ET.Element(name))

        except Exception:
            log.error("Could not create element " + name)
            raise


    def setElementValue(parent, name, value, attrib=None):

        try:
            elem = findElement(parent, name)
            elem.text = value

            if attrib is not None:
                elem.set('displayName', attrib)

        except Exception:
            log.error("Could not set value for element " + name)
            raise


    def findElement(parent, name):

        try:
            elem = None
            for child in parent.getchildren():
                if child.tag == name:
                    elem = child
            return elem

        except Exception:
            log.error("Could not find element " + name)
            raise

    # WriteXML main function code
    try:
        # Create file if does not exist
        try:
            if not os.path.exists(XMLfile):
                root = ET.Element("data")
                tree = ET.ElementTree(root)
                tree.write(XMLfile, encoding="utf-8", xml_declaration=True)
            else:
                # Open file for reading
                tree = ET.parse(XMLfile)
                root = tree.getroot()

        except Exception:
            log.error("Problem creating or opening XML file")
            raise

        # Loop through node/value list
        for nodeNameValue in nodeNameValueList:

            nodeName = nodeNameValue[0]
            value = nodeNameValue[1]

            if len(nodeNameValue) == 3:
                attrib = nodeNameValue[2]

            else:
                attrib = None

            # Check if node exists
            node = findElement(root, nodeName)
            if node is None:
                createElement(root, nodeName) # Create new node

            setElementValue(root, nodeName, value, attrib)

        try:
            # Make XML file more human-readable
            indentXML(root)

            # Save the XML file
            tree.write(XMLfile, encoding='utf-8', xml_declaration=True)

        except Exception:
            log.error("Problem saving XML file")
            raise     

    except Exception:
        log.error("Data not written to XML file")
        raise

def writeParamsToXML(params, folder, toolName=None):


    xmlFile = os.path.join(folder, 'inputs.xml')
    paramValueList = []

    # Adding date and time to list
    dateTime = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    paramValueList.append(('DateTimeRun', dateTime, 'Date/time ran'))

    if toolName is not None:
        paramValueList.append(('ToolName', toolName, 'Tool name'))

    for param in params:
        paramValueList.append((param.name, param.valueAsText, param.displayName))

    writeXML(xmlFile, paramValueList)

def logWarnings(folder, warningMsg):

    ''' Writes the warning message to warnings.xml '''
    time.sleep(0.05) # To correct for warnings that are within milliseconds of each other

    xmlFile = os.path.join(folder, 'warnings.xml')
    warningList = []

    # Adding dateTime info
    dateTime = datetime.datetime.now().strftime('%H%M%S%f')
    warningTime = 'Warning_' + dateTime

    warningList.append((warningTime, warningMsg))

    writeXML(xmlFile, warningList)

def CheckField(checkfile, fieldname):

    try:
        List = arcpy.ListFields(checkfile, fieldname)
        if len(List) == 1:
            exist = 1
        else:
            exist = 0
        return exist

    except Exception:
        log.error("Error occurred while checking if field " + fieldname + " exists in file " + checkfile)
        raise

def CleanFields(checkfile, fieldstokeep):

    try:
        desc = arcpy.Describe(checkfile)
        List = arcpy.ListFields(checkfile)
        fieldNameList = []

        for field in List:
            if not field.required:
                if field.name not in fieldstokeep:
                    fieldNameList.append(field.name)

        # dBASE tables require a field other than an OID and Shape.  If this is
        #  the case, retain an extra field (the first one in the original list)
        if desc.dataType in ["ShapeFile", "DbaseTable"]:
            fieldNameList = fieldNameList[1:]

        arcpy.DeleteField_management(checkfile, fieldNameList)

    except Exception:
        log.error("Error occurred while attempting to clean unwanted fields in file " + checkfile)
        raise


def writeFields(outputShp, fieldArray):

    # Writes fields to the outputShp

    # Write warning fields
    arcpy.AddField_management(outputShp, "warning", "TEXT")

    # Write the rest of the fields (1 to end)

    for x in range(1, len(fieldArray)):
        arcpy.AddField_management(outputShp, fieldArray[x], "DOUBLE", 10, 6)

def getInputValue(folder, paramName):
 
    inputsXML = os.path.join(folder, 'inputs.xml')

    if os.path.exists(inputsXML):
        inputValue = readXML(inputsXML, paramName)
    else:
        inputValue = None
 
    return inputValue

def writeWarning(outputShp, warningArray):

    # Write the warnings to output shapefile
    arcpy.AddField_management(outputShp, "warning", "TEXT")

    outputFields = ["warning"]
    
    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
        for row in cursor:
            row[0] = warningArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

def getOIDField(shapefile):
    OID = str(arcpy.Describe(shapefile).oidFieldName)

    return OID

def writeOutputWC(outputShp, WC_1kPaArray, WC_3kPaArray, WC_10kPaArray, WC_33kPaArray, WC_100kPaArray, WC_200kPaArray, WC_1000kPaArray, WC_1500kPaArray):
    # Write outputs of VG or BC equations to output shapefile

    # Add fields
    arcpy.AddField_management(outputShp, "WC_1kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_3kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_10kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_33kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_100kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_200kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_1000kPa", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "WC_1500kPa", "DOUBLE", 10, 6)

    outputFields = ["WC_1kPa", "WC_3kPa", "WC_10kPa", "WC_33kPa", "WC_100kPa", "WC_200kPa", "WC_1000kPa", "WC_1500kpa"]

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, outputFields) as cursor:
        for row in cursor:
            row[0] = WC_1kPaArray[recordNum]
            row[1] = WC_3kPaArray[recordNum]
            row[2] = WC_10kPaArray[recordNum]
            row[3] = WC_33kPaArray[recordNum]
            row[4] = WC_100kPaArray[recordNum]
            row[5] = WC_200kPaArray[recordNum]
            row[6] = WC_1000kPaArray[recordNum]
            row[7] = WC_1500kPaArray[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info("Water content at default pressures written to output shapefile")

def writeOutputCriticalWC(outputShp, wc_sat, wc_fc, wc_sic, wc_pwp, wc_DW, wc_RAW, wc_NRAW, wc_PAW):

    # Add fields
    arcpy.AddField_management(outputShp, "wc_satCalc", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "wc_fcCalc", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "wc_sicCalc", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "wc_pwpCalc", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "wc_DW", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "wc_RAW", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "wc_NRAW", "DOUBLE", 10, 6)
    arcpy.AddField_management(outputShp, "wc_PAW", "DOUBLE", 10, 6)

    wcFields = ["wc_satCalc", "wc_fcCalc", "wc_sicCalc", "wc_pwpCalc", "wc_DW", "wc_RAW", "wc_NRAW", "wc_PAW"]

    recordNum = 0
    with arcpy.da.UpdateCursor(outputShp, wcFields) as cursor:
        for row in cursor:
            row[0] = wc_sat[recordNum]
            row[1] = wc_fc[recordNum]
            row[2] = wc_sic[recordNum]
            row[3] = wc_pwp[recordNum]
            row[4] = wc_DW[recordNum]
            row[5] = wc_RAW[recordNum]
            row[6] = wc_NRAW[recordNum]
            row[7] = wc_PAW[recordNum]

            cursor.updateRow(row)
            recordNum += 1

    log.info('Water contents for critical thresholds written to output shapefile')

def writeWCCSV(outputFolder, soilName, pressureArray, WCArray, pressureTitle, WCTitle):
    import csv

    # This function writes a CSV containing pressure and WC

    # Loop through and reshape the array
    headings = [pressureTitle, WCTitle]
    outArray = []

    for i in range(0, len(pressureArray)):
        pressure = pressureArray[i]
        waterContent = WCArray[i]
        dataPoint = [pressure, waterContent]
        outArray.append(dataPoint)

    # Write to output CSV
    outName = str(soilName) + '.csv'
    outCSV = os.path.join(outputFolder, outName)

    with open(outCSV, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headings)

        for i in range(0, len(outArray)):
            row = outArray[i]
            writer.writerow(row)

        msg = 'Output CSV with water contents and pressure saved to: ' + str(outCSV)
        log.info(msg)

    csv_file.close()
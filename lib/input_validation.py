import os

from NB_PTFs.lib.external import six # Python 2/3 compatibility module

def checkFilePaths(self):

    for i in range(0, len(self.params)):
        if self.params[i].datatype in ["Folder", "Feature Layer", "Feature Class", "Raster Layer", "Raster Dataset", "File"]:

            # Check for spaces
            if " " in str(self.params[i].valueAsText) and not self.params[i].name.lower().endswith("overseer_xml_file"):
                self.params[i].setErrorMessage("Value: " + str(self.params[i].valueAsText) + ". The file path contains spaces. Please choose a file path without spaces")

            # Check for files being in OneDrive or Dropbox folders
            if "OneDrive" in str(self.params[i].valueAsText):
                self.params[i].setErrorMessage("Value: " + str(self.params[i].valueAsText) + ". The file/folder is located inside a OneDrive folder. Please move the file/folder outside of OneDrive.")
            if "Dropbox" in str(self.params[i].valueAsText):
                self.params[i].setErrorMessage("Value: " + str(self.params[i].valueAsText) + ". The file/folder is located inside a Dropbox folder. Please move the file/folder outside of Dropbox.")


def checkFolderContents(self, paramNo, feedbackType="warning"):

    folderName = str(self.params[paramNo].value)

    # Check if we're chosen to rerun the tool using the ReRun parameter.
    # If we are rerunning the tool, don't do the check on the folder contents
    rerun = False
    for i in range(0, len(self.params)):
        if self.params[i].name == 'Rerun_tool':
            if self.params[i].valueAsText == 'true':
                rerun = True

    if not rerun:
        # Check if the folder is empty or not
        if folderName != 'None':
            if os.path.exists(folderName):

                foundContent = False
                for root, dirs, files in os.walk(folderName):
                    for file in files:
                        foundContent = True

                if foundContent:
                    if feedbackType == "warning":
                        self.params[paramNo].setWarningMessage("This folder is not empty. Its contents will be deleted.")
                    elif feedbackType == "error":
                        self.params[paramNo].setErrorMessage("This folder is not empty. Please empty it or choose another folder. This error is shown as ArcMap lock problems would arise if the same folder was used. The locks cannot easily be removed.")


def checkRasterFilenameLength(self):

    import os

    for i in range(0, len(self.params)):
        if self.params[i].datatype in ["Raster Layer", "Raster Dataset"] and self.params[i].direction == "Output":

            rasterFilePath = self.params[i].valueAsText
            if rasterFilePath is not None:

                if len(rasterFilePath) > 128:
                    self.params[i].setErrorMessage("The raster and its file path must be less than 128 characters")

                # If raster not in a geodatabase
                if '.gdb' not in rasterFilePath:

                    fileName = os.path.basename(rasterFilePath)
                    if '.' not in fileName: # i.e. is a GRID raster
                        if len(fileName) > 13:
                            self.params[i].setErrorMessage("The name of the raster must be 13 characters or less")


def checkThresholdValues(self, tools):

    '''
    tools parameter can be either one tool specified as a string, or a list of tools (strings)
    '''

    def checkMinMaxValues(idx, value, minValue=None, maxValue=None):

        if (minValue is not None and value <= minValue) or (maxValue is not None and value >= maxValue):
            self.params[idx].setErrorMessage("Value must be greater than " + str(minValue) + " and must be less than " + str(maxValue))

        if (minValue is not None and value <= minValue) and maxValue is None:
            self.params[idx].setErrorMessage("Value must be greater than " + str(minValue))

        if minValue is None and (maxValue is not None and value >= maxValue):
            self.params[idx].setErrorMessage("Value must be less than " + str(minValue))

    # Check if tools is a list or string. If it is a string, make it the only value in a list.
    if isinstance(tools, six.string_types):
        tools = [tools]

    for tool in tools:

        if tool == "SoilMoisture":

            for i in range(0, len(self.params)):

                if self.params[i].name == "RAW_fraction":
                    fraction = self.params[i].value
                    checkMinMaxValues(i, fraction, 0.2, 0.8)

                if self.params[i].name == "Rooting_depth":
                    fraction = self.params[i].value
                    checkMinMaxValues(i, fraction, 0)
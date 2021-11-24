import arcpy
import configuration
import os
from NB_PTFs.lib.refresh_modules import refresh_modules

class CalcKsat(object):

    class ToolValidator:
        """Class for validating a tool's parameter values and controlling the behavior of the tool's dialog."""
    
        def __init__(self, parameters):
            """Setup the Geoprocessor and the list of tool parameters."""
            self.params = parameters
    
        def initializeParameters(self):
            """Refine the properties of a tool's parameters.
            This method is called when the tool is opened."""
            return
        
        def updateParameters(self):
            """Modify the values and properties of parameters before internal validation is performed.
            This method is called whenever a parameter has been changed."""

            return
    
        def updateMessages(self):
            """Modify the messages created by internal validation for each tool parameter.
            This method is called after internal validation."""

            import NB_PTFs.lib.input_validation as input_validation
            refresh_modules(input_validation)

            input_validation.checkFilePaths(self)
            input_validation.checkThresholdValues(self, "CalcKsat")
    
    def __init__(self):
        self.label = u'04 Calculate saturated hydraulic conductivity (Ksat)'
        self.canRunInBackground = False

    def getParameterInfo(self):

        params = []

        # 0 Output__Success
        param = arcpy.Parameter()
        param.name = u'Output__Success'
        param.displayName = u'Output: Success'
        param.parameterType = 'Derived'
        param.direction = 'Output'
        param.datatype = u'Boolean'
        params.append(param)

        # 1 Run_system_checks
        param = arcpy.Parameter()
        param.name = u'Run_system_checks'
        param.displayName = u'Run_system_checks'
        param.parameterType = 'Derived'
        param.direction = 'Output'
        param.datatype = u'Boolean'
        param.value = u'True'
        params.append(param)

        # 2 Output_folder
        param = arcpy.Parameter()
        param.name = u'Output_folder'
        param.displayName = u'Output folder'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Folder'
        params.append(param)

        # 3 Input_folder
        param = arcpy.Parameter()
        param.name = u'Input_folder'
        param.displayName = u'Input folder: results from calculation using point-PTF or vg-PTFs or bc-PTFs'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Folder'
        params.append(param)

        # 4 Ksat_of_choice
        param = arcpy.Parameter()
        param.name = u'Ksat_of_choice'
        param.displayName = u'Select PTF to estimate Ksat'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'String'
        param.value = u'Cosby et al. (1984)'
        param.filter.list = [u'Cosby et al. (1984)', u'Puckett et al. (1985)',
                             u'Jabro (1992)', u'Campbell and Shiozawa (1994)',
                             u'Ferrer Julia et al. (2004) - Sand',
                             u'Ferrer Julia et al. (2004) - Sand, clay, OM',
                             u'Brakensiek et al. (1984)',
                             u'Ahuja et al. (1989)', u'Minasny and McBratney (2000)',
                             u'Wosten et al. (1999)']
        params.append(param)

        # 5 Carbon_content
        param = arcpy.Parameter()
        param.name = u'Carbon_content'
        param.displayName = u'If the selected PTF requires OC or OM, select which type is present in your dataset:'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'String'
        param.value = u'Organic carbon'
        param.filter.list = [u'Organic carbon', u'Organic matter']
        params.append(param)

        # 6 Conversion_factor
        param = arcpy.Parameter()
        param.name = u'Conversion_factor'
        param.displayName = u'If the selected PTF requires OC or OM, enter the appropriate conversion factor to change OM to OC (or vice-versa):'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Double'
        param.value = u'1.724'
        params.append(param)

        # 7 Output_Layer_Ksat
        param = arcpy.Parameter()
        param.name = u'Output_Layer_Ksat'
        param.displayName = u'Ksat'
        param.parameterType = 'Derived'
        param.direction = 'Output'
        param.datatype = u'Feature Layer'
        params.append(param)

        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
             return validator(parameters).updateMessages()

    def execute(self, parameters, messages):

        import NB_PTFs.tools.t_calc_ksat as t_calc_ksat
        refresh_modules(t_calc_ksat)

        t_calc_ksat.function(parameters)

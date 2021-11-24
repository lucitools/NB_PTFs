import arcpy
import configuration
import os
from NB_PTFs.lib.refresh_modules import refresh_modules

class calcVG_PTFs(object):

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

            # Populate converstion factor automatically when either OM or OC is chosen has been chosen
            CarbParamNo = None
            ConvFactorParamNo = None
            for i in range(0, len(self.params)):
                if self.params[i].name == 'Carbon_content':
                    CarbParamNo = i
                if self.params[i].name == 'Conversion_factor':
                    ConvFactorParamNo = i

            CarbPairs = [('Organic carbon', 1.724),
                         ('Organic matter', 0.58)]

            if CarbParamNo is not None and ConvFactorParamNo is not None:
                # If this is the most recently changed param ...
                if not self.params[CarbParamNo].hasBeenValidated:

                    # Update the linking code with the correct value
                    for CarbPair in CarbPairs:
                        if self.params[CarbParamNo].valueAsText == CarbPair[0]:
                            self.params[ConvFactorParamNo].value = CarbPair[1]
            
            input_validation.checkFilePaths(self)
    
    def __init__(self):
        self.label = u'01 Calculate van Genuchten parameters and plot SMRC'
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

        # 3 Input_shapefile
        param = arcpy.Parameter()
        param.name = u'Input_shapefile'
        param.displayName = u'Input soil shapefile'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Feature Class'
        params.append(param)

        # 4 VG_of_choice
        param = arcpy.Parameter()
        param.name = u'VG_of_choice'
        param.displayName = u'PTFs of choice for van Genuchten model'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'String'
        param.value = u'Wosten et al. (1999) topsoil'
        param.filter.list = [u'Wosten et al. (1999) topsoil', u'Wosten et al. (1999) subsoil',
                             u'Vereecken et al. (1989)', u'Zacharias and Wessolek (2007)',
                             u'Weynants et al. (2009)',
                             u'Dashtaki et al. (2010)', u'Hodnett and Tomasella (2002)']
        params.append(param)

        # 5 Pressure_heads_VG
        param = arcpy.Parameter()
        param.name = u'Pressure_heads_VG'
        param.displayName = u'Specify pressures to calculate water content using van Genuchten and hydraulic conductivity using Mualem-van Genuchten model (space delimited)'
        param.parameterType = 'Optional'
        param.direction = 'Input'
        param.datatype = u'String'
        param.value = u'1 3 10 33 100 200 1000 1500'
        params.append(param)

        # 6 FieldCapacity
        param = arcpy.Parameter()
        param.name = u'FieldCapacity'
        param.displayName = u'Value of pressure (kPa) at field capacity'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'String'
        param.value = u'33'
        params.append(param)

        # 7 SIC
        param = arcpy.Parameter()
        param.name = u'SIC'
        param.displayName = u'Value of pressure (kPa) at water stress-induced stomata closure'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'String'
        param.value = u'100'
        params.append(param)

        # 8 PWP
        param = arcpy.Parameter()
        param.name = u'PWP'
        param.displayName = u'Value of pressure (kPa) at permanent wilting point'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'String'
        param.value = u'1500'
        params.append(param)        

        # 9 Carbon_content
        param = arcpy.Parameter()
        param.name = u'Carbon_content'
        param.displayName = u'If the selected PTF requires OC or OM, select which type is present in your dataset:'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'String'
        param.value = u'Organic carbon'
        param.filter.list = [u'Organic carbon', u'Organic matter']
        params.append(param)

        # 10 Conversion_factor
        param = arcpy.Parameter()
        param.name = u'Conversion_factor'
        param.displayName = u'If the selected PTF requires OC or OM, enter the appropriate conversion factor to change OM to OC (or vice-versa):'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Double'
        param.value = u'1.724'
        params.append(param)

        # 11 Pressure_units_plot
        param = arcpy.Parameter()
        param.name = u'Pressure_units_plot'
        param.displayName = u'Pressure unit for plotting purposes'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'String'
        param.value = u'kPa'
        param.filter.list = [u'kPa',
                             u'cm',
                             u'm']
        params.append(param)

        # 12 Plot_axis
        param = arcpy.Parameter()
        param.name = u'Plot_axis'
        param.displayName = u'Create water content and pressure plots with water content or hydraulic conductivity on the X-axis or Y-axis:'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'String'
        param.value = u'Y-axis'
        param.filter.list = [u'Y-axis',
                             u'X-axis']
        params.append(param)

        # 13 Calculate_MVG
        param = arcpy.Parameter()
        param.name = u'Calculate_MVG'
        param.displayName = u'Estimate unsaturated hydraulic conductivity and generate hydraulic conductivity curve using PTFs for Mualem van Genuchten model'
        param.parameterType = 'Required'
        param.direction = 'Input'
        param.datatype = u'Boolean'
        param.value = u'False'
        params.append(param)

        # 14 Output_Layer_SoilParam
        param = arcpy.Parameter()
        param.name = u'Output_Layer_SoilParam'
        param.displayName = u'Soil'
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

        import NB_PTFs.tools.t_calc_vg as t_calc_vg
        refresh_modules(t_calc_vg)

        t_calc_vg.function(parameters)

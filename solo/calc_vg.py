'''
Function to calculate van Genuchten parameters and SMRC
'''

import sys
import os
import arcpy
import csv
import numpy as np
import NB_PTFs.lib.log as log
import NB_PTFs.lib.common as common
import NB_PTFs.lib.vanGenuchten as vanGenuchten
import NB_PTFs.lib.vg_PTFs as vg_PTFs
import NB_PTFs.lib.checks_PTFs as checks_PTFs
from NB_PTFs.lib.external import six # Python 2/3 compatibility module

from NB_PTFs.lib.refresh_modules import refresh_modules
refresh_modules([log, common, vanGenuchten, vg_PTFs, checks_PTFs])

def function(outputFolder, inputShp, VGOption, VGPressArray, MVGChoice, fcVal, sicVal, pwpVal, carbContent, carbonConFactor):

    try:
        # Set temporary variables
        prefix = os.path.join(arcpy.env.scratchGDB, "soil_")

        # Set output filename
        if MVGChoice == True:
            outputShp = os.path.join(outputFolder, "soil_mvg.shp")
        else:
            outputShp = os.path.join(outputFolder, "soil_vg.shp")

        # Copy the input shapefile to the output folder
        arcpy.CopyFeatures_management(inputShp, outputShp)

        ##############################################
        ### Calculate the van Genuchten parameters ###
        ##############################################

        # Get the nameArray
        nameArray = []
        with arcpy.da.SearchCursor(outputShp, "soilname") as searchCursor:
            for row in searchCursor:
                name = row[0]

                nameArray.append(name)

        # Initialise the van Genuchten parameter arrays
        # All VG PTFs should return these arrays        
        WC_residualArray = []
        WC_satArray = []
        alpha_VGArray = []
        n_VGArray = []
        m_VGArray = []

        # Call VG PTF here depending on VGOption
        if str(VGOption[0:11]) == "Wosten_1999":
            # Has option to calculate Mualem-van Genuchten
            WC_residualArray, WC_satArray, alpha_VGArray, n_VGArray, m_VGArray, l_MvGArray, K_satArray = vg_PTFs.Wosten_1999(outputShp, VGOption, carbonConFactor, carbContent, MVGChoice)

        elif VGOption == "Vereecken_1989":
            WC_residualArray, WC_satArray, alpha_VGArray, n_VGArray, m_VGArray = vg_PTFs.Vereecken_1989(outputShp, VGOption, carbonConFactor, carbContent)

        elif VGOption == "ZachariasWessolek_2007":
            WC_residualArray, WC_satArray, alpha_VGArray, n_VGArray, m_VGArray = vg_PTFs.ZachariasWessolek_2007(outputShp, VGOption, carbonConFactor, carbContent)
        
        elif VGOption == "Weynants_2009":
            # Has option to calculate Mualem-van Genuchten
            WC_residualArray, WC_satArray, alpha_VGArray, n_VGArray, m_VGArray, l_MvGArray, K_satArray = vg_PTFs.Weynants_2009(outputShp, VGOption, carbonConFactor, carbContent, MVGChoice)

        elif VGOption == "Dashtaki_2010_vg":
            WC_residualArray, WC_satArray, alpha_VGArray, n_VGArray, m_VGArray = vg_PTFs.Dashtaki_2010(outputShp, VGOption, carbonConFactor, carbContent)

        elif VGOption == "HodnettTomasella_2002":
            WC_residualArray, WC_satArray, alpha_VGArray, n_VGArray, m_VGArray = vg_PTFs.HodnettTomasella_2002(outputShp, VGOption, carbonConFactor, carbContent)

        else:
            log.error("Van Genuchten option not recognised: " + str(VGOption))
            sys.exit()
 
        # Write VG parameter results to output shapefile
        vanGenuchten.writeVGParams(outputShp, WC_residualArray, WC_satArray, alpha_VGArray, n_VGArray, m_VGArray)

        # Plot VG parameters
        vanGenuchten.plotVG(outputFolder, WC_residualArray,
                            WC_satArray, alpha_VGArray, n_VGArray,
                            m_VGArray, nameArray, fcVal, sicVal, pwpVal)

        ###############################################
        ### Calculate water content using VG params ###
        ###############################################

        # Calculate water content at default pressures
        WC_1kPaArray = []
        WC_3kPaArray = []
        WC_10kPaArray = []
        WC_33kPaArray = []
        WC_100kPaArray = []
        WC_200kPaArray = []
        WC_1000kPaArray = []
        WC_1500kPaArray = []

        for x in range(0, len(nameArray)):
            WC_1kPa = vanGenuchten.calcVGfxn(1.0, WC_residualArray[x], WC_satArray[x], alpha_VGArray[x], n_VGArray[x], m_VGArray[x])
            WC_3kPa = vanGenuchten.calcVGfxn(3.0, WC_residualArray[x], WC_satArray[x], alpha_VGArray[x], n_VGArray[x], m_VGArray[x])
            WC_10kPa = vanGenuchten.calcVGfxn(10.0, WC_residualArray[x], WC_satArray[x], alpha_VGArray[x], n_VGArray[x], m_VGArray[x])
            WC_33kPa = vanGenuchten.calcVGfxn(33.0, WC_residualArray[x], WC_satArray[x], alpha_VGArray[x], n_VGArray[x], m_VGArray[x])
            WC_100kPa = vanGenuchten.calcVGfxn(100.0, WC_residualArray[x], WC_satArray[x], alpha_VGArray[x], n_VGArray[x], m_VGArray[x])
            WC_200kPa = vanGenuchten.calcVGfxn(200.0, WC_residualArray[x], WC_satArray[x], alpha_VGArray[x], n_VGArray[x], m_VGArray[x])
            WC_1000kPa = vanGenuchten.calcVGfxn(1000.0, WC_residualArray[x], WC_satArray[x], alpha_VGArray[x], n_VGArray[x], m_VGArray[x])
            WC_1500kPa = vanGenuchten.calcVGfxn(1500.0, WC_residualArray[x], WC_satArray[x], alpha_VGArray[x], n_VGArray[x], m_VGArray[x])

            WC_1kPaArray.append(WC_1kPa)
            WC_3kPaArray.append(WC_3kPa)
            WC_10kPaArray.append(WC_10kPa)
            WC_33kPaArray.append(WC_33kPa)
            WC_100kPaArray.append(WC_100kPa)
            WC_200kPaArray.append(WC_200kPa)
            WC_1000kPaArray.append(WC_1000kPa)
            WC_1500kPaArray.append(WC_1500kPa)

        common.writeOutputWC(outputShp, WC_1kPaArray, WC_3kPaArray, WC_10kPaArray, WC_33kPaArray, WC_100kPaArray, WC_200kPaArray, WC_1000kPaArray, WC_1500kPaArray)

        # Write water content at user-input pressures

        # Initialise the pressure head array
        x = np.array(VGPressArray)
        vgPressures = x.astype(np.float)

        # For the headings
        headings = ['Name']

        for pressure in vgPressures:
            headName = 'WC_' + str(pressure) + "kPa"
            headings.append(headName)

        wcHeadings = headings[1:]

        # Initialise water content arrays
        wcArrays = []

        # Calculate soil moisture content at custom VG pressures
        for x in range(0, len(nameArray)):
            wcValues = vanGenuchten.calcPressuresVG(nameArray[x], WC_residualArray[x], WC_satArray[x], alpha_VGArray[x], n_VGArray[x], m_VGArray[x], vgPressures)
            wcArrays.append(wcValues)

        # Write to output CSV
        outCSV = os.path.join(outputFolder, 'WaterContent.csv')

        with open(outCSV, 'wb') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headings)

            for i in range(0, len(nameArray)):
                row = wcArrays[i]
                writer.writerow(row)

            msg = 'Output CSV with water content saved to: ' + str(outCSV)
            log.info(msg)

        csv_file.close()

        ##################################################
        ### Calculate water content at critical points ###
        ##################################################

        # Initialise water content arrays
        wc_satCalc = []
        wc_fcCalc = []
        wc_sicCalc = []
        wc_pwpCalc = []

        wc_DW = []
        wc_RAW = []
        wc_NRAW = []
        wc_PAW = []

        for i in range(0, len(nameArray)):
            wc_sat = vanGenuchten.calcVGfxn(0, WC_residualArray[i], WC_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i])
            wc_fc = vanGenuchten.calcVGfxn(float(fcVal), WC_residualArray[i], WC_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i])
            wc_sic = vanGenuchten.calcVGfxn(float(sicVal), WC_residualArray[i], WC_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i])
            wc_pwp = vanGenuchten.calcVGfxn(float(pwpVal), WC_residualArray[i], WC_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i])

            drainWater = wc_sat - wc_fc
            readilyAvailWater = wc_fc - wc_sic
            notRAW = wc_sic - wc_pwp
            PAW = wc_fc - wc_pwp

            checks_PTFs.checkNegValue("Drainable water", drainWater, nameArray[i])
            checks_PTFs.checkNegValue("Readily available water", readilyAvailWater, nameArray[i])
            checks_PTFs.checkNegValue("Not readily available water", notRAW, nameArray[i])
            checks_PTFs.checkNegValue("Not readily available water", PAW, nameArray[i])

            wc_satCalc.append(wc_sat)
            wc_fcCalc.append(wc_fc)
            wc_sicCalc.append(wc_sic)
            wc_pwpCalc.append(wc_pwp)
            wc_DW.append(drainWater)
            wc_RAW.append(readilyAvailWater)
            wc_NRAW.append(notRAW)
            wc_PAW.append(PAW)

        common.writeOutputCriticalWC(outputShp, wc_satCalc, wc_fcCalc, wc_sicCalc, wc_pwpCalc, wc_DW, wc_RAW, wc_NRAW, wc_PAW)

        ############################################
        ### Calculate using Mualem-van Genuchten ###
        ############################################

        if MVGChoice == True:
            if VGOption in ["Wosten_1999_top", "Wosten_1999_sub", "Weynants_2009"]:
                # Allow for calculation of MVG
                log.info("Calculating and plotting MVG")

                # Write l_MvGArray to outputShp
                arcpy.AddField_management(outputShp, "l_MvG", "DOUBLE", 10, 6)

                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, "l_MvG") as cursor:
                    for row in cursor:
                        row[0] = l_MvGArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                # Plot MVG
                vanGenuchten.plotMVG(outputFolder, K_satArray, alpha_VGArray, n_VGArray, m_VGArray, l_MvGArray, WC_satArray, WC_residualArray, nameArray)

                # Calculate K at default pressures
                
                # Calculate at the pressures using the function
                K_1kPaArray = []
                K_3kPaArray = []
                K_10kPaArray = []
                K_33kPaArray = []
                K_100kPaArray = []
                K_200kPaArray = []
                K_1000kPaArray = []
                K_1500kPaArray = []

                for i in range(0, len(nameArray)):
                    K_1kPa = vanGenuchten.calcKhfxn(1.0, K_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i], l_MvGArray[i])
                    K_3kPa = vanGenuchten.calcKhfxn(3.0, K_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i], l_MvGArray[i])
                    K_10kPa = vanGenuchten.calcKhfxn(10.0, K_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i], l_MvGArray[i])
                    K_33kPa = vanGenuchten.calcKhfxn(33.0, K_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i], l_MvGArray[i])
                    K_100kPa = vanGenuchten.calcKhfxn(100.0, K_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i], l_MvGArray[i])
                    K_200kPa = vanGenuchten.calcKhfxn(200.0, K_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i], l_MvGArray[i])
                    K_1000kPa = vanGenuchten.calcKhfxn(1000.0, K_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i], l_MvGArray[i])
                    K_1500kPa = vanGenuchten.calcKhfxn(1500.0, K_satArray[i], alpha_VGArray[i], n_VGArray[i], m_VGArray[i], l_MvGArray[i])

                    K_1kPaArray.append(K_1kPa)
                    K_3kPaArray.append(K_3kPa)
                    K_10kPaArray.append(K_10kPa)
                    K_33kPaArray.append(K_33kPa)
                    K_100kPaArray.append(K_100kPa)
                    K_200kPaArray.append(K_200kPa)
                    K_1000kPaArray.append(K_1000kPa)
                    K_1500kPaArray.append(K_1500kPa)

                # Write to the shapefile
                MVGFields = ["K_1kPa", "K_3kPa", "K_10kPa", "K_33kPa", "K_100kPa", "K_200kPa", "K_1000kPa", "K_1500kPa"]
                
                # Add fields
                for field in MVGFields:
                    arcpy.AddField_management(outputShp, field, "DOUBLE", 10, 6)

                recordNum = 0
                with arcpy.da.UpdateCursor(outputShp, MVGFields) as cursor:
                    for row in cursor:
                        row[0] = K_1kPaArray[recordNum]
                        row[1] = K_3kPaArray[recordNum]
                        row[2] = K_10kPaArray[recordNum]
                        row[3] = K_33kPaArray[recordNum]
                        row[4] = K_100kPaArray[recordNum]
                        row[5] = K_200kPaArray[recordNum]
                        row[6] = K_1000kPaArray[recordNum]
                        row[7] = K_1500kPaArray[recordNum]

                        cursor.updateRow(row)
                        recordNum += 1

                log.info("Unsaturated hydraulic conductivity at default pressures written to output shapefile")

                # Calculate K at custom pressures

                # Initialise the pressure head array
                x = np.array(VGPressArray)
                vgPressures = x.astype(np.float)

                # For the headings
                headings = ['Name']

                for pressure in vgPressures:
                    headName = 'K_' + str(pressure) + "kPa"
                    headings.append(headName)

                kHeadings = headings[1:]

                # Initialise K arrays
                kArrays = []

                # Calculate K content at custom VG pressures
                for x in range(0, len(nameArray)):
                    kValues = vanGenuchten.calcPressuresMVG(nameArray[x], K_satArray[x], alpha_VGArray[x], n_VGArray[x], m_VGArray[x], l_MvGArray[x], vgPressures)
                    kArrays.append(kValues)
                
                # Write to output CSV
                outCSV = os.path.join(outputFolder, 'K_MVG.csv')

                with open(outCSV, 'wb') as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(headings)

                    for i in range(0, len(nameArray)):
                        row = kArrays[i]
                        writer.writerow(row)

                    msg = 'Output CSV with unsaturated hydraulic conductivity saved to: ' + str(outCSV)
                    log.info(msg)

                csv_file.close()

            else:
                log.error("Selected PTF does not calculate Mualem-van Genuchten parameters")
                log.error("Please select a different PTF")
                sys.exit()

    except Exception:
        arcpy.AddError("van Genuchten function failed")
        raise

    finally:
        # Remove feature layers from memory
        try:
            for lyr in common.listFeatureLayers(locals()):
                arcpy.Delete_management(locals()[lyr])
                exec(lyr + ' = None') in locals()
        except Exception:
            pass
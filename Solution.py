from __future__ import absolute_import, division, print_function
from datetime import datetime
import math
import csv
from ScenarioTree import ScenarioTree
from Constants import Constants
from Tool import Tool
from Instance import Instance
import openpyxl as opxl
from ast import literal_eval
import numpy as np
import pandas as pd
#from matplotlib import pyplot as plt


#This class define a solution to MRP
class Solution(object):

    #constructor
    def __init__(self, instance=None, 
                 solACFEstablishment_x_wi = None, 
                 solVehicleAssignment_thetavar_wmi = None, 
                 solApheresisAssignment_y_wti = None, 
                 solTransshipmentHI_b_wtcrhi = None, 
                 solTransshipmentII_bPrime_wtcrii = None, 
                 solTransshipmentHH_bDoublePrime_wtcrhh = None, 
                 solPatientTransfer_q_wtjclum = None, 
                 solUnsatisfiedPatient_mu_wtjcl = None, 
                 solPlateletInventory_eta_wtcru = None, 
                 solOutdatedPlatelet_sigmavar_wtu = None, 
                 solServedPatient_upsilon_wtjcPcru = None, 
                 solPatientPostponement_zeta_wtjcu = None, 
                 solPlateletApheresisExtraction_lambda_wtcu = None, 
                 solPlateletWholeExtraction_Rhovar_wtch = None, 
                 Final_ACFEstablishmentCost = 0, 
                 Final_Vehicle_AssignmentCost = 0, 
                 Final_ApheresisAssignmentCost = 0, 
                 Final_TransshipmentHICost = 0, 
                 Final_TransshipmentIICost = 0, 
                 Final_TransshipmentHHCost = 0, 
                 Final_PatientTransferCost = 0, 
                 Final_UnsatisfiedPatientsCost = 0, 
                 Final_PlateletInventoryCost = 0, 
                 Final_OutdatedPlateletCost = 0, 
                 Final_ServedPatientCost = 0, 
                 Final_PatientPostponementCost = 0, 
                 Final_PlateletApheresisExtractionCost = 0, 
                 Final_PlateletWholeExtractionCost = 0, 
                 scenarioset=None, 
                 scenriotree=None, 
                 partialsolution=False):
        if Constants.Debug: print("\n We are in 'Solution' Class -- Constructor")
        
        self.ACFEstablishmentCost = -1
        self.Vehicle_AssignmentCost = -1

        self.ApheresisAssignmentCost = -1
        self.TransshipmentHICost = -1
        self.TransshipmentIICost = -1
        self.TransshipmentHHCost = -1

        self.PatientTransferCost = -1
        self.UnsatisfiedPatientsCost = -1
        self.PlateletInventoryCost = -1
        self.OutdatedPlateletCost = -1
        self.ServedPatientCost = -1
        self.PatientPostponementCost = -1
        self.PlateletApheresisExtractionCost = -1
        self.PlateletWholeExtractionCost = -1

        self.InSamplePercentOnTimeTransfer = -1
        self.InSamplePercentOnTimeSurgery = -1
        self.InSamplePercentSameBloodTypeInfusion = -1

        self.TotalCost =-1

        self.Instance = instance

        self.IsSDDPSolution = False


        self.SValue = []        
        if not instance is None:
            self.FixedApheresisAssignments = [[-1 for i in instance.ACFPPointSet] for t in self.Instance.TimeBucketSet]
            #self.FixedTransshipmentHIs = [[[[[-1 for i in instance.ACFPPointSet] for h in self.Instance.HospitalSet] for r in self.Instance.PlateletAgeSet] for c in instance.BloodGPSet] for t in self.Instance.TimeBucketSet]
            #self.FixedTransshipmentIIs = [[[[[-1 for iprime in instance.ACFPPointSet] for i in self.Instance.ACFPPointSet] for r in self.Instance.PlateletAgeSet] for c in instance.BloodGPSet] for t in self.Instance.TimeBucketSet]
            #self.FixedTransshipmentHHs = [[[[[-1 for hprime in instance.HospitalSet] for h in self.Instance.HospitalSet] for r in self.Instance.PlateletAgeSet] for c in instance.BloodGPSet] for t in self.Instance.TimeBucketSet]
        else:
            self.FixedApheresisAssignments = []
            #self.FixedTransshipmentHIs = []
            #self.FixedTransshipmentIIs = []
            #self.FixedTransshipmentHHs = []

        self.InSampleAverageACFEstablishment = []
        self.InSampleAverageVehicleAssignment = []
        
        self.InSampleAverageApheresisAssignment = []
        self.InSampleAverageTransshipmentHI = []
        self.InSampleAverageTransshipmentII = []
        self.InSampleAverageTransshipmentHH = []
                
        self.InSampleAveragePatientTransfer = []
        self.InSampleAverageUnsatisfiedPatients = []
        self.InSampleAveragePlateletInventory = []
        self.InSampleAverageOutdatedPlatelet = []
        self.InSampleAverageServedPatient = []
        self.InSampleAveragePatientPostponement = []
        self.InSampleAveragePlateletApheresisExtraction = []
        self.InSampleAveragePlateletWholeExtraction = []
        
        self.InSampleAverageOnTimeTransfer = []
        self.InSampleAverageOnTimeSurgery = []
        self.InSampleAverageSameBloodTypeInfusion = []
        self.InSampleAverageSameBloodTypeInfusion_tuc = []

        # The objecie value as outputed by GRB,
        self.GRBCost = -1
        self.GRBGap = -1
        self.GRBTime = 0
        self.TotalTime = 0
        self.GRBNrConstraints = -1
        self.GRBNrVariables = -1
        self.MLLocalSearchLB = -1
        self.MLLocalSearchTimeBestSol = -1
        self.PHCost = -1
        self.PHNrIteration = -1

        self.SDDPLB = -1
        self.SDDPExpUB = -1
        self.SDDPSafeUB = -1
        self.SDDPNrIteration = -1

        self.LocalSearchIteration = -1

        self.SDDPTimeBackward = -1
        self.SDDPTimeForwardNoTest = -1
        self.SDDPTimeForwardTest = -1 

        #The set of scenario on which the solution is found
        self.Scenarioset = scenarioset
        self.ScenarioTree = scenriotree

        if not self.Scenarioset is None:
            self.SenarioNrset = range(len(self.Scenarioset))
        if Constants.Debug: print("\n We are in 'Solution' Class -- Constructor")

        self.ACFEstablishment_x_wi = solACFEstablishment_x_wi
        self.VehicleAssignment_thetavar_wmi = solVehicleAssignment_thetavar_wmi

        self.ApheresisAssignment_y_wti = solApheresisAssignment_y_wti
        self.TransshipmentHI_b_wtcrhi = solTransshipmentHI_b_wtcrhi
        self.TransshipmentII_bPrime_wtcrii = solTransshipmentII_bPrime_wtcrii
        self.TransshipmentHH_bDoublePrime_wtcrhh = solTransshipmentHH_bDoublePrime_wtcrhh
        
        self.PatientTransfer_q_wtjclum = solPatientTransfer_q_wtjclum
        self.UnsatisfiedPatient_mu_wtjcl = solUnsatisfiedPatient_mu_wtjcl
        self.PlateletInventory_eta_wtcru = solPlateletInventory_eta_wtcru
        self.OutdatedPlatelet_sigmavar_wtu = solOutdatedPlatelet_sigmavar_wtu
        self.ServedPatient_upsilon_wtjcPcru = solServedPatient_upsilon_wtjcPcru
        self.PatientPostponement_zeta_wtjcu = solPatientPostponement_zeta_wtjcu
        self.PlateletApheresisExtraction_lambda_wtcu = solPlateletApheresisExtraction_lambda_wtcu
        self.PlateletWholeExtraction_Rhovar_wtch = solPlateletWholeExtraction_Rhovar_wtch

        
        self.FinalACFEstablishmentCost = Final_ACFEstablishmentCost
        self.FinalVehicleAssignmentCost = Final_Vehicle_AssignmentCost

        self.FinalApheresisAssignmentCost = Final_ApheresisAssignmentCost
        self.FinalTransshipmentHICost = Final_TransshipmentHICost
        self.FinalTransshipmentIICost = Final_TransshipmentIICost
        self.FinalTransshipmentHHCost = Final_TransshipmentHHCost

        self.FinalPatientTransferCost = Final_PatientTransferCost
        self.FinalUnsatisfiedPatientsCost = Final_UnsatisfiedPatientsCost
        self.FinalPlateletInventoryCost = Final_PlateletInventoryCost
        self.FinalOutdatedPlateletCost = Final_OutdatedPlateletCost
        self.FinalServedPatientCost = Final_ServedPatientCost
        self.FinalPatientPostponementCost = Final_PatientPostponementCost
        self.FinalPlateletApheresisExtractionCost = Final_PlateletApheresisExtractionCost
        self.FinalPlateletWholeExtractionCost = Final_PlateletWholeExtractionCost


        # Total cost calculation
        self.TotalCost = (  self.FinalACFEstablishmentCost
                          + self.FinalVehicleAssignmentCost 
                          + self.FinalApheresisAssignmentCost 
                          + self.FinalTransshipmentHICost 
                          + self.FinalTransshipmentIICost 
                          + self.FinalTransshipmentHHCost 
                          + self.FinalPatientTransferCost 
                          + self.FinalUnsatisfiedPatientsCost 
                          + self.FinalPlateletInventoryCost 
                          + self.FinalOutdatedPlateletCost 
                          + self.FinalServedPatientCost 
                          + self.FinalPatientPostponementCost 
                          + self.FinalPlateletApheresisExtractionCost 
                          + self.FinalPlateletWholeExtractionCost 
                          )
        if Constants.Debug: print("TotalCost: ", self.TotalCost)
            
        self.IsPartialSolution = partialsolution

    def GetSolutionFileName(self, description):
        if Constants.Debug: print("\n We are in 'Solution' Class -- GetSolutionFileName")

        if Constants.PrintDetailsExcelFiles:
            result = "./Solutions/" + description + "_Solution.xlsx"
        else:
            result = "./Solutions/" + description + "_Solution.txt"  # Changed .xlsx to .txt
        
        return result

    def GetGeneralInfoDf(self):
        if Constants.Debug: print("\n We are in 'Solution' Class -- GetGeneralInfoDf")

        model = "Rule"
        if self.ScenarioTree and self.ScenarioTree.Owner:
            model = self.ScenarioTree.Owner.Model

        # Create a dictionary for general information with appropriate keys and values
        general_info = {
            "Name": self.Instance.InstanceName,
            "Distribution": self.Instance.Distribution,
            "Model": model,
            "GRBCost": round(self.GRBCost, 2),
            "GRBTime_sec": self.GRBTime,
            "TotalTime_sec": self.TotalTime,
            "GRBGap": self.GRBGap,
            "GRBNrConstraints": self.GRBNrConstraints,
            "GRBNrVariables": self.GRBNrVariables,
            "SDDP_LB": self.SDDPLB,
            "SDDP_ExpUB": self.SDDPExpUB,
            "SDDP_SafeUB": self.SDDPSafeUB,
            "SDDP_NrIteration": self.SDDPNrIteration,
            "SDDPTimeBackward": self.SDDPTimeBackward,
            "SDDPTimeForwardNoTest": self.SDDPTimeForwardNoTest,
            "SDDPTimeForwardTest": self.SDDPTimeForwardTest,
            "LocalSearchIterations": self.LocalSearchIteration,
            "IsPartialSolution": self.IsPartialSolution,
            "ISSDDPSolution": self.IsSDDPSolution
        }

        # Convert the dictionary into a DataFrame
        # Since general_info represents a single row, we turn it into a DataFrame by passing
        # the values in a list (to form a row) and specify the column names using the keys from the dictionary
        generaldf = pd.DataFrame([general_info], columns=general_info.keys())

        # Optionally, if you want to set one of the columns as the index of the DataFrame, you can do so.
        # For example, if you want "Name" as the index:
        # generaldf.set_index("Name", inplace=True)
        
        return generaldf

    def PrintScenarioTreeInfo(self, file_handle):
        if Constants.Debug: print("\n We are in 'Solution' Class -- PrintScenarioTreeInfoToTxt")
        
        # Write the header for the scenario tree section
        file_handle.write("\nScenario Tree Information:\n")
        
        # Write each piece of scenario tree information
        file_handle.write(f"Name: {self.Instance.InstanceName}\n")
        file_handle.write(f"Seed: {self.ScenarioTree.Seed}\n")
        file_handle.write(f"Tree Structure: {self.ScenarioTree.TreeStructure}\n")
        file_handle.write(f"Average Scenario Tree: {self.ScenarioTree.AverageScenarioTree}\n")
        file_handle.write(f"Scenario Generation Method: {self.ScenarioTree.ScenarioGenerationMethod}\n")

    # return the path to binary file of the solution is saved
    def GetSolutionPickleFileNameStart(self, description, dataframename):
        
        result ="./Solutions/"+  description + "_" + dataframename
            
        return result
            
    # This function print the solution different pickle files
    def PrintToPickle(self, description):
        if Constants.Debug: print("\n We are in 'Solution' Class -- PrintToPickle")

        acfestablishment_df, vehicleassignment_df, apheresisAssignments_df, transshipmentHI_df, transshipmentII_df, \
        transshipmentHH_df, patientTransfer_df, unsatisfiedPatient_df, plateletInventory_df, outdatedPlatelet_df, \
        servedPatient_df, patientPostponement_df, plateletApheresisExtraction_df, plateletWholeExtraction_df, fixed_y_values_df = self.DataFrameFromList()

        acfestablishment_df.to_pickle(self.GetSolutionPickleFileNameStart(description, 'ACFEstablishment') )
        vehicleassignment_df.to_pickle(self.GetSolutionPickleFileNameStart(description, 'VehicleAssignment') )

        apheresisAssignments_df.to_pickle(self.GetSolutionPickleFileNameStart(description,  'ApheresisAssignments'))
        transshipmentHI_df.to_pickle(self.GetSolutionPickleFileNameStart(description,  'TransshipmentHI'))
        transshipmentII_df.to_pickle(self.GetSolutionPickleFileNameStart(description,  'TransshipmentII'))
        transshipmentHH_df.to_pickle(self.GetSolutionPickleFileNameStart(description,  'TransshipmentHH'))

        patientTransfer_df.to_pickle(self.GetSolutionPickleFileNameStart(description,  'PatientTransfer'))
        unsatisfiedPatient_df.to_pickle(self.GetSolutionPickleFileNameStart(description,  'UnsatisfiedPatient'))
        plateletInventory_df.to_pickle(self.GetSolutionPickleFileNameStart(description,  'PlateletInventory'))
        outdatedPlatelet_df.to_pickle(self.GetSolutionPickleFileNameStart(description,  'OutdatedPlatelet'))
        servedPatient_df.to_pickle(self.GetSolutionPickleFileNameStart(description,  'ServedPatient'))
        patientPostponement_df.to_pickle(self.GetSolutionPickleFileNameStart(description,  'PatientPostponement'))
        plateletApheresisExtraction_df.to_pickle(self.GetSolutionPickleFileNameStart(description,  'PlateletApheresisExtraction'))
        plateletWholeExtraction_df.to_pickle(self.GetSolutionPickleFileNameStart(description,  'PlateletWholeExtraction'))

        fixed_y_values_df.to_pickle(self.GetSolutionPickleFileNameStart(description,  'Fixed_y_values'))

        generaldf = self.GetGeneralInfoDf()
        generaldf.to_pickle(self.GetSolutionPickleFileNameStart(description, "Generic"))

        scenariotreeinfo = [self.Instance.InstanceName, self.ScenarioTree.Seed, self.ScenarioTree.TreeStructure,
                            self.ScenarioTree.AverageScenarioTree, self.ScenarioTree.ScenarioGenerationMethod]
        columnstab = ["Name", "Seed", "TreeStructure", "AverageScenarioTree", "ScenarioGenerationMethod"]
        scenariotreeinfo = pd.DataFrame(scenariotreeinfo, index=columnstab)
        scenariotreeinfo.to_pickle( self.GetSolutionPickleFileNameStart(description,  "ScenarioTree") )

    #This function print the solution in an Excel file in the folder "Solutions"
    def PrintToExcel(self, description):
        if Constants.Debug: print("\n We are in 'Solution' Class -- PrintToExcel")

        acfestablishment_df, vehicleassignment_df, apheresisAssignments_df, transshipmentHI_df, transshipmentII_df, \
        transshipmentHH_df, patientTransfer_df, unsatisfiedPatient_df, plateletInventory_df, outdatedPlatelet_df, \
        servedPatient_df, patientPostponement_df, plateletApheresisExtraction_df, plateletWholeExtraction_df, fixed_y_values_df = self.DataFrameFromList()

        file_name = self.GetSolutionFileName(description)
        
        with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
            
            acfestablishment_df.to_excel(writer, sheet_name='ACF Establishment')
            vehicleassignment_df.to_excel(writer, sheet_name='Vehicle Assignment')

            apheresisAssignments_df.to_excel(writer, sheet_name='Apheresis Assignments')
            transshipmentHI_df.to_excel(writer, sheet_name='Transshipment HI')
            transshipmentII_df.to_excel(writer, sheet_name='Transshipment II')
            transshipmentHH_df.to_excel(writer, sheet_name='Transshipment HH')

            patientTransfer_df.to_excel(writer, sheet_name='Patient Transfer')
            unsatisfiedPatient_df.to_excel(writer, sheet_name='Unsatisfied Patient')
            plateletInventory_df.to_excel(writer, sheet_name='Platelet Inventory')
            outdatedPlatelet_df.to_excel(writer, sheet_name='Outdated Platelet')
            servedPatient_df.to_excel(writer, sheet_name='Served Patient')
            patientPostponement_df.to_excel(writer, sheet_name='Patient Postponement')
            plateletApheresisExtraction_df.to_excel(writer, sheet_name='Apheresis Extraction')
            plateletWholeExtraction_df.to_excel(writer, sheet_name='Whole Blood Extraction')

            fixed_y_values_df.to_excel(writer, sheet_name='Fixed_y_value')

            generaldf = self.GetGeneralInfoDf()
            generaldf.to_excel(writer, sheet_name="Generic")

            # Constructing ScenarioTree info DataFrame correctly
            # The original approach seems to be incorrect as it would raise an error due to shape mismatch.
            # Assuming 'scenariotreeinfo' is intended to be a single row in the DataFrame:
            scenariotreeinfo = [[self.Instance.InstanceName, self.ScenarioTree.Seed, self.ScenarioTree.TreeStructure, self.ScenarioTree.AverageScenarioTree, self.ScenarioTree.ScenarioGenerationMethod]]
            columnstab = ["Name", "Seed", "TreeStructure", "AverageScenarioTree", "ScenarioGenerationMethod"]
            scenariotreeinfo_df = pd.DataFrame(scenariotreeinfo, columns=columnstab)
            scenariotreeinfo_df.to_excel(writer, sheet_name="ScenarioTree")

    #This function return a set of dataframes describing the content of the binary file
    def ReadPickleFiles(self, description):
        if Constants.Debug: print("\n We are in 'Solution' Class -- ReadPickleFiles")
        # The supplychain is defined in the sheet named "01_LL" and the data are in the sheet "01_SD"

        acfestablishment_df = pd.read_pickle(self.GetSolutionPickleFileNameStart(description, 'ACFEstablishment'))
        vehicleassignment_df = pd.read_pickle(self.GetSolutionPickleFileNameStart(description, 'VehicleAssignment'))

        apheresisAssignments_df = pd.read_pickle(self.GetSolutionPickleFileNameStart(description,  'ApheresisAssignments'))
        transshipmentHI_df = pd.read_pickle(self.GetSolutionPickleFileNameStart(description,  'TransshipmentHI'))
        transshipmentII_df = pd.read_pickle(self.GetSolutionPickleFileNameStart(description,  'TransshipmentII'))
        transshipmentHH_df = pd.read_pickle(self.GetSolutionPickleFileNameStart(description,  'TransshipmentHH'))

        patientTransfer_df = pd.read_pickle(self.GetSolutionPickleFileNameStart(description,  'PatientTransfer'))
        unsatisfiedPatient_df = pd.read_pickle(self.GetSolutionPickleFileNameStart(description,  'UnsatisfiedPatient'))
        plateletInventory_df = pd.read_pickle(self.GetSolutionPickleFileNameStart(description,  'PlateletInventory'))
        outdatedPlatelet_df = pd.read_pickle(self.GetSolutionPickleFileNameStart(description,  'OutdatedPlatelet'))
        servedPatient_df = pd.read_pickle(self.GetSolutionPickleFileNameStart(description,  'ServedPatient'))
        patientPostponement_df = pd.read_pickle(self.GetSolutionPickleFileNameStart(description,  'PatientPostponement'))
        plateletApheresisExtraction_df = pd.read_pickle(self.GetSolutionPickleFileNameStart(description,  'PlateletApheresisExtraction'))
        plateletWholeExtraction_df = pd.read_pickle(self.GetSolutionPickleFileNameStart(description,  'PlateletWholeExtraction'))

        fixed_y_values_df = pd.read_pickle(self.GetSolutionPickleFileNameStart(description,  'Fixed_y_values'))

        instanceinfo = pd.read_pickle(self.GetSolutionPickleFileNameStart(description, "Generic"))
        scenariotreeinfo = pd.read_pickle(self.GetSolutionPickleFileNameStart(description, "ScenarioTree"))


        return acfestablishment_df, vehicleassignment_df, apheresisAssignments_df, transshipmentHI_df, \
                transshipmentII_df, transshipmentHH_df, patientTransfer_df, unsatisfiedPatient_df, \
                plateletInventory_df, outdatedPlatelet_df, servedPatient_df, patientPostponement_df, \
                plateletApheresisExtraction_df, plateletWholeExtraction_df, fixed_y_values_df, \
                instanceinfo, scenariotreeinfo

    #This function prints a solution
    def Print(self):
        acfestablishment_df, vehicleassignment_df, apheresisAssignments_df, \
            transshipmentHI_df, transshipmentII_df, transshipmentHH_df, patientTransfer_df, \
                unsatisfiedPatient_df, plateletInventory_df, outdatedPlatelet_df, servedPatient_df, \
                    patientPostponement_df, plateletApheresisExtraction_df, plateletWholeExtraction_df, \
                        fixed_y_values_df = self.DataFrameFromList()

        if Constants.Debug:
            print("Fixed Trans (cost: %r): \n %r" % ( self.ACFEstablishmentCost, acfestablishment_df))
            print("Fixed Trans (cost: %r): \n %r" % ( self.Vehicle_AssignmentCost, vehicleassignment_df))
            print("Variable Transportation (cost: %r): \n %r" % (self.ApheresisAssignmentCost, apheresisAssignments_df))
            print("Variable Transportation (cost: %r): \n %r" % (self.TransshipmentHICost, transshipmentHI_df))
            print("Variable Transportation (cost: %r): \n %r" % (self.TransshipmentIICost, transshipmentII_df))
            print("Variable Transportation (cost: %r): \n %r" % (self.TransshipmentHHCost, transshipmentHH_df))
            print("Shortage quantities:  (cost: %r) \n %r" % (self.PatientTransferCost, patientTransfer_df))
            print("Shortage quantities:  (cost: %r) \n %r" % (self.UnsatisfiedPatientsCost, unsatisfiedPatient_df))
            print("Shortage quantities:  (cost: %r) \n %r" % (self.PlateletInventoryCost, plateletInventory_df))
            print("Shortage quantities:  (cost: %r) \n %r" % (self.OutdatedPlateletCost, outdatedPlatelet_df))
            print("Shortage quantities:  (cost: %r) \n %r" % (self.ServedPatientCost, servedPatient_df))
            print("Shortage quantities:  (cost: %r) \n %r" % (self.PatientPostponementCost, patientPostponement_df))
            print("Shortage quantities:  (cost: %r) \n %r" % (self.PlateletApheresisExtractionCost, plateletApheresisExtraction_df))
            print("Shortage quantities:  (cost: %r) \n %r" % (self.PlateletWholeExtractionCost, plateletWholeExtraction_df))
            print("Fixed y values: \n %r" % fixed_y_values_df)

    def ComputeCost(self):
        if Constants.Debug: print("\n We are in 'Solution' Class -- ComputeCost")
        
        self.TotalCost, self.ACFEstablishmentCost, self.Vehicle_AssignmentCost, \
        self.ApheresisAssignmentCost, self.TransshipmentHICost, self.TransshipmentIICost, self.TransshipmentHHCost, \
        self.PatientTransferCost, self.UnsatisfiedPatientsCost, self.PlateletInventoryCost, self.OutdatedPlateletCost, \
        self.ServedPatientCost, self.PatientPostponementCost, self.PlateletApheresisExtractionCost, self.PlateletWholeExtractionCost = self.GetCostInInterval(self.Instance.TimeBucketSet)
           
    #This function return the costs encountered in a specific time interval
    def GetCostInInterval(self, timerange):
        if Constants.Debug: print("\n We are in 'Solution' Class -- GetCostInInterval")
        
        acfEstablishmentcost = 0
        vehicleassignmentcost = 0

        apheresisAssignmentcost = 0
        transshipmentHIcost = 0
        transshipmentIIcost = 0
        transshipmentHHcost = 0

        patientTransfercost = 0
        unsatisfiedPatientscost = 0
        plateletInventorycost = 0
        outdatedPlateletcost = 0
        servedPatientcost = 0
        patientPostponementcost = 0
        plateletApheresisExtractioncost = 0
        plateletWholeExtractioncost = 0

        ##########################
        for w in range(len(self.Scenarioset)):
            for i in self.Instance.ACFPPointSet:
                acfEstablishmentcost += self.ACFEstablishment_x_wi[w][i] \
                                        * self.Instance.Fixed_Cost_ACF[i] \
                                        * self.Scenarioset[w].Probability
        
        ##########################
        for w in range(len(self.Scenarioset)):
            for m in self.Instance.RescueVehicleSet:
                for i in self.Instance.ACFPPointSet:
                    vehicleassignmentcost += self.VehicleAssignment_thetavar_wmi[w][m][i] \
                                            * self.Instance.VehicleAssignment_Cost[m] \
                                            * self.Scenarioset[w].Probability

        ##########################
        for w in range(len(self.Scenarioset)):
            for t in timerange:
                for i in self.Instance.ACFPPointSet:
                        apheresisAssignmentcost += self.ApheresisAssignment_y_wti[w][t][i] \
                                                    * self.Instance.ApheresisMachineAssignment_Cost[i] \
                                                    * self.Scenarioset[w].Probability
        
        ##########################
        for w in range(len(self.Scenarioset)):
            for t in timerange:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            for i in self.Instance.ACFPPointSet:
                                transshipmentHIcost += self.TransshipmentHI_b_wtcrhi[w][t][c][r][h][i] \
                                                    * self.Instance.Distance_A_H[i][h] \
                                                    * self.Scenarioset[w].Probability
        
       ##########################
        for w in range(len(self.Scenarioset)):
            for t in timerange:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for i in self.Instance.ACFPPointSet:
                            for iprime in self.Instance.ACFPPointSet:
                                transshipmentIIcost += self.TransshipmentII_bPrime_wtcrii[w][t][c][r][i][iprime] \
                                                    * self.Instance.Distance_A_A[i][iprime] \
                                                    * self.Scenarioset[w].Probability   

        ##########################
        for w in range(len(self.Scenarioset)):
            for t in timerange:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            for hprime in self.Instance.HospitalSet:
                                transshipmentHHcost += self.TransshipmentHH_bDoublePrime_wtcrhh[w][t][c][r][h][hprime] \
                                                    * self.Instance.Distance_H_H[h][hprime] \
                                                    * self.Scenarioset[w].Probability
                                     
        ##########################   
        for w in range(len(self.Scenarioset)):
            for t in timerange:
                for j in self.Instance.InjuryLevelSet:
                    for c in self.Instance.BloodGPSet:
                        for l in self.Instance.DemandSet:
                            for u in self.Instance.FacilitySet:
                                for m in self.Instance.RescueVehicleSet:
                                    if u < self.Instance.NrHospitals:
                                        patientTransfercost += self.PatientTransfer_q_wtjclum[w][t][j][c][l][u][m] \
                                                                * self.Instance.Distance_D_H[l][u] \
                                                                * self.Scenarioset[w].Probability
                                    else:
                                        patientTransfercost += self.PatientTransfer_q_wtjclum[w][t][j][c][l][u][m] \
                                                                * self.Instance.Distance_D_A[l][u-self.Instance.NrHospitals] \
                                                                * self.Scenarioset[w].Probability
        
        ##########################  
        for w in range(len(self.Scenarioset)):
            for t in timerange:
                for j in self.Instance.InjuryLevelSet:
                    for c in self.Instance.BloodGPSet:
                        for l in self.Instance.DemandSet:
                            unsatisfiedPatientscost += self.UnsatisfiedPatient_mu_wtjcl[w][t][j][c][l] \
                                                    * self.Instance.Casualty_Shortage_Cost[j][l] \
                                                    * self.Scenarioset[w].Probability
        
        ##########################  
        for w in range(len(self.Scenarioset)):
            for t in timerange:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for u in self.Instance.FacilitySet:
                            plateletInventorycost += self.PlateletInventory_eta_wtcru[w][t][c][r][u] \
                                                    * self.Instance.Platelet_Inventory_Cost[u] \
                                                    * self.Scenarioset[w].Probability
        
        ##########################  
        for w in range(len(self.Scenarioset)):
            for t in timerange:
                for u in self.Instance.FacilitySet:
                    outdatedPlateletcost += self.OutdatedPlatelet_sigmavar_wtu[w][t][u] \
                                            * self.Instance.Platelet_Wastage_Cost[u] \
                                            * self.Scenarioset[w].Probability
        
        ##########################  
        for w in range(len(self.Scenarioset)):
            for t in timerange:
                for j in self.Instance.InjuryLevelSet:
                    for cprime in self.Instance.BloodGPSet:
                        for c in self.Instance.BloodGPSet:
                            for r in self.Instance.PlateletAgeSet:
                                for u in self.Instance.FacilitySet:
                                    servedPatientcost += self.ServedPatient_upsilon_wtjcPcru[w][t][j][cprime][c][r][u] \
                                                        * self.Instance.Substitution_Weight[cprime][c] \
                                                        * self.Scenarioset[w].Probability

        ##########################  
        for w in range(len(self.Scenarioset)):
            for t in timerange:
                for j in self.Instance.InjuryLevelSet:
                    for c in self.Instance.BloodGPSet:
                        for u in self.Instance.FacilitySet:
                            patientPostponementcost += self.PatientPostponement_zeta_wtjcu[w][t][j][c][u] \
                                                    * self.Instance.Postponing_Cost_Surgery[j] \
                                                    * self.Scenarioset[w].Probability
        
        ##########################  
        for w in range(len(self.Scenarioset)):
            for t in timerange:
                for c in self.Instance.BloodGPSet:
                    for u in self.Instance.FacilitySet:
                        plateletApheresisExtractioncost += self.PlateletApheresisExtraction_lambda_wtcu[w][t][c][u] \
                                            * self.Instance.ApheresisExtraction_Cost[u] \
                                            * self.Scenarioset[w].Probability
        
        ##########################  
        for w in range(len(self.Scenarioset)):
            for t in timerange:
                for c in self.Instance.BloodGPSet:
                    for h in self.Instance.HospitalSet:
                        plateletWholeExtractioncost += self.PlateletWholeExtraction_Rhovar_wtch[w][t][c][h] \
                                                            * self.Instance.WholeExtraction_Cost[h] \
                                                            * self.Scenarioset[w].Probability

        totalcost = (acfEstablishmentcost + vehicleassignmentcost + apheresisAssignmentcost + transshipmentHIcost
                     + transshipmentIIcost + transshipmentHHcost + patientTransfercost + unsatisfiedPatientscost
                     + plateletInventorycost + outdatedPlateletcost + servedPatientcost + patientPostponementcost 
                     + plateletApheresisExtractioncost + plateletWholeExtractioncost)
        
        if Constants.Debug:
            print("self.Scenarioset[0].Probability: ", self.Scenarioset[0].Probability)
            print(f"ACF Establishment Cost: {acfEstablishmentcost}")
            print(f"Vehicle Assignment Cost: {vehicleassignmentcost}")
            print(f"Apheresis Assignment Cost: {apheresisAssignmentcost}")
            print(f"Transshipment HI Cost: {transshipmentHIcost}")
            print(f"Transshipment II Cost: {transshipmentIIcost}")
            print(f"Transshipment HH Cost: {transshipmentHHcost}")
            print(f"Patient Transfer Cost: {patientTransfercost}")
            print(f"Unsatisfied Patients Cost: {unsatisfiedPatientscost}")
            print(f"Platelet Inventory Cost: {plateletInventorycost}")
            print(f"Outdated Platelet Cost: {outdatedPlateletcost}")
            print(f"Served Patient Cost: {servedPatientcost}")
            print(f"Patient Postponement Cost: {patientPostponementcost}")
            print(f"Platelet Apheresis Extraction Cost: {plateletApheresisExtractioncost}")
            print(f"Platelet Whole Extraction Cost: {plateletWholeExtractioncost}")
            print(f"Total Cost: {totalcost}")  

        return totalcost, acfEstablishmentcost, vehicleassignmentcost, \
                apheresisAssignmentcost, transshipmentHIcost, transshipmentIIcost, transshipmentHHcost, \
                patientTransfercost, unsatisfiedPatientscost, plateletInventorycost, outdatedPlateletcost, \
                servedPatientcost, patientPostponementcost, plateletApheresisExtractioncost , plateletWholeExtractioncost
    
    #This function set the attributes of the solution from the excel/binary file
    def ReadFromFile(self, description):
        if Constants.Debug: print("\n We are in 'Solution' Class -- ReadFromFile")
        

        acfestablishment_df, vehicleassignment_df, apheresisAssignments_df, transshipmentHI_df, transshipmentII_df, \
        transshipmentHH_df, patientTransfer_df, unsatisfiedPatient_df, plateletInventory_df, outdatedPlatelet_df, \
        servedPatient_df, patientPostponement_df, plateletApheresisExtraction_df, plateletWholeExtraction_df, fixed_y_values_df, \
        instanceinfo, scenariotreeinfo = self.ReadPickleFiles(description)

        self.Instance = Instance(instanceinfo['Name'].iloc[0])
        
        self.Instance.LoadInstanceFromPickle(instanceinfo['Name'].iloc[0])

        scenariogenerationm = scenariotreeinfo.at['ScenarioGenerationMethod', 0]
        avgscenariotree = scenariotreeinfo.at['AverageScenarioTree', 0]
        scenariotreeseed = int(scenariotreeinfo.at['Seed', 0])
        branchingstructure  = literal_eval(str(scenariotreeinfo.at['TreeStructure', 0]))


        model = instanceinfo['Model'].iloc[0]

        self.ScenarioTree = ScenarioTree(instance=self.Instance,
                                         branchperlevel=branchingstructure,
                                         seed=scenariotreeseed,
                                         averagescenariotree=avgscenariotree,
                                         scenariogenerationmethod=scenariogenerationm,
                                         model=model)

        self.IsPartialSolution = instanceinfo['IsPartialSolution'].iloc[0]
        self.IsSDDPSolution = instanceinfo['ISSDDPSolution'].iloc[0] 
        self.GRBCost = instanceinfo['GRBCost'].iloc[0] 
        self.GRBTime_sec = instanceinfo['GRBTime_sec'].iloc[0]  
        #self.PHCost = instanceinfo.at['PH_Cost', 0]
        #self.PHNrIteration = instanceinfo.at['PH_NrIteration', 0]
        self.TotalTime_sec = instanceinfo['TotalTime_sec'].iloc[0] 
        self.GRBGap = instanceinfo['GRBGap'].iloc[0]  
        self.GRBNrConstraints = instanceinfo['GRBNrConstraints'].iloc[0] 
        self.GRBNrVariables = instanceinfo['GRBNrVariables'].iloc[0] 

        self.SDDPLB = instanceinfo['SDDP_LB'].iloc[0] 
        self.SDDPExpUB = instanceinfo['SDDP_ExpUB'].iloc[0] 
        self.SDDPSafeUB = instanceinfo['SDDP_SafeUB'].iloc[0] 
        self.SDDPNrIteration = instanceinfo['SDDP_NrIteration'].iloc[0]
        
        self.LocalSearchIteration = instanceinfo['LocalSearchIterations'].iloc[0] 
        #self.MLLocalSearchLB = instanceinfo['MLLocalSearchLB'].iloc[0]  
        #self.MLLocalSearchTimeBestSol = instanceinfo.at['MLLocalSearchTimeBestSol', 0]


        self.SDDPTimeBackward = instanceinfo['SDDPTimeBackward'].iloc[0]  
        self.SDDPTimeForwardNoTest = instanceinfo['SDDPTimeForwardNoTest'].iloc[0]
        self.SDDPTimeForwardTest = instanceinfo['SDDPTimeForwardTest'].iloc[0]
        
        if Constants.Debug:
            print(f"GRBCost: {self.GRBCost}")
            print(f"GRBTime (sec): {self.GRBTime_sec}")
            print(f"PHCost: {self.PHCost}")
            print(f"PHNrIteration: {self.PHNrIteration}")
            print(f"TotalTime (sec): {self.TotalTime_sec}")
            print(f"GRBGap: {self.GRBGap}")
            print(f"GRBNrConstraints: {self.GRBNrConstraints}")
            print(f"GRBNrVariables: {self.GRBNrVariables}")
            print(f"SDDPLB: {self.SDDPLB}")
            print(f"SDDPExpUB: {self.SDDPExpUB}")
            print(f"SDDPSafeUB: {self.SDDPSafeUB}")
            print(f"SDDPNrIteration: {self.SDDPNrIteration}")
            print(f"LocalSearchIterations: {self.LocalSearchIteration}")
            print(f"MLLocalSearchLB: {self.MLLocalSearchLB}")
            print(f"MLLocalSearchTimeBestSol: {self.MLLocalSearchTimeBestSol}")
            print(f"SDDPTimeBackward: {self.SDDPTimeBackward}")
            print(f"SDDPTimeForwardNoTest: {self.SDDPTimeForwardNoTest}")
            print(f"SDDPTimeForwardTest: {self.SDDPTimeForwardTest}")


        self.Scenarioset = self.ScenarioTree.GetAllScenarios(False)

        if self.IsPartialSolution:
            self.Scenarioset = [self.Scenarioset[0]]
        
        self.SenarioNrset = range(len(self.Scenarioset))
        

        self.ListFromDataFrame(acfestablishment_df, vehicleassignment_df, 
                               apheresisAssignments_df, transshipmentHI_df, transshipmentII_df, transshipmentHH_df, 
                               patientTransfer_df, unsatisfiedPatient_df, plateletInventory_df, outdatedPlatelet_df, servedPatient_df, 
                               patientPostponement_df, plateletApheresisExtraction_df, plateletWholeExtraction_df, fixed_y_values_df)

        if not self.IsPartialSolution:
            self.ComputeCost()

            if model != Constants.Two_Stage:
                self.ScenarioTree.FillApheresisAndPlateletToSendFromCRPSolution(self)

    #This function return the number of time bucket covered by the solution
    def GetConsideredTimeBucket(self):
        result = self.Instance.TimeBucketSet
        if self.IsPartialSolution:
            result = range(1)
        if self.IsSDDPSolution:
            result = [0]
        return result
    
    #This function return a set of dataframes descirbing the solution
    def DataFrameFromList(self):
        if Constants.Debug: print("\n We are in 'Solution' Class -- DataFrameFromList")
        

        scenarioset = range(len(self.Scenarioset))
        
        timebucketset = self.GetConsideredTimeBucket()              

        ######################################## ACF Establishment Data Frame
        solacfEstablishment = [[self.ACFEstablishment_x_wi[w][i] 
                                for w in scenarioset] 
                                for i in self.Instance.ACFPPointSet]
        #if Constants.Debug: print("solacfEstablishment: ", solacfEstablishment)
                
        ScenarioLables = list(range(len(self.Scenarioset))) 
        acfestablishment_df = pd.DataFrame(solacfEstablishment, index=self.Instance.ACFPPointSet, columns=ScenarioLables)
        acfestablishment_df.index.name = "ACFLoc" 
        #if Constants.Debug: print("acfestablishment_df:\n ", acfestablishment_df)
     
        ######################################## Rescue Vehile Assignment Data Frame
        solvehicleAssignment = [[self.VehicleAssignment_thetavar_wmi[w][m][i] 
                                    for m in self.Instance.RescueVehicleSet 
                                    for w in scenarioset] 
                                    for i in self.Instance.ACFPPointSet]
        #if Constants.Debug: print("solvehicleAssignment: ", solvehicleAssignment)
                
        iterablesvehicle = [range(len(self.Instance.RescueVehicleSet)), 
                            range(len(self.Scenarioset))]
        multiindexvehicleassignment = pd.MultiIndex.from_product(iterablesvehicle, names=['Vehicle', 'scenario'])
        vehicleassignment_df = pd.DataFrame(solvehicleAssignment, index=self.Instance.ACFPPointSet, columns=multiindexvehicleassignment)
        vehicleassignment_df.index.name = "ACFLoc" 
        #if Constants.Debug: print("vehicleassignment_df:\n ", vehicleassignment_df)

        ######################################## Apheresis Assignment Data Frame
        solapheresisassignment = []
        for i in self.Instance.ACFPPointSet:
            apheresisassignment_Values = []
            for w in scenarioset:
                for t in timebucketset:
                    apheresisassignment = self.ApheresisAssignment_y_wti[w][t][i]
                    apheresisassignment_Values.append(apheresisassignment)
            solapheresisassignment.append(apheresisassignment_Values)
        #if Constants.Debug: print("solapheresisassignment: ", solapheresisassignment)
                
        iterablesapheresisassignment = [range(len(self.Scenarioset)), 
                                        timebucketset]
        multiindexapheresisassign = pd.MultiIndex.from_product(iterablesapheresisassignment, names=['Scenario', 'Time'])
        apheresisAssignments_df = pd.DataFrame(solapheresisassignment, index=self.Instance.ACFPPointSet, columns=multiindexapheresisassign)
        apheresisAssignments_df.index.name = "ACFLoc"
        #if Constants.Debug: print("apheresisAssignments_df:\n ", apheresisAssignments_df)
        
        ######################################## Transshipment HI Data Farame
        soltransshipmentHI = []
        for h in self.Instance.HospitalSet:
            transshipmentHI_Values = []
            for w in scenarioset:
                for t in timebucketset:
                    for c in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for i in self.Instance.ACFPPointSet:
                                transshipmentHI = self.TransshipmentHI_b_wtcrhi[w][t][c][r][h][i]
                                transshipmentHI_Values.append(transshipmentHI)
            soltransshipmentHI.append(transshipmentHI_Values)
        #if Constants.Debug: print("soltransshipmentHI:\n ", soltransshipmentHI)
                
        iterables_5d = [
                        range(len(self.Scenarioset)),
                        timebucketset,
                        range(len(self.Instance.BloodGPSet)),
                        range(len(self.Instance.PlateletAgeSet)),
                        range(len(self.Instance.ACFPPointSet))
                        ]
        multiindex_5d = pd.MultiIndex.from_product(iterables_5d, names=['Scenario', 'Time', 'BloodGP', 'PlateletAge', 'ACFLoc'])
        transshipmentHI_df = pd.DataFrame(soltransshipmentHI, index=self.Instance.HospitalSet, columns=multiindex_5d)
        transshipmentHI_df.index.name = "fromHospitalLoc"
        #if Constants.Debug: print("transshipmentHI_df:\n ", transshipmentHI_df)
        
        ######################################## Transshipment II Data Farame
        soltransshipmentII = []
        for i in self.Instance.ACFPPointSet:
            transshipmentII_Values = []
            for w in scenarioset:
                for t in timebucketset:
                    for c in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for iprime in self.Instance.ACFPPointSet:
                                transshipmentII = self.TransshipmentII_bPrime_wtcrii[w][t][c][r][i][iprime]
                                transshipmentII_Values.append(transshipmentII)
            soltransshipmentII.append(transshipmentII_Values)
        #if Constants.Debug: print("soltransshipmentII:\n ", soltransshipmentII)
                 
        iterables_5d = [
                        range(len(self.Scenarioset)),
                        timebucketset,
                        range(len(self.Instance.BloodGPSet)),
                        range(len(self.Instance.PlateletAgeSet)),
                        range(len(self.Instance.ACFPPointSet))
                        ]
        multiindex_5d = pd.MultiIndex.from_product(iterables_5d, names=['Scenario', 'Time', 'BloodGP', 'PlateletAge', 'ACFLoc'])
        transshipmentII_df = pd.DataFrame(soltransshipmentII, index=self.Instance.ACFPPointSet, columns=multiindex_5d)
        transshipmentII_df.index.name = "fromACFLoc"
        #if Constants.Debug: print("transshipmentII_df:\n ", transshipmentII_df)
        
        ######################################## Transshipment HH Data Farame
        soltransshipmentHH = []
        for h in self.Instance.HospitalSet:
            transshipmentHH_Values = []
            for w in scenarioset:
                for t in timebucketset:
                    for c in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for hprime in self.Instance.HospitalSet:
                                transshipmentHH = self.TransshipmentHH_bDoublePrime_wtcrhh[w][t][c][r][h][hprime]
                                transshipmentHH_Values.append(transshipmentHH)
            soltransshipmentHH.append(transshipmentHH_Values)
        #if Constants.Debug: print("soltransshipmentHH:\n ", soltransshipmentHH)
                
        iterables_5d = [range(len(self.Scenarioset)),
                        timebucketset,
                        range(len(self.Instance.BloodGPSet)),
                        range(len(self.Instance.PlateletAgeSet)),
                        range(len(self.Instance.HospitalSet))]
        
        multiindex_5d = pd.MultiIndex.from_product(iterables_5d, names=['Scenario', 'Time', 'BloodGP', 'PlateletAge', 'HospitalLoc'])
        transshipmentHH_df = pd.DataFrame(soltransshipmentHH, index=self.Instance.HospitalSet, columns=multiindex_5d)
        transshipmentHH_df.index.name = "fromHospitalLoc"
        #if Constants.Debug: print("transshipmentHH_df:\n ", transshipmentHH_df)

        ######################################################## Patient Transfer Data Frame
        solpatientTransfer = []
        for l in self.Instance.DemandSet:
            patientTransfer_Values = []
            for w in scenarioset:
                for t in timebucketset:
                    for j in self.Instance.InjuryLevelSet:
                        for c in self.Instance.BloodGPSet:
                            for u in self.Instance.FacilitySet:
                                for m in self.Instance.RescueVehicleSet:
                                    patientTransfer = self.PatientTransfer_q_wtjclum[w][t][j][c][l][u][m]
                                    patientTransfer_Values.append(patientTransfer)
            solpatientTransfer.append(patientTransfer_Values)
        #if Constants.Debug: print("solpatientTransfer:\n ", solpatientTransfer)

        iterables_6d = [range(len(self.Scenarioset)),
                        timebucketset,
                        range(len(self.Instance.InjuryLevelSet)),
                        range(len(self.Instance.BloodGPSet)),
                        range(len(self.Instance.FacilitySet)),
                        range(len(self.Instance.RescueVehicleSet))]
        
        multiindex_6d = pd.MultiIndex.from_product(iterables_6d, names=['Scenario', 'Time', 'InjuryLevel', 'BloodGP', 'Facility', 'RescueVehicle'])
        patientTransfer_df = pd.DataFrame(solpatientTransfer, index=self.Instance.DemandSet, columns=multiindex_6d)
        patientTransfer_df.index.name = "DemandLoc"
        #if Constants.Debug: print("patientTransfer_df:\n ", patientTransfer_df)
        
        ######################################################## Unsatisfied Patient Data Frame
        solunsatisfiedPatient = []
        for l in self.Instance.DemandSet:
            unsatisfiedPatient_Values = []
            for w in scenarioset:
                for t in timebucketset:
                    for j in self.Instance.InjuryLevelSet:
                        for c in self.Instance.BloodGPSet:                    
                            unsatisfiedPatient = self.UnsatisfiedPatient_mu_wtjcl[w][t][j][c][l]
                            unsatisfiedPatient_Values.append(unsatisfiedPatient)
            solunsatisfiedPatient.append(unsatisfiedPatient_Values)
        #if Constants.Debug: print("solunsatisfiedPatient:\n ", solunsatisfiedPatient)
                
        iterables_4d = [range(len(self.Scenarioset)),  
                        timebucketset,                 
                        range(len(self.Instance.InjuryLevelSet)),  
                        range(len(self.Instance.BloodGPSet))]
        
        multiindex_4d = pd.MultiIndex.from_product(iterables_4d, names=['Scenario', 'Time', 'InjuryLevel', 'BloodGP'])
        unsatisfiedPatient_df = pd.DataFrame(solunsatisfiedPatient, index=self.Instance.DemandSet, columns=multiindex_4d)
        unsatisfiedPatient_df.index.name = "DemandLoc"
        #if Constants.Debug: print("unsatisfiedPatient_df:\n ", unsatisfiedPatient_df)
        
        ######################################################## Platelet Inventory Level Data Frame
        solplateletInventory = []
        for u in self.Instance.FacilitySet:
            plateletInventory_Values = []
            for w in scenarioset:
                for t in timebucketset:
                    for c in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:                    
                            plateletInventory = self.PlateletInventory_eta_wtcru[w][t][c][r][u]
                            plateletInventory_Values.append(plateletInventory)
            solplateletInventory.append(plateletInventory_Values)
        #if Constants.Debug: print("solplateletInventory:\n ", solplateletInventory)
                
        iterables_4d = [range(len(self.Scenarioset)),  
                        timebucketset,                 
                        range(len(self.Instance.BloodGPSet)), 
                        range(len(self.Instance.PlateletAgeSet))]
        
        multiindex_4d = pd.MultiIndex.from_product(iterables_4d, names=['Scenario', 'Time', 'BloodGP', 'PlateletAge'])
        plateletInventory_df = pd.DataFrame(solplateletInventory, index=self.Instance.FacilitySet, columns=multiindex_4d)
        plateletInventory_df.index.name = "FacilityLoc"
        #if Constants.Debug: print("plateletInventory_df:\n ", plateletInventory_df)
                
        ######################################################## Outdated Platelet Data Frame
        soloutdatedPlatelet = []
        for u in self.Instance.FacilitySet:
            outdatedPlatelet_Values = []
            for w in scenarioset:
                for t in timebucketset:
                    outdatedPlatelet = self.OutdatedPlatelet_sigmavar_wtu[w][t][u]
                    outdatedPlatelet_Values.append(outdatedPlatelet)
            soloutdatedPlatelet.append(outdatedPlatelet_Values)
        #if Constants.Debug: print("soloutdatedPlatelet:\n ", soloutdatedPlatelet)
                
        iterables_2d = [range(len(self.Scenarioset)),
                        timebucketset]
        multiindex_2d = pd.MultiIndex.from_product(iterables_2d, names=['Scenario', 'Time'])
        outdatedPlatelet_df = pd.DataFrame(soloutdatedPlatelet, index=self.Instance.FacilitySet, columns=multiindex_2d)
        outdatedPlatelet_df.index.name = "FacilityLoc"
        #if Constants.Debug: print("outdatedPlatelet_df:\n ", outdatedPlatelet_df)
        
        ######################################################## Served Patients Data Frame
        solservedPatient = []
        for u in self.Instance.FacilitySet:
            servedPatient_Values = []
            for w in scenarioset:
                for t in timebucketset:
                    for j in self.Instance.InjuryLevelSet:
                        for cprime in self.Instance.BloodGPSet:
                            for c in self.Instance.BloodGPSet:
                                for r in self.Instance.PlateletAgeSet:                    
                                    servedPatient = self.ServedPatient_upsilon_wtjcPcru[w][t][j][cprime][c][r][u]
                                    servedPatient_Values.append(servedPatient)
            solservedPatient.append(servedPatient_Values)
        #if Constants.Debug: print("solservedPatient:\n ", solservedPatient)

        iterables_6d = [range(len(self.Scenarioset)),
                        timebucketset,
                        range(len(self.Instance.InjuryLevelSet)),
                        range(len(self.Instance.BloodGPSet)),
                        range(len(self.Instance.BloodGPSet)),
                        range(len(self.Instance.PlateletAgeSet))]
                    
        multiindex_6d = pd.MultiIndex.from_product(iterables_6d, names=['Scenario', 'Time', 'InjuryLevel', 'from_BloodGP', 'for_BloodGP', 'PlateletAge'])
        servedPatient_df = pd.DataFrame(solservedPatient, index=self.Instance.FacilitySet, columns=multiindex_6d)
        servedPatient_df.index.name = "FacilityLoc"
        #if Constants.Debug: print("servedPatient_df:\n ", servedPatient_df)
        
        ######################################################## Patient Postponement Data Frame
        solpatientPostponement = []
        for u in self.Instance.FacilitySet:
            patientPostponement_Values = []
            for w in scenarioset:
                for t in timebucketset:
                    for j in self.Instance.InjuryLevelSet:
                        for c in self.Instance.BloodGPSet:                    
                            patientPostponement = self.PatientPostponement_zeta_wtjcu[w][t][j][c][u]
                            patientPostponement_Values.append(patientPostponement)
            solpatientPostponement.append(patientPostponement_Values)
        #if Constants.Debug: print("solpatientPostponement:\n ", solpatientPostponement)

        iterables_4d = [range(len(self.Scenarioset)),  
                        timebucketset,                
                        range(len(self.Instance.InjuryLevelSet)),  
                        range(len(self.Instance.BloodGPSet))]

        multiindex_4d = pd.MultiIndex.from_product(iterables_4d, names=['Scenario', 'Time', 'InjuryLevel', 'BloodGP'])
        patientPostponement_df = pd.DataFrame(solpatientPostponement, index=self.Instance.FacilitySet, columns=multiindex_4d)
        patientPostponement_df.index.name = "FacilityLoc"
        #if Constants.Debug: print("patientPostponement_df:\n ", patientPostponement_df)
        
        ######################################################## Apheresis Extraction Data Frame
        solplateletApheresisExtraction = []
        for u in self.Instance.FacilitySet:
            plateletApheresisExtraction_Values = []
            for w in scenarioset:
                for t in timebucketset:
                    for c in self.Instance.BloodGPSet:
                        plateletApheresisExtraction = self.PlateletApheresisExtraction_lambda_wtcu[w][t][c][u]
                        plateletApheresisExtraction_Values.append(plateletApheresisExtraction)
            solplateletApheresisExtraction.append(plateletApheresisExtraction_Values)
        #if Constants.Debug: print("solplateletApheresisExtraction:\n ", solplateletApheresisExtraction)

        iterables_3d = [range(len(self.Scenarioset)),  
                        timebucketset,                 
                        range(len(self.Instance.BloodGPSet))]
                    
        multiindex_3d = pd.MultiIndex.from_product(iterables_3d, names=['Scenario', 'Time', 'BloodGP'])
        plateletApheresisExtraction_df = pd.DataFrame(solplateletApheresisExtraction, index=self.Instance.FacilitySet, columns=multiindex_3d)
        plateletApheresisExtraction_df.index.name = "FacilityLoc"
        #if Constants.Debug: print("plateletApheresisExtraction_df:\n ", plateletApheresisExtraction_df)
        
        ######################################################## Whole Blood Extraction Data Frame
        solplateletWholeExtraction = []
        for h in self.Instance.HospitalSet:
            plateletWholeExtraction_Values = []
            for w in scenarioset:
                for t in timebucketset:
                    for c in self.Instance.BloodGPSet:                    
                        plateletWholeExtraction = self.PlateletWholeExtraction_Rhovar_wtch[w][t][c][h]
                        plateletWholeExtraction_Values.append(plateletWholeExtraction)
            solplateletWholeExtraction.append(plateletWholeExtraction_Values)
        #if Constants.Debug: print("solplateletWholeExtraction:\n ", solplateletWholeExtraction)

        iterables_3d = [range(len(self.Scenarioset)),  
                        timebucketset,                 
                        range(len(self.Instance.BloodGPSet))]
                    
        multiindex_3d = pd.MultiIndex.from_product(iterables_3d, names=['Scenario', 'Time', 'BloodGP'])
        plateletWholeExtraction_df = pd.DataFrame(solplateletWholeExtraction, index=self.Instance.HospitalSet, columns=multiindex_3d)
        plateletWholeExtraction_df.index.name = "HospitalLoc"
        #if Constants.Debug: print("plateletWholeExtraction_df:\n ", plateletWholeExtraction_df)

        ######################################################## Fixed yValues
        fixedyvalues = []
        for i in self.Instance.ACFPPointSet:
            fixedy_Values = []
            for t in timebucketset:
                fixedy = self.FixedApheresisAssignments[t][i]
                fixedy_Values.append(fixedy)
            fixedyvalues.append(fixedy_Values)
        #if Constants.Debug: print("fixedyvalues:\n ", fixedyvalues)

        iterables_1d = [timebucketset]
        
        multiindex_1d = pd.MultiIndex.from_product(iterables_1d, names=['Time'])
        fixed_y_values_df = pd.DataFrame(fixedyvalues, index=self.Instance.ACFPPointSet, columns=multiindex_1d)
        fixed_y_values_df.index.name = "ACFLoc"
        #if Constants.Debug: print("fixed_y_values_df:\n ", fixed_y_values_df)

        return acfestablishment_df, vehicleassignment_df, apheresisAssignments_df, transshipmentHI_df, transshipmentII_df, transshipmentHH_df, patientTransfer_df, unsatisfiedPatient_df, plateletInventory_df, outdatedPlatelet_df, servedPatient_df, patientPostponement_df, plateletApheresisExtraction_df, plateletWholeExtraction_df, fixed_y_values_df
    
    #This function creates a solution from the set of dataframe given in paramter  
    def ListFromDataFrame(self, acfestablishment_df, vehicleassignment_df, apheresisAssignments_df, transshipmentHI_df, transshipmentII_df, transshipmentHH_df, patientTransfer_df, unsatisfiedPatient_df, plateletInventory_df, outdatedPlatelet_df, servedPatient_df, patientPostponement_df, plateletApheresisExtraction_df, plateletWholeExtraction_df, fixed_y_values_df):
        if Constants.Debug: print("\n We are in 'Solution' Class -- ListFromDataFrame")

        scenarioset = range(len(self.Scenarioset))

        timebucketset = self.GetConsideredTimeBucket()

        ###################################### ACF Establishment
        self.ACFEstablishment_x_wi = [[acfestablishment_df.loc[i, (w)] 
                                        for i in self.Instance.ACFPPointSet] 
                                        for w in scenarioset]        
        #if Constants.Debug: print("self.ACFEstablishment_x_wi: ", self.ACFEstablishment_x_wi)
        
        ######################################  Rescue Vehicle Assignment        
        self.VehicleAssignment_thetavar_wmi = [[[vehicleassignment_df.loc[i, (m, w)] 
                                            for i in self.Instance.ACFPPointSet]
                                            for m in self.Instance.RescueVehicleSet] 
                                            for w in scenarioset]
        
        #if Constants.Debug: print("self.VehicleAssignment_thetavar_wmi: ", self.VehicleAssignment_thetavar_wmi)
        
        ###################################### Apheresis Assignment
        self.ApheresisAssignment_y_wti = [[[apheresisAssignments_df.loc[i, (w, t)] 
                                            for i in self.Instance.ACFPPointSet] 
                                            for t in timebucketset] 
                                            for w in range(len(self.Scenarioset))]
        #if Constants.Debug: print("self.ApheresisAssignment_y_wti: ", self.ApheresisAssignment_y_wti)
        
        ###################################### Transshipment HI
        self.TransshipmentHI_b_wtcrhi = [[[[[[transshipmentHI_df.loc[h, (w, t, c, r, i)] 
                                            for i in self.Instance.ACFPPointSet] 
                                            for h in self.Instance.HospitalSet] 
                                            for r in self.Instance.PlateletAgeSet] 
                                            for c in self.Instance.BloodGPSet] 
                                            for t in timebucketset] 
                                            for w in range(len(self.Scenarioset))]
        #if Constants.Debug: print("self.TransshipmentHI_b_wtcrhi: ", self.TransshipmentHI_b_wtcrhi)
        
        ###################################### Transshipment II
        self.TransshipmentII_bPrime_wtcrii = [[[[[[transshipmentII_df.loc[i, (w, t, c, r, iprime)] 
                                                for iprime in self.Instance.ACFPPointSet] 
                                                for i in self.Instance.ACFPPointSet] 
                                                for r in self.Instance.PlateletAgeSet] 
                                                for c in self.Instance.BloodGPSet] 
                                                for t in timebucketset] 
                                                for w in range(len(self.Scenarioset))]
        #if Constants.Debug: print("self.TransshipmentII_bPrime_wtcrii: ", self.TransshipmentII_bPrime_wtcrii)
        
        ###################################### Transshipment HH
        self.TransshipmentHH_bDoublePrime_wtcrhh = [[[[[[transshipmentHH_df.loc[h, (w, t, c, r, hprime)] 
                                                        for hprime in self.Instance.HospitalSet] 
                                                        for h in self.Instance.HospitalSet] 
                                                        for r in self.Instance.PlateletAgeSet] 
                                                        for c in self.Instance.BloodGPSet] 
                                                        for t in timebucketset] 
                                                        for w in range(len(self.Scenarioset))]
        #if Constants.Debug: print("self.TransshipmentHH_bDoublePrime_wtcrhh: ", self.TransshipmentHH_bDoublePrime_wtcrhh)

        ###################################### Patient Transfer
        self.PatientTransfer_q_wtjclum = [[[[[[[patientTransfer_df.loc[l, (w, t, j, c, u, m)] 
                                            for m in self.Instance.RescueVehicleSet] 
                                            for u in self.Instance.FacilitySet] 
                                            for l in self.Instance.DemandSet] 
                                            for c in self.Instance.BloodGPSet] 
                                            for j in self.Instance.InjuryLevelSet] 
                                            for t in timebucketset] 
                                            for w in range(len(self.Scenarioset))]
        #if Constants.Debug: print("self.PatientTransfer_q_wtjclum: ", self.PatientTransfer_q_wtjclum)
        
        ###################################### Unsatisfied Patient
        self.UnsatisfiedPatient_mu_wtjcl = [[[[[unsatisfiedPatient_df.loc[l, (w, t, j, c)] 
                                            for l in self.Instance.DemandSet] 
                                            for c in self.Instance.BloodGPSet] 
                                            for j in self.Instance.InjuryLevelSet] 
                                            for t in timebucketset] 
                                            for w in range(len(self.Scenarioset))]
        #if Constants.Debug: print("self.UnsatisfiedPatient_mu_wtjcl: ", self.UnsatisfiedPatient_mu_wtjcl)
        
        ###################################### Platelet Inventory
        self.PlateletInventory_eta_wtcru = [[[[[plateletInventory_df.loc[u, (w, t, c, r)] 
                                              for u in self.Instance.FacilitySet] 
                                              for r in self.Instance.PlateletAgeSet] 
                                              for c in self.Instance.BloodGPSet] 
                                              for t in timebucketset] 
                                              for w in range(len(self.Scenarioset))]
        #if Constants.Debug: print("self.PlateletInventory_eta_wtcru: ", self.PlateletInventory_eta_wtcru)

        ###################################### Outdated Platelet
        self.OutdatedPlatelet_sigmavar_wtu = [[[outdatedPlatelet_df.loc[u, (w, t)] 
                                                for u in self.Instance.FacilitySet] 
                                                for t in timebucketset] 
                                                for w in range(len(self.Scenarioset))]
        #if Constants.Debug: print("self.OutdatedPlatelet_sigmavar_wtu: ", self.OutdatedPlatelet_sigmavar_wtu)
        
        ###################################### Served Patient
        self.ServedPatient_upsilon_wtjcPcru = [[[[[[[servedPatient_df.loc[u, (w, t, j, cprime, c, r)] 
                                                        for u in self.Instance.FacilitySet] 
                                                        for r in self.Instance.PlateletAgeSet] 
                                                        for c in self.Instance.BloodGPSet] 
                                                        for cprime in self.Instance.BloodGPSet] 
                                                        for j in self.Instance.InjuryLevelSet] 
                                                        for t in timebucketset] 
                                                        for w in range(len(self.Scenarioset))]
        #if Constants.Debug: print("self.ServedPatient_upsilon_wtjcPcru: ", self.ServedPatient_upsilon_wtjcPcru)

        ###################################### Patient Postponement
        self.PatientPostponement_zeta_wtjcu = [[[[[patientPostponement_df.loc[u, (w, t, j, c)] 
                                                    for u in self.Instance.FacilitySet] 
                                                    for c in self.Instance.BloodGPSet] 
                                                    for j in self.Instance.InjuryLevelSet] 
                                                    for t in timebucketset] 
                                                    for w in range(len(self.Scenarioset))]
        #if Constants.Debug: print("self.PatientPostponement_zeta_wtjcu: ", self.PatientPostponement_zeta_wtjcu)
        
        ###################################### Platelet Apheresis Extraction
        self.PlateletApheresisExtraction_lambda_wtcu = [[[[plateletApheresisExtraction_df.loc[u, (w, t, c)] 
                                                          for u in self.Instance.FacilitySet] 
                                                          for c in self.Instance.BloodGPSet] 
                                                          for t in timebucketset] 
                                                          for w in range(len(self.Scenarioset))]
        #if Constants.Debug: print("self.PlateletApheresisExtraction_lambda_wtcu: ", self.PlateletApheresisExtraction_lambda_wtcu)
        
        ###################################### Platelet Whole Extraction
        self.PlateletWholeExtraction_Rhovar_wtch = [[[[plateletWholeExtraction_df.loc[h, (w, t, c)] 
                                                      for h in self.Instance.HospitalSet] 
                                                      for c in self.Instance.BloodGPSet] 
                                                      for t in timebucketset] 
                                                      for w in range(len(self.Scenarioset))]
        #if Constants.Debug: print("self.PlateletWholeExtraction_Rhovar_wtch: ", self.PlateletWholeExtraction_Rhovar_wtch)

        ######################################
        self.FixedApheresisAssignments = [[fixed_y_values_df.loc[i, (t)] 
                                            for i in self.Instance.ACFPPointSet]  
                                            for t in timebucketset]
        #if Constants.Debug: print("FixedApheresisAssignments: ", self.FixedApheresisAssignments)

    #This function compute some statistic on the current solution
    def ComputeStatistics(self):
        if Constants.Debug: print("\n We are in 'Solution' Class -- ComputeStatistics")

        #if Constants.Debug: print("\ACFEstablishment_x_wi: ", self.ACFEstablishment_x_wi)
        self.InSampleAverageACFEstablishment = [sum(self.ACFEstablishment_x_wi[w][i]  for w in self.SenarioNrset) /len(self.SenarioNrset)
                                                for i in self.Instance.ACFPPointSet]
        #if Constants.Debug: print("InSampleAverageACFEstablishment: ", self.InSampleAverageACFEstablishment)
        
        #if Constants.Debug: print("\VehicleAssignment_thetavar_wmi: ", self.VehicleAssignment_thetavar_wmi)
        self.InSampleAverageVehicleAssignment = [[sum(self.VehicleAssignment_thetavar_wmi[w][m][i]  
                                                    for w in self.SenarioNrset) /len(self.SenarioNrset)
                                                    for i in self.Instance.ACFPPointSet]
                                                    for m in self.Instance.RescueVehicleSet]
        #if Constants.Debug: print("InSampleAverageVehicleAssignment: ", self.InSampleAverageVehicleAssignment)
        
        #if Constants.Debug: print("\n ApheresisAssignment_y_wti: ", self.ApheresisAssignment_y_wti)
        self.InSampleAverageApheresisAssignment = [sum(self.ApheresisAssignment_y_wti[w][t][i] for w in self.SenarioNrset for t in self.Instance.TimeBucketSet) / (len(self.SenarioNrset) * len(self.Instance.TimeBucketSet))
                                                    for i in self.Instance.ACFPPointSet]
        #if Constants.Debug: print("InSampleAverageApheresisAssignment: ", self.InSampleAverageApheresisAssignment)
        
        #if Constants.Debug: print("\n TransshipmentHI_b_wtcrhi: ", self.TransshipmentHI_b_wtcrhi)
        self.InSampleAverageTransshipmentHI = [[[[sum(self.TransshipmentHI_b_wtcrhi[w][t][c][r][h][i] for w in self.SenarioNrset for t in self.Instance.TimeBucketSet) / (len(self.SenarioNrset) * len(self.Instance.TimeBucketSet))
                                                    for i in self.Instance.ACFPPointSet]
                                                    for h in self.Instance.HospitalSet]
                                                    for r in self.Instance.PlateletAgeSet]
                                                    for c in self.Instance.BloodGPSet]
        #if Constants.Debug: print("InSampleAverageTransshipmentHI: ", self.InSampleAverageTransshipmentHI)
        
        #if Constants.Debug: print("\n TransshipmentII_bPrime_wtcrii: ", self.TransshipmentII_bPrime_wtcrii)
        self.InSampleAverageTransshipmentII = [[[[sum(self.TransshipmentII_bPrime_wtcrii[w][t][c][r][i][iprime] for w in self.SenarioNrset for t in self.Instance.TimeBucketSet) / (len(self.SenarioNrset) * len(self.Instance.TimeBucketSet))
                                                    for iprime in self.Instance.ACFPPointSet]
                                                    for i in self.Instance.ACFPPointSet]
                                                    for r in self.Instance.PlateletAgeSet]
                                                    for c in self.Instance.BloodGPSet]
        #if Constants.Debug: print("InSampleAverageTransshipmentII: ", self.InSampleAverageTransshipmentII)
        
        #if Constants.Debug: print("\n TransshipmentHH_bDoublePrime_wtcrhh: ", self.TransshipmentHH_bDoublePrime_wtcrhh)
        self.InSampleAverageTransshipmentHH = [[[[sum(self.TransshipmentHH_bDoublePrime_wtcrhh[w][t][c][r][h][hprime] for w in self.SenarioNrset for t in self.Instance.TimeBucketSet) / (len(self.SenarioNrset) * len(self.Instance.TimeBucketSet))
                                                    for hprime in self.Instance.HospitalSet]
                                                    for h in self.Instance.HospitalSet]
                                                    for r in self.Instance.PlateletAgeSet]
                                                    for c in self.Instance.BloodGPSet]
        #if Constants.Debug: print("InSampleAverageTransshipmentHH: ", self.InSampleAverageTransshipmentHH)

        #if Constants.Debug: print("\n PatientTransfer_q_wtjclum: ", self.PatientTransfer_q_wtjclum)
        self.InSampleAveragePatientTransfer = [[[[[[sum(self.PatientTransfer_q_wtjclum[w][t][j][c][l][u][m] for w in self.SenarioNrset) / len(self.SenarioNrset )
                                                    for m in self.Instance.RescueVehicleSet]
                                                    for u in self.Instance.FacilitySet]
                                                    for l in self.Instance.DemandSet]
                                                    for c in self.Instance.BloodGPSet]
                                                    for j in self.Instance.InjuryLevelSet]
                                                    for t in self.Instance.TimeBucketSet]
        #if Constants.Debug: print("\InSampleAveragePatientTransfer: ", self.InSampleAveragePatientTransfer)
        
        #if Constants.Debug: print("\n UnsatisfiedPatient_mu_wtjcl: ", self.UnsatisfiedPatient_mu_wtjcl)
        self.InSampleAverageUnsatisfiedPatients = [[[[sum(self.UnsatisfiedPatient_mu_wtjcl[w][t][j][c][l] for w in self.SenarioNrset) / len(self.SenarioNrset )
                                                        for l in self.Instance.DemandSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for j in self.Instance.InjuryLevelSet]
                                                        for t in self.Instance.TimeBucketSet]
        #if Constants.Debug: print("InSampleAverageUnsatisfiedPatients: ", self.InSampleAverageUnsatisfiedPatients)
        
        #if Constants.Debug: print("\n PlateletInventory_eta_wtcru: ", self.PlateletInventory_eta_wtcru)
        self.InSampleAveragePlateletInventory = [[[[sum(self.PlateletInventory_eta_wtcru[w][t][c][r][u] for w in self.SenarioNrset) / len(self.SenarioNrset )
                                                        for u in self.Instance.FacilitySet]
                                                        for r in self.Instance.PlateletAgeSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for t in self.Instance.TimeBucketSet]
        #if Constants.Debug: print("InSampleAveragePlateletInventory: ", self.InSampleAveragePlateletInventory)
        
        #if Constants.Debug: print("\n OutdatedPlatelet_sigmavar_wtu: ", self.OutdatedPlatelet_sigmavar_wtu)
        self.InSampleAverageOutdatedPlatelet = [[sum(self.OutdatedPlatelet_sigmavar_wtu[w][t][u] for w in self.SenarioNrset) / len(self.SenarioNrset )
                                                    for u in self.Instance.FacilitySet]
                                                    for t in self.Instance.TimeBucketSet]
        #if Constants.Debug: print("InSampleAverageOutdatedPlatelet: ", self.InSampleAverageOutdatedPlatelet)
        
        #if Constants.Debug: print("\n ServedPatient_upsilon_wtjcPcru: ", self.ServedPatient_upsilon_wtjcPcru)
        self.InSampleAverageServedPatient = [[[[[[sum(self.ServedPatient_upsilon_wtjcPcru[w][t][j][cprime][c][r][u] for w in self.SenarioNrset) / len(self.SenarioNrset )
                                                    for u in self.Instance.FacilitySet]
                                                    for r in self.Instance.PlateletAgeSet]
                                                    for c in self.Instance.BloodGPSet]
                                                    for cprime in self.Instance.BloodGPSet]
                                                    for j in self.Instance.InjuryLevelSet]
                                                    for t in self.Instance.TimeBucketSet]
        #if Constants.Debug: print("InSampleAverageServedPatient: ", self.InSampleAverageServedPatient)
        
        #if Constants.Debug: print("\n PatientPostponement_zeta_wtjcu: ", self.PatientPostponement_zeta_wtjcu)
        self.InSampleAveragePatientPostponement = [[[[sum(self.PatientPostponement_zeta_wtjcu[w][t][j][c][u] for w in self.SenarioNrset) / len(self.SenarioNrset )
                                                    for u in self.Instance.FacilitySet]
                                                    for c in self.Instance.BloodGPSet]
                                                    for j in self.Instance.InjuryLevelSet]
                                                    for t in self.Instance.TimeBucketSet]
        #if Constants.Debug: print("InSampleAveragePatientPostponement: ", self.InSampleAveragePatientPostponement)
        
        #if Constants.Debug: print("\n PlateletApheresisExtraction_lambda_wtcu: ", self.PlateletApheresisExtraction_lambda_wtcu)
        self.InSampleAveragePlateletApheresisExtraction = [[[sum(self.PlateletApheresisExtraction_lambda_wtcu[w][t][c][u] for w in self.SenarioNrset) / len(self.SenarioNrset )
                                                            for u in self.Instance.FacilitySet]
                                                            for c in self.Instance.BloodGPSet]
                                                            for t in self.Instance.TimeBucketSet]
        #if Constants.Debug: print("InSampleAveragePlateletApheresisExtraction: ", self.InSampleAveragePlateletApheresisExtraction)
        
        #if Constants.Debug: print("\n PlateletWholeExtraction_Rhovar_wtch: ", self.PlateletWholeExtraction_Rhovar_wtch)
        self.InSampleAveragePlateletWholeExtraction = [[[sum(self.PlateletWholeExtraction_Rhovar_wtch[w][t][c][h] for w in self.SenarioNrset) / len(self.SenarioNrset )
                                                            for h in self.Instance.HospitalSet]
                                                            for c in self.Instance.BloodGPSet]
                                                            for t in self.Instance.TimeBucketSet]
        #if Constants.Debug: print("InSampleAveragePlateletWholeExtraction: ", self.InSampleAveragePlateletWholeExtraction)


        #Calculates the average amount of time met on-time!
        self.InSampleAverageOnTimeTransfer = [[[[(sum(max([self.Scenarioset[w].Demands[t][j][c][l] - self.UnsatisfiedPatient_mu_wtjcl[w][t][j][c][l],0])  for w in self.SenarioNrset) / len(self.SenarioNrset))
                                                for l in self.Instance.DemandSet]
                                                for c in self.Instance.BloodGPSet]
                                                for j in self.Instance.InjuryLevelSet]
                                                for t in self.Instance.TimeBucketSet]
        if Constants.Debug: print("\n InSampleAverageOnTimeTransfer: ", self.InSampleAverageOnTimeTransfer)
        
        ###############################################
        self.InSampleAverageOnTimeSurgery = [[0 for u in self.Instance.FacilitySet]
                                                for t in self.Instance.TimeBucketSet]

        for t in self.Instance.TimeBucketSet:
            for u in self.Instance.FacilitySet:
                total_on_time_surgeries = 0
                for j in self.Instance.InjuryLevelSet:
                    for c in self.Instance.BloodGPSet:

                        total_on_time_surgeries += sum(
                            max(
                                sum(
                                    self.PatientTransfer_q_wtjclum[w][t][j][c][l][u][m]
                                    for m in self.Instance.RescueVehicleSet
                                    for l in self.Instance.DemandSet
                                ) - self.PatientPostponement_zeta_wtjcu[w][t][j][c][u],
                                0
                            )
                            for w in self.SenarioNrset
                        )
                self.InSampleAverageOnTimeSurgery[t][u] = total_on_time_surgeries / len(self.SenarioNrset)
        if Constants.Debug: print("\n\n InSampleAverageOnTimeSurgery: ", self.InSampleAverageOnTimeSurgery)

        
        ###############################################
        self.InSampleAverageSameBloodTypeInfusion = [[(sum(max(
                                                            # Sum where blood types match (c' == c)
                                                            sum(
                                                                self.ServedPatient_upsilon_wtjcPcru[w][t][j][c][c][r][u]
                                                                for j in self.Instance.InjuryLevelSet
                                                                for c in self.Instance.BloodGPSet  # Correctly positioned to define 'c' before its use
                                                                for r in self.Instance.PlateletAgeSet
                                                            ) -
                                                            # Sum where blood types do not match (c' != c)
                                                            sum(
                                                                self.ServedPatient_upsilon_wtjcPcru[w][t][j][cprime][c][r][u]
                                                                for j in self.Instance.InjuryLevelSet
                                                                for c in self.Instance.BloodGPSet  # Correctly positioned to define 'c' before its use
                                                                for cprime in self.Instance.BloodGPSet if cprime != c
                                                                for r in self.Instance.PlateletAgeSet
                                                            ), 0) for w in self.SenarioNrset) / len(self.SenarioNrset))
                                                        for u in self.Instance.FacilitySet]
                                                        for t in self.Instance.TimeBucketSet]

        # Print the results
        if Constants.Debug: print("\n InSampleAverageSameBloodTypeInfusion: ", self.InSampleAverageSameBloodTypeInfusion)

        self.InSampleAverageSameBloodTypeInfusion_tuc = [[[(sum(max(
                                                                # Sum over all dimensions where blood types match (c' == c)
                                                                sum(
                                                                    self.ServedPatient_upsilon_wtjcPcru[w][t][j][cprime][c][r][u]
                                                                    for j in self.Instance.InjuryLevelSet
                                                                    for cprime in self.Instance.BloodGPSet if cprime == c
                                                                    for r in self.Instance.PlateletAgeSet
                                                                ) -
                                                                # Sum over all dimensions where blood types do not match (c' != c)
                                                                sum(
                                                                    self.ServedPatient_upsilon_wtjcPcru[w][t][j][cprime][c][r][u]
                                                                    for j in self.Instance.InjuryLevelSet
                                                                    for cprime in self.Instance.BloodGPSet if cprime != c
                                                                    for r in self.Instance.PlateletAgeSet
                                                                ),0)for w in self.SenarioNrset) / len(self.SenarioNrset))
                                                    for c in self.Instance.BloodGPSet]
                                                    for u in self.Instance.FacilitySet] 
                                                    for t in self.Instance.TimeBucketSet]
        if Constants.Debug: print("\n InSampleAverageSameBloodTypeInfusion_tuc: ", self.InSampleAverageSameBloodTypeInfusion_tuc)

        ###############################################
        self.InSampleTotalDemandPerScenario = [sum(sum(sum(sum(w.Demands[t][j][c][l]
                                                    for l in self.Instance.DemandSet)
                                                    for c in self.Instance.BloodGPSet)
                                                    for j in self.Instance.InjuryLevelSet)
                                                    for t in self.Instance.TimeBucketSet)
                                                    for w in self.Scenarioset]
        if Constants.Debug: print("\n InSampleTotalDemandPerScenario: ", self.InSampleTotalDemandPerScenario)

        totaldemand = sum(self.InSampleTotalDemandPerScenario)
        if Constants.Debug: print("totaldemand: ", totaldemand)

        ###############################################
        self.InSampleTotalTransferPerScenario = [sum(sum(sum(sum(sum(sum(self.PatientTransfer_q_wtjclum[w][t][j][c][l][u][m] 
                                                    for m in self.Instance.RescueVehicleSet)
                                                    for u in self.Instance.FacilitySet)
                                                    for l in self.Instance.DemandSet)
                                                    for c in self.Instance.BloodGPSet)
                                                    for j in self.Instance.InjuryLevelSet)
                                                    for t in self.Instance.TimeBucketSet)
                                                    for w in self.SenarioNrset]
        if Constants.Debug: print("\n InSampleTotalTransferPerScenario: ", self.InSampleTotalTransferPerScenario)

        totaltransfer = sum(self.InSampleTotalTransferPerScenario)
        if Constants.Debug: print("totaltransfer: ", totaltransfer)

        ############################################################
        self.InSampleTotalInfusionPerScenario = [sum(sum(sum(sum(sum(sum(self.ServedPatient_upsilon_wtjcPcru[w][t][j][cprime][c][r][u] 
                                                    for u in self.Instance.FacilitySet)
                                                    for r in self.Instance.PlateletAgeSet)
                                                    for c in self.Instance.BloodGPSet)
                                                    for cprime in self.Instance.BloodGPSet)
                                                    for j in self.Instance.InjuryLevelSet)
                                                    for t in self.Instance.TimeBucketSet)
                                                    for w in self.SenarioNrset]
        if Constants.Debug: print("\n InSampleTotalInfusionPerScenario: ", self.InSampleTotalInfusionPerScenario)

        totalinfusion = sum(self.InSampleTotalInfusionPerScenario)
        if Constants.Debug: print("totalinfusion: ", totalinfusion)

        ###############################################
        self.InSampleTotalOnTimeTransferPerScenario = [sum(sum(sum(sum(max([self.Scenarioset[w].Demands[t][j][c][l] - self.UnsatisfiedPatient_mu_wtjcl[w][t][j][c][l],0])
                                                        for l in self.Instance.DemandSet)
                                                        for c in self.Instance.BloodGPSet)
                                                        for j in self.Instance.InjuryLevelSet)
                                                        for t in self.Instance.TimeBucketSet)
                                                        for w in self.SenarioNrset]
        if Constants.Debug: print("\n InSampleTotalOnTimeTransferPerScenario: ", self.InSampleTotalOnTimeTransferPerScenario)
        
        ###############################################
        self.InSampleTotalOnTimeSurgeryPerScenario = [sum(sum(sum(sum(max([sum(self.PatientTransfer_q_wtjclum[w][t][j][c][l][u][m] for l in self.Instance.DemandSet for m in self.Instance.RescueVehicleSet) - self.PatientPostponement_zeta_wtjcu[w][t][j][c][u],0])
                                                        for u in self.Instance.FacilitySet)
                                                        for c in self.Instance.BloodGPSet)
                                                        for j in self.Instance.InjuryLevelSet)
                                                        for t in self.Instance.TimeBucketSet)
                                                        for w in self.SenarioNrset]
        if Constants.Debug: print("\n InSampleTotalOnTimeSurgeryPerScenario: ", self.InSampleTotalOnTimeSurgeryPerScenario)
        
        ###############################################
        self.InSampleTotalSameBloodTypeInfusionPerScenario = [sum(sum(sum(sum(sum(self.ServedPatient_upsilon_wtjcPcru[w][t][j][cprime][c][r][u]
                                                                for u in self.Instance.FacilitySet)
                                                                for r in self.Instance.PlateletAgeSet)
                                                                for c in self.Instance.BloodGPSet
                                                                for cprime in self.Instance.BloodGPSet if cprime == c)
                                                                for j in self.Instance.InjuryLevelSet)
                                                                for t in self.Instance.TimeBucketSet)
                                                                for w in self.SenarioNrset]
        if Constants.Debug: print("\nInSampleTotalSameBloodTypeInfusionPerScenario: ", self.InSampleTotalSameBloodTypeInfusionPerScenario)

        ###############################################
        nrscenario = len(self.Scenarioset)
        self.InSampleAverageDemand = sum(self.InSampleTotalDemandPerScenario[w] for w in self.SenarioNrset) / nrscenario
        if Constants.Debug: print("\n InSampleAverageDemand: ", self.InSampleAverageDemand)
        
        ###############################################
        nrscenario = len(self.Scenarioset)
        self.InSampleAverageTransfer = sum(self.InSampleTotalTransferPerScenario[w] for w in self.SenarioNrset) / nrscenario
        if Constants.Debug: print("\n InSampleAverageTransfer: ", self.InSampleAverageTransfer)
        
        ###############################################
        nrscenario = len(self.Scenarioset)
        self.InSampleAverageInfusion = sum(self.InSampleTotalInfusionPerScenario[w] for w in self.SenarioNrset) / nrscenario
        if Constants.Debug: print("\n InSampleAverageInfusion: ", self.InSampleAverageInfusion)

        ###############################################
        self.InSamplePercentOnTimeTransfer = round(100 * (sum(self.InSampleTotalOnTimeTransferPerScenario[s] for s in self.SenarioNrset)) / totaldemand, 2)
        if Constants.Debug: print("\n InSamplePercentOnTimeTransfer: ", self.InSamplePercentOnTimeTransfer)
        
        ###############################################
        self.InSamplePercentOnTimeSurgery = round(100 * (sum(self.InSampleTotalOnTimeSurgeryPerScenario[s] for s in self.SenarioNrset)) / totaltransfer, 2)
        if Constants.Debug: print("\n InSamplePercentOnTimeSurgery: ", self.InSamplePercentOnTimeSurgery)
        
        ###############################################
        self.InSamplePercentSameBloodTypeInfusion = round(100 * (sum(self.InSampleTotalSameBloodTypeInfusionPerScenario[s] for s in self.SenarioNrset)) / totalinfusion, 2)
        if Constants.Debug: print("\n InSamplePercentSameBloodTypeInfusion: ", self.InSamplePercentSameBloodTypeInfusion)
        
    #This function print the statistic in an Excel file
    def PrintStatistics(self, testidentifier, filepostscript, offsetseed, nrevaluation,  evaluationduration, insample, evaluationmethod):
        if Constants.Debug: print("\n We are in 'Solution' Class -- PrintStatistics")

        #To compute every statistic Constants.PrintOnlyFirstStageDecision should be False
        if (not Constants.PrintOnlyFirstStageDecision) or (not insample):
            
            if Constants.PrintDetailsExcelFiles:
                self.PrintDetailExcelStatistic( filepostscript, offsetseed, nrevaluation,  testidentifier, evaluationmethod )


            self.ComputeCost()            
        
        nracfs = self.GetNrACFEstablishment()
        nrvehiclesassigned = self.GetNrVehicleAssignment()

        kpistat = [ self.GRBCost,
                    self.GRBTime,
                    self.GRBGap,
                    self.GRBNrConstraints,
                    self.GRBNrVariables,
                    self.SDDPLB,
                    self.SDDPExpUB,
                    self.SDDPSafeUB,
                    self.SDDPNrIteration,
                    self.SDDPTimeBackward,
                    self.SDDPTimeForwardNoTest,
                    self.SDDPTimeForwardTest,
                    self.MLLocalSearchLB,
                    self.MLLocalSearchTimeBestSol,
                    self.LocalSearchIteration,
                    self.PHCost,
                    self.PHNrIteration,
                    self.TotalTime,
                    self.ACFEstablishmentCost,
                    self.Vehicle_AssignmentCost,
                    self.ApheresisAssignmentCost,
                    self.TransshipmentHICost,
                    self.TransshipmentIICost,
                    self.TransshipmentHHCost,
                    self.PatientTransferCost,
                    self.UnsatisfiedPatientsCost,
                    self.PlateletInventoryCost,
                    self.OutdatedPlateletCost,
                    self.ServedPatientCost,
                    self.PatientPostponementCost,
                    self.PlateletApheresisExtractionCost,
                    self.PlateletWholeExtractionCost,
                    self.InSamplePercentOnTimeTransfer,
                    self.InSamplePercentOnTimeSurgery,
                    self.InSamplePercentSameBloodTypeInfusion,
                    nracfs,
                    nrvehiclesassigned,
                    evaluationduration
                    ]

        # Assuming 'column_names' is a list of strings representing the column names
        column_names = ["GRB Cost", "GRB Time", "GRB Gap", "GRB Nr Constraints", "GRB Nr Variables", 
                        "SDDP LB", "SDDP Exp UB", "SDDP Nr Iteration", "SDDP Time Backward", 
                        "SDDP Time Forward No Test", "SDDP Time Forward Test", "ML Local Search LB", 
                        "ML Local Search Time Best Sol", "Local Search Iteration", "PH Cost", "PH Nr Iteration", 
                        "Total Time", "ACF Establishment Cost", "Vehicle Assignment Cost",
                        "Apheresis Assignment Cost", "Transshipment HI Cost", "Transshipment II Cost", "Transshipment HH Cost",
                        "Patient Transfer Cost", "Unsatisfied Patients Cost", "PLT Inventory Cost", "Outdated PLT Cost",
                        "Served Patient Cost", "Patient Postponement Cost", "PLT Apheresis Ext. Cost", "PLT Whole Ext. Cost",
                        "% On-Time Transfer", "% On-Time Surgery", "% Same BloodTypeInfusion",
                        "Nr ACF Established", "Nr Veh. Assigned", "Evaluation Duration"]
        # Adding additional headers for data from testidentifier and other values
        additional_headers = ["Instance Name", "Model", "Method", "Scenario Sampling", "Number of Scenarios", "Scenario Seed", "EVPI", "Number of Scenarios Forward", "MIP Setting", "SDDP Setting", "HybridPHSetting", "MLLocalSearchSetting"]
        
        full_column_names = additional_headers + ["Out/In", "NrEvaluation"] + column_names

        data = testidentifier.GetAsStringList() + [filepostscript, len(self.Scenarioset)] + kpistat


        if Constants.PrintDetailsExcelFiles:
            d = datetime.now()
            date = d.strftime('%m_%d_%Y_%H_%M_%S')
            myfile = open(r'./Test/Statistic/TestResult_%s_%r.csv' % (testidentifier.GetAsString(), filepostscript), 'w')
            wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
            wr.writerow(full_column_names)
            wr.writerow(data)
            myfile.close()


        return kpistat

    #This function print detailed statistics about the obtained solution (avoid using it as it consume memory)
    def PrintDetailExcelStatistic(self, filepostscript, offsetseed, nrevaluation,  testidentifier, evaluationmethod):
        if Constants.Debug: print("\n We are in 'Solution' Class -- PrintDetailExcelStatistic")

        scenarioset = range(len(self.Scenarioset))

        d = datetime.now()
        date = d.strftime('%m_%d_%Y_%H_%M_%S')
        file_path = "./Solutions/" + testidentifier.GetAsString() + "_Statistics_" + filepostscript + ".xlsx"

        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            avgACFEstablishment_df = pd.DataFrame(self.InSampleAverageACFEstablishment)
            avgACFEstablishment_df.to_excel(writer, sheet_name="Avg.ACFEstablishment")
            
            avgVehicleAssignment_df = pd.DataFrame(self.InSampleAverageVehicleAssignment)
            avgVehicleAssignment_df.to_excel(writer, sheet_name="Avg.VehicleAssignment")

            avgApheresisAssignments_df = pd.DataFrame(self.InSampleAverageApheresisAssignment)
            avgApheresisAssignments_df.to_excel(writer, sheet_name="Avg.ApheresisAssignment")
            
            avgTransshipmentHI_df = pd.DataFrame(self.InSampleAverageTransshipmentHI)
            avgTransshipmentHI_df.to_excel(writer, sheet_name="Avg.Trans.HI")
            
            avgTransshipmentII_df = pd.DataFrame(self.InSampleAverageTransshipmentII)
            avgTransshipmentII_df.to_excel(writer, sheet_name="Avg.Trans.II")
            
            avgTransshipmentHH_df = pd.DataFrame(self.InSampleAverageTransshipmentHH)
            avgTransshipmentHH_df.to_excel(writer, sheet_name="Avg.Trans.HH")

            avgPatientTransfer_df = pd.DataFrame(self.InSampleAveragePatientTransfer)
            avgPatientTransfer_df.to_excel(writer, sheet_name="Avg.PatientTransfer")

            avgUnsatisfiedPatient_df = pd.DataFrame(self.InSampleAverageUnsatisfiedPatients)
            avgUnsatisfiedPatient_df.to_excel(writer, sheet_name="Avg.UnsatisfiedPatient")

            avgPlateletInventory_df = pd.DataFrame(self.InSampleAveragePlateletInventory)
            avgPlateletInventory_df.to_excel(writer, sheet_name="Avg.PLTInventory")

            avgOutdatedPlatelet_df = pd.DataFrame(self.InSampleAverageOutdatedPlatelet)
            avgOutdatedPlatelet_df.to_excel(writer, sheet_name="Avg.OutdatedPLT")

            avgServedPatient_df = pd.DataFrame(self.InSampleAverageServedPatient)
            avgServedPatient_df.to_excel(writer, sheet_name="Avg.ServedPatient")

            avgPatientPostponement_df = pd.DataFrame(self.InSampleAveragePatientPostponement)
            avgPatientPostponement_df.to_excel(writer, sheet_name="Avg.PatientPostponement")

            avgPlateletApheresisExtraction_df = pd.DataFrame(self.InSampleAveragePlateletApheresisExtraction)
            avgPlateletApheresisExtraction_df.to_excel(writer, sheet_name="Avg.ApheresisExt.")

            avgPlateletWholeExtraction_df = pd.DataFrame(self.InSampleAveragePlateletWholeExtraction)
            avgPlateletWholeExtraction_df.to_excel(writer, sheet_name="Avg.WholeExt.")

            perscenario_demand_df = pd.DataFrame([self.InSampleTotalDemandPerScenario],
                                                index=["Total Demand"],
                                                columns=scenarioset)
            perscenario_demand_df.to_excel(writer, sheet_name="Info Per Scenario", startrow=0)

            # DataFrame for Total Transfer per scenario
            perscenario_transfer_df = pd.DataFrame([self.InSampleTotalTransferPerScenario],
                                                index=["Total Transfer"],
                                                columns=scenarioset)
            # Calculate the next start row: length of current DF + 1 for a blank row, or more for multiple blank rows
            next_row = len(perscenario_demand_df.index) + 2  # plus 2 or more for spacing
            perscenario_transfer_df.to_excel(writer, sheet_name="Info Per Scenario", startrow=next_row)

            # DataFrame for Total Infusion per scenario
            perscenario_infusion_df = pd.DataFrame([self.InSampleTotalInfusionPerScenario],
                                                index=["Total Infusion"],
                                                columns=scenarioset)
            # Update the next row start index similarly
            next_row += len(perscenario_transfer_df.index) + 2  # adjust the spacing as needed
            perscenario_infusion_df.to_excel(writer, sheet_name="Info Per Scenario", startrow=next_row)


            general = testidentifier.GetAsStringList() + [self.InSampleAverageDemand, self.InSampleAverageTransfer, self.InSampleAverageInfusion, offsetseed, nrevaluation, testidentifier.ScenarioSeed, evaluationmethod]

            # Ensure the general data is in a 2D list format for DataFrame conversion
            general = [general]  # Wrapping general list in another list to make it 2D
            columnstab = ["Instance", "Model", "Method", "ScenarioGeneration", "NrScenario", "ScenarioSeed",
                        "EVPI", "NrForwardScenario", "mipsetting", "SDDPSetting", "HybridPHSetting", "MLLocalSearchSetting",
                        "Average demand", "Average Transfer", "Average Infusion", "offsetseed", "nrevaluation", "solutionseed", "evaluationmethod"]

            generaldf = pd.DataFrame(general, columns=columnstab)
            generaldf.to_excel(writer, sheet_name="General")
    
    def GetNrACFEstablishment(self):
        if Constants.Debug: print("\n We are in 'Solution' Class -- GetNrACFEstablishment")

        result = sum(self.ACFEstablishment_x_wi[w][i] 
                     for i in self.Instance.ACFPPointSet 
                     for w in range(len(self.Scenarioset)))
        result = result / len(self.Scenarioset)

        return result
    
    def GetNrVehicleAssignment(self):
        if Constants.Debug: print("\n We are in 'Solution' Class -- GetNrVehicleAssignment")

        result = sum(self.VehicleAssignment_thetavar_wmi[w][m][i] 
                     for i in self.Instance.ACFPPointSet 
                     for m in self.Instance.RescueVehicleSet 
                     for w in range(len(self.Scenarioset)))
        result = result / len(self.Scenarioset)

        return result
    
    #This function merge solution2 into self. Assume that solution2 has a single scenario
    def Merge( self, solution2 ):
        if Constants.Debug: print("\n We are in 'Solution' Class -- Merge")

        self.Scenarioset.append(solution2.Scenarioset[0])
        self.SenarioNrset = range(len(self.Scenarioset))

        self.ACFEstablishment_x_wi = self.ACFEstablishment_x_wi + solution2.ACFEstablishment_x_wi
        #if Constants.Debug: print("self.ACFEstablishment_x_wi:\n ", self.ACFEstablishment_x_wi)
        self.VehicleAssignment_thetavar_wmi = self.VehicleAssignment_thetavar_wmi + solution2.VehicleAssignment_thetavar_wmi
        #if Constants.Debug: print("self.VehicleAssignment_thetavar_wmi:\n ", self.VehicleAssignment_thetavar_wmi)

        self.ApheresisAssignment_y_wti = self.ApheresisAssignment_y_wti + solution2.ApheresisAssignment_y_wti
        #if Constants.Debug: print("self.ApheresisAssignment_y_wti:\n ", self.ApheresisAssignment_y_wti)
        self.TransshipmentHI_b_wtcrhi = self.TransshipmentHI_b_wtcrhi + solution2.TransshipmentHI_b_wtcrhi
        #if Constants.Debug: print("self.TransshipmentHI_b_wtcrhi:\n ", self.TransshipmentHI_b_wtcrhi)
        self.TransshipmentII_bPrime_wtcrii = self.TransshipmentII_bPrime_wtcrii + solution2.TransshipmentII_bPrime_wtcrii
        #if Constants.Debug: print("self.TransshipmentII_bPrime_wtcrii:\n ", self.TransshipmentII_bPrime_wtcrii)
        self.TransshipmentHH_bDoublePrime_wtcrhh = self.TransshipmentHH_bDoublePrime_wtcrhh + solution2.TransshipmentHH_bDoublePrime_wtcrhh
        #if Constants.Debug: print("self.TransshipmentHH_bDoublePrime_wtcrhh:\n ", self.TransshipmentHH_bDoublePrime_wtcrhh)

        self.PatientTransfer_q_wtjclum = self.PatientTransfer_q_wtjclum + solution2.PatientTransfer_q_wtjclum
        #if Constants.Debug: print("self.PatientTransfer_q_wtjclum:\n ", self.PatientTransfer_q_wtjclum)       
        self.UnsatisfiedPatient_mu_wtjcl = self.UnsatisfiedPatient_mu_wtjcl + solution2.UnsatisfiedPatient_mu_wtjcl
        #if Constants.Debug: print("self.UnsatisfiedPatient_mu_wtjcl:\n ", self.UnsatisfiedPatient_mu_wtjcl)             
        self.PlateletInventory_eta_wtcru = self.PlateletInventory_eta_wtcru + solution2.PlateletInventory_eta_wtcru
        #if Constants.Debug: print("self.PlateletInventory_eta_wtcru:\n ", self.PlateletInventory_eta_wtcru)     
        self.OutdatedPlatelet_sigmavar_wtu = self.OutdatedPlatelet_sigmavar_wtu + solution2.OutdatedPlatelet_sigmavar_wtu
        #if Constants.Debug: print("self.OutdatedPlatelet_sigmavar_wtu:\n ", self.OutdatedPlatelet_sigmavar_wtu)       
        self.ServedPatient_upsilon_wtjcPcru = self.ServedPatient_upsilon_wtjcPcru + solution2.ServedPatient_upsilon_wtjcPcru
        #if Constants.Debug: print("self.ServedPatient_upsilon_wtjcPcru:\n ", self.ServedPatient_upsilon_wtjcPcru)      
        self.PatientPostponement_zeta_wtjcu = self.PatientPostponement_zeta_wtjcu + solution2.PatientPostponement_zeta_wtjcu
        #if Constants.Debug: print("self.PatientPostponement_zeta_wtjcu:\n ", self.PatientPostponement_zeta_wtjcu)      
        self.PlateletApheresisExtraction_lambda_wtcu = self.PlateletApheresisExtraction_lambda_wtcu + solution2.PlateletApheresisExtraction_lambda_wtcu
        #if Constants.Debug: print("self.PlateletApheresisExtraction_lambda_wtcu:\n ", self.PlateletApheresisExtraction_lambda_wtcu)     
        self.PlateletWholeExtraction_Rhovar_wtch = self.PlateletWholeExtraction_Rhovar_wtch + solution2.PlateletWholeExtraction_Rhovar_wtch
        #if Constants.Debug: print("self.PlateletWholeExtraction_Rhovar_wtch:\n ", self.PlateletWholeExtraction_Rhovar_wtch)     

    def ComputeInventory(self):
        if Constants.Debug: print("\n We are in 'Solution' Class -- ComputeInventory")


        for w in self.SenarioNrset:
            for t in self.Instance.TimeBucketSet:
                prevdemand = [[self.Scenarioset[w].Demands[tau][d] for d in self.Instance.DemandSet] for tau in range(t+1)]
                prevvartrans = [[[self.VariableTransportation_x_wtsd[w][tau][s][d] for d in self.Instance.DemandSet] for s in self.Instance.SupplierSet] for tau in range(t+1)]

                currentinventory = []
                for d in self.Instance.DemandSet:
                    sum_vartrans = 0
                    sum_demand = 0
                    for t in range(max(t + 1, 0)):
                        for s in self.Instance.SupplierSet:
                            sum_vartrans += prevvartrans[t][s][d]

                    # Calculate the sum of demand for this product up to time t
                    for t in range(t+1):
                        sum_demand += prevdemand[t][d]

                    # Calculate the current inventory for this product
                    current_inventory_value = sum_vartrans - sum_demand
                    currentinventory.append(current_inventory_value)

                    # Print debugging information if needed
                    if Constants.Debug: print(f"DemandLoc {d}: VarTrans Sum = {sum_vartrans}, Demand Sum = {sum_demand}, Current Inventory = {current_inventory_value}")
                    
                # Print the final current inventory list
                if Constants.Debug: print("Current Inventory for all products:", currentinventory)


                for d in self.Instance.DemandSet:

                    if currentinventory[d] >= -0.0001:
                        self.Inventory_I_wtd[w][t][d] = currentinventory[d]
                        self.Shortage_u_wtd[w][t][d] = 0.0
                    else:
                        self.Shortage_u_wtd[w][t][d] = -currentinventory[d]
                        self.Inventory_I_wtd[w][t][d] = 0.0
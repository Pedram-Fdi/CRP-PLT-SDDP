import pandas as pd
import time
import numpy as np
import math
from Constants import Constants
from Solution import Solution
from Tool import Tool
from ScenarioTreeNode import ScenarioTreeNode
import itertools
import gurobipy as gp
from gurobipy import *
import os


class MIPSolver(object):
    # constructor
    def __init__(self,
                 instance,
                 model,
                 scenariotree,
                 evpi=False,
                 implicitnonanticipativity=True,
                 givenapheresisassignment=[],
                 giventransshipmentHI = [],
                 giventransshipmentII = [],
                 giventransshipmentHH = [],
                 givenacfestablishment = [],
                 givenvehicleassinment = [],
                 fixsolutionuntil=-1,
                 evaluatesolution=False,
                 Multi_Stageheuristic=False,
                 demandknownuntil=-1,
                 mipsetting="",
                 warmstart=False,
                 rollinghorizon=False,
                 expandfirstnode = False, #expandfirstnode is used to remove the non anticipativity constraint, if used, variable of the rootnode of the tree are created for each scenario
                 logfile="",
                 givenSGrave=[]):
        
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- Constructor")
        # Define some attributes and functions which help to set the index of the variable.

        # the attributs NrACFEstablishmentVariables, and ... gives the number of variable of each type
        self.NrACFEstablishmentVariables = 0
        self.NrVehicleAssignmentVariables = 0

        self.NrApheresisAssignmentVariables = 0
        self.NrTransshipmentHIVariables = 0
        self.NrTransshipmentIIVariables = 0
        self.NrTransshipmentHHVariables = 0

        self.NrPatientTransferVariables = 0
        self.NrUnsatisfiedPatientsVariables = 0
        self.NrPlateletInventoryVariables = 0
        self.NrOutdatedPlateletVariables = 0
        self.NrServedPatientVariables = 0
        self.NrPatientPostponementVariables = 0
        self.NrPlateletApheresisExtractionVariables = 0
        self.NrPlateletWholeExtractionVariables = 0

        # The variable StartFixedTransVariables and ... gives the index at which each variable type start
        self.StartACFEstablishmentVariables = 0
        self.StartVehicleAssignmentVariables = 0

        self.StartApheresisAssignmentVariables = 0
        self.StartTransshipmentHIVariables = 0
        self.StartTransshipmentIIVariables = 0
        self.StartTransshipmentHHVariables = 0

        self.StartPatientTransferVariables = 0
        self.StartUnsatisfiedPatientsVariables = 0
        self.StartPlateletInventoryVariables = 0
        self.StartOutdatedPlateletVariables = 0
        self.StartServedPatientVariables = 0
        self.StartPatientPostponementVariables = 0
        self.StartPlateletApheresisExtractionVariables = 0
        self.StartPlateletWholeExtractionVariables = 0

        self.Instance = instance

        #Takes value in Average/Two_Stage/Multi_Stage
        self.Model = model

        #If non anticipativity constraints are added, they can be implicit or explicit.
        self.UseImplicitNonAnticipativity = implicitnonanticipativity

        

        #self.UseNonAnticipativity
        self.EVPI = evpi
        self.MipSetting = mipsetting
        #The set of scenarios used to solve the instance
        self.DemandScenarioTree = scenariotree
        self.DemandScenarioTree.Owner = self
        self.NrScenario = len([n for n in self.DemandScenarioTree.Nodes if len(n.Branches) == 0])

        

        # DemandKnownUntil is used for the Two_Stage model, when the first period are considered known.
        self.DemandKnownUntil = demandknownuntil
        self.Multi_StageHeuristic = Multi_Stageheuristic
        self.ExpendFirstNode = expandfirstnode

        #self.Print_Attributes()

        self.ComputeIndices()

        if Constants.Debug: print("------------Moving from 'MIPSolver' Class (Constructor) to 'scenariotree' class (GetAllScenarios)---------------")
        self.Scenarios = scenariotree.GetAllScenarios(True, expandfirstnode)
        if Constants.Debug: print("------------Moving BACK from 'ScenarioTree' class (GetAllScenarios) to 'MIPSolver' Class (Constructor)---------------")

        self.GivenApheresisAssignment = givenapheresisassignment
        self.GivenTransshipmentHI = giventransshipmentHI
        self.GivenTransshipmentII = giventransshipmentII
        self.GivenTransshipmentHH = giventransshipmentHH

        self.GivenACFEstablishment = givenacfestablishment
        self.GivenVehicleAssignment = givenvehicleassinment

        self.FixSolutionUntil = fixsolutionuntil
        self.WamStart = warmstart

        self.ScenarioSet = range(self.NrScenario)


        self.EvaluateSolution = evaluatesolution
        self.logfilename= logfile
        #This list is filled after the resolution of the MIP
        self.SolveInfo = []

        #This list will contain the set of constraint number for each flow constraint
        
        self.LowMedPriorityPatientFlowConstraintNR = [[[[[None for _ in self.Instance.DemandSet] for _ in self.Instance.BloodGPSet] for _ in self.Instance.InjuryLevelSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.HighPriorityPatientFlowConstraintNR = [[[[[None for _ in self.Instance.DemandSet] for _ in self.Instance.BloodGPSet] for _ in self.Instance.InjuryLevelSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.LowMedPriorityPatientServiceConstraintNR = [[[[[None for _ in self.Instance.FacilitySet] for _ in self.Instance.BloodGPSet] for _ in self.Instance.InjuryLevelSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.HighPriorityPatientServiceConstraintNR = [[[[[None for _ in self.Instance.HospitalSet] for _ in self.Instance.BloodGPSet] for _ in self.Instance.InjuryLevelSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.ACFTreatmentCapacityConstraintNR = [[[None for _ in self.Instance.ACFPPointSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.HospitalTreatmentCapacityConstraintNR = [[[None for _ in self.Instance.HospitalSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.HospitalPlateletFlowConstraintNR = [[[[[None for _ in self.Instance.HospitalSet] for _ in self.Instance.PlateletAgeSet] for _ in self.Instance.BloodGPSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.ACFPlateletFlowConstraintNR = [[[[[None for _ in self.Instance.ACFPPointSet] for _ in self.Instance.PlateletAgeSet] for _ in self.Instance.BloodGPSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.PlateletWastageConstraintNR = [[[None for _ in self.Instance.FacilitySet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.HospitalRescueVehicleCapacityConstraintNR = [[[[None for _ in self.Instance.RescueVehicleSet] for _ in self.Instance.HospitalSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.ACFRescueVehicleCapacityConstraintNR = [[[[None for _ in self.Instance.RescueVehicleSet] for _ in self.Instance.ACFPPointSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.NrApheresisLimitConstraintNR = [[None for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.ApheresisACFConstraintNR = [[[None for _ in self.Instance.ACFPPointSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.ACFApheresisCapacityConstraintNR = [[[None for _ in self.Instance.ACFPPointSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.HospitalApheresisCapacityConstraintNR = [[[None for _ in self.Instance.HospitalSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.ApheresisCapacityDonorsConstraintNR = [[[[None for _ in self.Instance.FacilitySet] for _ in self.Instance.BloodGPSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.WholeCapacityDonorsConstraintNR = [[[[None for _ in self.Instance.HospitalSet] for _ in self.Instance.BloodGPSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.HospitalTransshipmentCapacityConstraintNR = [[[[[None for _ in self.Instance.HospitalSet] for _ in self.Instance.PlateletAgeSet] for _ in self.Instance.BloodGPSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        self.ACFTransshipmentCapacityConstraintNR = [[[[[None for _ in self.Instance.ACFPPointSet] for _ in self.Instance.PlateletAgeSet] for _ in self.Instance.BloodGPSet] for _ in self.Instance.TimeBucketSet] for _ in self.ScenarioSet]
        
        
        self.ACFEstablishmentVarConstraintNR = []
        self.VehicleAssignmentVarConstraintNR = []

        self.ApheresisAssignmentVarConstraintNR = []
        self.TransshipmentHIVarConstraintNR = []
        self.TransshipmentIIVarConstraintNR = []
        self.TransshipmentHHVarConstraintNR = []


        self.RollingHorizon = rollinghorizon

    def Print_Attributes(self):
        if Constants.Debug: 
            print("\n We are in 'MIPSolver' Class -- Print_Attributes")
            print(f"Instance: {self.Instance}")
            print(f"Model: {self.Model}")
            print("UseImplicitNonAnticipativity:", self.UseImplicitNonAnticipativity)
            print("EVPI:", self.EVPI)
            print("MipSetting:", self.MipSetting)        
            print("DemandScenarioTree:", self.DemandScenarioTree)
            print("NrScenario:", self.NrScenario)
            print("DemandKnownUntil:", self.DemandKnownUntil)    
            print("Multi_StageHeuristic:", self.Multi_StageHeuristic)
            print("ExpendFirstNode:", self.ExpendFirstNode)

   #This function print the scenario of the instance in an excel file
    def PrintScenarioToFile(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- PrintScenarioToFile")

        # Ensure the Instances directory exists
        os.makedirs("./Instances", exist_ok=True)
        
        filePath = "./Instances/" + self.Instance.InstanceName + "_Scenario.txt"

        # Open the file once here, with 'w' to overwrite existing content
        if Constants.Debug: print("------------Moving from 'MIPSolver' Class ('PrintScenarioToFile' Function) to 'Scenario' class ('PrintScenarioToText' Function))---------------")
        with open(filePath, 'w') as file:
            for s in self.Scenarios:
                # Pass the file object, not the path, and write directly to it
                s.PrintScenarioToText(file)
        if Constants.Debug: print("------------Moving BACK from 'Scenario' class ('PrintScenarioToText' Function) to 'MIPSolver' Class ('PrintScenarioToFile' Function))---------------")

    # Compute the start of index and the number of variables for the considered instance
    def ComputeIndices(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- ComputeIndices")
        if Constants.Debug: print("self.NrScenario: ", self.NrScenario)

        self.NrACFEstablishmentVariables = self.Instance.NrACFPPoints        
        self.NrVehicleAssignmentVariables = self.Instance.NrRescueVehicles * self.Instance.NrACFPPoints        
        
        self.NrApheresisAssignmentVariables = self.Instance.NrACFPPoints * (self.DemandScenarioTree.NrNode - 1)                                                                                         #We do not have NrApheresisAssignmentVariables var. in t=0!
        self.NrTransshipmentHIVariables = self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrACFPPoints * (self.DemandScenarioTree.NrNode - 1)        #We do not have variable Trans. Var. in t=0!
        self.NrTransshipmentIIVariables = self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints * (self.DemandScenarioTree.NrNode - 1)        #We do not have variable Trans. Var. in t=0!
        self.NrTransshipmentHHVariables = self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrHospitals * (self.DemandScenarioTree.NrNode - 1)        #We do not have variable Trans. Var. in t=0!
        
        self.NrPatientTransferVariables = self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * self.Instance.NrFacilities * self.Instance.NrRescueVehicles * (self.DemandScenarioTree.NrNode - 1)                                    #We do not have Shortage Var. in t=0!
        self.NrUnsatisfiedPatientsVariables = self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * (self.DemandScenarioTree.NrNode - 1)                                    #We do not have Shortage Var. in t=0!
        self.NrPlateletInventoryVariables = self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities * (self.DemandScenarioTree.NrNode - 1)                                    #We do not have Shortage Var. in t=0!
        self.NrOutdatedPlateletVariables = self.Instance.NrFacilities * (self.DemandScenarioTree.NrNode - 1)                                    #We do not have Shortage Var. in t=0!
        self.NrServedPatientVariables = self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities * (self.DemandScenarioTree.NrNode - 1)                                    #We do not have Shortage Var. in t=0!
        self.NrPatientPostponementVariables = self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrFacilities * (self.DemandScenarioTree.NrNode - 1)                                    #We do not have Shortage Var. in t=0!
        self.NrPlateletApheresisExtractionVariables = self.Instance.NRBloodGPs * self.Instance.NrFacilities * (self.DemandScenarioTree.NrNode - 1)                                    #We do not have Shortage Var. in t=0!
        self.NrPlateletWholeExtractionVariables = self.Instance.NRBloodGPs * self.Instance.NrHospitals * (self.DemandScenarioTree.NrNode - 1)                                    #We do not have Shortage Var. in t=0!

        self.StartACFEstablishmentVariables = 0
        self.StartVehicleAssignmentVariables = self.StartACFEstablishmentVariables + self.NrACFEstablishmentVariables
        self.StartApheresisAssignmentVariables = self.StartVehicleAssignmentVariables + self.NrVehicleAssignmentVariables
        self.StartTransshipmentHIVariables = self.StartApheresisAssignmentVariables + self.NrApheresisAssignmentVariables
        self.StartTransshipmentIIVariables = self.StartTransshipmentHIVariables + self.NrTransshipmentHIVariables
        self.StartTransshipmentHHVariables = self.StartTransshipmentIIVariables + self.NrTransshipmentIIVariables
        self.StartPatientTransferVariables = self.StartTransshipmentHHVariables + self.NrTransshipmentHHVariables
        self.StartUnsatisfiedPatientsVariables = self.StartPatientTransferVariables + self.NrPatientTransferVariables
        self.StartPlateletInventoryVariables = self.StartUnsatisfiedPatientsVariables + self.NrUnsatisfiedPatientsVariables
        self.StartOutdatedPlateletVariables = self.StartPlateletInventoryVariables + self.NrPlateletInventoryVariables
        self.StartServedPatientVariables = self.StartOutdatedPlateletVariables + self.NrOutdatedPlateletVariables
        self.StartPatientPostponementVariables = self.StartServedPatientVariables + self.NrServedPatientVariables
        self.StartPlateletApheresisExtractionVariables = self.StartPatientPostponementVariables + self.NrPatientPostponementVariables
        self.StartPlateletWholeExtractionVariables = self.StartPlateletApheresisExtractionVariables + self.NrPlateletApheresisExtractionVariables

        self.NrFixedQuantity = 0
        self.NrHasLeftOver = 0

        if Constants.Debug:
            print("self.StartACFEstablishmentVariables: ", self.StartACFEstablishmentVariables)
            print("self.NrACFEstablishmentVariables: ", self.NrACFEstablishmentVariables)
            print("self.StartVehicleAssignmentVariables: ", self.StartVehicleAssignmentVariables)
            print("self.NrVehicleAssignmentVariables: ", self.NrVehicleAssignmentVariables)
            print("self.StartApheresisAssignmentVariables: ", self.StartApheresisAssignmentVariables)
            print("self.NrApheresisAssignmentVariables: ", self.NrApheresisAssignmentVariables)
            print("self.StartTransshipmentHIVariables: ", self.StartTransshipmentHIVariables)
            print("self.NrTransshipmentHIVariables: ", self.NrTransshipmentHIVariables)
            print("self.StartTransshipmentIIVariables: ", self.StartTransshipmentIIVariables)
            print("self.NrTransshipmentIIVariables: ", self.NrTransshipmentIIVariables)
            print("self.StartTransshipmentHHVariables: ", self.StartTransshipmentHHVariables)
            print("self.NrTransshipmentHHVariables: ", self.NrTransshipmentHHVariables)
            print("self.StartPatientTransferVariables: ", self.StartPatientTransferVariables)
            print("self.NrPatientTransferVariables: ", self.NrPatientTransferVariables)
            print("self.StartUnsatisfiedPatientsVariables: ", self.StartUnsatisfiedPatientsVariables)
            print("self.NrUnsatisfiedPatientsVariables: ", self.NrUnsatisfiedPatientsVariables)
            print("self.StartPlateletInventoryVariables: ", self.StartPlateletInventoryVariables)
            print("self.NrPlateletInventoryVariables: ", self.NrPlateletInventoryVariables)
            print("self.StartOutdatedPlateletVariables: ", self.StartOutdatedPlateletVariables)
            print("self.NrOutdatedPlateletVariables: ", self.NrOutdatedPlateletVariables)
            print("self.StartServedPatientVariables: ", self.StartServedPatientVariables)
            print("self.NrServedPatientVariables: ", self.NrServedPatientVariables)
            print("self.StartPatientPostponementVariables: ", self.StartPatientPostponementVariables)
            print("self.NrPatientPostponementVariables: ", self.NrPatientPostponementVariables)
            print("self.StartPlateletApheresisExtractionVariables: ", self.StartPlateletApheresisExtractionVariables)
            print("self.NrPlateletApheresisExtractionVariables: ", self.NrPlateletApheresisExtractionVariables)
            print("self.StartPlateletWholeExtractionVariables: ", self.StartPlateletWholeExtractionVariables)
            print("self.NrPlateletWholeExtractionVariables: ", self.NrPlateletWholeExtractionVariables)

    def GetStartACFEstablishmentVariables(self):
        return self.StartACFEstablishmentVariables
    
    def GetStartVehicleAssignmentVariables(self):
        return self.StartVehicleAssignmentVariables
   
    def GetStartApheresisAssignmentVariable(self):
        return self.StartApheresisAssignmentVariables
    
    def GetStartTransshipmentHIVariable(self):
        return self.StartTransshipmentHIVariables
    
    def GetStartTransshipmentIIVariable(self):
        return self.StartTransshipmentIIVariables
    
    def GetStartTransshipmentHHVariable(self):
        return self.StartTransshipmentHHVariables

    def GetStartPatientTransferVariables(self):
        return self.StartPatientTransferVariables
    
    def GetStartUnsatisfiedPatientsVariables(self):
        return self.StartUnsatisfiedPatientsVariables
    
    def GetStartPlateletInventoryVariables(self):
        return self.StartPlateletInventoryVariables
    
    def GetStartOutdatedPlateletVariables(self):
        return self.StartOutdatedPlateletVariables
    
    def GetStartServedPatientVariables(self):
        return self.StartServedPatientVariables
    
    def GetStartPatientPostponementVariables(self):
        return self.StartPatientPostponementVariables
    
    def GetStartPlateletApheresisExtractionVariables(self):
        return self.StartPlateletApheresisExtractionVariables
    
    def GetStartPlateletWholeExtractionVariables(self):
        return self.StartPlateletWholeExtractionVariables
    
    #return the number of production variables
    def GetNrACFEstablishmentVariable(self):
        return self.NrACFEstablishmentVariables
    
    #return the number of production variables
    def GetNrVehicleAssignmentVariable(self):
        return self.NrVehicleAssignmentVariables
            
    # the function GetIndexACFEstablishmentVariable returns the index of the variable x_{i}
    def GetIndexACFEstablishmentVariable(self, i, w):
        #if Constants.Debug: print("We are in 'MIPSolver' Class -- GetIndexACFEstablishmentVariable")
        return self.Scenarios[w].ACFEstablishmentVariable[0][i]
    
    # the function GetIndexVehicleAssignmentVariable returns the index of the variable y_{s, d}
    def GetIndexVehicleAssignmentVariable(self, m, i, w):
        #if Constants.Debug: print("We are in 'MIPSolver' Class -- GetIndexVehicleAssignmentVariable")
        return self.Scenarios[w].VehicleAssignmentVariable[0][m][i]
        
    # the function GetIndexApheresisAssignmentVariable returns the index of the variable y_{tiw}    
    def GetIndexApheresisAssignmentVariable(self, t, i, w):

        if self.Model == Constants.Two_Stage:
            return self.GetStartApheresisAssignmentVariable() \
                            + t * self.Instance.NrACFPPoints \
                            + i
        else:        
            return self.Scenarios[w].ApheresisAssignmentVariable[t][i] 
    
    # the function GetIndexTransshipmentHIVariable returns the index of the variable b_{tcrhiw}.    
    def GetIndexTransshipmentHIVariable(self, t, c, r, h, i, w):

        if self.Model == Constants.Two_Stage:
            return self.GetStartTransshipmentHIVariable() \
                        + t * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrACFPPoints \
                        + c * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrACFPPoints \
                        + r * self.Instance.NrHospitals * self.Instance.NrACFPPoints \
                        + h * self.Instance.NrACFPPoints \
                        + i
        else:        
            return self.Scenarios[w].TransshipmentHIVariable[t][c][r][h][i] 
    
    # the function GetIndexTransshipmentIIVariable returns the index of the variable b'_{crii'}.    
    def GetIndexTransshipmentIIVariable(self, t, c, r, i, iprime, w):

        if self.Model == Constants.Two_Stage:
            return self.GetStartTransshipmentIIVariable() \
                        + t * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints \
                        + c * self.Instance.NRPlateletAges * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints \
                        + r * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints \
                        + i * self.Instance.NrACFPPoints \
                        + iprime
        else:        
            return self.Scenarios[w].TransshipmentIIVariable[t][c][r][i][iprime] 
    
    # the function GetIndexTransshipmentHHVariable returns the index of the variable b''_{crhh'}.    
    def GetIndexTransshipmentHHVariable(self, t, c, r, h, hprime, w):

        if self.Model == Constants.Two_Stage:
            return self.GetStartTransshipmentHHVariable() \
                        + t * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrHospitals \
                        + c * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrHospitals \
                        + r * self.Instance.NrHospitals * self.Instance.NrHospitals \
                        + h * self.Instance.NrHospitals \
                        + hprime
        else:        
            return self.Scenarios[w].TransshipmentHHVariable[t][c][r][h][hprime] 
            
    # the function GetIndexPatientTransferVariable returns the index of the variable q_{wtjclum}.    
    def GetIndexPatientTransferVariable(self, t, j, c, l, u, m, w):
        #if Constants.Debug: print("We are in 'MIPSolver' Class -- GetIndexPatientTransferVariable")
        return self.Scenarios[w].PatientTransferVariable[t][j][c][l][u][m] 
    
    # the function GetIndexUnsatisfiedPatientsVariable returns the index of the variable mu_{wtjcl}.    
    def GetIndexUnsatisfiedPatientsVariable(self, t, j, c, l, w):

        return self.Scenarios[w].UnsatisfiedPatientsVariable[t][j][c][l]
    
    # the function GetIndexPlateletInventoryVariable returns the index of the variable eta_{wtcru}.    
    def GetIndexPlateletInventoryVariable(self, t, c, r, u, w):

        return self.Scenarios[w].PlateletInventoryVariable[t][c][r][u] 
    
    # the function GetIndexOutdatedPlateletVariable returns the index of the variable sigmavar_{wtu}.    
    def GetIndexOutdatedPlateletVariable(self, t, u, w):
        return self.Scenarios[w].OutdatedPlateletVariable[t][u] 
    
    # the function GetIndexServedPatientVariable returns the index of the variable upsilon_{wtjc'cru}.    
    def GetIndexServedPatientVariable(self, t, j, cprime, c, r, u, w):
        return self.Scenarios[w].ServedPatientVariable[t][j][cprime][c][r][u]
    
    # the function GetIndexPatientPostponementVariable returns the index of the variable zeta_{wtjcu}.    
    def GetIndexPatientPostponementVariable(self, t, j, c, u, w):
        return self.Scenarios[w].PatientPostponementVariable[t][j][c][u] 
    
    # the function GetIndexPlateletApheresisExtractionVariable returns the index of the variable lambda_{wtcu}.    
    def GetIndexPlateletApheresisExtractionVariable(self, t, c, u, w):
        return self.Scenarios[w].PlateletApheresisExtractionVariable[t][c][u] 
    
    # the function GetIndexPlateletWholeExtractionVariable returns the index of the variable Rhovar_{wtch.    
    def GetIndexPlateletWholeExtractionVariable(self, t, c, h, w):
        return self.Scenarios[w].PlateletWholeExtractionVariable[t][c][h]

    def GetApheresisAssignmentCoeff(self, t, i, w):
        return self.Instance.ApheresisMachineAssignment_Cost[i] * self.Scenarios[w].Probability
        
    def GetTransshipmentHICoeff(self, t, h, i, w):
        return self.Instance.Distance_A_H[i][h] * self.Scenarios[w].Probability
        
    def GetTransshipmentIICoeff(self, t, i, iprime, w):
        return self.Instance.Distance_A_A[i][iprime] * self.Scenarios[w].Probability
        
    def GetTransshipmentHHCoeff(self, t, h, hprime, w):
        return self.Instance.Distance_H_H[h][hprime] * self.Scenarios[w].Probability
    
    def GetPatientTransferCoeff(self, t, l, u, w):

        if u < self.Instance.NrHospitals:
            return self.Instance.Distance_D_H[l][u] * self.Scenarios[w].Probability
        else:
            return self.Instance.Distance_D_A[l][u-self.Instance.NrHospitals] * self.Scenarios[w].Probability
        
    def GetUnsatisfiedPatientsCoeff(self, t, j, l, w):

        return self.Instance.Casualty_Shortage_Cost[j][l] * self.Scenarios[w].Probability
    
    def GetPlateletInventoryCoeff(self, t, u, w):
        return self.Instance.Platelet_Inventory_Cost[u] * self.Scenarios[w].Probability
    
    def GetOutdatedPlateletCoeff(self, t, u, w):
        return self.Instance.Platelet_Wastage_Cost[u] * self.Scenarios[w].Probability
    
    def GetServedPatientCoeff(self, t, cprime, c, w):
        return self.Instance.Substitution_Weight[cprime][c] * self.Scenarios[w].Probability
    
    def GetPatientPostponementCoeff(self, t, j, w):
        return self.Instance.Postponing_Cost_Surgery[j] * self.Scenarios[w].Probability
    
    def GetPlateletApheresisExtractionCoeff(self, u, t, w):
        return self.Instance.ApheresisExtraction_Cost[u] * self.Scenarios[w].Probability
    
    def GetPlateletWholeExtractionCoeff(self, h, t, w):
        return self.Instance.WholeExtraction_Cost[h] * self.Scenarios[w].Probability
        
    def GetacfestablishmentCoeff(self, i):
        return self.Instance.Fixed_Cost_ACF[i]
    
    def GetvehicleassignmentCoeff(self, m, i):
        return self.Instance.VehicleAssignment_Cost[m]
        
    # This function define the variables and related objective functions
    def CreateVariable_and_Objective_Function(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateVariable_and_Objective_Function")

        ################################# ACF Establishment Variable #################################
        acfestablishmentcost = {}
        self.ACF_Establishment_Var = {}

        for i in self.Instance.ACFPPointSet:                
            
            Index_Cost = self.GetIndexACFEstablishmentVariable(i, 0) - self.GetStartACFEstablishmentVariables()               
            acfestablishmentcost[Index_Cost] = self.GetacfestablishmentCoeff(i)
            Index_Var = self.GetIndexACFEstablishmentVariable(i, 0)
            var_name = f"x_i_{i}_index_{Index_Var}"

            if self.EvaluateSolution or self.Multi_StageHeuristic:
                self.ACF_Establishment_Var[Index_Var] = self.CRPBIM.addVar(vtype=GRB.CONTINUOUS, obj=acfestablishmentcost[Index_Cost], lb=0, ub=1, name=var_name)
            else:
                self.ACF_Establishment_Var[Index_Var] = self.CRPBIM.addVar(vtype=GRB.BINARY, obj=acfestablishmentcost[Index_Cost], lb=0, ub=1, name=var_name)

        self.CRPBIM.update()

        '''
        if Constants.Debug:
            for var_index in self.ACF_Establishment_Var:
                var = self.ACF_Establishment_Var[var_index]
                var_type = 'Continuous' if var.VType == GRB.CONTINUOUS else 'Binary' if var.VType == GRB.BINARY else 'Other'
                var_name = var.VarName
                lb = var.LB 
                ub = var.UB
                obj_coeff = var.Obj  
                print(f"Variable Name: {var_name}, Type: {var_type}, Lower Bound: {lb}, Upper Bound: {ub}, Objective Coefficient: {obj_coeff}")
        '''
        ################################# Vehicle Assignment Variable #################################
        vehicleassignmentcost = {}
        self.Vehicle_Assignment_Var = {}

        for m in self.Instance.RescueVehicleSet:
            for i in self.Instance.ACFPPointSet:
                
                Index_Cost = self.GetIndexVehicleAssignmentVariable(m, i, 0) - self.GetStartVehicleAssignmentVariables()               
                vehicleassignmentcost[Index_Cost] = self.GetvehicleassignmentCoeff(m, i)

                Index_Var = self.GetIndexVehicleAssignmentVariable(m, i, 0)
                var_name = f"vartheta_m_{m}_i_{i}_index_{Index_Var}"

                if self.EvaluateSolution or self.Multi_StageHeuristic:
                    self.Vehicle_Assignment_Var[Index_Var] = self.CRPBIM.addVar(vtype=GRB.CONTINUOUS, obj=vehicleassignmentcost[Index_Cost], lb=0, ub=self.Instance.Number_Rescue_Vehicle_ACF[m], name=var_name)
                else:
                    self.Vehicle_Assignment_Var[Index_Var] = self.CRPBIM.addVar(vtype=GRB.INTEGER, obj=vehicleassignmentcost[Index_Cost], lb=0, ub=self.Instance.Number_Rescue_Vehicle_ACF[m], name=var_name)
        self.CRPBIM.update()

        '''
        if Constants.Debug:
            for var_index in self.Vehicle_Assignment_Var:
                var = self.Vehicle_Assignment_Var[var_index]
                var_type = 'Continuous' if var.VType == GRB.CONTINUOUS else 'Binary' if var.VType == GRB.BINARY else 'Integer'
                var_name = var.VarName
                lb = var.LB        
                ub = var.UB 
                obj_coeff = var.Obj 
                print(f"Variable Name: {var_name}, Type: {var_type}, Lower Bound: {lb}, Upper Bound: {ub}, Objective Coefficient: {obj_coeff}")
        '''
        ################################# Apheresis Assignment Variable Variable #################################
        apheresisAssignmentcost = {}
        self.ApheresisAssignment_Var = {}

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:  
                for i in self.Instance.ACFPPointSet:

                    index_cost = self.GetIndexApheresisAssignmentVariable(t, i, w) - self.GetStartApheresisAssignmentVariable()

                    cost = self.GetApheresisAssignmentCoeff(t, i, w)
                    apheresisAssignmentcost[index_cost] = apheresisAssignmentcost.get(index_cost, 0) + cost

                    Index_Var = self.GetIndexApheresisAssignmentVariable(t, i, w)
                    var_name = f"y_w_{w}_t_{t}_i_{i}_index_{Index_Var}"

                    #if Constants.IntegerRecourse:
                    #    var_type = GRB.INTEGER

                    self.ApheresisAssignment_Var[Index_Var] = self.CRPBIM.addVar(vtype=GRB.CONTINUOUS, obj=apheresisAssignmentcost[index_cost], lb=0, ub=self.Instance.Total_Apheresis_Machine_ACF[t], name=var_name)
        self.CRPBIM.update()
        
        '''
        if Constants.Debug:
            for var_index in self.ApheresisAssignment_Var:
                var = self.ApheresisAssignment_Var[var_index]
                var_type = 'Continuous' if var.VType == GRB.CONTINUOUS else 'Binary' if var.VType == GRB.BINARY else 'Integer'
                var_name = var.VarName
                lb = var.LB         
                ub = var.UB  
                obj_coeff = var.Obj  
                print(f"Variable Name: {var_name}, Type: {var_type}, Lower Bound: {lb}, Upper Bound: {ub}, Objective Coefficient: {obj_coeff}")
        ''' 
        ################################# Transshipment HI Variable #################################
        transshipmentHIcost = {}
        self.TransshipmentHI_Var = {}

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:  
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            for i in self.Instance.ACFPPointSet:

                                index_cost = self.GetIndexTransshipmentHIVariable(t, c, r, h, i, w) - self.GetStartTransshipmentHIVariable()

                                cost = self.GetTransshipmentHICoeff(t, h, i, w)
                                transshipmentHIcost[index_cost] = transshipmentHIcost.get(index_cost, 0) + cost

                                Index_Var = self.GetIndexTransshipmentHIVariable(t, c, r, h, i, w)
                                var_name = f"b_w_{w}_t_{t}_c_{c}_r_{r}_h_{h}_i_{i}_index_{Index_Var}"
                                self.TransshipmentHI_Var[Index_Var] = self.CRPBIM.addVar(vtype=GRB.CONTINUOUS, obj=transshipmentHIcost[index_cost], lb=0, ub=Constants.Infinity, name=var_name)
        self.CRPBIM.update()
        
        '''
        if Constants.Debug:
            for var_index in self.TransshipmentHI_Var:
                var = self.TransshipmentHI_Var[var_index]
                var_type = 'Continuous' if var.VType == GRB.CONTINUOUS else 'Binary' if var.VType == GRB.BINARY else 'Integer'
                var_name = var.VarName
                lb = var.LB             
                ub = var.UB  
                obj_coeff = var.Obj 
                print(f"Variable Name: {var_name}, Type: {var_type}, Lower Bound: {lb}, Upper Bound: {ub}, Objective Coefficient: {obj_coeff}")
        '''

        ################################# Transshipment II Variable #################################
        transshipmentIIcost = {}
        self.TransshipmentII_Var = {}

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:  
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for i in self.Instance.ACFPPointSet:
                            for iprime in self.Instance.ACFPPointSet:

                                index_cost = self.GetIndexTransshipmentIIVariable(t, c, r, i, iprime, w) - self.GetStartTransshipmentIIVariable()

                                cost = self.GetTransshipmentIICoeff(t, i, iprime, w)
                                transshipmentIIcost[index_cost] = transshipmentIIcost.get(index_cost, 0) + cost

                                Index_Var = self.GetIndexTransshipmentIIVariable(t, c, r, i, iprime, w)
                                
                                var_name = f"b'_w_{w}_t_{t}_c_{c}_r_{r}_i_{i}_i'_{iprime}_index_{Index_Var}"
                                
                                if i == iprime:
                                    UBound = 0
                                else:
                                    UBound = Constants.Infinity
                                
                                if Constants.Transshipment_Enabled == False:
                                    UBound = 0
                                
                                self.TransshipmentII_Var[Index_Var] = self.CRPBIM.addVar(vtype=GRB.CONTINUOUS, obj=transshipmentIIcost[index_cost], lb=0, ub=UBound, name=var_name)
        
        self.CRPBIM.update()

        '''
        if Constants.Debug:
            for var_index in self.TransshipmentII_Var:
                var = self.TransshipmentII_Var[var_index]
                var_type = 'Continuous' if var.VType == GRB.CONTINUOUS else 'Binary' if var.VType == GRB.BINARY else 'Integer'
                var_name = var.VarName
                lb = var.LB             
                ub = var.UB  
                obj_coeff = var.Obj  
                print(f"Variable Name: {var_name}, Type: {var_type}, Lower Bound: {lb}, Upper Bound: {ub}, Objective Coefficient: {obj_coeff}")
        '''
        ################################# Transshipment HH Variable #################################
        transshipmentHHcost = {}
        self.TransshipmentHH_Var = {}

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:  
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            for hprime in self.Instance.HospitalSet:
                                
                                index_cost = self.GetIndexTransshipmentHHVariable(t, c, r, h, hprime, w) - self.GetStartTransshipmentHHVariable()
                                cost = self.GetTransshipmentHHCoeff(t, h, hprime, w)
                                transshipmentHHcost[index_cost] = transshipmentHHcost.get(index_cost, 0) + cost
                                Index_Var = self.GetIndexTransshipmentHHVariable(t, c, r, h, hprime, w)
                                var_name = f"b''_w_{w}_t_{t}_c_{c}_r_{r}_h_{h}_h'_{hprime}_index_{Index_Var}"
                                if h == hprime:
                                    UBound = 0
                                else:
                                    UBound = Constants.Infinity
                                
                                if Constants.Transshipment_Enabled == False:
                                    UBound = 0

                                self.TransshipmentHH_Var[Index_Var] = self.CRPBIM.addVar(vtype=GRB.CONTINUOUS, obj=transshipmentHHcost[index_cost], lb=0, ub=UBound, name=var_name)
        self.CRPBIM.update()
        
        '''
        if Constants.Debug:
            for var_index in self.TransshipmentHH_Var:
                var = self.TransshipmentHH_Var[var_index]
                var_type = 'Continuous' if var.VType == GRB.CONTINUOUS else 'Binary' if var.VType == GRB.BINARY else 'Integer'
                var_name = var.VarName
                lb = var.LB       
                ub = var.UB 
                obj_coeff = var.Obj  
                print(f"Variable Name: {var_name}, Type: {var_type}, Lower Bound: {lb}, Upper Bound: {ub}, Objective Coefficient: {obj_coeff}")
        '''                 
        ################################# Patient Transfer Variable #################################
        patientTransfercost = {}
        self.PatientTransfer_Var= {}

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for j in self.Instance.InjuryLevelSet:
                    for c in self.Instance.BloodGPSet:
                        for l in self.Instance.DemandSet:
                            for u in self.Instance.FacilitySet:
                                for m in self.Instance.RescueVehicleSet:
            
                                    index_cost = self.GetIndexPatientTransferVariable(t, j, c, l, u, m, w) - self.GetStartPatientTransferVariables()
                                    cost = self.GetPatientTransferCoeff(t, l, u, w)                   
                                    patientTransfercost[index_cost] = patientTransfercost.get(index_cost, 0) + cost
                                    
                                    Index_Var = self.GetIndexPatientTransferVariable(t, j, c, l, u, m, w)
                                    var_name = f"q_w_{w}_t_{t}_j_{j}_c_{c}_l_{l}_u_{u}_m_{m}_index_{Index_Var}"

                                    self.PatientTransfer_Var[Index_Var] = self.CRPBIM.addVar(vtype=GRB.CONTINUOUS, obj=patientTransfercost[index_cost], lb=0, ub=Constants.Infinity, name=var_name)
        self.CRPBIM.update()
        
        '''
        if Constants.Debug:
            for var_index in self.PatientTransfer_Var:
                var = self.PatientTransfer_Var[var_index]
                var_type = 'Continuous' if var.VType == GRB.CONTINUOUS else 'Binary' if var.VType == GRB.BINARY else 'Integer'
                var_name = var.VarName
                lb = var.LB            
                ub = var.UB  
                obj_coeff = var.Obj 
                print(f"Variable Name: {var_name}, Type: {var_type}, Lower Bound: {lb}, Upper Bound: {ub}, Objective Coefficient: {obj_coeff}")
        '''                
        ################################# Unsatisfied Patients Variable #################################
        unsatisfiedPatientscost = {}
        self.UnsatisfiedPatients_Var= {}

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for j in self.Instance.InjuryLevelSet:
                    for c in self.Instance.BloodGPSet:
                        for l in self.Instance.DemandSet:                    
                            
                            index_cost = self.GetIndexUnsatisfiedPatientsVariable(t, j, c, l, w) - self.GetStartUnsatisfiedPatientsVariables()
                            
                            cost = self.GetUnsatisfiedPatientsCoeff(t, j, l, w)
                            
                            unsatisfiedPatientscost[index_cost] = unsatisfiedPatientscost.get(index_cost, 0) + cost
                            
                            Index_Var = self.GetIndexUnsatisfiedPatientsVariable(t, j, c, l, w)
                            var_name = f"mu_w_{w}_t_{t}_j_{j}_c_{c}_l_{l}_index_{Index_Var}"

                            self.UnsatisfiedPatients_Var[Index_Var] = self.CRPBIM.addVar(vtype=GRB.CONTINUOUS, obj=unsatisfiedPatientscost[index_cost], lb=0, ub=Constants.Infinity, name=var_name)
                
        self.CRPBIM.update()
        
        '''
        if Constants.Debug:
            for var_index in self.UnsatisfiedPatients_Var:
                var = self.UnsatisfiedPatients_Var[var_index]
                var_type = 'Continuous' if var.VType == GRB.CONTINUOUS else 'Binary' if var.VType == GRB.BINARY else 'Integer'
                var_name = var.VarName
                lb = var.LB              
                ub = var.UB 
                obj_coeff = var.Obj 
                print(f"Variable Name: {var_name}, Type: {var_type}, Lower Bound: {lb}, Upper Bound: {ub}, Objective Coefficient: {obj_coeff}")
        '''
        ################################# Platelet Inventory Variable #################################
        plateletInventorycost = {}
        self.PlateletInventory_Var= {}

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for u in self.Instance.FacilitySet:  

                            index_cost = self.GetIndexPlateletInventoryVariable(t, c, r, u, w) - self.GetStartPlateletInventoryVariables()
                            cost = self.GetPlateletInventoryCoeff(t, u, w)                            
                            plateletInventorycost[index_cost] = plateletInventorycost.get(index_cost, 0) + cost
                            Index_Var = self.GetIndexPlateletInventoryVariable(t, c, r, u, w)
                            var_name = f"eta_w_{w}_t_{t}_c_{c}_r_{r}_u_{u}_index_{Index_Var}"

                            self.PlateletInventory_Var[Index_Var] = self.CRPBIM.addVar(vtype=GRB.CONTINUOUS, obj=plateletInventorycost[index_cost], lb=0, ub=Constants.Infinity, name=var_name)
                
        self.CRPBIM.update()

        '''
        if Constants.Debug:
            for var_index in self.PlateletInventory_Var:
                var = self.PlateletInventory_Var[var_index]
                var_type = 'Continuous' if var.VType == GRB.CONTINUOUS else 'Binary' if var.VType == GRB.BINARY else 'Integer'
                var_name = var.VarName
                lb = var.LB              
                ub = var.UB  
                obj_coeff = var.Obj  
                print(f"Variable Name: {var_name}, Type: {var_type}, Lower Bound: {lb}, Upper Bound: {ub}, Objective Coefficient: {obj_coeff}")        
        '''
        ################################# Outdated Platelet Variable #################################
        outdatedPlateletcost = {}
        self.OutdatedPlatelet_Var= {}

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for u in self.Instance.FacilitySet:
                    
                    index_cost = self.GetIndexOutdatedPlateletVariable(t, u, w) - self.GetStartOutdatedPlateletVariables()
                    cost = self.GetOutdatedPlateletCoeff(t, u, w)                     
                    outdatedPlateletcost[index_cost] = outdatedPlateletcost.get(index_cost, 0) + cost
                    
                    Index_Var = self.GetIndexOutdatedPlateletVariable(t, u, w)
                    var_name = f"Sigmavar_w_{w}_t_{t}_u_{u}_index_{Index_Var}"

                    self.OutdatedPlatelet_Var[Index_Var] = self.CRPBIM.addVar(vtype=GRB.CONTINUOUS, obj=outdatedPlateletcost[index_cost], lb=0, ub=Constants.Infinity, name=var_name)
        
        self.CRPBIM.update()

        '''
        if Constants.Debug:
            for var_index in self.OutdatedPlatelet_Var:
                var = self.OutdatedPlatelet_Var[var_index]
                var_type = 'Continuous' if var.VType == GRB.CONTINUOUS else 'Binary' if var.VType == GRB.BINARY else 'Integer'
                var_name = var.VarName
                lb = var.LB             
                ub = var.UB 
                obj_coeff = var.Obj 
                print(f"Variable Name: {var_name}, Type: {var_type}, Lower Bound: {lb}, Upper Bound: {ub}, Objective Coefficient: {obj_coeff}")        
        '''

        ################################# Served Patient  Variable #################################
        servedPatientcost = {}
        self.ServedPatient_Var= {}

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for j in self.Instance.InjuryLevelSet:
                    for cprime in self.Instance.BloodGPSet:
                        for c in self.Instance.BloodGPSet:
                            for r in self.Instance.PlateletAgeSet:
                                for u in self.Instance.FacilitySet:

                                    index_cost = self.GetIndexServedPatientVariable(t, j, cprime, c, r, u, w) - self.GetStartServedPatientVariables()
                                    cost = self.GetServedPatientCoeff(t, cprime, c, w)
                                    
                                    servedPatientcost[index_cost] = servedPatientcost.get(index_cost, 0) + cost
                                    
                                    Index_Var = self.GetIndexServedPatientVariable(t, j, cprime, c, r, u, w)
                                    var_name = f"upsilon_w_{w}_t_{t}_j_{j}_c'_{cprime}_c_{c}_r_{r}_u_{u}_index_{Index_Var}"

                                    self.ServedPatient_Var[Index_Var] = self.CRPBIM.addVar(vtype=GRB.CONTINUOUS, obj=servedPatientcost[index_cost], lb=0, ub=Constants.Infinity, name=var_name)
                        
        self.CRPBIM.update()

        '''
        if Constants.Debug:
            for var_index in self.ServedPatient_Var:
                var = self.ServedPatient_Var[var_index]
                var_type = 'Continuous' if var.VType == GRB.CONTINUOUS else 'Binary' if var.VType == GRB.BINARY else 'Integer'
                var_name = var.VarName
                lb = var.LB           
                ub = var.UB  
                obj_coeff = var.Obj  
                print(f"Variable Name: {var_name}, Type: {var_type}, Lower Bound: {lb}, Upper Bound: {ub}, Objective Coefficient: {obj_coeff}")        
        '''
        ################################# Patient Postponement Variable #################################
        patientPostponementcost = {}
        self.PatientPostponement_Var= {}

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for j in self.Instance.InjuryLevelSet:
                    for c in self.Instance.BloodGPSet:
                        for u in self.Instance.FacilitySet:

                            index_cost = self.GetIndexPatientPostponementVariable(t, j, c, u, w) - self.GetStartPatientPostponementVariables()
                            
                            cost = self.GetPatientPostponementCoeff(t, j, w)

                            patientPostponementcost[index_cost] = patientPostponementcost.get(index_cost, 0) + cost
                            
                            Index_Var = self.GetIndexPatientPostponementVariable(t, j, c, u, w)
                            var_name = f"zeta_w_{w}_t_{t}_j_{j}_c_{c}_u_{u}_index_{Index_Var}"

                            self.PatientPostponement_Var[Index_Var] = self.CRPBIM.addVar(vtype=GRB.CONTINUOUS, obj=patientPostponementcost[index_cost], lb=0, ub=Constants.Infinity, name=var_name)
                
        self.CRPBIM.update()

        '''
        if Constants.Debug:
            for var_index in self.PatientPostponement_Var:
                var = self.PatientPostponement_Var[var_index]
                var_type = 'Continuous' if var.VType == GRB.CONTINUOUS else 'Binary' if var.VType == GRB.BINARY else 'Integer'
                var_name = var.VarName
                lb = var.LB             
                ub = var.UB  
                obj_coeff = var.Obj  
                print(f"Variable Name: {var_name}, Type: {var_type}, Lower Bound: {lb}, Upper Bound: {ub}, Objective Coefficient: {obj_coeff}")        
        '''
        ################################# Platelet Apheresis Extraction Variable #################################
        plateletApheresisExtractioncost = {}
        self.PlateletApheresisExtraction_Var= {}

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for u in self.Instance.FacilitySet:
                    
                        index_cost = self.GetIndexPlateletApheresisExtractionVariable(t, c, u, w) - self.GetStartPlateletApheresisExtractionVariables()
                        
                        cost = self.GetPlateletApheresisExtractionCoeff(u, t, w)
                        
                        plateletApheresisExtractioncost[index_cost] = plateletApheresisExtractioncost.get(index_cost, 0) + cost
                        
                        Index_Var = self.GetIndexPlateletApheresisExtractionVariable(t, c, u, w)
                        var_name = f"lambda_w_{w}_t_{t}_c_{c}_u_{u}_index_{Index_Var}"

                        self.PlateletApheresisExtraction_Var[Index_Var] = self.CRPBIM.addVar(vtype=GRB.CONTINUOUS, obj=plateletApheresisExtractioncost[index_cost], lb=0, ub=Constants.Infinity, name=var_name)
            
        self.CRPBIM.update()

        '''
        if Constants.Debug:
            for var_index in self.PlateletApheresisExtraction_Var:
                var = self.PlateletApheresisExtraction_Var[var_index]
                var_type = 'Continuous' if var.VType == GRB.CONTINUOUS else 'Binary' if var.VType == GRB.BINARY else 'Integer'
                var_name = var.VarName
                lb = var.LB             
                ub = var.UB 
                obj_coeff = var.Obj 
                print(f"Variable Name: {var_name}, Type: {var_type}, Lower Bound: {lb}, Upper Bound: {ub}, Objective Coefficient: {obj_coeff}")        
        '''

        ################################# Platelet Whole Extraction Variable #################################
        plateletWholeExtractioncost = {}
        self.PlateletWholeExtraction_Var= {}

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for h in self.Instance.HospitalSet:

                        index_cost = self.GetIndexPlateletWholeExtractionVariable(t, c, h, w) - self.GetStartPlateletWholeExtractionVariables()
                        
                        cost = self.GetPlateletWholeExtractionCoeff(h, t, w)

                        plateletWholeExtractioncost[index_cost] = plateletWholeExtractioncost.get(index_cost, 0) + cost
                        
                        Index_Var = self.GetIndexPlateletWholeExtractionVariable(t, c, h, w)
                        
                        var_name = f"Rhovar_w_{w}_t_{t}_c_{c}_h_{h}_index_{Index_Var}"

                        self.PlateletWholeExtraction_Var[Index_Var] = self.CRPBIM.addVar(vtype=GRB.CONTINUOUS, obj=plateletWholeExtractioncost[index_cost], lb=0, ub=Constants.Infinity, name=var_name)
            
        self.CRPBIM.update()

        '''
        if Constants.Debug:
            for var_index in self.PlateletWholeExtraction_Var:
                var = self.PlateletWholeExtraction_Var[var_index]
                var_type = 'Continuous' if var.VType == GRB.CONTINUOUS else 'Binary' if var.VType == GRB.BINARY else 'Integer'
                var_name = var.VarName
                lb = var.LB             
                ub = var.UB 
                obj_coeff = var.Obj 
                print(f"Variable Name: {var_name}, Type: {var_type}, Lower Bound: {lb}, Upper Bound: {ub}, Objective Coefficient: {obj_coeff}")        
        '''
        self.CRPBIM.setObjective(self.CRPBIM.getObjective(), GRB.MINIMIZE)

    def CreateCopyGivenACFEstablishmentConstraints(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateCopyGivenACFEstablishmentConstraints")

        self.ACFEstablishmentVarConstraintNR = [["" for _ in self.Instance.ACFPPointSet] 
                                    for _ in self.ScenarioSet]

        AlreadyAdded = [False for _ in range(self.GetNrACFEstablishmentVariable())]

        # FixedVars equal to the given ones
        for i in self.Instance.ACFPPointSet:
            for w in self.ScenarioSet:
                indexvariable = self.GetIndexACFEstablishmentVariable(i, w)
                indexinarray = indexvariable - self.GetStartACFEstablishmentVariables()

                if not AlreadyAdded[indexinarray]:

                    vars_x = [self.GetIndexACFEstablishmentVariable(i, w)]

                    AlreadyAdded[indexinarray] = True

                    #righthandside = round(self.GivenACFEstablishment[i], 2) #It is Correct but since my PHA is taking too long, I will change it to the next line to be able to solve the evaluation part!
                    righthandside = min(round(self.GivenACFEstablishment[i]), 1) # Using min Function, since the variable is binary

                    # Add constraint
                    constraint_name = f"CopyGivenACFEstablishment_w_{w}_i_{i}"
                    
                    if Constants.Debug: print(f"Adding constraint: {constraint_name} with RHS: {righthandside}")

                    self.CRPBIM.addConstr(self.ACF_Establishment_Var[vars_x[0]] == righthandside, name=constraint_name)

                    self.ACFEstablishmentVarConstraintNR[w][i] = constraint_name
    
    def CreateCopyGivenVehicleAssignmentConstraints(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateCopyGivenVehicleAssignmentConstraints")

        self.VehicleAssignmentVarConstraintNR = [[["" for i in self.Instance.ACFPPointSet] 
                                    for m in self.Instance.RescueVehicleSet] 
                                    for w in self.ScenarioSet]

        AlreadyAdded = [False for v in range(self.GetNrVehicleAssignmentVariable())]

        # FixedVars equal to the given ones
        for m in self.Instance.RescueVehicleSet:
            for i in self.Instance.ACFPPointSet:
                for w in self.ScenarioSet:
                    indexvariable = self.GetIndexVehicleAssignmentVariable(m, i, w)
                    indexinarray = indexvariable - self.GetStartVehicleAssignmentVariables()

                    if not AlreadyAdded[indexinarray]:

                        vars_thetavar = [self.GetIndexVehicleAssignmentVariable(m, i, w)]

                        AlreadyAdded[indexinarray] = True

                        #righthandside = round(self.GivenVehicleAssignment[m][i], 2)     #It is Correct but since my PHA is taking too long, I will change it to the next line to be able to solve the evaluation part!
                        righthandside = round(self.GivenVehicleAssignment[m][i])

                        # Add constraint
                        constraint_name = f"CopyGivenVehicleAssignment_w_{w}_m_{m}_i_{i}"
                        
                        if Constants.Debug: print(f"Adding constraint: {constraint_name} with RHS: {righthandside}")

                        self.CRPBIM.addConstr(self.Vehicle_Assignment_Var[vars_thetavar[0]] == righthandside, name=constraint_name)

                        self.VehicleAssignmentVarConstraintNR[w][m][i] = constraint_name

    def CreateCopyGivenApheresisAssignmentConstraints(self):
        if Constants.Debug: print("\nWe are in 'MIPSolver' Class -- CreateCopyGivenApheresisAssignmentConstraints")

        # Make sure the initialization matches the expected dimensions
        self.ApheresisAssignmentVarConstraintNR = [[["" for _ in self.Instance.ACFPPointSet] 
                                                        for _ in self.Instance.TimeBucketSet] 
                                                        for _ in self.ScenarioSet]

        AlreadyAdded = [False for _ in range(self.NrApheresisAssignmentVariables)]

        #if Constants.Debug: print("self.GivenApheresisAssignment: ", self.GivenApheresisAssignment)            
        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for i in self.Instance.ACFPPointSet:
                        
                    indexvariable = self.GetIndexApheresisAssignmentVariable(t, i, w) - self.GetStartApheresisAssignmentVariable()
                    if not AlreadyAdded[indexvariable] and (t <= self.FixSolutionUntil):
                        vars_y = [self.GetIndexApheresisAssignmentVariable(t, i, w)]
                        
                        AlreadyAdded[indexvariable] = True

                        righthandside = float(self.GivenApheresisAssignment[t][i])  # Adjust this according to the correct structure
                        
                        constraint_name = f"CopyGivenApheresisAssignment_w_{w}_t_{t}_i_{i}"
                        
                        #if Constants.Debug: print(f"Adding constraint: {constraint_name} with RHS: {righthandside}")
                        
                        constraint = self.CRPBIM.addConstr(self.ApheresisAssignment_Var[vars_y[0]] == righthandside, name=constraint_name)
                        
                        self.ApheresisAssignmentVarConstraintNR[w][t][i] = constraint

                        #if Constants.Debug: print(f"Constraint {constraint_name} added successfully.")
    
    def CreateCopyGivenTransshipmentHIConstraints(self):
        if Constants.Debug: print("\nWe are in 'MIPSolver' Class -- CreateCopyGivenTransshipmentHIConstraints")

        # Make sure the initialization matches the expected dimensions
        self.TransshipmentHIVarConstraintNR = [[[[[["" for _ in self.Instance.ACFPPointSet] 
                                                    for _ in self.Instance.HospitalSet] 
                                                    for _ in self.Instance.PlateletAgeSet] 
                                                    for _ in self.Instance.BloodGPSet] 
                                                    for _ in self.Instance.TimeBucketSet] 
                                                    for _ in self.ScenarioSet]

        AlreadyAdded = [False for _ in range(self.NrTransshipmentHIVariables)]

        #if Constants.Debug: print("self.GivenTransshipmentHI: ", self.GivenTransshipmentHI)            
        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            for i in self.Instance.ACFPPointSet:
                        
                                indexvariable = self.GetIndexTransshipmentHIVariable(t, c, r, h, i, w) - self.GetStartTransshipmentHIVariable()
                                if not AlreadyAdded[indexvariable] and (t <= self.FixSolutionUntil):
                                    vars_b = [self.GetIndexTransshipmentHIVariable(t, c, r, h, i, w)]
                                    AlreadyAdded[indexvariable] = True
                                    righthandside = float(self.GivenTransshipmentHI[t][c][r][h][i])  # Adjust this according to the correct structure
                                    constraint_name = f"CopyGivenTransshipmentHI_w_{w}_t_{t}_c_{c}_r_{r}_h_{h}_i_{i}"
                                    
                                    constraint = self.CRPBIM.addConstr(self.TransshipmentHI_Var[vars_b[0]] == righthandside, name=constraint_name)
                                    
                                    self.TransshipmentHIVarConstraintNR[w][t][c][r][h][i] = constraint
                                    #if Constants.Debug: print(f"Constraint {constraint_name} added successfully.")
    
    def CreateCopyGivenTransshipmentIIConstraints(self):
        if Constants.Debug: print("\nWe are in 'MIPSolver' Class -- CreateCopyGivenTransshipmentIIConstraints")

        # Make sure the initialization matches the expected dimensions
        self.TransshipmentIIVarConstraintNR = [[[[[["" for _ in self.Instance.ACFPPointSet] 
                                                    for _ in self.Instance.ACFPPointSet] 
                                                    for _ in self.Instance.PlateletAgeSet] 
                                                    for _ in self.Instance.BloodGPSet] 
                                                    for _ in self.Instance.TimeBucketSet] 
                                                    for _ in self.ScenarioSet]

        AlreadyAdded = [False for _ in range(self.NrTransshipmentIIVariables)]

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for i in self.Instance.ACFPPointSet:
                            for iprime in self.Instance.ACFPPointSet:
                        
                                indexvariable = self.GetIndexTransshipmentIIVariable(t, c, r, i, iprime, w) - self.GetStartTransshipmentIIVariable()
                                if not AlreadyAdded[indexvariable] and (t <= self.FixSolutionUntil):
                                    vars_bprime = [self.GetIndexTransshipmentIIVariable(t, c, r, i, iprime, w)]
                                    
                                    AlreadyAdded[indexvariable] = True
                                    righthandside = float(self.GivenTransshipmentII[t][c][r][i][iprime])  
                                    constraint_name = f"CopyGivenTransshipmentII_w_{w}_t_{t}_c_{c}_r_{r}_i_{i}i'_{iprime}"
                                    
                                    constraint = self.CRPBIM.addConstr(self.TransshipmentII_Var[vars_bprime[0]] == righthandside, name=constraint_name)
                                    
                                    self.TransshipmentIIVarConstraintNR[w][t][c][r][i][iprime] = constraint

                                    #if Constants.Debug: print(f"Constraint {constraint_name} added successfully.")
    
    def CreateCopyGivenTransshipmentHHConstraints(self):
        if Constants.Debug: print("\nWe are in 'MIPSolver' Class -- CreateCopyGivenTransshipmentHHConstraints")

        # Make sure the initialization matches the expected dimensions
        self.TransshipmentHHVarConstraintNR = [[[[[["" for _ in self.Instance.HospitalSet] 
                                                    for _ in self.Instance.HospitalSet] 
                                                    for _ in self.Instance.PlateletAgeSet] 
                                                    for _ in self.Instance.BloodGPSet] 
                                                    for _ in self.Instance.TimeBucketSet] 
                                                    for _ in self.ScenarioSet]

        AlreadyAdded = [False for _ in range(self.NrTransshipmentHHVariables)]

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            for hprime in self.Instance.HospitalSet:
                        
                                indexvariable = self.GetIndexTransshipmentHHVariable(t, c, r, h, hprime, w) - self.GetStartTransshipmentHHVariable()
                                if not AlreadyAdded[indexvariable] and (t <= self.FixSolutionUntil):
                                    vars_bDPrime = [self.GetIndexTransshipmentHHVariable(t, c, r, h, hprime, w)]
                                    AlreadyAdded[indexvariable] = True
                                    righthandside = float(self.GivenTransshipmentHH[t][c][r][h][hprime])
                                    constraint_name = f"CopyGivenTransshipmentHH_w_{w}_t_{t}_c_{c}_r_{r}_h_{h}_h'_{hprime}"
                                    
                                    constraint = self.CRPBIM.addConstr(self.TransshipmentHH_Var[vars_bDPrime[0]] == righthandside, name=constraint_name)
                                    
                                    self.TransshipmentHHVarConstraintNR[w][t][c][r][h][hprime] = constraint

                                    #if Constants.Debug: print(f"Constraint {constraint_name} added successfully.")

    def CreateBudgetConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateBudgetConstraint")
        
        vars_x = [self.GetIndexACFEstablishmentVariable(i, 0) for i in self.Instance.ACFPPointSet]
        
        coeff_x = [-1 * self.Instance.Fixed_Cost_ACF_Constraint[i] for i in self.Instance.ACFPPointSet]
        
        # Create the left-hand side of the constraint
        LeftHandSide = gp.quicksum(coeff_x[i] * self.ACF_Establishment_Var[vars_x[i]] for i in range(len(vars_x)))

        # Define the right-hand side (RHS) of the constraint
        RightHandSide = -1 * self.Instance.Total_Budget_ACF_Establishment  

        # Add the constraint to the model
        constraint_name = f"Budget_Constraint"
        self.CRPBIM.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
        
        '''
        if Constants.Debug: 
            print(f"Vars_x: {vars_x}")
            print(f"Coefficients: {coeff_x}")
            print(f"RightHandSide: ", RightHandSide)
            print(f"Added constraint: {constraint_name}")
        '''

    def CreateVehicleAssignmentCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateVehicleAssignmentCapacityConstraint")
        
        for m in self.Instance.RescueVehicleSet:

            vars_vartheta = [self.GetIndexVehicleAssignmentVariable(m, i, 0) 
                             for i in self.Instance.ACFPPointSet]
            coeff_vartheta = [-1.0 for i in self.Instance.ACFPPointSet]
            
            # # Create the left-hand side of the constraint
            LeftHandSide = gp.quicksum(coeff_vartheta[i] * self.Vehicle_Assignment_Var[vars_vartheta[i]] for i in range(len(vars_vartheta)))

            # Define the right-hand side (RHS) of the constraint
            RightHandSide = -1 * self.Instance.Number_Rescue_Vehicle_ACF[m]  

            # Add the constraint to the model
            constraint_name = f"VehicleAssignmentCapacity_m_{m}"

            self.CRPBIM.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

            '''
            if Constants.Debug: 
                print(f"vars_vartheta: {vars_vartheta}")
                print(f"Coefficients: {coeff_vartheta}")
                print(f"RightHandSide: ", RightHandSide)
                print(f"Added constraint: {constraint_name}")
            '''    

    def CreateVehicleAssignemntACFEstablishmentConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateVehicleAssignemntACFEstablishmentConstraint")
        
        for i in self.Instance.ACFPPointSet:
            for m in self.Instance.RescueVehicleSet:

                vars_x = [self.GetIndexACFEstablishmentVariable(i, 0)]
                coeff_x = [self.Instance.Number_Rescue_Vehicle_ACF[m]]

                vars_vartheta = [self.GetIndexVehicleAssignmentVariable(m, i, 0)]
                coeff_vartheta = [-1.0]
                
                # # Create the left-hand side of the constraint
                LeftHandSide_x = gp.quicksum(coeff_x[i] * self.ACF_Establishment_Var[vars_x[i]] for i in range(len(vars_x)))
                LeftHandSide_vartheta = gp.quicksum(coeff_vartheta[i] * self.Vehicle_Assignment_Var[vars_vartheta[i]] for i in range(len(vars_vartheta)))

                LeftHandSide = LeftHandSide_x + LeftHandSide_vartheta

                # Define the right-hand side (RHS) of the constraint
                RightHandSide = 0  

                # Add the constraint to the model
                constraint_name = f"VehicleAssignemntACFEstablishment_i_{i}_m_{m}"

                self.CRPBIM.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                '''
                if Constants.Debug: 
                    print(f"vars_x: {vars_x}")
                    print(f"Coeff_x: {coeff_x}")
                    print(f"vars_vartheta: {vars_vartheta}")
                    print(f"Coeff_vartheta: {coeff_vartheta}")
                    print(f"RightHandSide: ", RightHandSide)
                    print(f"Added constraint: {constraint_name}")
                '''

    def CreateLowMedPriorityPatientFlowConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateLowMedPriorityPatientFlowConstraint")
        if Constants.Debug: Debug_Average_Demand = 0
        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for j in self.Instance.InjuryLevelSet:
                    if j != 0:                      # Only for Low- and Med- Priority Patients
                        for c in self.Instance.BloodGPSet:
                            for l in self.Instance.DemandSet:

                                vars_q = [self.GetIndexPatientTransferVariable(t, j, c, l, u, m, w) 
                                            for u in self.Instance.FacilitySet
                                            if self.Instance.J_u[u][j] == 1
                                            for m in self.Instance.RescueVehicleSet]

                                coeff_q = [1.0  
                                           for u in self.Instance.FacilitySet 
                                           if self.Instance.J_u[u][j] == 1
                                           for m in self.Instance.RescueVehicleSet]

                                vars_mu = [self.GetIndexUnsatisfiedPatientsVariable(t, j, c, l, w)]
                                coeff_mu = [1.0]

                                vars_mu_Prev = []
                                coeff_mu_Prev = []
                                
                                if t > 0:
                                    vars_mu_Prev = [self.GetIndexUnsatisfiedPatientsVariable(t-1, j, c, l, w)]
                                    coeff_mu_Prev = [-1.0]

                                ############ Create the left-hand side of the constraint
                                LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var[vars_q[i]] for i in range(len(vars_q)))
                                LeftHandSide_mu_Prev = gp.quicksum(coeff_mu_Prev[i] * self.UnsatisfiedPatients_Var[vars_mu_Prev[i]] for i in range(len(vars_mu_Prev))) if vars_mu_Prev else 0
                                LeftHandSide_mu = gp.quicksum(coeff_mu[i] * self.UnsatisfiedPatients_Var[vars_mu[i]] for i in range(len(vars_mu)))
                                LeftHandSide = LeftHandSide_q + LeftHandSide_mu + LeftHandSide_mu_Prev
                                
                                ############ Define the right-hand side (RHS) of the constraint
                                #print(f"Scenarios[w:{w+1}].Demands[t:{t}][j:{j}][c:{c}][l:{l}]:", self.Scenarios[w].Demands[t][j][c][l] )
                                RightHandSide = self.Scenarios[w].Demands[t][j][c][l]  
                                if Constants.Debug: Debug_Average_Demand += RightHandSide
                                ############ Add the constraint to the model
                                constraint_name = f"LowMedPriorityPatientFlow_w_{w}_t_{t}_j_{j}_c_{c}_l_{l}"
                                
                                constraint = self.CRPBIM.addConstr(LeftHandSide == RightHandSide, name=constraint_name)
                                
                                self.LowMedPriorityPatientFlowConstraintNR[w][t][j][c][l] = constraint

                                
                                if Constants.Debug:  
                                    print(f"Vars_q: {vars_q}")
                                    print(f"Coeff_q: {coeff_q}")
                            
                                    print(f"Vars_mu: {vars_mu}")
                                    print(f"Coeff_mu: {coeff_mu}")
                                    
                                    print(f"vars_mu_Prev: {vars_mu_Prev}")
                                    print(f"coeff_mu_Prev: {coeff_mu_Prev}")

                                    print(f"RightHandSide: {RightHandSide}")
                                    
                                    print(f"Added constraint: {constraint_name}")
                                
        if Constants.Debug: print("Debug_Average_Demand_LowMed: ", Debug_Average_Demand)
        if Constants.Debug: print("-------------------")
    
    def CreateHighPriorityPatientFlowConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateHighPriorityPatientFlowConstraint")
        if Constants.Debug: Debug_Average_Demand = 0
        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for j in self.Instance.InjuryLevelSet:
                    if j == 0:                      # Only for High-Priority Patients
                        for c in self.Instance.BloodGPSet:
                            for l in self.Instance.DemandSet:

                                vars_q = [self.GetIndexPatientTransferVariable(t, j, c, l, h, m, w) 
                                          for h in self.Instance.HospitalSet 
                                          if self.Instance.J_u[h][j] == 1
                                          for m in self.Instance.RescueVehicleSet]

                                coeff_q = [1.0  
                                           for h in self.Instance.HospitalSet 
                                           if self.Instance.J_u[h][j] == 1
                                           for m in self.Instance.RescueVehicleSet]

                                vars_mu = [self.GetIndexUnsatisfiedPatientsVariable(t, j, c, l, w)]
                                coeff_mu = [1.0]

                                vars_mu_Prev = []
                                coeff_mu_Prev = []
                                
                                if t > 0:
                                    vars_mu_Prev = [self.GetIndexUnsatisfiedPatientsVariable(t-1, j, c, l, w)]
                                    coeff_mu_Prev = [-1.0]

                                ############ Create the left-hand side of the constraint
                                LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var[vars_q[i]] for i in range(len(vars_q)))
                                LeftHandSide_mu_Prev = gp.quicksum(coeff_mu_Prev[i] * self.UnsatisfiedPatients_Var[vars_mu_Prev[i]] for i in range(len(vars_mu_Prev))) if vars_mu_Prev else 0
                                LeftHandSide_mu = gp.quicksum(coeff_mu[i] * self.UnsatisfiedPatients_Var[vars_mu[i]] for i in range(len(vars_mu)))
                                LeftHandSide = LeftHandSide_q + LeftHandSide_mu + LeftHandSide_mu_Prev
                                
                                ############ Define the right-hand side (RHS) of the constraint
                                #if Constants.Debug: print(f"Scenarios[w:{w+1}].Demands[t:{t}][j:{j}][c:{c}][l:{l}]:", self.Scenarios[w].Demands[t][j][c][l] )
                                RightHandSide = self.Scenarios[w].Demands[t][j][c][l]  
                                if Constants.Debug: Debug_Average_Demand += RightHandSide
                                ############ Add the constraint to the model
                                constraint_name = f"HighPriorityPatientFlow_w_{w}_t_{t}_j_{j}_c_{c}_l_{l}"
                                
                                constraint = self.CRPBIM.addConstr(LeftHandSide == RightHandSide, name=constraint_name)
                                
                                self.HighPriorityPatientFlowConstraintNR[w][t][j][c][l] = constraint

                                '''
                                if Constants.Debug:  
                                    print(f"Vars_q: {vars_q}")
                                    print(f"Coeff_q: {coeff_q}")
                            
                                    print(f"Vars_mu: {vars_mu}")
                                    print(f"Coeff_mu: {coeff_mu}")
                                    
                                    print(f"vars_mu_Prev: {vars_mu_Prev}")
                                    print(f"coeff_mu_Prev: {coeff_mu_Prev}")

                                    print(f"self.Scenarios[w].Demands[t][j][c]: {self.Scenarios[w].Demands[t][j][c]}")
                                    print(f"RightHandSide: {RightHandSide}")
                                    
                                    print(f"Added constraint: {constraint_name}")
                                '''
        if Constants.Debug: print("Debug_Average_Demand_High: ", Debug_Average_Demand)
        print("-------")
    
    def CreateLowMedPriorityPatientServiceConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateLowMedPriorityPatientServiceConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for j in self.Instance.InjuryLevelSet:
                    if j != 0:                      # Only for Low- and Med- Priority Patients
                        for c in self.Instance.BloodGPSet:
                            for u in self.Instance.FacilitySet:
                                

                                vars_upsilon = [self.GetIndexServedPatientVariable(t, j, cprime, c, r, u, w)
                                                for cprime in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime] == 1
                                                for r in self.Instance.PlateletAgeSet if self.Instance.R_j[r][j] == 1]
                                
                                coeff_upsilon = [1.0 
                                                 for cprime in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime]==1 
                                                 for r in self.Instance.PlateletAgeSet if self.Instance.R_j[r][j]==1]

                                vars_zeta = [self.GetIndexPatientPostponementVariable(t, j, c, u, w)]
                                coeff_zeta = [1.0]

                                vars_zeta_Prev = []
                                coeff_zeta_Prev = []
                                
                                if t > 0:
                                    vars_zeta_Prev = [self.GetIndexPatientPostponementVariable(t-1, j, c, u, w)]
                                    coeff_zeta_Prev = [-1.0]

                                vars_q = [self.GetIndexPatientTransferVariable(t, j, c, l, u, m, w)
                                            for m in self.Instance.RescueVehicleSet
                                            for l in self.Instance.DemandSet]
                                
                                coeff_q = [-1.0 
                                            for cprime in self.Instance.RescueVehicleSet 
                                            for r in self.Instance.DemandSet]


                                ############ Create the left-hand side of the constraint
                                LeftHandSide_upsilon = gp.quicksum(coeff_upsilon[i] * self.ServedPatient_Var[vars_upsilon[i]] for i in range(len(vars_upsilon)))
                                
                                LeftHandSide_zeta = gp.quicksum(coeff_zeta[i] * self.PatientPostponement_Var[vars_zeta[i]] for i in range(len(vars_zeta)))

                                LeftHandSide_zeta_Prev = gp.quicksum(coeff_zeta_Prev[i] * self.PatientPostponement_Var[vars_zeta_Prev[i]] for i in range(len(vars_zeta_Prev))) if vars_zeta_Prev else 0
                                
                                LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var[vars_q[i]] for i in range(len(vars_q)))
                                
                                LeftHandSide = LeftHandSide_upsilon + LeftHandSide_zeta + LeftHandSide_zeta_Prev + LeftHandSide_q
                                
                                ############ Define the right-hand side (RHS) of the constraint
                                RightHandSide = 0
                                
                                ############ Add the constraint to the model
                                constraint_name = f"LowMedPriorityPatientService_w_{w}_t_{t}_j_{j}_c_{c}_u_{u}"
                                
                                constraint = self.CRPBIM.addConstr(LeftHandSide == RightHandSide, name=constraint_name)
                                
                                self.LowMedPriorityPatientServiceConstraintNR[w][t][j][c][u] = constraint

                                '''
                                if Constants.Debug:  
                                    print(f"vars_upsilon: {vars_upsilon}")
                                    print(f"coeff_upsilon: {coeff_upsilon}")
                            
                                    print(f"vars_zeta: {vars_zeta}")
                                    print(f"Coeff_zeta: {coeff_zeta}")
                                    
                                    print(f"vars_zeta_Prev: {vars_zeta_Prev}")
                                    print(f"coeff_zeta_Prev: {coeff_zeta_Prev}")
                                    
                                    print(f"vars_q: {vars_q}")
                                    print(f"coeff_q: {coeff_q}")

                                    print(f"RightHandSide: {RightHandSide}")
                                    
                                    print(f"Added constraint: {constraint_name}")
                                '''    

    def CreateHighPriorityPatientServiceConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateHighPriorityPatientServiceConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for j in self.Instance.InjuryLevelSet:
                    if j == 0:                      # Only for High-Priority Patients
                        for c in self.Instance.BloodGPSet:
                            for h in self.Instance.HospitalSet:

                                vars_upsilon = [self.GetIndexServedPatientVariable(t, j, cprime, c, r, h, w)
                                                for cprime in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime] == 1
                                                for r in self.Instance.PlateletAgeSet if self.Instance.R_j[r][j] == 1]
                                
                                coeff_upsilon = [1.0 
                                                 for cprime in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime]==1 
                                                 for r in self.Instance.PlateletAgeSet if self.Instance.R_j[r][j]==1]

                                vars_zeta = [self.GetIndexPatientPostponementVariable(t, j, c, h, w)]
                                coeff_zeta = [1.0]

                                vars_zeta_Prev = []
                                coeff_zeta_Prev = []
                                
                                if t > 0:
                                    vars_zeta_Prev = [self.GetIndexPatientPostponementVariable(t-1, j, c, h, w)]
                                    coeff_zeta_Prev = [-1.0]

                                vars_q = [self.GetIndexPatientTransferVariable(t, j, c, l, h, m, w)
                                            for m in self.Instance.RescueVehicleSet
                                            for l in self.Instance.DemandSet]
                                
                                coeff_q = [-1.0 
                                            for m in self.Instance.RescueVehicleSet 
                                            for l in self.Instance.DemandSet]


                                ############ Create the left-hand side of the constraint
                                LeftHandSide_upsilon = gp.quicksum(coeff_upsilon[i] * self.ServedPatient_Var[vars_upsilon[i]] for i in range(len(vars_upsilon)))
                                
                                LeftHandSide_zeta = gp.quicksum(coeff_zeta[i] * self.PatientPostponement_Var[vars_zeta[i]] for i in range(len(vars_zeta)))

                                LeftHandSide_zeta_Prev = gp.quicksum(coeff_zeta_Prev[i] * self.PatientPostponement_Var[vars_zeta_Prev[i]] for i in range(len(vars_zeta_Prev))) if vars_zeta_Prev else 0
                                
                                LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var[vars_q[i]] for i in range(len(vars_q)))
                                
                                LeftHandSide = LeftHandSide_upsilon + LeftHandSide_zeta + LeftHandSide_zeta_Prev + LeftHandSide_q
                                
                                ############ Define the right-hand side (RHS) of the constraint
                                RightHandSide = 0
                                
                                ############ Add the constraint to the model
                                constraint_name = f"HighPriorityPatientService_w_{w}_t_{t}_j_{j}_c_{c}_h_{h}"
                                
                                constraint = self.CRPBIM.addConstr(LeftHandSide == RightHandSide, name=constraint_name)
                                
                                self.HighPriorityPatientServiceConstraintNR[w][t][j][c][h] = constraint

                                '''
                                if Constants.Debug:  
                                    print(f"vars_upsilon: {vars_upsilon}")
                                    print(f"coeff_upsilon: {coeff_upsilon}")
                            
                                    print(f"vars_zeta: {vars_zeta}")
                                    print(f"Coeff_zeta: {coeff_zeta}")
                                    
                                    print(f"vars_zeta_Prev: {vars_zeta_Prev}")
                                    print(f"coeff_zeta_Prev: {coeff_zeta_Prev}")
                                    
                                    print(f"vars_q: {vars_q}")
                                    print(f"coeff_q: {coeff_q}")

                                    print(f"RightHandSide: {RightHandSide}")
                                    
                                    print(f"Added constraint: {constraint_name}")
                                '''

    def CreateACFTreatmentCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateACFTreatmentCapacityConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for i in self.Instance.ACFPPointSet:
                    
                    vars_q = [self.GetIndexPatientTransferVariable(t, j, c, l, (self.Instance.NrHospitals + i), m, w)
                                for j in self.Instance.InjuryLevelSet if self.Instance.J_u[self.Instance.NrHospitals + i][j] == 1
                                for c in self.Instance.BloodGPSet
                                for l in self.Instance.DemandSet
                                for m in self.Instance.RescueVehicleSet]
                    
                    coeff_q = [-1.0 
                                for j in self.Instance.InjuryLevelSet if self.Instance.J_u[self.Instance.NrHospitals + i][j] == 1
                                for c in self.Instance.BloodGPSet
                                for l in self.Instance.DemandSet
                                for m in self.Instance.RescueVehicleSet]

                    vars_zeta_Prev = []
                    coeff_zeta_Prev = []
                    
                    if t > 0:
                        vars_zeta_Prev = [self.GetIndexPatientPostponementVariable(t-1, j, c, (self.Instance.NrHospitals + i), w)
                                            for j in self.Instance.InjuryLevelSet if self.Instance.J_u[self.Instance.NrHospitals + i][j] == 1
                                            for c in self.Instance.BloodGPSet]                                        
                        coeff_zeta_Prev = [-1.0
                                            for j in self.Instance.InjuryLevelSet if self.Instance.J_u[self.Instance.NrHospitals + i][j] == 1
                                            for c in self.Instance.BloodGPSet]                                              

                    vars_x = [self.GetIndexACFEstablishmentVariable(i, 0)]
                    
                    coeff_x = [self.Instance.ACF_Bed_Capacity[i]]

                    ############ Create the left-hand side of the constraint       
                    LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var[vars_q[i]] for i in range(len(vars_q)))
                    
                    LeftHandSide_zeta_Prev = gp.quicksum(coeff_zeta_Prev[i] * self.PatientPostponement_Var[vars_zeta_Prev[i]] for i in range(len(vars_zeta_Prev))) if vars_zeta_Prev else 0
                    
                    LeftHandSide_x = gp.quicksum(coeff_x[i] * self.ACF_Establishment_Var[vars_x[i]] for i in range(len(vars_x)))
                    
                    LeftHandSide = LeftHandSide_q + LeftHandSide_zeta_Prev + LeftHandSide_x
                    
                    ############ Define the right-hand side (RHS) of the constraint
                    RightHandSide = 0
                    
                    ############ Add the constraint to the model
                    constraint_name = f"ACFTreatmentCapacity_w_{w}_t_{t}_i_{i}"
                    
                    constraint = self.CRPBIM.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                    
                    self.ACFTreatmentCapacityConstraintNR[w][t][i] = constraint

    def CreateHospitalTreatmentCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateHospitalTreatmentCapacityConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for h in self.Instance.HospitalSet:
                    
                    vars_q = [self.GetIndexPatientTransferVariable(t, j, c, l, h, m, w)
                                for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1
                                for c in self.Instance.BloodGPSet
                                for l in self.Instance.DemandSet
                                for m in self.Instance.RescueVehicleSet]
                    
                    coeff_q = [-1.0 
                                for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1
                                for c in self.Instance.BloodGPSet
                                for l in self.Instance.DemandSet
                                for m in self.Instance.RescueVehicleSet]

                    vars_zeta_Prev = []
                    coeff_zeta_Prev = []
                    
                    if t > 0:
                        vars_zeta_Prev = [self.GetIndexPatientPostponementVariable(t-1, j, c, h, w)
                                            for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1
                                            for c in self.Instance.BloodGPSet]                                        
                        coeff_zeta_Prev = [-1.0
                                            for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1
                                            for c in self.Instance.BloodGPSet]                                              

                    
                    ############ Create the left-hand side of the constraint       
                    LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var[vars_q[i]] for i in range(len(vars_q)))
                    
                    LeftHandSide_zeta_Prev = gp.quicksum(coeff_zeta_Prev[i] * self.PatientPostponement_Var[vars_zeta_Prev[i]] for i in range(len(vars_zeta_Prev))) if vars_zeta_Prev else 0
                                        
                    LeftHandSide = LeftHandSide_q + LeftHandSide_zeta_Prev
                    
                    ############ Define the right-hand side (RHS) of the constraint
                    RightHandSide = -1.0 * self.Scenarios[w].HospitalCaps[t][h]  
                    
                    ############ Add the constraint to the model
                    constraint_name = f"HospitalTreatmentCapacity_w_{w}_t_{t}_h_{h}"
                    
                    constraint = self.CRPBIM.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                    
                    self.HospitalTreatmentCapacityConstraintNR[w][t][h] = constraint

    def CreateHospitalPlateletFlowConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateHospitalPlateletFlowConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for cprime in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            
                            vars_lambda = []
                            coeff_lambda = []
                            vars_eta_Prev = []
                            coeff_eta_Prev = []
                            vars_b_DoublePrime = []
                            coeff_b_DoublePrime = []
                            vars_b_DoublePrime_rev = []
                            coeff_b_DoublePrime_rev = []
                            vars_b = []
                            coeff_b = []
                            vars_Rhovar = []
                            coeff_Rhovar = []

                            if r == 0:
                                vars_lambda = [self.GetIndexPlateletApheresisExtractionVariable(t, cprime, h, w)]
                            
                                coeff_lambda = [1.0]

                            if r != 0:

                                if t > 0:

                                    vars_eta_Prev = [self.GetIndexPlateletInventoryVariable(t-1, cprime, r-1, h, w)]
                            
                                    coeff_eta_Prev = [1.0]                              

                                vars_b_DoublePrime = [self.GetIndexTransshipmentHHVariable(t, cprime, r, hprime, h, w) 
                                                        for hprime in self.Instance.HospitalSet if hprime != h]
                            
                                coeff_b_DoublePrime = [1.0  
                                                        for hprime in self.Instance.HospitalSet if hprime != h]
                                
                                vars_b_DoublePrime_rev = [self.GetIndexTransshipmentHHVariable(t, cprime, r, h, hprime, w) 
                                                            for hprime in self.Instance.HospitalSet if hprime != h]
                            
                                coeff_b_DoublePrime_rev = [-1.0  
                                                            for hprime in self.Instance.HospitalSet if hprime != h]
                            
                                vars_b = [self.GetIndexTransshipmentHIVariable(t, cprime, r, h, i, w) 
                                            for i in self.Instance.ACFPPointSet]
                                
                                coeff_b = [-1.0  
                                            for i in self.Instance.ACFPPointSet]
                            
                            if t >= self.Instance.Whole_Blood_Production_Time:
                                if r >= self.Instance.Whole_Blood_Production_Time:

                                    vars_Rhovar = [self.GetIndexPlateletWholeExtractionVariable(t - self.Instance.Whole_Blood_Production_Time, cprime, h, w)]
                            
                                    coeff_Rhovar = [1.0]
                            
                            vars_upsilon = [self.GetIndexServedPatientVariable(t, j, cprime, c, r, h, w) 
                                                for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1 and self.Instance.J_r[j][r] == 1 
                                                for c in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime]==1]
                            
                            coeff_upsilon = [-1.0 * self.Instance.Platelet_Units_Required_for_Injury[j] 
                                                for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1 and self.Instance.J_r[j][r] == 1 
                                                for c in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime]==1]
                            
                            vars_eta = [self.GetIndexPlateletInventoryVariable(t, cprime, r, h, w)]
                    
                            coeff_eta = [-1.0] 

                            ############ Create the left-hand side of the constraint
                            LeftHandSide_lambda = gp.quicksum(coeff_lambda[i] * self.PlateletApheresisExtraction_Var[vars_lambda[i]] for i in range(len(vars_lambda))) if vars_lambda else 0

                            LeftHandSide_eta_Prev = gp.quicksum(coeff_eta_Prev[i] * self.PlateletInventory_Var[vars_eta_Prev[i]] for i in range(len(vars_eta_Prev))) if vars_eta_Prev else 0
                            
                            LeftHandSide_b_DoublePrime = gp.quicksum(coeff_b_DoublePrime[i] * self.TransshipmentHH_Var[vars_b_DoublePrime[i]] for i in range(len(vars_b_DoublePrime))) if vars_b_DoublePrime else 0
                            
                            LeftHandSide_b_DoublePrime_rev = gp.quicksum(coeff_b_DoublePrime_rev[i] * self.TransshipmentHH_Var[vars_b_DoublePrime_rev[i]] for i in range(len(vars_b_DoublePrime_rev))) if vars_b_DoublePrime_rev else 0
                            
                            LeftHandSide_b = gp.quicksum(coeff_b[i] * self.TransshipmentHI_Var[vars_b[i]] for i in range(len(vars_b))) if vars_b else 0
                            
                            LeftHandSide_Rhovar = gp.quicksum(coeff_Rhovar[i] * self.PlateletWholeExtraction_Var[vars_Rhovar[i]] for i in range(len(vars_Rhovar))) if vars_Rhovar else 0
                            
                            LeftHandSide_upsilon = gp.quicksum(coeff_upsilon[i] * self.ServedPatient_Var[vars_upsilon[i]] for i in range(len(vars_upsilon)))
                            
                            LeftHandSide_eta = gp.quicksum(coeff_eta[i] * self.PlateletInventory_Var[vars_eta[i]] for i in range(len(vars_eta)))
                            
                            LeftHandSide = LeftHandSide_lambda + LeftHandSide_eta_Prev + LeftHandSide_b_DoublePrime + LeftHandSide_b_DoublePrime_rev + LeftHandSide_b + LeftHandSide_Rhovar + LeftHandSide_upsilon + LeftHandSide_eta
                            
                            ############ Define the right-hand side (RHS) of the constraint
                            if t == 0:
                                RightHandSide =  -1.0 * self.Instance.Initial_Platelet_Inventory[cprime][r][h]
                            else:
                                RightHandSide = 0 
                            
                            ############ Add the constraint to the model
                            constraint_name = f"HospitalPlateletFlow_w_{w}_t_{t}_c'_{cprime}_r_{r}_h_{h}"
                            
                            constraint = self.CRPBIM.addConstr(LeftHandSide == RightHandSide, name=constraint_name)
                            
                            self.HospitalPlateletFlowConstraintNR[w][t][cprime][r][h] = constraint

    def CreateACFPlateletFlowConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateACFPlateletFlowConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for cprime in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for i in self.Instance.ACFPPointSet:
                            
                            vars_lambda = []
                            coeff_lambda = []
                            vars_eta_Prev = []
                            coeff_eta_Prev = []
                            vars_b = []
                            coeff_b = []                            
                            vars_b_Prime = []
                            coeff_b_Prime = []
                            vars_b_Prime_rev = []
                            coeff_b_Prime_rev = []

                            if r == 0:
                                vars_lambda = [self.GetIndexPlateletApheresisExtractionVariable(t, cprime, self.Instance.NrHospitals + i, w)]
                            
                                coeff_lambda = [1.0]


                            if r != 0:

                                if t > 0:

                                    vars_eta_Prev = [self.GetIndexPlateletInventoryVariable(t-1, cprime, r-1, self.Instance.NrHospitals + i, w)]
                            
                                    coeff_eta_Prev = [1.0]                              

                                vars_b = [self.GetIndexTransshipmentHIVariable(t, cprime, r, h, i, w) 
                                            for h in self.Instance.HospitalSet]
                                
                                coeff_b = [1.0  
                                            for h in self.Instance.HospitalSet]
                                
                                vars_b_Prime = [self.GetIndexTransshipmentIIVariable(t, cprime, r, iprime, i, w) 
                                                    for iprime in self.Instance.ACFPPointSet if iprime != i]
                            
                                coeff_b_Prime = [1.0  
                                                    for iprime in self.Instance.ACFPPointSet if iprime != i]
                                
                                vars_b_Prime_rev = [self.GetIndexTransshipmentIIVariable(t, cprime, r, i, iprime, w) 
                                                        for iprime in self.Instance.ACFPPointSet if iprime != i]
                            
                                coeff_b_Prime_rev = [-1.0  
                                                        for iprime in self.Instance.ACFPPointSet if iprime != i]
                            
                            vars_upsilon = [self.GetIndexServedPatientVariable(t, j, cprime, c, r, self.Instance.NrHospitals + i, w) 
                                                for j in self.Instance.InjuryLevelSet if self.Instance.J_u[self.Instance.NrHospitals + i][j] == 1 and self.Instance.J_r[j][r] == 1 
                                                for c in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime]==1]
                            
                            coeff_upsilon = [-1.0 * self.Instance.Platelet_Units_Required_for_Injury[j] 
                                                for j in self.Instance.InjuryLevelSet if self.Instance.J_u[self.Instance.NrHospitals + i][j] == 1 and self.Instance.J_r[j][r] == 1 
                                                for c in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime]==1]
                            
                            vars_eta = [self.GetIndexPlateletInventoryVariable(t, cprime, r, self.Instance.NrHospitals + i, w)]
                    
                            coeff_eta = [-1.0] 
                            
                            
                            ############ Create the left-hand side of the constraint                            
                            LeftHandSide_lambda = gp.quicksum(coeff_lambda[i] * self.PlateletApheresisExtraction_Var[vars_lambda[i]] for i in range(len(vars_lambda))) if vars_lambda else 0

                            LeftHandSide_eta_Prev = gp.quicksum(coeff_eta_Prev[i] * self.PlateletInventory_Var[vars_eta_Prev[i]] for i in range(len(vars_eta_Prev))) if vars_eta_Prev else 0
                            
                            LeftHandSide_b = gp.quicksum(coeff_b[i] * self.TransshipmentHI_Var[vars_b[i]] for i in range(len(vars_b))) if vars_b else 0

                            LeftHandSide_b_Prime = gp.quicksum(coeff_b_Prime[i] * self.TransshipmentII_Var[vars_b_Prime[i]] for i in range(len(vars_b_Prime))) if vars_b_Prime else 0
                            
                            LeftHandSide_b_Prime_rev = gp.quicksum(coeff_b_Prime_rev[i] * self.TransshipmentII_Var[vars_b_Prime_rev[i]] for i in range(len(vars_b_Prime_rev))) if vars_b_Prime_rev else 0
                                                                                    
                            LeftHandSide_upsilon = gp.quicksum(coeff_upsilon[i] * self.ServedPatient_Var[vars_upsilon[i]] for i in range(len(vars_upsilon)))
                            
                            LeftHandSide_eta = gp.quicksum(coeff_eta[i] * self.PlateletInventory_Var[vars_eta[i]] for i in range(len(vars_eta)))
                            
                            LeftHandSide = LeftHandSide_lambda + LeftHandSide_eta_Prev + LeftHandSide_b + LeftHandSide_b_Prime + LeftHandSide_b_Prime_rev + LeftHandSide_upsilon + LeftHandSide_eta
                            
                            ############ Define the right-hand side (RHS) of the constraint
                            
                            RightHandSide = 0 

                            ############ Add the constraint to the model
                            constraint_name = f"ACFPlateletFlow_w_{w}_t_{t}_c'_{cprime}_r_{r}_i_{i}"
                            
                            constraint = self.CRPBIM.addConstr(LeftHandSide == RightHandSide, name=constraint_name)
                            
                            self.ACFPlateletFlowConstraintNR[w][t][cprime][r][i] = constraint

    def CreatePlateletWastageConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreatePlateletWastageConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for u in self.Instance.FacilitySet:
                    
                    vars_sigmavar = [self.GetIndexOutdatedPlateletVariable(t, u, w)]
                    
                    coeff_sigmavar = [1.0]

                    r_last = list(self.Instance.PlateletAgeSet)[-1]
                    vars_eta = [self.GetIndexPlateletInventoryVariable(t, c, r_last, u, w)
                                    for c in self.Instance.BloodGPSet]
                    coeff_eta = [-1.0
                                    for c in self.Instance.BloodGPSet]                                              

                    
                    ############ Create the left-hand side of the constraint       
                    LeftHandSide_sigmavar = gp.quicksum(coeff_sigmavar[i] * self.OutdatedPlatelet_Var[vars_sigmavar[i]] for i in range(len(vars_sigmavar)))
                    
                    LeftHandSide_eta = gp.quicksum(coeff_eta[i] * self.PlateletInventory_Var[vars_eta[i]] for i in range(len(vars_eta)))
                                        
                    LeftHandSide = LeftHandSide_sigmavar + LeftHandSide_eta
                    
                    ############ Define the right-hand side (RHS) of the constraint
                    RightHandSide = 0 
                    
                    ############ Add the constraint to the model
                    constraint_name = f"PlateletWastage_w_{w}_t_{t}_u_{u}"
                    
                    constraint = self.CRPBIM.addConstr(LeftHandSide == RightHandSide, name=constraint_name)
                    
                    self.PlateletWastageConstraintNR[w][t][u] = constraint

    def CreateHospitalRescueVehicleCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateHospitalRescueVehicleCapacityConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for h in self.Instance.HospitalSet:
                    for m in self.Instance.RescueVehicleSet:
                        
                        vars_q = [self.GetIndexPatientTransferVariable(t, j, c, l, h, m, w)
                                    for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1
                                    for c in self.Instance.BloodGPSet
                                    for l in self.Instance.DemandSet]
                        
                        coeff_q = [-1.0 * self.Instance.Distance_D_H[l][h] 
                                    for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1
                                    for c in self.Instance.BloodGPSet
                                    for l in self.Instance.DemandSet]                                             

                        
                        ############ Create the left-hand side of the constraint       
                        LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var[vars_q[i]] for i in range(len(vars_q)))
                                                                    
                        LeftHandSide = LeftHandSide_q
                        
                        ############ Define the right-hand side (RHS) of the constraint
                        RightHandSide = -1.0 * self.Instance.Rescue_Vehicle_Capacity[m] * self.Instance.Number_Rescue_Vehicle_Hospital[m][h]  
                        
                        ############ Add the constraint to the model
                        constraint_name = f"HospitalRescueVehicleCapacity_w_{w}_t_{t}_h_{h}_m_{m}"
                        
                        constraint = self.CRPBIM.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                        
                        self.HospitalRescueVehicleCapacityConstraintNR[w][t][h][m] = constraint

    def CreateACFRescueVehicleCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateACFRescueVehicleCapacityConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for i in self.Instance.ACFPPointSet:
                    for m in self.Instance.RescueVehicleSet:
                        
                        vars_q = [self.GetIndexPatientTransferVariable(t, j, c, l, self.Instance.NrHospitals + i, m, w)
                                    for j in self.Instance.InjuryLevelSet if self.Instance.J_u[self.Instance.NrHospitals + i][j] == 1
                                    for c in self.Instance.BloodGPSet
                                    for l in self.Instance.DemandSet]
                        
                        coeff_q = [-1.0 * self.Instance.Distance_D_A[l][i] 
                                    for j in self.Instance.InjuryLevelSet if self.Instance.J_u[self.Instance.NrHospitals + i][j] == 1
                                    for c in self.Instance.BloodGPSet
                                    for l in self.Instance.DemandSet]                                             
                        
                        vars_thetavar = [self.GetIndexVehicleAssignmentVariable(m, i, 0)]
                        
                        coeff_thetavar = [self.Instance.Rescue_Vehicle_Capacity[m]]                                             

                        
                        ############ Create the left-hand side of the constraint       
                        LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var[vars_q[i]] for i in range(len(vars_q)))
                        
                        LeftHandSide_thetavar = gp.quicksum(coeff_thetavar[i] * self.Vehicle_Assignment_Var[vars_thetavar[i]] for i in range(len(vars_thetavar)))
                                                                    
                        LeftHandSide = LeftHandSide_q + LeftHandSide_thetavar
                        
                        ############ Define the right-hand side (RHS) of the constraint
                        RightHandSide = 0  
                        
                        ############ Add the constraint to the model
                        constraint_name = f"ACFRescueVehicleCapacity_w_{w}_t_{t}_i_{i}_m_{m}"
                        
                        constraint = self.CRPBIM.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                        
                        self.ACFRescueVehicleCapacityConstraintNR[w][t][i][m] = constraint
    
    def CreateNrApheresisLimitConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateNrApheresisLimitConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                        
                vars_y = [self.GetIndexApheresisAssignmentVariable(t, i, w)
                            for i in self.Instance.ACFPPointSet]
                
                coeff_y = [-1.0
                            for i in self.Instance.ACFPPointSet]                                                                                      

                ############ Create the left-hand side of the constraint       
                LeftHandSide_y = gp.quicksum(coeff_y[i] * self.ApheresisAssignment_Var[vars_y[i]] for i in range(len(vars_y)))
                                                                            
                LeftHandSide = LeftHandSide_y
                
                ############ Define the right-hand side (RHS) of the constraint
                RightHandSide = -1.0 * self.Instance.Total_Apheresis_Machine_ACF[t]  
                
                ############ Add the constraint to the model
                constraint_name = f"NrApheresisLimit_w_{w}_t_{t}"
                
                constraint = self.CRPBIM.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                
                self.NrApheresisLimitConstraintNR[w][t] = constraint
    
    def CreateApheresisACFConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateApheresisACFConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for i in self.Instance.ACFPPointSet:
                        
                    vars_y = [self.GetIndexApheresisAssignmentVariable(t, i, w)]
                    
                    coeff_y = [-1.0]                                                                                      
                    
                    vars_x = [self.GetIndexACFEstablishmentVariable(i, 0)]
                    
                    coeff_x = [self.Instance.Total_Apheresis_Machine_ACF[t]]                                                                                      

                    ############ Create the left-hand side of the constraint       
                    LeftHandSide_y = gp.quicksum(coeff_y[i] * self.ApheresisAssignment_Var[vars_y[i]] for i in range(len(vars_y)))
                    LeftHandSide_x = gp.quicksum(coeff_x[i] * self.ACF_Establishment_Var[vars_x[i]] for i in range(len(vars_x)))
                                                                                
                    LeftHandSide = LeftHandSide_y + LeftHandSide_x
                    
                    ############ Define the right-hand side (RHS) of the constraint
                    RightHandSide = 0 
                    
                    ############ Add the constraint to the model
                    constraint_name = f"ApheresisACF_w_{w}_t_{t}_i_{i}"
                    
                    constraint = self.CRPBIM.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                    
                    self.ApheresisACFConstraintNR[w][t][i] = constraint
    
    def CreateACFApheresisCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateACFApheresisCapacityConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for i in self.Instance.ACFPPointSet:
                        
                    vars_lambda = [self.GetIndexPlateletApheresisExtractionVariable(t, c, self.Instance.NrHospitals + i, w)
                                   for c in self.Instance.BloodGPSet]
                    
                    coeff_lambda = [-1.0
                                    for c in self.Instance.BloodGPSet] 

                    vars_y = [self.GetIndexApheresisAssignmentVariable(t, i, w)]
                    
                    coeff_y = [self.Instance.Apheresis_Machine_Production_Capacity]                                                                                      
                                                                                                     

                    ############ Create the left-hand side of the constraint       
                    LeftHandSide_lambda = gp.quicksum(coeff_lambda[i] * self.PlateletApheresisExtraction_Var[vars_lambda[i]] for i in range(len(vars_lambda)))

                    LeftHandSide_y = gp.quicksum(coeff_y[i] * self.ApheresisAssignment_Var[vars_y[i]] for i in range(len(vars_y)))
                                                                                
                    LeftHandSide = LeftHandSide_lambda + LeftHandSide_y
                    
                    ############ Define the right-hand side (RHS) of the constraint
                    RightHandSide = 0 
                    
                    ############ Add the constraint to the model
                    constraint_name = f"ACFApheresisCapacity_w_{w}_t_{t}_i_{i}"
                    
                    constraint = self.CRPBIM.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                    
                    self.ACFApheresisCapacityConstraintNR[w][t][i] = constraint
    
    def CreateHospitalApheresisCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateHospitalApheresisCapacityConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for h in self.Instance.HospitalSet:
                        
                    vars_lambda = [self.GetIndexPlateletApheresisExtractionVariable(t, c, h, w)
                                   for c in self.Instance.BloodGPSet]
                    
                    coeff_lambda = [-1.0
                                    for c in self.Instance.BloodGPSet]                                                                                                   

                    ############ Create the left-hand side of the constraint       
                    LeftHandSide_lambda = gp.quicksum(coeff_lambda[i] * self.PlateletApheresisExtraction_Var[vars_lambda[i]] for i in range(len(vars_lambda)))
                                                                                
                    LeftHandSide = LeftHandSide_lambda
                    
                    ############ Define the right-hand side (RHS) of the constraint
                    RightHandSide = -1.0 * self.Instance.Apheresis_Machine_Production_Capacity * self.Instance.Number_Apheresis_Machine_Hospital[h]
                    
                    ############ Add the constraint to the model
                    constraint_name = f"HospitalApheresisCapacity_w_{w}_t_{t}_h_{h}"
                    
                    constraint = self.CRPBIM.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                    
                    self.HospitalApheresisCapacityConstraintNR[w][t][h] = constraint
    
    def CreateApheresisCapacityDonorsConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateApheresisCapacityDonorsConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for u in self.Instance.FacilitySet:
                        
                        vars_lambda = [self.GetIndexPlateletApheresisExtractionVariable(t, c, u, w)]
                        
                        coeff_lambda = [-1.0]                                                                                                   

                        ############ Create the left-hand side of the constraint       
                        LeftHandSide_lambda = gp.quicksum(coeff_lambda[i] * self.PlateletApheresisExtraction_Var[vars_lambda[i]] for i in range(len(vars_lambda)))
                                                                                    
                        LeftHandSide = LeftHandSide_lambda
                        
                        ############ Define the right-hand side (RHS) of the constraint
                        RightHandSide = -1.0 * self.Instance.Platelet_Units_Apheresis * self.Scenarios[w].ApheresisDonors[t][c][u]
                        
                        ############ Add the constraint to the model
                        constraint_name = f"ApheresisCapacityDonors_w_{w}_t_{t}_c_{c}_u_{u}"
                        
                        constraint = self.CRPBIM.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                        
                        self.ApheresisCapacityDonorsConstraintNR[w][t][c][u] = constraint
    
    def CreateWholeCapacityDonorsConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateWholeCapacityDonorsConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for h in self.Instance.HospitalSet:
                        
                        vars_Rhovar = [self.GetIndexPlateletWholeExtractionVariable(t, c, h, w)]
                        
                        coeff_Rhovar = [-1.0]                                                                                                   

                        ############ Create the left-hand side of the constraint       
                        LeftHandSide_Rhovar = gp.quicksum(coeff_Rhovar[i] * self.PlateletWholeExtraction_Var[vars_Rhovar[i]] for i in range(len(vars_Rhovar)))
                                                                                    
                        LeftHandSide = LeftHandSide_Rhovar
                        
                        ############ Define the right-hand side (RHS) of the constraint
                        RightHandSide = -1.0 * self.Scenarios[w].WholeDonors[t][c][h]
                        
                        ############ Add the constraint to the model
                        constraint_name = f"WholeCapacityDonors_w_{w}_t_{t}_c_{c}_h_{h}"
                        
                        constraint = self.CRPBIM.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                        
                        self.WholeCapacityDonorsConstraintNR[w][t][c][h] = constraint

    def CreateHospitalTransshipmentCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateHospitalTransshipmentCapacityConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                                
                            vars_b = [self.GetIndexTransshipmentHIVariable(t, c, r, h, i, w)
                                        for i in self.Instance.ACFPPointSet]
                            coeff_b = [-1.0 
                                        for i in self.Instance.ACFPPointSet]                                             
                            
                            vars_b_DoublePrime = [self.GetIndexTransshipmentHHVariable(t, c, r, h, hprime, w)
                                                    for hprime in self.Instance.HospitalSet if hprime != h]
                            coeff_b_DoublePrime = [-1.0 
                                                    for hprime in self.Instance.HospitalSet if hprime != h]                                             

                            vars_eta_Prev = []
                            coeff_eta_Prev = []

                            if r != 0:
                                if t > 0:

                                    vars_eta_Prev = [self.GetIndexPlateletInventoryVariable(t-1, c, r-1, h, w)]
                            
                                    coeff_eta_Prev = [1.0] 

                            ############ Create the left-hand side of the constraint       
                            LeftHandSide_b = gp.quicksum(coeff_b[i] * self.TransshipmentHI_Var[vars_b[i]] for i in range(len(vars_b)))
                            
                            LeftHandSide_b_DoublePrime = gp.quicksum(coeff_b_DoublePrime[i] * self.TransshipmentHH_Var[vars_b_DoublePrime[i]] for i in range(len(vars_b_DoublePrime)))
                            
                            LeftHandSide_eta_Prev = gp.quicksum(coeff_eta_Prev[i] * self.PlateletInventory_Var[vars_eta_Prev[i]] for i in range(len(vars_eta_Prev))) if vars_eta_Prev else 0
                                                                        
                            LeftHandSide = LeftHandSide_b + LeftHandSide_b_DoublePrime + LeftHandSide_eta_Prev
                            
                            ############ Define the right-hand side (RHS) of the constraint
                            if r == 0:
                                RightHandSide = 0  
                            else:
                                if t == 0:
                                    RightHandSide = -1.0 * self.Instance.Initial_Platelet_Inventory[c][r][h]
                                else:
                                    RightHandSide = 0

                            
                            ############ Add the constraint to the model
                            constraint_name = f"HospitalTransshipmentCapacity_w_{w}_t_{t}_c_{c}_r_{r}_h_{h}"
                            
                            constraint = self.CRPBIM.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                            
                            self.HospitalTransshipmentCapacityConstraintNR[w][t][c][r][h] = constraint
    
    def CreateACFTransshipmentCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateACFTransshipmentCapacityConstraint")

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for i in self.Instance.ACFPPointSet:
                                
                            vars_bprime = [self.GetIndexTransshipmentIIVariable(t, c, r, i, iprime, w)
                                                for iprime in self.Instance.ACFPPointSet if iprime != i]
                            coeff_bprime = [-1.0 
                                                for iprime in self.Instance.ACFPPointSet if iprime != i]                                             
                                                                   
                            vars_eta_Prev = []
                            coeff_eta_Prev = []
                            if r != 0:
                                if t > 0:
                                    vars_eta_Prev = [self.GetIndexPlateletInventoryVariable(t-1, c, r-1, self.Instance.NrHospitals + i, w)]
                                    coeff_eta_Prev = [1.0] 

                            ############ Create the left-hand side of the constraint       
                            LeftHandSide_bprime = gp.quicksum(coeff_bprime[i] * self.TransshipmentII_Var[vars_bprime[i]] for i in range(len(vars_bprime)))
                            LeftHandSide_eta_Prev = gp.quicksum(coeff_eta_Prev[i] * self.PlateletInventory_Var[vars_eta_Prev[i]] for i in range(len(vars_eta_Prev))) if vars_eta_Prev else 0
                                                                        
                            LeftHandSide = LeftHandSide_bprime + LeftHandSide_eta_Prev
                            
                            ############ Define the right-hand side (RHS) of the constraint
                            RightHandSide = 0
                            
                            ############ Add the constraint to the model
                            constraint_name = f"ACFTransshipmentCapacity_w_{w}_t_{t}_c_{c}_r_{r}_i_{i}"
                            
                            constraint = self.CRPBIM.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                            
                            self.ACFTransshipmentCapacityConstraintNR[w][t][c][r][i] = constraint
    
    # This function creates the non anticipitativity constraint
    def CreateNonanticipativityConstraints_y(self): 
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateNonanticipativityConstraints_y")

        AlreadyAdded = [[False for _ in range(self.NrApheresisAssignmentVariables)] for _ in range(self.NrApheresisAssignmentVariables)]
        considertimebucket = self.Instance.TimeBucketSet

        for w1 in self.ScenarioSet:
            for w2 in range(w1 + 1, self.NrScenario):
                for i in self.Instance.ACFPPointSet:                
                    for t in considertimebucket:
                        Index_x1 = self.GetIndexApheresisAssignmentVariable(t, i, w1) - self.GetStartApheresisAssignmentVariable()
                        Index_x2 = self.GetIndexApheresisAssignmentVariable(t, i, w2) - self.GetStartApheresisAssignmentVariable()

                        if self.Scenarios[w1].ApheresisAssignmentVariable[t][i] == self.Scenarios[w2].ApheresisAssignmentVariable[t][i] and not AlreadyAdded[Index_x1][Index_x2]:
                            
                            AlreadyAdded[Index_x1][Index_x2] = True
                            AlreadyAdded[Index_x2][Index_x1] = True

                            vars_y1 = self.GetIndexApheresisAssignmentVariable(t, i, w1)
                            vars_y2 = self.GetIndexApheresisAssignmentVariable(t, i, w2)

                            # Retrieving variable values
                            var_value_y1 = self.ApheresisAssignment_Var[vars_y1]
                            var_value_y2 = self.ApheresisAssignment_Var[vars_y2]
                            
                            coeff_y1 = 1.0
                            coeff_y2 = -1.0

                            # Calculating left hand side components
                            LeftHandSide_y1 = coeff_y1 * var_value_y1
                            LeftHandSide_y2 = coeff_y2 * var_value_y2
                            LeftHandSide = LeftHandSide_y1 + LeftHandSide_y2
                            

                            RightHandSide = 0.0

                            # Adding the constraint
                            constraint_name = f"Nonanticipativity_y_w1_{w1}_w2_{w2}_t_{t}_i_{i}"
                            self.CRPBIM.addConstr(LeftHandSide == RightHandSide, name=constraint_name)

                            #if Constants.Debug: 
                                #print(f"Added constraint: {constraint_name}")

    # This function creates the non anticipitativity constraint
    def CreateNonanticipativityConstraints_q(self): 
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateNonanticipativityConstraints_q")

        AlreadyAdded = [[False for _ in range(self.NrPatientTransferVariables)] for _ in range(self.NrPatientTransferVariables)]
        considertimebucket = self.Instance.TimeBucketSet

        for w1 in self.ScenarioSet:
            for w2 in range(w1 + 1, self.NrScenario):
                for t in considertimebucket:
                    for j in self.Instance.InjuryLevelSet:
                        for c in self.Instance.BloodGPSet:
                            for l in self.Instance.DemandSet:
                                for u in self.Instance.FacilitySet:
                                    for m in self.Instance.RescueVehicleSet:
                                    
                                        Index_x1 = self.GetIndexPatientTransferVariable(t, j, c, l, u, m, w1) - self.GetStartPatientTransferVariables()
                                        Index_x2 = self.GetIndexPatientTransferVariable(t, j, c, l, u, m, w2) - self.GetStartPatientTransferVariables()

                                        if self.Scenarios[w1].PatientTransferVariable[t][j][c][l][u][m] == self.Scenarios[w2].PatientTransferVariable[t][j][c][l][u][m] and not AlreadyAdded[Index_x1][Index_x2]:
                                            
                                            AlreadyAdded[Index_x1][Index_x2] = True
                                            AlreadyAdded[Index_x2][Index_x1] = True

                                            vars_q1 = self.GetIndexPatientTransferVariable(t, j, c, l, u, m, w1)
                                            vars_q2 = self.GetIndexPatientTransferVariable(t, j, c, l, u, m, w2)

                                            # Retrieving variable values
                                            var_value_q1 = self.PatientTransfer_Var[vars_q1]
                                            var_value_q2 = self.PatientTransfer_Var[vars_q2]
                                            
                                            coeff_q1 = 1.0
                                            coeff_q2 = -1.0

                                            # Calculating left hand side components
                                            LeftHandSide_q1 = coeff_q1 * var_value_q1
                                            LeftHandSide_q2 = coeff_q2 * var_value_q2
                                            LeftHandSide = LeftHandSide_q1 + LeftHandSide_q2
                                            

                                            RightHandSide = 0.0

                                            # Adding the constraint
                                            constraint_name = f"Nonanticipativity_q_w1_{w1}_w2_{w2}_t_{t}_j_{j}_c_{c}_l_{l}_u_{u}_m_{m}"
                                            self.CRPBIM.addConstr(LeftHandSide == RightHandSide, name=constraint_name)

                                            #if Constants.Debug: 
                                                #print(f"Added constraint: {constraint_name}")
    
    # This function creates the non anticipitativity constraint
    def CreateNonanticipativityConstraints_b(self): 
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateNonanticipativityConstraints_b")

        AlreadyAdded = [[False for _ in range(self.NrTransshipmentHIVariables)] for _ in range(self.NrTransshipmentHIVariables)]
        considertimebucket = self.Instance.TimeBucketSet

        for w1 in self.ScenarioSet:
            for w2 in range(w1 + 1, self.NrScenario):
                for t in considertimebucket:
                    for c in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for h in self.Instance.HospitalSet:
                                for i in self.Instance.ACFPPointSet:
                                
                                    Index_x1 = self.GetIndexTransshipmentHIVariable(t, c, r, h, i, w1) - self.GetStartTransshipmentHIVariable()
                                    Index_x2 = self.GetIndexTransshipmentHIVariable(t, c, r, h, i, w2) - self.GetStartTransshipmentHIVariable()

                                    if self.Scenarios[w1].TransshipmentHIVariable[t][c][r][h][i] == self.Scenarios[w2].TransshipmentHIVariable[t][c][r][h][i] and not AlreadyAdded[Index_x1][Index_x2]:
                                        
                                        AlreadyAdded[Index_x1][Index_x2] = True
                                        AlreadyAdded[Index_x2][Index_x1] = True

                                        vars_b1 = self.GetIndexTransshipmentHIVariable(t, c, r, h, i, w1)
                                        vars_b2 = self.GetIndexTransshipmentHIVariable(t, c, r, h, i, w2)

                                        # Retrieving variable values
                                        var_value_b1 = self.TransshipmentHI_Var[vars_b1]
                                        var_value_b2 = self.TransshipmentHI_Var[vars_b2]
                                        
                                        coeff_b1 = 1.0
                                        coeff_b2 = -1.0

                                        # Calculating left hand side components
                                        LeftHandSide_b1 = coeff_b1 * var_value_b1
                                        LeftHandSide_b2 = coeff_b2 * var_value_b2
                                        LeftHandSide = LeftHandSide_b1 + LeftHandSide_b2
                                        

                                        RightHandSide = 0.0

                                        # Adding the constraint
                                        constraint_name = f"Nonanticipativity_b_w1_{w1}_w2_{w2}_t_{t}_c_{c}_r_{r}_h_{h}_i_{i}"
                                        self.CRPBIM.addConstr(LeftHandSide == RightHandSide, name=constraint_name)

                                        #if Constants.Debug: 
                                            #print(f"Added constraint: {constraint_name}")

    # This function creates the non anticipitativity constraint
    def CreateNonanticipativityConstraints_bPrime(self): 
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateNonanticipativityConstraints_bPrime")

        AlreadyAdded = [[False for _ in range(self.NrTransshipmentIIVariables)] for _ in range(self.NrTransshipmentIIVariables)]
        considertimebucket = self.Instance.TimeBucketSet

        for w1 in self.ScenarioSet:
            for w2 in range(w1 + 1, self.NrScenario):
                for t in considertimebucket:
                    for c in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for i in self.Instance.ACFPPointSet:
                                for iprime in self.Instance.ACFPPointSet:
                                
                                    Index_x1 = self.GetIndexTransshipmentIIVariable(t, c, r, i, iprime, w1) - self.GetStartTransshipmentIIVariable()
                                    Index_x2 = self.GetIndexTransshipmentIIVariable(t, c, r, i, iprime, w2) - self.GetStartTransshipmentIIVariable()

                                    if self.Scenarios[w1].TransshipmentIIVariable[t][c][r][i][iprime] == self.Scenarios[w2].TransshipmentIIVariable[t][c][r][i][iprime] and not AlreadyAdded[Index_x1][Index_x2]:
                                        
                                        AlreadyAdded[Index_x1][Index_x2] = True
                                        AlreadyAdded[Index_x2][Index_x1] = True

                                        vars_bPrime1 = self.GetIndexTransshipmentIIVariable(t, c, r, i, iprime, w1)
                                        vars_bPrime2 = self.GetIndexTransshipmentIIVariable(t, c, r, i, iprime, w2)

                                        # Retrieving variable values
                                        var_value_bPrime1 = self.TransshipmentII_Var[vars_bPrime1]
                                        var_value_bPrime2 = self.TransshipmentII_Var[vars_bPrime2]
                                        
                                        coeff_bPrime1 = 1.0
                                        coeff_bPrime2 = -1.0

                                        # Calculating left hand side components
                                        LeftHandSide_bPrime1 = coeff_bPrime1 * var_value_bPrime1
                                        LeftHandSide_bPrime2 = coeff_bPrime2 * var_value_bPrime2
                                        LeftHandSide = LeftHandSide_bPrime1 + LeftHandSide_bPrime2
                                        

                                        RightHandSide = 0.0

                                        # Adding the constraint
                                        constraint_name = f"Nonanticipativity_bPrime_w1_{w1}_w2_{w2}_t_{t}_c_{c}_r_{r}_i_{i}_iprime_{iprime}"
                                        self.CRPBIM.addConstr(LeftHandSide == RightHandSide, name=constraint_name)

                                        #if Constants.Debug: 
                                            #print(f"Added constraint: {constraint_name}")

    # This function creates the non anticipitativity constraint
    def CreateNonanticipativityConstraints_bDoublePrime(self): 
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateNonanticipativityConstraints_bDoublePrime")

        AlreadyAdded = [[False for _ in range(self.NrTransshipmentHHVariables)] for _ in range(self.NrTransshipmentHHVariables)]
        considertimebucket = self.Instance.TimeBucketSet

        for w1 in self.ScenarioSet:
            for w2 in range(w1 + 1, self.NrScenario):
                for t in considertimebucket:
                    for c in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for h in self.Instance.HospitalSet:
                                for hprime in self.Instance.HospitalSet:
                                
                                    Index_x1 = self.GetIndexTransshipmentHHVariable(t, c, r, h, hprime, w1) - self.GetStartTransshipmentHHVariable()
                                    Index_x2 = self.GetIndexTransshipmentHHVariable(t, c, r, h, hprime, w2) - self.GetStartTransshipmentHHVariable()

                                    if self.Scenarios[w1].TransshipmentHHVariable[t][c][r][h][hprime] == self.Scenarios[w2].TransshipmentHHVariable[t][c][r][h][hprime] and not AlreadyAdded[Index_x1][Index_x2]:
                                        
                                        AlreadyAdded[Index_x1][Index_x2] = True
                                        AlreadyAdded[Index_x2][Index_x1] = True

                                        vars_bDoublePrime1 = self.GetIndexTransshipmentHHVariable(t, c, r, h, hprime, w1)
                                        vars_bDoublePrime2 = self.GetIndexTransshipmentHHVariable(t, c, r, h, hprime, w2)

                                        # Retrieving variable values
                                        var_value_bDoublePrime1 = self.TransshipmentHH_Var[vars_bDoublePrime1]
                                        var_value_bDoublePrime2 = self.TransshipmentHH_Var[vars_bDoublePrime2]
                                        
                                        coeff_bDoublePrime1 = 1.0
                                        coeff_bDoublePrime2 = -1.0

                                        # Calculating left hand side components
                                        LeftHandSide_bDoublePrime1 = coeff_bDoublePrime1 * var_value_bDoublePrime1
                                        LeftHandSide_bDoublePrime2 = coeff_bDoublePrime2 * var_value_bDoublePrime2
                                        LeftHandSide = LeftHandSide_bDoublePrime1 + LeftHandSide_bDoublePrime2
                                        

                                        RightHandSide = 0.0

                                        # Adding the constraint
                                        constraint_name = f"Nonanticipativity_bDoublePrime_w1_{w1}_w2_{w2}_t_{t}_c_{c}_r_{r}_h_{h}_hprime_{hprime}"
                                        self.CRPBIM.addConstr(LeftHandSide == RightHandSide, name=constraint_name)

                                        #if Constants.Debug: 
                                            #print(f"Added constraint: {constraint_name}")

    # This function creates the non anticipitativity constraint
    def CreateNonanticipativityConstraints_lambda(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateNonanticipativityConstraints_lambda")

        AlreadyAdded = [[False for _ in range(self.NrPlateletApheresisExtractionVariables)] for _ in range(self.NrPlateletApheresisExtractionVariables)]
        considertimebucket = self.Instance.TimeBucketSet

        for w1 in self.ScenarioSet:
            for w2 in range(w1 + 1, self.NrScenario):
                for t in considertimebucket:
                    for c in self.Instance.BloodGPSet:
                        for u in self.Instance.FacilitySet:  

                            Index_lambda1 = self.GetIndexPlateletApheresisExtractionVariable(t, c, u, w1) - self.GetStartPlateletApheresisExtractionVariables()
                            Index_lambda2 = self.GetIndexPlateletApheresisExtractionVariable(t, c, u, w2) - self.GetStartPlateletApheresisExtractionVariables()

                            if self.Scenarios[w1].PlateletApheresisExtractionVariable[t][c][u] == self.Scenarios[w2].PlateletApheresisExtractionVariable[t][c][u] and not AlreadyAdded[Index_lambda1][Index_lambda2]:
                                
                                AlreadyAdded[Index_lambda1][Index_lambda2] = True
                                AlreadyAdded[Index_lambda2][Index_lambda1] = True

                                vars_lambda1 = self.GetIndexPlateletApheresisExtractionVariable(t, c, u, w1)
                                vars_lambda2 = self.GetIndexPlateletApheresisExtractionVariable(t, c, u, w2)

                                # Retrieving variable values
                                var_value_lambda1 = self.PlateletApheresisExtraction_Var[vars_lambda1]
                                var_value_lambda2 = self.PlateletApheresisExtraction_Var[vars_lambda2]
                                
                                coeff_lambda1 = 1.0
                                coeff_lambda2 = -1.0

                                # Calculating left hand side components
                                LeftHandSide_lambda1 = coeff_lambda1 * var_value_lambda1
                                LeftHandSide_lambda2 = coeff_lambda2 * var_value_lambda2
                                LeftHandSide = LeftHandSide_lambda1 + LeftHandSide_lambda2
                                

                                RightHandSide = 0.0

                                # Adding the constraint
                                constraint_name = f"Nonanticipativity_lambda_w1_{w1}_w2_{w2}_t_{t}_c_{c}_u_{u}"
                                self.CRPBIM.addConstr(LeftHandSide == RightHandSide, name=constraint_name)
    
    # This function creates the non anticipitativity constraint
    def CreateNonanticipativityConstraints_Rhovar(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateNonanticipativityConstraints_Rhovar")

        AlreadyAdded = [[False for _ in range(self.NrPlateletWholeExtractionVariables)] for _ in range(self.NrPlateletWholeExtractionVariables)]
        considertimebucket = self.Instance.TimeBucketSet

        for w1 in self.ScenarioSet:
            for w2 in range(w1 + 1, self.NrScenario):
                for t in considertimebucket:
                    for c in self.Instance.BloodGPSet:
                        for h in self.Instance.HospitalSet:  

                            Index_Rhovar1 = self.GetIndexPlateletWholeExtractionVariable(t, c, h, w1) - self.GetStartPlateletWholeExtractionVariables()
                            Index_Rhovar2 = self.GetIndexPlateletWholeExtractionVariable(t, c, h, w2) - self.GetStartPlateletWholeExtractionVariables()

                            if self.Scenarios[w1].PlateletWholeExtractionVariable[t][c][h] == self.Scenarios[w2].PlateletWholeExtractionVariable[t][c][h] and not AlreadyAdded[Index_Rhovar1][Index_Rhovar2]:
                                
                                AlreadyAdded[Index_Rhovar1][Index_Rhovar2] = True
                                AlreadyAdded[Index_Rhovar2][Index_Rhovar1] = True

                                vars_Rhovar1 = self.GetIndexPlateletWholeExtractionVariable(t, c, h, w1)
                                vars_Rhovar2 = self.GetIndexPlateletWholeExtractionVariable(t, c, h, w2)

                                # Retrieving variable values
                                var_value_Rhovar1 = self.PlateletWholeExtraction_Var[vars_Rhovar1]
                                var_value_Rhovar2 = self.PlateletWholeExtraction_Var[vars_Rhovar2]
                                
                                coeff_Rhovar1 = 1.0
                                coeff_Rhovar2 = -1.0

                                # Calculating left hand side components
                                LeftHandSide_Rhovar1 = coeff_Rhovar1 * var_value_Rhovar1
                                LeftHandSide_Rhovar2 = coeff_Rhovar2 * var_value_Rhovar2
                                LeftHandSide = LeftHandSide_Rhovar1 + LeftHandSide_Rhovar2
                                

                                RightHandSide = 0.0

                                # Adding the constraint
                                constraint_name = f"Nonanticipativity_Rhovar_w1_{w1}_w2_{w2}_t_{t}_c_{c}_h_{h}"
                                self.CRPBIM.addConstr(LeftHandSide == RightHandSide, name=constraint_name)

    # This function creates the non anticipitativity constraint
    def CreateNonanticipativityConstraints_upsilon(self): 
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateNonanticipativityConstraints_upsilon")

        AlreadyAdded = [[False for _ in range(self.NrServedPatientVariables)] for _ in range(self.NrServedPatientVariables)]
        considertimebucket = self.Instance.TimeBucketSet

        for w1 in self.ScenarioSet:
            for w2 in range(w1 + 1, self.NrScenario):
                for t in considertimebucket:
                    for j in self.Instance.InjuryLevelSet:
                        for cprime in self.Instance.BloodGPSet:
                            for c in self.Instance.BloodGPSet:
                                for r in self.Instance.PlateletAgeSet:
                                    for u in self.Instance.FacilitySet:
                                    
                                        Index_x1 = self.GetIndexServedPatientVariable(t, j, cprime, c, r, u, w1) - self.GetStartServedPatientVariables()
                                        Index_x2 = self.GetIndexServedPatientVariable(t, j, cprime, c, r, u, w2) - self.GetStartServedPatientVariables()

                                        if self.Scenarios[w1].ServedPatientVariable[t][j][cprime][c][r][u] == self.Scenarios[w2].ServedPatientVariable[t][j][cprime][c][r][u] and not AlreadyAdded[Index_x1][Index_x2]:
                                            
                                            AlreadyAdded[Index_x1][Index_x2] = True
                                            AlreadyAdded[Index_x2][Index_x1] = True

                                            vars_upsilon1 = self.GetIndexServedPatientVariable(t, j, cprime, c, r, u, w1)
                                            vars_upsilon2 = self.GetIndexServedPatientVariable(t, j, cprime, c, r, u, w2)

                                            # Retrieving variable values
                                            var_value_upsilon1 = self.ServedPatient_Var[vars_upsilon1]
                                            var_value_upsilon2 = self.ServedPatient_Var[vars_upsilon2]
                                            
                                            coeff_upsilon1 = 1.0
                                            coeff_upsilon2 = -1.0

                                            # Calculating left hand side components
                                            LeftHandSide_upsilon1 = coeff_upsilon1 * var_value_upsilon1
                                            LeftHandSide_upsilon2 = coeff_upsilon2 * var_value_upsilon2
                                            LeftHandSide = LeftHandSide_upsilon1 + LeftHandSide_upsilon2
                                            

                                            RightHandSide = 0.0

                                            # Adding the constraint
                                            constraint_name = f"Nonanticipativity_upsilon_w1_{w1}_w2_{w2}_t_{t}_j_{j}_cprime_{cprime}_c_{c}_r_{r}_u_{u}"
                                            self.CRPBIM.addConstr(LeftHandSide == RightHandSide, name=constraint_name)

                                            #if Constants.Debug: 
                                                #print(f"Added constraint: {constraint_name}")

    # Define the constraint of the model
    def CreateConstraints(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateConstraints")

        self.CreateBudgetConstraint()
        self.CreateVehicleAssignmentCapacityConstraint()
        self.CreateVehicleAssignemntACFEstablishmentConstraint()
        self.CreateLowMedPriorityPatientFlowConstraint()
        self.CreateHighPriorityPatientFlowConstraint()
        self.CreateLowMedPriorityPatientServiceConstraint()
        self.CreateHighPriorityPatientServiceConstraint()
        self.CreateACFTreatmentCapacityConstraint()
        self.CreateHospitalTreatmentCapacityConstraint()
        self.CreateHospitalPlateletFlowConstraint()
        self.CreateACFPlateletFlowConstraint()
        self.CreatePlateletWastageConstraint()
        self.CreateHospitalRescueVehicleCapacityConstraint()
        self.CreateACFRescueVehicleCapacityConstraint()
        self.CreateNrApheresisLimitConstraint()
        self.CreateApheresisACFConstraint()
        self.CreateACFApheresisCapacityConstraint()
        self.CreateHospitalApheresisCapacityConstraint()
        self.CreateApheresisCapacityDonorsConstraint()
        self.CreateWholeCapacityDonorsConstraint()
        self.CreateHospitalTransshipmentCapacityConstraint()
        self.CreateACFTransshipmentCapacityConstraint()

        if self.Model != Constants.Two_Stage:
            print("Non-anticipativity Constraints")
            #self.CreateNonanticipativityConstraints_y()
            #self.CreateNonanticipativityConstraints_q()
            #self.CreateNonanticipativityConstraints_b()
            #self.CreateNonanticipativityConstraints_bPrime()
            #self.CreateNonanticipativityConstraints_bDoublePrime()
            #self.CreateNonanticipativityConstraints_lambda()
            #self.CreateNonanticipativityConstraints_Rhovar()
            #self.CreateNonanticipativityConstraints_upsilon()

        if self.EvaluateSolution or self.Multi_StageHeuristic:
            self.CreateCopyGivenACFEstablishmentConstraints()
            self.CreateCopyGivenVehicleAssignmentConstraints()


        if self.WamStart:
            self.WarmStartGivenSetupConstraints()

        if self.EvaluateSolution:
            if self.Model == Constants.Two_Stage or self.Model == Constants.ModelMulti_Stage:
                self.CreateCopyGivenApheresisAssignmentConstraints()
                # self.CreateCopyGivenTransshipmentHIConstraints()
                # self.CreateCopyGivenTransshipmentIIConstraints()
                # self.CreateCopyGivenTransshipmentHHConstraints()

    def BuildModel(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- BuildModel")
        
        # Initialize the Gurobi model
        self.CRPBIM = gp.Model("Casualty_Response_Planning_considering_Blood_Inventory_Management")

        # Create variables and objective function
        self.CreateVariable_and_Objective_Function()

        # Create all constraints
        self.CreateConstraints()

    def Parameter_Tunning(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- Parameter_Tunning")

        self.CRPBIM.setParam('TimeLimit', Constants.MIPTimeLimit)
        if Constants.UsingRelaxedMIPGapforTwoStageHeuristic == True:
            self.CRPBIM.setParam('MIPGap', self.Instance.My_EpGap_Heuristic)
        else:
            self.CRPBIM.setParam('MIPGap', self.Instance.My_EpGap)
        
        self.CRPBIM.setParam('Threads', 1)
        self.CRPBIM.setParam('OutputFlag', Constants.ModelOutputFlag)  # Prevents Gurobi from showing the optimization process!

    def Check_Optimality_and_Print_Solutions(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- Check_Optimality_and_Print_Solutions")

        solution = {}
        if self.CRPBIM.status == GRB.OPTIMAL:
            print("Optimal solution found.")
            objective_value = self.CRPBIM.objVal
            solution['objective_value'] = objective_value
            solution['variables'] = {}
            print(f"$$$$$$$$ Objective Value: {objective_value}")
            print("------------------------")
            for index, var_obj in self.ACF_Establishment_Var.items():
                if var_obj.X > 1e-6:  
                    if Constants.Debug: print(f"{var_obj.VarName} = {var_obj.X}")
                    solution['variables'][var_obj.VarName] = var_obj.X

            for index, var_obj in self.Vehicle_Assignment_Var.items():
                if var_obj.X > 1e-6:  
                    if Constants.Debug: print(f"{var_obj.VarName} = {var_obj.X}")
                    solution['variables'][var_obj.VarName] = var_obj.X

            for index, var_obj in self.ApheresisAssignment_Var.items():
                if var_obj.X > 1e-6:  
                    #if Constants.Debug: print(f"{var_obj.VarName} = {var_obj.X}")
                    solution['variables'][var_obj.VarName] = var_obj.X
            
            for index, var_obj in self.TransshipmentHI_Var.items():
                if var_obj.X > 1e-6:  
                    #if Constants.Debug: print(f"{var_obj.VarName} = {var_obj.X}")
                    solution['variables'][var_obj.VarName] = var_obj.X
            
            for index, var_obj in self.TransshipmentII_Var.items():
                if var_obj.X > 1e-6:  
                    #if Constants.Debug: print(f"{var_obj.VarName} = {var_obj.X}")
                    solution['variables'][var_obj.VarName] = var_obj.X
            
            for index, var_obj in self.TransshipmentHH_Var.items():
                if var_obj.X > 1e-6:  
                    #if Constants.Debug: print(f"{var_obj.VarName} = {var_obj.X}")
                    solution['variables'][var_obj.VarName] = var_obj.X

            for index, var_obj in self.PatientTransfer_Var.items():
                if var_obj.X > 1e-6:
                    #if Constants.Debug: print(f"{var_obj.VarName} = {var_obj.X}")  
                    solution['variables'][var_obj.VarName] = var_obj.X
            for index, var_obj in self.UnsatisfiedPatients_Var.items():
                if var_obj.X > 1e-6:
                    if Constants.Debug: print(f"{var_obj.VarName} = {var_obj.X}")  
                    solution['variables'][var_obj.VarName] = var_obj.X
            for index, var_obj in self.PlateletInventory_Var.items():
                if var_obj.X > 1e-6:
                    #if Constants.Debug: print(f"{var_obj.VarName} = {var_obj.X}")  
                    solution['variables'][var_obj.VarName] = var_obj.X
            for index, var_obj in self.OutdatedPlatelet_Var.items():
                if var_obj.X > 1e-6:
                    #if Constants.Debug: print(f"{var_obj.VarName} = {var_obj.X}")  
                    solution['variables'][var_obj.VarName] = var_obj.X
            for index, var_obj in self.ServedPatient_Var.items():
                if var_obj.X > 1e-6:
                    #if Constants.Debug: print(f"{var_obj.VarName} = {var_obj.X}")  
                    solution['variables'][var_obj.VarName] = var_obj.X
            for index, var_obj in self.PatientPostponement_Var.items():
                if var_obj.X > 1e-6:
                    #if Constants.Debug: print(f"{var_obj.VarName} = {var_obj.X}")  
                    solution['variables'][var_obj.VarName] = var_obj.X
            for index, var_obj in self.PlateletApheresisExtraction_Var.items():
                if var_obj.X > 1e-6:
                    #if Constants.Debug: print(f"{var_obj.VarName} = {var_obj.X}")  
                    solution['variables'][var_obj.VarName] = var_obj.X
            for index, var_obj in self.PlateletWholeExtraction_Var.items():
                if var_obj.X > 1e-6:
                    #if Constants.Debug: print(f"{var_obj.VarName} = {var_obj.X}")  
                    solution['variables'][var_obj.VarName] = var_obj.X
            
        else:
            print(f"No optimal solution found. Status code: {self.CRPBIM.status}")
        return solution

    def ReadNrVariableConstraint(self):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- ReadNrVariableConstraint")

        num_vars = self.CRPBIM.numVars
        num_constrs = self.CRPBIM.numConstrs

        return num_vars, num_constrs
   
    def Solve(self, createsolution = True ):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- Solve")

        start_time = time.time()

        self.Parameter_Tunning()

        end_modeling = time.time()

        # Create the directory "MIP_Model_LP" in the current working directory
        if self.EvaluateSolution:
            lp_dir = os.path.join(os.getcwd(), "MIP_Model_LP_SDDPEvaluation")
        else:
            lp_dir = os.path.join(os.getcwd(), "MIP_Model_LP")

        if not os.path.exists(lp_dir):
            os.makedirs(lp_dir)

        # Variables to include in the filename
        T = self.Instance.NrTimeBucket
        I = self.Instance.NrACFPPoints
        H = self.Instance.NrHospitals
        L = self.Instance.NrDemandLocations
        M = self.Instance.NrRescueVehicles
        scenario = len(self.ScenarioSet)

        # Format the filename with the variables
        lp_filename = f"MIP_Model_T_{T}_I_{I}_H_{H}_L_{L}_M_{M}_Scenario_{scenario}.lp"

        # Write the model to a file before optimization
        lp_full_path = os.path.join(lp_dir, lp_filename)
        self.CRPBIM.write(lp_full_path)

        self.CRPBIM.optimize()

        nrvariable, nrconstraints = self.ReadNrVariableConstraint()

        buildtime = round(end_modeling - start_time, 2)
        solvetime = round(time.time() - end_modeling, 2)

        #sol includes objective function and variables' values
        sol = self.Check_Optimality_and_Print_Solutions()

        if self.CRPBIM.status == GRB.OPTIMAL:
            if Constants.Debug:
                print("GRB Solve Time(s): %r   GRB build time(s): %s   cost: %s" % (solvetime, buildtime, sol['objective_value']))
            if createsolution:
                Solution = self.CreateCRPSolution(sol, solvetime, nrvariable, nrconstraints)
            else:
                Solution = None
            return Solution
        elif self.CRPBIM.status == GRB.INF_OR_UNBD:
            print("Solution status: INFEASIBLE OR UNBOUNDED")
            # Write the model to an LP file
            self.CRPBIM.write("infeasible_model.lp")
        elif self.CRPBIM.status == GRB.INFEASIBLE:
            print("Solution status: INFEASIBLE")
            # Write the model to an LP file
            self.CRPBIM.write("infeasible_model.lp")
            print("Model is infeasible. Identifying conflicts...")
            # Compute the IIS (Irreducible Inconsistent Subsystem)
            self.CRPBIM.computeIIS()
            for c in self.CRPBIM.getConstrs():
                if c.IISConstr:
                    print(f"Infeasible constraint!!!!!!!!!!!!!!: {c.constrName}")
        elif self.CRPBIM.status == GRB.UNBOUNDED:
            print("Solution status: UNBOUNDED")
            # Write the model to an LP file
            self.CRPBIM.write("unbounded_model.lp")
            
    def ModifyMipForScenarioTree(self, scenariotree):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- ModifyMipForScenarioTree")

        self.DemandScenarioTree = scenariotree
        self.DemandScenarioTree.Owner = self
        self.NrScenario = len([n for n in self.DemandScenarioTree.Nodes if len(n.Branches) == 0])
        if Constants.Debug: print(f"Number of scenarios: {self.NrScenario}")
        self.ComputeIndices()
        self.Scenarios = scenariotree.GetAllScenarios(True, self.ExpendFirstNode)
        if Constants.Debug: print(f"Retrieved {len(self.Scenarios)} scenarios.")
        self.ScenarioSet = range(self.NrScenario)
        if Constants.Debug: print(f"ScenarioSet range set to 0 to {self.NrScenario - 1}.")
   
        # Update the right-hand side (RHS) of the flow conservation constraints
        #Debug_Demand_LowMed = 0
        #Debug_Demand_High = 0
        for w_idx, w in enumerate(self.ScenarioSet):
            for t_idx, t in enumerate(self.Instance.TimeBucketSet):
                for j_idx, j in enumerate(self.Instance.InjuryLevelSet):
                    if j != 0:
                        for c_idx, c in enumerate(self.Instance.BloodGPSet):
                            for l_idx, l in enumerate(self.Instance.DemandSet):
                                # Calculate the new right-hand side for the constraint
                                righthandside = self.Scenarios[w].Demands[t][j][c][l]

                                # Retrieve the constraint reference
                                constr_ref = self.LowMedPriorityPatientFlowConstraintNR[w_idx][t_idx][j_idx][c_idx][l_idx]
                                
                                # Update the RHS of the constraint
                                constr_ref.RHS = righthandside
                                #Debug_Demand_LowMed += righthandside
                                #if Constants.Debug: print(f"Updated RHS of constraint '{constr_ref.ConstrName}' to {righthandside}")
                                self.CRPBIM.update()            
        #print("Debug_Demand_LowMed: ", Debug_Demand_LowMed)
        # Update the right-hand side (RHS) of the flow conservation constraints
        for w_idx, w in enumerate(self.ScenarioSet):
            for t_idx, t in enumerate(self.Instance.TimeBucketSet):
                for j_idx, j in enumerate(self.Instance.InjuryLevelSet):
                    if j == 0:
                        for c_idx, c in enumerate(self.Instance.BloodGPSet):
                            for l_idx, l in enumerate(self.Instance.DemandSet):
                                # Calculate the new right-hand side for the constraint
                                righthandside = self.Scenarios[w].Demands[t][j][c][l]

                                # Retrieve the constraint reference
                                constr_ref = self.HighPriorityPatientFlowConstraintNR[w_idx][t_idx][j_idx][c_idx][l_idx]
                                
                                # Update the RHS of the constraint
                                constr_ref.RHS = righthandside
                                #Debug_Demand_High += righthandside
                                #if Constants.Debug: print(f"Updated RHS of constraint '{constr_ref.ConstrName}' to {righthandside}")
                                self.CRPBIM.update()
        #print("Debug_Demand_High: ", Debug_Demand_High)
        #print("------")
        # Update the right-hand side (RHS) of the flow conservation constraints
        for w_idx, w in enumerate(self.ScenarioSet):
            for t_idx, t in enumerate(self.Instance.TimeBucketSet):
                for h_idx, h in enumerate(self.Instance.HospitalSet):
                    # Calculate the new right-hand side for the constraint
                    righthandside = -1.0 * self.Scenarios[w].HospitalCaps[t][h]

                    # Retrieve the constraint reference
                    constr_ref = self.HospitalTreatmentCapacityConstraintNR[w_idx][t_idx][h_idx]
                    
                    # Update the RHS of the constraint
                    constr_ref.RHS = righthandside
                    #if Constants.Debug: print(f"Updated RHS of constraint '{constr_ref.ConstrName}' to {righthandside}")
        self.CRPBIM.update()
        
        # Update the right-hand side (RHS) of the flow conservation constraints
        for w_idx, w in enumerate(self.ScenarioSet):
            for t_idx, t in enumerate(self.Instance.TimeBucketSet):
                for c_idx, c in enumerate(self.Instance.BloodGPSet):
                    for u_idx, u in enumerate(self.Instance.FacilitySet):
                        # Calculate the new right-hand side for the constraint
                        righthandside = -1.0 * self.Instance.Platelet_Units_Apheresis * self.Scenarios[w].ApheresisDonors[t][c][u]

                        # Retrieve the constraint reference
                        constr_ref = self.ApheresisCapacityDonorsConstraintNR[w_idx][t_idx][c_idx][u_idx]
                        
                        # Update the RHS of the constraint
                        constr_ref.RHS = righthandside
                        #if Constants.Debug: print(f"Updated RHS of constraint '{constr_ref.ConstrName}' to {righthandside}")
        self.CRPBIM.update()
        
        # Update the right-hand side (RHS) of the flow conservation constraints
        for w_idx, w in enumerate(self.ScenarioSet):
            for t_idx, t in enumerate(self.Instance.TimeBucketSet):
                for c_idx, c in enumerate(self.Instance.BloodGPSet):
                    for h_idx, h in enumerate(self.Instance.HospitalSet):
                        # Calculate the new right-hand side for the constraint
                        righthandside = -1.0 * self.Scenarios[w].WholeDonors[t][c][h]

                        # Retrieve the constraint reference
                        constr_ref = self.WholeCapacityDonorsConstraintNR[w_idx][t_idx][c_idx][h_idx]
                        
                        # Update the RHS of the constraint
                        constr_ref.RHS = righthandside
                        #if Constants.Debug: print(f"Updated RHS of constraint '{constr_ref.ConstrName}' to {righthandside}")
        self.CRPBIM.update()

        if self.EVPI:
            #Recompute the value of M
            totaldemandatt = [0 for p in self.Instance.ProductSet]
            self.ModifyBigMForScenario(totaldemandatt)

        self.CRPBIM.update()

    def ModifyMipForFixApheresisAssignment(self, givenapheresisassignments, fixuntil=-1):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- ModifyMipForFixApheresisAssignment")
        timeset = self.Instance.TimeBucketSet
        if fixuntil > -1:
            timeset = range(fixuntil)

        for t in timeset:
            for i in self.Instance.ACFPPointSet:
                        
                righthandside = float(givenapheresisassignments[t][i])

                constr_ref = self.ApheresisAssignmentVarConstraintNR[0][t][i]

                constr_ref.RHS = righthandside

                #if Constants.Debug: print(f"Updated RHS of constraint '{constr_ref.ConstrName}' to {righthandside}")

        self.CRPBIM.update()
    
    def ModifyMipForFixTransshipmentHI(self, giventransshipmentHIs, fixuntil=-1):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- ModifyMipForFixTransshipmentHI")
        timeset = self.Instance.TimeBucketSet
        if fixuntil > -1:
            timeset = range(fixuntil)
        
        for t in timeset:
            for c in self.Instance.BloodGPSet:
                for r in self.Instance.PlateletAgeSet:
                    for h in self.Instance.HospitalSet:
                        for i in self.Instance.ACFPPointSet:
                        
                            righthandside = float(giventransshipmentHIs[t][c][r][h][i])

                            constr_ref = self.TransshipmentHIVarConstraintNR[0][t][c][r][h][i]

                            constr_ref.RHS = righthandside

                            #if Constants.Debug: print(f"Updated RHS of constraint '{constr_ref.ConstrName}' to {righthandside}")

        self.CRPBIM.update()
    
    def ModifyMipForFixTransshipmentII(self, giventransshipmentIIs, fixuntil=-1):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- ModifyMipForFixTransshipmentII")
        timeset = self.Instance.TimeBucketSet
        if fixuntil > -1:
            timeset = range(fixuntil)
        
        for t in timeset:
            for c in self.Instance.BloodGPSet:
                for r in self.Instance.PlateletAgeSet:
                    for i in self.Instance.ACFPPointSet:
                        for iprime in self.Instance.ACFPPointSet:
                        
                            righthandside = float(giventransshipmentIIs[t][c][r][i][iprime])

                            constr_ref = self.TransshipmentIIVarConstraintNR[0][t][c][r][i][iprime]

                            constr_ref.RHS = righthandside

                            #if Constants.Debug: print(f"Updated RHS of constraint '{constr_ref.ConstrName}' to {righthandside}")

        self.CRPBIM.update()
    
    def ModifyMipForFixTransshipmentHH(self, giventransshipmentHHs, fixuntil=-1):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- ModifyMipForFixTransshipmentHH")
        timeset = self.Instance.TimeBucketSet
        if fixuntil > -1:
            timeset = range(fixuntil)
        
        for t in timeset:
            for c in self.Instance.BloodGPSet:
                for r in self.Instance.PlateletAgeSet:
                    for h in self.Instance.HospitalSet:
                        for hprime in self.Instance.HospitalSet:
                        
                            righthandside = float(giventransshipmentHHs[t][c][r][h][hprime])

                            constr_ref = self.TransshipmentHHVarConstraintNR[0][t][c][r][h][hprime]

                            constr_ref.RHS = righthandside

                            #if Constants.Debug: print(f"Updated RHS of constraint '{constr_ref.ConstrName}' to {righthandside}")

        self.CRPBIM.update()
    
    def CreateCRPSolution(self, sol, solvetime, nrvariable, nrconstraints):
        if Constants.Debug: print("\n We are in 'MIPSolver' Class -- CreateCRPSolution")

        scenarioset = self.ScenarioSet
        scenarios = self.Scenarios
        timebucketset = self.Instance.TimeBucketSet

        objvalue = sol['objective_value']
        
        ################################# Create an empty list to store the solution values based on the index
        sol_x_values_by_index = []
        Final_ACFEstablishmentCost = 0

        for i in self.Instance.ACFPPointSet:
            index = self.GetIndexACFEstablishmentVariable(i, 0)
            if index in self.ACF_Establishment_Var:
                Final_ACFEstablishmentCost += (self.Instance.Fixed_Cost_ACF[i] * self.ACF_Establishment_Var[index].X)
                sol_x_values_by_index.append(self.ACF_Establishment_Var[index].X)

        if Constants.Debug: print("Final_ACFEstablishmentCost: ", Final_ACFEstablishmentCost)

        if len(self.ScenarioSet) != 1:
            #This one is for when we are solving the MIP model.
            repeated_values = sol_x_values_by_index * len(self.ScenarioSet)  # Replicate the list
            solACFEstablishment_x_wi = Tool.Transform2d(repeated_values, len(self.ScenarioSet), len(self.Instance.ACFPPointSet))
        else:
            #This one is for when we are solving SDDP
            solACFEstablishment_x_wi = Tool.Transform2d(sol_x_values_by_index, len(self.ScenarioSet), len(self.Instance.ACFPPointSet))
        
        #if Constants.Debug: print("solACFEstablishment_x_wi:\n ", solACFEstablishment_x_wi)

        ################################# Create an empty list to store the solution values based on the index
        sol_thetavar_values_by_index = []
        Final_Vehicle_AssignmentCost = 0

        for m in self.Instance.RescueVehicleSet:
            for i in self.Instance.ACFPPointSet:
                index = self.GetIndexVehicleAssignmentVariable(m, i, 0)
                if index in self.Vehicle_Assignment_Var:
                    Final_Vehicle_AssignmentCost += (self.Instance.VehicleAssignment_Cost[m] * self.Vehicle_Assignment_Var[index].X)
                    sol_thetavar_values_by_index.append(self.Vehicle_Assignment_Var[index].X)

        if Constants.Debug: print("Final_Vehicle_AssignmentCost: ", Final_Vehicle_AssignmentCost)
        #if Constants.Debug: print("sol_thetavar_values_by_index: ", sol_thetavar_values_by_index)

        if len(self.ScenarioSet) != 1:
            #This one is for when we are solving the MIP model.
            repeated_values = sol_thetavar_values_by_index * len(self.ScenarioSet)  # Replicate the list
            solVehicleAssignment_thetavar_wmi = Tool.Transform3d(repeated_values, len(self.ScenarioSet), len(self.Instance.RescueVehicleSet), len(self.Instance.ACFPPointSet))
        else:
            #This one is for when we are solving SDDP
            solVehicleAssignment_thetavar_wmi = Tool.Transform3d(sol_thetavar_values_by_index, len(self.ScenarioSet), len(self.Instance.RescueVehicleSet), len(self.Instance.ACFPPointSet))
        
        #if Constants.Debug: print("solVehicleAssignment_thetavar_wmi:\n ", solVehicleAssignment_thetavar_wmi)

        ########################################## Create an empty list to store the solution values based on the index
        sol_y_values_by_index = []
        Final_ApheresisAssignmentCost = 0

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for i in self.Instance.ACFPPointSet:
                    index = self.GetIndexApheresisAssignmentVariable(t, i, w)
                    if index in self.ApheresisAssignment_Var:
                        Final_ApheresisAssignmentCost += (self.Instance.ApheresisMachineAssignment_Cost[i] * self.Scenarios[w].Probability * self.ApheresisAssignment_Var[index].X)
                        sol_y_values_by_index.append(self.ApheresisAssignment_Var[index].X)

        if Constants.Debug: print("Final_ApheresisAssignmentCost: ", Final_ApheresisAssignmentCost)

        solApheresisAssignment_y_wti = Tool.Transform3d(sol_y_values_by_index, len(self.ScenarioSet), len(self.Instance.TimeBucketSet), len(self.Instance.ACFPPointSet))
        
        #if Constants.Debug: print("solApheresisAssignment_y_wti: ", solApheresisAssignment_y_wti)
        
        ########################################## Create an empty list to store the solution values based on the index
        sol_b_values_by_index = []
        Final_TransshipmentHICost = 0

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            for i in self.Instance.ACFPPointSet:
                                index = self.GetIndexTransshipmentHIVariable(t, c, r, h, i, w)
                                if index in self.TransshipmentHI_Var:
                                    Final_TransshipmentHICost += (self.Instance.Distance_A_H[i][h] * self.Scenarios[w].Probability * self.TransshipmentHI_Var[index].X)
                                    sol_b_values_by_index.append(self.TransshipmentHI_Var[index].X)

        if Constants.Debug: print("Final_TransshipmentHICost: ", Final_TransshipmentHICost)

        solTransshipmentHI_b_wtcrhi = Tool.Transform6d(sol_b_values_by_index, len(self.ScenarioSet), len(self.Instance.TimeBucketSet), len(self.Instance.BloodGPSet), len(self.Instance.PlateletAgeSet), len(self.Instance.HospitalSet), len(self.Instance.ACFPPointSet))
        
        #if Constants.Debug: print("solTransshipmentHI_b_wtcrhi: ", solTransshipmentHI_b_wtcrhi)
        
        ########################################## Create an empty list to store the solution values based on the index
        sol_bPrime_values_by_index = []
        Final_TransshipmentIICost = 0

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for i in self.Instance.ACFPPointSet:
                            for iprime in self.Instance.ACFPPointSet:
                                index = self.GetIndexTransshipmentIIVariable(t, c, r, i, iprime, w)
                                if index in self.TransshipmentII_Var:
                                    Final_TransshipmentIICost += (self.Instance.Distance_A_A[i][iprime] * self.Scenarios[w].Probability * self.TransshipmentII_Var[index].X)
                                    sol_bPrime_values_by_index.append(self.TransshipmentII_Var[index].X)

        if Constants.Debug: print("Final_TransshipmentIICost: ", Final_TransshipmentIICost)

        solTransshipmentII_bPrime_wtcrii = Tool.Transform6d(sol_bPrime_values_by_index, len(self.ScenarioSet), len(self.Instance.TimeBucketSet), len(self.Instance.BloodGPSet), len(self.Instance.PlateletAgeSet), len(self.Instance.ACFPPointSet), len(self.Instance.ACFPPointSet))
        
        #if Constants.Debug: print("solTransshipmentII_bPrime_wtcrii': ", solTransshipmentII_bPrime_wtcrii)
        
        ########################################## Create an empty list to store the solution values based on the index
        sol_bDoublePrime_values_by_index = []
        Final_TransshipmentHHCost = 0

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            for hprime in self.Instance.HospitalSet:
                                index = self.GetIndexTransshipmentHHVariable(t, c, r, h, hprime, w)
                                if index in self.TransshipmentHH_Var:
                                    Final_TransshipmentHHCost += (self.Instance.Distance_H_H[h][hprime] * self.Scenarios[w].Probability * self.TransshipmentHH_Var[index].X)
                                    sol_bDoublePrime_values_by_index.append(self.TransshipmentHH_Var[index].X)

        if Constants.Debug: print("Final_TransshipmentHHCost: ", Final_TransshipmentHHCost)

        solTransshipmentHH_bDoublePrime_wtcrhh = Tool.Transform6d(sol_bDoublePrime_values_by_index, len(self.ScenarioSet), len(self.Instance.TimeBucketSet), len(self.Instance.BloodGPSet), len(self.Instance.PlateletAgeSet), len(self.Instance.HospitalSet), len(self.Instance.HospitalSet))
        
        #if Constants.Debug: print("solTransshipmentHH_bDoublePrime_wtcrhh: ", solTransshipmentHH_bDoublePrime_wtcrhh)

        ############################################# Create an empty list to store the solution values based on the index
        sol_q_values_by_index = []
        Final_PatientTransferCost = 0
        
        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for j in self.Instance.InjuryLevelSet:
                    for c in self.Instance.BloodGPSet:
                        for l in self.Instance.DemandSet:
                            for u in self.Instance.FacilitySet:
                                for m in self.Instance.RescueVehicleSet:
                                    index = self.GetIndexPatientTransferVariable(t, j, c, l, u, m, w)
                                    if index in self.PatientTransfer_Var:

                                        if u < self.Instance.NrHospitals:
                                            Final_PatientTransferCost +=  (self.Instance.Distance_D_H[l][u] * self.Scenarios[w].Probability * self.PatientTransfer_Var[index].X)
                                        else:
                                            Final_PatientTransferCost +=  (self.Instance.Distance_D_A[l][u-self.Instance.NrHospitals] * self.Scenarios[w].Probability * self.PatientTransfer_Var[index].X)
                                                
                                        sol_q_values_by_index.append(self.PatientTransfer_Var[index].X)

        if Constants.Debug: print("Final_PatientTransferCost: ", Final_PatientTransferCost)

        solPatientTransfer_q_wtjclum = Tool.Transform7d(sol_q_values_by_index, len(self.ScenarioSet), len(self.Instance.TimeBucketSet), len(self.Instance.InjuryLevelSet), len(self.Instance.BloodGPSet), len(self.Instance.DemandSet), len(self.Instance.FacilitySet), len(self.Instance.RescueVehicleSet))
        
        #if Constants.Debug: print("solPatientTransfer_q_wtjclum: ", solPatientTransfer_q_wtjclum)
        
        ############################################# Create an empty list to store the solution values based on the index
        sol_mu_values_by_index = []
        Final_UnsatisfiedPatientsCost = 0

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for j in self.Instance.InjuryLevelSet:
                    for c in self.Instance.BloodGPSet:
                        for l in self.Instance.DemandSet:

                            index = self.GetIndexUnsatisfiedPatientsVariable(t, j, c, l, w)

                            if index in self.UnsatisfiedPatients_Var:
                                Final_UnsatisfiedPatientsCost += (self.Instance.Casualty_Shortage_Cost[j][l] * self.Scenarios[w].Probability * self.UnsatisfiedPatients_Var[index].X)
                                sol_mu_values_by_index.append(self.UnsatisfiedPatients_Var[index].X)

        if Constants.Debug: print("Final_UnsatisfiedPatientsCost: ", Final_UnsatisfiedPatientsCost)

        solUnsatisfiedPatient_mu_wtjcl = Tool.Transform5d(sol_mu_values_by_index, len(self.ScenarioSet), len(self.Instance.TimeBucketSet), len(self.Instance.InjuryLevelSet), len(self.Instance.BloodGPSet), len(self.Instance.DemandSet))
        
        #if Constants.Debug: print("solUnsatisfiedPatient_mu_wtjcl: ", solUnsatisfiedPatient_mu_wtjcl)
        
        ############################################# Create an empty list to store the solution values based on the index
        sol_eta_values_by_index = []
        Final_PlateletInventoryCost = 0

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for u in self.Instance.FacilitySet:

                            index = self.GetIndexPlateletInventoryVariable(t, c, r, u, w)

                            if index in self.PlateletInventory_Var:
                                Final_PlateletInventoryCost += (self.Instance.Platelet_Inventory_Cost[u] * self.Scenarios[w].Probability * self.PlateletInventory_Var[index].X)
                                sol_eta_values_by_index.append(self.PlateletInventory_Var[index].X)

        if Constants.Debug: print("Final_PlateletInventoryCost: ", Final_PlateletInventoryCost)

        solPlateletInventory_eta_wtcru = Tool.Transform5d(sol_eta_values_by_index, len(self.ScenarioSet), len(self.Instance.TimeBucketSet), len(self.Instance.BloodGPSet), len(self.Instance.PlateletAgeSet), len(self.Instance.FacilitySet))
        
        #if Constants.Debug: print("solPlateletInventory_eta_wtcru: ", solPlateletInventory_eta_wtcru)
        
        ############################################# Create an empty list to store the solution values based on the index
        sol_sigmavar_values_by_index = []
        Final_OutdatedPlateletCost = 0

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for u in self.Instance.FacilitySet:

                    index = self.GetIndexOutdatedPlateletVariable(t, u, w)

                    if index in self.OutdatedPlatelet_Var:
                        Final_OutdatedPlateletCost += (self.Instance.Platelet_Wastage_Cost[u] * self.Scenarios[w].Probability * self.OutdatedPlatelet_Var[index].X)
                        sol_sigmavar_values_by_index.append(self.OutdatedPlatelet_Var[index].X)

        if Constants.Debug: print("Final_OutdatedPlateletCost: ", Final_OutdatedPlateletCost)

        solOutdatedPlatelet_sigmavar_wtu = Tool.Transform3d(sol_sigmavar_values_by_index, len(self.ScenarioSet), len(self.Instance.TimeBucketSet), len(self.Instance.FacilitySet))
        
        #if Constants.Debug: print("solOutdatedPlatelet_sigmavar_wtu: ", solOutdatedPlatelet_sigmavar_wtu)
        
        ############################################# Create an empty list to store the solution values based on the index
        sol_upsilon_values_by_index = []
        Final_ServedPatientCost = 0

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for j in self.Instance.InjuryLevelSet:
                    for cprime in self.Instance.BloodGPSet:
                        for c in self.Instance.BloodGPSet:
                            for r in self.Instance.PlateletAgeSet:
                                for u in self.Instance.FacilitySet:

                                    index = self.GetIndexServedPatientVariable(t, j, cprime, c, r, u, w)

                                    if index in self.ServedPatient_Var:
                                        Final_ServedPatientCost += (self.Instance.Substitution_Weight[cprime][c] * self.Scenarios[w].Probability * self.ServedPatient_Var[index].X)
                                        sol_upsilon_values_by_index.append(self.ServedPatient_Var[index].X)

        if Constants.Debug: print("Final_ServedPatientCost: ", Final_ServedPatientCost)

        solServedPatient_upsilon_wtjcPcru = Tool.Transform7d(sol_upsilon_values_by_index, len(self.ScenarioSet), len(self.Instance.TimeBucketSet), len(self.Instance.InjuryLevelSet), len(self.Instance.BloodGPSet), len(self.Instance.BloodGPSet), len(self.Instance.PlateletAgeSet), len(self.Instance.FacilitySet))
        
        #if Constants.Debug: print("solServedPatient_upsilon_wtjc'cru: ", solServedPatient_upsilon_wtjcPcru)
        
        ############################################# Create an empty list to store the solution values based on the index
        sol_zeta_values_by_index = []
        Final_PatientPostponementCost = 0

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for j in self.Instance.InjuryLevelSet:
                    for c in self.Instance.BloodGPSet:
                        for u in self.Instance.FacilitySet:

                            index = self.GetIndexPatientPostponementVariable(t, j, c, u, w)

                            if index in self.PatientPostponement_Var:
                                Final_PatientPostponementCost += (self.Instance.Postponing_Cost_Surgery[j] * self.Scenarios[w].Probability * self.PatientPostponement_Var[index].X)
                                sol_zeta_values_by_index.append(self.PatientPostponement_Var[index].X)

        if Constants.Debug: print("Final_PatientPostponementCost: ", Final_PatientPostponementCost)

        solPatientPostponement_zeta_wtjcu = Tool.Transform5d(sol_zeta_values_by_index, len(self.ScenarioSet), len(self.Instance.TimeBucketSet), len(self.Instance.InjuryLevelSet), len(self.Instance.BloodGPSet), len(self.Instance.FacilitySet))
        
        #if Constants.Debug: print("solPatientPostponement_zeta_wtjcu: ", solPatientPostponement_zeta_wtjcu)
        
        ############################################# Create an empty list to store the solution values based on the index
        sol_lambda_values_by_index = []
        Final_PlateletApheresisExtractionCost = 0

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for u in self.Instance.FacilitySet:

                        index = self.GetIndexPlateletApheresisExtractionVariable(t, c, u, w)

                        if index in self.PlateletApheresisExtraction_Var:
                            Final_PlateletApheresisExtractionCost += (self.Instance.ApheresisExtraction_Cost[u] * self.Scenarios[w].Probability * self.PlateletApheresisExtraction_Var[index].X)
                            sol_lambda_values_by_index.append(self.PlateletApheresisExtraction_Var[index].X)

        if Constants.Debug: print("Final_PlateletApheresisExtractionCost: ", Final_PlateletApheresisExtractionCost)

        solPlateletApheresisExtraction_lambda_wtcu = Tool.Transform4d(sol_lambda_values_by_index, len(self.ScenarioSet), len(self.Instance.TimeBucketSet), len(self.Instance.BloodGPSet), len(self.Instance.FacilitySet))
        
        #if Constants.Debug: print("solPlateletApheresisExtraction_lambda_wtcu: ", solPlateletApheresisExtraction_lambda_wtcu)
        
        ############################################# Create an empty list to store the solution values based on the index
        sol_Rhovar_values_by_index = []
        Final_PlateletWholeExtractionCost = 0

        for w in self.ScenarioSet:
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for h in self.Instance.HospitalSet:

                        index = self.GetIndexPlateletWholeExtractionVariable(t, c, h, w)

                        if index in self.PlateletWholeExtraction_Var:
                            Final_PlateletWholeExtractionCost += (self.Instance.WholeExtraction_Cost[h] * self.Scenarios[w].Probability * self.PlateletWholeExtraction_Var[index].X)
                            sol_Rhovar_values_by_index.append(self.PlateletWholeExtraction_Var[index].X)

        if Constants.Debug: print("Final_PlateletWholeExtractionCost: ", Final_PlateletWholeExtractionCost)

        solPlateletWholeExtraction_Rhovar_wtch = Tool.Transform4d(sol_Rhovar_values_by_index, len(self.ScenarioSet), len(self.Instance.TimeBucketSet), len(self.Instance.BloodGPSet), len(self.Instance.HospitalSet))
        
        #if Constants.Debug: print("solPlateletWholeExtraction_Rhovar_wtch: ", solPlateletWholeExtraction_Rhovar_wtch)
        
        ##########################################
        if Constants.Debug: print("------------Moving from 'MIPSolver' Class ('CreateCRPSolution' Function) to 'Solution' class (Constructor))---------------")
        solution = Solution(instance=self.Instance, 
                            solACFEstablishment_x_wi = solACFEstablishment_x_wi, 
                            solVehicleAssignment_thetavar_wmi = solVehicleAssignment_thetavar_wmi, 
                            solApheresisAssignment_y_wti = solApheresisAssignment_y_wti, 
                            solTransshipmentHI_b_wtcrhi = solTransshipmentHI_b_wtcrhi, 
                            solTransshipmentII_bPrime_wtcrii = solTransshipmentII_bPrime_wtcrii, 
                            solTransshipmentHH_bDoublePrime_wtcrhh = solTransshipmentHH_bDoublePrime_wtcrhh, 
                            solPatientTransfer_q_wtjclum = solPatientTransfer_q_wtjclum, 
                            solUnsatisfiedPatient_mu_wtjcl = solUnsatisfiedPatient_mu_wtjcl, 
                            solPlateletInventory_eta_wtcru = solPlateletInventory_eta_wtcru, 
                            solOutdatedPlatelet_sigmavar_wtu = solOutdatedPlatelet_sigmavar_wtu, 
                            solServedPatient_upsilon_wtjcPcru = solServedPatient_upsilon_wtjcPcru, 
                            solPatientPostponement_zeta_wtjcu = solPatientPostponement_zeta_wtjcu, 
                            solPlateletApheresisExtraction_lambda_wtcu = solPlateletApheresisExtraction_lambda_wtcu, 
                            solPlateletWholeExtraction_Rhovar_wtch = solPlateletWholeExtraction_Rhovar_wtch, 
                            Final_ACFEstablishmentCost = Final_ACFEstablishmentCost, 
                            Final_Vehicle_AssignmentCost = Final_Vehicle_AssignmentCost, 
                            Final_ApheresisAssignmentCost = Final_ApheresisAssignmentCost, 
                            Final_TransshipmentHICost = Final_TransshipmentHICost, 
                            Final_TransshipmentIICost = Final_TransshipmentIICost, 
                            Final_TransshipmentHHCost = Final_TransshipmentHHCost, 
                            Final_PatientTransferCost = Final_PatientTransferCost, 
                            Final_UnsatisfiedPatientsCost = Final_UnsatisfiedPatientsCost, 
                            Final_PlateletInventoryCost = Final_PlateletInventoryCost, 
                            Final_OutdatedPlateletCost = Final_OutdatedPlateletCost, 
                            Final_ServedPatientCost = Final_ServedPatientCost, 
                            Final_PatientPostponementCost = Final_PatientPostponementCost, 
                            Final_PlateletApheresisExtractionCost = Final_PlateletApheresisExtractionCost, 
                            Final_PlateletWholeExtractionCost = Final_PlateletWholeExtractionCost, 
                            scenarioset=scenarios, 
                            scenriotree=self.DemandScenarioTree, 
                            partialsolution=False)
        if Constants.Debug: print("------------Moving BACK from 'Solution' class (Constructor) to 'MIPSolver' Class ('CreateCRPSolution' Function))---------------")



        solution.GRBCost = objvalue
        solution.GRBGap = 0
        solution.GRBNrVariables = nrvariable
        solution.GRBNrConstraints = nrconstraints
        solution.GRBTime = solvetime

        return solution
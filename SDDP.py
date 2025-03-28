from Constants import Constants
from Solution import Solution
from SDDPStage import SDDPStage
from SDDPLastStage import SDDPLastStage
from ScenarioTree import ScenarioTree
from MIPSolver import MIPSolver
#from SDDPCallBack import SDDPCallBack
from ScenarioTreeNode import ScenarioTreeNode
from Scenario  import Scenario
import pickle
#from SDDPUserCutCallBack import SDDPUserCutCallBack
import numpy as np
import math
import time
import random
import copy
import gurobipy as gp
from gurobipy import *
import os
import itertools
import re
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
from minisom import MiniSom
from sklearn.cluster import AffinityPropagation
from sklearn.cluster import AgglomerativeClustering


# This class contains the attributes and methods allowing to define the SDDP algorithm.
class SDDP(object):

    #Fill the links predecessor and next of each object stage
    def LinkStages(self):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- LinkStages")

        previousstage = None
        if Constants.Debug: print("Starting to link stages...")

        for i, stage in enumerate(self.ForwardStage):
            stage.PreviousSDDPStage = previousstage
            if previousstage is not None:
                previousstage.NextSDDPStage = stage
            previousstage = stage
            if Constants.Debug: print(f"Linked Forward Stage {i}: PreviousSDDPStage set to {type(stage.PreviousSDDPStage)}, NextSDDPStage set to {type(stage.NextSDDPStage)}")

        for i, stage in enumerate(self.BackwardStage):
            stage.PreviousSDDPStage = previousstage
            if previousstage is not None:
                previousstage.NextSDDPStage = stage
            previousstage = stage
            if Constants.Debug: print(f"Linked Backward Stage {i}: PreviousSDDPStage set to {type(stage.PreviousSDDPStage)}, NextSDDPStage set to {type(stage.NextSDDPStage)}")

        curenttime = 0
        stageset = self.BackwardStage
        stageset = stageset + self.ForwardStage
        #list(set().union(self.BackwardStage, self.ForwardStage))
        for stage in stageset:

            if Constants.Debug: print("------------Moving from 'SDDP' Class (LinkStages) to 'SDDPStage' class (ComputeVariablePeriods)---------------")        
            stage.ComputeVariablePeriods()
            if Constants.Debug: print("------------Moving BACK from 'SDDPStage' class (ComputeVariablePeriods) to 'SDDP' Class (LinkStages)---------------")        

            if stage.IsFirstStage():
                stage.TimeDecisionStage = 0
            else:
                prevstage = stage.PreviousSDDPStage
                stage.TimeDecisionStage = prevstage.TimeDecisionStage + len(prevstage.RangePeriodApheresisAssignment)

            if stage.DecisionStage == 1: 
                stage.TimeObservationStage = 0
            if stage.DecisionStage >= 2:
                stage.TimeObservationStage = prevstage.TimeObservationStage + len(prevstage.RangePeriodPatientTransfer)

            if stage.TimeDecisionStage + max(len(stage.RangePeriodApheresisAssignment),1) <= 1:
                stage.FixedScenarioSet = [0]
            
            if Constants.Debug: print("------------Moving from 'SDDP' Class (LinkStages) to 'SDDPStage' class (ComputeVariableIndices)---------------")        
            stage.ComputeVariableIndices()
            if Constants.Debug: print("------------Moving BACK from 'SDDPStage' class (ComputeVariableIndices) to 'SDDP' Class (LinkStages)---------------")        

            if Constants.Debug: print("------------Moving from 'SDDP' Class (LinkStages) to 'SDDPStage' class (ComputeVariablePeriodsInLargeMIP)---------------")        
            stage.ComputeVariablePeriodsInLargeMIP()
            if Constants.Debug: print("------------Moving BACK from 'SDDPStage' class (ComputeVariablePeriodsInLargeMIP) to 'SDDP' Class (LinkStages)---------------")        

        self.AssociateDecisionAndStages()

    def AssociateDecisionAndStages(self):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- AssociateDecisionAndStages")

        if Constants.Debug: print("Initializing ForwardStageWithApheresisAssignmentDec...")
        self.ForwardStageWithApheresisAssignmentDec = [None for _ in range(len(self.Instance.TimeBucketSet))]
        for stage in self.ForwardStage:
            for tau in stage.RangePeriodApheresisAssignment:
                index = tau + stage.TimeDecisionStage
                self.ForwardStageWithApheresisAssignmentDec[index] = stage
        if Constants.Debug: print("Initializing ForwardStageWithTransshipmentHIDec...")
        self.ForwardStageWithTransshipmentHIDec = [None for _ in range(len(self.Instance.TimeBucketSet))]
        for stage in self.ForwardStage:
            for tau in stage.RangePeriodApheresisAssignment:
                index = tau + stage.TimeDecisionStage
                self.ForwardStageWithTransshipmentHIDec[index] = stage
        if Constants.Debug: print("Initializing ForwardStageWithTransshipmentIIDec...")
        self.ForwardStageWithTransshipmentIIDec = [None for _ in range(len(self.Instance.TimeBucketSet))]
        for stage in self.ForwardStage:
            for tau in stage.RangePeriodApheresisAssignment:
                index = tau + stage.TimeDecisionStage
                self.ForwardStageWithTransshipmentIIDec[index] = stage
        if Constants.Debug: print("Initializing ForwardStageWithTransshipmentHHDec...")
        self.ForwardStageWithTransshipmentHHDec = [None for _ in range(len(self.Instance.TimeBucketSet))]
        for stage in self.ForwardStage:
            for tau in stage.RangePeriodApheresisAssignment:
                index = tau + stage.TimeDecisionStage
                self.ForwardStageWithTransshipmentHHDec[index] = stage

        
        if Constants.Debug: print("\nInitializing ForwardStageWithPatientTransferDec...")
        self.ForwardStageWithPatientTransferDec = [None for t in self.Instance.TimeBucketSet]
        for stage in self.ForwardStage:
            #if Constants.Debug: print(f"Processing stage: {stage} with TimeObservationStage {stage.TimeObservationStage}")
            for tau in stage.RangePeriodPatientTransfer:
                #if Constants.Debug: print(f"Setting ForwardStageWithPatientTransferDec[{tau + stage.TimeObservationStage}] to {stage}")
                self.ForwardStageWithPatientTransferDec[tau + stage.TimeObservationStage] = stage
        if Constants.Debug: print("\nInitializing ForwardStageWithUnsatisfiedPatientsDec...")
        self.ForwardStageWithUnsatisfiedPatientsDec = [None for t in self.Instance.TimeBucketSet]
        for stage in self.ForwardStage:
            #if Constants.Debug: print(f"Processing stage: {stage} with TimeObservationStage {stage.TimeObservationStage}")
            for tau in stage.RangePeriodPatientTransfer:
                #if Constants.Debug: print(f"Setting ForwardStageWithUnsatisfiedPatientsDec[{tau + stage.TimeObservationStage}] to {stage}")
                self.ForwardStageWithUnsatisfiedPatientsDec[tau + stage.TimeObservationStage] = stage
        if Constants.Debug: print("\nInitializing ForwardStageWithPlateletInventoryDec...")
        self.ForwardStageWithPlateletInventoryDec = [None for t in self.Instance.TimeBucketSet]
        for stage in self.ForwardStage:
            #if Constants.Debug: print(f"Processing stage: {stage} with TimeObservationStage {stage.TimeObservationStage}")
            for tau in stage.RangePeriodPatientTransfer:
                #if Constants.Debug: print(f"Setting ForwardStageWithPlateletInventoryDec[{tau + stage.TimeObservationStage}] to {stage}")
                self.ForwardStageWithPlateletInventoryDec[tau + stage.TimeObservationStage] = stage
        if Constants.Debug: print("\nInitializing ForwardStageWithOutdatedPlateletDec...")
        self.ForwardStageWithOutdatedPlateletDec = [None for t in self.Instance.TimeBucketSet]
        for stage in self.ForwardStage:
            #if Constants.Debug: print(f"Processing stage: {stage} with TimeObservationStage {stage.TimeObservationStage}")
            for tau in stage.RangePeriodPatientTransfer:
                #if Constants.Debug: print(f"Setting ForwardStageWithOutdatedPlateletDec[{tau + stage.TimeObservationStage}] to {stage}")
                self.ForwardStageWithOutdatedPlateletDec[tau + stage.TimeObservationStage] = stage
        if Constants.Debug: print("\nInitializing ForwardStageWithServedPatientDec...")
        self.ForwardStageWithServedPatientDec = [None for t in self.Instance.TimeBucketSet]
        for stage in self.ForwardStage:
            #if Constants.Debug: print(f"Processing stage: {stage} with TimeObservationStage {stage.TimeObservationStage}")
            for tau in stage.RangePeriodPatientTransfer:
                #if Constants.Debug: print(f"Setting ForwardStageWithServedPatientDec[{tau + stage.TimeObservationStage}] to {stage}")
                self.ForwardStageWithServedPatientDec[tau + stage.TimeObservationStage] = stage
        if Constants.Debug: print("\nInitializing ForwardStageWithPatientPostponementDec...")
        self.ForwardStageWithPatientPostponementDec = [None for t in self.Instance.TimeBucketSet]
        for stage in self.ForwardStage:
            #if Constants.Debug: print(f"Processing stage: {stage} with TimeObservationStage {stage.TimeObservationStage}")
            for tau in stage.RangePeriodPatientTransfer:
                #if Constants.Debug: print(f"Setting ForwardStageWithPatientPostponementDec[{tau + stage.TimeObservationStage}] to {stage}")
                self.ForwardStageWithPatientPostponementDec[tau + stage.TimeObservationStage] = stage
        if Constants.Debug: print("\nInitializing ForwardStageWithPlateletApheresisExtractionDec...")
        self.ForwardStageWithPlateletApheresisExtractionDec = [None for t in self.Instance.TimeBucketSet]
        for stage in self.ForwardStage:
            #if Constants.Debug: print(f"Processing stage: {stage} with TimeObservationStage {stage.TimeObservationStage}")
            for tau in stage.RangePeriodPatientTransfer:
                #if Constants.Debug: print(f"Setting ForwardStageWithPlateletApheresisExtractionDec[{tau + stage.TimeObservationStage}] to {stage}")
                self.ForwardStageWithPlateletApheresisExtractionDec[tau + stage.TimeObservationStage] = stage
        if Constants.Debug: print("\nInitializing ForwardStageWithPlateletWholeExtractionDec...")
        self.ForwardStageWithPlateletWholeExtractionDec = [None for t in self.Instance.TimeBucketSet]
        for stage in self.ForwardStage:
            #if Constants.Debug: print(f"Processing stage: {stage} with TimeObservationStage {stage.TimeObservationStage}")
            for tau in stage.RangePeriodPatientTransfer:
                #if Constants.Debug: print(f"Setting ForwardStageWithPlateletWholeExtractionDec[{tau + stage.TimeObservationStage}] to {stage}")
                self.ForwardStageWithPlateletWholeExtractionDec[tau + stage.TimeObservationStage] = stage
        
    #Constructor
    def __init__(self, instance, testidentifier, treestructure):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- Constructor")
        self.Instance = instance
        self.TestIdentifier = testidentifier

        if self.TestIdentifier.SDDPSetting == "SingleCut":
            Constants.SDDPUseMultiCut = False

        if self.TestIdentifier.SDDPSetting == "NoStrongCut":
            Constants.GenerateStrongCut = False

        if self.TestIdentifier.SDDPSetting == "NoEVPI":
            Constants.SDDPUseEVPI = False

        nrstage = self.Instance.NrTimeBucket


        self.StagesSet = range(nrstage + 1)
        
        self.CurrentIteration = 0
        self.CurrentLowerBound = 0
        self.LowerBound_DeMatos = 0
        self.CurrentNrInSampleScenarioToTest = 0
        self.BestUpperBound = Constants.Infinity
        self.LastExpectedCostComputedOnAllScenario = Constants.Infinity
        self.SafeUpperBoundeOnAllScenario = Constants.Infinity
        self.CurrentBestSetups = []
        self.CurrentUpperBound = Constants.Infinity
        self.VarianceForwardPass = -1
        self.StartOfAlgorithm = time.time()
        self.CurrentSetOfTrialScenarios = []
        self.SetOfSAAScenarioDemand = []
        self.SetOfSAAScenarioHospitalCapacity = []
        self.SetOfSAAScenarioWholeDonor = []
        self.SetOfSAAScenarioApheresisDonor = []
        self.FullScenarioDemand = []
        self.FullScenarioHospitalCapacity  = []
        self.FullScenarioWholeDonor  = []
        self.FullScenarioApheresisDonor  = []
        self.FullScenarioProba = []     
        self.SAAScenarioNrSet = []
        self.TrialScenarioNrSet = []
        self.IsIterationWithConvergenceTest = False
        self.CurrentScenarioSeed = int(self.TestIdentifier.ScenarioSeed)
        self.StartingSeed = self.TestIdentifier.ScenarioSeed

        

        self.NrSAAScenarioInPeriod = treestructure[:] + [0] #for the last stage (T+1) which we will not have any demand!

        

        # First, generate the list of SDDPStage instances
        if Constants.Debug: print(f"------------Moving from 'SDDP' Class (Constructor) to 'SDDPStage' class (Constructor) for Forward Move---------------")        
        self.ForwardStage = [SDDPStage(owner=self, decisionstage=t, fixedscenarioset=[0], isforward=True, futurscenarioset=range(self.NrSAAScenarioInPeriod[t])) for t in range(nrstage)]
        if Constants.Debug: print("------------Moving BACK from 'SDDPStage' class (Constructor) to 'SDDP' Class (Constructor) for Forward Move---------------")        

        if Constants.Debug: print("------------\n\nMoving from 'SDDP' Class (Constructor) to 'SDDPLastStage' class (Constructor) for Forward Move---------------")        
        self.ForwardStage += [SDDPLastStage(owner=self, decisionstage=nrstage, fixedscenarioset=[0], isforward=True)]
        if Constants.Debug: print("------------Moving BACK from 'SDDPLastStage' class (Constructor) to 'SDDP' Class (Constructor) for Forward Move\n\n---------------")        


        backwardstagescenarioset = [[0]] + [range(self.NrSAAScenarioInPeriod[t-1]) for t in range(1,nrstage + 1)]
        
        if Constants.Debug: print("------------Moving from 'SDDP' Class (Constructor) to 'SDDPStage' class (Constructor) for Backward Move---------------")        
        self.BackwardStage = [SDDPStage(owner=self, decisionstage=t, fixedscenarioset=backwardstagescenarioset[t], forwardstage=self.ForwardStage[t], isforward=False, futurscenarioset=range(self.NrSAAScenarioInPeriod[t])) for t in range(nrstage)]
        if Constants.Debug: print("------------Moving BACK from 'SDDPStage' class (Constructor) to 'SDDP' Class (Constructor) for Backward Move---------------")        
        
        if Constants.Debug: print("------------\n\nMoving from 'SDDP' Class (Constructor) to 'SDDPLastStage' class (Constructor) for Backward Move---------------")
        self.BackwardStage += [SDDPLastStage(owner=self, decisionstage=nrstage, fixedscenarioset=backwardstagescenarioset[nrstage], forwardstage=self.ForwardStage[nrstage], isforward=False)]
        if Constants.Debug: print("------------Moving BACK from 'SDDPLastStage' class (Constructor) to 'SDDP' Class (Constructor) for Backward Move\n\n---------------")        

        #self.Print_Attributes()
        self.DefineBakwarMip = False
        self.LinkStages()

        self.CurrentNrScenario = self.TestIdentifier.NrScenarioForward # Constants.SDDPNrScenarioForwardPass

        self.SDDPNrScenarioTest = Constants.SDDPInitNrScenarioTest
        self.CurrentForwardSampleSize = self.TestIdentifier.NrScenarioForward
        
        if self.TestIdentifier.Method == Constants.NBD:
            if Constants.Debug: print("Constants.NestedBenders: ", Constants.NestedBenders)
            scenario_string = self.TestIdentifier.NrScenario
            if Constants.Debug: print("NrScenario: ", scenario_string)
            match = re.search(r'all(\d+)', scenario_string)
            if match:
                # This will extract '41' if scenario_string is 'all41'
                number = int(match.group(1))
                if Constants.Debug: print("Extracted Number: ", number)

                # Calculating CurrentNrScenario as number to the power of NrTimeBucket
                self.CurrentNrScenario = number ** self.Instance.NrTimeBucket
                if Constants.Debug: print("CurrentNrScenario: ", self.CurrentNrScenario)
                self.CurrentForwardSampleSize = number ** self.Instance.NrTimeBucket
                if Constants.Debug: print("CurrentForwardSampleSize: ", self.CurrentForwardSampleSize)
            else:
                if Constants.Debug: print("No valid number found in scenario string")
        
        self.CurrentBigM = []
        self.ScenarioGenerationMethod = self.TestIdentifier.ScenarioSampling
        self.CurrentExpvalueUpperBound = Constants.Infinity
        self.EvaluationMode = False
        self.UseCorePoint = False
        self.GenerateStrongCut = Constants.GenerateStrongCut
        self.TraceFile = None
        #self.TraceFileName = "./Temp/SDDPtrace_%s_.txt" % (self.TestIdentifier.GetAsString())
        self.TraceFileName = "./Temp/SDDPtrace_%s.txt" % (self.TestIdentifier.GetAsString())
        self.HeuristicACFEstablishmentValue = []
        self.HeuristicVehicleAssignmentValue = []
        self.LastIterationWithTest = 0
        self.IterationMultiplier = 0

        self.TimeBackward = 0
        self.TimeForwardTest = 0
        self.TimeForwardNonTest = 0

        self.NrIterationWithoutLBImprovment = 0
        self.SingleTreeGRBGap = -1

        self.CurrentACFEstablishments = []
        self.CurrentVehicleAssignments = []

        self.HasFixed_ACFEstablishmentVar = False
        self.HasFixed_VehicleAssignmentVar = False

        self.IterationACFEstablishmentFixed = 0
        self.IterationVehicleAssignmentFixed = 0
        self.CurrentToleranceForSameLB = 0.00001

        self.previousPassCost_NBD = float('inf')

    #This function make the forward pass of SDDP
    def ForwardPass(self, ignorefirststage=False):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- ForwardPass")
        start = time.time()
        if Constants.Debug: print(" Start forward pass")
        for t in self.StagesSet:
            if not ignorefirststage or t >= 1:
                if Constants.SDDPCleanCuts \
                    and self.CurrentIteration > 0 \
                    and self.CurrentIteration % 100 == 0 \
                    and (t >= 1 or not Constants.SDDPRunSingleTree):
                        self.ForwardStage[t].CleanCuts()
                        self.BackwardStage[t].CleanCuts()
                        if Constants.Debug: print("Clean cut Should not be used")

                #Run the forward pass at each stage t

                if Constants.Debug: print("------------Moving from 'SDDP' Class (ForwardPass) to 'SDDPStage' class (RunForwardPassMIP)---------------")        
                self.ForwardStage[t].RunForwardPassMIP()
                if Constants.Debug: print("------------Moving BACK from 'SDDPStage' class (RunForwardPassMIP) to 'SDDP' Class (ForwardPass)---------------")        

        end = time.time()
        duration = end-start

        if self.IsIterationWithConvergenceTest:
            self.TimeForwardTest += duration
        else:
            self.TimeForwardNonTest += duration

    #This function make the backward pass of SDDP
    def BackwardPass(self, returnfirststagecut=False):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- BackwardPass")

        start = time.time()
        
        if Constants.Debug: print("Start Backward pass")

        self.UseCorePoint = self.GenerateStrongCut
        if Constants.Debug: print("UseCorePoint set to:", self.UseCorePoint)

        for t in self.StagesSet:
            if self.GenerateStrongCut:
                if Constants.Debug: print("Updating Core Point for stage:", t)
                self.ForwardStage[t].UpdateCorePoint()

        self.ConsideredTrialForBackward = self.TrialScenarioNrSet
        if Constants.Debug: print("Considered Trials for Backward Pass:", self.ConsideredTrialForBackward)


        if not self.DefineBakwarMip:
            for stage in self.StagesSet:
                if not self.BackwardStage[stage].IsFirstStage():
                    if Constants.Debug: print("Defining MIP for Backward Stage:", stage)
                    self.BackwardStage[stage].CurrentTrialNr = 0
                    self.BackwardStage[stage].DefineMIP()
            self.DefineBakwarMip = True
            if Constants.Debug: print("Backward MIPs defined.")

        if Constants.SDDPPrintDebugLPFiles:  # or self.IsFirstStage():
            for stage in self.StagesSet:
                # Assuming self.BackwardStage[stage] is a Gurobi Model
                self.BackwardStage[stage].GurobiModel.write(
                    "./Temp/Backwardstage_%d.lp" % (self.BackwardStage[stage].DecisionStage))


        #generate a cut for each trial solution
        for t in reversed(range(1, len(self.StagesSet))):
            #Build or update the MIP of stage t
            returncutinsteadofadd = (returnfirststagecut and t == 1)
            if Constants.Debug: print(f"Generating cut for stage {t}, returncutinsteadofadd: {returncutinsteadofadd}")
            firststagecuts, avgsubprobcosts = self.BackwardStage[t].GernerateCut(returncutinsteadofadd)
            if Constants.Debug: print(f"Generated cuts for stage {t}. First stage cuts: {firststagecuts}, Avg Subprob Costs: {avgsubprobcosts}")


        self.UseCorePoint = False

        end = time.time()
        self.TimeBackward += (end - start)

        if returnfirststagecut:
            return firststagecuts, avgsubprobcosts
            
    def Print_Attributes(self):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- (Print_Attributes)")
        if Constants.Debug: print("\nSDDP Class Attributes:")
        for attr, value in self.__dict__.items():
            if Constants.Debug: print(f"{attr}: {value}")    

    def GenerateScenarios(self, nrscenario, average = False):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- (GenerateScenarios)")

        if Constants.Debug: print("Start generation of new scenarios")

        #Generate a scenario tree
        treestructure = [1] * (self.Instance.NrTimeBucket - 1) + [0]
        
        if Constants.Debug: print("------------Moving from 'SDDP' Class (GenerateScenarios) to 'ScenarioTree' class (Constructor)---------------")        
        scenariotree = ScenarioTree(self.Instance, treestructure, self.CurrentScenarioSeed,
                                    scenariogenerationmethod=self.ScenarioGenerationMethod,
                                    averagescenariotree=average, model=Constants.Two_Stage)
        if Constants.Debug: print("------------Moving BACK from 'Scenario' class (Constructor) to 'SDDP' Class (GenerateScenarios)---------------")        



        #Get the set of scenarios
        if Constants.Debug: print("------------Moving from 'SDDP' Class (GenerateScenarios) to 'ScenarioTree' class (GetAllScenarios)---------------")        
        scenarioset = scenariotree.GetAllScenarios(computeindex=False)
        if Constants.Debug: print("------------Moving BACK from 'ScenarioTree' class (GetAllScenarios) to 'SDDP' Class (GenerateScenarios)---------------")        

        if Constants.Debug:
            for i, scenario in enumerate(scenarioset):
                print(f"Scenario {i+1}:")
                print(f"Probability: {scenario.Probability}")
                print("Demands:")
                for demand in scenario.Demands:
                    print(demand)
                print("--------------------------------")

        return scenarioset

    def GetACFEstablishmentFixedEarlier(self, acf, scenario):

        if self.UseCorePoint:
            result = self.ForwardStage[0].CorePointACFEstablishmentValues[scenario][acf]
            if Constants.Debug: print("Result Core: ", result)
        else:
            result = self.ForwardStage[0].ACFEstablishmentValues[scenario][acf]
            if Constants.Debug: print("Result No Core: ", result)

        return result
    
    def GetVehicleAssignmentFixedEarlier(self, vehicle, acf, scenario):

        if self.UseCorePoint:
            result = self.ForwardStage[0].CorePointVehicleAssignmentValues[scenario][vehicle][acf]
        else:
            result = self.ForwardStage[0].VehicleAssignmentValues[scenario][vehicle][acf]

        return result
    
    def GetPatientTransferFixedEarlier(self, j, c, l, u, m, time, scenario):

        forwardstage = self.ForwardStageWithPatientTransferDec[time]
        t = forwardstage.GetTimeIndexForPatientTransfer(time)
        
        if self.UseCorePoint and forwardstage.IsFirstStage():
            result = forwardstage.CorePointPatientTransferValues[scenario][t][j][c][l][u][m]
        else:
            result = forwardstage.PatientTransferValues[scenario][t][j][c][l][u][m]
            
        return result
    
    #This function return the quanity of TransshipmentHH var to send at time which has been decided at an earlier stage!
    def GetTransshipmentHHFixedEarlier(self, cprime, r, h, hprime, time, scenario):

        forwardstage = self.ForwardStageWithTransshipmentHHDec[time]
        t = forwardstage.GetTimeIndexForTransshipmentHH(time)
        
        if self.UseCorePoint and forwardstage.IsFirstStage():
            result = forwardstage.CorePointTransshipmentHHValues[scenario][t][cprime][r][h][hprime]
        else:
            result = forwardstage.TransshipmentHHValues[scenario][t][cprime][r][h][hprime]
            
        return result
    
    #This function return the quanity of TransshipmentII var to send at time which has been decided at an earlier stage!
    def GetTransshipmentIIFixedEarlier(self, cprime, r, i, iprime, time, scenario):

        forwardstage = self.ForwardStageWithTransshipmentIIDec[time]
        t = forwardstage.GetTimeIndexForTransshipmentII(time)
        
        if self.UseCorePoint and forwardstage.IsFirstStage():
            result = forwardstage.CorePointTransshipmentIIValues[scenario][t][cprime][r][i][iprime]
        else:
            result = forwardstage.TransshipmentIIValues[scenario][t][cprime][r][i][iprime]
            
        return result
    
    def GetTransshipmentHIFixedEarlier(self, cprime, r, h, i, time, scenario):

        forwardstage = self.ForwardStageWithTransshipmentHIDec[time]
        t = forwardstage.GetTimeIndexForTransshipmentHI(time)
        
        if self.UseCorePoint and forwardstage.IsFirstStage():
            result = forwardstage.CorePointTransshipmentHIValues[scenario][t][cprime][r][h][i]
        else:
            result = forwardstage.TransshipmentHIValues[scenario][t][cprime][r][h][i]
            
        return result
    
    #This function return the quanity of TransshipmentHI var to send at time which has been decided at an earlier stage!
    def GetTransshipmentHIFixedEarlier_withSumOnI(self, cprime, r, h, time, scenario):

        forwardstage = self.ForwardStageWithTransshipmentHIDec[time]
        t = forwardstage.GetTimeIndexForTransshipmentHI(time)
        
        if self.UseCorePoint and forwardstage.IsFirstStage():
            sum_value = 0
            for i in range(len(self.Instance.ACFPPointSet)): 
                sum_value += forwardstage.CorePointTransshipmentHIValues[scenario][t][cprime][r][h][i]
            result = sum_value
        else:
            sum_value = 0
            for i in range(len(self.Instance.ACFPPointSet)): 
                sum_value += forwardstage.TransshipmentHIValues[scenario][t][cprime][r][h][i]
            result = sum_value
            
        return result
    
    #This function return the quanity of TransshipmentHI var to send at time which has been decided at an earlier stage!
    def GetTransshipmentHIFixedEarlier_withSumOnH(self, cprime, r, i, time, scenario):

        forwardstage = self.ForwardStageWithTransshipmentHIDec[time]
        t = forwardstage.GetTimeIndexForTransshipmentHI(time)

        #if Constants.Debug: print("forwardstage.TransshipmentHIValues: ", forwardstage.TransshipmentHIValues)
        
        if self.UseCorePoint and forwardstage.IsFirstStage():
            sum_value = 0
            for h in range(len(self.Instance.HospitalSet)): 
                sum_value += forwardstage.CorePointTransshipmentHIValues[scenario][t][cprime][r][h][i]
            result = sum_value
        else:
            sum_value = 0
            for h in range(len(self.Instance.HospitalSet)): 
                sum_value += forwardstage.TransshipmentHIValues[scenario][t][cprime][r][h][i]
            result = sum_value
            
        return result
    
    #This function return the number of Apheresis machines to be assigned at time which has been decided at an earlier stage!
    def GetApheresisAssignmentFixedEarlier(self, i, time, scenario):

        forwardstage = self.ForwardStageWithApheresisAssignmentDec[time]
        t = forwardstage.GetTimeIndexForApheresisAssignment(time)
        
        if self.UseCorePoint and forwardstage.IsFirstStage():
            result = forwardstage.CorePointApheresisAssignmentValues[scenario][t][i]
        else:
            result = forwardstage.ApheresisAssignmentValues[scenario][t][i]
            
        return result
    
    #This function return the quanity of TransshipmentHH var to send at time which has been decided at an earlier stage!
    def GetTransshipmentHHFixedEarlier_withSumOnHprime(self, cprime, r, h, time, scenario):

        forwardstage = self.ForwardStageWithTransshipmentHHDec[time]
        t = forwardstage.GetTimeIndexForTransshipmentHH(time)
        
        if self.UseCorePoint and forwardstage.IsFirstStage():
            sum_value = 0
            for hprime in range(len(self.Instance.HospitalSet)): 
                if hprime != h:
                    sum_value += forwardstage.CorePointTransshipmentHHValues[scenario][t][cprime][r][hprime][h]
                    sum_value -= forwardstage.CorePointTransshipmentHHValues[scenario][t][cprime][r][h][hprime]
            result = sum_value
        else:
            sum_value = 0
            for hprime in range(len(self.Instance.HospitalSet)): 
                if hprime != h:
                    sum_value += forwardstage.TransshipmentHHValues[scenario][t][cprime][r][hprime][h]
                    sum_value -= forwardstage.TransshipmentHHValues[scenario][t][cprime][r][h][hprime]
            result = sum_value

        return result
    
    #This function return the quanity of TransshipmentII var to send at time which has been decided at an earlier stage!
    def GetTransshipmentIIFixedEarlier_withSumOnIprime(self, cprime, r, i, time, scenario):

        forwardstage = self.ForwardStageWithTransshipmentIIDec[time]
        t = forwardstage.GetTimeIndexForTransshipmentII(time)
        
        if self.UseCorePoint and forwardstage.IsFirstStage():
            sum_value = 0
            for iprime in range(len(self.Instance.ACFPPointSet)): 
                sum_value += forwardstage.CorePointTransshipmentIIValues[scenario][t][cprime][r][iprime][i]
                sum_value -= forwardstage.CorePointTransshipmentIIValues[scenario][t][cprime][r][i][iprime]
            result = sum_value
        else:
            sum_value = 0
            for iprime in range(len(self.Instance.ACFPPointSet)): 
                sum_value += forwardstage.TransshipmentIIValues[scenario][t][cprime][r][iprime][i]
                sum_value -= forwardstage.TransshipmentIIValues[scenario][t][cprime][r][i][iprime]
            result = sum_value

        return result
            
    def GetOutdatedPlateletFixedEarlier(self, u, time, scenario):

        forwardstage = self.ForwardStageWithOutdatedPlateletDec[time]
        t = forwardstage.GetTimeIndexForOutdatedPlatelet(time)

        if self.UseCorePoint and forwardstage.IsFirstStage():
            result = forwardstage.CorePointOutdatedPlateletValues[scenario][t][u]
        else:
            result = forwardstage.OutdatedPlateletValues[scenario][t][u]

        return result
    
    def GetServedPatientFixedEarlier(self, j, cprime, c, r, u, time, scenario):

        forwardstage = self.ForwardStageWithServedPatientDec[time]
        t = forwardstage.GetTimeIndexForServedPatient(time)

        if self.UseCorePoint and forwardstage.IsFirstStage():
            result = forwardstage.CorePointServedPatientValues[scenario][t][j][cprime][c][r][u]
        else:
            result = forwardstage.ServedPatientValues[scenario][t][j][cprime][c][r][u]

        return result
        
    def GetPLTInventoryFixedEarlier(self, c, r, u, time, scenario):

        forwardstage = self.ForwardStageWithPlateletInventoryDec[time]
        t = forwardstage.GetTimeIndexForPlateletInventory(time)

        if time == -1:      
            result = self.Instance.Initial_Platelet_Inventory[cprime][r][u]      #Initial Inventory 
        else:
            if self.UseCorePoint and forwardstage.IsFirstStage():
                result = forwardstage.CorePointPlateletInventoryValues[scenario][t][c][r][u]
            else:
                result = forwardstage.PlateletInventoryValues[scenario][t][c][r][u]           

        return result
    
    # This function return the Inventory of Platelet  at time which has been decided at an earlier stage
    def GetHospitalPLTInventoryFixedEarlier(self, cprime, r, h, time, scenario):

        if time == -1:      
            result = self.Instance.Initial_Platelet_Inventory[cprime][r][h]      #Initial Inventory 
        else:
            if r == 0:
                result = 0                                                      #In period 2 onward, we can not have intital inventory of age 0 from previous period!
            if r != 0:
                forwardstage = self.ForwardStageWithPlateletInventoryDec[time]
                t = forwardstage.GetTimeIndexForPlateletInventory(time)

                if self.UseCorePoint and forwardstage.IsFirstStage():
                    result = forwardstage.CorePointPlateletInventoryValues[scenario][t][cprime][r-1][h]
                else:
                    result = forwardstage.PlateletInventoryValues[scenario][t][cprime][r-1][h]
        return result
    
    # This function return the production of whole blood Platelet  at time which has been decided at an earlier stage
    def GetPIWholePLTProductionFixedEarlier(self, cprime, h, time, scenario):
        forwardstage1 = self.ForwardStageWithPlateletWholeExtractionDec[0]
        if Constants.Debug: print("PlateletWholeExtractionValues: ", forwardstage1.PlateletWholeExtractionValues)
        forwardstage2 = self.ForwardStageWithPlateletWholeExtractionDec[1]
        if Constants.Debug: print("PlateletWholeExtractionValues: ", forwardstage2.PlateletWholeExtractionValues)
        forwardstage3 = self.ForwardStageWithPlateletWholeExtractionDec[2]
        if Constants.Debug: print("PlateletWholeExtractionValues: ", forwardstage3.PlateletWholeExtractionValues)
        time = time - self.Instance.Whole_Blood_Production_Time
        forwardstage = self.ForwardStageWithPlateletWholeExtractionDec[time]
        t = forwardstage.GetTimeIndexForPlateletWholeExtraction(time)
        if Constants.Debug: print("t: ", forwardstage.PlateletWholeExtractionValues)
        if Constants.Debug: print("PlateletWholeExtractionValues: ", forwardstage.PlateletWholeExtractionValues)

        if self.UseCorePoint and forwardstage.IsFirstStage():
            result = forwardstage.CorePointPlateletWholeExtractionValues[scenario][t][cprime][h]
        else:
            if Constants.Debug: print(f"scenario:{scenario}, t:{t}, c':{cprime}, h:{h}")

            result = forwardstage.PlateletWholeExtractionValues[scenario][t][cprime][h]

        return result
    
    # This function return the production of whole blood Platelet  at time which has been decided at an earlier stage
    def GetWholePLTProductionFixedEarlier(self, cprime, h, time, scenario):

        forwardstage = self.ForwardStageWithPlateletWholeExtractionDec[time]
        t = forwardstage.GetTimeIndexForPlateletWholeExtraction(time)
        if Constants.Debug: print("t: ", forwardstage.PlateletWholeExtractionValues)
        if Constants.Debug: print("PlateletWholeExtractionValues: ", forwardstage.PlateletWholeExtractionValues)

        if self.UseCorePoint and forwardstage.IsFirstStage():
            result = forwardstage.CorePointPlateletWholeExtractionValues[scenario][t][cprime][h]
        else:
            if Constants.Debug: print(f"scenario:{scenario}, t:{t}, c':{cprime}, h:{h}")

            result = forwardstage.PlateletWholeExtractionValues[scenario][t][cprime][h]

        return result
    
    # This function return the Inventory of Platelet  at time which has been decided at an earlier stage
    def GetACFPLTInventoryFixedEarlier(self, cprime, r, i, time, scenario):
         
        # Note that here, we do not have initial inventory. In fact, we have it, but since it relates to x_bar, we determine in later in ''!
        forwardstage = self.ForwardStageWithPlateletInventoryDec[time]
        t = forwardstage.GetTimeIndexForPlateletInventory(time)

        if self.UseCorePoint and forwardstage.IsFirstStage():
            result = forwardstage.CorePointPlateletInventoryValues[scenario][t][cprime][r-1][self.Instance.NrHospitals + i]
        else:
            result = forwardstage.PlateletInventoryValues[scenario][t][cprime][r-1][self.Instance.NrHospitals + i]

        return result
    
    # This function return the number of unsatisfied patients  at time which has been decided at an earlier stage
    def GetUnsatisfiedPatientFixedEarlier(self, injury, bloodgp, demand, time, scenario):

        forwardstage = self.ForwardStageWithUnsatisfiedPatientsDec[time]
        t = forwardstage.GetTimeIndexForUnsatisfiedPatients(time)

        if self.UseCorePoint and forwardstage.IsFirstStage():
            result = forwardstage.CorePointUnsatisfiedPatientsValues[scenario][t][injury][bloodgp][demand]
        else:
            result = forwardstage.UnsatisfiedPatientsValues[scenario][t][injury][bloodgp][demand]

        return result
    
    # This function return the number of unserved (postponned) patients  at time which has been decided at an earlier stage
    def GetUnservedPatientFixedEarlier(self, injury, bloodgp, facility, time, scenario):

        forwardstage = self.ForwardStageWithPatientPostponementDec[time]
        t = forwardstage.GetTimeIndexForPatientPostponement(time)

        if self.UseCorePoint and forwardstage.IsFirstStage():
            result = forwardstage.CorePointPatientPostponementValues[scenario][t][injury][bloodgp][facility]
        else:
            if Constants.Debug: print(f"forwardstage.PatientPostponementValues[w:{scenario}][t:{t}][j:{injury}][c:{bloodgp}][u:{facility}]: ", forwardstage.PatientPostponementValues[scenario][t][injury][bloodgp][facility])
            result = forwardstage.PatientPostponementValues[scenario][t][injury][bloodgp][facility]

        return result
    
    def GetPlateletApheresisExtractionFixedEarlier(self, bloodgp, facility, time, scenario):

        forwardstage = self.ForwardStageWithPlateletApheresisExtractionDec[time]
        t = forwardstage.GetTimeIndexForPlateletApheresisExtraction(time)

        if self.UseCorePoint and forwardstage.IsFirstStage():
            result = forwardstage.CorePointPlateletApheresisExtractionValues[scenario][t][bloodgp][facility]
        else:
            result = forwardstage.PlateletApheresisExtractionValues[scenario][t][bloodgp][facility]

        return result
    
    def GetPlateletWholeExtractionFixedEarlier(self, bloodgp, hospital, time, scenario):

        forwardstage = self.ForwardStageWithPlateletWholeExtractionDec[time]
        t = forwardstage.GetTimeIndexForPlateletWholeExtraction(time)

        if self.UseCorePoint and forwardstage.IsFirstStage():
            result = forwardstage.CorePointPlateletWholeExtractionValues[scenario][t][bloodgp][hospital]
        else:
            result = forwardstage.PlateletWholeExtractionValues[scenario][t][bloodgp][hospital]

        return result
               
    #This funciton update the lower bound based on the last forward pass
    def UpdateLowerBound(self):
        if Constants.Debug: print("\nWe are in 'SDDP' Class -- (UpdateLowerBound)")
        result = self.ForwardStage[0].PassCostWithAproxCosttoGo
        if Constants.Debug: print(f"New Lower Bound (result): {result}")

        if self.CurrentLowerBound > 0 and abs(result - self.CurrentLowerBound) <= self.CurrentToleranceForSameLB:
            self.NrIterationWithoutLBImprovment += 1
        else:
            self.NrIterationWithoutLBImprovment = 0

        if Constants.Debug: print(f"Number of Iterations Without Lower Bound Improvement: {self.NrIterationWithoutLBImprovment}")

        self.CurrentLowerBound = result
        if Constants.Debug: print(f"Updated Current Lower Bound: {self.CurrentLowerBound}")

    #This funciton update the upper bound based on the last forward pass
    def UpdateUpperBound_SDDP(self):
        if Constants.Debug: print("\nWe are in 'SDDP' Class -- (UpdateUpperBound_SDDP)")
        
        # Identify the last stage
        laststage = len(self.StagesSet) - 1
        if Constants.Debug: print("laststage: ", laststage)

        expectedupperbound = self.ForwardStage[laststage].PassCost
        if Constants.Debug: print(f"Expected Upper Bound: {expectedupperbound}")

        ###############################################
        # Initialize variables to compute statistics
        sum_cost = 0
        min_cost = float('inf')
        max_cost = float('-inf')
        # Print PartialCostPerScenario and compute statistics
        for w in self.TrialScenarioNrSet:
            cost = self.ForwardStage[laststage].PartialCostPerScenario[w]
            if Constants.Debug: print(f"PartialCostPerScenario[{w}]: {cost}")
            sum_cost += cost
            if cost < min_cost:
                min_cost = cost
            if cost > max_cost:
                max_cost = cost
        # Print statistics
        if Constants.Debug: print(f"Minimum PartialCostPerScenario (Min In-Sample Upper Bound): {min_cost}")
        if Constants.Debug: print(f"Maximum PartialCostPerScenario (Max In-Sample Upper Bound): {max_cost}")
        ###############################################
        
        # Calculate variance
        variance = sum(math.pow(expectedupperbound - self.ForwardStage[laststage].PartialCostPerScenario[w], 2) for w in self.TrialScenarioNrSet) / self.CurrentNrScenario
        if Constants.Debug: print(f"Variance: {variance}")
        
        # Update the current upper bound with confidence interval adjustments
        self.CurrentUpperBound = expectedupperbound - 1.96 * math.sqrt(variance / self.CurrentNrScenario)
        if Constants.Debug: print(f"Current Upper Bound: {self.CurrentUpperBound}")
        
        # Set the expected value of the upper bound
        self.CurrentExpvalueUpperBound = expectedupperbound
        if Constants.Debug: print(f"Current Expected Value Upper Bound: {self.CurrentExpvalueUpperBound}")
        
        # Calculate the safe upper bound
        self.CurrentSafeUpperBound = expectedupperbound + 1.96 * math.sqrt(variance / self.CurrentNrScenario)
        if Constants.Debug: print(f"Current Safe Upper Bound: {self.CurrentSafeUpperBound}")
        
        # Record the variance of the forward pass
        self.VarianceForwardPass = variance
        if Constants.Debug: print(f"Variance of the Forward Pass: {self.VarianceForwardPass}")

    def UpdateUpperBound_NBD(self):
        if Constants.Debug: print("\nWe are in 'NBD' Class -- (UpdateUpperBound_NBD)")
            
        # Identify the last stage
        laststage = len(self.StagesSet) - 1
        if Constants.Debug: print("laststage: ", laststage)

        currentPassCost = self.ForwardStage[laststage].PassCost
        if Constants.Debug: print(f"Current Pass Cost: {currentPassCost}")
        if Constants.Debug: print("self.previousPassCost_NBD: ", self.previousPassCost_NBD)
        # Compare with previous pass cost to decide whether to update UB
        if currentPassCost < self.previousPassCost_NBD:
            if Constants.Debug: print("Updating UB because current pass cost is lower than previous.")
            expectedupperbound = currentPassCost
            if Constants.Debug: print(f"Expected Upper Bound updated to: {expectedupperbound}")
            
            ###############################################
            # Initialize variables to compute statistics
            sum_cost = 0
            min_cost = float('inf')
            max_cost = float('-inf')
            # Print PartialCostPerScenario and compute statistics
            for w in self.TrialScenarioNrSet:
                cost = self.ForwardStage[laststage].PartialCostPerScenario[w]
                if Constants.Debug: print(f"PartialCostPerScenario[{w}]: {cost}")
                sum_cost += cost
                if cost < min_cost:
                    min_cost = cost
                if cost > max_cost:
                    max_cost = cost
            # Print statistics
            if Constants.Debug: print(f"Minimum PartialCostPerScenario (Min In-Sample Upper Bound): {min_cost}")
            if Constants.Debug: print(f"Maximum PartialCostPerScenario (Max In-Sample Upper Bound): {max_cost}")
            ###############################################
               
            # Calculate variance
            variance = sum(math.pow(expectedupperbound - self.ForwardStage[laststage].PartialCostPerScenario[w], 2) for w in self.TrialScenarioNrSet) / self.CurrentNrScenario
            if Constants.Debug: print(f"Variance: {variance}")
            
            # Update the current upper bound
            self.CurrentUpperBound = expectedupperbound
            if Constants.Debug: print(f"Current Upper Bound: {self.CurrentUpperBound}")
            
            # Set the expected value of the upper bound
            self.CurrentExpvalueUpperBound = expectedupperbound
            if Constants.Debug: print(f"Current Expected Value Upper Bound: {self.CurrentExpvalueUpperBound}")
            
            # Calculate the safe upper bound
            self.CurrentSafeUpperBound = expectedupperbound
            if Constants.Debug: print(f"Current Safe Upper Bound: {self.CurrentSafeUpperBound}")
                        
            # Record the variance of the forward pass
            self.VarianceForwardPass = variance
            if Constants.Debug: print(f"Variance of the Forward Pass: {self.VarianceForwardPass}")
            
            # Update the previous Pass Cost to the current one for the next iteration
            self.previousPassCost_NBD = currentPassCost
        else:
            if Constants.Debug: print("Not updating UB because current pass cost is not lower than previous.")
        
    #This function generates the scenarios for the current iteration of the algorithm
    def GenerateTrialScenarios(self):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- (GenerateTrialScenarios)")

        if self.IsIterationWithConvergenceTest:
            self.CurrentNrScenario = self.SDDPNrScenarioTest
        else:
            self.CurrentNrScenario = self.CurrentForwardSampleSize

        if Constants.Debug: print("CurrentNrScenario: ",self.CurrentNrScenario)

        if Constants.SDDPForwardPassInSAATree:
            self.CurrentSetOfTrialScenarios =[]
            if Constants.NestedBenders:
                if Constants.Debug: print("We are in NBD")
                # Generate all combinations of scenarios across stages
                indices = [range(self.NrSAAScenarioInPeriod[stage.TimeObservationStage]) for stage in self.ForwardStage if stage.TimeObservationStage >= 0]
                all_combinations = list(itertools.product(*indices))
                if Constants.Debug: print("all_combinations: ",all_combinations)
                for combo in all_combinations:
                    selected = self.CreateScenarioFromAllPossibleScenarioCombinations(combo)
                    self.CurrentSetOfTrialScenarios.append(selected)
            else:
                if Constants.Debug: print("We are in SDDP")
                for w in range(self.CurrentNrScenario):
                    selected = self.CreateRandomScenarioFromSAA()
                    self.CurrentSetOfTrialScenarios.append(selected)

            if self.IsIterationWithConvergenceTest and Constants.MIPBasedOnSymetricTree and not self.TestIdentifier.SDDPSetting == "EvalOutSample":
                #self.CurrentSetOfTrialScenarios = self.CreateAllScenarioFromSAA()
                self.CurrentSetOfTrialScenarios = self.CreateSubsetScenarioFromSAA(percentage = Constants.PercentageInSampleScnearioTest)      #If you set percentage to 100, it creates the all possible in-sample scenarios to test the final solution of the algorithm.

            self.TrialScenarioNrSet = range(len(self.CurrentSetOfTrialScenarios))
            self.CurrentNrScenario = len(self.CurrentSetOfTrialScenarios)
        else:
            self.CurrentSetOfTrialScenarios = self.GenerateScenarios(self.CurrentNrScenario, average=Constants.SDDPDebugSolveAverage)
            self.TrialScenarioNrSet = range(len(self.CurrentSetOfTrialScenarios))
            self.CurrentNrScenario = len(self.CurrentSetOfTrialScenarios)
        
        #Modify the number of scenario at each stage
        for stage in self.StagesSet:
            if Constants.Debug: print("------------Moving from 'SDDP' Class (GenerateTrialScenarios) to 'SDDPStage' class (SetNrTrialScenario)---------------")        
            self.ForwardStage[stage].SetNrTrialScenario(self.CurrentNrScenario)
            if Constants.Debug: print("------------Moving BACK 'SDDPStage' class (SetNrTrialScenario) to 'SDDP' Class (GenerateTrialScenarios---------------")        

            self.ForwardStage[stage].FixedScenarioPobability = [1]
            self.BackwardStage[stage].SAAStageCostPerScenarioWithoutCostoGopertrial = [0 for w in self.TrialScenarioNrSet]
            self.BackwardStage[stage].CurrentTrialNr = 0

        self.CurrentScenarioSeed = self.CurrentScenarioSeed + 1
        if Constants.Debug: print("self.CurrentScenarioSeed: ",self.CurrentScenarioSeed)

    def CreateScenarioFromAllPossibleScenarioCombinations(self, combination):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- (CreateScenarioFromAllPossibleScenarioCombinations)")

        w = Scenario(proabability=1)

        w.Demands = [[] for t in self.Instance.TimeBucketSet]
        w.HospitalCaps = [[] for t in self.Instance.TimeBucketSet]
        w.WholeDonors = [[] for t in self.Instance.TimeBucketSet]
        w.ApheresisDonors = [[] for t in self.Instance.TimeBucketSet]

        for s in range(len(self.StagesSet)):
            if self.ForwardStage[s].TimeObservationStage >= 0:
                x = combination[s-1]  # Selecting index from combination instead of random
            else:
                x = 0  # Default to 0 if no valid observation stage

            for tau in self.ForwardStage[s].RangePeriodPatientTransfer:
                t = self.ForwardStage[s].TimeObservationStage + tau
                w.Demands[t] = copy.deepcopy(self.SetOfSAAScenarioDemand[t][x]) if self.SetOfSAAScenarioDemand[t] else []
                w.HospitalCaps[t] = copy.deepcopy(self.SetOfSAAScenarioHospitalCapacity[t][x]) if self.SetOfSAAScenarioHospitalCapacity[t] else []
                w.WholeDonors[t] = copy.deepcopy(self.SetOfSAAScenarioWholeDonor[t][x]) if self.SetOfSAAScenarioWholeDonor[t] else []
                w.ApheresisDonors[t] = copy.deepcopy(self.SetOfSAAScenarioApheresisDonor[t][x]) if self.SetOfSAAScenarioApheresisDonor[t] else []

                w.Probability *= self.Saascenarioproba[t][x] if self.Saascenarioproba[t] else 1.0
                # if Constants.Debug: print(f"w.Demands[{t}]: ", w.Demands[t])
                # if Constants.Debug: print(f"w.HospitalCaps[{t}]: ", w.HospitalCaps[t])
                # if Constants.Debug: print(f"w.WholeDonors[{t}]: ", w.WholeDonors[t])
                # if Constants.Debug: print(f"w.ApheresisDonors[{t}]: ", w.ApheresisDonors[t])
                # if Constants.Debug: print(f"w.Probability: ", w.Probability)

        if Constants.Debug:
            print("\nw.Demands: ", w.Demands)
            print("\nw.HospitalCaps: ", w.HospitalCaps)
            print("\nw.WholeDonors: ", w.WholeDonors)
            print("\nw.ApheresisDonors: ", w.ApheresisDonors)

        return w
    
    def CreateRandomScenarioFromSAA(self):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- (CreateRandomScenarioFromSAA)")

        if Constants.Debug: print("------------Moving from 'SDDP' Class (CreateRandomScenarioFromSAA) to 'Scenario' class (Constructor)---------------")        
        w = Scenario(proabability=1)
        if Constants.Debug: print("------------Moving BACK from 'Scenario' class (Constructor) to 'SDDP' Class (CreateRandomScenarioFromSAA)---------------")        

        w.Demands = [[] for t in self.Instance.TimeBucketSet]
        w.HospitalCaps = [[] for t in self.Instance.TimeBucketSet]
        w.WholeDonors = [[] for t in self.Instance.TimeBucketSet]
        w.ApheresisDonors = [[] for t in self.Instance.TimeBucketSet]


        for s in range(len(self.StagesSet)):
            if self.ForwardStage[s].TimeObservationStage >= 0:
                x = random.randint(0, self.NrSAAScenarioInPeriod[self.ForwardStage[s].TimeObservationStage]-1)
            else:
                x = 0
            for tau in (self.ForwardStage[s].RangePeriodPatientTransfer):
                if Constants.Debug: print("s: ", s, "x: ", x)
                t = self.ForwardStage[s].TimeObservationStage + tau 
                w.Demands[t] = copy.deepcopy(self.SetOfSAAScenarioDemand[t][x]) if self.SetOfSAAScenarioDemand[t] else []
                w.HospitalCaps[t] = copy.deepcopy(self.SetOfSAAScenarioHospitalCapacity[t][x]) if self.SetOfSAAScenarioHospitalCapacity[t] else []
                w.WholeDonors[t] = copy.deepcopy(self.SetOfSAAScenarioWholeDonor[t][x]) if self.SetOfSAAScenarioWholeDonor[t] else []
                w.ApheresisDonors[t] = copy.deepcopy(self.SetOfSAAScenarioApheresisDonor[t][x]) if self.SetOfSAAScenarioApheresisDonor[t] else []
                w.Probability *= self.Saascenarioproba[t][x] if self.Saascenarioproba[t] else 1.0
        
        if Constants.Debug: 
            print(f"w.Probability: ", w.Probability)
            print(f"w.Demands: ",w.Demands)
            print(f"w.HospitalCaps: ",w.HospitalCaps)
            print(f"w.WholeDonors: ",w.WholeDonors)
            print(f"w.ApheresisDonors: ",w.ApheresisDonors)
            
        return w

    def CreateAllScenarioFromSAA(self):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- (CreateAllScenarioFromSAA)")

        scenarioset = []

        nrscenar = 1
        for s in range(len(self.StagesSet)):
            if self.ForwardStage[s].TimeObservationStage >= 0:
                if Constants.Debug: print(f"{self.NrSAAScenarioInPeriod[self.ForwardStage[s].TimeObservationStage]}")
                nrscenar *= self.NrSAAScenarioInPeriod[self.ForwardStage[s].TimeObservationStage]

        # Initialize the index array
        indexstage = [0] * (len(self.StagesSet) - 1)

        for nrw in range(nrscenar):
            w = Scenario(proabability=1)
            w.Demands = [[] for t in self.Instance.TimeBucketSet]
            w.HospitalCaps = [[] for t in self.Instance.TimeBucketSet]
            w.WholeDonors = [[] for t in self.Instance.TimeBucketSet]
            w.ApheresisDonors = [[] for t in self.Instance.TimeBucketSet]

            if Constants.Debug: print(f"\n----------------------Creating scenario {nrw + 1}/{nrscenar}--------------------------")
            for s in range(len(self.StagesSet) - 1):
                if Constants.Debug: print(f"\nProcessing stage {s}/{len(self.StagesSet) - 1}")
                if Constants.Debug: print(f"indexstage[{s}]: {indexstage[s]}")

                for tau in self.ForwardStage[s].RangePeriodApheresisAssignment:
                    t = self.ForwardStage[s].TimeObservationStage + tau
                    if Constants.Debug:
                        print(f"tau: {tau}, TimeObservationStage: {self.ForwardStage[s].TimeObservationStage}")
                        print(f"Size of SetOfSAAScenarioDemand at time {t}: {len(self.SetOfSAAScenarioDemand[t])}")
                        print(f"Size of SetOfSAAScenarioHospitalCapacity at time {t}: {len(self.SetOfSAAScenarioHospitalCapacity[t])}")
                        print(f"Size of SetOfSAAScenarioWholeDonor at time {t}: {len(self.SetOfSAAScenarioWholeDonor[t])}")
                        print(f"Size of SetOfSAAScenarioApheresisDonor at time {t}: {len(self.SetOfSAAScenarioApheresisDonor[t])}")
                    
                    if t < len(self.StagesSet) - 1:
                        w.Demands[t] = copy.deepcopy(self.SetOfSAAScenarioDemand[t][indexstage[s]])
                        w.HospitalCaps[t] = copy.deepcopy(self.SetOfSAAScenarioHospitalCapacity[t][indexstage[s]])
                        w.WholeDonors[t] = copy.deepcopy(self.SetOfSAAScenarioWholeDonor[t][indexstage[s]])
                        w.ApheresisDonors[t] = copy.deepcopy(self.SetOfSAAScenarioApheresisDonor[t][indexstage[s]])
                        w.Probability *= self.Saascenarioproba[t][indexstage[s]]
                        if Constants.Debug:
                            print(f"\nw.Demands[{s}]: ", w.Demands[s])
                            print(f"\nw.HospitalCaps[{s}]: ", w.HospitalCaps[s])
                            print(f"\nw.WholeDonors[{s}]: ", w.WholeDonors[s])
                            print(f"\nw.ApheresisDonors[{s}]: ", w.ApheresisDonors[s])
                            print("w.Probability: ", w.Probability)

            if Constants.Debug:
                print("\nw.Demands: ", w.Demands)
                print("\nw.HospitalCaps: ", w.HospitalCaps)
                print("\nw.WholeDonors: ", w.WholeDonors)
                print("\nw.ApheresisDonors: ", w.ApheresisDonors)

            scenarioset.append(w)

            k = len(self.StagesSet) - 2
            stop = False
            if Constants.Debug: print(f"Initial k: {k}, StagesSet length: {len(self.StagesSet)}")
            while not stop and k >= 0:
                if Constants.Debug: print(f"\nBefore increment: k={k}, indexstage[k]={indexstage[k]}, NrSAAScenarioInPeriod length: {len(self.NrSAAScenarioInPeriod)}")

                indexstage[k] += 1

                if Constants.Debug: print(f"After increment: k={k}, indexstage[k]={indexstage[k]}, NrSAAScenarioInPeriod length: {len(self.NrSAAScenarioInPeriod)}")

                if self.ForwardStage[k].TimeObservationStage >= 0:
                    if indexstage[k] >= self.NrSAAScenarioInPeriod[self.ForwardStage[k].TimeObservationStage]:
                        if Constants.Debug: print(f"Resetting indexstage[{k}] to 0 and decrease k by one unit, because it exceeded scenarios. indexstage[k]={indexstage[k]}, limit={self.NrSAAScenarioInPeriod[self.ForwardStage[k].TimeObservationStage]}")
                        indexstage[k] = 0
                        k -= 1
                    else:
                        stop = True
                else:
                    stop = True

                if Constants.Debug: print(f"After increment: k={k}, stop={stop}")

        if Constants.Debug:
            for i, scenario in enumerate(scenarioset):
                print(f"Scenario {i + 1}:")
                print(f"Probability: {scenario.Probability}")
                print("Demands:")
                for demand in scenario.Demands:
                    print(demand)
                print("HospitalCaps:")
                for hospitalCaps in scenario.HospitalCaps:
                    print(hospitalCaps)
                print("WholeDonors:")
                for wholeDonors in scenario.WholeDonors:
                    print(wholeDonors)
                print("ApheresisDonors:")
                for apheresisDonors in scenario.ApheresisDonors:
                    print(apheresisDonors)
                print("--------------------------------")

        return scenarioset

    def CreateSubsetScenarioFromSAA(self, percentage):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- (CreateSubsetScenarioFromSAA)")

        scenarioset = []

        nrscenar = 1
        for s in range(len(self.StagesSet)):
            if self.ForwardStage[s].TimeObservationStage >= 0:
                if Constants.Debug: print(f"{self.NrSAAScenarioInPeriod[self.ForwardStage[s].TimeObservationStage]}")
                nrscenar *= self.NrSAAScenarioInPeriod[self.ForwardStage[s].TimeObservationStage]

        # Calculate the number of scenarios to create based on the percentage
        NrScenariosBasedonPercentage = int(nrscenar * (percentage / 100.0))
        nrscenar_to_create = min(NrScenariosBasedonPercentage, Constants.NrInSampleScnearioTest)
        self.CurrentNrInSampleScenarioToTest = nrscenar_to_create

        # Initialize the index array
        indexstage = [0] * (len(self.StagesSet) - 1)
        
        if Constants.NrInSampleScnearioTest < NrScenariosBasedonPercentage:     #When we do not want to creat all scenarios! We want random Sampling!
            random_indices = [i for i in range(nrscenar)]
            random.shuffle(random_indices)

        created_scenarios = 0
        while created_scenarios < nrscenar_to_create:
            w = Scenario(proabability=1)
            w.Demands = [[] for t in self.Instance.TimeBucketSet]
            w.HospitalCaps = [[] for t in self.Instance.TimeBucketSet]
            w.WholeDonors = [[] for t in self.Instance.TimeBucketSet]
            w.ApheresisDonors = [[] for t in self.Instance.TimeBucketSet]

            if Constants.Debug: print(f"\n----------------------Creating scenario {created_scenarios + 1}/{nrscenar_to_create}--------------------------")
            for s in range(len(self.StagesSet) - 1):
                if Constants.Debug: print(f"\nProcessing stage {s}/{len(self.StagesSet) - 1}")
                if Constants.Debug: print(f"indexstage[{s}]: {indexstage[s]}")

                for tau in self.ForwardStage[s].RangePeriodApheresisAssignment:
                    t = self.ForwardStage[s].TimeObservationStage + tau
                    if Constants.Debug:
                        print(f"tau: {tau}, TimeObservationStage: {self.ForwardStage[s].TimeObservationStage}")
                        print(f"Size of SetOfSAAScenarioDemand at time {t}: {len(self.SetOfSAAScenarioDemand[t])}")
                        print(f"Size of SetOfSAAScenarioHospitalCapacity at time {t}: {len(self.SetOfSAAScenarioHospitalCapacity[t])}")
                        print(f"Size of SetOfSAAScenarioWholeDonor at time {t}: {len(self.SetOfSAAScenarioWholeDonor[t])}")
                        print(f"Size of SetOfSAAScenarioApheresisDonor at time {t}: {len(self.SetOfSAAScenarioApheresisDonor[t])}")

                    if t < len(self.StagesSet) - 1:
                        w.Demands[t] = copy.deepcopy(self.SetOfSAAScenarioDemand[t][indexstage[s]])
                        w.HospitalCaps[t] = copy.deepcopy(self.SetOfSAAScenarioHospitalCapacity[t][indexstage[s]])
                        w.WholeDonors[t] = copy.deepcopy(self.SetOfSAAScenarioWholeDonor[t][indexstage[s]])
                        w.ApheresisDonors[t] = copy.deepcopy(self.SetOfSAAScenarioApheresisDonor[t][indexstage[s]])
                        w.Probability *= self.Saascenarioproba[t][indexstage[s]]
                        if Constants.Debug:
                            print(f"\nw.Demands[{s}]: ", w.Demands[s])
                            print(f"\nw.HospitalCaps[{s}]: ", w.HospitalCaps[s])
                            print(f"\nw.WholeDonors[{s}]: ", w.WholeDonors[s])
                            print(f"\nw.ApheresisDonors[{s}]: ", w.ApheresisDonors[s])
                            print("w.Probability: ", w.Probability)

            if Constants.Debug:
                print("\nw.Demands: ", w.Demands)
                print("\nw.HospitalCaps: ", w.HospitalCaps)
                print("\nw.WholeDonors: ", w.WholeDonors)
                print("\nw.ApheresisDonors: ", w.ApheresisDonors)

            scenarioset.append(w)
            created_scenarios += 1

            if Constants.NrInSampleScnearioTest < NrScenariosBasedonPercentage:     #When we do not want to creat all scenarios! We want random Sampling!
                # Use the shuffled random indices
                current_index = random_indices[created_scenarios]
                for k in range(len(indexstage)):
                    if self.NrSAAScenarioInPeriod[self.ForwardStage[k].TimeObservationStage] > 0:
                        indexstage[k] = current_index % self.NrSAAScenarioInPeriod[self.ForwardStage[k].TimeObservationStage]
                        current_index //= self.NrSAAScenarioInPeriod[self.ForwardStage[k].TimeObservationStage]
            else:
                k = len(self.StagesSet) - 2
                stop = False
                if Constants.Debug: print(f"Initial k: {k}, StagesSet length: {len(self.StagesSet)}")
                while not stop and k >= 0:
                    if Constants.Debug: print(f"\nBefore increment: k={k}, indexstage[k]={indexstage[k]}, NrSAAScenarioInPeriod length: {len(self.NrSAAScenarioInPeriod)}")

                    indexstage[k] += 1

                    if Constants.Debug: print(f"After increment: k={k}, indexstage[k]={indexstage[k]}, NrSAAScenarioInPeriod length: {len(self.NrSAAScenarioInPeriod)}")

                    if self.ForwardStage[k].TimeObservationStage >= 0:
                        if indexstage[k] >= self.NrSAAScenarioInPeriod[self.ForwardStage[k].TimeObservationStage]:
                            if Constants.Debug: print(f"Resetting indexstage[{k}] to 0 and decrease k by one unit, because it exceeded scenarios. indexstage[k]={indexstage[k]}, limit={self.NrSAAScenarioInPeriod[self.ForwardStage[k].TimeObservationStage]}")
                            indexstage[k] = 0
                            k -= 1
                        else:
                            stop = True
                    else:
                        stop = True

                    if Constants.Debug: print(f"After increment: k={k}, stop={stop}")

        if Constants.Debug:
            for i, scenario in enumerate(scenarioset):
                print(f"Scenario {i + 1}:")
                print(f"Probability: {scenario.Probability}")
                print("Demands:")
                for demand in scenario.Demands:
                    print(demand)
                print("HospitalCaps:")
                for hospitalCaps in scenario.HospitalCaps:
                    print(hospitalCaps)
                print("WholeDonors:")
                for wholeDonors in scenario.WholeDonors:
                    print(wholeDonors)
                print("ApheresisDonors:")
                for apheresisDonors in scenario.ApheresisDonors:
                    print(apheresisDonors)
                print("--------------------------------")

        return scenarioset
            
    def GenerateSAAScenarios2(self):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- (GenerateSAAScenarios2)")

        if Constants.ScenarioReduction != "NoReduction":

            # Generate a larger set of scenarios for scenario reduction
            self.SAAScenarioNrSetInPeriod = [range(self.NrSAAScenarioInPeriod[t]) for t in self.Instance.TimeBucketSet]
            self.SAAScenarioNrSetInPeriod_KNN = [range(Constants.Coeeff_Init_Scen_bef_reduction * self.NrSAAScenarioInPeriod[t]) for t in self.Instance.TimeBucketSet]

            if Constants.Debug: print("self.SAAScenarioNrSetInPeriod_KNN: ", self.SAAScenarioNrSetInPeriod_KNN)

            SymetricDemand = [[] for t in self.Instance.TimeBucketSet]
            SymetricHospitalCapacity = [[] for t in self.Instance.TimeBucketSet]
            SymetricWholeDonor = [[] for t in self.Instance.TimeBucketSet]
            SymetricApheresisDonor = [[] for t in self.Instance.TimeBucketSet]
            SymetricProba = [[] for t in self.Instance.TimeBucketSet]
            SymetricProbaHospital = [[] for t in self.Instance.TimeBucketSet]
            SymetricProbaWholeDonor = [[] for t in self.Instance.TimeBucketSet]
            SymetricProbaApheresisDonor = [[] for t in self.Instance.TimeBucketSet]
            
            np.random.seed(self.TestIdentifier.ScenarioSeed)

            for t in self.Instance.TimeBucketSet:
                SymetricDemand[t], SymetricProba[t] = ScenarioTreeNode.CreateDemandNormalDistributiondemand(self.Instance, t, Constants.Coeeff_Init_Scen_bef_reduction * self.NrSAAScenarioInPeriod[t], False, self.ScenarioGenerationMethod)
                SymetricHospitalCapacity[t], SymetricProbaHospital[t] = ScenarioTreeNode.CreateHospitalCapNormalDistribution(self.Instance, t, Constants.Coeeff_Init_Scen_bef_reduction * self.NrSAAScenarioInPeriod[t], False, self.ScenarioGenerationMethod)
                SymetricWholeDonor[t], SymetricProbaWholeDonor[t] = ScenarioTreeNode.CreateWholeDonorNormalDistribution(self.Instance, t, Constants.Coeeff_Init_Scen_bef_reduction * self.NrSAAScenarioInPeriod[t], False, self.ScenarioGenerationMethod)
                SymetricApheresisDonor[t], SymetricProbaApheresisDonor[t] = ScenarioTreeNode.CreateApheresisDonorNormalDistribution(self.Instance, t, Constants.Coeeff_Init_Scen_bef_reduction * self.NrSAAScenarioInPeriod[t], False, self.ScenarioGenerationMethod)

            # Populate the scenarios into the respective variables
            self.SetOfSAAScenarioDemand = [[[] for w in self.SAAScenarioNrSetInPeriod_KNN[t]] for t in self.Instance.TimeBucketSet]
            self.SetOfSAAScenarioHospitalCapacity = [[[] for w in self.SAAScenarioNrSetInPeriod_KNN[t]] for t in self.Instance.TimeBucketSet]
            self.SetOfSAAScenarioWholeDonor = [[[] for w in self.SAAScenarioNrSetInPeriod_KNN[t]] for t in self.Instance.TimeBucketSet]
            self.SetOfSAAScenarioApheresisDonor = [[[] for w in self.SAAScenarioNrSetInPeriod_KNN[t]] for t in self.Instance.TimeBucketSet]
            self.Saascenarioproba = [[-1 for w in self.SAAScenarioNrSetInPeriod_KNN[t]] for t in self.Instance.TimeBucketSet]

            for t in self.Instance.TimeBucketSet:
                for w in self.SAAScenarioNrSetInPeriod_KNN[t]:
                    self.SetOfSAAScenarioDemand[t][w] = [[[SymetricDemand[t][j][c][l][w] 
                                                        for l in self.Instance.DemandSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for j in self.Instance.InjuryLevelSet]

                    self.SetOfSAAScenarioHospitalCapacity[t][w] = [SymetricHospitalCapacity[t][h][w] 
                                                                for h in self.Instance.HospitalSet]

                    self.SetOfSAAScenarioWholeDonor[t][w] = [[SymetricWholeDonor[t][c][h][w] 
                                                            for h in self.Instance.HospitalSet]
                                                            for c in self.Instance.BloodGPSet]

                    self.SetOfSAAScenarioApheresisDonor[t][w] = [[SymetricApheresisDonor[t][c][u][w] 
                                                                for u in self.Instance.FacilitySet]
                                                                for c in self.Instance.BloodGPSet]

                    self.Saascenarioproba[t][w] = Constants.Coeeff_Init_Scen_bef_reduction * SymetricProba[t][w]

            # Now that the scenarios are set up, perform scenario reduction
            self.rebuild_scenarios()

            for stage in self.StagesSet:
                time = self.BackwardStage[stage].TimeDecisionStage - 1
                if Constants.Debug: print(f"Processing stage: {stage}, TimeDecisionStage: {time}")

                if time + max(len(self.BackwardStage[stage].RangePeriodApheresisAssignment), 1) >= 1:
                    self.BackwardStage[stage].FixedScenarioSet = self.SAAScenarioNrSetInPeriod[time]
                    self.BackwardStage[stage].FixedScenarioPobability = [self.Saascenarioproba[time][w] for w in self.SAAScenarioNrSetInPeriod[time]]
                    self.BackwardStage[stage].SAAStageCostPerScenarioWithoutCostoGopertrial = [0 for w in self.TrialScenarioNrSet]
                    if Constants.Debug: print(f"Stage {stage} scenarios and probabilities fixed for time {time}")
                else:
                    self.BackwardStage[stage].FixedScenarioSet = [0]
                    self.BackwardStage[stage].FixedScenarioPobability = [1]
                    self.BackwardStage[stage].SAAStageCostPerScenarioWithoutCostoGopertrial = [0 for w in self.TrialScenarioNrSet]
                    if Constants.Debug: print(f"Stage {stage} default scenarios and probabilities set for time {time}")
                
                    if Constants.Debug: print(f"self.BackwardStage[stage={stage}].FixedScenarioPobability: ",self.BackwardStage[stage].FixedScenarioPobability)
                
                for stage in self.StagesSet:
                    if Constants.Debug: print(f"Checking if stage {stage} is not the last stage.")
                    if not self.BackwardStage[stage].IsLastStage():
                        nextstage = stage + 1
                        nextstagetime = self.BackwardStage[nextstage].TimeDecisionStage - 1
                        if Constants.Debug: print(f"Stage {stage} is not the last. Proceeding to next stage: {nextstage}, NextStageTime: {nextstagetime}")

                        self.BackwardStage[stage].FuturScenario = self.BackwardStage[nextstage].FixedScenarioSet
                        self.BackwardStage[stage].FuturScenarProba = self.BackwardStage[nextstage].FixedScenarioPobability
                        if Constants.Debug: print(f"BackwardStage[stage={stage}].FuturScenario: ",self.BackwardStage[stage].FuturScenario)
                        if Constants.Debug: print(f"BackwardStage[stage={stage}].FuturScenarProba: ",self.BackwardStage[stage].FuturScenarProba)
                        
                        self.ForwardStage[stage].FuturScenario = self.BackwardStage[nextstage].FixedScenarioSet
                        self.ForwardStage[stage].FuturScenarProba = self.BackwardStage[nextstage].FixedScenarioPobability                
                        if Constants.Debug: print(f"ForwardStage[stage={stage}].FuturScenario: ",self.ForwardStage[stage].FuturScenario)
                        if Constants.Debug: print(f"ForwardStage[stage={stage}].FuturScenarProba: ",self.ForwardStage[stage].FuturScenarProba)

                    if Constants.Debug: print(f"Computing variable indices for stage {stage} in both Forward and Backward Stages.")
                    self.ForwardStage[stage].ComputeVariableIndices()
                    self.BackwardStage[stage].ComputeVariableIndices()

        else:
            print("Generate SAA Scenarios with out reduction")
            # Regular scenario generation without reduction
            self.SAAScenarioNrSetInPeriod = [range(self.NrSAAScenarioInPeriod[t]) for t in self.Instance.TimeBucketSet]

            if Constants.Debug: print("self.SAAScenarioNrSetInPeriod: ",self.SAAScenarioNrSetInPeriod)
            SymetricDemand = [[] for t in self.Instance.TimeBucketSet]
            SymetricHospitalCapacity = [[] for t in self.Instance.TimeBucketSet]
            SymetricWholeDonor = [[] for t in self.Instance.TimeBucketSet]
            SymetricApheresisDonor = [[] for t in self.Instance.TimeBucketSet]
            SymetricProba = [[] for t in self.Instance.TimeBucketSet]               #For the probabilities, we only use "SymetricProba" in the future, because all of them have the same value
            SymetricProbaHospital = [[] for t in self.Instance.TimeBucketSet]       #For the probabilities, we only use "SymetricProba" in the future, because all of them have the same value
            SymetricProbaWholeDonor = [[] for t in self.Instance.TimeBucketSet]     #For the probabilities, we only use "SymetricProba" in the future, because all of them have the same value
            SymetricProbaApheresisDonor = [[] for t in self.Instance.TimeBucketSet] #For the probabilities, we only use "SymetricProba" in the future, because all of them have the same value
            np.random.seed(self.TestIdentifier.ScenarioSeed)


            for t in self.Instance.TimeBucketSet: 
                if Constants.Debug: print(f"self.NrSAAScenarioInPeriod[t={t}]: ", self.NrSAAScenarioInPeriod[t])
                SymetricDemand[t], SymetricProba[t] = ScenarioTreeNode.CreateDemandNormalDistributiondemand(self.Instance, t,  self.NrSAAScenarioInPeriod[t], False, self.ScenarioGenerationMethod)
                SymetricHospitalCapacity[t], SymetricProbaHospital[t] = ScenarioTreeNode.CreateHospitalCapNormalDistribution(self.Instance, t,  self.NrSAAScenarioInPeriod[t], False, self.ScenarioGenerationMethod)
                SymetricWholeDonor[t], SymetricProbaWholeDonor[t] = ScenarioTreeNode.CreateWholeDonorNormalDistribution(self.Instance, t,  self.NrSAAScenarioInPeriod[t], False, self.ScenarioGenerationMethod)
                SymetricApheresisDonor[t], SymetricProbaApheresisDonor[t] = ScenarioTreeNode.CreateApheresisDonorNormalDistribution(self.Instance, t,  self.NrSAAScenarioInPeriod[t], False, self.ScenarioGenerationMethod)


            self.SetOfSAAScenarioDemand = [[[] for w in self.SAAScenarioNrSetInPeriod[t]] for t in self.Instance.TimeBucketSet]
            self.SetOfSAAScenarioHospitalCapacity = [[[] for w in self.SAAScenarioNrSetInPeriod[t]] for t in self.Instance.TimeBucketSet]
            self.SetOfSAAScenarioWholeDonor = [[[] for w in self.SAAScenarioNrSetInPeriod[t]] for t in self.Instance.TimeBucketSet]
            self.SetOfSAAScenarioApheresisDonor = [[[] for w in self.SAAScenarioNrSetInPeriod[t]] for t in self.Instance.TimeBucketSet]

            self.Saascenarioproba = [[-1 for w in self.SAAScenarioNrSetInPeriod[t]] for t in self.Instance.TimeBucketSet]
            
            t = 0
            for t in self.Instance.TimeBucketSet:
                for w in self.SAAScenarioNrSetInPeriod[t]:
                    
                    self.SetOfSAAScenarioDemand[t][w] = [[[SymetricDemand[t][j][c][l][w] 
                                                        for l in self.Instance.DemandSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for j in self.Instance.InjuryLevelSet]

                    self.SetOfSAAScenarioHospitalCapacity[t][w] = [SymetricHospitalCapacity[t][h][w] 
                                                                for h in self.Instance.HospitalSet]

                    self.SetOfSAAScenarioWholeDonor[t][w] = [[SymetricWholeDonor[t][c][h][w] 
                                                            for h in self.Instance.HospitalSet]
                                                            for c in self.Instance.BloodGPSet]

                    self.SetOfSAAScenarioApheresisDonor[t][w] = [[SymetricApheresisDonor[t][c][u][w] 
                                                                for u in self.Instance.FacilitySet]
                                                                for c in self.Instance.BloodGPSet]

                    self.Saascenarioproba[t][w] = SymetricProba[t][w]


            for stage in self.StagesSet:
                time = self.BackwardStage[stage].TimeDecisionStage - 1
                if Constants.Debug: print(f"Processing stage: {stage}, TimeDecisionStage: {time}")

                if time + max(len(self.BackwardStage[stage].RangePeriodApheresisAssignment), 1) >= 1:
                    self.BackwardStage[stage].FixedScenarioSet = self.SAAScenarioNrSetInPeriod[time]
                    self.BackwardStage[stage].FixedScenarioPobability = [self.Saascenarioproba[time][w] for w in self.SAAScenarioNrSetInPeriod[time]]
                    self.BackwardStage[stage].SAAStageCostPerScenarioWithoutCostoGopertrial = [0 for w in self.TrialScenarioNrSet]
                    if Constants.Debug: print(f"Stage {stage} scenarios and probabilities fixed for time {time}")
                else:
                    self.BackwardStage[stage].FixedScenarioSet = [0]
                    self.BackwardStage[stage].FixedScenarioPobability = [1]
                    self.BackwardStage[stage].SAAStageCostPerScenarioWithoutCostoGopertrial = [0 for w in self.TrialScenarioNrSet]
                    if Constants.Debug: print(f"Stage {stage} default scenarios and probabilities set for time {time}")
                
                    if Constants.Debug: print(f"self.BackwardStage[stage={stage}].FixedScenarioPobability: ",self.BackwardStage[stage].FixedScenarioPobability)
                
                for stage in self.StagesSet:
                    if Constants.Debug: print(f"Checking if stage {stage} is not the last stage.")
                    if not self.BackwardStage[stage].IsLastStage():
                        nextstage = stage + 1
                        nextstagetime = self.BackwardStage[nextstage].TimeDecisionStage - 1
                        if Constants.Debug: print(f"Stage {stage} is not the last. Proceeding to next stage: {nextstage}, NextStageTime: {nextstagetime}")

                        self.BackwardStage[stage].FuturScenario = self.BackwardStage[nextstage].FixedScenarioSet
                        self.BackwardStage[stage].FuturScenarProba = self.BackwardStage[nextstage].FixedScenarioPobability
                        if Constants.Debug: print(f"BackwardStage[stage={stage}].FuturScenario: ",self.BackwardStage[stage].FuturScenario)
                        if Constants.Debug: print(f"BackwardStage[stage={stage}].FuturScenarProba: ",self.BackwardStage[stage].FuturScenarProba)
                        
                        self.ForwardStage[stage].FuturScenario = self.BackwardStage[nextstage].FixedScenarioSet
                        self.ForwardStage[stage].FuturScenarProba = self.BackwardStage[nextstage].FixedScenarioPobability                
                        if Constants.Debug: print(f"ForwardStage[stage={stage}].FuturScenario: ",self.ForwardStage[stage].FuturScenario)
                        if Constants.Debug: print(f"ForwardStage[stage={stage}].FuturScenarProba: ",self.ForwardStage[stage].FuturScenarProba)

                    if Constants.Debug: print(f"Computing variable indices for stage {stage} in both Forward and Backward Stages.")
                    self.ForwardStage[stage].ComputeVariableIndices()
                    self.BackwardStage[stage].ComputeVariableIndices()

    def rebuild_scenarios(self):
        for t in self.Instance.TimeBucketSet:
            # Extract features for clustering
            features = self.extract_scenario_features(t)

            if Constants.ScenarioReduction == "KMeans":
                # Scale the features
                scaler = StandardScaler()           
                scaled_features = scaler.fit_transform(features)                
                print("----- Applying -KMeans- For Scenario Reduction -----")
                # Apply KMeans clustering
                kmeans = KMeans(n_clusters=self.NrSAAScenarioInPeriod[t], random_state=0).fit(scaled_features)
                selected_scenarios = []
                for cluster_id in range(self.NrSAAScenarioInPeriod[t]):
                    cluster_indices = [i for i, label in enumerate(kmeans.labels_) if label == cluster_id]
                    selected_scenarios.append(cluster_indices[0])  # Pick the first scenario in each cluster

            elif Constants.ScenarioReduction == "KMeansPP":
                # Scale the features
                scaler = StandardScaler()           
                scaled_features = scaler.fit_transform(features)                
                print("----- Applying -KMeans++- For Scenario Reduction -----")
                # Apply KMeans++ clustering
                kmeans_pp = KMeans(n_clusters=self.NrSAAScenarioInPeriod[t], init='k-means++', random_state=42)
                kmeans_pp.fit(scaled_features)

                selected_scenarios = []
                for cluster_id in range(self.NrSAAScenarioInPeriod[t]):
                    cluster_indices = [i for i, label in enumerate(kmeans_pp.labels_) if label == cluster_id]
                    selected_scenarios.append(cluster_indices[0])  # Pick the first scenario in each cluster

            elif Constants.ScenarioReduction == "SOM":
                # Scale the features
                sc = MinMaxScaler(feature_range = (0,1))
                scaled_features = sc.fit_transform(features)                 
                print("----- Applying -SOM- For Scenario Reduction -----")
                # Apply SOM-based clustering
                som = MiniSom(x=self.NrSAAScenarioInPeriod[t], y=1, input_len=len(scaled_features[0]), sigma=1.0, learning_rate=0.5)
                som.random_weights_init(scaled_features)
                som.train_random(scaled_features, num_iteration=100)

                # Get the winning neurons (clusters) for each scenario
                winner_coordinates = np.array([som.winner(x) for x in scaled_features])
                winner_indices = np.ravel_multi_index(winner_coordinates.T, (self.NrSAAScenarioInPeriod[t], 1))

                # Initialize the list of selected scenarios
                selected_scenarios = []

                # Ensure that each cluster has at least one scenario
                for i in range(self.NrSAAScenarioInPeriod[t]):
                    indices_in_cluster = np.where(winner_indices == i)[0]
                    if len(indices_in_cluster) > 0:
                        selected_scenarios.append(indices_in_cluster[0])  # Select the first scenario in each cluster
                    else:
                        # If a cluster is empty, find the closest scenario to the cluster's neuron
                        closest_scenario = np.argmin([np.linalg.norm(scaled_features - som.get_weights()[i]) for _ in scaled_features])
                        selected_scenarios.append(closest_scenario)

                # If fewer scenarios were selected due to empty clusters, select additional scenarios
                if len(selected_scenarios) < self.NrSAAScenarioInPeriod[t]:
                    remaining_scenarios = set(range(len(scaled_features))) - set(selected_scenarios)
                    additional_scenarios = list(remaining_scenarios)[:self.NrSAAScenarioInPeriod[t] - len(selected_scenarios)]
                    selected_scenarios.extend(additional_scenarios)

                # Make sure the number of selected scenarios is exactly what is needed
                selected_scenarios = selected_scenarios[:self.NrSAAScenarioInPeriod[t]]
            
            elif Constants.ScenarioReduction == "Hierarchical":
                # Scale the features
                scaler = StandardScaler()           
                scaled_features = scaler.fit_transform(features)                
                print("----- Applying -Hierarchical- For Scenario Reduction -----")
                # Apply Hierarchical Clustering
                hierarchical = AgglomerativeClustering(n_clusters=self.NrSAAScenarioInPeriod[t])
                labels = hierarchical.fit_predict(scaled_features)
                selected_scenarios = []
                for cluster_id in range(self.NrSAAScenarioInPeriod[t]):
                    cluster_indices = [i for i, label in enumerate(labels) if label == cluster_id]
                    selected_scenarios.append(cluster_indices[0])  # Pick the first scenario in each cluster
            
            elif Constants.ScenarioReduction == "Hierarchical_Diverse":
                # Scale the features
                scaler = StandardScaler()           
                scaled_features = scaler.fit_transform(features)                   
                print("----- Applying -Hierarchical (Diverse Selection)- For Scenario Reduction -----")
                # Apply Hierarchical Clustering
                hierarchical = AgglomerativeClustering(n_clusters=self.NrSAAScenarioInPeriod[t])
                labels = hierarchical.fit_predict(scaled_features)
                selected_scenarios = []
                
                # Initialize with the first scenario from the first cluster
                first_scenario = np.argmax(np.linalg.norm(scaled_features - np.mean(scaled_features, axis=0), axis=1))
                selected_scenarios.append(first_scenario)
                
                # Select the remaining scenarios by maximizing the minimum distance to already selected scenarios
                for _ in range(1, self.NrSAAScenarioInPeriod[t]):
                    max_min_dist = -1
                    best_scenario = None
                    for i, feature in enumerate(scaled_features):
                        if i in selected_scenarios:
                            continue
                        min_dist = np.min([np.linalg.norm(feature - scaled_features[s]) for s in selected_scenarios])
                        if min_dist > max_min_dist:
                            max_min_dist = min_dist
                            best_scenario = i
                    selected_scenarios.append(best_scenario)

            else:
                raise ValueError("Invalid Scenario Reduction Method. Use 'KNN', 'SOM'.")

            # Rebuild the reduced scenarios
            self.SetOfSAAScenarioDemand[t] = [self.SetOfSAAScenarioDemand[t][w] for w in selected_scenarios]
            self.SetOfSAAScenarioHospitalCapacity[t] = [self.SetOfSAAScenarioHospitalCapacity[t][w] for w in selected_scenarios]
            self.SetOfSAAScenarioWholeDonor[t] = [self.SetOfSAAScenarioWholeDonor[t][w] for w in selected_scenarios]
            self.SetOfSAAScenarioApheresisDonor[t] = [self.SetOfSAAScenarioApheresisDonor[t][w] for w in selected_scenarios]
            self.Saascenarioproba[t] = [self.Saascenarioproba[t][w] for w in selected_scenarios]

    def extract_scenario_features(self, t):
        features = []
        for w in self.SAAScenarioNrSetInPeriod_KNN[t]:
            # Flatten the demand
            demand = []
            for j in self.Instance.InjuryLevelSet:
                for c in self.Instance.BloodGPSet:
                    for l in self.Instance.DemandSet:
                        demand.append(self.SetOfSAAScenarioDemand[t][w][j][c][l])

            # Flatten the hospital capacity
            hospital_capacity = self.SetOfSAAScenarioHospitalCapacity[t][w]

            # Flatten the whole donors
            whole_donor = []
            for c in self.Instance.BloodGPSet:
                for h in self.Instance.HospitalSet:
                    whole_donor.append(self.SetOfSAAScenarioWholeDonor[t][w][c][h])

            # Flatten the apheresis donors
            apheresis_donor = []
            for c in self.Instance.BloodGPSet:
                for u in self.Instance.FacilitySet:
                    apheresis_donor.append(self.SetOfSAAScenarioApheresisDonor[t][w][c][u])

            # Combine all into a single feature vector
            feature_vector = demand + hospital_capacity + whole_donor + apheresis_donor

            # Check if feature_vector length is consistent
            #print(f"Scenario {w} feature vector length: {len(feature_vector)}")  # Debugging line

            features.append(feature_vector)
        
        return features

    def WriteInTraceFile(self, string):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- (WriteInTraceFile)")
        if Constants.PrintSDDPTrace:
            self.TraceFile = open(self.TraceFileName, "a")
            self.TraceFile.write(string)
            self.TraceFile.close()

    def CheckStoppingCriterion(self):
        duration = time.time() - self.StartOfAlgorithm

        timelimitreached = (duration > (Constants.AlgorithmTimeLimit * self.Instance.NrTimeBucket))
        if Constants.Debug:
            print("TIME LIMIT reached: %r - %r" % (round(duration, 2), (Constants.AlgorithmTimeLimit * self.Instance.NrTimeBucket)))

        if self.CurrentExpvalueUpperBound != 0:
            optimalitygap = (self.CurrentExpvalueUpperBound - self.CurrentLowerBound) / self.CurrentExpvalueUpperBound
        else:
            optimalitygap = 1

        absolute_optimalitygap = abs(optimalitygap)

        optimalitygapreached = (absolute_optimalitygap < Constants.AlgorithmOptimalityTolerence)

        if Constants.PrintSDDPTrace:
            self.WriteInTraceFile(
                "Iteration: %d, Duration: %d, LB: %r, (exp UB:%r),  Gap: %.2f,  Fixed x: %r,  Fixed thetavar: %r  \n"
                % (self.CurrentIteration, duration, self.CurrentLowerBound,
                self.CurrentExpvalueUpperBound,
                100 * optimalitygap, self.HasFixed_ACFEstablishmentVar, self.HasFixed_VehicleAssignmentVar)
            )

        if Constants.Debug:
            print("TIME LIMIT reached: %r" % timelimitreached)
        if Constants.Debug:
            print("OPTIMALITY GAP reached: %r" % optimalitygapreached)

        result = timelimitreached

        if (
            not result 
            and (
                self.IsIterationWithConvergenceTest 
                or (
                    Constants.SDDPForwardPassInSAATree
                    and ((self.CurrentIteration - self.LastIterationWithTest) >= Constants.SDDPMinimumNrIterationBetweenTest)
                ) 
                or (
                    Constants.SDDPForwardPassInSAATree 
                    and (self.NrIterationWithoutLBImprovment >= Constants.SDDPNrItNoImproveLBBeforeTest + self.IterationMultiplier * Constants.SDDPNrItNoImproveLBBeforeTest)
                )
            )
        ):
            if self.IsIterationWithConvergenceTest:
                self.SDDPNrScenarioTest += Constants.SDDPIncreaseNrScenarioTest
            self.LastIterationWithTest = self.CurrentIteration

            if Constants.SDDPPerformConvergenceTestDuringRun:
                self.IsIterationWithConvergenceTest = True

            self.GenerateTrialScenarios()
            self.ForwardPass()
            self.ComputeCost()
            if Constants.NestedBenders:
                self.UpdateUpperBound_NBD()
            else:
                self.UpdateUpperBound_SDDP()
            self.LastExpectedCostComputedOnAllScenario = self.CurrentExpvalueUpperBound
            self.SafeUpperBoundeOnAllScenario = self.CurrentSafeUpperBound

            #We obtain The lower bound based on the reference: "Assessing policy quality in a multistage stochastic program for long-term hydrothermal scheduling"
            self.LowerBound_DeMatos = min(self.CurrentExpvalueUpperBound, self.CurrentLowerBound)
            print("self.LowerBound_DeMatos: ", self.LowerBound_DeMatos)

            if self.CurrentSafeUpperBound != 0:
                SafeGap = ((self.CurrentSafeUpperBound - self.LowerBound_DeMatos) / self.CurrentSafeUpperBound) * 100
            else:
                SafeGap = float('inf')  

            # Write the values to the trace file
            self.WriteInTraceFile(
                "Convergence Test, Nr Scenario: %r, LB: %r, (exp UB: %r - safe UB: %r), SafeGap: %.2f%% \n"
                % (self.CurrentNrInSampleScenarioToTest, self.LowerBound_DeMatos, self.CurrentExpvalueUpperBound, self.CurrentSafeUpperBound, SafeGap)
            )
            
            # Perform the stopping criterion check one more time after convergence test
            duration = time.time() - self.StartOfAlgorithm
            timelimitreached = (duration > (Constants.AlgorithmTimeLimit * self.Instance.NrTimeBucket))
            if self.CurrentSafeUpperBound != 0:
                optimalitygap = (self.CurrentSafeUpperBound - self.LowerBound_DeMatos) / self.CurrentSafeUpperBound
            else:
                optimalitygap = 1
            
            optimalitygapreached = (optimalitygap <= Constants.AlgorithmOptimalityTolerenceTest)

            result = timelimitreached or optimalitygapreached

            if not result:
                self.IsIterationWithConvergenceTest = False
                self.IterationMultiplier += 1  # Increment the iteration multiplier
            else:
                self.IsIterationWithConvergenceTest = True
        else:
            self.IsIterationWithConvergenceTest = False

        return result

        convergencecriterion = Constants.Infinity
        c = Constants.Infinity
        if self.CurrentLowerBound > 0:
            convergencecriterion = float(self.CurrentUpperBound) / float(self.CurrentLowerBound) \
                                   - (1.96 * math.sqrt(float(self.VarianceForwardPass) \
                                                     / float(self.CurrentNrScenario)) \
                                         / float(self.CurrentLowerBound))

            c = (1.96 * math.sqrt(float(self.VarianceForwardPass) / float(self.CurrentNrScenario)) \
                                     / float(self.CurrentLowerBound))

        delta = Constants.Infinity
        if self.CurrentLowerBound > 0:
            delta = 3.92 * math.sqrt(float(self.VarianceForwardPass) / float(self.CurrentNrScenario)) \
                    / float(self.CurrentLowerBound)

        convergencecriterionreached = convergencecriterion <= 1 \
                                      and delta <= Constants.AlgorithmOptimalityTolerence



        optimalitygapreached = (optimalitygap < Constants.AlgorithmOptimalityTolerence)
        iterationlimitreached = (self.CurrentIteration > Constants.SDDPIterationLimit)
        result = ( self.IsIterationWithConvergenceTest and convergencecriterionreached) \
                 or timelimitreached \
                 or iterationlimitreached

        if Constants.SDDPForwardPassInSAATree:
            result = (self.IsIterationWithConvergenceTest and optimalitygapreached) \
                     or timelimitreached \
                     or iterationlimitreached

        if Constants.PrintSDDPTrace:
            if self.IsIterationWithConvergenceTest:
                self.WriteInTraceFile(
                    "Convergence Test, Nr Scenario: %r, Duration: %d, LB: %r, (exp UB:%r), c: %r Gap: %r, conv: %r, delta : %r Fixed Y: %r \n"
                    % (self.SDDPNrScenarioTest, duration, self.CurrentLowerBound, self.CurrentExpvalueUpperBound,
                       c, optimalitygap, convergencecriterion, delta,  self.HasFixedSetup))
            else:
                self.WriteInTraceFile("Iteration: %d, Duration: %d, LB: %r, (exp UB:%r), c: %r Gap: %r, conv: %r, delta : %r Fixed Y: %r  \n"
                                  %(self.CurrentIteration, duration, self.CurrentLowerBound, self.CurrentExpvalueUpperBound,
                                    c, optimalitygap, convergencecriterion, delta,  self.HasFixedSetup))

        if not result and convergencecriterion <= 1 \
            and (self.IsIterationWithConvergenceTest \
                or ((not Constants.SDDPForwardPassInSAATree)
                     and ((self.CurrentIteration - self.LastIterationWithTest) > Constants.SDDPMinimumNrIterationBetweenTest))

                 or (Constants.SDDPForwardPassInSAATree
                         and (self.NrIterationWithoutLBImprovment) > Constants.SDDPNrItNoImproveLBBeforeTest)):

            if self.IsIterationWithConvergenceTest:
                self.SDDPNrScenarioTest += Constants.SDDPIncreaseNrScenarioTest
            self.LastIterationWithTest = self.CurrentIteration

            if Constants.SDDPForwardPassInSAATree and self.IsIterationWithConvergenceTest:
                self.IsIterationWithConvergenceTest = False
            else:
                if Constants.SDDPPerformConvergenceTestDuringRun:
                    self.IsIterationWithConvergenceTest = True
            result = False
            self.GenerateTrialScenarios()
            self.ForwardPass()
            self.ComputeCost()
            if Constants.NestedBenders:
                self.UpdateUpperBound_NBD()
            else:
                self.UpdateUpperBound_SDDP()
            self.LastExpectedCostComputedOnAllScenario = self.CurrentExpvalueUpperBound
            self.SafeUpperBoundeOnAllScenario = self.CurrentSafeUpperBound
            self.WriteInTraceFile(
                "Convergence Test, Nr Scenario: %r, LB: %r, (exp UB: %r - safe UB: %r),  Fixed x: %r, Fixed thetavar: %r \n"
                % (self.SDDPNrScenarioTest,  self.CurrentLowerBound, self.CurrentExpvalueUpperBound, self.CurrentSafeUpperBound,  self.HasFixed_ACFEstablishmentVar, self.HasFixed_VehicleAssignmentVar))
            result = self.CheckStoppingCriterion()
        else:
            self.IsIterationWithConvergenceTest = False
            #self.SDDPNrScenarioTest = Constants.SDDPInitNrScenarioTest

        duration = time.time() - self.StartOfAlgorithm

        return result

    def CheckStoppingRelaxationCriterion(self, phase, createpreliminarycuts):

        duration = time.time() - self.StartOfAlgorithm
        if Constants.Debug: print(f"Duration: {duration}")

        optimalitygap = (self.CurrentExpvalueUpperBound - self.CurrentLowerBound) / self.CurrentExpvalueUpperBound
        if Constants.Debug: print(f"Optimality Gap: {optimalitygap}")
        
        optimalitygapreached = (optimalitygap < Constants.SDDPGapRelax)
        if Constants.Debug: print(f"Optimality Gap Reached: {optimalitygapreached}")

        #iterationlimitreached = (self.CurrentIteration > Constants.SDDPNrIterationRelax * phase)
        iterationlimitreached = (self.CurrentIteration > Constants.SDDPNrIterationRelax)
        if Constants.Debug: print(f"Iteration Limit Reached: {iterationlimitreached}")

        durationlimitreached = duration > (Constants.AlgorithmTimeLimit * self.Instance.NrTimeBucket) * 0.5
        if Constants.Debug: print(f"Duration Limit Reached: {durationlimitreached}")

        result = iterationlimitreached or durationlimitreached or optimalitygapreached
        if Constants.Debug: print(f"Result: {result}")

        # self.WriteInTraceFile("Iteration: %d, Duration: %d, LB: %r, (exp UB:%r),  Gap: %r \n"
        #                       % (self.CurrentIteration, duration, self.CurrentLowerBound, self.CurrentExpvalueUpperBound,
        #                          optimalitygap,))

        if Constants.Debug: print("Result: ", result)
        
        if result == True:
            createpreliminarycuts = False

        return result, createpreliminarycuts
            
    #This function runs the SDDP algorithm
    def Run(self):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- (Run)")
        
        if Constants.PrintSDDPTrace:
            self.TraceFile = open(self.TraceFileName, "w")

            self.TraceFile.write("Start the SDDP algorithm \n")
            self.TraceFile.write("Use Papadakos method to generate strong cuts: %r \n"%Constants.GenerateStrongCut)
            self.TraceFile.write("Generate  cuts with linear relaxation: %r \n"%Constants.SolveRelaxationFirst)
            self.TraceFile.write("Generate  WarmUp cuts in SDDP: %r \n"%Constants.WarmUp_SDDP)
            self.TraceFile.write("Generate  cuts with LBF: %r \n" % Constants.SDDPUseEVPI)
            self.TraceFile.write("Generate  cuts with two-stage solution: %r \n" % Constants.SolveRelaxationFirst)
            self.TraceFile.write("Use valid inequalities: %r \n"%Constants.SDDPUseValidInequalities)
            self.TraceFile.write("Run SDDP in a single tree: %r \n"%Constants.SDDPRunSingleTree)
            self.TraceFile.write("SDDP setting: %r \n"%self.TestIdentifier.SDDPSetting )
            self.TraceFile.close()
        self.StartOfAlgorithm = time.time()
       # if Constants.Debug: print("Attention SDDP solve average")

        self.GenerateSAAScenarios2()

        if Constants.Debug:
            print("********************Scenarios SAA*********************")
            for t in self.Instance.TimeBucketSet:
                for w in self.SAAScenarioNrSetInPeriod[t]:
                    print("--------------")
                    print("SAA demand at stage %r in scenario %r:\n %r" % (t, w, self.SetOfSAAScenarioDemand[t][w]))
                    print("SAA Hospital Capacity at stage %r in scenario %r:\n %r" % (t, w, self.SetOfSAAScenarioHospitalCapacity[t][w]))
                    print("SAA WholeDonors at stage %r in scenario %r:\n %r" % (t, w, self.SetOfSAAScenarioWholeDonor[t][w]))
                    print("SAA ApheresisDonors at stage %r in scenario %r:\n %r" % (t, w, self.SetOfSAAScenarioApheresisDonor[t][w]))
                    print("SAA Saascenarioproba at stage %r :\n %r" % (t, self.Saascenarioproba[t]))

        if self.TestIdentifier.Model == Constants.ModelHeuristicMulti_Stage or self.TestIdentifier.Method == Constants.Hybrid or self.TestIdentifier.SDDPSetting == Constants.JustYFix:
            Constants.SDDPGenerateCutWith2Stage = False
            Constants.SolveRelaxationFirst = False
            Constants.SDDPRunSingleTree = False
        else:
            self.ChangeFixedTransToValueOfTwoStage()
        
        createpreliminarycuts = Constants.SolveRelaxationFirst or Constants.SDDPGenerateCutWith2Stage or Constants.WarmUp_SDDP

        phase = 1
        if not Constants.SolveRelaxationFirst:
            phase = 2

        ExitLoop = not createpreliminarycuts and Constants.SDDPRunSingleTree

        DoNotCheckWarmUpIfAgain = False

        Stop = False

        while (not Stop or createpreliminarycuts) and not ExitLoop:

            # if createpreliminarycuts and (Stop or self.CheckStoppingRelaxationCriterion(phase)):
            #     phase += 1            
            #     if phase < 3:
            #         self.ForwardStage[0].ChangeSetupToValueOfTwoStage()
            #         self.WriteInTraceFile("Change stage 1 problem to heuristic solution \n")
            #         self.CurrentUpperBound = Constants.Infinity
            #         self.LastExpectedCostComputedOnAllScenario = Constants.Infinity
            #         self.CurrentLowerBound = 0
            #         self.NrIterationWithoutLBImprovment = 0
            #     else:
            #         ExitLoop = Constants.SDDPRunSingleTree
            #         createpreliminarycuts = False
            #         self.CurrentUpperBound = Constants.Infinity
            #         self.CurrentLowerBound = 0
            #         self.NrIterationWithoutLBImprovment = 0
            #         #Make a convergence test after adding cuts of the two stage
            #         if not ExitLoop:
            #             self.ForwardStage[0].ChangeSetupToBinary()
            #             self.WriteInTraceFile("Change stage 1 problem to integer \n")

            result_CheckStoppingRelaxationCriterion, createpreliminarycuts = self.CheckStoppingRelaxationCriterion(phase, createpreliminarycuts)
            if Constants.WarmUp_SDDP and not DoNotCheckWarmUpIfAgain and (Stop or result_CheckStoppingRelaxationCriterion):        
                    self.CurrentUpperBound = Constants.Infinity
                    self.CurrentLowerBound = 0
                    self.NrIterationWithoutLBImprovment = 0
                    self.ForwardStage[0].ChangeACFEstablishmentVarToBinary()
                    self.ForwardStage[0].ChangeVehicleAssignmentVarToInteger()
                    self.WriteInTraceFile("Change stage 1 problem to integer \n")
                    DoNotCheckWarmUpIfAgain = True


            self.IsIterationWithConvergenceTest = False

            self.GenerateTrialScenarios()

            if Constants.Debug:
                print("********************Scenarios Trial*********************")
                for s in self.CurrentSetOfTrialScenarios:
                    print("Demands: %r" % s.Demands)
                    print("HospitalCaps: %r" % s.HospitalCaps)
                    print("WholeDonors: %r" % s.WholeDonors)
                    print("ApheresisDonors: %r" % s.ApheresisDonors)
                
                if Constants.SDDPForwardPassInSAATree:
                    print("********************Scenarios SAA*********************")
                    for t in self.Instance.TimeBucketSet:
                        for w in self.SAAScenarioNrSetInPeriod[t]:
                            print("SAA demand at stage %r in scenario %r: %r" % (t, w, self.SetOfSAAScenarioDemand[t][w]))
                            print("SAA Hospital Caps at stage %r in scenario %r: %r" % (t, w, self.SetOfSAAScenarioHospitalCapacity[t][w]))
                            print("SAA Whole Donors at stage %r in scenario %r: %r" % (t, w, self.SetOfSAAScenarioWholeDonor[t][w]))
                            print("SAA Apheresis Donors at stage %r in scenario %r: %r" % (t, w, self.SetOfSAAScenarioApheresisDonor[t][w]))
                
                if Constants.SDDPUseEVPI and self.ForwardStage[0].EVPIScenarioSet is not None:
                    print("********************Scenarios EVPI*********************")
                    for s in self.ForwardStage[0].EVPIScenarioSet:
                        print("Demands: %r" % s.Demands)
                        print("HospitalCaps: %r" % s.HospitalCaps)
                        print("WholeDonors: %r" % s.WholeDonors)
                        print("ApheresisDonors: %r" % s.ApheresisDonors)
                
                print("****************************************************")
            
            if Constants.SDDPModifyBackwardScenarioAtEachIteration:
                self.GenerateSAAScenarios2()
            
            self.ForwardPass()
            self.ComputeCost()
            self.UpdateLowerBound()
            if Constants.NestedBenders:
                self.UpdateUpperBound_NBD()
            else:
                self.UpdateUpperBound_SDDP()

            self.BackwardPass()
            self.CurrentIteration = self.CurrentIteration + 1

            if not createpreliminarycuts:# and (not self.HasFixed_FixedTransVar or self.TestIdentifier.Model == Constants.ModelHeuristicMulti_Stage):
                Stop = self.CheckStoppingCriterion()
            #if self.HasFixed_FixedTransVar and not self.TestIdentifier.Model == Constants.ModelHeuristicMulti_Stage:
            else:
                self.CheckStoppingCriterion()
                #self.WriteInTraceFile("Iteration With Fixed Setup  LB: % r, (exp UB: % r) \n"% (self.CurrentLowerBound, self.CurrentExpvalueUpperBound))
            
            duration = time.time() - self.StartOfAlgorithm


            newACFEstablishment = [round(self.ForwardStage[0].ACFEstablishmentValues[0][i], 0)
                                    for i in self.Instance.ACFPPointSet]
            if Constants.Debug: print("New newACFEstablishment Values:\n ", newACFEstablishment)
            newVehicleAssignment = [[round(self.ForwardStage[0].VehicleAssignmentValues[0][m][i], 0)
                                    for i in self.Instance.ACFPPointSet]
                                    for m in self.Instance.RescueVehicleSet]
            if Constants.Debug: print("New newVehicleAssignment Values:\n ", newVehicleAssignment)
        
        if Constants.SDDPRunSingleTree:
            self.RunSingleTreeSDDP()

        self.SDDPNrScenarioTest = 1000           #To test the algorithm, previously was 1000!
        random.seed = self.TestIdentifier.ScenarioSeed  #previously was 9876

        if self.IsIterationWithConvergenceTest == False:
            self.ComputeUpperBound()

        self.RecordSolveInfo()

        if Constants.PrintSDDPTrace:
            self.WriteInTraceFile("End of the SDDP algorithm \n ")    

    def ComputeUpperBound(self):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- (ComputeUpperBound)")
        self.IsIterationWithConvergenceTest = True
        self.GenerateTrialScenarios()
        self.ForwardPass()
        self.ComputeCost()
        if Constants.NestedBenders:
            self.UpdateUpperBound_NBD()
        else:
            self.UpdateUpperBound_SDDP()
        self.LastExpectedCostComputedOnAllScenario = self.CurrentExpvalueUpperBound
        self.SafeUpperBoundeOnAllScenario = self.CurrentSafeUpperBound

        #We obtain The lower bound based on the reference: "Assessing policy quality in a multistage stochastic program for long-term hydrothermal scheduling"
        self.LowerBound_DeMatos = min(self.CurrentExpvalueUpperBound, self.CurrentLowerBound)
        print("self.LowerBound_DeMatos: ", self.LowerBound_DeMatos)
        
        if self.CurrentSafeUpperBound != 0:
            SafeGap = ((self.CurrentSafeUpperBound - self.LowerBound_DeMatos) / self.CurrentSafeUpperBound) * 100
        else:
            SafeGap = float('inf')  


        # Write the values to the trace file
        self.WriteInTraceFile(
            "Convergence Test, Nr Scenario: %r, LB: %r, (exp UB: %r - safe UB: %r), SafeGap: %.2f%% \n"
            % (self.CurrentNrInSampleScenarioToTest, self.LowerBound_DeMatos, self.CurrentExpvalueUpperBound, self.CurrentSafeUpperBound, SafeGap)
        )
    
    def ComputeCost(self):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- (ComputeCost)")

        for stage in self.ForwardStage:
            stage.ComputePassCost()            

    def RecordSolveInfo(self):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- (RecordSolveInfo)")

        self.SolveInfo = [self.Instance.InstanceName,
                          "SDDP",
                          self.LastExpectedCostComputedOnAllScenario,
                          self.SafeUpperBoundeOnAllScenario,
                          self.LowerBound_DeMatos,
                          self.CurrentIteration,
                          time.time() - self.StartOfAlgorithm,
                          0,
                          0,
                          #sol.progress.get_num_iterations(),
                          #sol.progress.get_num_nodes_processed(),
                          0,
                          0,
                          0,
                          0,
                          0,
                          0,
                          0,
                          self.Instance.ACFPPointSet,
                          self.Instance.HospitalSet,
                          self.Instance.DemandSet,
                          self.Instance.FacilitySet,
                          self.Instance.RescueVehicleSet,
                          self.Instance.BloodGPSet,
                          self.Instance.InjuryLevelSet,
                          self.Instance.PlateletAgeSet,
                          self.Instance.NrTimeBucket,
                          0,
                          self.CurrentNrScenario,
                          0]
        
    def CreateSolutionAtFirstStage(self):
        if Constants.Debug: print("\n We are in 'SDDP' Class -- (CreateSolutionAtFirstStage)")
            
        # Get the setup quantitities associated with the solultion
        solacfEstablishment = [[self.GetACFEstablishmentFixedEarlier(i, 0)  
                                for i in self.Instance.ACFPPointSet]]
        if Constants.Debug: print("solacfEstablishment:\n", solacfEstablishment)
        solvehicleAssignment = [[[self.GetVehicleAssignmentFixedEarlier(m, i, 0)  
                                    for i in self.Instance.ACFPPointSet]
                                    for m in self.Instance.RescueVehicleSet]]
        if Constants.Debug: print("solvehicleAssignment:\n", solvehicleAssignment)
        
        #Be careful, becuase y_wti is, in fact, 3-dimensional, we start the following with 3 of brackets.
        solapheresisassignment = [[[self.GetApheresisAssignmentFixedEarlier(i, 0, 0) 
                                    for i in self.Instance.ACFPPointSet]]]
        #if Constants.Debug: print("solapheresisassignment:\n", solapheresisassignment)
        
        soltransshipmentHI = [[[[[[self.GetTransshipmentHIFixedEarlier(c, r, h, i, 0, 0) 
                                    for i in self.Instance.ACFPPointSet] 
                                    for h in self.Instance.HospitalSet] 
                                    for r in self.Instance.PlateletAgeSet] 
                                    for c in self.Instance.BloodGPSet]]]
        #if Constants.Debug: print("soltransshipmentHI:\n", soltransshipmentHI)

        soltransshipmentII = [[[[[[self.GetTransshipmentIIFixedEarlier(c, r, i, iprime, 0, 0) 
                                    for iprime in self.Instance.ACFPPointSet] 
                                    for i in self.Instance.ACFPPointSet] 
                                    for r in self.Instance.PlateletAgeSet] 
                                    for c in self.Instance.BloodGPSet]]]
        #if Constants.Debug: print("soltransshipmentII:\n", soltransshipmentII)
        
        soltransshipmentHH = [[[[[[self.GetTransshipmentHHFixedEarlier(c, r, h, hprime, 0, 0) 
                                    for hprime in self.Instance.HospitalSet] 
                                    for h in self.Instance.HospitalSet] 
                                    for r in self.Instance.PlateletAgeSet] 
                                    for c in self.Instance.BloodGPSet]]]
        #if Constants.Debug: print("soltransshipmentHH:\n", soltransshipmentHH)

        solpatientTransfer = [[[[[[[self.GetPatientTransferFixedEarlier(j, c, l, u, m, 0, 0) 
                                    for m in self.Instance.RescueVehicleSet] 
                                    for u in self.Instance.FacilitySet] 
                                    for l in self.Instance.DemandSet] 
                                    for c in self.Instance.BloodGPSet] 
                                    for j in self.Instance.InjuryLevelSet]]]
        #if Constants.Debug: print("solpatientTransfer:\n", solpatientTransfer)

        solunsatisfiedPatient = [[[[[self.GetUnsatisfiedPatientFixedEarlier(j, c, l, 0, 0) 
                                    for l in self.Instance.DemandSet] 
                                    for c in self.Instance.BloodGPSet] 
                                    for j in self.Instance.InjuryLevelSet]]]
        #if Constants.Debug: print("solunsatisfiedPatient:\n", solunsatisfiedPatient)

        solplateletInventory = [[[[[self.GetPLTInventoryFixedEarlier(c, r, u, 0, 0) 
                                    for u in self.Instance.FacilitySet] 
                                    for r in self.Instance.PlateletAgeSet] 
                                    for c in self.Instance.BloodGPSet]]]
        #if Constants.Debug: print("solplateletInventory:\n", solplateletInventory)

        soloutdatedPlatelet = [[[self.GetOutdatedPlateletFixedEarlier(u, 0, 0) 
                                    for u in self.Instance.FacilitySet]]]
        #if Constants.Debug: print("soloutdatedPlatelet:\n", soloutdatedPlatelet)

        solservedPatient = [[[[[[[self.GetServedPatientFixedEarlier(j, cprime, c, r, u, 0, 0) 
                                    for u in self.Instance.FacilitySet] 
                                    for r in self.Instance.PlateletAgeSet] 
                                    for c in self.Instance.BloodGPSet] 
                                    for cprime in self.Instance.BloodGPSet] 
                                    for j in self.Instance.InjuryLevelSet]]]
        #if Constants.Debug: print("solservedPatient:\n", solservedPatient)

        solpatientPostponement = [[[[[self.GetUnservedPatientFixedEarlier(j, c, u, 0, 0) 
                                    for u in self.Instance.FacilitySet] 
                                    for c in self.Instance.BloodGPSet] 
                                    for j in self.Instance.InjuryLevelSet]]]
        #if Constants.Debug: print("solpatientPostponement:\n", solpatientPostponement)
        
        solplateletApheresisExtraction = [[[[self.GetPlateletApheresisExtractionFixedEarlier(c, u, 0, 0) 
                                            for u in self.Instance.FacilitySet] 
                                            for c in self.Instance.BloodGPSet]]]
        #if Constants.Debug: print("solplateletApheresisExtraction:\n", solplateletApheresisExtraction)

        solplateletWholeExtraction = [[[[self.GetPlateletWholeExtractionFixedEarlier(c, h, 0, 0) 
                                            for h in self.Instance.HospitalSet] 
                                            for c in self.Instance.BloodGPSet]]]
        #if Constants.Debug: print("solplateletWholeExtraction:\n", solplateletWholeExtraction)
        
        
        emptyscenariotree = ScenarioTree(instance=self.Instance,
                                            branchperlevel=[0,0,0,0,0],
                                            seed=self.TestIdentifier.ScenarioSeed)# instance = None, branchperlevel = [], seed = -1, mipsolver = None, evaluationscenario = False, averagescenariotree = False,  givenfirstperiod = [], scenariogenerationmethod = "MC", generateasYQfix = False, model = "Multi_Stage", CopyscenariofromMulti_Stage=False ):
        
        solution = Solution(instance=self.Instance, 
                            solACFEstablishment_x_wi=solacfEstablishment, 
                            solVehicleAssignment_thetavar_wmi=solvehicleAssignment, 
                            solApheresisAssignment_y_wti=solapheresisassignment, 
                            solTransshipmentHI_b_wtcrhi=soltransshipmentHI, 
                            solTransshipmentII_bPrime_wtcrii=soltransshipmentII, 
                            solTransshipmentHH_bDoublePrime_wtcrhh=soltransshipmentHH, 
                            solPatientTransfer_q_wtjclum=solpatientTransfer, 
                            solUnsatisfiedPatient_mu_wtjcl=solunsatisfiedPatient, 
                            solPlateletInventory_eta_wtcru=solplateletInventory, 
                            solOutdatedPlatelet_sigmavar_wtu=soloutdatedPlatelet, 
                            solServedPatient_upsilon_wtjcPcru=solservedPatient, 
                            solPatientPostponement_zeta_wtjcu=solpatientPostponement, 
                            solPlateletApheresisExtraction_lambda_wtcu=solplateletApheresisExtraction, 
                            solPlateletWholeExtraction_Rhovar_wtch=solplateletWholeExtraction, 
                            Final_ACFEstablishmentCost =0,  
                            Final_Vehicle_AssignmentCost =0,  
                            Final_ApheresisAssignmentCost =0,  
                            Final_TransshipmentHICost =0,  
                            Final_TransshipmentIICost =0,  
                            Final_TransshipmentHHCost =0,  
                            Final_PatientTransferCost =0, 
                            Final_UnsatisfiedPatientsCost =0, 
                            Final_PlateletInventoryCost =0, 
                            Final_OutdatedPlateletCost =0, 
                            Final_ServedPatientCost =0, 
                            Final_PatientPostponementCost =0, 
                            Final_PlateletApheresisExtractionCost =0, 
                            Final_PlateletWholeExtractionCost =0, 
                            scenarioset=[0],  
                            scenriotree=emptyscenariotree,  
                            partialsolution=True)

        solution.IsSDDPSolution = True

        solution.SDDPLB = self.LowerBound_DeMatos
        solution.SDDPExpUB = self.LastExpectedCostComputedOnAllScenario
        solution.SDDPSafeUB = self.SafeUpperBoundeOnAllScenario
        solution.SDDPNrIteration = self.CurrentIteration

        solution.SDDPTimeBackward = self.TimeBackward
        solution.SDDPTimeForwardNoTest = self.TimeForwardNonTest
        solution.SDDPTimeForwardTest = self.TimeForwardTest

        solution.GRBGap = self.SingleTreeGRBGap

        return solution
# This class contains the attributes and methods allowing to define the progressive hedging algorithm.
from ScenarioTree import ScenarioTree
from Constants import Constants
from MIPSolver import MIPSolver
from SDDP import SDDP
from ProgressiveHedging import ProgressiveHedging

from Solution import Solution

import copy
import time
import math

class Hybrid_PH_SDDP(object):

    def __init__(self, instance, testidentifier, treestructure, solver):
        if Constants.Debug: print("\n We are in 'Hybrid_PH_SDDP' Class -- Constructor")

        self.Instance = instance
        self.TestIdentifier = testidentifier
        self.TreeStructure = treestructure
        if self.TestIdentifier.HybridPHSetting == "Multiplier100":
            Constants.Rho_PH_PenaltyParameter = 100.0
        if self.TestIdentifier.HybridPHSetting == "Multiplier10":
            Constants.Rho_PH_PenaltyParameter = 10.0
        if self.TestIdentifier.HybridPHSetting == "Multiplier1":
            Constants.Rho_PH_PenaltyParameter = 1.0
        if self.TestIdentifier.HybridPHSetting == "Multiplier01":
            Constants.Rho_PH_PenaltyParameter = 0.1
        if self.TestIdentifier.HybridPHSetting == "Multiplier001":
            Constants.Rho_PH_PenaltyParameter = 0.01
        if self.TestIdentifier.HybridPHSetting == "Multiplier0001":
            Constants.Rho_PH_PenaltyParameter = 0.001
        if self.TestIdentifier.HybridPHSetting == "Multiplier00001":
            Constants.Rho_PH_PenaltyParameter = 0.0001
        if self.TestIdentifier.HybridPHSetting == "Multiplier0":
             Constants.Rho_PH_PenaltyParameter = 0.0

 #       self.TraceFileName = "./Temp/SDDPPHtrace_%s.txt" % (self.TestIdentifier.GetAsString())
#
        self.Solver = solver

        self.NrScenarioOnceYIsFix = self.TestIdentifier.NrScenario

        if not Constants.MIPBasedOnSymetricTree:
            if self.Instance.NrTimeBucket > 5:
             self.TestIdentifier.NrScenario = "all2"
            else:
                self.TestIdentifier.NrScenario = "all5"

        if self.Instance.NrTimeBucket > 5:
            self.TestIdentifier.NrScenario = "all2"

        PHTreestructure = solver.GetTreeStructure()

        self.ProgressiveHedging = ProgressiveHedging(self.Instance, self.TestIdentifier, PHTreestructure)

        self.TestIdentifier.NrScenario = self.NrScenarioOnceYIsFix

    #This function is the main loop of the hybrid progressive hedging/SDDP heuristic
    def Run(self):
        if Constants.Debug: print("\n We are in 'Hybrid_PH_SDDP' Class -- Run")

        #self.GetHeuristicSetup()
        self.ProgressiveHedging.InitTrace()
        self.ProgressiveHedging.CurrentSolution = [None for w in self.ProgressiveHedging.ScenarioNrSet]
        self.PrintOnlyFirstStagePreviousValue = Constants.PrintOnlyFirstStageDecision
        if Constants.PrintOnlyFirstStageDecision:
            Constants.PrintOnlyFirstStageDecision = False

        self.ProgressiveHedging.CurrentIteration = 0
        stop = False
        while not stop:
            self.ProgressiveHedging.SolveScenariosIndependently()
            if False and self.ProgressiveHedging.CurrentIteration == -1:
                treestructure = [1, 200] + [1] * (self.Instance.NrTimeBucket - 1) + [0]
                self.TestIdentifier.Model = Constants.ModelYQFix
                chosengeneration = self.TestIdentifier.ScenarioSampling
                self.ScenarioGeneration = "RQMC"
                solution, mipsolver = self.Solver.MRP(treestructure, False, recordsolveinfo=True)
                self.ProgressiveHedging.GivenSetup = [[solution.Production[0][t][p] for p in self.Instance.ProductSet]
                                                      for t in self.Instance.TimeBucketSet]

                self.ProgressiveHedging.CurrentImplementableSolution= Solution.GetEmptySolution(self.Instance)

                self.ProgressiveHedging.CurrentImplementableSolution.ProductionQuantity = \
                                [[[solution.ProductionQuantity[0][t][p] for p in self.Instance.ProductSet]
                                                                      for t in self.Instance.TimeBucketSet]
                                                                     for w in self.ProgressiveHedging.ScenarioNrSet]

                self.ProgressiveHedging.CurrentImplementableSolution.Production = \
                    [[[solution.Production[0][t][p] for p in self.Instance.ProductSet]
                      for t in self.Instance.TimeBucketSet]
                     for w in self.ProgressiveHedging.ScenarioNrSet]


                self.ProgressiveHedging.CurrentImplementableSolution.Consumption = \
                    [ [[[solution.Consumption[0][t][p][q] for q in self.Instance.ProductSet]
                            for p in self.Instance.ProductSet]
                      for t in self.Instance.TimeBucketSet]
                     for w in self.ProgressiveHedging.ScenarioNrSet]
                solution= self.ProgressiveHedging.CurrentImplementableSolution
            else:
                solution = self.ProgressiveHedging.CreateImplementableSolution()
                self.ProgressiveHedging.CurrentImplementableSolution = solution

            self.ProgressiveHedging.PreviousImplementableSolution = copy.deepcopy(self.ProgressiveHedging.CurrentImplementableSolution)

            self.ProgressiveHedging.CurrentIteration += 1
            
            if self.ProgressiveHedging.CurrentIteration == 1:
                self.ProgressiveHedging.rho_PenaltyParameter = Constants.Rho_PH_PenaltyParameter

            self.ProgressiveHedging.UpdateLagragianMultipliers()

            #Just for the printing:
            stop = self.ProgressiveHedging.CheckStopingCriterion()

            #if Constants.Debug:
            #    self.ProgressiveHedging.PrintCurrentIteration()

        # Rounding First Stage variable obtained from PHA, for using as inputs of SDDP
        self.GivenACFEstablishment = []
        for i in self.Instance.ACFPPointSet:
            if solution.ACFEstablishment_x_wi[0][i] >= 0.5:
                fixed_acfestablishment_value = 1
            else:
                fixed_acfestablishment_value = 0
            self.GivenACFEstablishment.append(fixed_acfestablishment_value)

        if Constants.Debug: print("GivenACFEstablishment: ", self.GivenACFEstablishment)
        
        # Rounding First Stage variable obtained from PHA, for using as inputs of SDDP
        self.GivenVehicleAssignment = []
        for m in self.Instance.RescueVehicleSet:
            acf_list = []
            for i in self.Instance.ACFPPointSet:
                if solution.ACFEstablishment_x_wi[0][i] == 0:
                    fixed_vehicleassign_value = 0
                else:
                    fixed_vehicleassign_value = round(solution.VehicleAssignment_thetavar_wmi[0][m][i])
                acf_list.append(fixed_vehicleassign_value)
            self.GivenVehicleAssignment.append(acf_list)
        if Constants.Debug: print("GivenVehicleAssignment: ", self.GivenVehicleAssignment)
        
        Constants.PrintOnlyFirstStageDecision = self.PrintOnlyFirstStagePreviousValue

        self.RunSDDP()        

    #This function runs SDDP for the current values of the setup
    def RunSDDP(self):
        if Constants.Debug: print("\n We are in 'Hybrid_PH_SDDP' Class -- RunSDDP")

        self.SDDPSolver = SDDP(self.Instance, self.TestIdentifier, self.TreeStructure)

        #Make sure SDDP do not enter in preliminary stage (at the end of the preliminary stage, SDDP would change the setup to binary)
        Constants.SDDPGenerateCutWith2Stage = False
        Constants.SolveRelaxationFirst = False
        Constants.SDDPRunSigleTree = False

        self.SDDPSolver.HeuristicACFEstablishmentValue = self.GivenACFEstablishment
        self.SDDPSolver.HeuristicVehicleAssignmentValue = self.GivenVehicleAssignment

        self.SDDPSolver.Run()
       # return self.SDDPSolver.CreateSolutionOfAllInSampleScenario()
import time
from MIPSolver import MIPSolver
import csv
import datetime
import re
from Constants import Constants
from ScenarioTree import ScenarioTree
import gurobipy as gp
from gurobipy import *
from SDDP import SDDP
from ProgressiveHedging import ProgressiveHedging
from Hybrid_PH_SDDP import Hybrid_PH_SDDP
from MLLocalSearch import MLLocalSearch

class Solver(object):

    #Constructor
    def __init__(self, instance, testidentifier, mipsetting, evaluatesol):
        if Constants.Debug: print("\n We are in 'Solver' Class -- Constructor")
        self.Instance = instance
        self.TestIdentifier = testidentifier
        self.ScenarioGeneration = self.TestIdentifier.ScenarioSampling
        self.GivenACFEstablishment = []
        self.GivenVehicleAssignment = []
        self.MIPSetting = mipsetting
        if Constants.Debug: print("------------Moving from 'Solver' Class Constructor to 'TestIdentifier' class GetAsString---------------")
        self.TestDescription = self.TestIdentifier.GetAsString()
        if Constants.Debug: print("------------Moving BACK from 'TestIdentifier' class GetAsString to 'Solver' Class Constructor---------------")
        self.EvaluateSolution = evaluatesol
        self.TreeStructure = self.GetTreeStructure()
        self.SDDPSolver = None

    #return true if the considered model is a two-stage formulation or reduction
    def Use_Two_Stage(self):
        if Constants.Debug: print("\n We are in 'Solver' Class -- Use_Two_Stage")
        use_two_stage = self.TestIdentifier.Model == Constants.Two_Stage \
                    or self.TestIdentifier.Model == Constants.Average
        return use_two_stage
    
    #This method call the right method
    def Solve(self):
        if Constants.Debug: print("\n We are in 'Solver' Class -- Solve")
        solution = None
        if self.Use_Two_Stage():
            solution = self.Solve_Use_Two_Stage()
        
        if self.TestIdentifier.Model == Constants.ModelMulti_Stage:
            solution = self.SolveMulti_Stage()
        
        if self.TestIdentifier.Model == Constants.ModelHeuristicMulti_Stage:
            solution = self.SolveMulti_StageHeuristic()


        self.PrintSolutionToFile(solution)

        return solution

    def PrintSolutionToFile(self, solution):
        if Constants.Debug: print("\n We are in 'Solver' Class -- PrintSolutionToFile")

        if Constants.Debug: print("------------Moving from 'Solver' Class ('PrintSolutionToFile' Function) to 'TestIdentifier' class (GetAsString))---------------")
        testdescription = self.TestIdentifier.GetAsString()
        if Constants.Debug: print("------------Moving BACK from 'TestIdentifier' class (GetAsString) to 'Solver' Class ('PrintSolutionToFile' Function))---------------")
        
        if Constants.PrintSolutionFileToPickle:
            solution.PrintToPickle(testdescription)
        
        if Constants.PrintSolutionFileToExcel:
            solution.PrintToExcel(testdescription)

    def CRP(self, treestructur, averagescenario=False, recordsolveinfo=False, Multi_Stageheuristic=False, warmstart=False):    
        if Constants.Debug: print("\n We are in 'Solver' Class -- CRP")
        scenariotreemodel = self.TestIdentifier.Model
        
        if Constants.Debug: print("------------Moving from 'Solver' Class ('CRP' Function) to 'ScenarioTree' class Constructor---------------")
        scenariotree = ScenarioTree(self.Instance, treestructur, self.TestIdentifier.ScenarioSeed,
                                    averagescenariotree=averagescenario,
                                    scenariogenerationmethod=self.ScenarioGeneration,
                                    model=scenariotreemodel,
                                    issymetric=(Constants.MIPBasedOnSymetricTree and scenariotreemodel == Constants.ModelMulti_Stage))        
        if Constants.Debug: print("------------Moving BACK from 'ScenarioTree' class Constructor to 'Solver' Class ('CRP' Function)---------------")

        if Constants.Debug: print("------------Moving from 'Solver' Class ('CRP' Function) to 'ScenarioTree' class ('GetAllScenarios' Function))---------------")
        scenarioset = scenariotree.GetAllScenarios(computeindex=False)
        if Constants.Debug: print("------------Moving BACK from 'ScenarioTree' class ('GetAllScenarios' Function) to 'Solver' Class ('CRP' Function))---------------")
        
        MIPModel = self.TestIdentifier.Model

        if self.TestIdentifier.Model == Constants.Average:
            MIPModel = Constants.Two_Stage

        if Constants.Debug: print("------------Moving from 'Solver' Class ('CRP' Function) to 'MIPSolver' class Constructor---------------")
        mipsolver = MIPSolver(self.Instance, 
                              MIPModel, 
                              scenariotree, 
                              evpi=self.TestIdentifier.EVPI,
                              implicitnonanticipativity=(not self.TestIdentifier.EVPI),
                              evaluatesolution=self.EvaluateSolution,
                              Multi_Stageheuristic=Multi_Stageheuristic,
                              givenacfestablishment=self.GivenACFEstablishment,
                              givenvehicleassinment=self.GivenVehicleAssignment,
                              mipsetting=self.TestIdentifier.MIPSetting,
                              warmstart=warmstart,
                              logfile=self.TestDescription) 
        if Constants.Debug: print("------------Moving BACK from 'MIPSolver' class Constructor to 'Solver' Class ('CRP' Function)---------------")
       
        if Constants.Debug:
            print("------------Moving from 'Solver' Class ('CRP' Function) to 'Instance' class ('PrintInstance' Function))---------------")
            self.Instance.PrintInstance()
            print("------------Moving BACK from 'Instance' class ('PrintInstance' Function) to 'Solver' Class ('CRP' Function))---------------")


        if Constants.PrintScenarios:
            if Constants.Debug: print("------------Moving from 'Solver' Class ('CRP' Function) to 'MIPSolver' class ('PrintScenarioToFile' Function))---------------")
            mipsolver.PrintScenarioToFile()
            if Constants.Debug: print("------------Moving BACK from 'MIPSolver' class ('PrintScenarioToFile' Function) to 'Solver' Class ('CRP' Function))---------------")

        if Constants.Debug:
            print("Start to model in Gurobi")  
            print("------------Moving from 'Solver' Class ('CRP' Function) to 'MIPSolver' class ('BuildModel' Function))---------------")
        mipsolver.BuildModel()

        if Constants.Debug: print("------------Moving BACK from 'MIPSolver' class ('BuildModel' Function) to 'Solver' Class ('CRP' Function))---------------")
        
        if Constants.Debug: print("------------Moving from 'Solver' Class ('CRP' Function) to 'MIPSolver' class ('Solve' Function))---------------")

        solution = mipsolver.Solve()

        if Constants.Debug: print("------------Moving BACK from 'MIPSolver' class ('Solve' Function) to 'Solver' Class ('CRP' Function))---------------")

        return solution, mipsolver
                            
    #Solve the two-stage version of the problem    
    def Solve_Use_Two_Stage(self):
        if Constants.Debug: print("\n We are in 'Solver' Class -- Solve_Use_Two_Stage")

        tmpmodel = self.TestIdentifier.Model
        
        start = time.time()

        average = False
        
        # The following two lines, get the "self.TestIdentifier.NrScenario" as a string, like "all2", and give us the integer part of it to build the scenario tree in 2-stage model!
        #intPart_NrScenario = re.findall(r'\d+', self.TestIdentifier.NrScenario)
        #nrscenario = int(intPart_NrScenario[0]) * self.Instance.NrTimeBucket if intPart_NrScenario else None
        ####

        if Constants.IsDeterministic(self.TestIdentifier.Model):
            average = True
            nrscenario = 1
            self.TestIdentifier.Model = Constants.Average

        treestructure = self.TreeStructure
        solution, mipsolver = self.CRP(treestructure, average, recordsolveinfo=True )
        
        end = time.time()
        solution.TotalTime = round((end - start), 2)

        self.Model = tmpmodel

        return solution
    
    #This function solve the multi-stage stochastic optimization model
    def SolveMulti_Stage(self):
        if Constants.Debug: print("\n We are in 'Solver' Class -- SolveMulti_Stage")
        start = time.time()

        methodtemp = self.TestIdentifier.Method

        if self.TestIdentifier.Method == Constants.MIP:
            treestructure = self.TreeStructure
            self.TestIdentifier.Model = Constants.ModelMulti_Stage
            chosengeneration = self.TestIdentifier.ScenarioSampling
            self.ScenarioGeneration = "RQMC"
            solution, mipsolver = self.CRP(treestructure, False, recordsolveinfo=True)

            self.ScenarioGeneration = chosengeneration
            self.TestIdentifier.Model = Constants.ModelMulti_Stage
            self.TestIdentifier.Method = methodtemp
      
        if self.TestIdentifier.Method == Constants.SDDP:
            Constants.NestedBenders = False
            self.TreeStructure = self.GetTreeStructure()
            if Constants.Debug: print("------------Moving from 'Solver' Class (SolveMulti_Stage) to 'SDDP' class (Constructor)---------------")
            self.SDDPSolver = SDDP(self.Instance, self.TestIdentifier, self.TreeStructure)
            if Constants.Debug: print("------------Moving BACK from 'SDDP' class (Constructor) to 'Solver' Class (SolveMulti_Stage)---------------")
            self.SDDPSolver.HeuristicACFEstablishmentValue = self.GivenACFEstablishment
            self.SDDPSolver.HeuristicVehicleAssignmentValue = self.GivenVehicleAssignment
            if Constants.Debug: print("------------Moving from 'Solver' Class (SolveMulti_Stage) to 'SDDP' class (Run)---------------")
            self.SDDPSolver.Run()
            if Constants.Debug: print("------------Moving BACK from 'SDDP' class (Run) to 'Solver' Class (SolveMulti_Stage)---------------")
            if Constants.PrintOnlyFirstStageDecision:
               solution = self.SDDPSolver.CreateSolutionAtFirstStage()
            else:
                solution = self.SDDPSolver.CreateSolutionOfAllInSampleScenario()
            if Constants.SDDPSaveInExcel:
               self.SDDPSolver.SaveSolver()

        if self.TestIdentifier.Method == Constants.NBD:
            Constants.NestedBenders = True

            self.TreeStructure = self.GetTreeStructure()
            if Constants.Debug: print("------------Moving from 'Solver' Class (SolveMulti_Stage) to 'SDDP' class (Constructor)---------------")
            self.SDDPSolver = SDDP(self.Instance, self.TestIdentifier, self.TreeStructure)
            if Constants.Debug: print("------------Moving BACK from 'SDDP' class (Constructor) to 'Solver' Class (SolveMulti_Stage)---------------")
            self.SDDPSolver.HeuristicACFEstablishmentValue = self.GivenACFEstablishment
            self.SDDPSolver.HeuristicVehicleAssignmentValue = self.GivenVehicleAssignment
            if Constants.Debug: print("------------Moving from 'Solver' Class (SolveMulti_Stage) to 'SDDP' class (Run)---------------")
            self.SDDPSolver.Run()
            if Constants.Debug: print("------------Moving BACK from 'SDDP' class (Run) to 'Solver' Class (SolveMulti_Stage)---------------")
            if Constants.PrintOnlyFirstStageDecision:
               solution = self.SDDPSolver.CreateSolutionAtFirstStage()
            else:
                solution = self.SDDPSolver.CreateSolutionOfAllInSampleScenario()
            if Constants.SDDPSaveInExcel:
               self.SDDPSolver.SaveSolver()
          
        if self.TestIdentifier.Method == Constants.ProgressiveHedging:
            self.TreeStructure = self.GetTreeStructure()

            self.ProgressiveHedging = ProgressiveHedging(self.Instance, self.TestIdentifier, self.TreeStructure)
            solution = self.ProgressiveHedging.Run()
        
        if self.TestIdentifier.Method == Constants.Hybrid:
            self.TreeStructure = self.GetTreeStructure()

            self.Hybrid = Hybrid_PH_SDDP(self.Instance, self.TestIdentifier, self.TreeStructure, self)
            self.Hybrid.Run()
            if Constants.PrintOnlyFirstStageDecision:
                solution = self.Hybrid.SDDPSolver.CreateSolutionAtFirstStage()
            else:
                 solution = self.Hybrid.SDDPSolver.CreateSolutionOfAllInSampleScenario()

            self.SDDPSolver = self.Hybrid.SDDPSolver
            if Constants.SDDPSaveInExcel:
                self.SDDPSolver.SaveSolver()
               
        if self.TestIdentifier.Method == Constants.MLLocalSearch:
            self.MLLocalSearch = MLLocalSearch(self.Instance, self.TestIdentifier, self.TreeStructure, self)

            solution = self.MLLocalSearch.Run()
            self.SDDPSolver = self.MLLocalSearch.SDDPSolver
            if Constants.PrintOnlyFirstStageDecision:
                solution = self.SDDPSolver.CreateSolutionAtFirstStage()
            else:
                solution = self.SDDPSolver.CreateSolutionOfAllInSampleScenario()

            solution.MLLocalSearchLB =  self.MLLocalSearch.MLLocalSearchLB
            solution.MLLocalSearchTimeBestSol = self.MLLocalSearch.MLLocalSearchTimeBestSol

            if Constants.SDDPSaveInExcel:
                self.SDDPSolver.SaveSolver()
                        
        end = time.time()
        solution.TotalTime = round((end - start), 2)
        return solution

    # Run the method Heuristic Multi_Stage: First solve the 2-stage problem to fix the Y variables, then solve the multi-stages problem on large scenario tree.
    def SolveMulti_StageHeuristic(self):
        if Constants.Debug: print("\n We are in 'Solver' Class -- SolveMulti_StageHeuristic")

        start = time.time()
        
        if self.Instance.NrTimeBucket == 2:
            Constants.NrScenarioinHeuristicTwoStageModel = 8
        elif self.Instance.NrTimeBucket == 3:
            Constants.NrScenarioinHeuristicTwoStageModel = 4
        elif self.Instance.NrTimeBucket == 4:
            Constants.NrScenarioinHeuristicTwoStageModel = 3
        elif self.Instance.NrTimeBucket >= 5:
            Constants.NrScenarioinHeuristicTwoStageModel = 3

        treestructure = [Constants.NrScenarioinHeuristicTwoStageModel ** self.Instance.NrTimeBucket] + [1] * (self.Instance.NrTimeBucket - 1) #5 is chosen randomly (It is for the starting solution to be used in the Heuristic approach)
        
        self.TestIdentifier.Model = Constants.Two_Stage
        chosengeneration = self.ScenarioGeneration
        self.ScenarioGeneration = Constants.RQMC
        solution, mipsolver = self.CRP(treestructure, False, recordsolveinfo=True)
        print("ACFEstablishment_x_wi: ", solution.ACFEstablishment_x_wi)
        print("VehicleAssignment_thetavar_wmi: ", solution.VehicleAssignment_thetavar_wmi)
        self.GivenACFEstablishment = [solution.ACFEstablishment_x_wi[0][i] 
                                        for i in self.Instance.ACFPPointSet] 
        self.GivenVehicleAssignment = [[solution.VehicleAssignment_thetavar_wmi[0][m][i] 
                                        for i in self.Instance.ACFPPointSet] 
                                        for m in self.Instance.RescueVehicleSet]
        
        if Constants.Debug: self.Instance.PrintInstance()

        self.ScenarioGeneration = chosengeneration

        self.TreeStructure = self.GetTreeStructure()

        if self.TestIdentifier.Method == Constants.MIP:
            self.TestIdentifier.Model = Constants.ModelMulti_Stage
            solution, mipsolver = self.CRP(self.TreeStructure,
                                      averagescenario=False,
                                      recordsolveinfo=True,
                                      Multi_Stageheuristic=True)
            self.TestIdentifier.Model = Constants.ModelHeuristicMulti_Stage

        if self.TestIdentifier.Method == Constants.SDDP:
            self.TestIdentifier.Model = Constants.ModelHeuristicMulti_Stage

            self.SDDPSolver = SDDP(self.Instance, self.TestIdentifier, self.TreeStructure)
            self.SDDPSolver.HasFixed_ACFEstablishmentVar = True
            self.SDDPSolver.HasFixed_VehicleAssignmentVar = True
            self.SDDPSolver.HeuristicACFEstablishmentValue = self.GivenACFEstablishment
            self.SDDPSolver.HeuristicVehicleAssignmentValue = self.GivenVehicleAssignment
            self.SDDPSolver.Run()
            
            if Constants.PrintOnlyFirstStageDecision:
               solution = self.SDDPSolver.CreateSolutionAtFirstStage()
            else:
                solution = self.SDDPSolver.CreateSolutionOfAllInSampleScenario()
            
            if Constants.SDDPSaveInExcel:
               self.SDDPSolver.SaveSolver()

        if self.TestIdentifier.Method == Constants.ProgressiveHedging:
            self.TestIdentifier.Model = Constants.ModelHeuristicMulti_Stage

            self.ProgressiveHedging = ProgressiveHedging(self.Instance, self.TestIdentifier, self.TreeStructure, givenfixedtrans=self.GivenFixedTrans)
            solution = self.ProgressiveHedging.Run()


        end = time.time()
        solution.TotalTime = end - start
        return solution
            
    #Define the tree  structur do be used
    def GetTreeStructure(self):
        if Constants.Debug: print("\n We are in 'Solver' Class -- GetTreeStructure")
        treestructure = []
        nrtimebucketconsidered = self.Instance.NrTimeBucket
        
        if Constants.IsDeterministic(self.TestIdentifier.Model):
            treestructure = [1] * (nrtimebucketconsidered - 1) + [0]  #we have (+ [0]), because the last nodes do not have any branches.
            if Constants.Debug: print("treestructure for Deterministic Model with Average Demand:\n",treestructure)

        if self.TestIdentifier.Model == Constants.Two_Stage:
            # The following two lines, get the "self.TestIdentifier.NrScenario" as a string, like "all2", and give us the integer part of it to build the scenario tree in 2-stage model!
            intPart_NrScenario = re.findall(r'\d+', self.TestIdentifier.NrScenario)
            intNrScenario = int(intPart_NrScenario[0]) if intPart_NrScenario else None
            ####
                    
            treestructure = [intNrScenario ** self.Instance.NrTimeBucket] + [1] * (nrtimebucketconsidered - 1)
            if Constants.Debug: print("treestructure for Two_Stage Model:\n",treestructure)        

        if self.TestIdentifier.Model == Constants.ModelMulti_Stage:
            # Extract the integer part of NrScenario, default to None if not found
            intPart_NrScenario = re.findall(r'\d+', self.TestIdentifier.NrScenario)
            intNrScenario = int(intPart_NrScenario[0]) if intPart_NrScenario else None

            # Initialize treestructure with the first element as 0
            treestructure = [0] * nrtimebucketconsidered
            # Determine the number of scenarios to apply from the second element onwards
            nrScenarios = 1  # Default to 1 if not specified
            if self.TestIdentifier.NrScenario.startswith("all"):
                nrScenarios = int(self.TestIdentifier.NrScenario[3:])
            elif intNrScenario is not None:
                nrScenarios = intNrScenario

            # Update the treestructure from the second element with the determined number of scenarios
            for i in range(0, nrtimebucketconsidered):
                treestructure[i] = nrScenarios

            if Constants.Debug: print("treestructure for Stochastic Model:\n", treestructure)

        return treestructure

    #Define the tree  structur do be used in VSS Calculation
    def GetTreeStructure_EEV(self):
        if Constants.Debug: print("\n We are in 'Solver' Class -- GetTreeStructure_EEV")
        treestructure_EEV = []
        nrtimebucketconsidered = self.Instance.NrTimeBucket
        
        if Constants.IsDeterministic(self.TestIdentifier.Model):
            treestructure_EEV = [1] * (nrtimebucketconsidered - 1) + [0]  #we have (+ [0]), because the last nodes do not have any branches.
            if Constants.Debug: print("treestructure_EEV for Deterministic Model with Average Demand:\n",treestructure_EEV)

        if self.TestIdentifier.Model == Constants.ModelMulti_Stage:
            # Extract the integer part of NrScenario, default to None if not found
            intPart_NrScenario = re.findall(r'\d+', self.TestIdentifier.NrScenario)
            intNrScenario = int(intPart_NrScenario[0]) if intPart_NrScenario else None

            # Initialize treestructure_EEV with the first element as 0
            treestructure_EEV = [0] * nrtimebucketconsidered
            # Determine the number of scenarios to apply from the second element onwards
            nrScenarios = 1  # Default to 1 if not specified
            if self.TestIdentifier.NrScenario.startswith("all"):
                nrScenarios = 1
            elif intNrScenario is not None:
                nrScenarios = 1

            # Update the treestructure from the second element with the determined number of scenarios
            for i in range(0, nrtimebucketconsidered):
                treestructure_EEV[i] = nrScenarios

            if Constants.Debug: print("treestructure_EEV for Stochastic Model:\n", treestructure_EEV)

        return treestructure_EEV
# This class contains the attributes and methods allowing to define the progressive hedging algorithm.

from ScenarioTree import ScenarioTree
from Constants import Constants
from MIPSolver import MIPSolver
from Solution import Solution
import gurobipy as gp
from gurobipy import *

import copy
import time
import math
import os

# Define the directory path relative to the current script location
directory = "./PH_Model_lp"
try:
    os.makedirs(directory, exist_ok=True)
except OSError as e:
    if e.errno != os.errno.EEXIST:
        raise

#This class give the methods for the classical Progressive Hedging approach
class ProgressiveHedging(object):

    def __init__(self, instance, testidentifier, treestructure, scenariotree=None, givenacfestablishments=[], givenvehicleassinments=[], fixuntil=-2):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- Constructor")

        self.Instance = instance
        self.TestIdentifier = testidentifier
        self.TreeStructure = treestructure

        ########## The Following block of code is only for the when that we terminate PH earlier than its convergence. As a result, it may lead to infeasible solutions!
        # That is why we do the following calculations, to prevent infeasibility! However, note that, using this way cause having not good solutions at the end of the day!
        if len(givenacfestablishments) > 0:
            givenacfestablishments = [min(round(x), 1) for x in givenacfestablishments]
        if len(givenvehicleassinments) > 0:
            for m in range(len(givenvehicleassinments)):  
                for i in range(len(givenacfestablishments)):  
                    if givenacfestablishments[i] == 0:
                        givenvehicleassinments[m][i] = 0.0
                    
        ##########
        if Constants.Debug: print("givenacfestablishments: ", givenacfestablishments)
        if Constants.Debug: print("givenvehicleassinments: ", givenvehicleassinments)
        self.GivenACFEstablishment = givenacfestablishments
        self.GivenVehicleAssignment = givenvehicleassinments
        self.SolveWithfixedACFEstablishment = len(self.GivenACFEstablishment) > 0
        self.SolveWithfixedVehicleAssignment = len(self.GivenVehicleAssignment) > 0
        self.Evaluation = False

        self.GenerateScenarios(scenariotree)

        self.FixedUntil = fixuntil

        self.rho_PenaltyParameter = 0
        self.CurrentImplementableSolution = None

        self.PreviouBeta = 0.5

        self.TraceFileName = "./Temp/PHtrace_%s_Evaluation_%s.txt" % (self.TestIdentifier.GetAsString(), Constants.Evaluation_Part)
        
        ####################### ACFEstablishment
        self.LagrangianACFEstablishment = [[0 for i in self.Instance.ACFPPointSet]
                                            for w in self.ScenarioNrSet]

        self.lambda_LinearLagACFEstablishment = [[0 for i in self.Instance.ACFPPointSet]
                                                    for w in self.ScenarioNrSet]
        ####################### VehicleAssignment
        self.LagrangianVehicleAssignment = [[[0 for i in self.Instance.ACFPPointSet]
                                                for m in self.Instance.RescueVehicleSet]
                                                for w in self.ScenarioNrSet]

        self.lambda_LinearLagVehicleAssignment = [[[0 for i in self.Instance.ACFPPointSet]
                                                        for m in self.Instance.RescueVehicleSet]
                                                        for w in self.ScenarioNrSet]

        ####################### ApheresisAssignment
        self.LagrangianApheresisAssignment = [[[0 for i in self.Instance.ACFPPointSet]
                                                    for t in self.Instance.TimeBucketSet]
                                                    for w in self.ScenarioNrSet]

        self.lambda_LinearLagApheresisAssignment = [[[0 for i in self.Instance.ACFPPointSet]
                                                        for t in self.Instance.TimeBucketSet]
                                                        for w in self.ScenarioNrSet]
        ####################### TransshipmentHI
        self.LagrangianTransshipmentHI = [[[[[[0 for i in self.Instance.ACFPPointSet]
                                                for h in self.Instance.HospitalSet]
                                                for r in self.Instance.PlateletAgeSet]
                                                for c in self.Instance.BloodGPSet]
                                                for t in self.Instance.TimeBucketSet]
                                                for w in self.ScenarioNrSet]

        self.lambda_LinearLagTransshipmentHI = [[[[[[0 for i in self.Instance.ACFPPointSet]
                                                        for h in self.Instance.HospitalSet]
                                                        for r in self.Instance.PlateletAgeSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for t in self.Instance.TimeBucketSet]
                                                        for w in self.ScenarioNrSet]
        ####################### TransshipmentII
        self.LagrangianTransshipmentII = [[[[[[0 for iprime in self.Instance.ACFPPointSet]
                                                for i in self.Instance.ACFPPointSet]
                                                for r in self.Instance.PlateletAgeSet]
                                                for c in self.Instance.BloodGPSet]
                                                for t in self.Instance.TimeBucketSet]
                                                for w in self.ScenarioNrSet]

        self.lambda_LinearLagTransshipmentII = [[[[[[0 for iprime in self.Instance.ACFPPointSet]
                                                        for i in self.Instance.ACFPPointSet]
                                                        for r in self.Instance.PlateletAgeSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for t in self.Instance.TimeBucketSet]
                                                        for w in self.ScenarioNrSet]
        ####################### TransshipmentHH
        self.LagrangianTransshipmentHH = [[[[[[0 for hprime in self.Instance.HospitalSet]
                                                for h in self.Instance.HospitalSet]
                                                for r in self.Instance.PlateletAgeSet]
                                                for c in self.Instance.BloodGPSet]
                                                for t in self.Instance.TimeBucketSet]
                                                for w in self.ScenarioNrSet]

        self.lambda_LinearLagTransshipmentHH = [[[[[[0 for hprime in self.Instance.HospitalSet]
                                                        for h in self.Instance.HospitalSet]
                                                        for r in self.Instance.PlateletAgeSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for t in self.Instance.TimeBucketSet]
                                                        for w in self.ScenarioNrSet]


        self.CurrentIteration = 0
        self.StartTime = time.time()
        self.BuildMIPs2()

    #This function creates the scenario tree
    def GenerateScenarios(self, scenariotree=None):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- GenerateScenarios")
        #Build the scenario tree
        if Constants.Debug: print(self.TreeStructure)
        if scenariotree is None:
            self.ScenarioTree = ScenarioTree(self.Instance, self.TreeStructure, self.TestIdentifier.ScenarioSeed,
                                             scenariogenerationmethod=self.TestIdentifier.ScenarioSampling,
                                             issymetric=Constants.MIPBasedOnSymetricTree,
                                             model=Constants.ModelMulti_Stage)
        else:
            self.ScenarioTree = scenariotree

        self.ScenarioSet = self.ScenarioTree.GetAllScenarios(False)
        print("self.ScenarioSet: ", self.ScenarioSet)
        # for s in self.ScenarioSet:
        #     print("Demandssss:\n ", s.Demands)
        #     print("HospitalCapssss:\n ", s.HospitalCaps)
        #     print("WholeDonorssss:\n ", s.WholeDonors)
        #     print("ApheresisDonorssss:\n ", s.ApheresisDonors)
        
        self.ScenarioNrSet = range(len(self.ScenarioSet))
        if Constants.Debug: print("self.ScenarioNrSet: ", self.ScenarioNrSet)
        
        self.SplitScenrioTree2()

    def BuildMIPs2(self):
        #Build the mathematicals models (1 per scenarios)
        #mipset = [0]
        mipset = range(self.NrMIPBatch)

        print("self.SplitedScenarioTree[w]: ", self.SplitedScenarioTree[0])
        self.MIPSolvers = [MIPSolver(self.Instance, Constants.ModelMulti_Stage, self.SplitedScenarioTree[w],
                                     Multi_Stageheuristic=self.SolveWithfixedACFEstablishment,
                                     givenapheresisassignment=[],  
                                     giventransshipmentHI=[],  
                                     giventransshipmentII=[],  
                                     giventransshipmentHH=[],  
                                     givenacfestablishment = self.GivenACFEstablishment,  
                                     givenvehicleassinment = self.GivenVehicleAssignment,  
                                     logfile="NO",
                                     expandfirstnode=True)
                                        for w in mipset]

        self.SetFixedUntil(self.FixedUntil)

        for w in mipset:
            self.MIPSolvers[w].BuildModel()

            if Constants.Debug:
                # Define the path for the LP file within the newly created (or existing) directory
                file_path = os.path.join(directory, f"PH_MathematicalModel_w_{w}.lp")
                # Write the model to the file
                self.MIPSolvers[w].CRPBIM.write(file_path)

    def SplitScenrioTree(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- SplitScenrioTree")

        treestructure = [1] * self.Instance.NrTimeBucket
        self.SplitedScenarioTree = [None for s in self.ScenarioNrSet]

        for scenarionr in self.ScenarioNrSet:
            scenario = self.ScenarioSet[scenarionr]
            self.SplitedScenarioTree[scenarionr] = ScenarioTree(self.Instance, treestructure, 0,
                                                              givenfirstperiod=scenario.Demands,
                                                              scenariogenerationmethod=self.TestIdentifier.ScenarioSampling,
                                                              model=Constants.ModelMulti_Stage)
            
    def SplitScenrioTree2(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- SplitScenrioTree2")

        #batchsize = 1030
        batchsize = 1
        self.NrMIPBatch = int(math.ceil(len(self.ScenarioNrSet)/(batchsize)))
        if Constants.Debug: print("Total number of batches:", self.NrMIPBatch)
        self.Indexscenarioinbatch = [None for m in range(self.NrMIPBatch)]
        self.Scenarioinbatch = [None for m in range(self.NrMIPBatch)]
        self.SplitedScenarioTree = [None for m in range(self.NrMIPBatch)]
        self.BatchofScenario = [int(math.floor(w/batchsize)) for w in self.ScenarioNrSet]
        self.NewIndexOfScenario = [ w % batchsize for w in self.ScenarioNrSet]

        if Constants.Debug: print("Batch of each scenario:", self.BatchofScenario)
        if Constants.Debug: print("New index of each scenario within its batch:", self.NewIndexOfScenario)

        for m in range(self.NrMIPBatch):

            firstscenarioinbatch = m * batchsize
            lastscenarioinbatch = min((m+1) * batchsize, len(self.ScenarioNrSet))
            nrscenarioinbatch = lastscenarioinbatch - firstscenarioinbatch
            
            if Constants.Debug: print("\nProcessing Batch #", m+1)
            if Constants.Debug: print("First scenario index in batch:", firstscenarioinbatch)
            if Constants.Debug: print("Last scenario index in batch:", lastscenarioinbatch)
            if Constants.Debug: print("Number of scenarios in batch:", nrscenarioinbatch)

            self.Indexscenarioinbatch[m] = range(firstscenarioinbatch, lastscenarioinbatch)
            self.Scenarioinbatch[m] = [self.ScenarioSet[w] for w in self.Indexscenarioinbatch[m]]

            if Constants.Debug: print("Scenarios in Batch #", m+1, ":", self.Scenarioinbatch[m])

            #treestructure = [1] * (self.Instance.NrTimeBucket - 1) + [0]
            treestructure = [1] * (self.Instance.NrTimeBucket)

            if Constants.Debug: print("Tree structure for Batch #", m+1, ":", treestructure)

            self.SplitedScenarioTree[m] = ScenarioTree(self.Instance, treestructure, 0,
                                                                    givenscenarioset=self.Scenarioinbatch[m],
                                                                    CopyscenariofromMulti_Stage = True,
                                                                    scenariogenerationmethod=self.TestIdentifier.ScenarioSampling,
                                                                    model=Constants.ModelMulti_Stage)    
              

        if Constants.Debug: print("self.SplitedScenarioTree: ", self.SplitedScenarioTree) 

    def SetFixedUntil(self, time):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- SetFixedUntil")      
        # for w in self.ScenarioNrSet:
        self.MIPSolvers[0].FixSolutionUntil = time
        self.MIPSolvers[0].DemandKnownUntil = time + 1      

    def CheckStopingCriterion(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- CheckStopingCriterion")      
        gapX = Constants.Infinity
        gapThetavar = Constants.Infinity

        if Constants.ProgressiveHedging: #Because, only if we use pure PH, then we need to be sure that all variables are implmentable, otherwise, we develope a kind of Heuristic PH only which obtains implementable solutions in the First-stgae!
            gapY = Constants.Infinity
            gapB = Constants.Infinity
            gapBPrime = Constants.Infinity
            gapBDoublePrime = Constants.Infinity
        else:
            gapY = 0
            gapB = 0
            gapBPrime = 0
            gapBDoublePrime = 0            

        if self.CurrentIteration > 0:
            gapX = self.ComputeConvergenceX()
            gapThetavar = self.ComputeConvergenceThetavar()
            if Constants.ProgressiveHedging:    #Only when we are applying pure PH
                gapY = self.ComputeConvergenceY()
                gapB = self.ComputeConvergenceB()
                gapBPrime = self.ComputeConvergenceBPrime()
                gapBDoublePrime = self.ComputeConvergenceBDoublePrime()

        convergencereached = ((gapX < Constants.PHConvergenceTolerence) and 
                              (gapThetavar < Constants.PHConvergenceTolerence) and 
                              (gapY < Constants.PHConvergenceTolerence) and 
                              (gapB < Constants.PHConvergenceTolerence) and 
                              (gapBPrime < Constants.PHConvergenceTolerence) and 
                              (gapBDoublePrime < Constants.PHConvergenceTolerence))

        duration = time.time() - self.StartTime
        timelimitreached = duration > Constants.AlgorithmTimeLimit
        iterationlimitreached = self.CurrentIteration > Constants.PHIterationLimit
        result = convergencereached or timelimitreached or iterationlimitreached

        if Constants.PrintSDDPTrace and self.CurrentIteration > 0:
            #self.CurrentImplementableSolution.ComputeInventory()
            self.CurrentImplementableSolution.ComputeCost()

            dualconv = -1
            primconv = -1
            lpenalty = self.GetLinearPenalty()
            qpenalty = self.GetQuadraticPenalty()
            ratequad_lin = self.RateQuadLinear()
            ratechangeimplem = -1
            ratedualprimal = -1
            rateprimaldual = -1
            if self.CurrentIteration > 1:
                primconv = self.GetPrimalConvergenceIndice()
                dualconv = self.GetDualConvergenceIndice()
                ratechangeimplem = self.RateLargeChangeInImplementable()
                rateprimaldual = self.RatePrimalDual()
                ratedualprimal = self.RateDualPrimal()

            trace_message = (
                "Iteration: %r, Duration: %.2f, GapX: %.2f, GapThetavar: %.2f, GapY: %.2f, GapB: %.2f, GapB': %.2f, GapB'': %.2f, UB: %.2f, linear penalty: %.2f, "
                "quadratic penalty: %.2f, Multiplier: %.6f, primal conv: %.2f, dual conv: %.2f, "
                "Rate Large Change(l): %.2f, rate quad_lin(s): %.2f, rateprimaldual(l<-): %.2f, "
                "ratedualprimal(l->): %.2f, convergenceX: %.2f, convergenceThetavar: %.2f,\n, "
                % (
                    self.CurrentIteration,
                    duration,
                    gapX,
                    gapThetavar,
                    gapY,
                    gapB,
                    gapBPrime,
                    gapBDoublePrime,
                    self.CurrentImplementableSolution.TotalCost,
                    lpenalty,
                    qpenalty,
                    self.rho_PenaltyParameter,
                    primconv,
                    dualconv,
                    ratechangeimplem,
                    ratequad_lin,
                    rateprimaldual,
                    ratedualprimal,
                    self.ComputeConvergenceX(),
                    self.ComputeConvergenceThetavar()
                )
            )
            self.WriteInTraceFile(trace_message)

        return result

    def InitTrace(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- InitTrace")
        if Constants.PrintSDDPTrace:
            self.TraceFile = open(self.TraceFileName, "w")
            self.TraceFile.write("Start the Progressive Hedging algorithm \n")
            self.TraceFile.close()

    def SolveScenariosIndependently(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- SolveScenariosIndependently")

        #For each scenario
        for m in range(self.NrMIPBatch):

            #Update the coeffient in the objective function
            self.UpdateLagrangianCoeff(m)
            mip = self.MIPSolvers[m]
            mip.ModifyMipForScenarioTree(self.SplitedScenarioTree[m])

            #Solve the model.
            #self.MIPSolvers[w].Cplex.write("moel.lp")
            self.CurrentSolution[m] = mip.Solve(True)

            #compute the cost for the penalty update strategy
            self.CurrentSolution[m].ComputeCost()

    def UpdateLagrangianCoeff(self, batch):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- UpdateLagrangianCoeff")

        mipsolver = self.MIPSolvers[batch]

        # Initialize or retrieve storage for quadratic expressions
        if not hasattr(mipsolver, 'quadratic_terms'):
            mipsolver.quadratic_terms = {}

        # Collect all changes before updating the model
        changes = []

        # Function to handle linear and quadratic term updates
        def update_variable(variable, new_coeff, scenario_index, variable_type):
            variable.setAttr(GRB.Attr.Obj, new_coeff)
            if self.CurrentIteration > 0:
                var_name = variable.VarName
                if var_name in mipsolver.quadratic_terms:
                    old_quad_expr = mipsolver.quadratic_terms[var_name]
                    mipsolver.CRPBIM.setObjective(mipsolver.CRPBIM.getObjective() - old_quad_expr)
                quad_expr = Constants.PHCoeeff_QuadraticPart * self.rho_PenaltyParameter * variable * variable
                mipsolver.quadratic_terms[var_name] = quad_expr
                changes.append(quad_expr)

        # Update Apheresis Assignment Variables
        for scenario_index, scenario in enumerate(self.Indexscenarioinbatch[batch]):
            for i in self.Instance.ACFPPointSet:
                x_var_index = mipsolver.GetIndexACFEstablishmentVariable(i, scenario_index)
                variable = mipsolver.ACF_Establishment_Var[x_var_index]
                new_coeff = mipsolver.GetacfestablishmentCoeff(i) + self.LagrangianACFEstablishment[scenario][i]
                update_variable(variable, new_coeff, scenario_index, 'ACF_Establishment_Var')

        # Update VehicleAssignment Variables
        for scenario_index, scenario in enumerate(self.Indexscenarioinbatch[batch]):
            for m in self.Instance.RescueVehicleSet:
                for i in self.Instance.ACFPPointSet:
                    theta_var_index = mipsolver.GetIndexVehicleAssignmentVariable(m, i, scenario_index)
                    variable = mipsolver.Vehicle_Assignment_Var[theta_var_index]
                    new_coeff = mipsolver.GetvehicleassignmentCoeff(m, i) + self.LagrangianVehicleAssignment[scenario][m][i]
                    update_variable(variable, new_coeff, scenario_index, 'Vehicle_Assignment_Var')

        # Update ApheresisAssignment Variables
        for scenario_index, scenario in enumerate(self.Indexscenarioinbatch[batch]):
            for t in self.Instance.TimeBucketSet:
                for i in self.Instance.ACFPPointSet:
                    y_var_index = mipsolver.GetIndexApheresisAssignmentVariable(t, i, scenario_index)
                    variable = mipsolver.ApheresisAssignment_Var[y_var_index]
                    new_coeff = mipsolver.GetApheresisAssignmentCoeff(t, i, scenario_index) + self.LagrangianApheresisAssignment[scenario][t][i]
                    update_variable(variable, new_coeff, scenario_index, 'ApheresisAssignment_Var')

        # Update TransshipmentHI Variables
        for scenario_index, scenario in enumerate(self.Indexscenarioinbatch[batch]):
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            for i in self.Instance.ACFPPointSet:
                                b_var_index = mipsolver.GetIndexTransshipmentHIVariable(t, c, r, h, i, scenario_index)
                                variable = mipsolver.TransshipmentHI_Var[b_var_index]
                                new_coeff = mipsolver.GetTransshipmentHICoeff(t, h, i, scenario_index) + self.LagrangianTransshipmentHI[scenario][t][c][r][h][i]
                                update_variable(variable, new_coeff, scenario_index, 'TransshipmentHI_Var')

        # Update TransshipmentII Variables
        for scenario_index, scenario in enumerate(self.Indexscenarioinbatch[batch]):
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for i in self.Instance.ACFPPointSet:
                            for iprime in self.Instance.ACFPPointSet:
                                b_prime_var_index = mipsolver.GetIndexTransshipmentIIVariable(t, c, r, i, iprime, scenario_index)
                                variable = mipsolver.TransshipmentII_Var[b_prime_var_index]
                                new_coeff = mipsolver.GetTransshipmentIICoeff(t, i, iprime, scenario_index) + self.LagrangianTransshipmentII[scenario][t][c][r][i][iprime]
                                update_variable(variable, new_coeff, scenario_index, 'TransshipmentII_Var')

        # Update TransshipmentHH Variables
        for scenario_index, scenario in enumerate(self.Indexscenarioinbatch[batch]):
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            for hprime in self.Instance.HospitalSet:
                                b_double_prime_var_index = mipsolver.GetIndexTransshipmentHHVariable(t, c, r, h, hprime, scenario_index)
                                variable = mipsolver.TransshipmentHH_Var[b_double_prime_var_index]
                                new_coeff = mipsolver.GetTransshipmentHHCoeff(t, h, hprime, scenario_index) + self.LagrangianTransshipmentHH[scenario][t][c][r][h][hprime]
                                update_variable(variable, new_coeff, scenario_index, 'TransshipmentHH_Var')

        # Apply all changes at once
        mipsolver.CRPBIM.update()

        # Set all variables to continuous for a QP problem if necessary
        if self.SolveWithfixedACFEstablishment and self.SolveWithfixedVehicleAssignment:
            for var in mipsolver.CRPBIM.getVars():
                var.setAttr(GRB.Attr.VType, GRB.CONTINUOUS)
            if Constants.Debug: print("All variables set to continuous for a QP problem.")

        if Constants.Debug: print("Objective and problem type updated.")

    def UpdateLagragianMultipliers(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- UpdateLagragianMultipliers")

        for w in self.ScenarioNrSet:
            mm = self.BatchofScenario[w]
            nw = self.NewIndexOfScenario[w] 

            ############################# ACF Establishment
            for i in self.Instance.ACFPPointSet:
                self.lambda_LinearLagACFEstablishment[w][i], self.LagrangianACFEstablishment[w][i] = \
                    self.ComputeLagrangian(self.lambda_LinearLagACFEstablishment[w][i],
                                            self.CurrentSolution[mm].ACFEstablishment_x_wi[nw][i],
                                            self.CurrentImplementableSolution.ACFEstablishment_x_wi[w][i])
            
            ############################# Vehicle Assignment
            for m in self.Instance.RescueVehicleSet:
                for i in self.Instance.ACFPPointSet:
                    self.lambda_LinearLagVehicleAssignment[w][m][i], self.LagrangianVehicleAssignment[w][m][i] = \
                        self.ComputeLagrangian(self.lambda_LinearLagVehicleAssignment[w][m][i],
                                               self.CurrentSolution[mm].VehicleAssignment_thetavar_wmi[nw][m][i],
                                               self.CurrentImplementableSolution.VehicleAssignment_thetavar_wmi[w][m][i])

            ############################# Apheresis Assignment
            for t in self.Instance.TimeBucketSet:
                for i in self.Instance.ACFPPointSet:
                    self.lambda_LinearLagApheresisAssignment[w][t][i], self.LagrangianApheresisAssignment[w][t][i] = \
                        self.ComputeLagrangian(self.lambda_LinearLagApheresisAssignment[w][t][i],
                                            self.CurrentSolution[mm].ApheresisAssignment_y_wti[nw][t][i],
                                            self.CurrentImplementableSolution.ApheresisAssignment_y_wti[w][t][i])
            
            ############################# TransshipmentHI
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            for i in self.Instance.ACFPPointSet:
                                self.lambda_LinearLagTransshipmentHI[w][t][c][r][h][i], self.LagrangianTransshipmentHI[w][t][c][r][h][i] = \
                                    self.ComputeLagrangian(self.lambda_LinearLagTransshipmentHI[w][t][c][r][h][i],
                                                        self.CurrentSolution[mm].TransshipmentHI_b_wtcrhi[nw][t][c][r][h][i],
                                                        self.CurrentImplementableSolution.TransshipmentHI_b_wtcrhi[w][t][c][r][h][i])
            
            ############################# TransshipmentII
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for i in self.Instance.ACFPPointSet:
                            for iprime in self.Instance.ACFPPointSet:
                                self.lambda_LinearLagTransshipmentII[w][t][c][r][i][iprime], self.LagrangianTransshipmentII[w][t][c][r][i][iprime] = \
                                    self.ComputeLagrangian(self.lambda_LinearLagTransshipmentII[w][t][c][r][i][iprime],
                                                        self.CurrentSolution[mm].TransshipmentII_bPrime_wtcrii[nw][t][c][r][i][iprime],
                                                        self.CurrentImplementableSolution.TransshipmentII_bPrime_wtcrii[w][t][c][r][i][iprime])
            
            ############################# TransshipmentHH
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            for hprime in self.Instance.HospitalSet:
                                self.lambda_LinearLagTransshipmentHH[w][t][c][r][h][hprime], self.LagrangianTransshipmentHH[w][t][c][r][h][hprime] = \
                                    self.ComputeLagrangian(self.lambda_LinearLagTransshipmentHH[w][t][c][r][h][hprime],
                                                        self.CurrentSolution[mm].TransshipmentHH_bDoublePrime_wtcrhh[nw][t][c][r][h][hprime],
                                                        self.CurrentImplementableSolution.TransshipmentHH_bDoublePrime_wtcrhh[w][t][c][r][h][hprime])
                  
    def ComputeLagrangian(self, prevlag, independentvalue, implementablevalue):
        #if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- ComputeLagrangian")
        lambda_LinearLag = prevlag + (self.rho_PenaltyParameter * (independentvalue - implementablevalue))

        lagrangian = lambda_LinearLag - (self.rho_PenaltyParameter * implementablevalue)

        return lambda_LinearLag, lagrangian
    
    def GetScenariosAssociatedWithNode(self, node):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- GetScenariosAssociatedWithNode")

        scenarios = node.Scenarios
        if Constants.Debug: print("scenarios: ", scenarios)
        result = []
        for s in scenarios:
            result.append(self.ScenarioSet.index(s))

        return result
    
    def CreateImplementableSolution(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- CreateImplementableSolution")

        ###########
        solacfEstablishment = [[-1 for i in self.Instance.ACFPPointSet]
                                for w in self.ScenarioNrSet]
        
        solvehicleAssignment = [[[-1 for i in self.Instance.ACFPPointSet]
                                    for m in self.Instance.RescueVehicleSet]
                                    for w in self.ScenarioNrSet]
        
        ###########
        solapheresisassignment = [[[-1 for i in self.Instance.ACFPPointSet]
                                        for t in self.Instance.TimeBucketSet]
                                        for w in self.ScenarioNrSet]
        
        soltransshipmentHI = [[[[[[-1   for i in self.Instance.ACFPPointSet]
                                        for h in self.Instance.HospitalSet]
                                        for r in self.Instance.PlateletAgeSet]
                                        for c in self.Instance.BloodGPSet]
                                        for t in self.Instance.TimeBucketSet]
                                        for w in self.ScenarioNrSet]
        
        soltransshipmentII = [[[[[[-1   for iprime in self.Instance.ACFPPointSet]
                                        for i in self.Instance.ACFPPointSet]
                                        for r in self.Instance.PlateletAgeSet]
                                        for c in self.Instance.BloodGPSet]
                                        for t in self.Instance.TimeBucketSet]
                                        for w in self.ScenarioNrSet]
        
        soltransshipmentHH = [[[[[[-1   for hprime in self.Instance.HospitalSet]
                                        for h in self.Instance.HospitalSet]
                                        for r in self.Instance.PlateletAgeSet]
                                        for c in self.Instance.BloodGPSet]
                                        for t in self.Instance.TimeBucketSet]
                                        for w in self.ScenarioNrSet]

        ###########
        solpatientTransfer = [[[[[[[-1  for m in self.Instance.RescueVehicleSet]
                                        for u in self.Instance.FacilitySet]
                                        for l in self.Instance.DemandSet]
                                        for c in self.Instance.BloodGPSet]
                                        for j in self.Instance.InjuryLevelSet]
                                        for t in self.Instance.TimeBucketSet]
                                        for w in self.ScenarioNrSet]
        
        solunsatisfiedPatient = [[[[[-1  for l in self.Instance.DemandSet]
                                        for c in self.Instance.BloodGPSet]
                                        for j in self.Instance.InjuryLevelSet]
                                        for t in self.Instance.TimeBucketSet]
                                        for w in self.ScenarioNrSet]
        
        solplateletInventory = [[[[[-1  for u in self.Instance.FacilitySet]
                                        for r in self.Instance.PlateletAgeSet]
                                        for c in self.Instance.BloodGPSet]
                                        for t in self.Instance.TimeBucketSet]
                                        for w in self.ScenarioNrSet]
        
        soloutdatedPlatelet = [[[-1  for u in self.Instance.FacilitySet]
                                    for t in self.Instance.TimeBucketSet]
                                    for w in self.ScenarioNrSet]

        solservedPatient = [[[[[[[-1  for u in self.Instance.FacilitySet]
                                        for r in self.Instance.PlateletAgeSet]
                                        for c in self.Instance.BloodGPSet]
                                        for cprime in self.Instance.BloodGPSet]
                                        for j in self.Instance.InjuryLevelSet]
                                        for t in self.Instance.TimeBucketSet]
                                        for w in self.ScenarioNrSet]
        
        solpatientPostponement = [[[[[-1  for u in self.Instance.FacilitySet]
                                        for c in self.Instance.BloodGPSet]
                                        for j in self.Instance.InjuryLevelSet]
                                        for t in self.Instance.TimeBucketSet]
                                        for w in self.ScenarioNrSet]
        
        solplateletApheresisExtraction = [[[[-1  for u in self.Instance.FacilitySet]
                                                for c in self.Instance.BloodGPSet]
                                                for t in self.Instance.TimeBucketSet]
                                                for w in self.ScenarioNrSet]
        
        solplateletWholeExtraction = [[[[-1  for h in self.Instance.HospitalSet]
                                            for c in self.Instance.BloodGPSet]
                                            for t in self.Instance.TimeBucketSet]
                                            for w in self.ScenarioNrSet]
                                
        #For each node on the tree
        for n in self.ScenarioTree.Nodes:
            if Constants.Debug: print(" IN NODE = ", n)
            if Constants.Debug: print(f"n:{n}.Time: ", n.Time)

            if n.Time >= 0:
                scenarios = self.GetScenariosAssociatedWithNode(n)
                if Constants.Debug: print("scenarios: ", scenarios)
                time = n.Time
                sumprob = sum(self.ScenarioSet[w].Probability for w in scenarios)
                if Constants.Debug: print("sumprob: ", sumprob)
                
                # Average the quantities, and setups for this nodes.
                if time < self.Instance.NrTimeBucket:
                    
                    # First-Stage Variables
                    ####################################### ACF Establishment
                    acfestablishment = [round(sum(self.ScenarioSet[w].Probability * 
                                        self.CurrentSolution[self.BatchofScenario[w]].ACFEstablishment_x_wi[self.NewIndexOfScenario[w]][i] 
                                        for w in range(len(self.ScenarioSet)))\
                                        / 1 ,4)  #Here, exceptionally we devide the final value over 1 because it is the first-stage variable and it should be the same for all scenarios
                                        for i in self.Instance.ACFPPointSet]
                    if Constants.Debug: print("\nCurrent Value of ACFEstablishment at node:\n")
                    for w in range(len(self.ScenarioSet)):
                        if Constants.Debug: print(self.CurrentSolution[self.BatchofScenario[w]].ACFEstablishment_x_wi[self.NewIndexOfScenario[w]][:][:])
                    if Constants.Debug: print(f"Implementable Value of Fixed Trans Values at node: \n", acfestablishment)
                    for w in scenarios:
                        for i in self.Instance.ACFPPointSet:
                            solacfEstablishment[w][i] = acfestablishment[i]                    
                    ####################################### Vehicle Assignment
                    vehicleassignment = [[round(sum(self.ScenarioSet[w].Probability * 
                                        self.CurrentSolution[self.BatchofScenario[w]].VehicleAssignment_thetavar_wmi[self.NewIndexOfScenario[w]][m][i] 
                                        for w in range(len(self.ScenarioSet)))\
                                        / 1 ,4)  #Here, exceptionally we devide the final value over 1 because it is the first-stage variable and it should be the same for all scenarios
                                        for i in self.Instance.ACFPPointSet]
                                        for m in self.Instance.RescueVehicleSet]
                    if Constants.Debug: print("\nCurrent Value of VehicleAssignment at node:\n")
                    for w in range(len(self.ScenarioSet)):
                        if Constants.Debug: print(self.CurrentSolution[self.BatchofScenario[w]].VehicleAssignment_thetavar_wmi[self.NewIndexOfScenario[w]][:][:])
                    if Constants.Debug: print(f"Implementable Value of VehicleAssignment at node: \n", vehicleassignment)

                    for w in scenarios:
                        for m in self.Instance.RescueVehicleSet:
                            for i in self.Instance.ACFPPointSet:
                                solvehicleAssignment[w][m][i] = vehicleassignment[m][i] 

                    #Recourse Variables
                    ####################################### Apheresis Assignment
                    apheresisassignment = [round(sum(self.ScenarioSet[w].Probability * 
                                            self.CurrentSolution[self.BatchofScenario[w]].ApheresisAssignment_y_wti[self.NewIndexOfScenario[w]][time][i] for w in scenarios) \
                                            / sumprob, 4)
                                            for i in self.Instance.ACFPPointSet]
                    # if Constants.Debug: print("\nCurrent Value of Apheresis Assignment at node:\n")
                    # for w in range(len(self.ScenarioSet)):
                    #     if Constants.Debug: print(self.CurrentSolution[self.BatchofScenario[w]].ApheresisAssignment_y_wti[self.NewIndexOfScenario[w]][time])
                    # if Constants.Debug: print(f"Implementable Value of Apheresis Assignment at node: \n", apheresisassignment)
                    for w in scenarios:
                        for i in self.Instance.ACFPPointSet:
                            solapheresisassignment[w][time][i] = apheresisassignment[i]
                    
                    ####################################### Transshipment HI
                    transshipmentHI = [[[[round(sum(self.ScenarioSet[w].Probability * 
                                        self.CurrentSolution[self.BatchofScenario[w]].TransshipmentHI_b_wtcrhi[self.NewIndexOfScenario[w]][time][c][r][h][i] for w in scenarios) \
                                        / sumprob, 4)
                                        for i in self.Instance.ACFPPointSet]
                                        for h in self.Instance.HospitalSet]
                                        for r in self.Instance.PlateletAgeSet]
                                        for c in self.Instance.BloodGPSet]
                    # if Constants.Debug: print("\nCurrent Value of TransshipmentHI at node:\n")
                    # for w in range(len(self.ScenarioSet)):
                    #     if Constants.Debug: print(self.CurrentSolution[self.BatchofScenario[w]].TransshipmentHI_b_wtcrhi[self.NewIndexOfScenario[w]][time])
                    # if Constants.Debug: print(f"Implementable Value of transshipmentHI at node: \n", transshipmentHI)
                    for w in scenarios:
                        for c in self.Instance.BloodGPSet:
                            for r in self.Instance.PlateletAgeSet:
                                for h in self.Instance.HospitalSet:
                                    for i in self.Instance.ACFPPointSet:
                                        soltransshipmentHI[w][time][c][r][h][i] = transshipmentHI[c][r][h][i]
                    
                    ####################################### Transshipment II
                    transshipmentII = [[[[round(sum(self.ScenarioSet[w].Probability * 
                                        self.CurrentSolution[self.BatchofScenario[w]].TransshipmentII_bPrime_wtcrii[self.NewIndexOfScenario[w]][time][c][r][i][iprime] for w in scenarios) \
                                        / sumprob, 4)
                                        for iprime in self.Instance.ACFPPointSet]
                                        for i in self.Instance.ACFPPointSet]
                                        for r in self.Instance.PlateletAgeSet]
                                        for c in self.Instance.BloodGPSet]
                    # if Constants.Debug: print("\nCurrent Value of TransshipmentII at node:\n")
                    # for w in range(len(self.ScenarioSet)):
                    #     if Constants.Debug: print(self.CurrentSolution[self.BatchofScenario[w]].TransshipmentII_bPrime_wtcrii[self.NewIndexOfScenario[w]][time])
                    # if Constants.Debug: print(f"Implementable Value of transshipmentII at node: \n", transshipmentII)
                    for w in scenarios:
                        for c in self.Instance.BloodGPSet:
                            for r in self.Instance.PlateletAgeSet:
                                for i in self.Instance.ACFPPointSet:
                                    for iprime in self.Instance.ACFPPointSet:
                                        soltransshipmentII[w][time][c][r][i][iprime] = transshipmentII[c][r][i][iprime]

                    ####################################### Transshipment HH
                    transshipmentHH = [[[[round(sum(self.ScenarioSet[w].Probability * 
                                        self.CurrentSolution[self.BatchofScenario[w]].TransshipmentHH_bDoublePrime_wtcrhh[self.NewIndexOfScenario[w]][time][c][r][h][hprime] for w in scenarios) \
                                        / sumprob, 4)
                                        for hprime in self.Instance.HospitalSet]
                                        for h in self.Instance.HospitalSet]
                                        for r in self.Instance.PlateletAgeSet]
                                        for c in self.Instance.BloodGPSet]
                    # if Constants.Debug: print("\nCurrent Value of TransshipmentHH at node:\n")
                    # for w in range(len(self.ScenarioSet)):
                    #     if Constants.Debug: print(self.CurrentSolution[self.BatchofScenario[w]].TransshipmentHH_bDoublePrime_wtcrhh[self.NewIndexOfScenario[w]][time])
                    # if Constants.Debug: print(f"Implementable Value of transshipmentHH at node: \n", transshipmentHH)
                    for w in scenarios:
                        for c in self.Instance.BloodGPSet:
                            for r in self.Instance.PlateletAgeSet:
                                for h in self.Instance.HospitalSet:
                                    for hprime in self.Instance.HospitalSet:
                                        soltransshipmentHH[w][time][c][r][h][hprime] = transshipmentHH[c][r][h][hprime]

                    ####################################### Patient Transfer
                    patienttransfer = [[[[[round(sum(self.ScenarioSet[w].Probability * 
                                        self.CurrentSolution[self.BatchofScenario[w]].PatientTransfer_q_wtjclum[self.NewIndexOfScenario[w]][time][j][c][l][u][m] for w in scenarios) \
                                        / sumprob, 4)
                                        for m in self.Instance.RescueVehicleSet]
                                        for u in self.Instance.FacilitySet]
                                        for l in self.Instance.DemandSet]
                                        for c in self.Instance.BloodGPSet]
                                        for j in self.Instance.InjuryLevelSet]
                    # if Constants.Debug: print("\nCurrent Value of Patient Transfer at node:", )
                    # for w in range(len(self.ScenarioSet)):
                    #     if Constants.Debug: print(self.CurrentSolution[self.BatchofScenario[w]].PatientTransfer_q_wtjclum[self.NewIndexOfScenario[w]][time])                                        
                    # if Constants.Debug: print(f"Implementable Value of Patient Transfer at node: \n", patienttransfer)
                    for w in scenarios:
                        for j in self.Instance.InjuryLevelSet:
                            for c in self.Instance.BloodGPSet:
                                for l in self.Instance.DemandSet:
                                    for u in self.Instance.FacilitySet:
                                        for m in self.Instance.RescueVehicleSet:
                                            solpatientTransfer[w][time][j][c][l][u][m] = patienttransfer[j][c][l][u][m]
                    
                    ####################################### Unsatisfied Patient
                    unsatisfiedpatient = [[[round(sum(self.ScenarioSet[w].Probability * 
                                        self.CurrentSolution[self.BatchofScenario[w]].UnsatisfiedPatient_mu_wtjcl[self.NewIndexOfScenario[w]][time][j][c][l] for w in scenarios) \
                                        / sumprob, 4)
                                        for l in self.Instance.DemandSet]
                                        for c in self.Instance.BloodGPSet]
                                        for j in self.Instance.InjuryLevelSet]
                    # if Constants.Debug: print("\nCurrent Value of Unsatisfied Patient at node:", )
                    # for w in range(len(self.ScenarioSet)):
                    #     if Constants.Debug: print(self.CurrentSolution[self.BatchofScenario[w]].UnsatisfiedPatient_mu_wtjcl[self.NewIndexOfScenario[w]][time])                                        
                    # if Constants.Debug: print(f"Implementable Value of Patient Transfer at node: \n", unsatisfiedpatient)
                    for w in scenarios:
                        for j in self.Instance.InjuryLevelSet:
                            for c in self.Instance.BloodGPSet:
                                for l in self.Instance.DemandSet:
                                    solunsatisfiedPatient[w][time][j][c][l] = unsatisfiedpatient[j][c][l]
                    
                    ####################################### PLT Inventory
                    pltinventory = [[[round(sum(self.ScenarioSet[w].Probability * 
                                        self.CurrentSolution[self.BatchofScenario[w]].PlateletInventory_eta_wtcru[self.NewIndexOfScenario[w]][time][c][r][u] for w in scenarios) \
                                        / sumprob, 4)
                                        for u in self.Instance.FacilitySet]
                                        for r in self.Instance.PlateletAgeSet]
                                        for c in self.Instance.BloodGPSet]
                    # if Constants.Debug: print("\nCurrent Value of PLt Inventory at node:", )
                    # for w in range(len(self.ScenarioSet)):
                    #     if Constants.Debug: print(self.CurrentSolution[self.BatchofScenario[w]].PlateletInventory_eta_wtcru[self.NewIndexOfScenario[w]][time])                                        
                    # if Constants.Debug: print(f"Implementable Value of PLT Inventory at node: \n", pltinventory)
                    for w in scenarios:
                        for c in self.Instance.BloodGPSet:
                            for r in self.Instance.PlateletAgeSet:
                                for u in self.Instance.FacilitySet:
                                    solplateletInventory[w][time][c][r][u] = pltinventory[c][r][u]
                    
                    ####################################### Outdated PLT
                    outdatedplt = [round(sum(self.ScenarioSet[w].Probability * 
                                        self.CurrentSolution[self.BatchofScenario[w]].OutdatedPlatelet_sigmavar_wtu[self.NewIndexOfScenario[w]][time][u] for w in scenarios) \
                                        / sumprob, 4)
                                        for u in self.Instance.FacilitySet]
                    # if Constants.Debug: print("\nCurrent Value of Outdated PLT at node:", )
                    # for w in range(len(self.ScenarioSet)):
                    #     if Constants.Debug: print(self.CurrentSolution[self.BatchofScenario[w]].OutdatedPlatelet_sigmavar_wtu[self.NewIndexOfScenario[w]][time])                                        
                    # if Constants.Debug: print(f"Implementable Value of Outdated PLT at node: \n", outdatedplt)
                    for w in scenarios:
                        for u in self.Instance.FacilitySet:
                            soloutdatedPlatelet[w][time][u] = outdatedplt[u]
                    
                    ####################################### Served Patient
                    servedpatient = [[[[[round(sum(self.ScenarioSet[w].Probability * 
                                        self.CurrentSolution[self.BatchofScenario[w]].ServedPatient_upsilon_wtjcPcru[self.NewIndexOfScenario[w]][time][j][cprime][c][r][u] for w in scenarios) \
                                        / sumprob, 4)
                                        for u in self.Instance.FacilitySet]
                                        for r in self.Instance.PlateletAgeSet]
                                        for c in self.Instance.BloodGPSet]
                                        for cprime in self.Instance.BloodGPSet]
                                        for j in self.Instance.InjuryLevelSet]
                    # if Constants.Debug: print("\nCurrent Value of Served Patient at node:", )
                    # for w in range(len(self.ScenarioSet)):
                    #     if Constants.Debug: print(self.CurrentSolution[self.BatchofScenario[w]].ServedPatient_upsilon_wtjcPcru[self.NewIndexOfScenario[w]][time])                                        
                    # if Constants.Debug: print(f"Implementable Value of Served Patient at node: \n", servedpatient)
                    for w in scenarios:
                        for j in self.Instance.InjuryLevelSet:
                            for cprime in self.Instance.BloodGPSet:
                                for c in self.Instance.BloodGPSet:
                                    for r in self.Instance.PlateletAgeSet:
                                        for u in self.Instance.FacilitySet:
                                            solservedPatient[w][time][j][cprime][c][r][u] = servedpatient[j][cprime][c][r][u]
                    
                    ####################################### Patient Postponement
                    patientpostponement = [[[round(sum(self.ScenarioSet[w].Probability * 
                                        self.CurrentSolution[self.BatchofScenario[w]].PatientPostponement_zeta_wtjcu[self.NewIndexOfScenario[w]][time][j][c][u] for w in scenarios) \
                                        / sumprob, 4)
                                        for u in self.Instance.FacilitySet]
                                        for c in self.Instance.BloodGPSet]
                                        for j in self.Instance.InjuryLevelSet]
                    # if Constants.Debug: print("\nCurrent Value of Patient Postponement at node:", )
                    # for w in range(len(self.ScenarioSet)):
                    #     if Constants.Debug: print(self.CurrentSolution[self.BatchofScenario[w]].PatientPostponement_zeta_wtjcu[self.NewIndexOfScenario[w]][time])                                        
                    # if Constants.Debug: print(f"Implementable Value of Patient Postponement at node: \n", patientpostponement)
                    for w in scenarios:
                        for j in self.Instance.InjuryLevelSet:
                            for c in self.Instance.BloodGPSet:
                                for u in self.Instance.FacilitySet:
                                    solpatientPostponement[w][time][j][c][u] = patientpostponement[j][c][u]

                    ####################################### Apheresis Extraction
                    apheresisextraction = [[round(sum(self.ScenarioSet[w].Probability * 
                                        self.CurrentSolution[self.BatchofScenario[w]].PlateletApheresisExtraction_lambda_wtcu[self.NewIndexOfScenario[w]][time][c][u] for w in scenarios) \
                                        / sumprob, 4)
                                        for u in self.Instance.FacilitySet]
                                        for c in self.Instance.BloodGPSet]
                    # if Constants.Debug: print("\nCurrent Value of Apheresis Extraction at node:", )
                    # for w in range(len(self.ScenarioSet)):
                    #     if Constants.Debug: print(self.CurrentSolution[self.BatchofScenario[w]].PlateletApheresisExtraction_lambda_wtcu[self.NewIndexOfScenario[w]][time])                                        
                    # if Constants.Debug: print(f"Implementable Value of Apheresis Extraction at node: \n", apheresisextraction)
                    for w in scenarios:
                        for c in self.Instance.BloodGPSet:
                            for u in self.Instance.FacilitySet:
                                solplateletApheresisExtraction[w][time][c][u] = apheresisextraction[c][u]

                    ####################################### Whole Extraction
                    wholeextraction = [[round(sum(self.ScenarioSet[w].Probability * 
                                        self.CurrentSolution[self.BatchofScenario[w]].PlateletWholeExtraction_Rhovar_wtch[self.NewIndexOfScenario[w]][time][c][h] for w in scenarios) \
                                        / sumprob, 4)
                                        for h in self.Instance.HospitalSet]
                                        for c in self.Instance.BloodGPSet]
                    # if Constants.Debug: print("\nCurrent Value of Whole Extraction at node:", )
                    # for w in range(len(self.ScenarioSet)):
                    #     if Constants.Debug: print(self.CurrentSolution[self.BatchofScenario[w]].PlateletWholeExtraction_Rhovar_wtch[self.NewIndexOfScenario[w]][time])                                        
                    # if Constants.Debug: print(f"Implementable Value of Whole Extraction at node: \n", wholeextraction)
                    for w in scenarios:
                        for c in self.Instance.BloodGPSet:
                            for h in self.Instance.HospitalSet:
                                solplateletWholeExtraction[w][time][c][h] = wholeextraction[c][h]

        solution = Solution(instance=self.Instance, 
                            solACFEstablishment_x_wi = solacfEstablishment, 
                            solVehicleAssignment_thetavar_wmi = solvehicleAssignment, 
                            solApheresisAssignment_y_wti = solapheresisassignment, 
                            solTransshipmentHI_b_wtcrhi = soltransshipmentHI, 
                            solTransshipmentII_bPrime_wtcrii = soltransshipmentII, 
                            solTransshipmentHH_bDoublePrime_wtcrhh = soltransshipmentHH, 
                            solPatientTransfer_q_wtjclum = solpatientTransfer, 
                            solUnsatisfiedPatient_mu_wtjcl = solunsatisfiedPatient, 
                            solPlateletInventory_eta_wtcru = solplateletInventory, 
                            solOutdatedPlatelet_sigmavar_wtu = soloutdatedPlatelet, 
                            solServedPatient_upsilon_wtjcPcru = solservedPatient, 
                            solPatientPostponement_zeta_wtjcu = solpatientPostponement, 
                            solPlateletApheresisExtraction_lambda_wtcu = solplateletApheresisExtraction, 
                            solPlateletWholeExtraction_Rhovar_wtch = solplateletWholeExtraction, 
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
                            scenarioset = self.ScenarioSet, 
                            scenriotree = self.ScenarioTree, 
                            partialsolution = False)

        return solution

    def ComputeConvergenceX(self):
        #if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- ComputeConvergenceX")
        difference = 0
        for w in self.ScenarioNrSet:
            nw = self.NewIndexOfScenario[w]
            mm = self.BatchofScenario[w]
            for i in self.Instance.ACFPPointSet:    
                difference += self.ScenarioSet[w].Probability \
                                * math.pow(self.CurrentSolution[mm].ACFEstablishment_x_wi[nw][i] - 
                                            self.CurrentImplementableSolution.ACFEstablishment_x_wi[w][i], 2)

        #if Constants.Debug: print("difference_x: ", difference)
        convergence = math.sqrt(difference)
        #if Constants.Debug: print("convergence: ", convergence)
        return convergence
    
    def ComputeConvergenceThetavar(self):
        #if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- ComputeConvergenceThetavar")
        difference = 0
        for w in self.ScenarioNrSet:
            nw = self.NewIndexOfScenario[w]
            mm = self.BatchofScenario[w]
            for m in self.Instance.RescueVehicleSet:
                for i in self.Instance.ACFPPointSet:
                    difference += self.ScenarioSet[w].Probability \
                                  * math.pow(self.CurrentSolution[mm].VehicleAssignment_thetavar_wmi[nw][m][i] - 
                                             self.CurrentImplementableSolution.VehicleAssignment_thetavar_wmi[w][m][i], 2)
        #if Constants.Debug: print("difference_thetavar: ", difference)
        convergence = math.sqrt(difference)
        #if Constants.Debug: print("convergence: ", convergence)
        return convergence

    def ComputeConvergenceY(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- ComputeConvergenceY")
        
        difference = 0
        
        # Dictionary to hold the implementable solutions grouped by nodes
        node_based_apheresisassignment = {}
        for n in self.ScenarioTree.Nodes:
            if n.Time >= 0:  
                scenarios = self.GetScenariosAssociatedWithNode(n)
                time = n.Time
                sumprob = sum(self.ScenarioSet[w].Probability for w in scenarios)
                if time < self.Instance.NrTimeBucket:
                    # Compute average `y` for all scenarios under this node
                    for i in self.Instance.ACFPPointSet:
                        avg_y = round(sum(self.ScenarioSet[w].Probability * 
                                          self.CurrentSolution[self.BatchofScenario[w]].ApheresisAssignment_y_wti[self.NewIndexOfScenario[w]][time][i] for w in scenarios) / sumprob, 4)
                        for w in scenarios:
                            node_based_apheresisassignment[(w, time, i)] = avg_y
                            #if Constants.Debug: print(f"node_based_apheresisassignment[({w}, {time}, {i})]: ", node_based_apheresisassignment[(w, time, i)])
        
        # Compute differences based on the node-based average values
        for w in self.ScenarioNrSet:
            nw = self.NewIndexOfScenario[w]
            mm = self.BatchofScenario[w]
            for t in self.Instance.TimeBucketSet:
                for i in self.Instance.ACFPPointSet:
                    expected_y = round(node_based_apheresisassignment[(w, t, i)],2)
                    actual_y = round(self.CurrentSolution[mm].ApheresisAssignment_y_wti[nw][t][i],2)
                    difference += round(self.ScenarioSet[w].Probability * math.pow(actual_y - expected_y, 2),3)
                    #if Constants.Debug: print(f"Expected Y for node, time {t}, ACF {i}: {expected_y}")
                    #if Constants.Debug: print(f"Actual Y: {actual_y}")
                    #if Constants.Debug: print("Difference so far: ", difference)
        
        convergence = round(math.sqrt(difference),3)
        if Constants.Debug: print("Convergence for Apheresis Assignment: ", convergence)
        return convergence
    
    def ComputeConvergenceB(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- ComputeConvergenceB")
        
        difference = 0
        
        # Dictionary to hold the implementable solutions grouped by nodes
        node_based_transshipmentHI = {}
        for n in self.ScenarioTree.Nodes:
            if n.Time >= 0:  
                scenarios = self.GetScenariosAssociatedWithNode(n)
                time = n.Time
                sumprob = sum(self.ScenarioSet[w].Probability for w in scenarios)
                if time < self.Instance.NrTimeBucket:
                    # Compute average `B` for all scenarios under this node
                    for c in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for h in self.Instance.HospitalSet:
                                for i in self.Instance.ACFPPointSet:
                                    avg_b = round(sum(self.ScenarioSet[w].Probability * 
                                                    self.CurrentSolution[self.BatchofScenario[w]].TransshipmentHI_b_wtcrhi[self.NewIndexOfScenario[w]][time][c][r][h][i] for w in scenarios) 
                                                    / sumprob, 4)
                                    for w in scenarios:
                                        node_based_transshipmentHI[(w, time, c, r, h, i)] = avg_b
                                        #if Constants.Debug: print(f"node_based_transshipmentHI[({w}, {time}, {c}, {r}, {h}, {i})]: ", node_based_transshipmentHI[(w, time, c, r, h, i)])
        
        # Compute differences based on the node-based average values
        for w in self.ScenarioNrSet:
            nw = self.NewIndexOfScenario[w]
            mm = self.BatchofScenario[w]
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            for i in self.Instance.ACFPPointSet:
                                expected_b = round(node_based_transshipmentHI[(w, t, c, r, h, i)],2)
                                actual_b = round(self.CurrentSolution[mm].TransshipmentHI_b_wtcrhi[nw][t][c][r][h][i],2)
                                difference += round(self.ScenarioSet[w].Probability * math.pow(actual_b - expected_b, 2),3)
                                #if Constants.Debug: print(f"Expected b for node, time {t}, c:{c}, r:{r}, h:{h}, i:{i}: {expected_b}")
                                #if Constants.Debug: print(f"Actual b: {actual_b}")
                                #if Constants.Debug: print("Difference so far: ", difference)
        
        convergence = round(math.sqrt(difference),3)
        if Constants.Debug: print("Convergence for TransshipmentHI: ", convergence)
        return convergence
    
    def ComputeConvergenceBPrime(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- ComputeConvergenceB")
        
        difference = 0
        
        # Dictionary to hold the implementable solutions grouped by nodes
        node_based_transshipmentII = {}
        for n in self.ScenarioTree.Nodes:
            if n.Time >= 0:  
                scenarios = self.GetScenariosAssociatedWithNode(n)
                time = n.Time
                sumprob = sum(self.ScenarioSet[w].Probability for w in scenarios)
                if time < self.Instance.NrTimeBucket:
                    # Compute average `B` for all scenarios under this node
                    for c in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for i in self.Instance.ACFPPointSet:
                                for iprime in self.Instance.ACFPPointSet:
                                    avg_bPrime = round(sum(self.ScenarioSet[w].Probability * 
                                                    self.CurrentSolution[self.BatchofScenario[w]].TransshipmentII_bPrime_wtcrii[self.NewIndexOfScenario[w]][time][c][r][i][iprime] for w in scenarios) 
                                                    / sumprob, 4)
                                    for w in scenarios:
                                        node_based_transshipmentII[(w, time, c, r, i, iprime)] = avg_bPrime
                                        #if Constants.Debug: print(f"node_based_transshipmentII[({w}, {time}, {c}, {r}, {i}, {iprime})]: ", node_based_transshipmentII[(w, time, c, r, i, iprime)])
        
        # Compute differences based on the node-based average values
        for w in self.ScenarioNrSet:
            nw = self.NewIndexOfScenario[w]
            mm = self.BatchofScenario[w]
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for i in self.Instance.ACFPPointSet:
                            for iprime in self.Instance.ACFPPointSet:
                                expected_bPrime = round(node_based_transshipmentII[(w, t, c, r, i, iprime)],2)
                                actual_bPrime = round(self.CurrentSolution[mm].TransshipmentII_bPrime_wtcrii[nw][t][c][r][i][iprime],2)
                                difference += round(self.ScenarioSet[w].Probability * math.pow(actual_bPrime - expected_bPrime, 2),3)
                                #if Constants.Debug: print(f"Expected b' for node, time {t}, c:{c}, r:{r}, i:{i}, i':{iprime}: {expected_bPrime}")
                                #if Constants.Debug: print(f"Actual b: {actual_bPrime}")
                                #if Constants.Debug: print("Difference so far: ", difference)
        
        convergence = round(math.sqrt(difference),3)
        if Constants.Debug: print("Convergence for TransshipmentII: ", convergence)
        return convergence
        
    def ComputeConvergenceBDoublePrime(self):
        
        difference = 0
        
        # Dictionary to hold the implementable solutions grouped by nodes
        node_based_transshipmentHH = {}
        for n in self.ScenarioTree.Nodes:
            if n.Time >= 0:  
                scenarios = self.GetScenariosAssociatedWithNode(n)
                time = n.Time
                sumprob = sum(self.ScenarioSet[w].Probability for w in scenarios)
                if time < self.Instance.NrTimeBucket:
                    # Compute average `B` for all scenarios under this node
                    for c in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for h in self.Instance.HospitalSet:
                                for hprime in self.Instance.HospitalSet:
                                    avg_bDoublePrime = round(sum(self.ScenarioSet[w].Probability * 
                                                    self.CurrentSolution[self.BatchofScenario[w]].TransshipmentHH_bDoublePrime_wtcrhh[self.NewIndexOfScenario[w]][time][c][r][h][hprime] for w in scenarios) 
                                                    / sumprob, 4)
                                    for w in scenarios:
                                        node_based_transshipmentHH[(w, time, c, r, h, hprime)] = avg_bDoublePrime
                                        #if Constants.Debug: print(f"node_based_transshipmentHH[({w}, {time}, {c}, {r}, {h}, {hprime})]: ", node_based_transshipmentHH[(w, time, c, r, h, hprime)])
        
        # Compute differences based on the node-based average values
        for w in self.ScenarioNrSet:
            nw = self.NewIndexOfScenario[w]
            mm = self.BatchofScenario[w]
            for t in self.Instance.TimeBucketSet:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            for hprime in self.Instance.HospitalSet:
                                expected_bDoublePrime = round(node_based_transshipmentHH[(w, t, c, r, h, hprime)],2)
                                actual_bDoublePrime = round(self.CurrentSolution[mm].TransshipmentHH_bDoublePrime_wtcrhh[nw][t][c][r][h][hprime],2)
                                difference += round(self.ScenarioSet[w].Probability * math.pow(actual_bDoublePrime - expected_bDoublePrime, 2),3)
                                #if Constants.Debug: print(f"Expected b'' for node, time {t}, c:{c}, r:{r}, h:{h}, h':{hprime}: {expected_bDoublePrime}")
                                #if Constants.Debug: print(f"Actual b'': {actual_bDoublePrime}")
                                #if Constants.Debug: print("Difference so far: ", difference)
        
        convergence = round(math.sqrt(difference),3)
        if Constants.Debug: print("Convergence for TransshipmentHI: ", convergence)
        return convergence
 
    def GetLinearPenaltyForScenario(self, w):
        #if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- GetLinearPenaltyForScenario")

        nw = self.NewIndexOfScenario[w]
        mm = self.BatchofScenario[w]
        linterm = 0

        linterm = linterm + sum(self.LagrangianACFEstablishment[w][i] \
                                * (self.CurrentSolution[mm].ACFEstablishment_x_wi[nw][i])
                                for i in self.Instance.ACFPPointSet)
        linterm = linterm + sum(self.LagrangianVehicleAssignment[w][m][i] \
                                * (self.CurrentSolution[mm].VehicleAssignment_thetavar_wmi[nw][m][i])
                                for i in self.Instance.ACFPPointSet
                                for m in self.Instance.RescueVehicleSet)
                
        linterm = linterm + sum(self.LagrangianApheresisAssignment[w][t][i] \
                                * (self.CurrentSolution[mm].ApheresisAssignment_y_wti[nw][t][i])
                                for i in self.Instance.ACFPPointSet
                                for t in self.Instance.TimeBucketSet)
        linterm = linterm + sum(self.LagrangianTransshipmentHI[w][t][c][r][h][i] \
                                * (self.CurrentSolution[mm].TransshipmentHI_b_wtcrhi[nw][t][c][r][h][i])
                                for i in self.Instance.ACFPPointSet
                                for h in self.Instance.HospitalSet
                                for r in self.Instance.PlateletAgeSet
                                for c in self.Instance.BloodGPSet
                                for t in self.Instance.TimeBucketSet)
        linterm = linterm + sum(self.LagrangianTransshipmentII[w][t][c][r][i][iprime] \
                                * (self.CurrentSolution[mm].TransshipmentII_bPrime_wtcrii[nw][t][c][r][i][iprime])
                                for iprime in self.Instance.ACFPPointSet
                                for i in self.Instance.ACFPPointSet
                                for r in self.Instance.PlateletAgeSet
                                for c in self.Instance.BloodGPSet
                                for t in self.Instance.TimeBucketSet)
        linterm = linterm + sum(self.LagrangianTransshipmentHH[w][t][c][r][h][hprime] \
                                * (self.CurrentSolution[mm].TransshipmentHH_bDoublePrime_wtcrhh[nw][t][c][r][h][hprime])
                                for hprime in self.Instance.HospitalSet
                                for h in self.Instance.HospitalSet
                                for r in self.Instance.PlateletAgeSet
                                for c in self.Instance.BloodGPSet
                                for t in self.Instance.TimeBucketSet)

        return linterm
    
    def GetLinearPenalty(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- GetLinearPenalty")
        result = sum(self.ScenarioSet[w].Probability * (self.GetLinearPenaltyForScenario(w))
                     for w in self.ScenarioNrSet)

        return result

    def GetQuadraticPenaltyForScenario(self, w):
        #if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- GetQuadraticPenaltyForScenario")
        
        nw = self.NewIndexOfScenario[w]
        mm = self.BatchofScenario[w]
        quadterm = 0

        quadterm = quadterm + sum(Constants.PHCoeeff_QuadraticPart * self.rho_PenaltyParameter \
                                    * math.pow((self.CurrentSolution[mm].ACFEstablishment_x_wi[nw][i]), 2)
                                    for i in self.Instance.ACFPPointSet)
        quadterm = quadterm + sum(Constants.PHCoeeff_QuadraticPart * self.rho_PenaltyParameter \
                                    * math.pow((self.CurrentSolution[mm].VehicleAssignment_thetavar_wmi[nw][m][i]), 2)
                                    for i in self.Instance.ACFPPointSet
                                    for m in self.Instance.RescueVehicleSet)
        
        quadterm = quadterm + sum(Constants.PHCoeeff_QuadraticPart * self.rho_PenaltyParameter \
                                    * math.pow((self.CurrentSolution[mm].ApheresisAssignment_y_wti[nw][t][i]), 2)
                                    for i in self.Instance.ACFPPointSet
                                    for t in self.Instance.TimeBucketSet)
        quadterm = quadterm + sum(Constants.PHCoeeff_QuadraticPart * self.rho_PenaltyParameter \
                                    * math.pow((self.CurrentSolution[mm].TransshipmentHI_b_wtcrhi[nw][t][c][r][h][i]), 2)
                                    for i in self.Instance.ACFPPointSet
                                    for h in self.Instance.HospitalSet
                                    for r in self.Instance.PlateletAgeSet
                                    for c in self.Instance.BloodGPSet
                                    for t in self.Instance.TimeBucketSet)
        quadterm = quadterm + sum(Constants.PHCoeeff_QuadraticPart * self.rho_PenaltyParameter \
                                    * math.pow((self.CurrentSolution[mm].TransshipmentII_bPrime_wtcrii[nw][t][c][r][i][iprime]), 2)
                                    for iprime in self.Instance.ACFPPointSet
                                    for i in self.Instance.ACFPPointSet
                                    for r in self.Instance.PlateletAgeSet
                                    for c in self.Instance.BloodGPSet
                                    for t in self.Instance.TimeBucketSet)
        quadterm = quadterm + sum(Constants.PHCoeeff_QuadraticPart * self.rho_PenaltyParameter \
                                    * math.pow((self.CurrentSolution[mm].TransshipmentHH_bDoublePrime_wtcrhh[nw][t][c][r][h][hprime]), 2)
                                    for hprime in self.Instance.HospitalSet
                                    for h in self.Instance.HospitalSet
                                    for r in self.Instance.PlateletAgeSet
                                    for c in self.Instance.BloodGPSet
                                    for t in self.Instance.TimeBucketSet)

        return quadterm
    
    def GetQuadraticPenalty(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- GetQuadraticPenalty")

        result = sum(self.ScenarioSet[w].Probability * self.GetQuadraticPenaltyForScenario(w)
                     for w in self.ScenarioNrSet)

        return result

    def RateQuadLinear(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- GetQuadraticPenalty")

        result = self.GetQuadraticPenalty()/ (self.Getlambda_LinearLagrangianterm())

        return result

    def Getlambda_LinearLagrangianterm(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- Getlambda_LinearLagrangianterm")

        result = sum( self.ScenarioSet[w].Probability * \
                      (self.GetLinearPenaltyForScenario(w) + self.CurrentSolution[self.BatchofScenario[w]].TotalCost)
                        for w in self.ScenarioNrSet)
        return result

    def WriteInTraceFile(self, string):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- WriteInTraceFile")

        if Constants.PrintSDDPTrace:
            self.TraceFile = open(self.TraceFileName, "a")
            self.TraceFile.write(string)
            self.TraceFile.close()

    def GetPrimalConvergenceIndice(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- GetPrimalConvergenceIndice")

        result = 0

        result = result + sum(self.ScenarioSet[w].Probability \
                                * math.pow(self.CurrentImplementableSolution.ACFEstablishment_x_wi[w][i]
                                - self.PreviousImplementableSolution.ACFEstablishment_x_wi[w][i], 2)
                                for i in self.Instance.ACFPPointSet
                                for w in self.ScenarioNrSet)
        result = result + sum(self.ScenarioSet[w].Probability \
                                * math.pow(self.CurrentImplementableSolution.VehicleAssignment_thetavar_wmi[w][m][i]
                                - self.PreviousImplementableSolution.VehicleAssignment_thetavar_wmi[w][m][i], 2)
                                for i in self.Instance.ACFPPointSet
                                for m in self.Instance.RescueVehicleSet
                                for w in self.ScenarioNrSet)
        
        result = result + sum(self.ScenarioSet[w].Probability \
                                * math.pow(self.CurrentImplementableSolution.ApheresisAssignment_y_wti[w][t][i]
                                - self.PreviousImplementableSolution.ApheresisAssignment_y_wti[w][t][i], 2)
                                for i in self.Instance.ACFPPointSet
                                for t in self.Instance.TimeBucketSet
                                for w in self.ScenarioNrSet)
        result = result + sum(self.ScenarioSet[w].Probability \
                                * math.pow(self.CurrentImplementableSolution.TransshipmentHI_b_wtcrhi[w][t][c][r][h][i]
                                - self.PreviousImplementableSolution.TransshipmentHI_b_wtcrhi[w][t][c][r][h][i], 2)
                                for i in self.Instance.ACFPPointSet
                                for h in self.Instance.HospitalSet
                                for r in self.Instance.PlateletAgeSet
                                for c in self.Instance.BloodGPSet
                                for t in self.Instance.TimeBucketSet
                                for w in self.ScenarioNrSet)
        result = result + sum(self.ScenarioSet[w].Probability \
                                * math.pow(self.CurrentImplementableSolution.TransshipmentII_bPrime_wtcrii[w][t][c][r][i][iprime]
                                - self.PreviousImplementableSolution.TransshipmentII_bPrime_wtcrii[w][t][c][r][i][iprime], 2)
                                for iprime in self.Instance.ACFPPointSet
                                for i in self.Instance.ACFPPointSet
                                for r in self.Instance.PlateletAgeSet
                                for c in self.Instance.BloodGPSet
                                for t in self.Instance.TimeBucketSet
                                for w in self.ScenarioNrSet)
        result = result + sum(self.ScenarioSet[w].Probability \
                                * math.pow(self.CurrentImplementableSolution.TransshipmentHH_bDoublePrime_wtcrhh[w][t][c][r][h][hprime]
                                - self.PreviousImplementableSolution.TransshipmentHH_bDoublePrime_wtcrhh[w][t][c][r][h][hprime], 2)
                                for hprime in self.Instance.HospitalSet
                                for h in self.Instance.HospitalSet
                                for r in self.Instance.PlateletAgeSet
                                for c in self.Instance.BloodGPSet
                                for t in self.Instance.TimeBucketSet
                                for w in self.ScenarioNrSet)

        return result

    def GetDualConvergenceIndice(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- GetDualConvergenceIndice")
        result = 0

        result = result + sum(self.ScenarioSet[w].Probability \
                                * math.pow(self.CurrentSolution[self.BatchofScenario[w]].ACFEstablishment_x_wi[self.NewIndexOfScenario[w]][i]
                                - self.CurrentImplementableSolution.ACFEstablishment_x_wi[w][i], 2)
                                for i in self.Instance.ACFPPointSet
                                for w in self.ScenarioNrSet)
        result = result + sum(self.ScenarioSet[w].Probability \
                                * math.pow(self.CurrentSolution[self.BatchofScenario[w]].VehicleAssignment_thetavar_wmi[self.NewIndexOfScenario[w]][m][i]
                                - self.CurrentImplementableSolution.VehicleAssignment_thetavar_wmi[w][m][i], 2)
                                for i in self.Instance.ACFPPointSet
                                for m in self.Instance.RescueVehicleSet
                                for w in self.ScenarioNrSet)
        
        result = result + sum(self.ScenarioSet[w].Probability \
                                * math.pow(self.CurrentSolution[self.BatchofScenario[w]].ApheresisAssignment_y_wti[self.NewIndexOfScenario[w]][t][i]
                                - self.CurrentImplementableSolution.ApheresisAssignment_y_wti[w][t][i], 2)
                                for i in self.Instance.ACFPPointSet
                                for t in self.Instance.TimeBucketSet
                                for w in self.ScenarioNrSet)
        result = result + sum(self.ScenarioSet[w].Probability \
                                * math.pow(self.CurrentSolution[self.BatchofScenario[w]].TransshipmentHI_b_wtcrhi[self.NewIndexOfScenario[w]][t][c][r][h][i]
                                - self.CurrentImplementableSolution.TransshipmentHI_b_wtcrhi[w][t][c][r][h][i], 2)
                                for i in self.Instance.ACFPPointSet
                                for h in self.Instance.HospitalSet
                                for r in self.Instance.PlateletAgeSet
                                for c in self.Instance.BloodGPSet
                                for t in self.Instance.TimeBucketSet
                                for w in self.ScenarioNrSet)
        result = result + sum(self.ScenarioSet[w].Probability \
                                * math.pow(self.CurrentSolution[self.BatchofScenario[w]].TransshipmentII_bPrime_wtcrii[self.NewIndexOfScenario[w]][t][c][r][i][iprime]
                                - self.CurrentImplementableSolution.TransshipmentII_bPrime_wtcrii[w][t][c][r][i][iprime], 2)
                                for iprime in self.Instance.ACFPPointSet
                                for i in self.Instance.ACFPPointSet
                                for r in self.Instance.PlateletAgeSet
                                for c in self.Instance.BloodGPSet
                                for t in self.Instance.TimeBucketSet
                                for w in self.ScenarioNrSet)
        result = result + sum(self.ScenarioSet[w].Probability \
                                * math.pow(self.CurrentSolution[self.BatchofScenario[w]].TransshipmentHH_bDoublePrime_wtcrhh[self.NewIndexOfScenario[w]][t][c][r][h][hprime]
                                - self.CurrentImplementableSolution.TransshipmentHH_bDoublePrime_wtcrhh[w][t][c][r][h][hprime], 2)
                                for hprime in self.Instance.HospitalSet
                                for h in self.Instance.HospitalSet
                                for r in self.Instance.PlateletAgeSet
                                for c in self.Instance.BloodGPSet
                                for t in self.Instance.TimeBucketSet
                                for w in self.ScenarioNrSet)

        return result

    def GetDistance(self, solution):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- GetDistance")
        result = 0

        result = result + sum(self.ScenarioSet[w].Probability \
                            * math.pow(solution.ACFEstablishment_x_wi[w][i], 2)
                            for i in self.Instance.ACFPPointSet
                            for w in self.ScenarioNrSet)
        result = result + sum(self.ScenarioSet[w].Probability \
                            * math.pow(solution.VehicleAssignment_thetavar_wmi[w][m][i], 2)
                            for i in self.Instance.ACFPPointSet
                            for m in self.Instance.RescueVehicleSet
                            for w in self.ScenarioNrSet)
        
        result = result + sum(self.ScenarioSet[w].Probability \
                            * math.pow(solution.ApheresisAssignment_y_wti[w][t][i], 2)
                            for i in self.Instance.ACFPPointSet
                            for t in self.Instance.TimeBucketSet
                            for w in self.ScenarioNrSet)
        result = result + sum(self.ScenarioSet[w].Probability \
                            * math.pow(solution.TransshipmentHI_b_wtcrhi[w][t][c][r][h][i], 2)
                            for i in self.Instance.ACFPPointSet
                            for h in self.Instance.HospitalSet
                            for r in self.Instance.PlateletAgeSet
                            for c in self.Instance.BloodGPSet
                            for t in self.Instance.TimeBucketSet
                            for w in self.ScenarioNrSet)
        result = result + sum(self.ScenarioSet[w].Probability \
                            * math.pow(solution.TransshipmentII_bPrime_wtcrii[w][t][c][r][i][iprime], 2)
                            for iprime in self.Instance.ACFPPointSet
                            for i in self.Instance.ACFPPointSet
                            for r in self.Instance.PlateletAgeSet
                            for c in self.Instance.BloodGPSet
                            for t in self.Instance.TimeBucketSet
                            for w in self.ScenarioNrSet)
        result = result + sum(self.ScenarioSet[w].Probability \
                            * math.pow(solution.TransshipmentHH_bDoublePrime_wtcrhh[w][t][c][r][h][hprime], 2)
                            for hprime in self.Instance.HospitalSet
                            for h in self.Instance.HospitalSet
                            for r in self.Instance.PlateletAgeSet
                            for c in self.Instance.BloodGPSet
                            for t in self.Instance.TimeBucketSet
                            for w in self.ScenarioNrSet)

        return result
    
    def RateLargeChangeInImplementable(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- RateLargeChangeInImplementable")

        primalcon = self.GetPrimalConvergenceIndice()
        divider = max(self.GetDistance(self.CurrentImplementableSolution),
                      self.GetDistance(self.PreviousImplementableSolution))

        result =(primalcon / divider)
        return result
    
    def RatePrimalDual(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- RatePrimalDual")

        primalcon = self.GetPrimalConvergenceIndice()
        dualcon = self.GetDualConvergenceIndice()
        divider = max(1,dualcon)

        result =(primalcon-dualcon / divider)
        return result

    def RateDualPrimal(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- RateDualPrimal")

        primalcon = self.GetPrimalConvergenceIndice()
        dualcon = self.GetDualConvergenceIndice()
        divider = max(1, primalcon)

        result = (dualcon - primalcon / divider)
        return result

    def ReSetParameter(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- RateDualPrimal")

        self.StartTime = time.time()
        self.rho_PenaltyParameter = 0.0
        self.CurrentImplementableSolution = None

        self.PreviouBeta = 0.5

        ####################### ACFEstablishment
        self.LagrangianACFEstablishment = [[0 for i in self.Instance.ACFPPointSet]
                                            for w in self.ScenarioNrSet]

        self.lambda_LinearLagACFEstablishment = [[0 for i in self.Instance.ACFPPointSet]
                                                    for w in self.ScenarioNrSet]
        ####################### VehicleAssignment
        self.LagrangianVehicleAssignment = [[[0 for i in self.Instance.ACFPPointSet]
                                                for m in self.Instance.RescueVehicleSet]
                                                for w in self.ScenarioNrSet]

        self.lambda_LinearLagVehicleAssignment = [[[0 for i in self.Instance.ACFPPointSet]
                                                        for m in self.Instance.RescueVehicleSet]
                                                        for w in self.ScenarioNrSet]

        ####################### ApheresisAssignment
        self.LagrangianApheresisAssignment = [[[0 for i in self.Instance.ACFPPointSet]
                                                    for t in self.Instance.TimeBucketSet]
                                                    for w in self.ScenarioNrSet]

        self.lambda_LinearLagApheresisAssignment = [[[0 for i in self.Instance.ACFPPointSet]
                                                        for t in self.Instance.TimeBucketSet]
                                                        for w in self.ScenarioNrSet]
        ####################### TransshipmentHI
        self.LagrangianTransshipmentHI = [[[[[[0 for i in self.Instance.ACFPPointSet]
                                                for h in self.Instance.HospitalSet]
                                                for r in self.Instance.PlateletAgeSet]
                                                for c in self.Instance.BloodGPSet]
                                                for t in self.Instance.TimeBucketSet]
                                                for w in self.ScenarioNrSet]

        self.lambda_LinearLagTransshipmentHI = [[[[[[0 for i in self.Instance.ACFPPointSet]
                                                        for h in self.Instance.HospitalSet]
                                                        for r in self.Instance.PlateletAgeSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for t in self.Instance.TimeBucketSet]
                                                        for w in self.ScenarioNrSet]
        ####################### TransshipmentII
        self.LagrangianTransshipmentII = [[[[[[0 for iprime in self.Instance.ACFPPointSet]
                                                for i in self.Instance.ACFPPointSet]
                                                for r in self.Instance.PlateletAgeSet]
                                                for c in self.Instance.BloodGPSet]
                                                for t in self.Instance.TimeBucketSet]
                                                for w in self.ScenarioNrSet]

        self.lambda_LinearLagTransshipmentII = [[[[[[0 for iprime in self.Instance.ACFPPointSet]
                                                        for i in self.Instance.ACFPPointSet]
                                                        for r in self.Instance.PlateletAgeSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for t in self.Instance.TimeBucketSet]
                                                        for w in self.ScenarioNrSet]
        ####################### TransshipmentHH
        self.LagrangianTransshipmentHH = [[[[[[0 for hprime in self.Instance.HospitalSet]
                                                for h in self.Instance.HospitalSet]
                                                for r in self.Instance.PlateletAgeSet]
                                                for c in self.Instance.BloodGPSet]
                                                for t in self.Instance.TimeBucketSet]
                                                for w in self.ScenarioNrSet]

        self.lambda_LinearLagTransshipmentHH = [[[[[[0 for hprime in self.Instance.HospitalSet]
                                                        for h in self.Instance.HospitalSet]
                                                        for r in self.Instance.PlateletAgeSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for t in self.Instance.TimeBucketSet]
                                                        for w in self.ScenarioNrSet]

        self.CurrentIteration = 0

    def UpdateForDemand(self, demanduptotimet):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- UpdateForDemand")

        for w in self.ScenarioNrSet:
            for t in range(self.FixedUntil+1):
                for j in self.Instance.InjuryLevelSet:
                    for c in self.Instance.BloodGPSet:
                        for l in self.Instance.DemandSet:
                            self.ScenarioSet[w].Demands[t][j][c][l] = demanduptotimet[t][j][c][l]
        self.SplitScenrioTree()
    
    def UpdateForHospitalCap(self, hospitalcapuptotimet):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- UpdateForHospitalCap")

        for w in self.ScenarioNrSet:
            for t in range(self.FixedUntil+1):
                for h in self.Instance.HospitalSet:
                    self.ScenarioSet[w].HospitalCaps[t][h] = hospitalcapuptotimet[t][h]
        #    self.MIPSolvers[w].ModifyMipForScenario(demanduptotimet, self.FixedUntil+1)
        self.SplitScenrioTree()
    
    def UpdateForWholeDonor(self, wholedonoruptotimet):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- UpdateForWholeDonor")

        for w in self.ScenarioNrSet:
            for t in range(self.FixedUntil+1):
                for c in self.Instance.BloodGPSet:
                    for h in self.Instance.HospitalSet:
                        self.ScenarioSet[w].WholeDonors[t][c][h] = wholedonoruptotimet[t][c][h]

        self.SplitScenrioTree()
    
    def UpdateForApheresisDonor(self, apheresisdonoruptotimet):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- UpdateForApheresisDonor")

        for w in self.ScenarioNrSet:
            for t in range(self.FixedUntil+1):
                for c in self.Instance.BloodGPSet:
                    for u in self.Instance.FacilitySet:
                        self.ScenarioSet[w].ApheresisDonors[t][c][u] = apheresisdonoruptotimet[t][c][u]

        self.SplitScenrioTree()

    def UpdateForApheresisAssignment(self, givenapheresisassignments):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- UpdateForApheresisAssignment")

        for w in self.ScenarioNrSet:
            self.MIPSolvers[0].GivenApheresisAssignment = givenapheresisassignments
            self.MIPSolvers[0].ModifyMipForFixApheresisAssignment(givenapheresisassignments, self.FixedUntil+1)
    
    def UpdateForTransshipmentHI(self, giventransshipmentHIs):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- UpdateForTransshipmentHI")

        for w in self.ScenarioNrSet:
            self.MIPSolvers[0].GivenTransshipmentHI = giventransshipmentHIs
            self.MIPSolvers[0].ModifyMipForFixTransshipmentHI(giventransshipmentHIs, self.FixedUntil+1)
    
    def UpdateForTransshipmentII(self, giventransshipmentIIs):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- UpdateForVarTrans")

        for w in self.ScenarioNrSet:
            self.MIPSolvers[0].GivenTransshipmentII = giventransshipmentIIs
            self.MIPSolvers[0].ModifyMipForFixTransshipmentII(giventransshipmentIIs, self.FixedUntil+1)
    
    def UpdateForTransshipmentHH(self, giventransshipmentHHs):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- UpdateForVarTrans")

        for w in self.ScenarioNrSet:
            self.MIPSolvers[0].GivenTransshipmentHH = giventransshipmentHHs
            self.MIPSolvers[0].ModifyMipForFixTransshipmentHH(giventransshipmentHHs, self.FixedUntil+1)

    def PrintCurrentIteration(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- PrintCurrentIteration")

        # if Constants.Debug: print("----------------Independent solutions--------------")
        # for w in self.ScenarioNrSet:
        #     #self.CurrentSolution[w].Print()
        #     if Constants.Debug: print("Scenario %r: %r"%(w, self.CurrentSolution[self.BatchofScenario[w]].VariableTransportation_x_wtsd[self.NewIndexOfScenario[w]]))

        # if Constants.Debug: print("Implementable: %r" % ( self.CurrentImplementableSolution.VariableTransportation_x_wtsd))
        if Constants.Debug: print("-----------IMPLEMENTABLE: -------------------------")
        self.CurrentImplementableSolution.Print()
        # if Constants.Debug:
            # print("---------------------------------------------------")
            # print("----------------------Multipliers------------------")
            # print("VarTrans:%r"%self.LagrangianVariableTrans)
            # print("Linear VarTrans:%r" % self.lambda_LinearLagVariableTrans)
            # print("---------------------------------------------------")

   #This function run the algorithm
    def Run(self):
        if Constants.Debug: print("\n We are in 'ProgressiveHedging' Class -- Run")
        self.PrintOnlyFirstStagePreviousValue = Constants.PrintOnlyFirstStageDecision
        if Constants.PrintOnlyFirstStageDecision:
            Constants.PrintOnlyFirstStageDecision = False
            # raise NameError("Progressive Hedging requires to print the full solution, set Constants.PrintOnlyFirstStageDecision to False")

        self.InitTrace()
        self.CurrentSolution = [None for w in self.ScenarioNrSet]

        while not self.CheckStopingCriterion():
            print("######################## PH Iteration: ", self.CurrentIteration)
            # Solve each scenario independentely
            self.SolveScenariosIndependently()

            # Create an implementable solution on the scenario tree
            self.PreviousImplementableSolution = copy.deepcopy(self.CurrentImplementableSolution)

            self.CurrentImplementableSolution = self.CreateImplementableSolution()

            self.CurrentIteration += 1

            if self.CurrentIteration == 1:
                    self.rho_PenaltyParameter = Constants.Rho_PH_PenaltyParameter

            # Increment rho_PenaltyParameter every 1000 iterations
            if (Constants.Dynamic_rho_PenaltyParameter) and (self.CurrentIteration > 1) and (self.CurrentIteration % 10 == 0):
                self.rho_PenaltyParameter += 0.005
                if Constants.Debug: print(f"Updated rho_PenaltyParameter to {self.rho_PenaltyParameter} after {self.CurrentIteration} iterations.")
                
            if False and self.CurrentIteration >= 2:
                self.UpdateMultipler()

            # Update the lagrangian multiplier
            self.UpdateLagragianMultipliers()

            #if Constants.Debug:
            #    self.PrintCurrentIteration()

        self.CurrentImplementableSolution.PHCost = self.CurrentImplementableSolution.TotalCost

        self.CurrentImplementableSolution.PHNrIteration = self.CurrentIteration
        #self.CurrentImplementableSolution.ComputeInventory()
        self.CurrentImplementableSolution.ComputeCost()
        self.WriteInTraceFile("End of PH algorithm cost: %r"%self.CurrentImplementableSolution.TotalCost)

        Constants.PrintOnlyFirstStageDecision = self.PrintOnlyFirstStagePreviousValue

        return self.CurrentImplementableSolution
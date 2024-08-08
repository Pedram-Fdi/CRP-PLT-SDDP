# This class contains the attributes and methods allowing to define the progressive hedging algorithm.
from ScenarioTree import ScenarioTree
from Constants import Constants
from MIPSolver import MIPSolver
from SDDP import SDDP
from sklearn import datasets, linear_model
from sklearn.preprocessing import PolynomialFeatures
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV, KFold
from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPRegressor
import sys
from sklearn.metrics import mean_absolute_error
import random
from SDDPStage import SDDPStage
import gurobipy as gp
from gurobipy import *
#from CallBackML import CallBackML
import pandas as pd
import numpy as np

from ProgressiveHedging import ProgressiveHedging

from Solution import Solution

import copy
import time
import math

class MLLocalSearch(object):

    def __init__(self, instance, testidentifier, treestructure, solver):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- Constructor")
        self.Instance = instance
        self.TestIdentifier = testidentifier

        if self.TestIdentifier.MLLocalSearchSetting == "NrIterationBeforeTabu10":
            Constants.MLLSNrIterationBeforeTabu = 10
        if self.TestIdentifier.MLLocalSearchSetting == "NrIterationBeforeTabu50":
            Constants.MLLSNrIterationBeforeTabu = 50
        if self.TestIdentifier.MLLocalSearchSetting == "NrIterationBeforeTabu100":
            Constants.MLLSNrIterationBeforeTabu = 100
        if self.TestIdentifier.MLLocalSearchSetting == "NrIterationBeforeTabu1000":
            Constants.MLLSNrIterationBeforeTabu = 1000
        if self.TestIdentifier.MLLocalSearchSetting == "TabuList0":
            Constants.MLLSTabuList = 0
        if self.TestIdentifier.MLLocalSearchSetting == "TabuList2":
            Constants.MLLSTabuList = 2
        if self.TestIdentifier.MLLocalSearchSetting == "TabuList5":
            Constants.MLLSTabuList = 5
        if self.TestIdentifier.MLLocalSearchSetting == "TabuList10":
            Constants.MLLSTabuList = 10
        if self.TestIdentifier.MLLocalSearchSetting == "TabuList50":
            Constants.MLLSTabuList = 50
        if self.TestIdentifier.MLLocalSearchSetting == "IterationTabu10":
            Constants.MLLSNrIterationTabu = 10
        if self.TestIdentifier.MLLocalSearchSetting == "IterationTabu100":
            Constants.MLLSNrIterationTabu = 100
        if self.TestIdentifier.MLLocalSearchSetting == "IterationTabu1000":
            Constants.MLLSNrIterationTabu = 1000
        if self.TestIdentifier.MLLocalSearchSetting == "PercentFilter1":
            Constants.MLLSPercentFilter = 1
        if self.TestIdentifier.MLLocalSearchSetting == "PercentFilter5":
            Constants.MLLSPercentFilter = 5
        if self.TestIdentifier.MLLocalSearchSetting == "PercentFilter10":
            Constants.MLLSPercentFilter = 10
        if self.TestIdentifier.MLLocalSearchSetting == "PercentFilter25":
            Constants.MLLSPercentFilter = 25

        self.TreeStructure = treestructure

        self.TraceFileName = "./Temp/MLLocalSearch%s.txt" % (self.TestIdentifier.GetAsString())
#
        self.Solver = solver
        self.TestedACFEstablishment = []
        self.TestedVehicleAssignment = []
        self.CostToGoOfTestedACFEstablishmentAndVehicleAssignment = []

        self.BestSolution = None
        self.BestSolutionCost = Constants.Infinity
        self.BestSolutionSafeUperBound = Constants.Infinity
        self.NrScenarioOnceXIsFix = self.TestIdentifier.NrScenario

        if not Constants.MIPBasedOnSymetricTree:
            if self.Instance.NrTimeBucket > 5:
             self.TestIdentifier.NrScenario = "all2"
            else:
                self.TestIdentifier.NrScenario = "all5"

        MLTreestructure = solver.GetTreeStructure()
        self.SDDPSolver = SDDP(self.Instance, self.TestIdentifier, MLTreestructure)
        self.SDDPSolver.HasFixed_ACFEstablishmentVar = True
        self.SDDPSolver.HasFixed_VehicleAssignmentVar = True
        self.SDDPSolver.IsIterationWithConvergenceTest = False
        # self.SDDPSolver.Run()
        self.SDDPSolver.GenerateSAAScenarios2()

        # Make sure SDDP do not enter in preliminary stage (at the end of the preliminary stage, SDDP would change the setup to Binary)
        Constants.SDDPGenerateCutWith2Stage = False
        #Constants.SolveRelaxationFirst = False
        Constants.SDDPRunSigleTree = False

        treestructure = [10] + [1] * (self.Instance.NrTimeBucket - 1)

        solution, self.SingleScenarioMipSolver = self.Solver.CRP(treestructure)
        print("ACFEstablishment_x_wi: ", solution.ACFEstablishment_x_wi)

        self.CurrentScenarioSeed = 0

        self.Iteration = 0
        self.SDDPNrScenarioTest = 200
        self.SDDPSolver.CurrentToleranceForSameLB = 1

        self.MLLocalSearchLB = -1
        self.MLLocalSearchTimeBestSol = -1
        self.InitTrace()

    def updateRecord(self, solution):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- updateRecord")

        if solution.TotalCost < self.BestSolutionCost \
                and self.SDDPSolver.CurrentExpvalueUpperBound < self.BestSolutionSafeUperBound\
                and self.SDDPSolver.CurrentLowerBound < self.BestSolutionSafeUperBound:
            self.BestSolutionCost = solution.TotalCost
            self.BestSolutionSafeUperBound = max( self.SDDPSolver.CurrentExpvalueUpperBound, self.SDDPSolver.CurrentLowerBound)
            self.BestSolution = solution
            self.MLLocalSearchTimeBestSol = time.time() - self.Start

    def RunSDDPAndAddToTraining(self):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- RunSDDPAndAddToTraining")

        solution = self.RunSDDP()

        self.TestedACFEstablishment.append(self.GivenACFEstablishment1D)
        self.TestedVehicleAssignment.append(self.GivenVehicleAssignment1D)
        self.CostToGoOfTestedACFEstablishmentAndVehicleAssignment.append(solution.TotalCost - (solution.ACFEstablishmentCost + solution.Vehicle_AssignmentCost))

        self.updateRecord(solution)

    def trainML(self):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- trainML")

        if Constants.Debug:
            print("TestedACFEstablishment: ", self.TestedACFEstablishment)
            print("TestedVehicleAssignment: ", self.TestedVehicleAssignment)
            print("CostToGoOfTestedACFEstablishmentAndVehicleAssignment: ", self.CostToGoOfTestedACFEstablishmentAndVehicleAssignment)

        # Concatenating x and θ for each sample to form the input for MLPRegressor
        input_features = [x + θ for x, θ in zip(self.TestedACFEstablishment, self.TestedVehicleAssignment)]

        # Reshape CostToGoOfTestedACFEstablishmentAndVehicleAssignment to match the expected input format for fitting
        cost_to_go = np.array(self.CostToGoOfTestedACFEstablishmentAndVehicleAssignment).reshape(-1)

        # Standardize the input features
        scaler = StandardScaler()
        input_features = scaler.fit_transform(input_features)

        # Check if we have enough samples to split
        if len(input_features) > 2:
            # Split data into training and validation sets
            X_train, X_val, y_train, y_val = train_test_split(input_features, cost_to_go, test_size=0.2, random_state=42)
        else:
            # Use all data for training if there are not enough samples
            X_train, y_train = input_features, cost_to_go
            X_val, y_val = input_features, cost_to_go  # Dummy values to avoid errors

        # Initialize and fit the MLPRegressor with hyperparameter tuning
        param_grid = {
            'hidden_layer_sizes': [(15,), (30,), (50,)],
            'alpha': [1e-5, 1e-4, 1e-3],
            'max_iter': [2000, 3000, 4000]
        }

        if Constants.ScailingDataML == 0:
            # Initialize and fit the MLPRegressor
            self.clf = MLPRegressor(solver='lbfgs', alpha=1e-5, hidden_layer_sizes=(15,), max_iter=2000)
            self.clf.fit(input_features, cost_to_go)
        else:
            mlp = MLPRegressor(solver='lbfgs', random_state=42)
            if len(X_train) > 1:
                grid_search = GridSearchCV(mlp, param_grid, cv=3 if len(X_train) >= 3 else KFold(n_splits=2))
                grid_search.fit(X_train, y_train)
                self.clf = grid_search.best_estimator_

                # Evaluate on validation set
                val_predictions = self.clf.predict(X_val)
                val_error = mean_absolute_error(y_val, val_predictions)
                if Constants.Debug: print(f"Model trained successfully with validation MAE: {val_error:.4f}")
                if Constants.Debug: print(f"Best parameters: {grid_search.best_params_}")
            else:
                self.clf = mlp
                self.clf.fit(X_train, y_train)
                if Constants.Debug: print("Not enough data for cross-validation. Model trained on all available data.")

        if Constants.Debug: print("Model trained successfully.")

    def Run(self):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- Run")

        self.Start = time.time()
        duration = 0

        self.CurrentTolerance = Constants.AlgorithmOptimalityTolerence

        self.BestSolutionCost = Constants.Infinity
        self.BestSolutionSafeUperBound = Constants.Infinity


        curentsolution = copy.deepcopy(self.BestSolution)
        self.RunSDDP(relaxacfvehicle = True)

        while(duration < Constants.AlgorithmTimeLimit_MLTabu_Part):
            
            if(self.Iteration == 0):
                self.WriteInTraceFile(f"Using Heuristic ACFEstablishment and Vehicle Assignment (Iteration: {self.Iteration})...")
                self.GivenACFEstablishment1D, self.GivenVehicleAssignment2D = self.GetHeuristicACFEstablishmentAndVehicleAssignment()
            else:
                if(self.Iteration <= Constants.MLLSNrIterationBeforeTabu):
                    self.WriteInTraceFile(f"Using MIP for ACFEstablishment and Vehicle Assignment (Iteration: {self.Iteration})...")
                    self.GivenACFEstablishment1D, self.GivenVehicleAssignment2D = self.GetACFEstablishmentAndVehicleAssignmentWithMIP()
                else:
                    if self.Iteration == Constants.MLLSNrIterationBeforeTabu + 1:
                        self.WriteInTraceFile(f"Using Tabu for ACFEstablishment and Vehicle Assignment (Iteration: {self.Iteration})...")
                        curentsolution = copy.deepcopy(self.BestSolution)
                    self.GivenACFEstablishment1D, self.GivenVehicleAssignment2D = self.Descent(curentsolution)

            self.GivenVehicleAssignment1D = [self.GivenVehicleAssignment2D[m][i] 
                                                for i in self.Instance.ACFPPointSet 
                                                for m in self.Instance.RescueVehicleSet]

            self.RunSDDPAndAddToTraining()

            self.WriteInTraceFile("Iteration: %r, Considered ACFEstablish.: %r, VehicleAssing.: %r, MLCost: %r, ActualCost: %r\n" % (self.Iteration, self.GivenACFEstablishment1D, self.GivenVehicleAssignment1D, self.PredictForACFEstablishment_VehicleAssignment(self.GivenACFEstablishment1D, self.GivenVehicleAssignment2D) , self.CostToGoOfTestedACFEstablishmentAndVehicleAssignment[-1]))

            self.trainML()

            '''
            # print("-------------------------Linear Regression-----------------------------")
            # insampleprediction = self.Regr.predict(self.TestedFixedTrans)
            # outsampleprediction = self.Regr.predict(self.outofsampletest)
            # print("self.TestedFixedTrans : %r "%self.TestedFixedTrans)
            # print("self.CostToGoOfTestedFixedTrans : %r "%self.CostToGoOfTestedFixedTrans)
            # print("insampleprediction : %r " % insampleprediction)
            # print("insample absolute error %r"% mean_absolute_error(self.CostToGoOfTestedFixedTrans, insampleprediction) )
            # print("outsampleprediction : %r " % outsampleprediction)
            # print("outsample absolute error %r" % mean_absolute_error(self.outofsamplecost, outsampleprediction))
            #
            # print("-------------------------Polynomial Regression-----------------------------")
            # X_poly = self.poly.fit_transform(self.TestedFixedTrans)
            # insamplepredictionpoly = self.lin2.predict(X_poly)
            # X_poly = self.poly.fit_transform(self.outofsampletest)
            # outsamplepredictionpoly = self.lin2.predict(X_poly)
            # print("insamplepredictionpoly : %r " % insamplepredictionpoly)
            # print("insample absolute error predictionpoly %r" % mean_absolute_error(self.CostToGoOfTestedFixedTrans, insamplepredictionpoly))
            # print("outsamplepredictionpoly : %r " % insamplepredictionpoly)
            # print("outsample absolute error predictionpoly %r" % mean_absolute_error(self.outofsamplecost,
            #                                                                          outsamplepredictionpoly))
            #
            # print("------------------------- Ridge -----------------------------")
            # insamplepredictionRidge = self.reg.predict(self.TestedFixedTrans)
            # outsamplepredictionRidge = self.reg.predict(self.outofsampletest)
            # print("self.TestedFixedTrans : %r " % self.TestedFixedTrans)
            # print("self.CostToGoOfTestedFixedTrans : %r " % self.CostToGoOfTestedFixedTrans)
            # print("insampleprediction : %r " % insamplepredictionRidge)
            # print("insample absolute error %r" % mean_absolute_error(self.CostToGoOfTestedFixedTrans,
            #                                                          insamplepredictionRidge))
            # print("outsampleprediction : %r " % outsamplepredictionRidge)
            # print("outsample absolute error %r" % mean_absolute_error(self.outofsamplecost, outsamplepredictionRidge))
            '''

            # Combine the TestedACFEstablishment and TestedVehicleAssignment for prediction
            input_features_for_prediction = [x + θ for x, θ in zip(self.TestedACFEstablishment, self.TestedVehicleAssignment)]

            # Make predictions using the trained neural network model
            insamplepredictionNN = self.clf.predict(input_features_for_prediction)

            if Constants.Debug:
                print("-------------------------Neural NetWork-----------------------------")
                print("TestedACFEstablishment : %r " % self.TestedACFEstablishment)
                print("TestedVehicleAssignment : %r " % self.TestedVehicleAssignment)
                print("self.CostToGoOfTestedACFEstablishmentAndVehicleAssignment : %r " % self.CostToGoOfTestedACFEstablishmentAndVehicleAssignment)
                print("insampleprediction : %r " % insamplepredictionNN)
                print("insample absolute error %r" % mean_absolute_error(self.CostToGoOfTestedACFEstablishmentAndVehicleAssignment, insamplepredictionNN))
                        
            self.Iteration += 1

            end = time.time()
            duration = end - self.Start

        self.GivenACFEstablishment1D = self.BestSolution.ACFEstablishment_x_wi[0]
        self.GivenACFEstablishment1D = [round(self.GivenACFEstablishment1D[i]) 
                                        for i in self.Instance.ACFPPointSet]
        
        self.GivenVehicleAssignment2D = self.BestSolution.VehicleAssignment_thetavar_wmi[0]
        self.GivenVehicleAssignment2D = [[round(self.GivenVehicleAssignment2D[m][i]) 
                                            for i in self.Instance.ACFPPointSet]
                                            for m in self.Instance.RescueVehicleSet]

        self.TestIdentifier.NrScenario = self.NrScenarioOnceXIsFix
        self.TestIdentifier.Model = Constants.ModelHeuristicMulti_Stage
        self.SDDPSolver = SDDP(self.Instance, self.TestIdentifier, self.TreeStructure)
        self.SDDPSolver.HasFixed_ACFEstablishmentVar = True
        self.SDDPSolver.HasFixed_VehicleAssignmentVar = True
        self.SDDPSolver.HeuristicACFEstablishmentValue = self.GivenACFEstablishment1D
        self.SDDPSolver.HeuristicVehicleAssignmentValue = self.GivenVehicleAssignment2D
        self.SDDPSolver.IsIterationWithConvergenceTest = False

        self.GivenVehicleAssignment1D = [self.GivenVehicleAssignment2D[m][i] 
                                            for i in self.Instance.ACFPPointSet 
                                            for m in self.Instance.RescueVehicleSet]

        # Make sure SDDP do not enter in preliminary stage (at the end of the preliminary stage, SDDP would change the setup to binary)
        Constants.SDDPGenerateCutWith2Stage = False
        Constants.SolveRelaxationFirst = False
        Constants.SDDPRunSigleTree = False
        self.SDDPSolver.CurrentToleranceForSameLB = 0.0001
        self.Start = 0
        self.SDDPSolver.Run()
        self.BestSolution = self.SDDPSolver.CreateSolutionAtFirstStage()


        self.SDDPSolver.SDDPNrScenarioTest = 1000

        self.SDDPSolver.ComputeUpperBound()

        self.TestIdentifier.Model = Constants.ModelMulti_Stage
        return self.BestSolution

    def GetCostBasedML(self, input_features):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- GetCostBasedML")
        
        return self.clf.predict(input_features)
    
    def GetACFEstablishmentAndVehicleAssignmentWithMIP(self):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- GetACFEstablishmentAndVehicleAssignmentWithMIP")

        self.SDDPSolver.ForwardStage[0].ChangeACFEstablishmentVarToBinary()
        self.SDDPSolver.ForwardStage[0].ChangeVehicleAssignmentVarToInteger()
        
        self.SDDPSolver.ForwardStage[0].GurobiModel.optimize()
        
        # Check if the optimization was successful
        if self.SDDPSolver.ForwardStage[0].GurobiModel.status == GRB.Status.OPTIMAL:
            sol = self.SDDPSolver.ForwardStage[0].GurobiModel
            self.MLLocalSearchLB = sol.objVal  # Get the objective value from Gurobi solution

            if Constants.Debug: print("MLLocalSearchLB: ", self.MLLocalSearchLB)

            GivenACFEstablishment = []
            for i in self.Instance.ACFPPointSet:
                index_var = self.SDDPSolver.ForwardStage[0].GetIndexACFEstablishmentVariable(i)
                value = self.SDDPSolver.ForwardStage[0].ACFEstablishment_Var_SDDP[index_var].X
                GivenACFEstablishment.append(value)
            if Constants.Debug: print("GivenACFEstablishment: ", GivenACFEstablishment)
            
            GivenVehicleAssignment=[]
            for m in self.Instance.RescueVehicleSet:
                row=[]
                for i in self.Instance.ACFPPointSet:
                    index_var = self.SDDPSolver.ForwardStage[0].GetIndexVehicleAssignmentVariable(m, i)
                    value = self.SDDPSolver.ForwardStage[0].VehicleAssignment_Var_SDDP[index_var].X
                    row.append(value)
                GivenVehicleAssignment.append(row)
            if Constants.Debug: print("GivenVehicleAssignment: ", GivenVehicleAssignment)

            return GivenACFEstablishment, GivenVehicleAssignment
        else:
            if Constants.Debug: print("Optimization problem did not solve to optimality")
            return None, None

    def InitTrace(self):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- InitTrace")

        if Constants.PrintSDDPTrace:
            self.TraceFile = open(self.TraceFileName, "w")
            self.TraceFile.write("Start the MLLocal search \n")
            self.TraceFile.close()

    def PredictForACFEstablishment_VehicleAssignment(self, acfestablishment, vehicleassignment):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- PredictForACFEstablishment_VehicleAssignment")

        if self.Iteration < Constants.MLLSNrIterationBeforeTabu:
                return -1;
        else:
            acfestablishmentcost = sum(acfestablishment[i] * self.Instance.Fixed_Cost_ACF[i] 
                                          for i in self.Instance.ACFPPointSet)
            
            vehicleassignmentcost = sum(vehicleassignment[m][i] * self.Instance.VehicleAssignment_Cost[m] 
                                          for i in self.Instance.ACFPPointSet
                                          for m in self.Instance.RescueVehicleSet)
            
            # Combine acfestablishment and vehicleassignment for prediction
            acfestablishment1D = [acfestablishment[i] for i in self.Instance.ACFPPointSet]
            
            # Flatten the 2D vehicleassignment into a 1D list
            vehicleassignment1D = [vehicleassignment[m][i] 
                                   for i in self.Instance.ACFPPointSet
                                   for m in self.Instance.RescueVehicleSet]
            
            combined_features = acfestablishment1D + vehicleassignment1D

            # Reshape to match the expected input format for the model
            combined_features = [combined_features]

            approxcosttogo = self.GetCostBasedML(combined_features)

        return (acfestablishmentcost + vehicleassignmentcost + approxcosttogo)

    def Descent(self, initialsolution):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- Descent")

        currentsolution = initialsolution

        self.UseTabu = True
        self.DescentBestCost = Constants.Infinity
        self.DescentBestMove = ("N", -1, -1)

        self.TabuCurrentSolLB = Constants.Infinity
        self.TabuBestSolLB = Constants.Infinity
        self.TabuBestSolLB = Constants.Infinity
        self.TabuBestSolPredictedUB = Constants.Infinity
        self.TabuBestSol = None
       
        iterationtabu = [0 for i in self.Instance.ACFPPointSet]
        
        curentiterationLS = 0
        Total_Used_Vehicles = [0 for m in self.Instance.RescueVehicleSet]
        Total_Available_Vehicles = [0 for m in self.Instance.RescueVehicleSet]

        while ( not self.UseTabu and self.DescentBestMove[0] != "") or (self.UseTabu and (self.TabuBestSol is None or curentiterationLS < Constants.MLLSNrIterationTabu)):
                
            self.TabuCurrentPredictedUB = Constants.Infinity
            self.TabuCurrentSolLB = Constants.Infinity
            self.DescentBestMove = ("", -1, -1)
            CurrentACFEstablishmentCost = sum(currentsolution.ACFEstablishment_x_wi[0][i] * self.Instance.Fixed_Cost_ACF_Constraint[i] for i in self.Instance.ACFPPointSet)                
            for m in self.Instance.RescueVehicleSet:
                Total_Used_Vehicles[m] = sum(currentsolution.VehicleAssignment_thetavar_wmi[0][m][acf] for acf in self.Instance.ACFPPointSet)
            for m in self.Instance.RescueVehicleSet:
                Total_Available_Vehicles[m] = self.Instance.Number_Rescue_Vehicle_ACF[m] - Total_Used_Vehicles[m]                      
            if Constants.Debug:
                print("CurrentACFEstablishmentCost: ", CurrentACFEstablishmentCost)
                print("Total_Used_Vehicles: ", Total_Used_Vehicles)
                print("Total_Available_Vehicles: ", Total_Available_Vehicles)
                print("self.Instance.Total_Budget_ACF_Establishment: ", self.Instance.Total_Budget_ACF_Establishment)
                print("self.Instance.Fixed_Cost_ACF_Constraint: ", self.Instance.Fixed_Cost_ACF_Constraint)
                
            move_found = False

            for i in self.Instance.ACFPPointSet:
                Random = random.uniform(0, 1)
                if iterationtabu[i] <= curentiterationLS and Random < (float(Constants.MLLSPercentFilter) / 100.0):
                    if currentsolution.ACFEstablishment_x_wi[0][i] == 1:
                        NewACFEstablishmentCost_WithoutACF_i = CurrentACFEstablishmentCost - (currentsolution.ACFEstablishment_x_wi[0][i] * self.Instance.Fixed_Cost_ACF_Constraint[i])                                                  
                        if Constants.Debug: print(f"NewACFEstablishmentCost_WithoutACF_i:{i}: ", NewACFEstablishmentCost_WithoutACF_i)
                        if i > 0:
                            ## First Check if it is possible to change your ACFEstablishment variable   
                            NewACFEstablishmentCost_Earlier = NewACFEstablishmentCost_WithoutACF_i + self.Instance.Fixed_Cost_ACF_Constraint[i - 1]
                            if NewACFEstablishmentCost_Earlier <= self.Instance.Total_Budget_ACF_Establishment:
                                if Constants.Debug: print(f"Before going to EvaluateMoveEarlier_Fixed for i:{i}, \n with ACFEstablishment_x_wi:{currentsolution.ACFEstablishment_x_wi[0]}, \n VehicleAssignment_thetavar_wmi:{currentsolution.VehicleAssignment_thetavar_wmi[0]}")
                                self.EvaluateMoveEarlier_Fixed(currentsolution.ACFEstablishment_x_wi[0], currentsolution.VehicleAssignment_thetavar_wmi[0], i)
                                
                                # Apply the conditions for each m
                                for m in self.Instance.RescueVehicleSet:
                                    if not (Total_Available_Vehicles[m] > 0 and (Total_Used_Vehicles[m] + Constants.VehicleChangesinTabu) <= self.Instance.Number_Rescue_Vehicle_ACF[m]):
                                        if Constants.Debug: print(f"Condition failed for m: {m}, stopping further checks.")
                                        break
                                else:
                                    # This block will only execute if the loop wasn't broken, meaning all conditions were met
                                    if Constants.Debug: print(f"Before going to EvaluateMoveEarlier_Increase for i: {i}, \n with ACFEstablishment_x_wi: {currentsolution.ACFEstablishment_x_wi[0]}, \n VehicleAssignment_thetavar_wmi: {currentsolution.VehicleAssignment_thetavar_wmi[0]}")
                                    self.EvaluateMoveEarlier_Increase(currentsolution.ACFEstablishment_x_wi[0], currentsolution.VehicleAssignment_thetavar_wmi[0], i)
                                move_found = True
                            else:
                                if Constants.Debug: print("(EvaluateMoveEarlier) is an invalid Move due to the Budget Constraint!")
                        if i < self.Instance.NrACFPPoints - 1:
                            ## First Check if it is possible to change your ACFEstablishment variable   
                            NewACFEstablishmentCost_Later = NewACFEstablishmentCost_WithoutACF_i + self.Instance.Fixed_Cost_ACF_Constraint[i + 1]
                            if NewACFEstablishmentCost_Later <= self.Instance.Total_Budget_ACF_Establishment:    
                                if Constants.Debug: print(f"Before going to EvaluateMoveLater_Fixed for i:{i}, \n with ACFEstablishment_x_wi:{currentsolution.ACFEstablishment_x_wi[0]}, \n VehicleAssignment_thetavar_wmi:{currentsolution.VehicleAssignment_thetavar_wmi[0]}")
                                self.EvaluateMoveLater_Fixed(currentsolution.ACFEstablishment_x_wi[0], currentsolution.VehicleAssignment_thetavar_wmi[0], i)

                                # Apply the conditions for each m
                                for m in self.Instance.RescueVehicleSet:
                                    if not (Total_Available_Vehicles[m] > 0 and (Total_Used_Vehicles[m] + Constants.VehicleChangesinTabu) <= self.Instance.Number_Rescue_Vehicle_ACF[m]):
                                        if Constants.Debug: print(f"Condition failed for m: {m}, stopping further checks.")
                                        break
                                else:                                    
                                    if Constants.Debug: print(f"Before going to EvaluateMoveLater_Increase for i:{i}, \n with ACFEstablishment_x_wi:{currentsolution.ACFEstablishment_x_wi[0]}, \n VehicleAssignment_thetavar_wmi:{currentsolution.VehicleAssignment_thetavar_wmi[0]}")                                    
                                    self.EvaluateMoveLater_Increase(currentsolution.ACFEstablishment_x_wi[0], currentsolution.VehicleAssignment_thetavar_wmi[0], i)
                                move_found = True
                            else:
                                if Constants.Debug: print("(EvaluateMoveLater) is an invalid Move due to the Budget Constraint!")
                        # Remoiving an ACF is always ok considering limited budget!
                        if Constants.Debug: print(f"Before going to EvaluateRemove for i:{i}, \n with ACFEstablishment_x_wi:{currentsolution.ACFEstablishment_x_wi[0]}, \n VehicleAssignment_thetavar_wmi:{currentsolution.VehicleAssignment_thetavar_wmi[0]}")                                                                
                        self.EvaluateRemove(currentsolution.ACFEstablishment_x_wi[0], currentsolution.VehicleAssignment_thetavar_wmi[0], i)
                        move_found = True
                    else:
                        NewACFEstablishmentCost_Add = CurrentACFEstablishmentCost + self.Instance.Fixed_Cost_ACF_Constraint[i] 
                        if Constants.Debug: print(f"NewACFEstablishmentCost_Add_i:{i}: ", NewACFEstablishmentCost_Add)
                        if NewACFEstablishmentCost_Add <= self.Instance.Total_Budget_ACF_Establishment: 
                            # Apply the conditions for each m
                            for m in self.Instance.RescueVehicleSet:
                                if not (Total_Available_Vehicles[m] > 0 and (Total_Used_Vehicles[m] + Constants.VehicleChangesinTabu) <= self.Instance.Number_Rescue_Vehicle_ACF[m]):
                                    if Constants.Debug: print(f"Condition failed for m: {m}, stopping further checks.")
                                    break
                            else:                                                       
                                if Constants.Debug: print(f"Before going to EvaluateAdd for i:{i}, \n with ACFEstablishment_x_wi:{currentsolution.ACFEstablishment_x_wi[0]}, \n VehicleAssignment_thetavar_wmi:{currentsolution.VehicleAssignment_thetavar_wmi[0]}")                                                                                                
                                self.EvaluateAdd(currentsolution.ACFEstablishment_x_wi[0], currentsolution.VehicleAssignment_thetavar_wmi[0], i)
                                move_found = True
                        else:
                            if Constants.Debug: print("(EvaluateAdd) is an invalid Move due to the Budget Constraint!")


            #perform the best move
            if move_found:
                if self.UseTabu:
                    self.DescentBestMove = self.TabuBestMove
                                
                MoveType = self.DescentBestMove[0]
                acf = self.DescentBestMove[1]

                tabulistsize = Constants.MLLSTabuList
                if MoveType == "EF":
                    currentsolution.ACFEstablishment_x_wi[0][acf] = 0
                    currentsolution.ACFEstablishment_x_wi[0][acf - 1] = 1
                    for m in self.Instance.RescueVehicleSet:
                        currentsolution.VehicleAssignment_thetavar_wmi[0][m][acf - 1] = currentsolution.VehicleAssignment_thetavar_wmi[0][m][acf]
                        currentsolution.VehicleAssignment_thetavar_wmi[0][m][acf] = 0
                    iterationtabu[acf - 1] = curentiterationLS + tabulistsize
                    iterationtabu[acf] = curentiterationLS + tabulistsize
                if MoveType == "EI":
                    currentsolution.ACFEstablishment_x_wi[0][acf] = 0
                    currentsolution.ACFEstablishment_x_wi[0][acf - 1] = 1
                    for m in self.Instance.RescueVehicleSet:
                        currentsolution.VehicleAssignment_thetavar_wmi[0][m][acf - 1] = currentsolution.VehicleAssignment_thetavar_wmi[0][m][acf] + Constants.VehicleChangesinTabu
                        currentsolution.VehicleAssignment_thetavar_wmi[0][m][acf] = 0
                    iterationtabu[acf - 1] = curentiterationLS + tabulistsize
                    iterationtabu[acf] = curentiterationLS + tabulistsize
                if MoveType == "LF":
                    currentsolution.ACFEstablishment_x_wi[0][acf] = 0
                    currentsolution.ACFEstablishment_x_wi[0][acf + 1] = 1
                    for m in self.Instance.RescueVehicleSet:
                        currentsolution.VehicleAssignment_thetavar_wmi[0][m][acf + 1] = currentsolution.VehicleAssignment_thetavar_wmi[0][m][acf]
                        currentsolution.VehicleAssignment_thetavar_wmi[0][m][acf] = 0
                    iterationtabu[acf + 1] = curentiterationLS + tabulistsize
                    iterationtabu[acf] = curentiterationLS + tabulistsize
                if MoveType == "LI":
                    currentsolution.ACFEstablishment_x_wi[0][acf] = 0
                    currentsolution.ACFEstablishment_x_wi[0][acf + 1] = 1
                    for m in self.Instance.RescueVehicleSet:
                        currentsolution.VehicleAssignment_thetavar_wmi[0][m][acf + 1] = currentsolution.VehicleAssignment_thetavar_wmi[0][m][acf] + Constants.VehicleChangesinTabu
                        currentsolution.VehicleAssignment_thetavar_wmi[0][m][acf] = 0
                    iterationtabu[acf + 1] = curentiterationLS + tabulistsize
                    iterationtabu[acf] = curentiterationLS + tabulistsize
                if MoveType == "A":
                    currentsolution.ACFEstablishment_x_wi[0][acf] = 1
                    for m in self.Instance.RescueVehicleSet:
                        currentsolution.VehicleAssignment_thetavar_wmi[0][m][acf] = currentsolution.VehicleAssignment_thetavar_wmi[0][m][acf] + Constants.VehicleChangesinTabu
                    iterationtabu[acf] = curentiterationLS + tabulistsize
                if MoveType == "R":
                    currentsolution.ACFEstablishment_x_wi[0][acf] = 0
                    for m in self.Instance.RescueVehicleSet:
                        currentsolution.VehicleAssignment_thetavar_wmi[0][m][acf] = 0
                    iterationtabu[acf] = curentiterationLS + tabulistsize

                cost = self.PredictForACFEstablishment_VehicleAssignment(currentsolution.ACFEstablishment_x_wi[0], currentsolution.VehicleAssignment_thetavar_wmi[0])
                lb = self.GetCurrentLowerBound(currentsolution.ACFEstablishment_x_wi[0], currentsolution.VehicleAssignment_thetavar_wmi[0])
                newrecord = False

                if self.TabuBestSolLB < self.BestSolutionSafeUperBound:
                    if lb < self.BestSolutionSafeUperBound and cost < self.TabuBestCost:
                        newrecord = True
                else:
                    if(lb < self.TabuBestSolLB ):
                        newrecord = True

                if newrecord:
                        self.TabuBestCost = cost
                        self.TabuBestSolLB = lb
                        self.TabuBestSol = copy.deepcopy(currentsolution)

            curentiterationLS += 1


        return self.TabuBestSol.ACFEstablishment_x_wi[0], self.TabuBestSol.VehicleAssignment_thetavar_wmi[0]

    def UpdateDescentRecord(self, move, i, cost, acfestablishmentvars, vehicleassignmentvars):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- UpdateDescentRecord")
            
        lb = self.GetCurrentLowerBound(acfestablishmentvars, vehicleassignmentvars)
        newrecord = False

        if self.TabuCurrentSolLB < self.BestSolutionSafeUperBound:
            if lb < self.BestSolutionSafeUperBound and cost < self.TabuCurrentPredictedUB:
                newrecord = True
        else:
            if (lb < self.TabuCurrentSolLB):
                newrecord = True

        if newrecord:
            self.TabuCurrentPredictedUB = cost
            self.TabuCurrentSolLB = lb
            self.TabuBestMove = (move, i)

    def EvaluateMoveEarlier_Fixed(self, currentacfestablishmentvars, currentvehicleassignmentvars, i):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- EvaluateMoveEarlier_Fixed")

        previousvalue_x = currentacfestablishmentvars[i]
        previousvalueprev_x = currentacfestablishmentvars[i - 1]

        previousvalue_theta = [0 for m in self.Instance.RescueVehicleSet]
        previousvalueprev_theta = [0 for m in self.Instance.RescueVehicleSet]
        for m in self.Instance.RescueVehicleSet:
            previousvalue_theta[m] = currentvehicleassignmentvars[m][i]
            previousvalueprev_theta[m] = currentvehicleassignmentvars[m][i - 1]

        currentacfestablishmentvars[i] = 0
        currentacfestablishmentvars[i - 1] = 1
        for m in self.Instance.RescueVehicleSet:
            currentvehicleassignmentvars[m][i - 1] = currentvehicleassignmentvars[m][i]
            currentvehicleassignmentvars[m][i] = 0 

        cost = self.PredictForACFEstablishment_VehicleAssignment(currentacfestablishmentvars, currentvehicleassignmentvars)
        self.UpdateDescentRecord("EF", i, cost, currentacfestablishmentvars, currentvehicleassignmentvars)

        currentacfestablishmentvars[i] = previousvalue_x
        currentacfestablishmentvars[i - 1] = previousvalueprev_x
        for m in self.Instance.RescueVehicleSet:
            currentvehicleassignmentvars[m][i] = previousvalue_theta[m]
            currentvehicleassignmentvars[m][i - 1] = previousvalueprev_theta[m]

        return cost
    
    def EvaluateMoveEarlier_Increase(self, currentacfestablishmentvars, currentvehicleassignmentvars, i):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- EvaluateMoveEarlier_Increase")


        previousvalue_x = currentacfestablishmentvars[i]
        previousvalueprev_x = currentacfestablishmentvars[i - 1]

        previousvalue_theta = [0 for m in self.Instance.RescueVehicleSet]
        previousvalueprev_theta = [0 for m in self.Instance.RescueVehicleSet]
        for m in self.Instance.RescueVehicleSet:
            previousvalue_theta[m] = currentvehicleassignmentvars[m][i]
            previousvalueprev_theta[m] = currentvehicleassignmentvars[m][i - 1]

        currentacfestablishmentvars[i] = 0
        currentacfestablishmentvars[i - 1] = 1
        
        for m in self.Instance.RescueVehicleSet:
            currentvehicleassignmentvars[m][i - 1] = currentvehicleassignmentvars[m][i] + Constants.VehicleChangesinTabu
            currentvehicleassignmentvars[m][i] = 0 

        cost = self.PredictForACFEstablishment_VehicleAssignment(currentacfestablishmentvars, currentvehicleassignmentvars)
        self.UpdateDescentRecord("EI", i, cost, currentacfestablishmentvars, currentvehicleassignmentvars)

        currentacfestablishmentvars[i] = previousvalue_x
        currentacfestablishmentvars[i - 1] = previousvalueprev_x
        for m in self.Instance.RescueVehicleSet:
            currentvehicleassignmentvars[m][i] = previousvalue_theta[m]
            currentvehicleassignmentvars[m][i - 1] = previousvalueprev_theta[m]

        return cost

    def EvaluateMoveLater_Fixed(self, currentacfestablishmentvars, currentvehicleassignmentvars, i):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- EvaluateMoveLater_Fixed")

        previousvalue_x = currentacfestablishmentvars[i]
        previousvalueprev_x = currentacfestablishmentvars[i + 1]

        previousvalue_theta = [0 for m in self.Instance.RescueVehicleSet]
        previousvalueprev_theta = [0 for m in self.Instance.RescueVehicleSet]
        for m in self.Instance.RescueVehicleSet:
            previousvalue_theta[m] = currentvehicleassignmentvars[m][i]
            previousvalueprev_theta[m] = currentvehicleassignmentvars[m][i + 1]

        currentacfestablishmentvars[i] = 0
        currentacfestablishmentvars[i + 1] = 1
        for m in self.Instance.RescueVehicleSet:
            currentvehicleassignmentvars[m][i + 1] = currentvehicleassignmentvars[m][i]
            currentvehicleassignmentvars[m][i] = 0  

        cost = self.PredictForACFEstablishment_VehicleAssignment(currentacfestablishmentvars, currentvehicleassignmentvars)
        self.UpdateDescentRecord("LF", i, cost, currentacfestablishmentvars, currentvehicleassignmentvars)

        currentacfestablishmentvars[i] = previousvalue_x
        currentacfestablishmentvars[i + 1] = previousvalueprev_x
        for m in self.Instance.RescueVehicleSet:
            currentvehicleassignmentvars[m][i] = previousvalue_theta[m]
            currentvehicleassignmentvars[m][i + 1] = previousvalueprev_theta[m]

        return cost
    
    def EvaluateMoveLater_Increase(self, currentacfestablishmentvars, currentvehicleassignmentvars, i):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- EvaluateMoveLater_Increase")

        previousvalue_x = currentacfestablishmentvars[i]
        previousvalueprev_x = currentacfestablishmentvars[i + 1]

        previousvalue_theta = [0 for m in self.Instance.RescueVehicleSet]
        previousvalueprev_theta = [0 for m in self.Instance.RescueVehicleSet]
        
        for m in self.Instance.RescueVehicleSet:
            previousvalue_theta[m] = currentvehicleassignmentvars[m][i]
            previousvalueprev_theta[m] = currentvehicleassignmentvars[m][i + 1]

        currentacfestablishmentvars[i] = 0
        currentacfestablishmentvars[i + 1] = 1
        
        for m in self.Instance.RescueVehicleSet:
            currentvehicleassignmentvars[m][i + 1] = currentvehicleassignmentvars[m][i] + Constants.VehicleChangesinTabu
            currentvehicleassignmentvars[m][i] = 0

        cost = self.PredictForACFEstablishment_VehicleAssignment(currentacfestablishmentvars, currentvehicleassignmentvars)
        self.UpdateDescentRecord("LI", i, cost, currentacfestablishmentvars, currentvehicleassignmentvars)

        currentacfestablishmentvars[i] = previousvalue_x
        currentacfestablishmentvars[i + 1] = previousvalueprev_x
        for m in self.Instance.RescueVehicleSet:
            currentvehicleassignmentvars[m][i] = previousvalue_theta[m]
            currentvehicleassignmentvars[m][i + 1] = previousvalueprev_theta[m]

        return cost

    def EvaluateAdd(self, currentacfestablishmentvars, currentvehicleassignmentvars, i):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- EvaluateAdd")

        previousvalue_x = currentacfestablishmentvars[i]

        previousvalue_theta = [0 for m in self.Instance.RescueVehicleSet]
        for m in self.Instance.RescueVehicleSet:
            previousvalue_theta[m] = currentvehicleassignmentvars[m][i]
        
        currentacfestablishmentvars[i] = 1
        for m in self.Instance.RescueVehicleSet:
            currentvehicleassignmentvars[m][i] = currentvehicleassignmentvars[m][i] + Constants.VehicleChangesinTabu
                        
        cost = self.PredictForACFEstablishment_VehicleAssignment(currentacfestablishmentvars, currentvehicleassignmentvars)
        self.UpdateDescentRecord("A", i, cost, currentacfestablishmentvars, currentvehicleassignmentvars)

        currentacfestablishmentvars[i] = previousvalue_x
        for m in self.Instance.RescueVehicleSet:
            currentvehicleassignmentvars[m][i] = previousvalue_theta[m]

        return cost
    
    def EvaluateRemove(self, currentacfestablishmentvars, currentvehicleassignmentvars, i):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- EvaluateRemove")

        previousvalue_x = currentacfestablishmentvars[i]

        previousvalue_theta = [0 for m in self.Instance.RescueVehicleSet]
        for m in self.Instance.RescueVehicleSet:
            previousvalue_theta[m] = currentvehicleassignmentvars[m][i]

        currentacfestablishmentvars[i] = 0
        for m in self.Instance.RescueVehicleSet:
            currentvehicleassignmentvars[m][i] = 0
            
        cost = self.PredictForACFEstablishment_VehicleAssignment(currentacfestablishmentvars, currentvehicleassignmentvars)
        self.UpdateDescentRecord("R", i, cost, currentacfestablishmentvars, currentvehicleassignmentvars)

        currentacfestablishmentvars[i] = previousvalue_x
        for m in self.Instance.RescueVehicleSet:
            currentvehicleassignmentvars[m][i] = previousvalue_theta[m]

        return cost
                  
    def RunSDDP(self, relaxacfvehicle = False, runwithbinary = False):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- RunSDDP")

        self.SDDPSolver.WriteInTraceFile("__________________New run of SDDP ______________best ub: %r______ MLLocalSearchLB: %r \n"%(self.BestSolutionSafeUperBound, self.MLLocalSearchLB))

        if runwithbinary:
            if self.SDDPSolver.ForwardStage[0].MIPDefined:
                self.SDDPSolver.ForwardStage[0].ChangeACFEstablishmentVarToBinary()
                self.SDDPSolver.ForwardStage[0].ChangeVehicleAssignmentVarToInteger()

        if relaxacfvehicle:
            if self.SDDPSolver.ForwardStage[0].MIPDefined:
                self.SDDPSolver.ForwardStage[0].ChangeACFEstablishmentVarToContinous()
                self.SDDPSolver.ForwardStage[0].ChangeVehicleAssignmentVarToContinous()

        if  not relaxacfvehicle and not runwithbinary:
            self.SDDPSolver.HeuristicACFEstablishmentValue = self.GivenACFEstablishment1D
            self.SDDPSolver.HeuristicVehicleAssignmentValue = self.GivenVehicleAssignment2D

            self.SDDPSolver.WriteInTraceFile("_Values of X : %r \n" %self.SDDPSolver.HeuristicACFEstablishmentValue)
            self.SDDPSolver.WriteInTraceFile("_Values of Thetavar : %r \n" %self.SDDPSolver.HeuristicVehicleAssignmentValue)

            if self.SDDPSolver.ForwardStage[0].MIPDefined :
                self.SDDPSolver.ForwardStage[0].ChangeACFEstablishmentVarToContinous()          #Just Added 
                self.SDDPSolver.ForwardStage[0].ChangeVehicleAssignmentVarToContinous()         #Just Added           
                self.SDDPSolver.ForwardStage[0].ChangeACFEstablishmentToValueOfTwoStage()
                self.SDDPSolver.ForwardStage[0].ChangeVehicleAssignmentToValueOfTwoStage()


        stop = False
        lastbeforestop = False

        self.SDDPSolver.NrIterationWithoutLBImprovment = 0

        self.SDDPSolver.CorePointApheresisAssignmentValues = []
        self.SDDPSolver.CorePointTransshipmentHIValues = []
        self.SDDPSolver.CorePointTransshipmentIIValues = []
        self.SDDPSolver.CorePointTransshipmentHHValues = []

        self.SDDPSolver.CurrentForwardSampleSize = self.TestIdentifier.NrScenarioForward

        iteration = 0

        self.FirstStageCutAddedInLastSDDP=[]
        while (not stop):
            self.SDDPSolver.GenerateTrialScenarios()
            self.SDDPSolver.ForwardPass()
            self.SDDPSolver.ComputeCost()
            self.SDDPSolver.UpdateLowerBound()
            self.SDDPSolver.UpdateUpperBound_SDDP()
            FirstStageCuts, avgsubprobcosts = self.SDDPSolver.BackwardPass(returnfirststagecut=True)
            self.FirstStageCutAddedInLastSDDP = self.FirstStageCutAddedInLastSDDP + FirstStageCuts
            self.SDDPSolver.CurrentIteration = self.SDDPSolver.CurrentIteration + 1

            end = time.time()
            duration = end - self.Start
            iteration = iteration +1
            stop = self.CheckStopingSDDP() or duration > Constants.AlgorithmTimeLimit \
                   or (relaxacfvehicle and iteration >= 10) \
                   or (runwithbinary and iteration >= 100)

        if not relaxacfvehicle and not runwithbinary:
            if self.SDDPSolver.CurrentLowerBound < self.BestSolutionSafeUperBound:
                self.SDDPSolver.SDDPNrScenarioTest = 100
                self.SDDPSolver.ComputeUpperBound()
                self.SDDPSolver.IsIterationWithConvergenceTest = False


            self.SDDPSolver.ForwardStage[0].ACFEstablishmentValues = [[self.SDDPSolver.HeuristicACFEstablishmentValue[i]  
                                                                        for i in self.Instance.ACFPPointSet]
                                                                        for w in range(len(self.SDDPSolver.CurrentSetOfTrialScenarios))]
            self.SDDPSolver.ForwardStage[0].VehicleAssignmentValues = [[[self.SDDPSolver.HeuristicVehicleAssignmentValue[m][i]  
                                                                            for i in self.Instance.ACFPPointSet]
                                                                            for m in self.Instance.RescueVehicleSet]
                                                                            for w in range(len(self.SDDPSolver.CurrentSetOfTrialScenarios))]

        solution =  self.SDDPSolver.CreateSolutionAtFirstStage()
        solution.TotalCost = self.SDDPSolver.CurrentExpvalueUpperBound

        self.SDDPSolver.LastExpectedCostComputedOnAllScenario = self.SDDPSolver.CurrentExpvalueUpperBound
        solution.SDDPExpUB = self.SDDPSolver.CurrentExpvalueUpperBound

        return solution
    
    def CheckStopingSDDP(self):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- CheckStopingSDDP")

        convergencecriterion = Constants.Infinity
        c = Constants.Infinity
        if self.SDDPSolver.CurrentLowerBound > 0:
            convergencecriterion = float(self.SDDPSolver.CurrentUpperBound) / float(self.SDDPSolver.CurrentLowerBound) \
                                   - (1.96 * math.sqrt(float(self.SDDPSolver.VarianceForwardPass) \
                                                       / float(self.SDDPSolver.CurrentNrScenario)) \
                                      / float(self.SDDPSolver.CurrentLowerBound))

            c = (1.96 * math.sqrt(float(self.SDDPSolver.VarianceForwardPass) / float(self.SDDPSolver.CurrentNrScenario)) \
                 / float(self.SDDPSolver.CurrentLowerBound))

        delta = Constants.Infinity
        if self.SDDPSolver.CurrentLowerBound > 0:
            delta = 3.92 * math.sqrt(float(self.SDDPSolver.VarianceForwardPass) / float(self.SDDPSolver.CurrentNrScenario)) \
                    / float(self.SDDPSolver.CurrentLowerBound)

        self.SDDPSolver.WriteInTraceFile("Iteration SDDP for ML Descent LB: % r, (exp UB: % r - safe ub: %r), variance: %r, convergencecriterion: %r, delta: %r, NrforwardSampleSize: %r, NrIterWithoutImprovment: %r  \n" % (
        self.SDDPSolver.CurrentLowerBound, self.SDDPSolver.CurrentExpvalueUpperBound, self.SDDPSolver.CurrentSafeUpperBound, self.SDDPSolver.VarianceForwardPass, convergencecriterion, delta, self.SDDPSolver.CurrentForwardSampleSize, self.SDDPSolver.NrIterationWithoutLBImprovment))

        return self.SDDPSolver.NrIterationWithoutLBImprovment >= Constants.LimitNrIterWithoutImprovmentMLLocalSearch or (self.SDDPSolver.CurrentLowerBound >= self.BestSolutionSafeUperBound and self.SDDPSolver.NrIterationWithoutLBImprovment > 2)
      
    def GetHeuristicACFEstablishmentAndVehicleAssignment(self):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- GetHeuristicACFEstablishmentAndVehicleAssignment")

        if self.Instance.NrTimeBucket == 2:
            Constants.NrScenarioinHeuristicTwoStageModel = 6
        elif self.Instance.NrTimeBucket == 3:
            Constants.NrScenarioinHeuristicTwoStageModel = 3
        elif self.Instance.NrTimeBucket == 4:
            Constants.NrScenarioinHeuristicTwoStageModel = 2
        elif self.Instance.NrTimeBucket >= 5:
            Constants.NrScenarioinHeuristicTwoStageModel = 2

        treestructure = [Constants.NrScenarioinHeuristicTwoStageModel ** self.Instance.NrTimeBucket] + [1] * (self.Instance.NrTimeBucket - 1) #""Constants.NrScenarioinHeuristicTwoStageModel"" is chosen randomly (It is for the starting solution to be used in the Heuristic approach)
        self.TestIdentifier.Model = Constants.Two_Stage
        chosengeneration = self.TestIdentifier.ScenarioSampling
        self.ScenarioGeneration = "RQMC"
        solution, mipsolver = self.Solver.CRP(treestructure, False, recordsolveinfo=True)

        GivenACFEstablishment = [solution.ACFEstablishment_x_wi[0][i] 
                            for i in self.Instance.ACFPPointSet]
        
        GivenVehicleAssignment = [[solution.VehicleAssignment_thetavar_wmi[0][m][i] 
                            for i in self.Instance.ACFPPointSet] 
                            for m in self.Instance.RescueVehicleSet]
        
        self.ScenarioGeneration = chosengeneration
        self.TestIdentifier.Model = Constants.ModelMulti_Stage
        self.TestIdentifier.Method = Constants.MLLocalSearch
        
        return GivenACFEstablishment, GivenVehicleAssignment
    
    def WriteInTraceFile(self, string):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- WriteInTraceFile")

        if Constants.PrintSDDPTrace:
            self.TraceFile = open(self.TraceFileName, "a")
            self.TraceFile.write(string)
            self.TraceFile.close()
    
    def GetCurrentLowerBound(self, GivenACFEstablishment1D, GivenVehicleAssignment2D):
        if Constants.Debug: print("\n We are in 'MLLocalSearch' Class -- GetCurrentLowerBound")

        self.SDDPSolver.HeuristicACFEstablishmentValue = GivenACFEstablishment1D
        self.SDDPSolver.HeuristicVehicleAssignmentValue = GivenVehicleAssignment2D
        self.SDDPSolver.ForwardStage[0].ChangeACFEstablishmentToValueOfTwoStage()
        self.SDDPSolver.ForwardStage[0].ChangeVehicleAssignmentToValueOfTwoStage()
        self.SDDPSolver.ForwardStage[0].RunForwardPassMIP()

        self.SDDPSolver.ForwardStage[0].ComputePassCost()

        return self.SDDPSolver.ForwardStage[0].PassCostWithAproxCosttoGo
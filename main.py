import os
import platform
import argparse
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time
import logging
import threading

import gurobipy as gp
from gurobipy import *
import sys

import csv
import datetime

from Constants import Constants
from Solver import Solver
from Evaluator import Evaluator
from TestIdentificator import TestIdentificator
from EvaluatorIdentificator import EvaluatorIdentificator
from Instance import Instance
from DebugLPFile import DebugLPFile

#Contain the paramter of the test being run and the evaluation method
TestIdentifier = None
EvaluatorIdentifier = None

#Solve or Evaluate
Action = ""

#The solution to evaluate
EvaluateSolution = None

if platform.system() == "Linux":
    desired_path = "/home/pfarghad/Myschedulingmodel_2"
else:
    desired_path = r"C:\PhD\Thesis\Papers\2nd\Code\SDDP"

# desired_path = r"C:\PhD\Thesis\Papers\2nd\Code\SDDP"
# desired_path = "/home/pfarghad/Myschedulingmodel_2" 

# Change the current working directory to the desired path
os.chdir(desired_path)
  
def CreateRequiredDir():
    if Constants.Debug:
        print("\n We are in 'CreateRequiredDir' Function.")
    requireddir = [
        "./Test",
        "./GurobiLog",
        "./Test/Statistic",
        "./Test/Bounds",
        "./Test/SolveInfo",
        "./Solutions",
        "./Evaluations",
        "./Temp"
    ]
    for dir in requireddir:
        os.makedirs(dir, exist_ok=True)

# def CreateRequiredDir():
#     if Constants.Debug: print("\n We are in 'CreateRequiredDir' Function.")
#     requireddir = ["./Test","./GurobiLog", "./Test/Statistic", "./Test/Bounds", "./Test/SolveInfo", "./Solutions", "./Evaluations", "./Temp", ]
#     for dir in requireddir:
#         if not os.path.exists(dir):
#             os.makedirs(dir)

def parseArguments():
    if Constants.Debug: print("\n We are in 'parseArguments' Function.")

    # Create argument parser
    parser = argparse.ArgumentParser()

    #Positional mandatory arguments

    if platform.system() == "Linux":
        parser.add_argument("--Action", help="What do you want to do?", type=str, required=True, choices=["GenerateInstances", "Solve", "DebugLPFile"]) 
        parser.add_argument("--Instance", help="Name of the instance.", type=str, required=True) 
        parser.add_argument("--Model", help="Which Type of Model?", type=str, required=True, choices=["Average", "Two_Stage", "Multi_Stage", "HeuristicMulti_Stage"])
        parser.add_argument("--NrScenario", help="The number of scenarios used for optimization (all10 ...)", type=str, required=True)
        parser.add_argument("--ScenarioGeneration", help="Which Type of Sampling?", type=str, required=True, choices=["MC", "QMC", "RQMC"])
        parser.add_argument("-m", "--method", help="Method used to solve?", type=str, required=True, choices=["MIP", "NBD", "SDDP", "PH", "Hybrid", "MLLocalSearch"])
        parser.add_argument("-c", "--mipsetting", help="Enhancements?", required=True, choices=["JustStrongCut", "JustLBF", "JustWarmUp", "JustMultiCut", "NoEnhancements", "NoStrongCut", "NoLBF", "NoWarmUp", "NoMultiCut", "AllEnhancements"])
        parser.add_argument("-seq", "--sequencetype", help="Which RQMC Method?", type=str, required=True, choices=["Halton", "LHS"])
        parser.add_argument("-LBF", "--lbfpercentage", help="Percentage of Scenarios to be used for LBF", type=int, required=True)
        parser.add_argument("-Cluster", "--ClusteringMethod", help="The method used for Clustering Scenarios?", type=str, required=True, choices=["NoReduction", "KMeans", "SOM", "Hierarchical", "Hierarchical_Diverse"]) 
        parser.add_argument("-InitNumScenCoeff", "--InitNumScenCoeff", help="Initial Number of Scenarios to be reduced", type=int, required=True)

    else:
        parser.add_argument("--Action", help="What do you want to do?", type=str, default="Solve", choices=["GenerateInstances", "Solve", "DebugLPFile"]) 
        parser.add_argument("--Instance", help="Name of the instance.", type=str, default="2_5_5_5_3_4_1_CRP") 
        parser.add_argument("--Model", help="Which Type of Model?", type=str, default="Multi_Stage", choices=["Average", "Two_Stage", "Multi_Stage", "HeuristicMulti_Stage"])
        parser.add_argument("--NrScenario", help="The number of scenarios used for optimization (all10 ...)", type=str, default="all5")
        parser.add_argument("--ScenarioGeneration", help="Which Type of Sampling?", type=str, default="RQMC", choices=["MC", "QMC", "RQMC"])
        parser.add_argument("-m", "--method", help="Method used to solve?", type=str, default="SDDP", choices=["MIP", "NBD", "SDDP", "PH", "Hybrid", "MLLocalSearch"])
        parser.add_argument("-c", "--mipsetting", help="Enhancements?", default="AllEnhancements", choices=["JustStrongCut", "JustLBF", "JustWarmUp", "JustMultiCut", "NoEnhancements", "NoStrongCut", "NoLBF", "NoWarmUp", "NoMultiCut", "AllEnhancements"])
        parser.add_argument("-seq", "--sequencetype", help="Which RQMC Method?", type=str, default="Halton", choices=["Halton", "LHS"])
        parser.add_argument("-LBF", "--lbfpercentage", help="Percentage of Scenarios to be used for LBF", type=int, default=100)
        parser.add_argument("-Cluster", "--ClusteringMethod", help="The method used for Clustering Scenarios?", type=str, default="KMeansPP", choices=["NoReduction", "KMeans", "KMeansPP", "SOM", "Hierarchical", "Hierarchical_Diverse"]) 
        parser.add_argument("-InitNumScenCoeff", "--InitNumScenCoeff", help="Initial Number of Scenarios to be reduced", type=int, default=10)


    # Optional arguments
    parser.add_argument("-s", "--ScenarioSeed", help="The seed used for scenario generation", type=int, default = -1)
    parser.add_argument("-p", "--policy", help="NearestNeighbor", type=str, default="_")
    parser.add_argument("-n", "--nrevaluation", help="nr scenario used for evaluation.", type=int, default = 2500)
    parser.add_argument("-f", "--fixuntil", help="Use with VSS action, how many periods are fixed", type=int, default = 0)
    parser.add_argument("-e", "--evpi", help="if true the evpi model is consdiered",  default=False, action = 'store_true')
    parser.add_argument("-t", "--timehorizon", help="the time horizon used in shiting window.", type=int, default = 1)
    parser.add_argument("-a", "--allscenario", help="generate all possible scenario.", type=int, default = 0)
    parser.add_argument("-w", "--nrforward", help="number of scenario in the forward pass of sddp.", type=int, default = 1)
    parser.add_argument("-d", "--sddpsetting", help="test a specific sddp parameter", default = "JustYFix")
    parser.add_argument("-y", "--hybridphsetting", help="test a specific hybridph parameter: Multiplier1, Multiplier10, Multiplier100, ...", default = "")                     # Here, you can set the "Rho_PH_PenaltyParameter" in the Hybrid (PHA + SDDP) algorithm!
    parser.add_argument("-z", "--mllocalsearchsetting", help="test a specific mllocalsearch parameter", default = "") 
    
    # Print version
    parser.add_argument("--version", action="version", version='%(prog)s - Version 1.0')


    # Parse arguments
    args = parser.parse_args()

    global TestIdentifier
    global EvaluatorIdentifier
    global Action
    Action = args.Action
    policygeneration = args.policy
    FixUntilTime = args.fixuntil
    if args.evpi:
        policygeneration ="EVPI"

    if Constants.Debug: print("------------Moving from 'main.py' Class ('parseArguments' Function) to 'TestIdentificator' class Constructor---------------")
    TestIdentifier = TestIdentificator(args.Instance,
                                       args.Model,
                                       args.method,
                                       args.ScenarioGeneration,
                                       args.NrScenario,
                                       Constants.SeedArray[args.ScenarioSeed],
                                       args.evpi,
                                       args.nrforward,
                                       args.mipsetting,
                                       args.sddpsetting,
                                       args.hybridphsetting,
                                       args.mllocalsearchsetting,
                                       args.sequencetype,
                                       args.lbfpercentage,
                                       args.ClusteringMethod,
                                       args.InitNumScenCoeff)
    
    if Constants.Debug: print("------------Moving BACK from 'TestIdentificator' class Constructor to 'main.py' Class ('parseArguments' Function)---------------")

    #TestIdentifier.Print_Attributes()

    if Constants.Debug: print("------------Moving from 'main.py' Class ('parseArguments' Function) to 'EvaluatorIdentificator' class Constructor---------------")
    EvaluatorIdentifier = EvaluatorIdentificator(policygeneration,  args.nrevaluation, args.timehorizon, args.allscenario)
    if Constants.Debug: print("------------Moving BACK from 'EvaluatorIdentificator' class Constructor to 'main.py' Class ('parseArguments' Function)---------------")
    EvaluatorIdentifier.Print_Attributes()

    # Check for incompatible options
    if args.Model == "Two_Stage" and not (args.method == "MIP"):
        print("Error: 'Two_Stage' model cannot be used with The type of Method you selected!")
        sys.exit(1)  # Exit the program with an error status
    
    if (args.ScenarioGeneration == "QMC" or args.ScenarioGeneration == "MC") and (args.Model == "Two_Stage"):
        print("Error: If you want to compare the 'Two_Stage' model with the 'Multi-Stage' model, They are generating the same scenarios only if the scenariogeneration method is RQMC!")
        sys.exit(1)  # Exit the program with an error status        
    
    if args.Model == "HeuristicMulti_Stage" and not (args.method == "SDDP"):
        print("Error: 'HeuristicMulti_Stage' model cannot be used with The type of Method you selected (It is only compatible with MIP and SDDP)!")
        sys.exit(1)  # Exit the program with an error status

    if args.Model == "Average" and not (args.method == "MIP"):
        print("Error: 'Average' model cannot be used with The type of Method you selected (It is only compatible with MIP) to findout the value of considering uncertainty in the model!")
        sys.exit(1)  # Exit the program with an error status
    
def GenerateInstances():
    if Constants.Debug: print("\nWe are in the 'GenerateInstances' function")

    for t in range(2, 5, 1):
        for i in range(5, 21, 5):
            for h in range(5, 6, 5):
                for l in range(5, 21, 5):
                    for m in range(3, 4, 1):
                        for c in range (4, 5, 4):
                            for InstanceNumber in range (1, 6, 1):
                                if c not in (4, 8):
                                    raise ValueError("Invalid value for Blood GP. Blood group (c) should only be 4 or 8.")

                                nr_time_buckets = t  
                                nr_ACF_Points = i  
                                nr_Hospitals = h  
                                nr_Demand_Locations = l 
                                nr_Rescue_Vehilce_Mode = m 
                                nr_Blood_Groupes = c            #Only 4 or 8   
                                nr_Injury_Levels = 3            #Do Not Change
                                nr_Platelet_Ages = 5            #Do Not Change

                                instance_name = f"{nr_time_buckets}_{nr_ACF_Points}_{nr_Hospitals}_{nr_Demand_Locations}_{nr_Rescue_Vehilce_Mode}_{nr_Blood_Groupes}_{InstanceNumber}_CRP"
                                
                                instance = Instance(instance_name)
                                instance.NrTimeBucket = nr_time_buckets
                                instance.NrACFPPoints = nr_ACF_Points
                                instance.NrHospitals = nr_Hospitals
                                instance.NrDemandLocations = nr_Demand_Locations
                                instance.NrFacilities = nr_Hospitals + nr_ACF_Points    #In facilities, We have Hospitals first, and then, ACFs ----->>> {HOSPITALs + ACFs}
                                instance.NrRescueVehicles = nr_Rescue_Vehilce_Mode
                                instance.NRBloodGPs = nr_Blood_Groupes
                                instance.NRInjuryLevels = nr_Injury_Levels
                                instance.NRPlateletAges = nr_Platelet_Ages

                                RandomSeed_InstanceGeneration = Constants.SeedArray[0] + InstanceNumber

                                instance.ComputeIndices()  
                                instance.Generate_Data(RandomSeed_InstanceGeneration)
                                #instance.SaveInstanceToTXTFileWithExplaination()  
                                instance.SaveInstanceToPickle()  
                                if Constants.Debug: instance.Print_Attributes()

def Solve(instance):

    global LastFoundSolution
    
    Constants.Evaluation_Part = False
    if Constants.Debug: print("------------Moving from 'main.py' Class ('Solve' Function) to 'Solver' class (Constructor)---------------")
    solver = Solver(instance, TestIdentifier, mipsetting="", evaluatesol=EvaluateSolution)
    if Constants.Debug: print("------------Moving BACK from 'Solver' class Constructor to 'main.py' Class ('Solve' Function)---------------")
    
    if Constants.Debug: print("------------Moving from 'main.py' Class ('Solve' Function) to 'Solver' class ('Solve' Function)---------------")    
    solution = solver.Solve()
    if Constants.Debug: print("------------Moving BACK from 'Solver' class ('Solve' Function) to 'main.py' Class ('Solve' Function)---------------")    
    
    LastFoundSolution = solution

    Constants.Evaluation_Part = True
    Constants.IntegerRecourse = False
    if Constants.Debug: print("------------Moving from 'main.py' Class ('Solve' Function) to 'Evaluator' class (Constructor)---------------")    
    evaluator = Evaluator(instance, TestIdentifier, EvaluatorIdentifier, solver)
    if Constants.Debug: print("------------Moving BACK from 'Evaluator' class Constructor to 'main.py' Class ('Solve' Function)---------------")

    if Constants.Debug: print("------------Moving from 'main.py' Class ('Solve' Function) to 'Evaluator' class (RunEvaluation)---------------") 
    evaluator.RunEvaluation()
    if Constants.Debug: print("------------Moving BACK from 'Evaluator' class 'RunEvaluation' to 'main.py' Class ('Solve' Function)---------------")

    if Constants.LauchEvalAfterSolve and EvaluatorIdentifier.NrEvaluation>0:
        if Constants.Debug: print("------------Moving from 'main.py' Class ('Solve' Function) to 'Evaluator' class (GatherEvaluation)---------------") 
        evaluator.GatherEvaluation()
        if Constants.Debug: print("------------Moving BACK from 'Evaluator' class 'GatherEvaluation' to 'main.py' Class ('Solve' Function)---------------")

def Evaluate():
   
    if Constants.Debug: print("------------Moving from 'main.py' Class ('Evaluate' Function) to 'Solver' class (Constructor)---------------")
    solver = Solver(instance, TestIdentifier, mipsetting="", evaluatesol=EvaluateSolution)
    if Constants.Debug: print("------------Moving BACK from 'Solver' class Constructor to 'main.py' Class ('Evaluate' Function)---------------")

    if Constants.Debug: print("------------Moving from 'main.py' Class ('Evaluate' Function) to 'Solver' class (Evaluator)---------------")
    evaluator = Evaluator(instance, TestIdentifier, EvaluatorIdentifier, solver)
    if Constants.Debug: print("------------Moving BACK from 'Evaluator' class Constructor to 'main.py' Class ('Evaluate' Function)---------------")

    evaluator.RunEvaluation()
    evaluator.GatherEvaluation()

def DebugLPFileAction(instance_name):
    lp_file_path = os.path.join(desired_path, "Temp", f"{instance_name}.lp")
    debugger = DebugLPFile(lp_file_path)
    debugger.solve_lp_file()

if __name__ == '__main__':

    if Constants.Debug: print("\n We are in the beginning of the program\n")

    print("------- The current working directory: \n", os.getcwd())
  
    try:
        CreateRequiredDir()

        parseArguments()

        #For experimentation purpose, we remove some of the enhancement to SDDP depending on the value of the parameter "MIPSetting"
        
        if TestIdentifier.MIPSetting == "JustStrongCut":
            Constants.GenerateStrongCut = True
            Constants.SDDPUseEVPI = False
            Constants.WarmUp_SDDP = False
            Constants.SDDPUseMultiCut = False
        if TestIdentifier.MIPSetting == "JustLBF":
            Constants.GenerateStrongCut = False
            Constants.SDDPUseEVPI = True
            Constants.WarmUp_SDDP = False
            Constants.SDDPUseMultiCut = False
        if TestIdentifier.MIPSetting == "JustWarmUp":
            Constants.GenerateStrongCut = False
            Constants.SDDPUseEVPI = False
            Constants.WarmUp_SDDP = True
            Constants.SDDPUseMultiCut = False
        if TestIdentifier.MIPSetting == "JustMultiCut":
            Constants.GenerateStrongCut = False
            Constants.SDDPUseEVPI = False
            Constants.WarmUp_SDDP = False
            Constants.SDDPUseMultiCut = True
        if TestIdentifier.MIPSetting == "NoEnhancements":
            Constants.GenerateStrongCut = False
            Constants.SDDPUseEVPI = False
            Constants.WarmUp_SDDP = False
            Constants.SDDPUseMultiCut = False
        if TestIdentifier.MIPSetting == "NoStrongCut":
            Constants.GenerateStrongCut = False
            Constants.SDDPUseEVPI = True
            Constants.WarmUp_SDDP = True
            Constants.SDDPUseMultiCut = True
        if TestIdentifier.MIPSetting == "NoLBF":
            Constants.GenerateStrongCut = True
            Constants.SDDPUseEVPI = False
            Constants.WarmUp_SDDP = True
            Constants.SDDPUseMultiCut = True            
        if TestIdentifier.MIPSetting == "NoWarmUp":
            Constants.GenerateStrongCut = True
            Constants.SDDPUseEVPI = True
            Constants.WarmUp_SDDP = False
            Constants.SDDPUseMultiCut = True
        if TestIdentifier.MIPSetting == "NoMultiCut":
            Constants.GenerateStrongCut = True
            Constants.SDDPUseEVPI = True
            Constants.WarmUp_SDDP = True
            Constants.SDDPUseMultiCut = False
        if TestIdentifier.MIPSetting == "AllEnhancements":
            Constants.GenerateStrongCut = True
            Constants.SDDPUseEVPI = True
            Constants.WarmUp_SDDP = True
            Constants.SDDPUseMultiCut = True
        
        if TestIdentifier.SequenceType == "Halton":
            Constants.SequenceTypee = "Halton"
        if TestIdentifier.SequenceType == "LHS":
            Constants.SequenceTypee = "LHS"

        Constants.LBFPercentage = TestIdentifier.LBFPercentage
        Constants.ScenarioReduction = TestIdentifier.ClusteringMethod
        Constants.Coeeff_Init_Scen_bef_reduction = TestIdentifier.InitNumScenCoeff

        if Constants.Debug: print("------------Moving from 'main.py' Class ('__name__ == '__main__'' Function) to 'Instance' class Constructor---------------")
        instance = Instance(TestIdentifier.InstanceName)
        if Constants.Debug: print("------------Moving BACK from 'Instance' class Constructor to 'main.py' Class ('__name__ == '__main__'' Function)---------------")
        
        if (Action != "GenerateInstances") and (Action != "DebugLPFile"):
            instance.LoadInstanceFromPickle(TestIdentifier.InstanceName)        
    
    except KeyError:
        print(KeyError.message)
        print("This instance does not exist.")

    if Action == Constants.Solve:
        if Constants.Debug: print("\n We are in main.py -- 'Action == Constants.Solve")

        if TestIdentifier.Model == "HeuristicMulti_Stage":
            Constants.UsingRelaxedMIPGapforTwoStageHeuristic = True
        else:
            Constants.UsingRelaxedMIPGapforTwoStageHeuristic = False
            
        Solve(instance)

    if Action == Constants.Evaluate:
        Evaluate()

    if Action == "GenerateInstances":
        GenerateInstances()

    if Action == "DebugLPFile":
        DebugLPFileAction(TestIdentifier.InstanceName)   

    print("****************************** WE ARE DONE *************************************")  
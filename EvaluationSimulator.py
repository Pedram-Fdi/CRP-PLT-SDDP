#This class provide a framework to evaluate the performance of the method through a simulation
#over a large number of scenarios.

from __future__ import absolute_import, division, print_function
import pandas as pd
#from matplotlib import pyplot as PLT
from MIPSolver import MIPSolver
from ScenarioTree import ScenarioTree
from Constants import Constants
#from DecentralizedMRP import DecentralizedMRP
from ProgressiveHedging import ProgressiveHedging
#from RollingHorizonSolver import RollingHorizonSolver
import time
import math
from datetime import datetime
import csv
from scipy import stats
import numpy as np
import copy
import itertools
#from MRPSolution import MRPSolution
#from decimal import Decimal, ROUND_HALF_DOWN
import pickle
#import RollingHorizonSolver
#from matplotlib import pyplot as PLT

class EvaluationSimulator(object):

    #Constructor
    def __init__(self, instance, solutions=[], sddps=[], testidentificator = [], evaluatoridentificator =[], treestructure=[], model="YQFix"):
        
        if Constants.Debug: print("\n We are in 'EvaluationSimulator' Class -- Constructor")
        self.Instance = instance
        if Constants.Debug: print(f"Instance set to: {instance}")

        self.Solutions = solutions
        self.SDDPs = sddps
        if Constants.Debug: print(f"Solutions provided: {len(solutions)}, SDDPs provided: {len(sddps)}")


        self.TestIdentificator = testidentificator
        self.EvalatorIdentificator = evaluatoridentificator
        if Constants.Debug: print(f"TestIdentificator: {testidentificator}, EvalatorIdentificator: {evaluatoridentificator}")


        self.NrSolutions = max(len(self.Solutions), len(self.SDDPs))
        if Constants.Debug: print(f"NrSolutions determined: {self.NrSolutions}")

        self.Policy = evaluatoridentificator.PolicyGeneration
        self.StartSeedResolve = Constants.SeedArray[0]
        if Constants.Debug: print(f"Policy: {self.Policy}, StartSeedResolve: {self.StartSeedResolve}")

        self.ScenarioGenerationResolvePolicy = self.TestIdentificator.ScenarioSampling
        self.EVPI = testidentificator.EVPI
        if Constants.Debug: print(f"ScenarioGenerationResolvePolicy: {self.ScenarioGenerationResolvePolicy}, EVPI: {self.EVPI}")

        if self.EVPI:
            self.EVPISeed = Constants.SeedArray[0]
            if Constants.Debug: print(f"EVPISeed: {self.EVPISeed}")

        self.MIPResolveTime = [None for t in instance.TimeBucketSet]
        self.IsDefineMIPResolveTime = [False for t in instance.TimeBucketSet]
        self.PHResolveTime = [None for t in instance.TimeBucketSet]
        self.IsDefinePHResolve = [False for t in instance.TimeBucketSet]
        if Constants.Debug: print("Initialized MIP and PH solve time lists")

        self.ReferenceTreeStructure = treestructure
        self.EvaluateAverage = Constants.IsDeterministic(self.TestIdentificator.Model)
        self.Model = model
        if Constants.Debug: print(f"ReferenceTreeStructure: {treestructure}, EvaluateAverage: {self.EvaluateAverage}, Model: {model}")

        self.YeuristicMulti_Stage = self.TestIdentificator.Model == Constants.ModelHeuristicMulti_Stage
        if Constants.Debug: print(f"YeuristicMulti_Stage: {self.YeuristicMulti_Stage}")

        if self.Policy == Constants.RollingHorizon:
            if Constants.Debug: print("Initializing RollingHorizonSolver...")
            self.RollingHorizonSolver = RollingHorizonSolver(self.Instance,  model , self.ReferenceTreeStructure,
                                                             self.StartSeedResolve, self.ScenarioGenerationResolvePolicy,
                                                             self.EvaluatorIdentificator.TimeHorizon, self.UseSafetyStock, self)

        #self.DecentralizedMRP = DecentralizedMRP(self.Instance, Constants.IsRuleWithGrave(self.Model))
            
    #This function evaluate the performance of a set of solutions obtain with the same method (different solutions due to randomness in the method)
    def EvaluateYQFixSolution(self, saveevaluatetab=False, filename="", evpi=False):
        if Constants.Debug: print("\n We are in 'EvaluationSimulator' Class -- EvaluateYQFixSolution")

        # Compute the average value of the demand
        nrscenario = self.EvalatorIdentificator.NrEvaluation
        allscenario = self.EvalatorIdentificator.AllScenario
        start_time = time.time()
        
        if Constants.Debug: print(f"Number of scenarios: {nrscenario}, All scenarios: {allscenario}")

        Evaluated = [-1 for e in range(nrscenario)]
        Probabilities = [-1 for e in range(nrscenario)]
        if Constants.Debug: print("Initialized Evaluated and Probabilities lists.")

        OutOfSampleSolution = None
        mipsolver = None
        firstsolution = True
        nrerror = 0

        for n in range(self.NrSolutions):
                if Constants.Debug: print(f"Evaluating solution {n+1} / {self.NrSolutions}")

                sol = None

                if not evpi and not self.Policy == Constants.RollingHorizon:
                   sol = self.Solutions[n]
                   if Constants.Debug: print(f"Using direct solution for scenario {n+1}")

                if Constants.IsSDDPBased(self.TestIdentificator.Method) or Constants.IsNBDBased(self.TestIdentificator.Method):
                    sddp = self.SDDPs[n]
                    if Constants.Debug: print(f"Using SDDP based method for scenario {n+1}")

                evaluatoinscenarios, scenariotrees = self.GetScenarioSet(Constants.EvaluationScenarioSeed, nrscenario, allscenario)
                                
                if Constants.IsSDDPBased(self.TestIdentificator.Method) or Constants.IsNBDBased(self.TestIdentificator.Method): #== Constants.SDDP:
                     self.ForwardPassOnScenarios(sddp, evaluatoinscenarios, sol)

                firstscenario = True
                self.IsDefineMIPResolveTime = [False for t in self.Instance.TimeBucketSet]
                self.IsDefinePHResolve = [False for t in self.Instance.TimeBucketSet]

                average = 0
                totalproba = 0
                for indexscenario in range(nrscenario):

                    scenario = evaluatoinscenarios[indexscenario]
                    scenariotree = scenariotrees[indexscenario]

                    if not evpi:
                        if self.TestIdentificator.Method == Constants.MIP or self.TestIdentificator.Method == Constants.ProgressiveHedging:
                            givenacfestablishments, givenvehicleassinments, \
                                givenapheresisassignments, giventransshipmentHIs, giventransshipmentIIs, giventransshipmentHHs = self.GetDecisionFromSolutionForScenario(sol, scenario)

                        if Constants.IsSDDPBased(self.TestIdentificator.Method) or Constants.IsNBDBased(self.TestIdentificator.Method):
                            givenacfestablishments, givenvehicleassinments, \
                                givenapheresisassignments, giventransshipmentHIs, giventransshipmentIIs, giventransshipmentHHs = self.GetDecisionFromSDDPForScenario(sddp, indexscenario)

                            # Solve the MIP and fix the decision to the one given.
                        
                        if Constants.Debug:
                            for t in self.Instance.TimeBucketSet:
                                    if Constants.Debug: print(f"ACF Establishments: %r" % givenacfestablishments)
                                    if Constants.Debug: print(f"Vehicle Assinments: %r" % givenvehicleassinments)

                                    if Constants.Debug: print(f"Apheresis Assignment[t={t}]: %r" % givenapheresisassignments[t])
                                    if Constants.Debug: print(f"Transshipment HI[t={t}]: %r" % giventransshipmentHIs[t])
                                    if Constants.Debug: print(f"Transshipment II[t={t}]: %r" % giventransshipmentIIs[t])
                                    if Constants.Debug: print(f"Transshipment HH[t={t}]: %r" % giventransshipmentHHs[t])

                                    if Constants.Debug: print(f"Demand[t={t}]: %r" % scenario.Demands[t])
                                    if Constants.Debug: print(f"HospitalCaps[t={t}]: %r" % scenario.HospitalCaps[t])
                                    if Constants.Debug: print(f"WholeDonors[t={t}]: %r" % scenario.WholeDonors[t])
                                    if Constants.Debug: print(f"ApheresisDonors[t={t}]: %r" % scenario.ApheresisDonors[t])
                    else:
                        givenfixedtrans = []
                        givenvartrans = []

                    if firstscenario:
                        #Defin the MIP
                        if not evpi:
                            mipsolver = MIPSolver(instance=self.Instance, 
                                                  model=Constants.Two_Stage, 
                                                  scenariotree=scenariotree,
                                                  evpi=False,
                                                  implicitnonanticipativity=False,
                                                  evaluatesolution=True,
                                                  givenapheresisassignment=givenapheresisassignments,
                                                  giventransshipmentHI=giventransshipmentHIs,
                                                  giventransshipmentII=giventransshipmentIIs,
                                                  giventransshipmentHH=giventransshipmentHHs,
                                                  givenacfestablishment=givenacfestablishments,
                                                  givenvehicleassinment=givenvehicleassinments,
                                                  fixsolutionuntil=self.Instance.NrTimeBucket)                
                        else:
                            mipsolver = MIPSolver(self.Instance, self.Model, scenariotree,
                                                  evpi=True)
                        mipsolver.BuildModel()
                    else:
                        #update the MIP
                        mipsolver.ModifyMipForScenarioTree(scenariotree)
                        if not self.Policy == Constants.Fix and not evpi:
                            mipsolver.ModifyMipForFixApheresisAssignment(givenapheresisassignments)
                            # mipsolver.ModifyMipForFixTransshipmentHI(giventransshipmentHIs)
                            # mipsolver.ModifyMipForFixTransshipmentII(giventransshipmentIIs)
                            # mipsolver.ModifyMipForFixTransshipmentHH(giventransshipmentHHs)

                        if self.Policy == Constants.RollingHorizon:
                            mipsolver.ModifyMIPForSetup(givensetup)

                    mipsolver.CRPBIM.Params.Method = 2  # Use barrier method for linear programming
                    mipsolver.CRPBIM.Params.FeasibilityTol = 0.01  # Set feasibility tolerance

                    solution = mipsolver.Solve()  # Assuming Solve() method is appropriately defined for Gurobi

                    #GRB should always find a solution due to complete recourse
                    if solution is None:
                        if Constants.Debug:
                            mipsolver.CRPBIM.write("CRPBIM_Evaluation.lp")  # Save the model to an LP file
                            # Raising an error with a custom message
                            raise NameError(f"Error at seed {indexscenario} with given quantity {givenvartrans}")
                            nrerror += 1
                    else:
                        if Constants.Debug: print(f"Solution found: Total Cost = {solution.TotalCost}")
                        Evaluated[indexscenario] = solution.TotalCost

                        if allscenario == 0:
                            scenario.Probability = 1.0 / float(nrscenario)
                            if Constants.Debug: print(f"Set scenario probability: {scenario.Probability}")
                        Probabilities[indexscenario] = scenario.Probability
                        average += solution.TotalCost * scenario.Probability
                        if Constants.Debug: print(f"Updated average: {average}")
                        totalproba += scenario.Probability
                        if Constants.Debug: print(f"Updated total probability: {totalproba}")
                        
                        #Record the obtain solution in an MRPsolution  OutOfSampleSolution
                        if firstsolution:
                            if firstscenario:
                                if Constants.Debug: print("Recording first solution.")
                                OutOfSampleSolution = solution
                            else:
                                if Constants.Debug: print("Merging solution.")
                                OutOfSampleSolution.Merge(solution)

                        firstscenario = False

                    if firstsolution:
                        if Constants.Debug: print(f"Adjusting probabilities for {len(OutOfSampleSolution.Scenarioset)} scenarios.")
                        for s in OutOfSampleSolution.Scenarioset:
                            s.Probability = 1.0 / len(OutOfSampleSolution.Scenarioset)
                            if Constants.Debug: print(f"Scenario {s} probability adjusted to {s.Probability}")


        OutOfSampleSolution.ComputeStatistics()

        duration = time.time() - start_time

        if Constants.Debug: print("Duration of evaluation (sec): %r, \nOutofSample cost:%r \ntotal proba:%r" % (duration, average, totalproba)) # %r"%( duration, Evaluated )
        
        self.EvaluationDuration = duration

        KPIStat = OutOfSampleSolution.PrintStatistics(self.TestIdentificator, "OutOfSample", indexscenario, nrscenario, duration, False, self.Policy )

        #Save the evaluation result in a file (This is used when the evaluation is parallelized)
        if saveevaluatetab:
                with open(filename+"_Evaluator.txt", "wb") as fp:
                    pickle.dump(Evaluated, fp)

                with open(filename + "_Probabilities.txt", "wb") as fp:
                    
                    pickle.dump(Probabilities, fp)

                with open(filename+"_KPIStat.txt", "wb") as fp:
                    pickle.dump(KPIStat, fp)

        if Constants.PrintDetailsExcelFiles:
            namea = self.TestIdentificator.GetAsString()
            nameb = self.EvalatorIdentificator.GetAsString()
            OutOfSampleSolution.PrintToExcel(namea + nameb)

    #This function return the FixedTrans decision and VarTrans decisions for the scenario given in argument
    def GetDecisionFromSolutionForScenario(self, sol,  scenario):
        if Constants.Debug: print("\n We are in 'EvaluationSimulator' Class -- GetDecisionFromSolutionForScenario")

        givenacfestablishments = [0 for i in self.Instance.ACFPPointSet]
        
        givenvehicleassinments = [[0 for i in self.Instance.ACFPPointSet] 
                                    for m in self.Instance.RescueVehicleSet]
        
        givenapheresisassignments = [[0 for i in self.Instance.ACFPPointSet] 
                                        for t in self.Instance.TimeBucketSet]
        
        giventransshipmentHIs = [[[[[0 for i in self.Instance.ACFPPointSet] 
                                        for h in self.Instance.HospitalSet] 
                                        for r in self.Instance.PlateletAgeSet] 
                                        for c in self.Instance.BloodGPSet] 
                                        for t in self.Instance.TimeBucketSet]
        
        giventransshipmentIIs = [[[[[0 for iprime in self.Instance.ACFPPointSet] 
                                        for i in self.Instance.ACFPPointSet] 
                                        for r in self.Instance.PlateletAgeSet] 
                                        for c in self.Instance.BloodGPSet] 
                                        for t in self.Instance.TimeBucketSet]
        
        giventransshipmentHHs = [[[[[0 for hprime in self.Instance.HospitalSet] 
                                        for h in self.Instance.HospitalSet] 
                                        for r in self.Instance.PlateletAgeSet] 
                                        for c in self.Instance.BloodGPSet] 
                                        for t in self.Instance.TimeBucketSet]
        
        if self.Policy == Constants.RollingHorizon:
            givenfixedtrans, givenvartrans = self.RollingHorizonSolver.ApplyRollingHorizonSimulation( scenario )
        else:
            # The ACFEtablishment are fixed in the first stage
            givenacfestablishments = [(sol.ACFEstablishment_x_wi[0][i] ) 
                                        for i in self.Instance.ACFPPointSet]
            if Constants.Debug: print("givenacfestablishments: ", givenacfestablishments)
            
            # The VehicleAssinments are fixed in the first stage
            givenvehicleassinments = [[(sol.VehicleAssignment_thetavar_wmi[0][m][i] ) 
                                        for i in self.Instance.ACFPPointSet]
                                        for m in self.Instance.RescueVehicleSet]
            if Constants.Debug: print("givenvehicleassinments: ", givenvehicleassinments)

            # For model YQFix, the quatities are fixed, and can be taken from the solution
            if self.Policy == Constants.Fix:
                givenvartrans = [[[sol.VariableTransportation_x_wtsd[0][t][s][d]
                                    for d in self.Instance.DemandSet]
                                    for s in self.Instance.SupplierSet]
                                    for t in self.Instance.TimeBucketSet]
            # For model Multi_Stage, the quantities depend on the scenarion
            else:
                previousnode = sol.ScenarioTree.RootNode
                #At each time period the quantity to produce is decided based on the demand known up to now
                for ti in self.Instance.TimeBucketSet:
                    demanduptotimet = [[[[scenario.Demands[t][j][c][l] 
                                          for l in self.Instance.DemandSet] 
                                          for c in self.Instance.BloodGPSet] 
                                          for j in self.Instance.InjuryLevelSet] 
                                          for t in range(ti)]
                    if Constants.Debug: print("demanduptotimet: ", demanduptotimet)
                    hospitalCapsuptotimet = [[scenario.HospitalCaps[t][h] 
                                                for h in self.Instance.HospitalSet] 
                                                for t in range(ti)]
                    if Constants.Debug: print("hospitalCapsuptotimet: ", hospitalCapsuptotimet)
                    wholeDonorsuptotimet = [[[scenario.WholeDonors[t][c][h] 
                                                for h in self.Instance.HospitalSet] 
                                                for c in self.Instance.BloodGPSet] 
                                                for t in range(ti)]
                    if Constants.Debug: print("wholeDonorsuptotimet: ", wholeDonorsuptotimet)
                    apheresisDonorsuptotimet = [[[scenario.ApheresisDonors[t][c][u]
                                                    for u in self.Instance.FacilitySet] 
                                                    for c in self.Instance.BloodGPSet] 
                                                    for t in range(ti)]
                    if Constants.Debug: print("apheresisDonorsuptotimet: ", apheresisDonorsuptotimet)
                    if self.Policy == Constants.Resolve:
                            givenapheresisassignments[ti], giventransshipmentHIs[ti], \
                            giventransshipmentIIs[ti], giventransshipmentHHs[ti], \
                            error = self.GetApheresisTransshipmentVarByResolve(demanduptotimet, hospitalCapsuptotimet, wholeDonorsuptotimet, 
                                                                                apheresisDonorsuptotimet, ti, givenapheresisassignments, giventransshipmentHIs, 
                                                                                giventransshipmentIIs, giventransshipmentHHs, sol,
                                                                                givenacfestablishments, givenvehicleassinments)
                            #if Constants.Debug: print("givenapheresisassignments: ", givenapheresisassignments)
                            #if Constants.Debug: print("giventransshipmentHIs: ", giventransshipmentHIs)
                            #if Constants.Debug: print("giventransshipmentIIs: ", giventransshipmentIIs)
                            #if Constants.Debug: print("giventransshipmentHHs: ", giventransshipmentHHs)
                            
            
        return givenacfestablishments, givenvehicleassinments, givenapheresisassignments, giventransshipmentHIs, giventransshipmentIIs, giventransshipmentHHs

    #Recover the Apheresis and Transshipment related Values from the last MIP resolution
    def GetApheresisTransshipmentVarByResolve(self, demanduptotimet, hospitalCapsuptotimet, wholeDonorsuptotimet, apheresisDonorsuptotimet, \
                                              resolvetime, givenapheresisassignments, giventransshipmentHIs, giventransshipmentIIs, \
                                                giventransshipmentHHs, solution, givenacfestablishments, givenvehicleassinments):
        if Constants.Debug: print("\n We are in 'EvaluationSimulator' Class -- GetApheresisTransshipmentVarByResolve")  
        
        error = 0

        apheresisassignmentstofix = [[givenapheresisassignments[t][i] 
                                        for i in self.Instance.ACFPPointSet] 
                                        for t in range(resolvetime)]
        
        transshipmentHIstofix = [[[[[giventransshipmentHIs[t][c][r][h][i]
                                    for i in self.Instance.ACFPPointSet] 
                                    for h in self.Instance.HospitalSet] 
                                    for r in self.Instance.PlateletAgeSet] 
                                    for c in self.Instance.BloodGPSet] 
                                    for t in range(resolvetime)]
        
        transshipmentIIstofix = [[[[[giventransshipmentIIs[t][c][r][i][iprime]
                                    for iprime in self.Instance.ACFPPointSet] 
                                    for i in self.Instance.ACFPPointSet] 
                                    for r in self.Instance.PlateletAgeSet] 
                                    for c in self.Instance.BloodGPSet] 
                                    for t in range(resolvetime)]
        
        transshipmentHHstofix = [[[[[giventransshipmentHHs[t][c][r][h][hprime]
                                    for hprime in self.Instance.HospitalSet] 
                                    for h in self.Instance.HospitalSet] 
                                    for r in self.Instance.PlateletAgeSet] 
                                    for c in self.Instance.BloodGPSet] 
                                    for t in range(resolvetime)]
        
        if self.TestIdentificator.Method == Constants.MIP:
                resultapheresisassignments, resulttransshipmentHIs,  \
                resulttransshipmentIIs, resulttransshipmentHHs = self.ResolveMIP(demanduptotimet, hospitalCapsuptotimet, wholeDonorsuptotimet, apheresisDonorsuptotimet,
                                                                                resolvetime, apheresisassignmentstofix, transshipmentHIstofix, transshipmentIIstofix, transshipmentHHstofix, 
                                                                                givenacfestablishments, givenvehicleassinments, solution)
        
        if self.TestIdentificator.Method == Constants.ProgressiveHedging:
                resultapheresisassignments, resulttransshipmentHIs,  \
                resulttransshipmentIIs, resulttransshipmentHHs = self.GetDecisionFromPHForScenario(demanduptotimet, hospitalCapsuptotimet, wholeDonorsuptotimet, apheresisDonorsuptotimet, resolvetime, apheresisassignmentstofix, transshipmentHIstofix, transshipmentIIstofix, 
                                                                   transshipmentHHstofix, givenacfestablishments, givenvehicleassinments)

        return resultapheresisassignments, resulttransshipmentHIs, resulttransshipmentIIs, resulttransshipmentHHs, error

    # This function return the FixedTrans Var decisions and VariableVar Trans decisions for the scenario given in argument
    def GetDecisionFromPHForScenario(self, demanduptotimet, hospitalCapsuptotimet, wholeDonorsuptotimet, apheresisDonorsuptotimet, time, givenapheresisassignments, giventransshipmentHIs, giventransshipmentIIs, giventransshipmentHHs, givenacfestablishments, givenvehicleassinments):
        if Constants.Debug: print("\n We are in 'EvaluationSimulator' Class -- GetDecisionFromPHForScenario")  
        
        if not self.IsDefinePHResolve[time]:
            #Create the set of sub-instances.
            scenariotree, treestructure = self.GetScenarioTreeForResolve(time, demanduptotimet)
            self.PHResolveTime[time] = ProgressiveHedging(self.Instance, self.TestIdentificator, treestructure, scenariotree, 
                                                          givenacfestablishments=givenacfestablishments, givenvehicleassinments=givenvehicleassinments, fixuntil=time-1)

            for w in [0]:
                if Constants.Debug: print("givenapheresisassignments: ", givenapheresisassignments)
                if Constants.Debug: print("giventransshipmentHIs: ", giventransshipmentHIs)
                if Constants.Debug: print("giventransshipmentIIs: ", giventransshipmentIIs)
                if Constants.Debug: print("giventransshipmentHHs: ", giventransshipmentHHs)

                self.PHResolveTime[time].MIPSolvers[w].GivenApheresisAssignment = givenapheresisassignments
                self.PHResolveTime[time].MIPSolvers[w].GivenTransshipmentHI = giventransshipmentHIs
                self.PHResolveTime[time].MIPSolvers[w].GivenTransshipmentII = giventransshipmentIIs
                self.PHResolveTime[time].MIPSolvers[w].GivenTransshipmentHH = giventransshipmentHHs

                self.PHResolveTime[time].MIPSolvers[w].CreateCopyGivenApheresisAssignmentConstraints()
                self.PHResolveTime[time].MIPSolvers[w].CreateCopyGivenTransshipmentHIConstraints()
                self.PHResolveTime[time].MIPSolvers[w].CreateCopyGivenTransshipmentIIConstraints()
                self.PHResolveTime[time].MIPSolvers[w].CreateCopyGivenTransshipmentHHConstraints()

            self.IsDefinePHResolve[time] = True
        #Update the model for made decisions
        else:
            self.PHResolveTime[time].UpdateForDemand(demanduptotimet)
            self.PHResolveTime[time].UpdateForHospitalCap(hospitalCapsuptotimet)
            self.PHResolveTime[time].UpdateForWholeDonor(wholeDonorsuptotimet)
            self.PHResolveTime[time].UpdateForApheresisDonor(apheresisDonorsuptotimet)

            self.PHResolveTime[time].UpdateForApheresisAssignment(givenapheresisassignments)
            self.PHResolveTime[time].UpdateForTransshipmentHI(giventransshipmentHIs)
            self.PHResolveTime[time].UpdateForTransshipmentII(giventransshipmentIIs)
            self.PHResolveTime[time].UpdateForTransshipmentHH(giventransshipmentHHs)

        #Re-set the parameters
        self.PHResolveTime[time].ReSetParameter()

        #solve.
        solution = self.PHResolveTime[time].Run()

        #get the result.
        givenapheresisassignments = [solution.ApheresisAssignment_y_wti[0][time][i] 
                                        for i in self.Instance.ACFPPointSet]
        giventransshipmentHIs = [[[[solution.TransshipmentHI_b_wtcrhi[0][time][c][r][h][i] 
                                    for i in self.Instance.ACFPPointSet]
                                    for h in self.Instance.HospitalSet]
                                    for r in self.Instance.PlateletAgeSet]
                                    for c in self.Instance.BloodGPSet]
        giventransshipmentIIs = [[[[solution.TransshipmentII_bPrime_wtcrii[0][time][c][r][i][iprime] 
                                    for iprime in self.Instance.ACFPPointSet]
                                    for i in self.Instance.ACFPPointSet]
                                    for r in self.Instance.PlateletAgeSet]
                                    for c in self.Instance.BloodGPSet]
        giventransshipmentHHs = [[[[solution.TransshipmentHH_bDoublePrime_wtcrhh[0][time][c][r][h][hprime] 
                                    for hprime in self.Instance.HospitalSet]
                                    for h in self.Instance.HospitalSet]
                                    for r in self.Instance.PlateletAgeSet]
                                    for c in self.Instance.BloodGPSet]

        #print the result.
        return givenapheresisassignments, giventransshipmentHIs, giventransshipmentIIs, giventransshipmentHHs

    #This function generate the scenario tree for the next planning horizon
    def GetScenarioTreeForResolve(self, resolvetime, demanduptotimet):
        if Constants.Debug: print("\n We are in 'EvaluationSimulator' Class -- GetScenarioTreeForResolve")  

        
        if Constants.Debug: print("ReferenceTreeStructure: ", self.ReferenceTreeStructure)
        treestructure = []
        # Loop through each time bucket to build the middle part of the tree structure
        for t in range(self.Instance.NrTimeBucket):
            if t >= resolvetime and t <= (self.Instance.NrTimeBucket):
                tree_element = self.ReferenceTreeStructure[t - (resolvetime)]
            else:
                # Default tree structure element if conditions are not met
                tree_element = 1
            
            # Append the calculated element to the tree structure
            treestructure.append(tree_element)

        # Append 0 to the end of the tree structure list

        if Constants.Debug: print("treestructure: ", treestructure)
        
        
        if self.Model == Constants.Two_Stage:
            treestructure = [1] \
                            + [self.ReferenceTreeStructure[1]
                               if (t == resolvetime)
                               else 1
                               for t in range(self.Instance.NrTimeBucket)] \
                            + [0]

        if self.Model == Constants.Two_Stage and self.ScenarioGenerationResolvePolicy == Constants.All:
            nrstochasticperiod = self.Instance.NrTimeBucket - resolvetime
            treestructure = [1] \
                            + [int(math.pow(8, nrstochasticperiod))
                               if (t == resolvetime and (
                        t < (self.Instance.NrTimeBucket - self.Instance.NrTimeBucketWithoutUncertaintyAfter)))
                               else 1
                               for t in range(self.Instance.NrTimeBucket)] \
                            + [0]

        # self.StartSeedResolve = self.StartSeedResolve + 1
        scenariotree = ScenarioTree(self.Instance, treestructure, self.StartSeedResolve,
                                    averagescenariotree=self.EvaluateAverage,
                                    givenfirstperiod=demanduptotimet,
                                    scenariogenerationmethod=self.ScenarioGenerationResolvePolicy,
                                    model=self.Model)
        if Constants.Debug: print("scenariotree: ", scenariotree)
        return scenariotree, treestructure
                  
    #This method run a forward pass of the SDDP algorithm on the considered set of scenarios
    def ForwardPassOnScenarios(self, sddp, scenarios, solution):
        if Constants.Debug: print("\n We are in 'EvaluationSimulator' Class -- GetScenarioSet")

        sddp.EvaluationMode = True
        Constants.SDDPRunSigleTree = False


        sddp.HeuristicACFEstablishmentValue = [solution.ACFEstablishment_x_wi[0][i] 
                                                for i in self.Instance.ACFPPointSet]
        if Constants.Debug: print("HeuristicACFEstablishmentValue: ", sddp.HeuristicACFEstablishmentValue)
        
        sddp.HeuristicVehicleAssignmentValue = [[solution.VehicleAssignment_thetavar_wmi[0][m][i] 
                                                for i in self.Instance.ACFPPointSet] 
                                                for m in self.Instance.RescueVehicleSet]
        if Constants.Debug: print("HeuristicVehicleAssignmentValue: ", sddp.HeuristicVehicleAssignmentValue)

        # Make a forward pass on the
        #Create the SAA scenario, which are used to compute the EVPI scenario
        sddp.GenerateSAAScenarios2()

        # Get the set of scenarios
        sddp.CurrentSetOfTrialScenarios = scenarios
        sddp.ScenarioNrSet = len(scenarios)
        sddp.CurrentNrScenario = len(scenarios)
        sddp.TrialScenarioNrSet = range(len(sddp.CurrentSetOfTrialScenarios))
        if Constants.Debug: print(f"Scenarios set for trial: {list(sddp.TrialScenarioNrSet)}")
        
        sddp.GenerateStrongCut = False
        # Modify the number of scenario at each stage
        for stage in sddp.StagesSet:
            if Constants.Debug: print(f"Modifying settings for stage: {stage}")
            sddp.ForwardStage[stage].SetNrTrialScenario(len(scenarios))
            sddp.ForwardStage[stage].FixedScenarioPobability = [1]
            sddp.ForwardStage[stage].FixedScenarioSet = [0]
            sddp.BackwardStage[stage].SAAStageCostPerScenarioWithoutCostoGopertrial = [0 for w in sddp.TrialScenarioNrSet]
            if Constants.Debug: print(f"Stage {stage} modified with {len(scenarios)} scenarios.")

        if Constants.Debug: print("Copying decision of scenario 0 to all scenarios for ForwardStage[0].")    
        sddp.ForwardStage[0].CopyDecisionOfScenario0ToAllScenario()

        if Constants.Debug: print("Executing forward pass...")
        sddp.ForwardPass(ignorefirststage=False)

        sddp.ForwardStage[0].CopyDecisionOfScenario0ToAllScenario()
        
        if Constants.Debug:
            print("Computing cost and updating upper bound...")
            sddp.ComputeCost()
            if Constants.NestedBenders:
                sddp.UpdateUpperBound_NBD()
            else:
                sddp.UpdateUpperBound_SDDP()
            print("Run forward pass on all evaluation scenarios, cost: %r" %sddp.CurrentExpvalueUpperBound)

    # This function return the Fixed Trans Vars decisions and Variable Trans Vars to transfer for the scenario given in argument
    def GetDecisionFromSDDPForScenario(self, sddp, scenario):
        if Constants.Debug: print("\n We are in 'EvaluationSimulator' Class -- GetDecisionFromSDDPForScenario")
        #Get the setup quantitities associated with the solultion

        givenacfestablishments = [sddp.GetACFEstablishmentFixedEarlier(i, scenario) 
                                    for i in self.Instance.ACFPPointSet]
        if Constants.Debug: print("givenacfestablishments:\n ", givenacfestablishments)
        givenvehicleassinments = [[sddp.GetVehicleAssignmentFixedEarlier(m, i, scenario) 
                                    for i in self.Instance.ACFPPointSet] 
                                    for m in self.Instance.RescueVehicleSet]
        if Constants.Debug: print("givenvehicleassinments:\n ", givenvehicleassinments)

        givenapheresisassignments = [[0 for i in self.Instance.ACFPPointSet] 
                                        for t in self.Instance.TimeBucketSet]
        for stage in sddp.ForwardStage:
            for t in stage.RangePeriodApheresisAssignment:
                time = stage.GetTimePeriodAssociatedToApheresisAssignmentVariable(t)
                for i in self.Instance.ACFPPointSet:
                    givenapheresisassignments[time][i] = stage.ApheresisAssignmentValues[scenario][t][i]
        if Constants.Debug: print("givenapheresisassignments:\n ", givenapheresisassignments)

        giventransshipmentHIs = [[[[[0 for i in self.Instance.ACFPPointSet] 
                                    for h in self.Instance.HospitalSet] 
                                    for r in self.Instance.PlateletAgeSet] 
                                    for c in self.Instance.BloodGPSet] 
                                    for t in self.Instance.TimeBucketSet]
        for stage in sddp.ForwardStage:
            for t in stage.RangePeriodApheresisAssignment:
                time = stage.GetTimePeriodAssociatedToApheresisAssignmentVariable(t)
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            for i in self.Instance.ACFPPointSet:
                                giventransshipmentHIs[time][c][r][h][i] = stage.TransshipmentHIValues[scenario][t][c][r][h][i]
        if Constants.Debug: print("giventransshipmentHIs:\n ", giventransshipmentHIs)

        giventransshipmentIIs = [[[[[0 for iprime in self.Instance.ACFPPointSet] 
                                    for i in self.Instance.ACFPPointSet] 
                                    for r in self.Instance.PlateletAgeSet] 
                                    for c in self.Instance.BloodGPSet] 
                                    for t in self.Instance.TimeBucketSet]
        for stage in sddp.ForwardStage:
            for t in stage.RangePeriodApheresisAssignment:
                time = stage.GetTimePeriodAssociatedToApheresisAssignmentVariable(t)
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for i in self.Instance.ACFPPointSet:
                            for iprime in self.Instance.ACFPPointSet:
                                giventransshipmentIIs[time][c][r][i][iprime] = stage.TransshipmentIIValues[scenario][t][c][r][i][iprime]
        if Constants.Debug: print("giventransshipmentIIs:\n ", giventransshipmentIIs)

        giventransshipmentHHs = [[[[[0 for hprime in self.Instance.HospitalSet] 
                                    for h in self.Instance.HospitalSet] 
                                    for r in self.Instance.PlateletAgeSet] 
                                    for c in self.Instance.BloodGPSet] 
                                    for t in self.Instance.TimeBucketSet]
        for stage in sddp.ForwardStage:
            for t in stage.RangePeriodApheresisAssignment:
                time = stage.GetTimePeriodAssociatedToApheresisAssignmentVariable(t)
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            for hprime in self.Instance.HospitalSet:
                                giventransshipmentHHs[time][c][r][h][hprime] = stage.TransshipmentHHValues[scenario][t][c][r][h][hprime]
        if Constants.Debug: print("giventransshipmentHHs:\n ", giventransshipmentHHs)


        return givenacfestablishments, givenvehicleassinments, givenapheresisassignments, giventransshipmentHIs, giventransshipmentIIs, giventransshipmentHHs
    
    def GetScenarioSet(self, solveseed, nrscenario, allscenarios):
        if Constants.Debug: print("\n We are in 'EvaluationSimulator' Class -- GetScenarioSet")
        scenarioset = []
        treeset = []
        # Use an offset in the seed to make sure the scenario used for evaluation are different from the scenario used for optimization
        offset = solveseed + 999323

        #Uncoment to generate all the scenario if a  distribution with smallll support is used
        if allscenarios == 1:
            if Constants.Debug: print("Generate all the scenarios")

            scenariotree = ScenarioTree(self.Instance, [1] + [1]*self.Instance.NrTimeBucketWithoutUncertaintyBefore + [8, 8, 8, 8, 0], offset,
                                         scenariogenerationmethod=Constants.All,
                                         model=Constants.ModelMulti_Stage)
            scenarioset = scenariotree.GetAllScenarios(False)

            for s in range(len(scenarioset)):
                tree = ScenarioTree(self.Instance, [1, 1, 1, 1, 1, 1, 1, 1, 0], offset,
                                    model=Constants.ModelMulti_Stage, givenfirstperiod=scenarioset[s].Demands)
                treeset.append(tree)
        else:
            for seed in range(offset, nrscenario + offset, 1):
                # Generate a random scenario
                ScenarioSeed = seed
                # Evaluate the solution on the scenario
                #treestructure = [1] + [1] * self.Instance.NrTimeBucket + [0]
                treestructure = [1] * self.Instance.NrTimeBucket

                if Constants.Debug: print("treestructure: ", treestructure)
                
                scenariotree = ScenarioTree(self.Instance, treestructure, ScenarioSeed, evaluationscenario=True, scenariogenerationmethod="MC")
                
                scenario = scenariotree.GetAllScenarios(False)[0]

                scenarioset.append(scenario)
                treeset.append(scenariotree)


        return scenarioset, treeset

    def ComputeStatistic(self, Evaluated, Probabilities, KPIStat, nrerror):
        if Constants.Debug: print("\n We are in 'EvaluationSimulator' Class -- ComputeStatistic")

        # Flatten the Evaluated list to a single list of values
        all_evaluated_values = [val for sublist in Evaluated for val in sublist]

        # Number of scenarios (KK) and evaluations per scenario (MM)
        KK = len(Evaluated)
        MM = self.EvalatorIdentificator.NrEvaluation

        # Calculate mean
        mean = np.mean(all_evaluated_values)
        
        # Calculate variance
        variance_New = np.var(all_evaluated_values, ddof=0)  # Population variance (ddof=0)
        
        # Calculate standard deviation (STD)
        std_New = np.sqrt(variance_New)
        
        # Calculate 95% confidence interval
        z = 1.96  # Critical value for 95% confidence
        margin_of_error = z * (std_New / math.sqrt(KK * MM))
        LB = max(0, mean - margin_of_error)
        UB = mean + margin_of_error

        ###################################################
        '''
        numerator_sum = 0
        denominator_sum = 0
        if Constants.Debug: print("Evaluated: ", Evaluated)
        if Constants.Debug: print("Probabilities: ", Probabilities)
        if Constants.Debug: print("KPIStat: ", KPIStat)
        if Constants.Debug: print("nrerror: ", nrerror)

        # Loop over each element in Evaluated and Probabilities to calculate sums
        for k in range(len(Evaluated)):
            for m in range(self.EvalatorIdentificator.NrEvaluation): 
                if Evaluated[k][m] >= 0:

                    product = np.dot(Evaluated[k][m], Probabilities[k][m])
                    numerator_sum += product
                    #if Constants.Debug: print(f"Product at Evaluated[{k}][{m}] and Probabilities[{k}][{m}]: {product}")
                    
                    denominator_sum += Probabilities[k][m]
                    #if Constants.Debug: print(f"Numerator sum so far: {numerator_sum}, Denominator sum so far: {denominator_sum}")

        mean = float(numerator_sum / denominator_sum)
        if Constants.Debug: print("Calculated mean: ", mean)

        K = len(Evaluated)
        M = self.EvalatorIdentificator.NrEvaluation
        variancepondere = (1.0 / K) * sum(Probabilities[k][seed] * math.pow(Evaluated[k][seed]- mean, 2)
                               for seed in range(M)
                               for k in range(K))

        if Constants.Debug: print("variancepondere: ", variancepondere)

        variance2 = ((1.0 / K) * sum((1.0 / M) * sum(math.pow(Evaluated[k][seed], 2) for seed in range(M)) for k in range(K))) - math.pow(mean,  2)
        if Constants.Debug: print("variance2: ", variance2)

        covariance = 0
        for seed in range(M):
            step = 1
            for k in range(K):
                step *= (math.pow(Evaluated[k][seed] - mean, 2))
            covariance += Probabilities[0][seed] * 1/K * step
        if Constants.Debug: print("covariance: ", covariance)

        term = stats.norm.ppf(1 - 0.05) * math.sqrt(max(((variancepondere + (covariance * (M - 1))) / (K * M)), 0.0))
        if Constants.Debug: print("term: ", term)

        LB = max(0, mean - term)  # Ensure non-negative lower bound
        UB = mean + term
        '''
        
        d = datetime.now()
        date = d.strftime('%m_%d_%Y_%H_%M_%S')

        EvaluateInfo = self.ComputeInformation(Evaluated, self.EvalatorIdentificator.NrEvaluation)

        MinAverage = 0
        MaxAverage = 0
              
        if Constants.PrintDetailsExcelFiles:
            if Constants.Debug: print("self.TestIdentificator.GetAsStringList():\n ", self.TestIdentificator.GetAsStringList())
            if Constants.Debug: print("self.EvalatorIdentificator.GetAsStringList():\n ", self.EvalatorIdentificator.GetAsStringList())

            general = self.TestIdentificator.GetAsStringList() + self.EvalatorIdentificator.GetAsStringList() + [mean, variance_New, LB, UB, MinAverage, MaxAverage, nrerror]

            columnstab = ["Instance", "Model", "Method", "ScenarioGeneration", "NrScenario", "ScenarioSeed",  "EVPI", "NrForwardScenario", 
                          "mipsetting", "SDDPSetting", "HybridPHSetting", "MLLocalSearchSetting",
                           "Policy Generation", "NrEvaluation", "Time Horizon", "All Scenario",  
                           "Mean", "Variance", "LB", "UB", "Min Average", "Max Average", "nrerror"]
            #myfile = open(r'./Test/Bounds/TestResultOfEvaluated_%s_%r.csv' % (self.TestIdentificator.GetAsStringList(), self.EvalatorIdentificator.GetAsStringList()), 'w', newline='', encoding='utf-8')  # 'newline' to avoid extra newlines in Windows
            
            test_identificator_str = '_'.join(self.TestIdentificator.GetAsStringList())
            evaluator_identificator_str = '_'.join(self.EvalatorIdentificator.GetAsStringList())
            # Combine the strings with an underscore and format them into the file path
            # Ensure to replace empty strings or undesired characters if necessary
            filename = f"./Test/Bounds/TestResultOfEvaluated_{test_identificator_str}_{evaluator_identificator_str}.csv"

            myfile = open(filename, 'w', newline='', encoding='utf-8')
            wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
            wr.writerow(columnstab)  # Write the column headers
            wr.writerow(general)  # Write the data
            myfile.close()

        #KPIStat = KPIStat[6:] #The first values in KPIStats are not interesting for out of sample evalution (see MRPSolution::PrintStatistics)
        EvaluateInfo = [mean, LB, UB, MinAverage, MaxAverage, nrerror] + KPIStat

        if Constants.Debug: print("EvaluateInfo: ", EvaluateInfo)

        return EvaluateInfo
    
    def ComputeInformation(self, Evaluation, nrscenario):
        if Constants.Debug: print("\n We are in 'EvaluationSimulator' Class -- ComputeInformation")
        if Constants.Debug: print("Evaluation: ", Evaluation)
        if Constants.Debug: print("nrscenario: ", nrscenario)

        Sum = sum(Evaluation[s][sol] for s in range(nrscenario) for sol in range(self.NrSolutions))
        if Constants.Debug: print("Sum: ", Sum)
        Average = Sum/nrscenario
        if Constants.Debug: print(f"Average: {Average}")

        sumdeviation = sum(math.pow((Evaluation[s][sol] - Average), 2) for s in range(nrscenario) for sol in range(self.NrSolutions))
        std_dev = math.sqrt((sumdeviation / nrscenario))
        if Constants.Debug: print(f"Standard Deviation: {std_dev}")

        EvaluateInfo = [nrscenario, Average, std_dev]

        return EvaluateInfo

    #Run the MIP with some decisions fixed in previous iterations
    def ResolveMIP(self, demanduptotimet, hospitalCapsuptotimet, wholeDonorsuptotimet, apheresisDonorsuptotimet, 
                   resolvetime, givenapheresisassignments, giventransshipmentHIs, giventransshipmentIIs, giventransshipmentHHs,
                   givenacfestablishments, givenvehicleassinments, solution):
        if Constants.Debug: print("\n We are in 'EvaluationSimulator' Class -- ResolveMIP")
        
        givenapheresisassignments = [solution.ApheresisAssignment_y_wti[0][resolvetime][i]
                                        for i in self.Instance.ACFPPointSet]
        if Constants.Debug: print("givenapheresisassignments: ", givenapheresisassignments)
        
        giventransshipmentHIs = [[[[solution.TransshipmentHI_b_wtcrhi[0][resolvetime][c][r][h][i]
                                    for i in self.Instance.ACFPPointSet]
                                    for h in self.Instance.HospitalSet] 
                                    for r in self.Instance.PlateletAgeSet] 
                                    for c in self.Instance.BloodGPSet] 
        if Constants.Debug: print("giventransshipmentHIs: ", giventransshipmentHIs)
        
        giventransshipmentIIs = [[[[solution.TransshipmentII_bPrime_wtcrii[0][resolvetime][c][r][i][iprime]
                                    for iprime in self.Instance.ACFPPointSet]
                                    for i in self.Instance.ACFPPointSet] 
                                    for r in self.Instance.PlateletAgeSet] 
                                    for c in self.Instance.BloodGPSet] 
        if Constants.Debug: print("giventransshipmentIIs: ", giventransshipmentIIs)
        
        giventransshipmentHHs = [[[[solution.TransshipmentHH_bDoublePrime_wtcrhh[0][resolvetime][c][r][h][hprime]
                                    for hprime in self.Instance.HospitalSet]
                                    for h in self.Instance.HospitalSet] 
                                    for r in self.Instance.PlateletAgeSet] 
                                    for c in self.Instance.BloodGPSet] 
        if Constants.Debug: print("giventransshipmentHHs: ", giventransshipmentHHs)
        
        return givenapheresisassignments, giventransshipmentHIs, giventransshipmentIIs, giventransshipmentHHs
               
        if not self.IsDefineMIPResolveTime[resolvetime]:
            scenariotree, _ = self.GetScenarioTreeForResolve(resolvetime, demanduptotimet)

            mipsolver = MIPSolver(self.Instance, self.Model, scenariotree,
                                    self.EVPI,
                                    implicitnonanticipativity=(not self.EVPI),
                                    evaluatesolution=True,
                                    givenvartranss=givenvartrans,
                                    givenfixedtranss=givenfixedtrans,
                                    fixsolutionuntil=(resolvetime -1), #time lower or equal
                                    demandknownuntil=resolvetime)

            mipsolver.BuildModel()
            self.MIPResolveTime[resolvetime] = mipsolver
            self.IsDefineMIPResolveTime[resolvetime] = True
        else:
            self.MIPResolveTime[resolvetime].ModifyMipForScenario(demanduptotimet, resolvetime)
            self.MIPResolveTime[resolvetime].ModifyMipForFixVarTrans(givenvartrans, fixuntil=resolvetime)


        self.MIPResolveTime[resolvetime].Cplex.parameters.advance = 1
        self.MIPResolveTime[resolvetime].Cplex.parameters.lpmethod.set(self.MIPResolveTime[resolvetime].Cplex.parameters.lpmethod.values.barrier)

        solution = self.MIPResolveTime[resolvetime].Solve(createsolution=False)

        if Constants.Debug:
            if Constants.Debug: print("End solving")

        #self.MIPResolveTime[time].Cplex.write("MRP-Re-Solve.lp")
        # Get the corresponding node:
        error = 0
        sol = self.MIPResolveTime[resolvetime].Cplex.solution
        if sol.is_primal_feasible():
            array = [self.MIPResolveTime[resolvetime].GetIndexQuantityVariable(p, resolvetime, 0) for p in self.Instance.ProductSet];

            resultqty = sol.get_values(array)
            if Constants.Debug:
                if Constants.Debug: print(resultqty)

            array = [int(self.MIPResolveTime[resolvetime].GetIndexConsumptionVariable(c[0], c[1], resolvetime, 0)) for c in self.Instance.ConsumptionSet];
            resultconsumption = sol.get_values(array)
            if Constants.Debug:
                if Constants.Debug: print(resultqty)
        else:
            if Constants.Debug:
                self.MIPResolveTime[resolvetime].Cplex.write("MRP-Re-Solve.lp")
                raise NameError("Infeasible MIP at time %d in Re-solve see MRP-Re-Solve.lp" % resolvetime)

            error = 1

        return resultqty, error
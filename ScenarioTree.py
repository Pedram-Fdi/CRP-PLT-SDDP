import numpy as np
from ScenarioTreeNode import ScenarioTreeNode
from Scenario import Scenario
from Constants import Constants
from RQMCGenerator import RQMCGenerator
import math
import itertools


#from matplotlib import pyplot as PLT

class ScenarioTree(object):
    #Constructor
    def __init__(self, instance=None, branchperlevel=[], seed=-1, mipsolver=None, evaluationscenario = False, averagescenariotree = False, scenariogenerationmethod="MC", generateas_Two_Stage = False, model = "Multi_Stage", CopyscenariofromMulti_Stage=False, issymetric = False, givenscenarioset = [], givenfirstperiod=[]):
        if Constants.Debug: print("\n We are in 'ScenarioTree' Class -- Constructor")

        self.CopyscenariofromMulti_Stage = CopyscenariofromMulti_Stage
        self.Seed = seed
        if Constants.Debug: print("Create a tree with seed %r structure: %r"%(seed, branchperlevel))
        
        np.random.seed(seed)
        self.Nodes = []
        self.Owner = mipsolver
        self.Instance = instance
        self.TreeStructure = branchperlevel
        self.NrBranches = branchperlevel
        self.EvaluationScenrio = evaluationscenario
        self.AverageScenarioTree = averagescenariotree
        self.ScenarioGenerationMethod = scenariogenerationmethod

        #For some types of evaluation, the demand of the  first periods are given and the rest is stochastic
        self.GivenFirstPeriod = givenfirstperiod
        self.FollowGivenUntil = len(self.GivenFirstPeriod)
        firstuknown = len(self.GivenFirstPeriod)        
        firststochastic = firstuknown
        
        #In case the scenario tree has to be the same as the two stage (YQFix) scenario tree.
        self.Generateas_Two_Stage = generateas_Two_Stage
        self.Distribution = instance.Distribution
        self.DemandToFollow = []

        self.IsSymetric = issymetric   

        #Generate the demand of Multi_Stage (Multi-Stage Model), then replicate them in the generation of the scenario tree
        if self.Generateas_Two_Stage:
            TwoStageExtended_Tree = ScenarioTree(instance, self.TreeStructure, seed, scenariogenerationmethod=self.ScenarioGenerationMethod)
            TwoStageExtended_Sceanrios = TwoStageExtended_Tree.GetAllScenarios(computeindex=True)
            self.DemandToFollow = [[[TwoStageExtended_Sceanrios[w].Demands[d][t]
                                     for d in self.Instance.DemandSet]
                                    for t in self.Instance.TimeBucketSet]
                                   for w in range(len(TwoStageExtended_Sceanrios))]        
        
        
        self.Demand_TwoStage_RQMC = []
        self.HospitalCap_TwoStage_RQMC = []
        self.WholeDonor_TwoStage_RQMC = []
        self.ApheresisDonor_TwoStage_RQMC = []
        self.Model = model
        
        self.GenerateRQMCForTwoStage = (Constants.IsQMCMethos(self.ScenarioGenerationMethod) and self.Model == Constants.Two_Stage)

        if Constants.Debug: print("self.Model: ", self.Model)
        if Constants.Debug: print("self.GenerateRQMCForTwoStage: ", self.GenerateRQMCForTwoStage)

        TimeBucketsWithUncertainty = range(self.Instance.NrTimeBucket)
        if Constants.Debug: print("TimeBucketsWithUncertainty: ", TimeBucketsWithUncertainty)

        nrTimeBucketsWithUncertainty = len(TimeBucketsWithUncertainty)
        if Constants.Debug: print("nrTimeBucketsWithUncertainty: ", nrTimeBucketsWithUncertainty)

        if self.ScenarioGenerationMethod == Constants.All and model == Constants.Two_Stage:
            self.GenerateUncertainParametersToFollowAll(self.TreeStructure)

        if Constants.Debug: self.Print_Attributes()

        if Constants.IsQMCMethos(self.ScenarioGenerationMethod) and self.GenerateRQMCForTwoStage:
            self.GenerateDemandToFollowRQMC(TimeBucketsWithUncertainty, nrTimeBucketsWithUncertainty)
            self.GenerateHospitalCapToFollowRQMC(TimeBucketsWithUncertainty, nrTimeBucketsWithUncertainty)            
            self.GenerateWholeDonorToFollowRQMC(TimeBucketsWithUncertainty, nrTimeBucketsWithUncertainty)
            self.GenerateApheresisDonorToFollowRQMC(TimeBucketsWithUncertainty, nrTimeBucketsWithUncertainty)

        if self.CopyscenariofromMulti_Stage:
            self.GenerateDemandToFollowFromScenarioSet(givenscenarioset)
            self.GenerateHospitalCapToFollowFromScenarioSet(givenscenarioset)
            self.GenerateWholeDonorToFollowFromScenarioSet(givenscenarioset)
            self.GenerateApheresisDonorToFollowFromScenarioSet(givenscenarioset)

        if self.IsSymetric:
            if Constants.Debug: print("------------Moving from 'ScenarioTree' Class Constructor to 'ScenarioTreeNode' Class (CreateDemandNormalDistributiondemand))---------------")
            ##################### Uncertain Demands
            self.SymetricDemand=[ [] for t in self.Instance.TimeBucketSet]
            self.SymetricProba=[ [] for t in self.Instance.TimeBucketSet]
            
            for t in self.Instance.TimeBucketSet:
                    if Constants.Debug: print(f"self.TreeStructure[t={t}]: ", self.TreeStructure[t])
                    self.SymetricDemand[t], self.SymetricProba[t] = ScenarioTreeNode.CreateDemandNormalDistributiondemand(self.Instance, t, self.TreeStructure[t], False, self.ScenarioGenerationMethod)
                    if Constants.Debug: print(f"SymetricDemand[t:{t}]: ", self.SymetricDemand[t])
            if Constants.Debug: print("SymetricDemand: ", self.SymetricDemand)        
            if Constants.Debug: print("SymetricProba: ", self.SymetricProba)        
            
            ##################### Uncertain Hospoital Treatment Capacity
            self.SymetricHospitalCapacity=[ [] for t in self.Instance.TimeBucketSet]
            self.SymetricProbaHospital=[ [] for t in self.Instance.TimeBucketSet]
            
            for t in self.Instance.TimeBucketSet:
                    if Constants.Debug: print(f"self.TreeStructure[t={t}]: ", self.TreeStructure[t])
                    self.SymetricHospitalCapacity[t], self.SymetricProbaHospital[t] = ScenarioTreeNode.CreateHospitalCapNormalDistribution(self.Instance, t, self.TreeStructure[t], False, self.ScenarioGenerationMethod)
            
            if Constants.Debug: print("SymetricHospitalCapacity: ", self.SymetricHospitalCapacity)
            if Constants.Debug: print("SymetricProbaHospital: ", self.SymetricProbaHospital)
            
            ##################### Uncertain Whole Blood Donors
            self.SymetricWholeDonor=[ [] for t in self.Instance.TimeBucketSet]
            self.SymetricProbaWholeDonor=[ [] for t in self.Instance.TimeBucketSet]
            
            for t in self.Instance.TimeBucketSet:
                    if Constants.Debug: print(f"self.TreeStructure[t={t}]: ", self.TreeStructure[t])
                    self.SymetricWholeDonor[t], self.SymetricProbaWholeDonor[t] = ScenarioTreeNode.CreateWholeDonorNormalDistribution(self.Instance, t, self.TreeStructure[t], False, self.ScenarioGenerationMethod)
            
            if Constants.Debug: print("SymetricWholeDonor: ", self.SymetricWholeDonor)
            if Constants.Debug: print("SymetricProbaWholeDonor: ", self.SymetricProbaWholeDonor)
            
            ##################### Uncertain Apheresis Blood Donors
            self.SymetricApheresisDonor=[ [] for t in self.Instance.TimeBucketSet]
            self.SymetricProbaApheresisDonor=[ [] for t in self.Instance.TimeBucketSet]
            
            for t in self.Instance.TimeBucketSet:
                    if Constants.Debug: print(f"self.TreeStructure[t={t}]: ", self.TreeStructure[t])
                    self.SymetricApheresisDonor[t], self.SymetricProbaApheresisDonor[t] = ScenarioTreeNode.CreateApheresisDonorNormalDistribution(self.Instance, t, self.TreeStructure[t], False, self.ScenarioGenerationMethod)
            
            if Constants.Debug: print("SymetricApheresisDonor: ", self.SymetricApheresisDonor)
            if Constants.Debug: print("SymetricProbaApheresisDonor: ", self.SymetricProbaApheresisDonor)

            if Constants.Debug: print("------------Moving BACK from 'ScenarioTreeNode' Class (CreateDemandNormalDistributiondemand) to 'ScenarioTree' Class Constructor)---------------")

       
        ScenarioTreeNode.NrNode = 0
        #Create the tree:

        if Constants.Debug: print("------------Moving from 'ScenarioTree' Class Constructor to 'ScenarioTreeNode' Class constructor---------------")
        if Constants.Evaluation_Part:
            self.RootNode = ScenarioTreeNode(owner=self,
                                                instance=instance,
                                                mipsolver=self.Owner,
                                                time=-1, 
                                                nrbranch=1,
                                                proabibilty=1,
                                                averagescenariotree=False)
        else:
            self.RootNode = ScenarioTreeNode(owner=self,
                                                instance=instance,
                                                mipsolver=self.Owner,
                                                time=-1, 
                                                nrbranch=1,
                                                proabibilty=1,
                                                averagescenariotree=True)
        if Constants.Debug: print("------------Moving BACK from 'ScenarioTreeNode' Class constructor 'ScenarioTree' Class Constructor---------------")

        if instance is None:
            self.NrLevel = -1
        else:
            self.NrLevel = instance.NrTimeBucket
        
        self.NrNode = ScenarioTreeNode.NrNode
        if Constants.Debug: print("self.NrNode: ",self.NrNode)

        self.Renumber()

    def Transpose_Vectors_forTwoStage(self, period_rmcpoints):
        
        # Convert to numpy array for easier manipulation
        array = np.array(period_rmcpoints)

        # Calculate new shape
        new_shape = (array.shape[0], array.shape[2], array.shape[1])

        # Transpose the inner arrays
        transposed_arrays = np.transpose(array, axes=(0, 2, 1))

        # Convert back to list to display
        return transposed_arrays.tolist()

    def Combine_Vectors_forTwoStage(self, transposed_period_rmcpoints):
        if Constants.Debug: print("\n We are in 'ScenarioTree' Class -- combine_vectors")

        # Calculate number of parts
        number_of_parts = len(transposed_period_rmcpoints)
        
        # Initialize the list of combined results with the first part
        combined_result = [[vec] for vec in transposed_period_rmcpoints[0]]

        # Iteratively combine each existing combination with each vector in the next part
        for part in transposed_period_rmcpoints[1:]:
            new_combinations = []
            for combo in combined_result:
                for vector in part:
                    new_combinations.append(combo + [vector])
            combined_result = new_combinations
        
        return combined_result
        
        return combined_result
    
    # Generate the demand to follow in two stage when these demand are generated with a tree with RQMC scenario
    def GenerateDemandToFollowRQMC(self, TimeBucketsWithUncertainty, nrTimeBucketsWithUncertainty):
        if Constants.Debug: print("\n We are in 'ScenarioTree' Class -- GenerateDemandToFollowRQMC")

        dimension = len(self.Instance.DemandSet) * len(self.Instance.BloodGPSet) * len(self.Instance.InjuryLevelSet)
        nrscenario = max(self.NrBranches[i] for i in range(len(self.NrBranches)))
        nrscenario_In_each_TimePeroid = round(nrscenario ** (1 / self.Instance.NrTimeBucket))
        
        self.Demand_TwoStage_RQMC = [[[[[0 
                                        for l in self.Instance.DemandSet] 
                                        for c in self.Instance.BloodGPSet] 
                                        for j in self.Instance.InjuryLevelSet] 
                                        for t in self.Instance.TimeBucketSet] 
                                        for s in range(nrscenario)]
        
        period_rmcpoints = []

        for i in range(nrTimeBucketsWithUncertainty):
            avgvector = [self.Instance.ForecastedAverageDemand[i][j][c][l]
                        for j in self.Instance.InjuryLevelSet
                        for c in self.Instance.BloodGPSet
                        for l in self.Instance.DemandSet]
            stdvector = [self.Instance.ForecastedStandardDeviationDemand[i][j][c][l]
                        for j in self.Instance.InjuryLevelSet
                        for c in self.Instance.BloodGPSet
                        for l in self.Instance.DemandSet]

            nrnonzero = sum(1 for p in range(dimension) if avgvector[p] > 0)
            idnonzero = [p for p in range(dimension) if avgvector[p] > 0]
            avg = [avgvector[d] for d in idnonzero]
            stddev = [stdvector[d] for d in idnonzero]

            rqmcpoint01 = RQMCGenerator.RQMC01(nrscenario_In_each_TimePeroid, dimension, withweight=False, QMC=(self.ScenarioGenerationMethod == Constants.QMC), sequence_type = Constants.SequenceTypee)
            rmcpoint = ScenarioTreeNode.TransformInverse(rqmcpoint01, nrscenario_In_each_TimePeroid, nrnonzero, self.Instance.Distribution, avg, stddev)
            if Constants.Debug: print("rmcpoint:\n", rmcpoint)  
            # Create a fresh points array for each time bucket
            points = [[0.0 for _ in range(nrscenario_In_each_TimePeroid)] for _ in range(dimension)]
            
            for p in range(nrnonzero): 
                for s in range(nrscenario_In_each_TimePeroid):
                    points[idnonzero[p]][s] = rmcpoint[p][s]  # No need to round here

            if Constants.Debug: print("points:\n ", points)
            period_rmcpoints.append(points)                    
        
        transposed_period_rmcpoints = self.Transpose_Vectors_forTwoStage(period_rmcpoints)        
        TwoStage=self.Combine_Vectors_forTwoStage(transposed_period_rmcpoints)
        if Constants.Debug: print("TwoStage: ", TwoStage)
        # Flattened index to multi-dimensional indices
        for w in range(nrscenario):
            for t in range(nrTimeBucketsWithUncertainty):
                for d in range(dimension):
                    # Calculate multi-dimensional indices from flattened index d
                    l_index = d % len(self.Instance.DemandSet)
                    c_index = (d // len(self.Instance.DemandSet)) % len(self.Instance.BloodGPSet)
                    j_index = (d // (len(self.Instance.DemandSet) * len(self.Instance.BloodGPSet))) % len(self.Instance.InjuryLevelSet)
                    
                    self.Demand_TwoStage_RQMC[w][t][j_index][c_index][l_index] = TwoStage[w][t][d]
        
        if Constants.Debug: print("self.Demand_TwoStage_RQMC: ", self.Demand_TwoStage_RQMC)
    
    def GenerateHospitalCapToFollowRQMC(self, TimeBucketsWithUncertainty, nrTimeBucketsWithUncertainty):
        if Constants.Debug: print("\n We are in 'ScenarioTree' Class -- GenerateHospitalCapToFollowRQMC")
        Constants.GeneratingHospitalUncertainCapacity = True
        
        dimension = len(self.Instance.HospitalSet)
        nrscenario = max(self.NrBranches[i] for i in range(len(self.NrBranches)))
        nrscenario_In_each_TimePeroid = round(nrscenario ** (1 / self.Instance.NrTimeBucket))
        
        self.HospitalCap_TwoStage_RQMC = [[[0 
                                            for h in self.Instance.HospitalSet] 
                                            for t in self.Instance.TimeBucketSet] 
                                            for s in range(nrscenario)]
        
        period_rmcpoints = []

        for i in range(nrTimeBucketsWithUncertainty):

            avgvector = [self.Instance.ForecastedAverageHospital_Bed_Capacity[i][h]
                        for h in self.Instance.HospitalSet]
            stdvector = [self.Instance.ForecastedSTDHospital_Bed_Capacity[i][h] 
                        for h in self.Instance.HospitalSet]
                    
            nrnonzero = sum(1 for p in range(dimension) if avgvector[p] > 0)
            idnonzero = [p for p in range(dimension) if avgvector[p] > 0]
            avg = [avgvector[d] for d in idnonzero]
            stddev = [stdvector[d] for d in idnonzero]
                    
            rqmcpoint01 = RQMCGenerator.RQMC01(nrscenario_In_each_TimePeroid, dimension, withweight=False, QMC=(self.ScenarioGenerationMethod == Constants.QMC), sequence_type = Constants.SequenceTypee)
            rmcpoint = ScenarioTreeNode.TransformInverse(rqmcpoint01, nrscenario_In_each_TimePeroid, nrnonzero, self.Instance.Distribution, avg, stddev)
            if Constants.Debug: print("rmcpoint:\n", rmcpoint)  
            # Create a fresh points array for each time bucket
            points = [[0.0 for _ in range(nrscenario_In_each_TimePeroid)] for _ in range(dimension)]
            
            for p in range(nrnonzero): 
                for s in range(nrscenario_In_each_TimePeroid):
                    points[idnonzero[p]][s] = rmcpoint[p][s]  # No need to round here

            if Constants.Debug: print("points:\n ", points)
            period_rmcpoints.append(points) 
        
        transposed_period_rmcpoints = self.Transpose_Vectors_forTwoStage(period_rmcpoints)        
        TwoStage=self.Combine_Vectors_forTwoStage(transposed_period_rmcpoints)
        if Constants.Debug: print("Hospital Cap TwoStage: ", TwoStage)

        for w in range(nrscenario):
            for t in range(nrTimeBucketsWithUncertainty):
                for h in range(dimension):
                    self.HospitalCap_TwoStage_RQMC[w][t][h] = TwoStage[w][t][h]
        
        if Constants.Debug: print("self.HospitalCap_TwoStage_RQMC: ", self.HospitalCap_TwoStage_RQMC)
        Constants.GeneratingHospitalUncertainCapacity = False
        
    def GenerateWholeDonorToFollowRQMC(self, TimeBucketsWithUncertainty, nrTimeBucketsWithUncertainty):
        if Constants.Debug: print("\n We are in 'ScenarioTree' Class -- GenerateWholeDonorToFollowRQMC")

        dimension = len(self.Instance.BloodGPSet) * len(self.Instance.HospitalSet)
        nrscenario = max(self.NrBranches[i] for i in range(len(self.NrBranches)))
        nrscenario_In_each_TimePeroid = round(nrscenario ** (1 / self.Instance.NrTimeBucket))
        
        self.WholeDonor_TwoStage_RQMC = [[[[0 
                                       for h in self.Instance.HospitalSet] 
                                       for c in self.Instance.BloodGPSet] 
                                       for t in self.Instance.TimeBucketSet] 
                                       for s in range(nrscenario)]
        period_rmcpoints = []

        for i in range(nrTimeBucketsWithUncertainty):

            avgvector = [self.Instance.ForecastedAverageWhole_Blood_Donors[i][c][h]
                        for c in self.Instance.BloodGPSet
                        for h in self.Instance.HospitalSet]
            stdvector = [self.Instance.ForecastedSTDWhole_Blood_Donors[i][c][h]
                        for c in self.Instance.BloodGPSet
                        for h in self.Instance.HospitalSet]
        
            nrnonzero = sum(1 for p in range(dimension) if avgvector[p] > 0)
            idnonzero = [p for p in range(dimension) if avgvector[p] > 0]
            avg = [avgvector[d] for d in idnonzero]
            stddev = [stdvector[d] for d in idnonzero]
                    
            rqmcpoint01 = RQMCGenerator.RQMC01(nrscenario_In_each_TimePeroid, dimension, withweight=False, QMC=(self.ScenarioGenerationMethod == Constants.QMC), sequence_type = Constants.SequenceTypee)
            rmcpoint = ScenarioTreeNode.TransformInverse(rqmcpoint01, nrscenario_In_each_TimePeroid, nrnonzero, self.Instance.Distribution, avg, stddev)
            if Constants.Debug: print("rmcpoint:\n", rmcpoint)  
            # Create a fresh points array for each time bucket
            points = [[0.0 for _ in range(nrscenario_In_each_TimePeroid)] for _ in range(dimension)]
            
            for p in range(nrnonzero): 
                for s in range(nrscenario_In_each_TimePeroid):
                    points[idnonzero[p]][s] = rmcpoint[p][s]  # No need to round here

            if Constants.Debug: print("points:\n ", points)
            period_rmcpoints.append(points) 
        
        transposed_period_rmcpoints = self.Transpose_Vectors_forTwoStage(period_rmcpoints)        
        TwoStage=self.Combine_Vectors_forTwoStage(transposed_period_rmcpoints)
        
        # Flattened index to multi-dimensional indices
        for w in range(nrscenario):
            for t in range(nrTimeBucketsWithUncertainty):
                for d in range(dimension):
                    # Calculate multi-dimensional indices from flattened index d
                    h_index = d % len(self.Instance.HospitalSet)
                    c_index = (d // len(self.Instance.HospitalSet)) % len(self.Instance.BloodGPSet)
                    
                    self.WholeDonor_TwoStage_RQMC[w][t][c_index][h_index] = TwoStage[w][t][d]
        
        if Constants.Debug: print("self.WholeDonor_TwoStage_RQMC: ", self.WholeDonor_TwoStage_RQMC)

    def GenerateApheresisDonorToFollowRQMC(self, TimeBucketsWithUncertainty, nrTimeBucketsWithUncertainty):
        if Constants.Debug: print("\n We are in 'ScenarioTree' Class -- GenerateApheresisDonorToFollowRQMC")

        dimension = len(self.Instance.BloodGPSet) * len(self.Instance.FacilitySet)
        nrscenario = max(self.NrBranches[i] for i in range(len(self.NrBranches)))
        nrscenario_In_each_TimePeroid = round(nrscenario ** (1 / self.Instance.NrTimeBucket))
        
        self.ApheresisDonor_TwoStage_RQMC = [[[[0 
                                                for u in self.Instance.FacilitySet] 
                                                for c in self.Instance.BloodGPSet] 
                                                for t in self.Instance.TimeBucketSet] 
                                                for s in range(nrscenario)]
        period_rmcpoints = []

        for i in range(nrTimeBucketsWithUncertainty):

            avgvector = [self.Instance.ForecastedAverageApheresis_Donors[i][c][u]
                        for c in self.Instance.BloodGPSet
                        for u in self.Instance.FacilitySet]
            stdvector = [self.Instance.ForecastedSTDApheresis_Donors[i][c][u]
                        for c in self.Instance.BloodGPSet
                        for u in self.Instance.FacilitySet]
        
            nrnonzero = sum(1 for p in range(dimension) if avgvector[p] > 0)
            idnonzero = [p for p in range(dimension) if avgvector[p] > 0]
            avg = [avgvector[d] for d in idnonzero]
            stddev = [stdvector[d] for d in idnonzero]
                    
            rqmcpoint01 = RQMCGenerator.RQMC01(nrscenario_In_each_TimePeroid, dimension, withweight=False, QMC=(self.ScenarioGenerationMethod == Constants.QMC), sequence_type = Constants.SequenceTypee)
            rmcpoint = ScenarioTreeNode.TransformInverse(rqmcpoint01, nrscenario_In_each_TimePeroid, nrnonzero, self.Instance.Distribution, avg, stddev)
            if Constants.Debug: print("rmcpoint:\n", rmcpoint)  
            # Create a fresh points array for each time bucket
            points = [[0.0 for _ in range(nrscenario_In_each_TimePeroid)] for _ in range(dimension)]
            
            for p in range(nrnonzero): 
                for s in range(nrscenario_In_each_TimePeroid):
                    points[idnonzero[p]][s] = rmcpoint[p][s]  # No need to round here

            if Constants.Debug: print("points:\n ", points)
            period_rmcpoints.append(points) 
        
        transposed_period_rmcpoints = self.Transpose_Vectors_forTwoStage(period_rmcpoints)        
        TwoStage=self.Combine_Vectors_forTwoStage(transposed_period_rmcpoints)
        
        # Flattened index to multi-dimensional indices
        for w in range(nrscenario):
            for t in range(nrTimeBucketsWithUncertainty):
                for d in range(dimension):
                    # Calculate multi-dimensional indices from flattened index d
                    u_index = d % len(self.Instance.FacilitySet)
                    c_index = (d // len(self.Instance.FacilitySet)) % len(self.Instance.BloodGPSet)
                    
                    self.ApheresisDonor_TwoStage_RQMC[w][t][c_index][u_index] = TwoStage[w][t][d]
        
        if Constants.Debug: print("self.ApheresisDonor_TwoStage_RQMC: ", self.ApheresisDonor_TwoStage_RQMC)

    def GenerateDemandToFollowFromScenarioSet(self, scenarioset):
        if Constants.Debug: print("\n We are in 'ScenarioTree' Class -- GenerateDemandToFollowFromScenarioSet")
        if Constants.Debug: print("scenarioset:",scenarioset)
        nrscenario = len(scenarioset)
        if Constants.Debug: print("nrscenario:",nrscenario)
        self.DemandToFollowMultipleSceario = [[[[[scenarioset[s].Demands[t][j][c][l]
                                                for l in self.Instance.DemandSet]
                                                for c in self.Instance.BloodGPSet]
                                                for j in self.Instance.InjuryLevelSet]
                                                for t in self.Instance.TimeBucketSet]
                                                for s in range(nrscenario)]
        self.ProbabilityToFollowMultipleSceario = [scenarioset[s].Probability for s in range(nrscenario)]
        if Constants.Debug: print("self.DemandToFollowMultipleSceario:" , self.DemandToFollowMultipleSceario)
        if Constants.Debug: print("self.ProbabilityToFollowMultipleSceario:" , self.ProbabilityToFollowMultipleSceario)
    
    def GenerateHospitalCapToFollowFromScenarioSet(self, scenarioset):
        if Constants.Debug: print("\n We are in 'ScenarioTree' Class -- GenerateHospitalCapToFollowFromScenarioSet")
        nrscenario = len(scenarioset)
        self.HospitalCapToFollowMultipleSceario = [[[scenarioset[s].HospitalCaps[t][h]
                                                        for h in self.Instance.HospitalSet]
                                                        for t in self.Instance.TimeBucketSet]
                                                        for s in range(nrscenario)]
        #self.ProbabilityToFollowMultipleSceario = [scenarioset[s].Probability for s in range(nrscenario)]
        if Constants.Debug: print("self.HospitalCapToFollowMultipleSceario:" , self.HospitalCapToFollowMultipleSceario)
        #if Constants.Debug: print("self.ProbabilityToFollowMultipleSceario:" , self.ProbabilityToFollowMultipleSceario)
    
    def GenerateWholeDonorToFollowFromScenarioSet(self, scenarioset):
        if Constants.Debug: print("\n We are in 'ScenarioTree' Class -- GenerateWholeDonorToFollowFromScenarioSet")
        if Constants.Debug: print("scenarioset:",scenarioset)
        nrscenario = len(scenarioset)
        if Constants.Debug: print("nrscenario:",nrscenario)
        self.WholeDonorToFollowMultipleSceario = [[[[scenarioset[s].WholeDonors[t][c][h]
                                                        for h in self.Instance.HospitalSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for t in self.Instance.TimeBucketSet]
                                                        for s in range(nrscenario)]
        #self.ProbabilityToFollowMultipleSceario = [scenarioset[s].Probability for s in range(nrscenario)]
        if Constants.Debug: print("self.WholeDonorToFollowMultipleSceario:" , self.WholeDonorToFollowMultipleSceario)
        #if Constants.Debug: print("self.ProbabilityToFollowMultipleSceario:" , self.ProbabilityToFollowMultipleSceario)
    
    def GenerateApheresisDonorToFollowFromScenarioSet(self, scenarioset):
        if Constants.Debug: print("\n We are in 'ScenarioTree' Class -- GenerateApheresisDonorToFollowFromScenarioSet")
        if Constants.Debug: print("scenarioset:",scenarioset)
        nrscenario = len(scenarioset)
        if Constants.Debug: print("nrscenario:",nrscenario)

        self.ApheresisDonorToFollowMultipleSceario = [[[[scenarioset[s].ApheresisDonors[t][c][u]
                                                        for u in self.Instance.FacilitySet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for t in self.Instance.TimeBucketSet]
                                                        for s in range(nrscenario)]
        #self.ProbabilityToFollowMultipleSceario = [scenarioset[s].Probability for s in range(nrscenario)]
        if Constants.Debug: print("self.ApheresisDonorToFollowMultipleSceario:" , self.ApheresisDonorToFollowMultipleSceario)
        #if Constants.Debug: print("self.ProbabilityToFollowMultipleSceario:" , self.ProbabilityToFollowMultipleSceario)
    
    # Generate the demand to follow in two stage when these demand are generated with a tree with all scenario
    def GenerateUncertainParametersToFollowAll(self, TimeBucketsWithUncertainty):
        if Constants.Debug: print("\n We are in 'ScenarioTree' Class -- GenerateUncertainParametersToFollowAll")

        temporarytreestructur = TimeBucketsWithUncertainty
        temporaryscenariotree = ScenarioTree(self.Instance, temporarytreestructur, self.Seed,
                                             averagescenariotree=False,
                                             scenariogenerationmethod=Constants.All)
        temporaryscenarios = temporaryscenariotree.GetAllScenarios(False)

        self.GenerateDemandToFollowFromScenarioSet(temporaryscenarios)
        self.GenerateHospitalCapToFollowFromScenarioSet(temporaryscenarios)
        self.GenerateWholeDonorToFollowFromScenarioSet(temporaryscenarios)
        self.GenerateApheresisDonorToFollowFromScenarioSet(temporaryscenarios)

    #This function number the node from highest level to lowest.
    def Renumber(self):
        if Constants.Debug: print("\n We are in 'ScenarioTree' Class -- Renumber")
        k = 1
        # Find the maximum level in the tree
        nrlevel = max(n.Time for n in self.Nodes)
        if Constants.Debug: print("nrlevel: ", nrlevel)
        
        # Iterate through each level
        for l in range(nrlevel + 1):
            # Retrieve nodes at the current level
            nodes = [n for n in self.Nodes if n.Time == l]
            if Constants.Debug: print(f"Processing level {l} with {len(nodes)} nodes")
            
            # Assign a unique number to each node at this level
            for n in nodes:
                #if Constants.Debug: print(f"Assigning NodeNumber {k} to node at level {l}")
                n.NodeNumber = k
                k += 1
    
    #Compute the index of the variable (one variable for each node of the tree)
    def ComputeVariableIdicies(self):
        if Constants.Debug: print("\n We are in 'ScenarioTree' Class -- ComputeVariableIdicies")
        if Constants.Debug: print("------------Moving from 'ScenarioTree' Class ('GetAllScenarios' Function) to 'ScenarioTreeNode' class ('ComputeVariableIndex' Function)---------------")        
        for n in self.Nodes:
            n.ComputeVariableIndex()          
        if Constants.Debug: print("------------Moving BACK from 'ScenarioTreeNode' class ('ComputeVariableIndex' Function) to 'ScenarioTree' Class ('GetAllScenarios' Function)---------------")        

    #This function assemble the data in the tree, and return the list of leaves, which contain the scenarios
    def GetAllScenarios(self, computeindex=False, expandfirststage = False):
        if Constants.Debug: print("\n We are in 'ScenarioTree' Class -- GetAllScenarios")
        #A mip solver is required to compute the index, it is not always set
        if computeindex:  
            self.ComputeVariableIdicies()

        if Constants.Debug: print("------------Moving from 'ScenarioTree' Class ('GetAllScenarios' Function) to 'ScenarioTreeNode' class ('CreateAllScenarioFromNode' Function)---------------")
        self.RootNode.CreateAllScenarioFromNode()
        if Constants.Debug: print("------------Moving BACK from 'ScenarioTreeNode' class ('CreateAllScenarioFromNode' Function) to 'ScenarioTree' Class ('GetAllScenarios' Function)---------------")
       
        if Constants.Debug: print("------------Moving from 'ScenarioTree' Class ('GetAllScenarios' Function) to 'ScenarioTreeNode' class ('Display' Function)---------------")
        if Constants.Debug: self.RootNode.Display()
        if Constants.Debug: print("------------Moving BACK from 'ScenarioTreeNode' class ('Display' Function) to 'ScenarioTree' Class ('GetAllScenarios' Function)---------------")

        #return the set of leaves as they represent the scenario
        scenarioset = [n for n in self.Nodes if len(n.Branches) == 0]

        if Constants.Debug: print("------------Moving from 'ScenarioTree' Class ('GetAllScenarios' Function) to 'Scenario' class (Constructor)---------------")       
        Scenario.NrScenario = 0         #Added by Pedram (to reset the Scenario number each time entering Scenario Class)

        scenarios = [Scenario(owner=self,
                              demand=s.DemandsInScenario,
                              hospitalcap=s.HospitalCapsInScenario,
                              wholedonor=s.WholeDonorsInScenario,
                              apheresisdonor=s.ApheresisDonorsInScenario,
                              proabability=s.ProbabilityOfScenario,
                              acfestablishment_variable=s.ACFEstablishmentVariableOfScenario,
                              vehicleassignment_variable=s.VehicleAssignmentVariableOfScenario,
                              apheresisAssignment_variable=s.ApheresisAssignmentVariableOfScenario,
                              transshipmentHI_variable=s.TransshipmentHIVariableOfScenario,
                              transshipmentII_variable=s.TransshipmentIIVariableOfScenario,
                              transshipmentHH_variable=s.TransshipmentHHVariableOfScenario,
                              patientTransfer_variable=s.PatientTransferVariableOfScenario,
                              unsatisfiedPatients_variable=s.UnsatisfiedPatientsVariableOfScenario,
                              plateletInventory_vriable=s.PlateletInventoryVariableOfScenario,
                              outdatedPlatelet_variable=s.OutdatedPlateletVariableOfScenario,
                              servedPatient_variable=s.ServedPatientVariableOfScenario,
                              patientPostponement_variable=s.PatientPostponementVariableOfScenario,
                              plateletApheresisExtraction_variable=s.PlateletApheresisExtractionVariableOfScenario,
                              plateletWholeExtraction_variable=s.PlateletWholeExtractionVariableOfScenario,
                              nodesofscenario=s.NodesOfScenario) for s in scenarioset]
        if Constants.Debug: print("------------Moving BACK from 'Scenario' class (Constructor) to 'ScenarioTree' Class ('GetAllScenarios' Function)---------------")

        if Constants.Debug: print("------------Moving from 'ScenarioTree' Class ('GetAllScenarios' Function) to 'Scenario' class ('DisplayScenario' Function)---------------")
        if Constants.Debug:
            for scenario in scenarios:
                scenario.DisplayScenario()        
        if Constants.Debug: print("------------Moving Back from 'Scenario' class ('DisplayScenario' Function) to 'ScenarioTree' Class ('GetAllScenarios' Function)---------------")

        id = 0
        for s in scenarios:
            s.ScenarioId = id
            id = id + 1
        
        return scenarios
    
    def Print_Attributes(self):
        if Constants.Debug: 
            print("\n We are in 'ScenarioTree' Class -- Print_Attributes")
            print("\n------")
            print(f"CopyscenariofromMulti_Stage: {self.CopyscenariofromMulti_Stage}")
            print(f"Seed: {self.Seed}")
            print(f"TreeStructure: {self.TreeStructure}")
            print(f"NrBranches: {self.NrBranches}")
            print(f"EvaluationScenrio: {self.EvaluationScenrio}")
            print(f"AverageScenarioTree: {self.AverageScenarioTree}")
            print(f"ScenarioGenerationMethod: {self.ScenarioGenerationMethod}")
            print(f"Generateas_Two_Stage: {self.Generateas_Two_Stage}")
            print(f"Distribution: {self.Distribution}")
            print(f"DemandToFollow: {self.DemandToFollow}")
            print(f"IsSymetric: {self.IsSymetric}")
            print(f"Demand_TwoStage_RQMC: {self.Demand_TwoStage_RQMC}")
            print(f"Model: {self.Model}")
            print(f"GenerateRQMCForTwoStage: {self.GenerateRQMCForTwoStage}")
            print("------\n")    
        
    #This function set the variables at each node of the tree as found in the solution given in argument
    def FillApheresisAndPlateletToSendFromCRPSolution(self, sol):
        if Constants.Debug: print("\n We are in 'ScenarioTree' Class -- FillApheresisAndPlateletToSendFromCRPSolution")

        scenarionr = -1
        for n in self.Nodes:
            if n.Time >= 0 and  n.Time < self.Instance.NrTimeBucket:
                scenarionr = n.OneOfScenario.ScenarioId
                
                ##########################
                n.ApheresisToAssignNextTime = [sol.ApheresisAssignment_y_wti[scenarionr][n.Time][i]
                                                for i in self.Instance.ACFPPointSet]
                #if Constants.Debug: print("n.ApheresisToAssignNextTime: ", n.ApheresisToAssignNextTime)
                
                ##########################
                n.QuantityToTransshipHINextTime = [[[[sol.TransshipmentHI_b_wtcrhi[scenarionr][n.Time][c][r][h][i]
                                                    for i in self.Instance.ACFPPointSet]
                                                    for h in self.Instance.HospitalSet]
                                                    for r in self.Instance.PlateletAgeSet]
                                                    for c in self.Instance.BloodGPSet]
                #if Constants.Debug: print("n.QuantityToTransshipHINextTime: ", n.QuantityToTransshipHINextTime)
                
                ##########################
                n.QuantityToTransshipIINextTime = [[[[sol.TransshipmentII_bPrime_wtcrii[scenarionr][n.Time][c][r][i][iprime]
                                                    for iprime in self.Instance.ACFPPointSet]
                                                    for i in self.Instance.ACFPPointSet]
                                                    for r in self.Instance.PlateletAgeSet]
                                                    for c in self.Instance.BloodGPSet]
                #if Constants.Debug: print("n.QuantityToTransshipIINextTime: ", n.QuantityToTransshipIINextTime)
                
                ##########################
                n.QuantityToTransshipHHNextTime = [[[[sol.TransshipmentHH_bDoublePrime_wtcrhh[scenarionr][n.Time][c][r][h][hprime]
                                                    for hprime in self.Instance.HospitalSet]
                                                    for h in self.Instance.HospitalSet]
                                                    for r in self.Instance.PlateletAgeSet]
                                                    for c in self.Instance.BloodGPSet]
                #if Constants.Debug: print("n.QuantityToTransshipHHNextTime: ", n.QuantityToTransshipHHNextTime)
                

                if n.Time >= 1:
                    ##########################
                    n.PatientToTransferTime = [[[[[sol.PatientTransfer_q_wtjclum[scenarionr][n.Time-1][j][c][l][u][m]
                                                        for m in self.Instance.RescueVehicleSet]
                                                        for u in self.Instance.FacilitySet]
                                                        for l in self.Instance.DemandSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for j in self.Instance.InjuryLevelSet]
                    #if Constants.Debug: print("n.PatientToTransferTime: ", n.PatientToTransferTime)
                    
                    ##########################
                    n.UnsatisfiedPatientTime = [[[sol.UnsatisfiedPatient_mu_wtjcl[scenarionr][n.Time-1][j][c][l]
                                                        for l in self.Instance.DemandSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for j in self.Instance.InjuryLevelSet]
                    #if Constants.Debug: print("n.UnsatisfiedPatientTime: ", n.UnsatisfiedPatientTime)

                    ##########################
                    n.PlateletInventoryTime = [[[sol.PlateletInventory_eta_wtcru[scenarionr][n.Time-1][c][r][u]
                                                        for u in self.Instance.FacilitySet]
                                                        for r in self.Instance.PlateletAgeSet]
                                                        for c in self.Instance.BloodGPSet]
                    #if Constants.Debug: print("n.PlateletInventoryTime: ", n.PlateletInventoryTime)

                    ##########################
                    n.OutdatedPlateletsTime = [sol.OutdatedPlatelet_sigmavar_wtu[scenarionr][n.Time-1][u]
                                                        for u in self.Instance.FacilitySet]
                    #if Constants.Debug: print("n.OutdatedPlateletsTime: ", n.OutdatedPlateletsTime)

                    ##########################
                    n.ServedPatientsTime = [[[[[sol.ServedPatient_upsilon_wtjcPcru[scenarionr][n.Time-1][j][cprime][c][r][u]
                                                        for u in self.Instance.FacilitySet]
                                                        for r in self.Instance.PlateletAgeSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for cprime in self.Instance.BloodGPSet]
                                                        for j in self.Instance.InjuryLevelSet]
                    #if Constants.Debug: print("n.ServedPatientsTime: ", n.ServedPatientsTime)

                    ##########################
                    n.PostponnedPatientTime = [[[sol.PatientPostponement_zeta_wtjcu[scenarionr][n.Time-1][j][c][u]
                                                        for u in self.Instance.FacilitySet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for j in self.Instance.InjuryLevelSet]
                    #if Constants.Debug: print("n.PostponnedPatientTime: ", n.PostponnedPatientTime)
                    
                    ##########################
                    n.ApheresisExtractionTime = [[sol.PlateletApheresisExtraction_lambda_wtcu[scenarionr][n.Time-1][c][u]
                                                        for u in self.Instance.FacilitySet]
                                                        for c in self.Instance.BloodGPSet]
                    #if Constants.Debug: print("n.ApheresisExtractionTime: ", n.ApheresisExtractionTime)
                    
                    ##########################
                    n.WholeBloodExtractionTime = [[sol.PlateletWholeExtraction_Rhovar_wtch[scenarionr][n.Time-1][c][h]
                                                        for h in self.Instance.HospitalSet]
                                                        for c in self.Instance.BloodGPSet]
                    #if Constants.Debug: print("n.WholeBloodExtractionTime: ", n.WholeBloodExtractionTime)



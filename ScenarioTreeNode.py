import numpy as np
import math
from Constants import Constants
from Tool import Tool
from RQMCGenerator import RQMCGenerator
from scipy import stats
from scipy.stats import qmc, norm

class ScenarioTreeNode(object):
    #Count the number of node created
    NrNode = 0

    # This function create a node for the instance and time given in argument
    # The node is associated to the time given in paramter.
    # nr demand is the number of demand scenario fo
    def __init__(self, owner=None, parent=None, firstbranchid=0, instance=None, mipsolver=None, time=-1, nrbranch=-1,
                 demands=None, hospitalcaps=None, wholedonors=None, apheresisdonors=None, proabibilty=-1, averagescenariotree=False):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- Constructor")
        if owner is not None:
            owner.Nodes.append(self)
        self.Owner = owner
        self.Parent = parent
        if Constants.Debug: print("self.Parent: ",self.Parent)
        self.Instance = instance
        self.Branches = []

        # An identifier of the node
        self.NodeNumber = ScenarioTreeNode.NrNode
        #if Constants.Debug: print("self.NodeNumber: ",self.NodeNumber)
        ScenarioTreeNode.NrNode = ScenarioTreeNode.NrNode + 1
        if Constants.Debug: print("self.NrNode: ",ScenarioTreeNode.NrNode)
        self.FirstBranchID = firstbranchid
        self.Time = time
        
        self.CreateChildrens(nrbranch, averagescenariotree)
        # The probability associated with the node
        self.Probability = proabibilty
        if Constants.Debug: print("######## self.Probability: ",self.Probability)
        # The demand for each product associated with the node of the sceanrio
        self.Demand = demands
        self.HospitalCap = hospitalcaps
        self.WholeDonor = wholedonors
        self.ApheresisDonor = apheresisdonors
        
        # The attribute DemandsInParitalScenario contains all the demand since the beginning of the time horizon in the partial scenario
        self.DemandsInScenario = []  # will be built later
        self.HospitalCapsInScenario = []  # will be built later
        self.WholeDonorsInScenario = []  # will be built later
        self.ApheresisDonorsInScenario = []  # will be built later
        
        # The probability of the partial scenario ( take into account the paroability of parents )
        self.ProbabilityOfScenario = -1
        
        # The attribute below contains the index of the GRB variables associated with the node for each product at the relevant time.
        self.ACFEstablishmentVariable = []      # will be built later
        self.VehicleAssignmentVariable = []     # will be built later
        self.ApheresisAssignmentVariable = []   # will be built later
        self.TransshipmentHIVariable = []       # will be built later
        self.TransshipmentIIVariable = []       # will be built later
        self.TransshipmentHHVariable = []       # will be built later
        self.PatientTransferVariable = []              
        self.UnsatisfiedPatientsVariable = []   
        self.PlateletInventoryVariable = []              
        self.OutdatedPlateletVariable = []              
        self.ServedPatientVariable = []              
        self.PatientPostponementVariable = []              
        self.PlateletApheresisExtractionVariable = []              
        self.PlateletWholeExtractionVariable = []              

        # The attributes below contain the list of variable for all time period of the scenario
        self.ACFEstablishmentVariableOfScenario = []  # will be built later
        self.VehicleAssignmentVariableOfScenario = []  # will be built later
        self.ApheresisAssignmentVariableOfScenario = [] # will be built later
        self.TransshipmentHIVariableOfScenario = [] # will be built later
        self.TransshipmentIIVariableOfScenario = [] # will be built later
        self.TransshipmentHHVariableOfScenario = [] # will be built later
        self.PatientTransferVariableOfScenario = []              
        self.UnsatisfiedPatientsVariableOfScenario = []   
        self.PlateletInventoryVariableOfScenario = []              
        self.OutdatedPlateletVariableOfScenario = []              
        self.ServedPatientVariableOfScenario = []              
        self.PatientPostponementVariableOfScenario = []              
        self.PlateletApheresisExtractionVariableOfScenario = []              
        self.PlateletWholeExtractionVariableOfScenario = [] 
        
        self.NodesOfScenario = []  # will be built later
        self.Scenarios = []
        self.OneOfScenario = None   
        if Constants.Debug: print("OneOfScenario:", self.OneOfScenario) 

    # This function creates the children of the current node
    def CreateChildrens(self,  nrbranch, averagescenariotree):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- CreateChildrens")
        if Constants.Debug: print(f"nrbranch = {nrbranch}, averagescenariotree = {averagescenariotree}")
        #Record the value of the first branch (this is used to copy the scenario in the tree)
        if self.Time > 1:
            self.FirstBranchID = self.Parent.FirstBranchID

        t = self.Time + 1 
        
        if Constants.Debug: print("t before IF:",t)
        if self.Instance is not None and t < self.Instance.NrTimeBucket:
            if Constants.Debug: print("Instance is not None and t is within the number of time buckets")

            # #Generate the scenario for the branches of the node
            nrscneartoconsider = max(self.Owner.NrBranches[t], 1)
            if Constants.Debug: print(f"nrscneartoconsider for time t={t}:", nrscneartoconsider)

            probabilities = [(1.0 / nrscneartoconsider) for b in range(nrscneartoconsider)]
            if Constants.Debug: print("Initial probabilities set:", probabilities)
           
            if t < 0:
                nextdemands = self.GetDemandRQMCForTwoStage(t, self.Owner.NrBranches[t],  self.FirstBranchID )
                probabilities = [(1.0 / nrscneartoconsider) for b in range(nrscneartoconsider)]
                
                # nextdemands = self.Owner.SymetricDemand[t]
                # if Constants.Debug: print(f"nextdemands  at t={t}: ", nextdemands)
                # probabilities = self.Owner.SymetricProba[t]                                
                # if Constants.Debug: print(f"probabilities at t={t}:", probabilities)

                # nextdemands = []
                # probabilities = [1]                
            else:
                
                if Constants.Debug: print("Time t is greater than 0, following logic for demands")
                #case 1: the tree should copy the scenarios generated with QMC/RQMC for the two stage model
                if (Constants.IsQMCMethos(self.Owner.ScenarioGenerationMethod)
                        and self.Owner.GenerateRQMCForTwoStage
                        #and not averagescenariotree
                        and not self.Time >= (self.Instance.NrTimeBucket)):
                    if Constants.Debug: print("case 1: the tree should copy the scenarios generated with QMC/RQMC for the two stage model")
                    nextdemands = self.GetDemandRQMCForTwoStage(t, nrbranch,  self.FirstBranchID )                    
                    nexthospitalcaps = self.GetHospitalCapRQMCForTwoStage(t, nrbranch,  self.FirstBranchID )
                    nextwholedonors = self.GetWholeDonorRQMCForTwoStage(t, nrbranch,  self.FirstBranchID )
                    nextapheresisdonors = self.GetApheresisDonorRQMCForTwoStage(t, nrbranch,  self.FirstBranchID )
                # case 3: the tree of a two-stage model contains all the scenario of a multi-stage tree
                elif self.Owner.CopyscenariofromMulti_Stage or (self.Owner.ScenarioGenerationMethod == Constants.All and self.Owner.Model == Constants.Two_Stage):
                    if Constants.Debug: print("case 3: the tree of a two-stage model contains all the scenario of a multi-stage tree")
                    #nextdemands, probabilities = self.GetDemandToFollowMultipleScenarios(t - 1, nrbranch,  self.FirstBranchID )
                    nextdemands, probabilities = self.GetDemandToFollowMultipleScenarios(t, nrbranch, self.FirstBranchID)
                    nexthospitalcaps, probabilities0 = self.GetHospitalCapToFollowMultipleScenarios(t, nrbranch, self.FirstBranchID)
                    nextwholedonors, probabilities00 = self.GetWholeDonorToFollowMultipleScenarios(t, nrbranch, self.FirstBranchID)
                    nextapheresisdonors, probabilities000 = self.GetApheresisDonorToFollowMultipleScenarios(t, nrbranch, self.FirstBranchID)
                    if Constants.Debug:
                        print("nextdemands:\n ", nextdemands)                    
                        print("nexthospitalcaps:\n ", nexthospitalcaps)                    
                        print("nextwholedonors:\n ", nextwholedonors)                    
                        print("nextapheresisdonors:\n ", nextapheresisdonors)                    
                        print("probabilities: ", probabilities)
                        print("-----")
                # case 4: Sample a set of scenario for the next stage
                elif self.Owner.IsSymetric:
                    
                    if Constants.Debug: print("case 4: Sample a set of scenario for the next stage")
                    nextdemands = self.Owner.SymetricDemand[t]
                    nexthospitalcaps = self.Owner.SymetricHospitalCapacity[t]
                    nextwholedonors = self.Owner.SymetricWholeDonor[t]
                    nextapheresisdonors = self.Owner.SymetricApheresisDonor[t]
                    
                    probabilities = self.Owner.SymetricProba[t]
                else:
                    if Constants.Debug: print("averagescenariotree: ", averagescenariotree)
                    if Constants.Debug: print("case 5: using 'CreateDemandNormalDistributiondemand' function")
                    nextdemands, probabilities = ScenarioTreeNode.CreateDemandNormalDistributiondemand(self.Instance, t, nrbranch, averagescenariotree, self.Owner.ScenarioGenerationMethod)
                    nexthospitalcaps, probabilitieshospital = ScenarioTreeNode.CreateHospitalCapNormalDistribution(self.Instance, t, nrbranch, averagescenariotree, self.Owner.ScenarioGenerationMethod)
                    nextwholedonors, probabilitieswholedonor = ScenarioTreeNode.CreateWholeDonorNormalDistribution(self.Instance, t, nrbranch, averagescenariotree, self.Owner.ScenarioGenerationMethod)
                    nextapheresisdonors, Probabilitiesapheresisdonor = ScenarioTreeNode.CreateApheresisDonorNormalDistribution(self.Instance, t, nrbranch, averagescenariotree, self.Owner.ScenarioGenerationMethod)

            #Use the sample to create the new branches

            if len(nextdemands) > 0:
                nrbranch = len(nexthospitalcaps[0])      # Here I aim to obtain the number of branches from this node, based on the valued already generated for the next nodes
                self.Owner.NrBranches[t] = nrbranch
                self.Owner.TreeStructure[t] = nrbranch

            if Constants.Debug: print(f"self.Owner.TreeStructure[t={t}]: ",self.Owner.TreeStructure[t])
            usaverageforbranch = (t >= self.Instance.NrTimeBucket) or self.Owner.AverageScenarioTree

            nextfirstbranchid = [self.FirstBranchID for b in range(nrbranch)]
            if t == 0:
                nextfirstbranchid = [b for b in range(nrbranch)]
            
            if Constants.Debug:
                print("\n---------------------------------------1")
                print("time: ", t)
                print("nrbranch: ",nrbranch)
                print("nextfirstbranchid: ",nextfirstbranchid)
                print("nrscneartoconsider: ",nrscneartoconsider)
                print("probabilities: ",probabilities)
                print("nextdemands: ",nextdemands)
                print("nexthospitalcaps: ",nexthospitalcaps)
                print("nextwholedonors: ",nextwholedonors)
                print("nextapheresisdonors: ",nextapheresisdonors)
                print("usaverageforbranch: ",usaverageforbranch)
                print("---------------------------------------2\n")
            
            self.Branches = [ScenarioTreeNode(owner=self.Owner,
                                              parent=self,
                                              firstbranchid=nextfirstbranchid[b],
                                              instance=self.Instance,
                                              time=t,
                                              nrbranch=self.Owner.NrBranches[t],
                                              demands = [[[nextdemands[j][c][l][b] 
                                                           for l in self.Instance.DemandSet if t >= 0] 
                                                           for c in self.Instance.BloodGPSet] 
                                                           for j in self.Instance.InjuryLevelSet],
                                              hospitalcaps=[nexthospitalcaps[h][b] 
                                                            for h in self.Instance.HospitalSet if t >= 0],
                                              wholedonors = [[nextwholedonors[c][h][b] 
                                                              for h in self.Instance.HospitalSet if t >= 0] 
                                                              for c in self.Instance.BloodGPSet],
                                              apheresisdonors = [[nextapheresisdonors[c][u][b] 
                                                                  for u in self.Instance.FacilitySet if t >= 0] 
                                                                  for c in self.Instance.BloodGPSet],
                                              proabibilty=probabilities[b],
                                              averagescenariotree=usaverageforbranch) for b in range(nrbranch)]
            if Constants.Debug: print("---------------------------------------3\n")

    #This function is used when the demand is gereqated using RQMC for Two_Stage Model
    #Return the demands  at time at position nrdemand in array Demand_TwoStage_RQMC
    def GetDemandRQMCForTwoStage( self, time, nrdemand, firstbranchid ):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- GetDemandRQMCForTwoStage")
        
        TotalNumberofSenarios_in_TwoStage_Model = len(self.Owner.Demand_TwoStage_RQMC)

        if time==0:
            demandvector = [[[[self.Owner.Demand_TwoStage_RQMC[firstbranchid + i][time][j][c][l]
                            for i in range(TotalNumberofSenarios_in_TwoStage_Model)]
                            for l in self.Instance.DemandSet]
                            for c in self.Instance.BloodGPSet]
                            for j in self.Instance.InjuryLevelSet]
        else:
            demandvector = [[[[self.Owner.Demand_TwoStage_RQMC[firstbranchid + i][time][j][c][l]
                            for i in range(1)]
                            for l in self.Instance.DemandSet]
                            for c in self.Instance.BloodGPSet]
                            for j in self.Instance.InjuryLevelSet]       
        if Constants.Debug: print("demandvector: ", demandvector)   
        return demandvector
    
    #This function is used when the Hospital Capacity is gereqated using RQMC for Two_Stage Model
    #Return the demands  at time at position nrdemand in array HospitalCap_TwoStage_RQMC
    def GetHospitalCapRQMCForTwoStage( self, time, nrdemand, firstbranchid ):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- GetHospitalCapRQMCForTwoStage")
        
        TotalNumberofSenarios_in_TwoStage_Model = len(self.Owner.HospitalCap_TwoStage_RQMC)

        if time==0:
            hospitalvector = [[self.Owner.HospitalCap_TwoStage_RQMC[firstbranchid + i][time][h]
                            for i in range(TotalNumberofSenarios_in_TwoStage_Model)]
                            for h in self.Instance.HospitalSet]
        else:
            hospitalvector = [[self.Owner.HospitalCap_TwoStage_RQMC[firstbranchid + i][time][h]
                            for i in range(1)]
                            for h in self.Instance.HospitalSet]            
        return hospitalvector
        
    #This function is used when the demand is gereqated using RQMC for Two_Stage Model
    #Return the demands  at time at position nrdemand in array WholeDonor_TwoStage_RQMC
    def GetWholeDonorRQMCForTwoStage( self, time, nrdemand, firstbranchid ):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- GetWholeDonorRQMCForTwoStage")
        
        TotalNumberofSenarios_in_TwoStage_Model = len(self.Owner.WholeDonor_TwoStage_RQMC)

        if time==0:
            wholedonorvector = [[[self.Owner.WholeDonor_TwoStage_RQMC[firstbranchid + i][time][c][h]
                                    for i in range(TotalNumberofSenarios_in_TwoStage_Model)]
                                    for h in self.Instance.HospitalSet]
                                    for c in self.Instance.BloodGPSet]
        else:
            wholedonorvector = [[[self.Owner.WholeDonor_TwoStage_RQMC[firstbranchid + i][time][c][h]
                                    for i in range(1)]
                                    for h in self.Instance.HospitalSet]
                                    for c in self.Instance.BloodGPSet]        
        return wholedonorvector
    
    #This function is used when the demand is gereqated using RQMC for Two_Stage Model
    #Return the demands  at time at position nrdemand in array ApheresisDonor_TwoStage_RQMC
    def GetApheresisDonorRQMCForTwoStage( self, time, nrdemand, firstbranchid ):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- GetApheresisDonorRQMCForTwoStage")
        
        TotalNumberofSenarios_in_TwoStage_Model = len(self.Owner.ApheresisDonor_TwoStage_RQMC)

        if time==0:
            apheresisdonorvector = [[[self.Owner.ApheresisDonor_TwoStage_RQMC[firstbranchid + i][time][c][u]
                                        for i in range(TotalNumberofSenarios_in_TwoStage_Model)]
                                        for u in self.Instance.FacilitySet]
                                        for c in self.Instance.BloodGPSet]
        else:
            apheresisdonorvector = [[[self.Owner.ApheresisDonor_TwoStage_RQMC[firstbranchid + i][time][c][u]
                                        for i in range(1)]
                                        for u in self.Instance.FacilitySet]
                                        for c in self.Instance.BloodGPSet]  
                 
        return apheresisdonorvector

    #This function is used To generate a set of scenario in Two_Stage which must follow given demand and Probability
    def GetDemandToFollowMultipleScenarios(self, time, nrdemand, firstbranchid):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- GetDemandToFollowMultipleScenarios")

        if Constants.Debug: print("self.Owner.DemandToFollowMultipleSceario: ", self.Owner.DemandToFollowMultipleSceario)
        demandvector = [[[[self.Owner.DemandToFollowMultipleSceario[firstbranchid + i][time][j][c][l]
                             for i in range(nrdemand)]
                            for l in self.Instance.DemandSet]
                            for c in self.Instance.BloodGPSet]
                            for j in self.Instance.InjuryLevelSet]
        if Constants.Debug: print("demandvector: ", demandvector)
        probability = [1 for i in range(nrdemand)]
        if time == 0:
                probability = [self.Owner.ProbabilityToFollowMultipleSceario[i] for i in range(nrdemand)]

        return demandvector, probability
    
    #This function is used To generate a set of scenario in Two_Stage which must follow given HospitalCap 
    def GetHospitalCapToFollowMultipleScenarios(self, time, nrdemand, firstbranchid):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- GetHospitalCapToFollowMultipleScenarios")

        hospitalvector = [[self.Owner.HospitalCapToFollowMultipleSceario[firstbranchid + i][time][h]
                                for i in range(nrdemand)]
                                for h in self.Instance.HospitalSet]
        if Constants.Debug: print("hospitalvector: ", hospitalvector)
        probability = [1 for i in range(nrdemand)]
        #if time == 0:
                #probability = [self.Owner.ProbabilityToFollowMultipleSceario[i] for i in range(nrdemand)]
        return hospitalvector, probability
    
    #This function is used To generate a set of scenario in Two_Stage which must follow given WholeDonor 
    def GetWholeDonorToFollowMultipleScenarios(self, time, nrdemand, firstbranchid):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- GetWholeDonorToFollowMultipleScenarios")

        wholedonorvector = [[[self.Owner.WholeDonorToFollowMultipleSceario[firstbranchid + i][time][c][h]
                                for i in range(nrdemand)]
                                for h in self.Instance.HospitalSet]
                                for c in self.Instance.BloodGPSet]
        if Constants.Debug: print("wholedonorvector: ", wholedonorvector)
        probability = [1 for i in range(nrdemand)]
        #if time == 0:
                #probability = [self.Owner.ProbabilityToFollowMultipleSceario[i] for i in range(nrdemand)]
        return wholedonorvector, probability
    
    #This function is used To generate a set of scenario in Two_Stage which must follow given ApheresisDonor 
    def GetApheresisDonorToFollowMultipleScenarios(self, time, nrdemand, firstbranchid):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- GetApheresisDonorToFollowMultipleScenarios")

        apheresisdonorvector = [[[self.Owner.ApheresisDonorToFollowMultipleSceario[firstbranchid + i][time][c][u]
                                for i in range(nrdemand)]
                                for u in self.Instance.FacilitySet]
                                for c in self.Instance.BloodGPSet]
        if Constants.Debug: print("apheresisdonorvector: ", apheresisdonorvector)
        probability = [1 for i in range(nrdemand)]
        #if time == 0:
                #probability = [self.Owner.ProbabilityToFollowMultipleSceario[i] for i in range(nrdemand)]
        return apheresisdonorvector, probability
        
    # Apply the inverse of the given distribution for each point (generated in [0,1]) in the set.
    @staticmethod
    def TransformInverse( points, nrpoints, dimensionpoint, distribution, average, std = 0 ):

        if Constants.Debug:
            print("points: ", points)
            print("nrpoints: ", nrpoints)
            print("dimensionpoint: ", dimensionpoint)
            print("distribution: ", distribution)
            print("average: ", average)
            print("std: ", std)
            print("GeneratingHospitalUncertainCapacity: ", Constants.GeneratingHospitalUncertainCapacity)

        result = []
        if distribution == Constants.NonStationary:
            if Constants.Debug: print("Distribution is: NonStationary")
            for p in range(dimensionpoint):
                if std[p] > 0:
                    column = []
                    for i in range(nrpoints):
                        prob = points[i][p]
                        # Ensure probability is strictly between 0 and 1
                        inv_value = stats.norm.ppf(prob, average[p], std[p])
                        # Floor and ensure non-negative result
                        column.append(float(max(np.round(inv_value), 0.0)))
                    result.append(column)
                else:
                    # Handle the zero standard deviation case
                    result.append([float(average[p])] * nrpoints)  # Repeat the average as the fixed value
        
        if distribution == Constants.Uniform:
            if Constants.Debug: print("Distribution is: Uniform")

            if Constants.GeneratingHospitalUncertainCapacity == False:
                for p in range(dimensionpoint):
                    if std[p] > 0:
                        column = []
                        for i in range(nrpoints):
                            prob = points[i][p]
                            # Generate a value uniformly between (average - std) and (average + std)
                            uniform_value = (average[p] - std[p]) + prob * 2 * std[p]
                            #uniform_value = stats.uniform.ppf(prob, average[p] - std[p], 2 * std[p])
                            # Ensure the result is non-negative
                            column.append(float(max(np.ceil(uniform_value), 0.0)))
                        result.append(column)
                    else:
                        # Handle the zero standard deviation case
                        result.append([float(average[p])] * nrpoints)  # Repeat the average as the fixed value
            else:
                for p in range(dimensionpoint):
                    if std[p] > 0:
                        column = []
                        for i in range(nrpoints):
                            prob = points[i][p]
                            # Generate a value uniformly between (average - std) and (average + std)
                            uniform_value = (average[p] - std[p]) + prob * 1 * std[p]
                            #uniform_value = stats.uniform.ppf(prob, average[p] - std[p], std[p])
                            # Ensure the result is non-negative
                            column.append(float(max(np.ceil(uniform_value), 0.0)))
                        result.append(column)
                    else:
                        # Handle the zero standard deviation case
                        result.append([float(average[p])] * nrpoints)  # Repeat the average as the fixed value

        if distribution == Constants.Normal:
            if Constants.Debug: print("Distribution is: Normal")

            if Constants.GeneratingHospitalUncertainCapacity == False:
                for p in range(dimensionpoint):
                    if std[p] > 0:
                        column = []
                        for i in range(nrpoints):
                            prob = points[i][p]
                            # Generate a value using the inverse CDF of the normal distribution
                            normal_value = norm.ppf(prob, loc=average[p], scale=std[p])
                            # Ensure the result is non-negative
                            column.append(float(max(np.ceil(normal_value), 0.0)))
                        result.append(column)
                    else:
                        # Handle the zero standard deviation case
                        result.append([float(average[p])] * nrpoints)  # Repeat the average as the fixed value
            else:
                for p in range(dimensionpoint):
                    if std[p] > 0:
                        column = []
                        for i in range(nrpoints):
                            prob = points[i][p]
                            # Generate a value using the inverse CDF of the normal distribution and then truncate to the range [average - std, average]
                            normal_value = norm.ppf(prob * 0.5 + 0.5, loc=average[p] - std[p] / 2, scale=std[p] / 2)
                            # Ensure the result is non-negative
                            column.append(float(max(np.ceil(normal_value), 0.0)))
                        result.append(column)
                    else:
                        # Handle the zero standard deviation case
                        result.append([float(average[p])] * nrpoints)  # Repeat the average as the fixed value
                            
        if distribution == Constants.Binomial:
            if Constants.Debug: print("Distribution is: Binomial")
            n = 7
            prob = 0.5
            result = [[stats.binom.ppf(points[i][p], n, prob) for i in range(nrpoints)] for p in range(dimensionpoint)]

        if distribution == Constants.SlowMoving:
            if Constants.Debug: print("Distribution is: SlowMoving")
            result = [[stats.poisson.ppf(points[i][p], average[p]) for i in range(nrpoints)] for p in range(dimensionpoint)]
        
        if distribution == Constants.Lumpy:
            if Constants.Debug: print("Distribution is: Lumpy")
            result = [[stats.poisson.ppf((points[i][p] - 0.5) / 0.5, (average[p]) / 0.5) + 1 if points[i][p] > 0.5 else 0 for i in range(nrpoints)] for p in range(dimensionpoint)]

        if Constants.Debug: print("result: ",result)
        return result    

    #This method aggregate the points with same value and update the prbability accordingly
    @staticmethod
    def Aggregate(points, probabilities):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- Aggregate")

       # get the set of difflerent value in points
        if Constants.RQMCAggregate:
            newpoints = points

            #newprobaba = probabilities
            newpoints = map(list, zip(*newpoints))
            newpoints = list(set(map(tuple,newpoints)))
            #
            newpoints = [list(t) for t in newpoints]
            tpoint = map(list, zip(*points))
            newprobaba = [sum(probabilities[i] for i in range(len(tpoint)) if tpoint[i] == newpoints[p]) for p in range(len(newpoints))]


            newpoints = map(list, zip(*newpoints))

            return newpoints, newprobaba
        else:
            return points, probabilities
        
    #This method generate a set of nrpoint according to the method and given distribution.
    @staticmethod
    def GeneratePoints(method, nrpoints, dimensionpoint, distribution, average, std=[]):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- GeneratePoints")
    
        sampler = None
        probability = None
        points = []
        
        # In monte Carlo, each point as the same probability
        if method == Constants.MonteCarlo:
            if distribution == Constants.NonStationary or Constants.Uniform:
                # Direct sampling for MC, assuming normal distribution for simplicity
                points = [np.floor(np.random.normal(average[p], std[p], nrpoints).clip(min=0.0)).tolist()
                                     if std[p] > 0 else [float(average[p])] * nrpoints
                                     for p in range(dimensionpoint)]
                probability = [1.0 / nrpoints] * nrpoints
                        
        # Generate the points using RQMC
        if method == Constants.RQMC or method == Constants.QMC:
            if Constants.Debug: print("The method is RQMC or QMC")
            newnrpoints = nrpoints
            nextdemands = [[]]
            nrnonzero = 0
            #The method continue to generate points until to have n distinct points
            while len(nextdemands[0]) < nrpoints and newnrpoints <= 100000000:
                if Constants.Debug and len(nextdemands[0]) > 0:
                    print("try with %r points because only %r points were generated, required: %r" % (newnrpoints, len(nextdemands[0]), nrpoints))
                points = [[0.0 for pt in range(newnrpoints)] for p in range(dimensionpoint)]
                nrnonzero = sum(1 for p in range(dimensionpoint) if average[p] > 0)
                idnonzero = [p for p in range(dimensionpoint) if average[p] > 0]
                avg = [average[d] for d in idnonzero]
                stddev = [std[d] for d in idnonzero]
                
                pointsin01 = RQMCGenerator.RQMC01(newnrpoints, nrnonzero, withweight=False, QMC=(method == Constants.QMC), sequence_type = Constants.SequenceTypee)
                # print("Length of pointsin01: ", len(pointsin01))
                # print("Length of pointsin01: ", len(pointsin01[0]))
                # print("pointsin01:\n ", pointsin01)
                
                rqmcpoints = ScenarioTreeNode.TransformInverse(pointsin01, newnrpoints, nrnonzero, distribution, avg, stddev)
                # print("rqmcpoints:\n", rqmcpoints)
                # print("-------------")
                for p in range(nrnonzero): 
                        for i in range(newnrpoints):
                            points[idnonzero[p]][i] = float(np.round(rqmcpoints[p][i], 0))

                nextdemands, probability = ScenarioTreeNode.Aggregate(rqmcpoints, [1.0 / max(newnrpoints, 1) for pt in range(max(newnrpoints, 1))])

                if len(nextdemands[0]) < nrpoints:
                    newnrpoints = newnrpoints + 1
                rqmcpoints = nextdemands

            if probability is None:
                probability = [1/nrpoints for pt in range(nrpoints)]

            nrpoints = min(len(nextdemands[0]), nrpoints)
            points = [[0.0 for pt in range(nrpoints)] for p in range(dimensionpoint)]

            for p in range(nrnonzero):  # instance.ProductWithExternalDemand:
                        for i in range(nrpoints):
                            points[idnonzero[p]][i]= float (np.round(rqmcpoints[p][i], 0))

        # print("points:\n ", points)
        # print("probability:\n", probability)
        
        return points, probability
 
    #Create the demand in a node following a normal distribution
    @staticmethod
    def CreateDemandNormalDistributiondemand(instance, time, nrscenario, average=False, scenariogenerationmethod=Constants.MonteCarlo):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- CreateDemandNormalDistributiondemand")

        demandvector = [[[[float(instance.ForecastedAverageDemand[time][j][c][l]) 
                           for s in range(nrscenario)] 
                            for l in instance.DemandSet] 
                            for c in instance.BloodGPSet] 
                            for j in instance.InjuryLevelSet]

        probability = [float(1.0 / max(nrscenario, 1)) for i in range(max(nrscenario, 1))]

        if not average and nrscenario > 0:
            points, probability = ScenarioTreeNode.GeneratePoints(method=scenariogenerationmethod,
                                                                    nrpoints=nrscenario,
                                                                    dimensionpoint=len(instance.InjuryLevelSet)*len(instance.BloodGPSet)*len(instance.DemandSet),
                                                                    distribution=instance.Distribution,
                                                                    average=[instance.ForecastedAverageDemand[time][j][c][l] 
                                                                        for j in instance.InjuryLevelSet 
                                                                        for c in instance.BloodGPSet 
                                                                        for l in instance.DemandSet],
                                                                    std=[instance.ForecastedStandardDeviationDemand[time][j][c][l] 
                                                                        for j in instance.InjuryLevelSet 
                                                                        for c in instance.BloodGPSet 
                                                                        for l in instance.DemandSet])

            resultingnrpoints = len(points[0])

            for i in range(resultingnrpoints):
                idx = 0
                for j in instance.InjuryLevelSet:
                    for c in instance.BloodGPSet:
                        for l in instance.DemandSet:
                            demandvector[j][c][l][i] = points[idx][i]
                            idx += 1

        return demandvector, probability
    
    #Create the Hospital Treatment Capacity in a node following a normal distribution
    @staticmethod
    def CreateHospitalCapNormalDistribution(instance, time, nrscenario, average=False, scenariogenerationmethod=Constants.MonteCarlo):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- CreateHospitalCapNormalDistribution")
        Constants.GeneratingHospitalUncertainCapacity = True
        
        hospitalvector = [[float(instance.ForecastedAverageHospital_Bed_Capacity[time][h]) 
                           for s in range(nrscenario)]  
                           for h in instance.HospitalSet]

        probability = [float(1.0 / max(nrscenario, 1)) for i in range(max(nrscenario, 1))]

        if not average and nrscenario > 0:
            points, probability = ScenarioTreeNode.GeneratePoints(method=scenariogenerationmethod,
                                                                    nrpoints=nrscenario,
                                                                    dimensionpoint=len(instance.HospitalSet),
                                                                    distribution=instance.Distribution,
                                                                    average=[instance.ForecastedAverageHospital_Bed_Capacity[time][h] for h in instance.HospitalSet],
                                                                    std=[instance.ForecastedSTDHospital_Bed_Capacity[time][h] for h in instance.HospitalSet]) 

            resultingnrpoints = len(points[0])

            for i in range(resultingnrpoints):
                idx = 0
                for h in instance.HospitalSet:
                    hospitalvector[h][i] = points[idx][i]
                    idx += 1
        
        Constants.GeneratingHospitalUncertainCapacity = False
        return hospitalvector, probability

    #Create the Whole Blood Donors in a node following a normal distribution
    @staticmethod
    def CreateWholeDonorNormalDistribution(instance, time, nrscenario, average=False, scenariogenerationmethod=Constants.MonteCarlo):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- CreateWholeDonorNormalDistribution")
        
        wholedonorvector = [[[float(instance.ForecastedAverageWhole_Blood_Donors[time][c][h]) for s in range(nrscenario)] 
                        for h in instance.HospitalSet] for c in instance.BloodGPSet]

        probability = [float(1.0 / max(nrscenario, 1)) for i in range(max(nrscenario, 1))]

        if not average and nrscenario > 0:
            points, probability = ScenarioTreeNode.GeneratePoints(method=scenariogenerationmethod,
                                                                    nrpoints=nrscenario,
                                                                    dimensionpoint=len(instance.BloodGPSet)*len(instance.HospitalSet),
                                                                    distribution=instance.Distribution,
                                                                    average=[instance.ForecastedAverageWhole_Blood_Donors[time][c][h] 
                                                                        for c in instance.BloodGPSet 
                                                                        for h in instance.HospitalSet],
                                                                    std=[instance.ForecastedSTDWhole_Blood_Donors[time][c][h] 
                                                                        for c in instance.BloodGPSet 
                                                                        for h in instance.HospitalSet])

            resultingnrpoints = len(points[0])

            for i in range(resultingnrpoints):
                idx = 0
                for c in instance.BloodGPSet:
                    for h in instance.HospitalSet:
                        wholedonorvector[c][h][i] = points[idx][i]
                        idx += 1
        return wholedonorvector, probability
    
    #Create the Whole Blood Donors in a node following a normal distribution
    @staticmethod
    def CreateApheresisDonorNormalDistribution(instance, time, nrscenario, average=False, scenariogenerationmethod=Constants.MonteCarlo):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- CreateApheresisDonorNormalDistribution")
        
        apheresisdonorvector = [[[float(instance.ForecastedAverageApheresis_Donors[time][c][u]) for s in range(nrscenario)] 
                        for u in instance.FacilitySet] for c in instance.BloodGPSet]

        probability = [float(1.0 / max(nrscenario, 1)) for i in range(max(nrscenario, 1))]

        if not average and nrscenario > 0:
            points, probability = ScenarioTreeNode.GeneratePoints(method=scenariogenerationmethod,
                                                                    nrpoints=nrscenario,
                                                                    dimensionpoint=len(instance.BloodGPSet)*len(instance.FacilitySet),
                                                                    distribution=instance.Distribution,
                                                                    average=[instance.ForecastedAverageApheresis_Donors[time][c][u] 
                                                                                for c in instance.BloodGPSet 
                                                                                for u in instance.FacilitySet],
                                                                    std=[instance.ForecastedSTDApheresis_Donors[time][c][u] 
                                                                                for c in instance.BloodGPSet 
                                                                                for u in instance.FacilitySet])

            resultingnrpoints = len(points[0])

            for i in range(resultingnrpoints):
                idx = 0
                for c in instance.BloodGPSet:
                    for u in instance.FacilitySet:
                        apheresisdonorvector[c][u][i] = points[idx][i]
                        idx += 1

        return apheresisdonorvector, probability
        
    #This function compute the indices of the variables associated with each node of the tree
    def ComputeVariableIndex(self, expandfirststage = False, nrscenar = -1):
        #if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- ComputeVariableIndex")
        #if Constants.Debug: print("self.NodeNumber: ",self.NodeNumber)
        #if Constants.Debug: print("self.Time: ",self.Time)

        #With this combination, it gives us y_{sd}
        if self.NodeNumber == 0:
            
            #x_i
            self.ACFEstablishmentVariable = [self.Owner.Owner.StartACFEstablishmentVariables + i for i in self.Instance.ACFPPointSet]

            #thetaVar_mi
            self.VehicleAssignmentVariable = [[(self.Owner.Owner.StartVehicleAssignmentVariables 
                                                + self.Instance.NrRescueVehicles * (i) + m) 
                                                for i in self.Instance.ACFPPointSet]
                                                for m in self.Instance.RescueVehicleSet]

        #if Constants.Debug: print("ACFEstablishmentVariable indices:\n", self.ACFEstablishmentVariable)
        #if Constants.Debug: print("VehicleAssignmentVariable indices:\n", self.VehicleAssignmentVariable)


        if self.Time >= 0:
            
            #y_i
            self.ApheresisAssignmentVariable = [
                (self.Owner.Owner.StartApheresisAssignmentVariables
                + (self.Instance.NrACFPPoints * (self.NodeNumber - 1))
                + i)
                    for i in self.Instance.ACFPPointSet]       
            #if Constants.Debug: print("ApheresisAssignmentVariable indices:\n", self.ApheresisAssignmentVariable)

            #b_crhi
            self.TransshipmentHIVariable = [[[[
                            (self.Owner.Owner.StartTransshipmentHIVariables
                            + (self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrACFPPoints * (self.NodeNumber - 1))
                            + (c * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrACFPPoints)
                            + (r * self.Instance.NrHospitals * self.Instance.NrACFPPoints)
                            + (h * self.Instance.NrACFPPoints) + i)
                                for i in self.Instance.ACFPPointSet]
                                for h in self.Instance.HospitalSet]
                                for r in self.Instance.PlateletAgeSet]
                                for c in self.Instance.BloodGPSet]
            #if Constants.Debug: print("TransshipmentHIVariable indices:\n", self.TransshipmentHIVariable)
            
            #b'_crii'
            self.TransshipmentIIVariable = [[[[
                            (self.Owner.Owner.StartTransshipmentIIVariables
                            + (self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints * (self.NodeNumber - 1))
                            + (c * self.Instance.NRPlateletAges * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints)
                            + (r * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints)
                            + (i * self.Instance.NrACFPPoints) + iprime)
                                for iprime in self.Instance.ACFPPointSet]
                                for i in self.Instance.ACFPPointSet]
                                for r in self.Instance.PlateletAgeSet]
                                for c in self.Instance.BloodGPSet]
            #if Constants.Debug: print("TransshipmentIIVariable indices:\n", self.TransshipmentIIVariable)

            #b''_crhh'
            self.TransshipmentHHVariable = [[[[
                            (self.Owner.Owner.StartTransshipmentHHVariables
                            + (self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrHospitals * (self.NodeNumber - 1))
                            + (c * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrHospitals)
                            + (r * self.Instance.NrHospitals * self.Instance.NrHospitals)
                            + (h * self.Instance.NrHospitals) + hprime)
                                for hprime in self.Instance.HospitalSet]
                                for h in self.Instance.HospitalSet]
                                for r in self.Instance.PlateletAgeSet]
                                for c in self.Instance.BloodGPSet]
            #if Constants.Debug: print("TransshipmentHHVariable indices:\n", self.TransshipmentHHVariable)

            #q_jclum            
            self.PatientTransferVariable = [[[[[
                                (self.Owner.Owner.StartPatientTransferVariables
                                + (self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * self.Instance.NrFacilities * self.Instance.NrRescueVehicles * (self.NodeNumber - 1))
                                + (j * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * self.Instance.NrFacilities * self.Instance.NrRescueVehicles)
                                + (c * self.Instance.NrDemandLocations * self.Instance.NrFacilities * self.Instance.NrRescueVehicles)
                                + (l * self.Instance.NrFacilities * self.Instance.NrRescueVehicles)
                                + (u * self.Instance.NrRescueVehicles) + m)
                                    for m in self.Instance.RescueVehicleSet]
                                    for u in self.Instance.FacilitySet]
                                    for l in self.Instance.DemandSet]
                                    for c in self.Instance.BloodGPSet]
                                    for j in self.Instance.InjuryLevelSet]
            #if Constants.Debug: print("PatientTransferVariable indices:\n", self.PatientTransferVariable)

            #mu_jcl    
            self.UnsatisfiedPatientsVariable = [[[
                        (self.Owner.Owner.StartUnsatisfiedPatientsVariables
                        + (self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * (self.NodeNumber - 1))
                        + (j * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations)
                        + (c * self.Instance.NrDemandLocations) + l)
                            for l in self.Instance.DemandSet]
                            for c in self.Instance.BloodGPSet]
                            for j in self.Instance.InjuryLevelSet]
            #if Constants.Debug: print("UnsatisfiedPatientsVariable indices:\n", self.UnsatisfiedPatientsVariable)

            #eta_cru    
            self.PlateletInventoryVariable = [[[
                        (self.Owner.Owner.StartPlateletInventoryVariables
                        + (self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities * (self.NodeNumber - 1))
                        + (c * self.Instance.NRPlateletAges * self.Instance.NrFacilities)
                        + (r * self.Instance.NrFacilities) + u)
                            for u in self.Instance.FacilitySet]
                            for r in self.Instance.PlateletAgeSet]
                            for c in self.Instance.BloodGPSet]
            #if Constants.Debug: print("PlateletInventoryVariable indices:\n", self.PlateletInventoryVariable)

            #varsigma_u
            self.OutdatedPlateletVariable = [
                (self.Owner.Owner.StartOutdatedPlateletVariables
                + (self.Instance.NrFacilities * (self.NodeNumber - 1))
                + u)
                    for u in self.Instance.FacilitySet]
            #if Constants.Debug: print("OutdatedPlateletVariable indices:\n", self.OutdatedPlateletVariable)

            #upsilon_jc'cru            
            self.ServedPatientVariable = [[[[[
                                (self.Owner.Owner.StartServedPatientVariables
                                + (self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities * (self.NodeNumber - 1))
                                + (j * self.Instance.NRBloodGPs * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities)
                                + (cprime * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities)
                                + (c * self.Instance.NRPlateletAges * self.Instance.NrFacilities)
                                + (r * self.Instance.NrFacilities) + u)
                                    for u in self.Instance.FacilitySet]
                                    for r in self.Instance.PlateletAgeSet]
                                    for c in self.Instance.BloodGPSet]
                                    for cprime in self.Instance.BloodGPSet]
                                    for j in self.Instance.InjuryLevelSet]
            #if Constants.Debug: print("ServedPatientVariable indices:\n", self.ServedPatientVariable)

            #zeta_jcu    
            self.PatientPostponementVariable = [[[
                        (self.Owner.Owner.StartPatientPostponementVariables
                        + (self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrFacilities * (self.NodeNumber - 1))
                        + (j * self.Instance.NRBloodGPs * self.Instance.NrFacilities)
                        + (c * self.Instance.NrFacilities) + u)
                            for u in self.Instance.FacilitySet]
                            for c in self.Instance.BloodGPSet]
                            for j in self.Instance.InjuryLevelSet]
            #if Constants.Debug: print("PatientPostponementVariable indices:\n", self.PatientPostponementVariable)

            #lambda_cu
            self.PlateletApheresisExtractionVariable = [[
                    (self.Owner.Owner.StartPlateletApheresisExtractionVariables
                    + (self.Instance.NRBloodGPs * self.Instance.NrFacilities * (self.NodeNumber - 1))
                    + (c * self.Instance.NrFacilities) + u)
                        for u in self.Instance.FacilitySet]
                        for c in self.Instance.BloodGPSet]
            #if Constants.Debug: print("PlateletApheresisExtractionVariable indices:\n", self.PlateletApheresisExtractionVariable)
            
            #RhoVar_ch
            self.PlateletWholeExtractionVariable = [[
                    (self.Owner.Owner.StartPlateletWholeExtractionVariables
                    + (self.Instance.NRBloodGPs * self.Instance.NrHospitals * (self.NodeNumber - 1))
                    + (c * self.Instance.NrHospitals) + h)
                        for h in self.Instance.HospitalSet]
                        for c in self.Instance.BloodGPSet]
            #if Constants.Debug: print("PlateletWholeExtractionVariable indices:\n", self.PlateletWholeExtractionVariable)

    #This function display the tree
    def Display(self):
        #if Constants.Debug: 
            # print("\n We are in 'ScenarioTreeNode' Class -- Display")
            # print("Demand of node(%d): %r" % (self.NodeNumber, self.Demand))
            # print("HospitalCap of node(%d): %r" % (self.NodeNumber, self.HospitalCap))
            # print("WholeDonor of node(%d): %r" % (self.NodeNumber, self.WholeDonor))
            # print("ApheresisDonor of node(%d): %r" % (self.NodeNumber, self.ApheresisDonor))
            # print("Probability of branch (%d): %r" % (self.NodeNumber, self.Probability))
            # print("ACFEstablishmentVariable of node(%d): %r" % (self.NodeNumber, self.ACFEstablishmentVariable))
            # print("VehicleAssignmentVariable of node(%d): %r" % (self.NodeNumber, self.VehicleAssignmentVariable))
            # print("ApheresisAssignmentVariable of node(%d): %r" % (self.NodeNumber, self.ApheresisAssignmentVariable))
            # print("TransshipmentHIVariable of node(%d): %r" % (self.NodeNumber, self.TransshipmentHIVariable))
            # print("TransshipmentIIVariable of node(%d): %r" % (self.NodeNumber, self.TransshipmentIIVariable))
            # print("TransshipmentHHVariable of node(%d): %r" % (self.NodeNumber, self.TransshipmentHHVariable))
            # print("PatientTransferVariable of node(%d): %r" % (self.NodeNumber, self.PatientTransferVariable))
            # print("UnsatisfiedPatientsVariable of node(%d): %r" % (self.NodeNumber, self.UnsatisfiedPatientsVariable))
            # print("PlateletInventoryVariable of node(%d): %r" % (self.NodeNumber, self.PlateletInventoryVariable))
            # print("OutdatedPlateletVariable of node(%d): %r" % (self.NodeNumber, self.OutdatedPlateletVariable))
            # print("ServedPatientVariable of node(%d): %r" % (self.NodeNumber, self.ServedPatientVariable))
            # print("PatientPostponementVariable of node(%d): %r" % (self.NodeNumber, self.PatientPostponementVariable))
            # print("PlateletApheresisExtractionVariable of node(%d): %r" % (self.NodeNumber, self.PlateletApheresisExtractionVariable))
            # print("PlateletWholeExtractionVariable of node(%d): %r" % (self.NodeNumber, self.PlateletWholeExtractionVariable))
        for b in self.Branches:
            b.Display()

    # This function aggregate the data of a node: It will contain the list of demand, and variable in the partial scenario
    def CreateAllScenarioFromNode(self):
        if Constants.Debug: print("\n We are in 'ScenarioTreeNode' Class -- CreateAllScenarioFromNode")
        if Constants.Debug: print(f"Entering CreateAllScenarioFromNode for Node: {self.NodeNumber}, in time: {self.Time}")

		# copy the demand and probability of the parent:
        if self.Parent is not None:
            if Constants.Debug: print("It has Parent.")           
            # Copy the demand and probability from the parent node and print the copied values
            self.DemandsInScenario = self.Parent.DemandsInScenario[:]
            #if Constants.Debug: print(f"The demand from the parent node: {self.DemandsInScenario}") 
            
            self.HospitalCapsInScenario = self.Parent.HospitalCapsInScenario[:]
            #if Constants.Debug: print(f"The HospitalCaps from the parent node: {self.HospitalCapsInScenario}") 
            
            self.WholeDonorsInScenario = self.Parent.WholeDonorsInScenario[:]
            #if Constants.Debug: print(f"The Whole Donors from the parent node: {self.WholeDonorsInScenario}") 

            self.ApheresisDonorsInScenario = self.Parent.ApheresisDonorsInScenario[:]
            #if Constants.Debug: print(f"The Apheresis Donors from the parent node: {self.ApheresisDonorsInScenario}") 

            self.ProbabilityOfScenario = self.Parent.ProbabilityOfScenario
            #if Constants.Debug: print(f"The probability from the parent node: {self.ProbabilityOfScenario}") 

            self.ACFEstablishmentVariableOfScenario = self.Parent.ACFEstablishmentVariableOfScenario[:]
            #if Constants.Debug: print(f"The ACFEstablishmentVariableOfScenario from the parent node: {self.ACFEstablishmentVariableOfScenario}")  
            
            self.VehicleAssignmentVariableOfScenario = self.Parent.VehicleAssignmentVariableOfScenario[:]
            #if Constants.Debug: print(f"The VehicleAssignmentVariableOfScenario from the parent node: {self.VehicleAssignmentVariableOfScenario}")  

            self.ApheresisAssignmentVariableOfScenario = self.Parent.ApheresisAssignmentVariableOfScenario[:]
            #if Constants.Debug: print(f"The ApheresisAssignmentVariableOfScenario from the parent node: {self.ApheresisAssignmentVariableOfScenario}")
            
            self.TransshipmentHIVariableOfScenario = self.Parent.TransshipmentHIVariableOfScenario[:]
            #if Constants.Debug: print(f"The TransshipmentHIVariableOfScenario from the parent node: {self.TransshipmentHIVariableOfScenario}")
            
            self.TransshipmentIIVariableOfScenario = self.Parent.TransshipmentIIVariableOfScenario[:]
            #if Constants.Debug: print(f"The TransshipmentIIVariableOfScenario from the parent node: {self.TransshipmentIIVariableOfScenario}")
            
            self.TransshipmentHHVariableOfScenario = self.Parent.TransshipmentHHVariableOfScenario[:]
            #if Constants.Debug: print(f"The TransshipmentHHVariableOfScenario from the parent node: {self.TransshipmentHHVariableOfScenario}")

            self.PatientTransferVariableOfScenario = self.Parent.PatientTransferVariableOfScenario[:]
            #if Constants.Debug: print(f"The PatientTransferVariableOfScenario from the parent node: {self.PatientTransferVariableOfScenario}") 
            
            self.UnsatisfiedPatientsVariableOfScenario = self.Parent.UnsatisfiedPatientsVariableOfScenario[:]
            #if Constants.Debug: print(f"The UnsatisfiedPatientsVariableOfScenario from the parent node: {self.UnsatisfiedPatientsVariableOfScenario}") 
            
            self.PlateletInventoryVariableOfScenario = self.Parent.PlateletInventoryVariableOfScenario[:]
            #if Constants.Debug: print(f"The PlateletInventoryVariableOfScenario from the parent node: {self.PlateletInventoryVariableOfScenario}") 
            
            self.OutdatedPlateletVariableOfScenario = self.Parent.OutdatedPlateletVariableOfScenario[:]
            #if Constants.Debug: print(f"The OutdatedPlateletVariableOfScenario from the parent node: {self.OutdatedPlateletVariableOfScenario}") 
            
            self.ServedPatientVariableOfScenario = self.Parent.ServedPatientVariableOfScenario[:]
            #if Constants.Debug: print(f"The ServedPatientVariableOfScenario from the parent node: {self.ServedPatientVariableOfScenario}") 
            
            self.PatientPostponementVariableOfScenario = self.Parent.PatientPostponementVariableOfScenario[:]
            #if Constants.Debug: print(f"The PatientPostponementVariableOfScenario from the parent node: {self.PatientPostponementVariableOfScenario}") 
            
            self.PlateletApheresisExtractionVariableOfScenario = self.Parent.PlateletApheresisExtractionVariableOfScenario[:]
            #if Constants.Debug: print(f"The PlateletApheresisExtractionVariableOfScenario from the parent node: {self.PlateletApheresisExtractionVariableOfScenario}") 
            
            self.PlateletWholeExtractionVariableOfScenario = self.Parent.PlateletWholeExtractionVariableOfScenario[:]
            #if Constants.Debug: print(f"The PlateletWholeExtractionVariableOfScenario from the parent node: {self.PlateletWholeExtractionVariableOfScenario}") 
             
            self.NodesOfScenario = self.Parent.NodesOfScenario[:]
            #if Constants.Debug: print(f"The NodesOfScenario from the parent node: {self.NodesOfScenario}")

            # Add the demand of the the current node and update the probability
            #if Constants.Debug: print("Add the demand of the the current node and update the probability")
            Tool.AppendIfNotEmpty(self.DemandsInScenario, self.Demand)
            Tool.AppendIfNotEmpty(self.HospitalCapsInScenario, self.HospitalCap)
            Tool.AppendIfNotEmpty(self.WholeDonorsInScenario, self.WholeDonor)
            Tool.AppendIfNotEmpty(self.ApheresisDonorsInScenario, self.ApheresisDonor)
            
            #Tool.AppendIfNotEmpty(self.FixedTransVariableOfScenario, self.FixedTransVariable)
            Tool.AppendIfNotEmpty(self.ApheresisAssignmentVariableOfScenario, self.ApheresisAssignmentVariable)
            Tool.AppendIfNotEmpty(self.TransshipmentHIVariableOfScenario, self.TransshipmentHIVariable)
            Tool.AppendIfNotEmpty(self.TransshipmentIIVariableOfScenario, self.TransshipmentIIVariable)
            Tool.AppendIfNotEmpty(self.TransshipmentHHVariableOfScenario, self.TransshipmentHHVariable)

            Tool.AppendIfNotEmpty(self.PatientTransferVariableOfScenario, self.PatientTransferVariable)
            Tool.AppendIfNotEmpty(self.UnsatisfiedPatientsVariableOfScenario, self.UnsatisfiedPatientsVariable)
            Tool.AppendIfNotEmpty(self.PlateletInventoryVariableOfScenario, self.PlateletInventoryVariable)
            Tool.AppendIfNotEmpty(self.OutdatedPlateletVariableOfScenario, self.OutdatedPlateletVariable)
            Tool.AppendIfNotEmpty(self.ServedPatientVariableOfScenario, self.ServedPatientVariable)
            Tool.AppendIfNotEmpty(self.PatientPostponementVariableOfScenario, self.PatientPostponementVariable)
            Tool.AppendIfNotEmpty(self.PlateletApheresisExtractionVariableOfScenario, self.PlateletApheresisExtractionVariable)
            Tool.AppendIfNotEmpty(self.PlateletWholeExtractionVariableOfScenario, self.PlateletWholeExtractionVariable)

            self.NodesOfScenario.append(self)

            #Compute the probability of the scenario
            self.ProbabilityOfScenario = self.ProbabilityOfScenario * self.Probability

        else :
            if Constants.Debug: print("It does not have Parent")
            self.ProbabilityOfScenario = 1
            Tool.AppendIfNotEmpty(self.ACFEstablishmentVariableOfScenario, self.ACFEstablishmentVariable)
            Tool.AppendIfNotEmpty(self.VehicleAssignmentVariableOfScenario, self.VehicleAssignmentVariable)

        # If the node has children (i.e., it's not a leaf node), recurse into them
        if self.Branches:
            for b in self.Branches:
                # Print the action of moving to a child node
                if Constants.Debug: print(f"Moving to Branch of Node: {self.NodeNumber}")
                b.CreateAllScenarioFromNode()
                # Print after returning from a child node's recursion
                if Constants.Debug: print(f"Returning to Node: {self.NodeNumber} from its Branch")
        else:
            # If no branches exist, it means this node is a leaf
            if Constants.Debug: print(f"Node: {self.NodeNumber} is a leaf node.")
        
        # Print when exiting the method for the current node
        if Constants.Debug: print(f"Exiting CreateAllScenarioFromNode for Node: {self.NodeNumber}")
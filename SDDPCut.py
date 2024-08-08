from Constants import Constants
import gurobipy as gp
from gurobipy import *
from Tool import Tool

#This class contains the parameters and method to generate and store the cuts.
class SDDPCut(object):

    def __init__(self, owner=None, forwardstage=None, trial=-1, backwardscenario=-1):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- Constructor")

        self.BackwarStage = owner
        self.ForwardStage = forwardstage
        self.BackwarStage.SDDPCuts.append(self)
        self.ForwardStage.SDDPCuts.append(self)
        self.Iteration = self.BackwarStage.SDDPOwner.CurrentIteration
        self.Trial = trial
        self.Id = len(self.BackwarStage.SDDPCuts) -1
        self.Name = "Cut_%d_%d" % (self.Iteration, self.Trial)
        self.Instance = self.BackwarStage.Instance
        
        
        self.CoefficientACFEstablishmentVariable = [0 for i in self.Instance.ACFPPointSet] 
        self.CoefficientVehicleAssignmentVariable = [[0 for i in self.Instance.ACFPPointSet] 
                                                     for m in self.Instance.RescueVehicleSet] #it going to be [m][i]
        
        self.CoefficientApheresisAssignmentVariable = [[0 for i in self.Instance.ACFPPointSet] for t in self.Instance.TimeBucketSet] #it going to be [t][i]
        self.CoefficientTransshipmentHIVariable = [[[[[0 
                                                        for i in self.Instance.ACFPPointSet] 
                                                        for h in self.Instance.HospitalSet] 
                                                        for r in self.Instance.PlateletAgeSet] 
                                                        for c in self.Instance.BloodGPSet] 
                                                        for t in self.Instance.TimeBucketSet] #it going to be [t][c][r][h][i]
        self.CoefficientTransshipmentIIVariable = [[[[[0 
                                                        for iprime in self.Instance.ACFPPointSet] 
                                                        for i in self.Instance.ACFPPointSet] 
                                                        for r in self.Instance.PlateletAgeSet] 
                                                        for c in self.Instance.BloodGPSet] 
                                                        for t in self.Instance.TimeBucketSet] #it going to be [t][c][r][i][i']
        self.CoefficientTransshipmentHHVariable = [[[[[0 
                                                        for hprime in self.Instance.HospitalSet] 
                                                        for h in self.Instance.HospitalSet] 
                                                        for r in self.Instance.PlateletAgeSet] 
                                                        for c in self.Instance.BloodGPSet] 
                                                        for t in self.Instance.TimeBucketSet] #it going to be [t][c][r][h][h']

        self.CoefficientPatientTransferVariable = [[[[[[0 
                                                        for m in self.Instance.RescueVehicleSet] 
                                                        for u in self.Instance.FacilitySet] 
                                                        for l in self.Instance.DemandSet] 
                                                        for c in self.Instance.BloodGPSet] 
                                                        for j in self.Instance.InjuryLevelSet] 
                                                        for t in self.Instance.TimeBucketSet] #it going to be [t][j][c][l][u][m]
        self.CoefficientUnsatisfiedPatientsVariable = [[[[0 
                                                        for l in self.Instance.DemandSet] 
                                                        for c in self.Instance.BloodGPSet] 
                                                        for j in self.Instance.InjuryLevelSet] 
                                                        for t in self.Instance.TimeBucketSet] #it going to be [t][j][c][l]
        self.CoefficientPlateletInventoryVariable = [[[[0 
                                                        for u in self.Instance.FacilitySet] 
                                                        for r in self.Instance.PlateletAgeSet] 
                                                        for c in self.Instance.BloodGPSet] 
                                                        for t in self.Instance.TimeBucketSet] #it going to be [t][c][r][u]
        self.CoefficientOutdatedPlateletVariable = [[0 
                                                     for u in self.Instance.FacilitySet] 
                                                     for t in self.Instance.TimeBucketSet] #it going to be [t][u]
        self.CoefficientServedPatientVariable = [[[[[[0 
                                                        for u in self.Instance.FacilitySet] 
                                                        for r in self.Instance.PlateletAgeSet] 
                                                        for c in self.Instance.BloodGPSet] 
                                                        for cprime in self.Instance.BloodGPSet] 
                                                        for j in self.Instance.InjuryLevelSet] 
                                                        for t in self.Instance.TimeBucketSet] #it going to be [t][j][c'][c][r][u]
        self.CoefficientPatientPostponementVariable = [[[[0 
                                                        for u in self.Instance.FacilitySet] 
                                                        for c in self.Instance.BloodGPSet] 
                                                        for j in self.Instance.InjuryLevelSet] 
                                                        for t in self.Instance.TimeBucketSet] #it going to be [t][j][c][u]
        self.CoefficientPlateletApheresisExtractionVariable = [[[0 
                                                                for u in self.Instance.FacilitySet] 
                                                                for c in self.Instance.BloodGPSet] 
                                                                for t in self.Instance.TimeBucketSet] #it going to be [t][c][u]
        self.CoefficientPlateletWholeExtractionVariable = [[[0 
                                                            for h in self.Instance.HospitalSet] 
                                                            for c in self.Instance.BloodGPSet] 
                                                            for t in self.Instance.TimeBucketSet] #it going to be [t][c][h]
    
        #The quantity variable fixed at earlier stages with a non zero coefficient
        self.NonZeroFixedEarlierACFEstablishmentVariable = set()   
        self.NonZeroFixedEarlierVehicleAssignmentVariable = set()   
        self.NonZeroFixedEarlierApheresisAssignmentVariable = set()
        self.NonZeroFixedEarlierTransshipmentHIVariable = set()
        self.NonZeroFixedEarlierTransshipmentIIVariable = set()
        self.NonZeroFixedEarlierTransshipmentHHVariable = set()
        self.NonZeroFixedEarlierPatientTransferVariable = set()
        self.NonZeroFixedEarlierUnsatisfiedPatientsVariable = set()
        self.NonZeroFixedEarlierPlateletInventoryVariable = set()
        self.NonZeroFixedEarlierOutdatedPlateletVariable = set()
        self.NonZeroFixedEarlierServedPatientVariable = set()
        self.NonZeroFixedEarlierPatientPostponementVariable = set()
        self.NonZeroFixedEarlierPlateletApheresisExtractionVariable = set()
        self.NonZeroFixedEarlierPlateletWholeExtractionVariable = set()

        self.DemandRHS = 0.0
        self.HospitalCapRHS = 0.0
        self.WholeDonorRHS = 0.0
        self.ApheresisDonorRHS = 0.0

        self.DemandAVGRHS = 0.0
        self.HospitalCapAVGRHS = 0.0
        self.WholeDonorAVGRHS = 0.0
        self.ApheresisDonorAVGRHS = 0.0

        self.HospitalRescueVehicleCapacityRHS = 0.0
        self.HospitalApheresisCapacityRHS = 0.0
        self.NrApheresisLimitRHS = 0.0

        self.PreviousCutRHS = 0.0

        self.InitialInventoryRHS = 0.0

        self.CPlexConstraint = None
        self.IsActive = False
        self.RHSConstantValue = -1
        self.RHSValueComputed = False

        #The index of the cut in the model
        self.IndexForward = []
        self.IndexBackward = []
        self.LastIterationWithDual = self.Iteration

        #This function add the cut to the MIP

        self.BackwardScenario = backwardscenario

        #self.Print_Attributes()


    def Print_Attributes(self):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (Print_Attributes)")
        if Constants.Debug: print("\nSDDPCut Class Attributes:")
        for attr, value in self.__dict__.items():
            if Constants.Debug: print(f"{attr}: {value}")   

    def Print(self):
        if Constants.Debug:
            print("RHS:%s"%self.GetRHS())
            print("coefficients:")
            print("FixedTrans: %s" % self.CoefficientFixedTransVariable)
            print("VarTrans: %s"%self.CoefficientVarTransVariable)
            print("Shortage: %s" % self.CoefficientShortageVariable)
            print("Inventory: %s" % self.CoefficientInventoryVariable)

    #This function return the variables of the cut in its stage (do not include the variable fixed at previous stage)
    def GetCutVariablesAtStage(self, stage, w):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (GetCutVariablesAtStage)")

        CostToGo_vars = [stage.GetIndexCostToGo(w, self.BackwardScenario)]
        if Constants.Debug: print("CostToGo_vars:\n ", CostToGo_vars)

        y_vars = [[stage.GetIndexApheresisAssignmentVariable(i, t, w)
                    for i in self.Instance.ACFPPointSet]
                    for t in self.ForwardStage.RangePeriodApheresisAssignment]
        if Constants.Debug: print("y_vars:\n ", y_vars)

        b_vars = [[[[[stage.GetIndexTransshipmentHIVariable(c, r, h, i, t, w)
                    for i in self.Instance.ACFPPointSet]
                    for h in self.Instance.HospitalSet]
                    for r in self.Instance.PlateletAgeSet]
                    for c in self.Instance.BloodGPSet]
                    for t in self.ForwardStage.RangePeriodApheresisAssignment]                      
        if Constants.Debug: print("b_vars:\n ", b_vars)

        bPrime_vars = [[[[[stage.GetIndexTransshipmentIIVariable(c, r, i, iprime, t, w)
                            for iprime in self.Instance.ACFPPointSet]
                            for i in self.Instance.ACFPPointSet]
                            for r in self.Instance.PlateletAgeSet]
                            for c in self.Instance.BloodGPSet]
                            for t in self.ForwardStage.RangePeriodApheresisAssignment]
        if Constants.Debug: print("bPrime_vars:\n ", bPrime_vars)

        bDoublePrime_vars = [[[[[stage.GetIndexTransshipmentHHVariable(c, r, h, hprime, t, w)
                            for hprime in self.Instance.HospitalSet]
                            for h in self.Instance.HospitalSet]
                            for r in self.Instance.PlateletAgeSet]
                            for c in self.Instance.BloodGPSet]
                            for t in self.ForwardStage.RangePeriodApheresisAssignment]
        if Constants.Debug: print("bDoublePrime_vars:\n ", bDoublePrime_vars)
        
        q_vars = [[[[[[stage.GetIndexPatientTransferVariable(j, c, l, u, m, t, w)
                        for m in self.Instance.RescueVehicleSet]
                        for u in self.Instance.FacilitySet]
                        for l in self.Instance.DemandSet]
                        for c in self.Instance.BloodGPSet]
                        for j in self.Instance.InjuryLevelSet]
                        for t in self.ForwardStage.RangePeriodPatientTransfer]
        if Constants.Debug: print("q_vars:\n ", q_vars)

        
        mu_vars = [[[[stage.GetIndexUnsatisfiedPatientsVariable(j, c, l, t, w)
                        for l in self.Instance.DemandSet]
                        for c in self.Instance.BloodGPSet]
                        for j in self.Instance.InjuryLevelSet]
                        for t in self.ForwardStage.RangePeriodPatientTransfer]
        if Constants.Debug: print("mu_vars:\n ", mu_vars)
        
        eta_vars = [[[[stage.GetIndexPlateletInventoryVariable(c, r, u, t, w)
                        for u in self.Instance.FacilitySet]
                        for r in self.Instance.PlateletAgeSet]
                        for c in self.Instance.BloodGPSet]
                        for t in self.ForwardStage.RangePeriodPatientTransfer]
        if Constants.Debug: print("eta_vars:\n ", eta_vars)
        
        sigmavar_vars = [[stage.GetIndexOutdatedPlateletVariable(u, t, w)
                        for u in self.Instance.FacilitySet]
                        for t in self.ForwardStage.RangePeriodPatientTransfer]
        if Constants.Debug: print("sigmavar_vars:\n ", sigmavar_vars)
        
        upsilon_vars = [[[[[[stage.GetIndexServedPatientVariable(j, cprime, c, r, u, t, w)
                        for u in self.Instance.FacilitySet]
                        for r in self.Instance.PlateletAgeSet]
                        for c in self.Instance.BloodGPSet]
                        for cprime in self.Instance.BloodGPSet]
                        for j in self.Instance.InjuryLevelSet]
                        for t in self.ForwardStage.RangePeriodPatientTransfer]
        if Constants.Debug: print("upsilon_vars:\n ", upsilon_vars)
        
        zeta_vars = [[[[stage.GetIndexPatientPostponementVariable(j, c, u, t, w)
                        for u in self.Instance.FacilitySet]
                        for c in self.Instance.BloodGPSet]
                        for j in self.Instance.InjuryLevelSet]
                        for t in self.ForwardStage.RangePeriodPatientTransfer]
        if Constants.Debug: print("zeta_vars:\n ", zeta_vars)
        
        lambda_vars = [[[stage.GetIndexPlateletApheresisExtractionVariable(c, u, t, w)
                        for u in self.Instance.FacilitySet]
                        for c in self.Instance.BloodGPSet]
                        for t in self.ForwardStage.RangePeriodPatientTransfer]
        if Constants.Debug: print("lambda_vars:\n ", lambda_vars)
        
        Rhovar_vars = [[[stage.GetIndexPlateletWholeExtractionVariable(c, h, t, w)
                        for h in self.Instance.HospitalSet]
                        for c in self.Instance.BloodGPSet]
                        for t in self.ForwardStage.RangePeriodPatientTransfer]
        if Constants.Debug: print("Rhovar_vars:\n ", Rhovar_vars)

        x_vars = []
        if self.BackwarStage.DecisionStage == 0:
            x_vars = [stage.GetIndexACFEstablishmentVariable(i)
                           for i in self.Instance.ACFPPointSet]
        if Constants.Debug: print("x_vars:\n ", x_vars)

        thetavar_vars = []
        if self.BackwarStage.DecisionStage == 0:
            thetavar_vars = [[stage.GetIndexVehicleAssignmentVariable(m, i)
                                for i in self.Instance.ACFPPointSet]
                                for m in self.Instance.RescueVehicleSet]
        if Constants.Debug: print("thetavar_vars:\n ", thetavar_vars)

        cutRHS_vars = [stage.GetIndexCutRHSFromPreviousSatge(self)]
        if Constants.Debug: print("cutRHS_vars:\n ", cutRHS_vars)

        return CostToGo_vars, y_vars, b_vars, bPrime_vars, bDoublePrime_vars, q_vars, mu_vars, eta_vars, \
                sigmavar_vars, upsilon_vars, zeta_vars, lambda_vars, Rhovar_vars, x_vars, thetavar_vars, cutRHS_vars
    
    # This function return the coefficient variables of the cut in its stage (do not include the variable fixed at previous stage)
    def GetCutVariablesCoefficientAtStage(self):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (GetCutVariablesCoefficientAtStage)")

        CostToGo_coeff = [1.0]


        y_coeff =  [[self.CoefficientApheresisAssignmentVariable[self.BackwarStage.GetTimePeriodAssociatedToApheresisAssignmentVariable(t)][i]
                    for i in self.Instance.ACFPPointSet]
                    for t in self.ForwardStage.RangePeriodApheresisAssignment]
        #if Constants.Debug: print("y_coeff:\n ", y_coeff)

        b_coeff =  [[[[[self.CoefficientTransshipmentHIVariable[self.BackwarStage.GetTimePeriodAssociatedToApheresisAssignmentVariable(t)][c][r][h][i]
                            for i in self.Instance.ACFPPointSet]
                            for h in self.Instance.HospitalSet]
                            for r in self.Instance.PlateletAgeSet]
                            for c in self.Instance.BloodGPSet]
                            for t in self.ForwardStage.RangePeriodApheresisAssignment]
        #if Constants.Debug: print("b_coeff:\n ", b_coeff)

        bPrime_coeff =  [[[[[self.CoefficientTransshipmentIIVariable[self.BackwarStage.GetTimePeriodAssociatedToApheresisAssignmentVariable(t)][c][r][i][iprime]
                            for iprime in self.Instance.ACFPPointSet]
                            for i in self.Instance.ACFPPointSet]
                            for r in self.Instance.PlateletAgeSet]
                            for c in self.Instance.BloodGPSet]
                            for t in self.ForwardStage.RangePeriodApheresisAssignment]
        #if Constants.Debug: print("bPrime_coeff:\n ", bPrime_coeff)
        
        bDoublePrime_coeff =  [[[[[self.CoefficientTransshipmentHHVariable[self.BackwarStage.GetTimePeriodAssociatedToApheresisAssignmentVariable(t)][c][r][h][hprime]
                                for hprime in self.Instance.HospitalSet]
                                for h in self.Instance.HospitalSet]
                                for r in self.Instance.PlateletAgeSet]
                                for c in self.Instance.BloodGPSet]
                                for t in self.ForwardStage.RangePeriodApheresisAssignment]
        #if Constants.Debug: print("bDoublePrime_coeff:\n ", bDoublePrime_coeff)
        
        q_coeff =  [[[[[[self.CoefficientPatientTransferVariable[self.BackwarStage.GetTimePeriodAssociatedToPatientTransferVariable(t)][j][c][l][u][m]
                        for m in self.Instance.RescueVehicleSet]
                        for u in self.Instance.FacilitySet]
                        for l in self.Instance.DemandSet]
                        for c in self.Instance.BloodGPSet]
                        for j in self.Instance.InjuryLevelSet]
                        for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("q_coeff:\n ", q_coeff)
        
        mu_coeff =  [[[[self.CoefficientUnsatisfiedPatientsVariable[self.BackwarStage.GetTimePeriodAssociatedToPatientTransferVariable(t)][j][c][l]
                        for l in self.Instance.DemandSet]
                        for c in self.Instance.BloodGPSet]
                        for j in self.Instance.InjuryLevelSet]
                        for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("mu_coeff:\n ", mu_coeff)
        
        eta_coeff =  [[[[self.CoefficientPlateletInventoryVariable[self.BackwarStage.GetTimePeriodAssociatedToPatientTransferVariable(t)][c][r][u]
                        for u in self.Instance.FacilitySet]
                        for r in self.Instance.PlateletAgeSet]
                        for c in self.Instance.BloodGPSet]
                        for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("eta_coeff:\n ", eta_coeff)
        
        sigmavar_coeff =  [[self.CoefficientOutdatedPlateletVariable[self.BackwarStage.GetTimePeriodAssociatedToPatientTransferVariable(t)][u]
                            for u in self.Instance.FacilitySet]
                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("sigmavar_coeff:\n ", sigmavar_coeff)
        
        upsilon_coeff =  [[[[[[self.CoefficientServedPatientVariable[self.BackwarStage.GetTimePeriodAssociatedToPatientTransferVariable(t)][j][cprime][c][r][u]
                            for u in self.Instance.FacilitySet]
                            for r in self.Instance.PlateletAgeSet]
                            for c in self.Instance.BloodGPSet]
                            for cprime in self.Instance.BloodGPSet]
                            for j in self.Instance.InjuryLevelSet]
                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("upsilon_coeff:\n ", upsilon_coeff)
        
        zeta_coeff =  [[[[self.CoefficientPatientPostponementVariable[self.BackwarStage.GetTimePeriodAssociatedToPatientTransferVariable(t)][j][c][u]
                            for u in self.Instance.FacilitySet]
                            for c in self.Instance.BloodGPSet]
                            for j in self.Instance.InjuryLevelSet]
                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("zeta_coeff:\n ", zeta_coeff)
        
        lambda_coeff =  [[[self.CoefficientPlateletApheresisExtractionVariable[self.BackwarStage.GetTimePeriodAssociatedToPatientTransferVariable(t)][c][u]
                            for u in self.Instance.FacilitySet]
                            for c in self.Instance.BloodGPSet]
                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("lambda_coeff:\n ", lambda_coeff)
        
        Rhovar_coeff =  [[[self.CoefficientPlateletWholeExtractionVariable[self.BackwarStage.GetTimePeriodAssociatedToPatientTransferVariable(t)][c][h]
                            for h in self.Instance.HospitalSet]
                            for c in self.Instance.BloodGPSet]
                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("Rhovar_coeff:\n ", Rhovar_coeff)
        
        x_coeff=[]
        thetavar_coeff=[]
        if self.BackwarStage.DecisionStage == 0:
            x_coeff = [self.CoefficientACFEstablishmentVariable[i]
                             for i in self.Instance.ACFPPointSet]
            if Constants.Debug: print("x_coeff:\n ", x_coeff)

            thetavar_coeff = [[self.CoefficientVehicleAssignmentVariable[m][i]
                             for i in self.Instance.ACFPPointSet]
                             for m in self.Instance.RescueVehicleSet]
            if Constants.Debug: print("thetavar_coeff:\n ", thetavar_coeff)

        CutRHS_coeff = [-1]

        Total_coeff = CostToGo_coeff \
                        + y_coeff + b_coeff + bPrime_coeff + bDoublePrime_coeff \
                        + q_coeff + mu_coeff + eta_coeff + sigmavar_coeff + upsilon_coeff + zeta_coeff + lambda_coeff + Rhovar_coeff \
                        + x_coeff + thetavar_coeff \
                        + CutRHS_coeff
        
        return Total_coeff, CostToGo_coeff, \
                y_coeff, b_coeff, bPrime_coeff, bDoublePrime_coeff, \
                q_coeff, mu_coeff, eta_coeff, sigmavar_coeff, upsilon_coeff, zeta_coeff, lambda_coeff, Rhovar_coeff, \
                x_coeff, thetavar_coeff, \
                CutRHS_coeff
        
    #Increase the coefficient of the Unsatisfied Patients variable 
    def IncreaseCoefficientUnsatisfiedPatients(self, injury, bloodgp, demand, time, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseCoefficientUnsatisfiedPatients)")
                
        self.CoefficientUnsatisfiedPatientsVariable[time][injury][bloodgp][demand] = self.CoefficientUnsatisfiedPatientsVariable[time][injury][bloodgp][demand] + value

        if time < self.BackwarStage.GetTimePeriodAssociatedToPatientTransferVariable(0):
            self.NonZeroFixedEarlierUnsatisfiedPatientsVariable.add((injury, dd, demand, time))
    
    #Increase the coefficient of the Unsatisfied Patients variable 
    def IncreaseCoefficientPatientPostponement(self, injury, bloodgp, facility, time, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseCoefficientPatientPostponement)")
        
        self.CoefficientPatientPostponementVariable[time][injury][bloodgp][facility] = self.CoefficientPatientPostponementVariable[time][injury][bloodgp][facility] + value

        if time < self.BackwarStage.GetTimePeriodAssociatedToPatientTransferVariable(0):
            self.NonZeroFixedEarlierPatientPostponementVariable.add((injury, bloodgp, facility, time))
                
    #Increase the coefficient of the TransshipmentH'H 
    def IncreaseCoefficientTransshipmentHH(self, bloodgp, age, h, hprime, time, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseCoefficientTransshipmentHH)")
                
        self.CoefficientTransshipmentHHVariable[time][bloodgp][age][h][hprime] = self.CoefficientTransshipmentHHVariable[time][bloodgp][age][h][hprime] + value

        if time < self.BackwarStage.GetTimePeriodAssociatedToApheresisAssignmentVariable(0):
            self.NonZeroFixedEarlierTransshipmentHHVariable.add((bloodgp, age, h, hprime, time))
        
    #Increase the coefficient of the TransshipmentHI 
    def IncreaseCoefficientTransshipmentHI(self, bloodgp, age, hospital, acf, time, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseCoefficientTransshipmentHI)")
                
        self.CoefficientTransshipmentHIVariable[time][bloodgp][age][hospital][acf] = self.CoefficientTransshipmentHIVariable[time][bloodgp][age][hospital][acf] + value

        if time < self.BackwarStage.GetTimePeriodAssociatedToApheresisAssignmentVariable(0):
            self.NonZeroFixedEarlierTransshipmentHIVariable.add((bloodgp, age, acf, time))
    
    #Increase the coefficient of the TransshipmentII 
    def IncreaseCoefficientTransshipmentII(self, bloodgp, age, acf, acfprime, time, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseCoefficientTransshipmentII)")
                
        self.CoefficientTransshipmentIIVariable[time][bloodgp][age][acf][acfprime] = self.CoefficientTransshipmentIIVariable[time][bloodgp][age][acf][acfprime] + value

        if time < self.BackwarStage.GetTimePeriodAssociatedToApheresisAssignmentVariable(0):
            self.NonZeroFixedEarlierTransshipmentIIVariable.add((bloodgp, age, acf, time))
    
    #Increase the coefficient of the TransshipmentHI considering summation on i 
    def IncreaseCoefficientPlateletWholeExtractionVariable(self, bloodgp, h, time, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseCoefficientPlateletWholeExtractionVariable)")
        
        self.CoefficientPlateletWholeExtractionVariable[time][bloodgp][h] = self.CoefficientPlateletWholeExtractionVariable[time][bloodgp][h] + value

        if time < self.BackwarStage.GetTimePeriodAssociatedToPatientTransferVariable(0):
            self.NonZeroFixedEarlierPlateletWholeExtractionVariable.add((bloodgp, h, time))
    
    #Increase the coefficient of the PlateletInventory variable 
    def IncreaseCoefficientPlateletInventory(self, bloodgp, age, facility, time, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseCoefficientPlateletInventory)")
                
        self.CoefficientPlateletInventoryVariable[time][bloodgp][age][facility] = self.CoefficientPlateletInventoryVariable[time][bloodgp][age][facility] + value

        if time < self.BackwarStage.GetTimePeriodAssociatedToPatientTransferVariable(0):
            self.NonZeroFixedEarlierPlateletInventoryVariable.add((bloodgp, age, facility, time))

    #Increase the coefficient of the VarTrans variable 
    def IncreaseCoefficientApheresisAssignment(self, acf, time, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseCoefficientApheresisAssignment)")
                
        self.CoefficientApheresisAssignmentVariable[time][acf] = self.CoefficientApheresisAssignmentVariable[time][acf] + value

        if time < self.BackwarStage.GetTimePeriodAssociatedToApheresisAssignmentVariable(0):
            self.NonZeroFixedEarlierApheresisAssignmentVariable.add((dd, time))
    
    #Increase the coefficient of the VarTrans variable 
    def IncreaseCoefficientVarTrans(self, demand, time, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseCoefficientVarTrans)")
                
        self.CoefficientVarTransVariable[time][demand] = self.CoefficientVarTransVariable[time][demand] + value

        if time < self.BackwarStage.GetTimePeriodAssociatedToVarTransVariable(0):
            self.NonZeroFixedEarlierVarTransVar.add((demand, time))

    def IncreaseCoefficientShortage(self, demand, time, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseCoefficientShortage)")

        self.CoefficientShortageVariable[time][demand] = self.CoefficientShortageVariable[time][demand] + value

        if time < self.BackwarStage.GetTimePeriodAssociatedToShortageVariable(0):
            self.NonZeroFixedEarlierShortageVar.add((demand, time))
    
    def IncreaseCoefficientInventory(self, demand, time, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseCoefficientInventory)")

        self.CoefficientInventoryVariable[time][demand] = self.CoefficientInventoryVariable[time][demand] + value

        if time < self.BackwarStage.GetTimePeriodAssociatedToInventoryVariable(0):
            self.NonZeroFixedEarlierInventoryVar.add((demand, time))

    def IncreaseCoefficientACFEstablishmentVariable(self, acf, time, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseCoefficientACFEstablishmentVariable)")

        self.CoefficientACFEstablishmentVariable[acf] = self.CoefficientACFEstablishmentVariable[acf] + value

        if not self.BackwarStage.IsFirstStage():
            self.NonZeroFixedEarlierACFEstablishmentVariable.add((acf, time))
    
    def IncreaseCoefficientVehicleAssignment(self, vehicle, acf, time, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseCoefficientVehicleAssignment)")

        self.CoefficientVehicleAssignmentVariable[vehicle][acf] = self.CoefficientVehicleAssignmentVariable[vehicle][acf] + value

        if not self.BackwarStage.IsFirstStage():
            self.NonZeroFixedEarlierVehicleAssignmentVariable.add((vehicle, acf, time))
    
    def IncreaseCoefficientFixedTrans(self, supply, demand, time, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseCoefficientFixedTrans)")

        self.CoefficientFixedTransVariable[supply][demand] = self.CoefficientFixedTransVariable[supply][demand] + value

        if not self.BackwarStage.IsFirstStage():
            self.NonZeroFixedEarlierFixedTransVar.add((supply, demand, time))
            
    def ComputeRHSFromPreviousStage(self, forward):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (ComputeRHSFromPreviousStage)")

        if forward:
            scenarionr = self.ForwardStage.CurrentTrialNr
        else:
            scenarionr = self.BackwarStage.CurrentTrialNr

        result = 0

        if Constants.Debug:
            print("forward: ", forward, ", scenarionr:", scenarionr)
            print("NonZeroFixedEarlierACFEstablishmentVariable: ", self.NonZeroFixedEarlierACFEstablishmentVariable)
            print("NonZeroFixedEarlierVehicleAssignmentVariable: ", self.NonZeroFixedEarlierVehicleAssignmentVariable)

            print("NonZeroFixedEarlierApheresisAssignmentVariable: ", self.NonZeroFixedEarlierApheresisAssignmentVariable)
            print("NonZeroFixedEarlierTransshipmentHIVariable: ", self.NonZeroFixedEarlierTransshipmentHIVariable)
            print("NonZeroFixedEarlierTransshipmentIIVariable: ", self.NonZeroFixedEarlierTransshipmentIIVariable)
            print("NonZeroFixedEarlierTransshipmentHHVariable: ", self.NonZeroFixedEarlierTransshipmentHHVariable)

            print("NonZeroFixedEarlierPatientTransferVariable: ", self.NonZeroFixedEarlierPatientTransferVariable)
            print("NonZeroFixedEarlierUnsatisfiedPatientsVariable: ", self.NonZeroFixedEarlierUnsatisfiedPatientsVariable)
            print("NonZeroFixedEarlierPlateletInventoryVariable: ", self.NonZeroFixedEarlierPlateletInventoryVariable)
            print("NonZeroFixedEarlierOutdatedPlateletVariable: ", self.NonZeroFixedEarlierOutdatedPlateletVariable)
            print("NonZeroFixedEarlierServedPatientVariable: ", self.NonZeroFixedEarlierServedPatientVariable)
            print("NonZeroFixedEarlierPatientPostponementVariable: ", self.NonZeroFixedEarlierPatientPostponementVariable)
            print("NonZeroFixedEarlierPlateletApheresisExtractionVariable: ", self.NonZeroFixedEarlierPlateletApheresisExtractionVariable)
            print("NonZeroFixedEarlierPlateletWholeExtractionVariable: ", self.NonZeroFixedEarlierPlateletWholeExtractionVariable)

        for tuple in self.NonZeroFixedEarlierACFEstablishmentVariable:
            acf = tuple[0]
            time = tuple[1]
            result = result - (self.BackwarStage.SDDPOwner.GetACFEstablishmentFixedEarlier(acf, scenarionr) * self.CoefficientACFEstablishmentVariable[acf])
            
            if Constants.Debug:
                print(f"GetACFEstablishmentFixedEarlier(i:{acf}, w:{scenarionr}): ", self.BackwarStage.SDDPOwner.GetACFEstablishmentFixedEarlier(acf, scenarionr))
                print(f"CoefficientACFEstablishmentVariable[i:{acf}] ", self.CoefficientACFEstablishmentVariable[acf])
                print(f"tuple: {tuple}, acf:{acf}, result for ACFEstablishment Var FixedEarlier:{result}")
                print("-----------------------------------------------")
            
        for tuple in self.NonZeroFixedEarlierVehicleAssignmentVariable:
            vehicle = tuple[0]
            acf = tuple[1]
            time = tuple[2]
            result = result - self.BackwarStage.SDDPOwner.GetVehicleAssignmentFixedEarlier(vehicle, acf, scenarionr) * self.CoefficientVehicleAssignmentVariable[vehicle][acf]
            
            if Constants.Debug:
                print(f"GetVehicleAssignmentFixedEarlier(m:{vehicle}, i:{acf}, w:{scenarionr}): ", self.BackwarStage.SDDPOwner.GetVehicleAssignmentFixedEarlier(vehicle, acf, scenarionr))
                print(f"CoefficientVehicleAssignmentVariable[m:{vehicle}][i:{acf}] ", self.CoefficientVehicleAssignmentVariable[vehicle][acf])
                print(f"tuple: {tuple}, m:{vehicle}, i:{acf}, result for VehicleAssignment Var FixedEarlier:{result}")
                print("-----------------------------------------------")

        for tuple in self.NonZeroFixedEarlierApheresisAssignmentVariable:
            d = tuple[0]
            t = tuple[1]
            result = result - self.BackwarStage.SDDPOwner.GetVarTransFixedEarlier(d, t, scenarionr) \
                                            * self.CoefficientVarTransVariable[t][d]
            print(f"tuple: {tuple}, d:{d}, t:{t}, result for VarTrans Var:{result}")
        
        for tuple in self.NonZeroFixedEarlierTransshipmentHIVariable:
            d = tuple[0]
            t = tuple[1]
            result = result - self.BackwarStage.SDDPOwner.GetVarTransFixedEarlier(d, t, scenarionr) \
                                            * self.CoefficientVarTransVariable[t][d]
        
        for tuple in self.NonZeroFixedEarlierTransshipmentIIVariable:
            d = tuple[0]
            t = tuple[1]
            result = result - self.BackwarStage.SDDPOwner.GetVarTransFixedEarlier(d, t, scenarionr) \
                                            * self.CoefficientVarTransVariable[t][d]
        
        for tuple in self.NonZeroFixedEarlierTransshipmentHHVariable:
            d = tuple[0]
            t = tuple[1]
            result = result - self.BackwarStage.SDDPOwner.GetVarTransFixedEarlier(d, t, scenarionr) \
                                            * self.CoefficientVarTransVariable[t][d]

        for tuple in self.NonZeroFixedEarlierPatientTransferVariable:
            d = tuple[0]
            t = tuple[1]
            result = result - self.BackwarStage.SDDPOwner.GetShortageFixedEarlier(d, t, scenarionr) \
                                            * self.CoefficientShortageVariable[t][d]

        for tuple in self.NonZeroFixedEarlierUnsatisfiedPatientsVariable:
            d = tuple[0]
            t = tuple[1]
            result = result - self.BackwarStage.SDDPOwner.GetShortageFixedEarlier(d, t, scenarionr) \
                                            * self.CoefficientShortageVariable[t][d]

        for tuple in self.NonZeroFixedEarlierPlateletInventoryVariable:
            d = tuple[0]
            t = tuple[1]
            result = result - self.BackwarStage.SDDPOwner.GetShortageFixedEarlier(d, t, scenarionr) \
                                            * self.CoefficientShortageVariable[t][d]

        for tuple in self.NonZeroFixedEarlierOutdatedPlateletVariable:
            d = tuple[0]
            t = tuple[1]
            result = result - self.BackwarStage.SDDPOwner.GetShortageFixedEarlier(d, t, scenarionr) \
                                            * self.CoefficientShortageVariable[t][d]

        for tuple in self.NonZeroFixedEarlierServedPatientVariable:
            d = tuple[0]
            t = tuple[1]
            result = result - self.BackwarStage.SDDPOwner.GetShortageFixedEarlier(d, t, scenarionr) \
                                            * self.CoefficientShortageVariable[t][d]

        for tuple in self.NonZeroFixedEarlierPatientPostponementVariable:
            d = tuple[0]
            t = tuple[1]
            result = result - self.BackwarStage.SDDPOwner.GetShortageFixedEarlier(d, t, scenarionr) \
                                            * self.CoefficientShortageVariable[t][d]

        for tuple in self.NonZeroFixedEarlierPlateletApheresisExtractionVariable:
            d = tuple[0]
            t = tuple[1]
            result = result - self.BackwarStage.SDDPOwner.GetShortageFixedEarlier(d, t, scenarionr) \
                                            * self.CoefficientShortageVariable[t][d]

        for tuple in self.NonZeroFixedEarlierPlateletWholeExtractionVariable:
            cprime = tuple[0]
            h = tuple[1]
            t = tuple[2]
            result = result - self.BackwarStage.SDDPOwner.GetWholePLTProductionFixedEarlier(cprime, h, t, scenarionr) * self.CoefficientPlateletWholeExtractionVariable[t][cprime][h]

        return result

    def IncreaseDemandRHS(self, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseDemandRHS)")

        self.DemandRHS = self.DemandRHS + value
  
    def IncreaseApheresisDonorRHS(self, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseApheresisDonorRHS)")
        
        self.ApheresisDonorRHS = self.ApheresisDonorRHS + value
    
    def IncreaseWholeDonorRHS(self, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseWholeDonorRHS)")
        
        self.WholeDonorRHS = self.WholeDonorRHS + value
    
    def IncreaseAvgDemandRHS(self, value):
        self.DemandAVGRHS = self.DemandAVGRHS + value

    def UpdateRHS (self):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (UpdateRHS)")
        
        self.RHSConstantValue =   self.DemandRHS \
                                    + self.HospitalCapRHS \
                                    + self.WholeDonorRHS \
                                    + self.ApheresisDonorRHS \
                                    + self.HospitalRescueVehicleCapacityRHS \
                                    + self.HospitalApheresisCapacityRHS \
                                    + self.DemandAVGRHS \
                                    + self.HospitalCapAVGRHS \
                                    + self.WholeDonorAVGRHS \
                                    + self.ApheresisDonorAVGRHS \
                                    + self.NrApheresisLimitRHS \
                                    + self.InitialInventoryRHS \
                                    + self.PreviousCutRHS 

        if Constants.Debug:
            print("DemandRHS: ", self.DemandRHS)
            print("HospitalCapRHS: ", self.HospitalCapRHS)
            print("WholeDonorRHS: ", self.WholeDonorRHS)
            print("ApheresisDonorRHS: ", self.ApheresisDonorRHS)
            print("HospitalRescueVehicleCapacityRHS: ", self.HospitalRescueVehicleCapacityRHS)
            print("HospitalApheresisCapacityRHS: ", self.HospitalApheresisCapacityRHS)
            print("DemandAVGRHS: ", self.DemandAVGRHS)
            print("HospitalCapAVGRHS: ", self.HospitalCapAVGRHS)
            print("WholeDonorAVGRHS: ", self.WholeDonorAVGRHS)
            print("ApheresisDonorAVGRHS: ", self.ApheresisDonorAVGRHS)
            print("NrApheresisLimitRHS: ", self.NrApheresisLimitRHS)
            print("InitialInventoryRHS: ", self.InitialInventoryRHS)
            print("PreviousCutRHS: ", self.PreviousCutRHS)
            print("RHSConstantValue: ", self.RHSConstantValue)
            print("-------------------------------")

    def AddCut(self, addtomodel=True):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (AddCut)")

        self.IsActive = True
        if Constants.Debug: print("Add the Cut %s" %self.Name)

        #multiply by -1 because the variable goes on the left hand side
        righthandside = [self.ComputeCurrentRightHandSide()]
        if addtomodel:
            self.ActuallyAddToModel(self.ForwardStage,   righthandside, True)
            if not self.BackwarStage.IsFirstStage() and self.BackwarStage.MIPDefined:
                self.ActuallyAddToModel(self.BackwarStage,   righthandside, False)

    def ActuallyAddToModel(self, stage, righthandside, forward):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (ActuallyAddToModel)")

        RHSFromPreviousStage = self.ComputeRHSFromPreviousStage(forward)
                
        # Create a new auxiliary variable for the RHS adjustment
        Index_Var = stage.GetIndexCutRHSFromPreviousSatge(self)
        aux_var = stage.GurobiModel.addVar(lb=RHSFromPreviousStage, ub=RHSFromPreviousStage, obj=0.0, name=f"CutRHSFromPrevStageFixedEarlier_SDDP_{stage.DecisionStage}_index_{Index_Var}")
        stage.GurobiModel.update()
        
        # Store the variable in the dictionary
        stage.CutRHSVariable_SDDP[Index_Var] = aux_var


        # Correctly access the variable from the dictionary using its index to print its attributes
        if Constants.Debug: print(f"Var Name: {stage.CutRHSVariable_SDDP[Index_Var].VarName}, Obj: {stage.CutRHSVariable_SDDP[Index_Var].Obj}, LB: {stage.CutRHSVariable_SDDP[Index_Var].LB}, UB: {stage.CutRHSVariable_SDDP[Index_Var].UB}, VType: {stage.CutRHSVariable_SDDP[Index_Var].vtype}")

                
        # Now proceed to use this auxiliary variable in your constraints
        Total_coeff, CostToGo_coeff, y_coeff, b_coeff, bPrime_coeff, bDoublePrime_coeff, \
        q_coeff, mu_coeff, eta_coeff, sigmavar_coeff, upsilon_coeff, zeta_coeff, lambda_coeff, Rhovar_coeff, \
        x_coeff, thetavar_coeff, CutRHS_coeff = self.GetCutVariablesCoefficientAtStage()

        righthandside = self.GetRHS()  # Assuming this is a scalar value

        # Loop through each scenario to add constraints
        for w in stage.FixedScenarioSet:
            # Retrieve the variables and their coefficients for this cut
            CostToGo_vars, y_vars, b_vars, bPrime_vars, bDoublePrime_vars, q_vars, mu_vars, eta_vars, \
            sigmavar_vars, upsilon_vars, zeta_vars, lambda_vars, Rhovar_vars, x_vars, thetavar_vars, cutRHS_vars = self.GetCutVariablesAtStage(stage, w) 
            
            CostToGo_LeftHandSide = gp.quicksum(CostToGo_coeff[i] * stage.Cost_To_Go_Var_SDDP[CostToGo_vars[i]] for i in range(len(CostToGo_vars)))    
            
            ########################################################
            flat_x_vars = list(Tool.flatten(x_vars))            
            flat_x_coeff = list(Tool.flatten(x_coeff))             
            x_LeftHandSide = gp.quicksum(flat_x_coeff[i] * stage.ACFEstablishment_Var_SDDP[flat_x_vars[i]] for i in range(len(flat_x_vars))) 
            
            flat_thetavar_vars = list(Tool.flatten(thetavar_vars))            
            flat_thetavar_coeff = list(Tool.flatten(thetavar_coeff))             
            thatavar_LeftHandSide = gp.quicksum(flat_thetavar_coeff[i] * stage.VehicleAssignment_Var_SDDP[flat_thetavar_vars[i]] for i in range(len(flat_thetavar_vars)))    
            
            ########################################################
            flat_y_vars = list(Tool.flatten(y_vars))            
            flat_y_coeff = list(Tool.flatten(y_coeff)) 
            y_LeftHandSide = gp.quicksum(flat_y_coeff[i] * stage.ApheresisAssignment_Var_SDDP[flat_y_vars[i]] for i in range(len(flat_y_vars)))   

            flat_b_vars = list(Tool.flatten(b_vars))            
            flat_b_coeff = list(Tool.flatten(b_coeff))
            b_LeftHandSide = gp.quicksum(flat_b_coeff[i] * stage.TransshipmentHI_Var_SDDP[flat_b_vars[i]] for i in range(len(flat_b_vars)))  

            flat_bPrime_vars = list(Tool.flatten(bPrime_vars))            
            flat_bPrime_coeff = list(Tool.flatten(bPrime_coeff))
            bPrime_LeftHandSide = gp.quicksum(flat_bPrime_coeff[i] * stage.TransshipmentII_Var_SDDP[flat_bPrime_vars[i]] for i in range(len(flat_bPrime_vars)))

            flat_bDoublePrime_vars = list(Tool.flatten(bDoublePrime_vars))            
            flat_bDoublePrime_coeff = list(Tool.flatten(bDoublePrime_coeff))
            bDoublePrime_LeftHandSide = gp.quicksum(flat_bDoublePrime_coeff[i] * stage.TransshipmentHH_Var_SDDP[flat_bDoublePrime_vars[i]] for i in range(len(flat_bDoublePrime_vars)))    
            
            ########################################################
            flat_q_vars = list(Tool.flatten(q_vars))            
            flat_q_coeff = list(Tool.flatten(q_coeff))            
            q_LeftHandSide = gp.quicksum(flat_q_coeff[i] * stage.PatientTransfer_Var_SDDP[flat_q_vars[i]] for i in range(len(flat_q_vars))) 

            flat_mu_vars = list(Tool.flatten(mu_vars))            
            flat_mu_coeff = list(Tool.flatten(mu_coeff))
            mu_LeftHandSide = gp.quicksum(flat_mu_coeff[i] * stage.UnsatisfiedPatients_Var_SDDP[flat_mu_vars[i]] for i in range(len(flat_mu_vars)))  
            
            flat_eta_vars = list(Tool.flatten(eta_vars))            
            flat_eta_coeff = list(Tool.flatten(eta_coeff))              
            eta_LeftHandSide = gp.quicksum(flat_eta_coeff[i] * stage.PlateletInventory_Var_SDDP[flat_eta_vars[i]] for i in range(len(flat_eta_vars)))

            flat_sigmavar_vars = list(Tool.flatten(sigmavar_vars))            
            flat_sigmavar_coeff = list(Tool.flatten(sigmavar_coeff))                
            sigmavar_LeftHandSide = gp.quicksum(flat_sigmavar_coeff[i] * stage.OutdatedPlatelet_Var_SDDP[flat_sigmavar_vars[i]] for i in range(len(flat_sigmavar_vars))) 

            flat_upsilon_vars = list(Tool.flatten(upsilon_vars))            
            flat_upsilon_coeff = list(Tool.flatten(upsilon_coeff))              
            upsilon_LeftHandSide = gp.quicksum(flat_upsilon_coeff[i] * stage.ServedPatient_Var_SDDP[flat_upsilon_vars[i]] for i in range(len(flat_upsilon_vars)))  

            flat_zeta_vars = list(Tool.flatten(zeta_vars))            
            flat_zeta_coeff = list(Tool.flatten(zeta_coeff))
            zeta_LeftHandSide = gp.quicksum(flat_zeta_coeff[i] * stage.PatientPostponement_Var_SDDP[flat_zeta_vars[i]] for i in range(len(flat_zeta_vars))) 

            flat_lambda_vars = list(Tool.flatten(lambda_vars))            
            flat_lambda_coeff = list(Tool.flatten(lambda_coeff))
            lambda_LeftHandSide = gp.quicksum(flat_lambda_coeff[i] * stage.PlateletApheresisExtraction_Var_SDDP[flat_lambda_vars[i]] for i in range(len(flat_lambda_vars)))

            flat_Rhovar_vars = list(Tool.flatten(Rhovar_vars))            
            flat_Rhovar_coeff = list(Tool.flatten(Rhovar_coeff))
            Rhovar_LeftHandSide = gp.quicksum(flat_Rhovar_coeff[i] * stage.PlateletWholeExtraction_Var_SDDP[flat_Rhovar_vars[i]] for i in range(len(flat_Rhovar_vars)))    
            
            CutRHS_LeftHandSide = gp.quicksum(CutRHS_coeff[i] * stage.CutRHSVariable_SDDP[cutRHS_vars[i]] for i in range(len(cutRHS_vars)))    

            LeftHandSide = CostToGo_LeftHandSide \
                            + x_LeftHandSide + thatavar_LeftHandSide \
                            + y_LeftHandSide + b_LeftHandSide + bPrime_LeftHandSide + bDoublePrime_LeftHandSide \
                            + q_LeftHandSide + mu_LeftHandSide + eta_LeftHandSide + sigmavar_LeftHandSide \
                            + upsilon_LeftHandSide + zeta_LeftHandSide + lambda_LeftHandSide + Rhovar_LeftHandSide\
                            + CutRHS_LeftHandSide

            constraint_name = f"CutConstraint_w_{w}_stage_{stage.DecisionStage}_forward_{int(forward)}_Name_{self.Name}_index_{stage.LastAddedConstraintIndex}"
            

            stage.GurobiModel.addConstr(LeftHandSide >= righthandside, name=constraint_name)
            stage.GurobiModel.update()

            stage.CutConstraint_Names.append(constraint_name)

            
            # Keep track of constraint names if needed
            stage.IndexCutConstraint.append(constraint_name)
            stage.IndexCutConstraintPerScenario[w].append(constraint_name)

            if forward:
                self.IndexForward.append(constraint_name)
                if Constants.Debug: print(f"Added constraint name to IndexForward: {constraint_name}")
            else:
                self.IndexBackward.append(constraint_name)
                if Constants.Debug: print(f"Added constraint name to IndexBackward: {constraint_name}")

            stage.ConcernedScenarioCutConstraint.append(w)
            if Constants.Debug: print(f"Added scenario to ConcernedScenarioCutConstraint: {w}")

            stage.LastAddedConstraintIndex += 1  # Assuming this is to keep track of the number of constraints
            if Constants.Debug: print(f"Updated LastAddedConstraintIndex to: {stage.LastAddedConstraintIndex}")
            
            stage.ConcernedCutinConstraint.append(self)

            if Constants.Debug: print(f"Added constraint {constraint_name}")

    def GetRHS(self):

        righthandside = self.RHSConstantValue

        return righthandside
    
    def ComputeCurrentRightHandSide(self):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (ComputeCurrentRightHandSide)")
        
        righthandside = self.GetRHS()

        return righthandside
        
    def GetCostToGoLBInCUrrentSolution(self,  w):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (UpdateRHS)")

        variablofstage = self.GetCutVariablesAtStage(self.ForwardStage, 0)
                        
        # Remove cost to go
        variablofstage = variablofstage[1:]

        ################################## ApheresisAssignmentValues
        valueofvariable_y = [[self.ForwardStage.ApheresisAssignmentValues[w][t][i]
                                for i in self.Instance.ACFPPointSet]
                                for t in self.ForwardStage.RangePeriodApheresisAssignment]
        #if Constants.Debug: print("value of ApheresisAssignment variables:\n ", valueofvariable_y)

        ################################## TransshipmentHIValues
        valueofvariable_b = [[[[[self.ForwardStage.TransshipmentHIValues[w][t][c][r][h][i]
                                    for i in self.Instance.ACFPPointSet]
                                    for h in self.Instance.HospitalSet]
                                    for r in self.Instance.PlateletAgeSet]
                                    for c in self.Instance.BloodGPSet]
                                    for t in self.ForwardStage.RangePeriodApheresisAssignment]
        #if Constants.Debug: print("value of TransshipmentHI variables:\n ", valueofvariable_b)
        
        ################################## TransshipmentIIValues
        valueofvariable_bPrime = [[[[[self.ForwardStage.TransshipmentIIValues[w][t][c][r][i][iprime]
                                        for iprime in self.Instance.ACFPPointSet]
                                        for i in self.Instance.ACFPPointSet]
                                        for r in self.Instance.PlateletAgeSet]
                                        for c in self.Instance.BloodGPSet]
                                        for t in self.ForwardStage.RangePeriodApheresisAssignment]
        #if Constants.Debug: print("value of TransshipmentII variables:\n ", valueofvariable_bPrime)
        
        ################################## TransshipmentHHValues
        valueofvariable_DoublebPrime = [[[[[self.ForwardStage.TransshipmentHHValues[w][t][c][r][h][hprime]
                                            for hprime in self.Instance.HospitalSet]
                                            for h in self.Instance.HospitalSet]
                                            for r in self.Instance.PlateletAgeSet]
                                            for c in self.Instance.BloodGPSet]
                                            for t in self.ForwardStage.RangePeriodApheresisAssignment]
        #if Constants.Debug: print("value of TransshipmentHH variables:\n ", valueofvariable_DoublebPrime)
        
        ################################## PatientTransferValues
        valueofvariable_q = [[[[[[self.ForwardStage.PatientTransferValues[w][t][j][c][l][u][m]
                                            for m in self.Instance.RescueVehicleSet]
                                            for u in self.Instance.FacilitySet]
                                            for l in self.Instance.DemandSet]
                                            for c in self.Instance.BloodGPSet]
                                            for j in self.Instance.InjuryLevelSet]
                                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("value of PatientTransfer variables:\n ", valueofvariable_q)
        
        ################################## UnsatisfiedPatientsValues
        valueofvariable_mu = [[[[self.ForwardStage.UnsatisfiedPatientsValues[w][t][j][c][l]
                                            for l in self.Instance.DemandSet]
                                            for c in self.Instance.BloodGPSet]
                                            for j in self.Instance.InjuryLevelSet]
                                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("value of UnsatisfiedPatients variables:\n ", valueofvariable_mu)
        
        ################################## PlateletInventoryValues
        valueofvariable_eta = [[[[self.ForwardStage.PlateletInventoryValues[w][t][c][r][u]
                                            for u in self.Instance.FacilitySet]
                                            for r in self.Instance.PlateletAgeSet]
                                            for c in self.Instance.BloodGPSet]
                                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("value of PlateletInventory variables:\n ", valueofvariable_eta)
        
        ################################## OutdatedPlateletValues
        valueofvariable_sigmavar = [[self.ForwardStage.OutdatedPlateletValues[w][t][u]
                                    for u in self.Instance.FacilitySet]
                                    for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("value of OutdatedPlatelet variables:\n ", valueofvariable_sigmavar)
        
        ################################## ServedPatientValues
        valueofvariable_upsilon = [[[[[[self.ForwardStage.ServedPatientValues[w][t][j][cprime][c][r][u]
                                            for u in self.Instance.FacilitySet]
                                            for r in self.Instance.PlateletAgeSet]
                                            for c in self.Instance.BloodGPSet]
                                            for cprime in self.Instance.BloodGPSet]
                                            for j in self.Instance.InjuryLevelSet]
                                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("value of ServedPatient variables:\n ", valueofvariable_upsilon)
        
        ################################## PatientPostponementValues
        valueofvariable_zeta = [[[[self.ForwardStage.PatientPostponementValues[w][t][j][c][u]
                                            for u in self.Instance.FacilitySet]
                                            for c in self.Instance.BloodGPSet]
                                            for j in self.Instance.InjuryLevelSet]
                                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("value of PatientPostponement variables:\n ", valueofvariable_zeta)
        
        ################################## PlateletApheresisExtractionValues
        valueofvariable_lambda = [[[self.ForwardStage.PlateletApheresisExtractionValues[w][t][c][u]
                                            for u in self.Instance.FacilitySet]
                                            for c in self.Instance.BloodGPSet]
                                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("value of PlateletApheresisExtraction variables:\n ", valueofvariable_lambda)
        
        ################################## PlateletWholeExtractionValues
        valueofvariable_Rhovar = [[[self.ForwardStage.PlateletWholeExtractionValues[w][t][c][h]
                                            for h in self.Instance.HospitalSet]
                                            for c in self.Instance.BloodGPSet]
                                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("value of PlateletWholeExtraction variables:\n ", valueofvariable_Rhovar)
        
        valueofvariable_x = []
        valueofvariable_thetavar = []
        if self.BackwarStage.DecisionStage == 0:
            ################################## ACFEstablishmentValues
            valueofvariable_x = [self.ForwardStage.ACFEstablishmentValues[w][i]
                                    for i in self.Instance.ACFPPointSet]
            if Constants.Debug: print("value of ACFEstablishment variables:\n ", valueofvariable_x)
            
            ################################## VehicleAssignmentValues
            valueofvariable_thetavar = [[self.ForwardStage.VehicleAssignmentValues[w][m][i]
                                        for i in self.Instance.ACFPPointSet]
                                        for m in self.Instance.RescueVehicleSet]
            if Constants.Debug: print("value of VehicleAssignment variables:\n ", valueofvariable_thetavar)

        valueofvariable = valueofvariable_y + valueofvariable_b + valueofvariable_bPrime \
                            + valueofvariable_DoublebPrime + valueofvariable_q + valueofvariable_mu \
                            + valueofvariable_eta + valueofvariable_sigmavar + valueofvariable_upsilon \
                            + valueofvariable_zeta + valueofvariable_lambda + valueofvariable_Rhovar \
                            + valueofvariable_x + valueofvariable_thetavar
        #if Constants.Debug: print("valueofvariable:\n", valueofvariable)

        coefficientvariableatstage, CostToGo_coeff, \
                y_coeff, b_coeff, bPrime_coeff, bDoublePrime_coeff, \
                q_coeff, mu_coeff, eta_coeff, sigmavar_coeff, upsilon_coeff, zeta_coeff, lambda_coeff, Rhovar_coeff, \
                x_coeff, thetavar_coeff, \
                CutRHS_coeff = self.GetCutVariablesCoefficientAtStage()
        
        #if Constants.Debug: print("coefficient of variables at stage:\n ", coefficientvariableatstage)

        coefficientvariableatstage = coefficientvariableatstage[1:-1]

        #Chaging from Multi-dimensional list to a 1D flat list to be able to do the multiplications!
        flat_valueofvariable = list(Tool.flatten(valueofvariable))
        #if Constants.Debug: print("flat_valueofvariable:\n ", flat_valueofvariable)
        flat_coefficientvariableatstage = list(Tool.flatten(coefficientvariableatstage))
        #if Constants.Debug: print("flat_coefficientvariableatstage:\n ", flat_coefficientvariableatstage)

        valueofvarsinconsraint = sum(i[0] * i[1] for i in zip(flat_valueofvariable, flat_coefficientvariableatstage))
        if Constants.Debug: print("value of vars in consraint: ", valueofvarsinconsraint)

        if Constants.Debug:
            for i, (coef, val) in enumerate(zip(coefficientvariableatstage, valueofvariable)):
                print('----------------')
                print(f"Coefficient {i}: {coef}, \nValue {i}: {val}")

        
        RHS = self.ComputeRHSFromPreviousStage(False) + self.GetRHS()

        costtogo = RHS - valueofvarsinconsraint

        return costtogo

    def IncreasePReviousCutRHS(self, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreasePReviousCutRHS)")

        self.PreviousCutRHS = self.PreviousCutRHS + value

    def IncreaseHospitalTreatmentCapacityRHS(self, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseHospitalTreatmentCapacityRHS)")

        self.HospitalCapRHS = self.HospitalCapRHS + value

    def IncreaseHospitalRescueVehicleCapacityRHS(self, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseHospitalRescueVehicleCapacityRHS)")

        self.HospitalRescueVehicleCapacityRHS = self.HospitalRescueVehicleCapacityRHS + value

    def IncreaseHospitalApheresisCapacityRHS(self, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseHospitalApheresisCapacityRHS)")
        
        self.HospitalApheresisCapacityRHS = self.HospitalApheresisCapacityRHS + value
    
    def IncreaseNrApheresisLimitRHS(self, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseNrApheresisLimitRHS)")

        self.NrApheresisLimitRHS = self.NrApheresisLimitRHS + value
    
    def IncreaseSupplyCapacityRHS(self, value):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (IncreaseSupplyCapacityRHS)")

        self.SupplyCapacityRHS = self.SupplyCapacityRHS + value

    def IncreaseInitInventryRHS(self, value):
        self.InitialInventoryRHS = self.InitialInventoryRHS + value

    def GetCostToGoLBInCorePoint(self, w):
        if Constants.Debug: print("\n We are in 'SDDPCut' Class -- (GetCostToGoLBInCorePoint)")
        variablofstage = self.GetCutVariablesAtStage(self.ForwardStage, 0)

        #Remove cost to go
        variablofstage = variablofstage[1:]

        ################################## CorePointApheresisAssignmentValues
        valueofvariable_y = [[self.ForwardStage.CorePointApheresisAssignmentValues[w][t][i]
                                for i in self.Instance.ACFPPointSet]
                                for t in self.ForwardStage.RangePeriodApheresisAssignment]
        #if Constants.Debug: print("value of ApheresisAssignment variables:\n ", valueofvariable_y)

        ################################## CorePointTransshipmentHIValues
        valueofvariable_b = [[[[[self.ForwardStage.CorePointTransshipmentHIValues[w][t][c][r][h][i]
                                    for i in self.Instance.ACFPPointSet]
                                    for h in self.Instance.HospitalSet]
                                    for r in self.Instance.PlateletAgeSet]
                                    for c in self.Instance.BloodGPSet]
                                    for t in self.ForwardStage.RangePeriodApheresisAssignment]
        #if Constants.Debug: print("value of TransshipmentHI variables:\n ", valueofvariable_b)
        
        ################################## CorePointTransshipmentIIValues
        valueofvariable_bPrime = [[[[[self.ForwardStage.CorePointTransshipmentIIValues[w][t][c][r][i][iprime]
                                        for iprime in self.Instance.ACFPPointSet]
                                        for i in self.Instance.ACFPPointSet]
                                        for r in self.Instance.PlateletAgeSet]
                                        for c in self.Instance.BloodGPSet]
                                        for t in self.ForwardStage.RangePeriodApheresisAssignment]
        #if Constants.Debug: print("value of TransshipmentII variables:\n ", valueofvariable_bPrime)
        
        ################################## CorePointTransshipmentHHValues
        valueofvariable_DoublebPrime = [[[[[self.ForwardStage.CorePointTransshipmentHHValues[w][t][c][r][h][hprime]
                                            for hprime in self.Instance.HospitalSet]
                                            for h in self.Instance.HospitalSet]
                                            for r in self.Instance.PlateletAgeSet]
                                            for c in self.Instance.BloodGPSet]
                                            for t in self.ForwardStage.RangePeriodApheresisAssignment]
        #if Constants.Debug: print("value of TransshipmentHH variables:\n ", valueofvariable_DoublebPrime)
        
        ################################## CorePointPatientTransferValues
        valueofvariable_q = [[[[[[self.ForwardStage.CorePointPatientTransferValues[w][t][j][c][l][u][m]
                                            for m in self.Instance.RescueVehicleSet]
                                            for u in self.Instance.FacilitySet]
                                            for l in self.Instance.DemandSet]
                                            for c in self.Instance.BloodGPSet]
                                            for j in self.Instance.InjuryLevelSet]
                                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("value of PatientTransfer variables:\n ", valueofvariable_q)
        
        ################################## CorePointUnsatisfiedPatientsValues
        valueofvariable_mu = [[[[self.ForwardStage.CorePointUnsatisfiedPatientsValues[w][t][j][c][l]
                                            for l in self.Instance.DemandSet]
                                            for c in self.Instance.BloodGPSet]
                                            for j in self.Instance.InjuryLevelSet]
                                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("value of UnsatisfiedPatients variables:\n ", valueofvariable_mu)
        
        ################################## CorePointPlateletInventoryValues
        valueofvariable_eta = [[[[self.ForwardStage.CorePointPlateletInventoryValues[w][t][c][r][u]
                                            for u in self.Instance.FacilitySet]
                                            for r in self.Instance.PlateletAgeSet]
                                            for c in self.Instance.BloodGPSet]
                                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("value of PlateletInventory variables:\n ", valueofvariable_eta)
        
        ################################## CorePointOutdatedPlateletValues
        valueofvariable_sigmavar = [[self.ForwardStage.CorePointOutdatedPlateletValues[w][t][u]
                                    for u in self.Instance.FacilitySet]
                                    for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("value of OutdatedPlatelet variables:\n ", valueofvariable_sigmavar)
        
        ################################## CorePointServedPatientValues
        valueofvariable_upsilon = [[[[[[self.ForwardStage.CorePointServedPatientValues[w][t][j][cprime][c][r][u]
                                            for u in self.Instance.FacilitySet]
                                            for r in self.Instance.PlateletAgeSet]
                                            for c in self.Instance.BloodGPSet]
                                            for cprime in self.Instance.BloodGPSet]
                                            for j in self.Instance.InjuryLevelSet]
                                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("value of ServedPatient variables:\n ", valueofvariable_upsilon)
        
        ################################## CorePointPatientPostponementValues
        valueofvariable_zeta = [[[[self.ForwardStage.CorePointPatientPostponementValues[w][t][j][c][u]
                                            for u in self.Instance.FacilitySet]
                                            for c in self.Instance.BloodGPSet]
                                            for j in self.Instance.InjuryLevelSet]
                                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("value of PatientPostponement variables:\n ", valueofvariable_zeta)
        
        ################################## CorePointPlateletApheresisExtractionValues
        valueofvariable_lambda = [[[self.ForwardStage.CorePointPlateletApheresisExtractionValues[w][t][c][u]
                                            for u in self.Instance.FacilitySet]
                                            for c in self.Instance.BloodGPSet]
                                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("value of PlateletApheresisExtraction variables:\n ", valueofvariable_lambda)
        
        ################################## CorePointPlateletWholeExtractionValues
        valueofvariable_Rhovar = [[[self.ForwardStage.CorePointPlateletWholeExtractionValues[w][t][c][h]
                                            for h in self.Instance.HospitalSet]
                                            for c in self.Instance.BloodGPSet]
                                            for t in self.ForwardStage.RangePeriodPatientTransfer]
        #if Constants.Debug: print("value of PlateletWholeExtraction variables:\n ", valueofvariable_Rhovar)
        
        valueofvariable_x = []
        valueofvariable_thetavar = []
        if self.BackwarStage.DecisionStage == 0:
            ################################## CorePointACFEstablishmentValues
            valueofvariable_x = [self.ForwardStage.CorePointACFEstablishmentValues[w][i]
                                    for i in self.Instance.ACFPPointSet]
            if Constants.Debug: print("value of ACFEstablishment variables:\n ", valueofvariable_x)
            
            ################################## CorePointVehicleAssignmentValues
            valueofvariable_thetavar = [[self.ForwardStage.CorePointVehicleAssignmentValues[w][m][i]
                                        for i in self.Instance.ACFPPointSet]
                                        for m in self.Instance.RescueVehicleSet]
            if Constants.Debug: print("value of VehicleAssignment variables:\n ", valueofvariable_thetavar)

        valueofvariable = valueofvariable_y + valueofvariable_b + valueofvariable_bPrime \
                            + valueofvariable_DoublebPrime + valueofvariable_q + valueofvariable_mu \
                            + valueofvariable_eta + valueofvariable_sigmavar + valueofvariable_upsilon \
                            + valueofvariable_zeta + valueofvariable_lambda + valueofvariable_Rhovar \
                            + valueofvariable_x + valueofvariable_thetavar
        #if Constants.Debug: print("valueofvariable:\n", valueofvariable)

        coefficientvariableatstage, CostToGo_coeff, \
                y_coeff, b_coeff, bPrime_coeff, bDoublePrime_coeff, \
                q_coeff, mu_coeff, eta_coeff, sigmavar_coeff, upsilon_coeff, zeta_coeff, lambda_coeff, Rhovar_coeff, \
                x_coeff, thetavar_coeff, \
                CutRHS_coeff = self.GetCutVariablesCoefficientAtStage()
        
        #if Constants.Debug: print("coefficient of variables at stage:\n ", coefficientvariableatstage)

        coefficientvariableatstage = coefficientvariableatstage[1:-1]

        #Chaging from Multi-dimensional list to a 1D flat list to be able to do the multiplications!
        flat_valueofvariable = list(Tool.flatten(valueofvariable))
        #if Constants.Debug: print("flat_valueofvariable:\n ", flat_valueofvariable)
        flat_coefficientvariableatstage = list(Tool.flatten(coefficientvariableatstage))
        #if Constants.Debug: print("flat_coefficientvariableatstage:\n ", flat_coefficientvariableatstage)

        valueofvarsinconsraint = sum(i[0] * i[1] for i in zip(flat_valueofvariable, flat_coefficientvariableatstage))
        if Constants.Debug: print("value of vars in consraint: ", valueofvarsinconsraint)

        if Constants.Debug:
            for i, (coef, val) in enumerate(zip(coefficientvariableatstage, valueofvariable)):
                print('----------------')
                print(f"Coefficient {i}: {coef}, \nValue {i}: {val}")

        
        RHS = self.ComputeRHSFromPreviousStage(False) + self.GetRHS()

        costtogo = RHS - valueofvarsinconsraint

        return costtogo





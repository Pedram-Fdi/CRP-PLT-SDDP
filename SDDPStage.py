import math
import sys
from Constants import Constants
from SDDPCut import SDDPCut
#from SDDPMLCut import SDDPMLCut
import gurobipy as gp
from gurobipy import *
import os

from ScenarioTree import ScenarioTree
import itertools

# This class contains the attributes and methodss allowing to define one stage of the SDDP algorithm.
class SDDPStage(object):

    def __init__(self, owner=None, previousstage=None, nextstage=None, decisionstage=-1, fixedscenarioset=[],
                 forwardstage=None, isforward=False, futurscenarioset = []):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (Constructor)")

        self.SDDPOwner = owner
        self.PreviousSDDPStage = previousstage
        self.NextSDDPStage = nextstage
        self.CorrespondingForwardStage = forwardstage
        self.IsForward = isforward
        self.SDDPCuts = []
        #A GRB MIP object will be associated to each stage later.
        self.GurobiModel = gp.Model("SDDPStageModel")
        #The variable MIPDefined is turned to True when the MIP is built
        self.MIPDefined = False
        self.DecisionStage = decisionstage
        #self.TimeDecisionStage corresponds to the period of the first quantity variables in the stage
        self.TimeDecisionStage = -1
        self.TimeObservationStage = -1
        self.Instance = self.SDDPOwner.Instance

        #The following attribute will contain the coefficient of the variable in the cuts
        self.CoefficientConstraint = []
        #The following table constains the value at which the variables are fixed
        self.VariableFixedTo = []


        self.EVPIScenarioSet = None
        self.EVPIScenarioRange = range(Constants.SDDPNrEVPIScenario)

        # Set of scenario used to build the MIP
        self.FixedScenarioSet = fixedscenarioset
        self.FuturScenario = futurscenarioset
        self.FixedScenarioPobability = []

        #The number of variable of each type in the stage will be set later
        self.NrACFEstablishmentVariables = 0
        self.NrVehicleAssignmentVariables = 0

        self.NrApheresisAssignmentVariables = 0
        self.NrTransshipmentHIVariables = 0
        self.NrTransshipmentIIVariables = 0
        self.NrTransshipmentHHVariables = 0
        
        self.NrPatientTransferVariables = 0
        self.NrUnsatisfiedPatientsVariables = 0
        self.NrPlateletInventoryVariables = 0
        self.NrOutdatedPlateletVariables = 0
        self.NrServedPatientVariables = 0
        self.NrPatientPostponementVariables = 0
        self.NrPlateletApheresisExtractionVariables = 0
        self.NrPlateletWholeExtractionVariables = 0

        self.NrCostToGo = 0

        self.NRFlowUnsatisfiedLowMedPatientsFromPreviousStage = 0
        self.NRFlowUnsatisfiedHighPatientsFromPreviousStage = 0
        self.NRFlowUnservedLowMedPatientsFromPreviousStage = 0
        self.NRFlowUnservedHighPatientsFromPreviousStage = 0
        self.NRFlowUnservedACFFromPreviousStage = 0
        self.NRFlowUnservedHospitalFromPreviousStage = 0
        self.NRFlowPLTInvTransHospitalFromPreviousStage = 0
        self.NRFlowPLTInvTransACFFromPreviousStage = 0
        self.NRFlowApheresisAssignmentFromPreviousStage = 0

        self.NRACFEstablishmentRHS_ACFTreatCapConst = 0
        self.NRACFEstablishmentRHS_ApheresisAssignCons = 0
        self.NRVehicleAssignmentRHS_ACFRescVehCapCons = 0

        self.NrEstmateCostToGoPerItemPeriod = 0

        self.NrPIACFEstablishment = 0
        self.NrPIVehicleAssignment = 0

        self.NrPIApheresisAssignment = 0
        self.NrPITransshipmentHI = 0
        self.NrPITransshipmentII = 0
        self.NrPITransshipmentHH = 0

        self.NrPIPatientTransfer = 0
        self.NrPIUnsatisfiedPatients = 0
        self.NrPIPlateletInventory = 0
        self.NrPIOutdatedPlatelet = 0
        self.NrPIServedPatient = 0
        self.NrPIPatientPostponement = 0
        self.NrPIPlateletApheresisExtraction = 0
        self.NrPIPlateletWholeExtraction = 0

        self.NrEstmateCostToGoEVPI = 0

        # self.NrPIFlowUnsatisfiedLowMedPatientsFromPreviousStage = 0
        # self.NrPIFlowUnsatisfiedHighPatientsFromPreviousStage = 0
        # self.NrPIFlowUnservedLowMedPatientsFromPreviousStage = 0
        # self.NrPIFlowUnservedHighPatientsFromPreviousStage = 0
        # self.NrPIFlowUnservedACFFromPreviousStage = 0
        # self.NrPIFlowUnservedHospitalFromPreviousStage = 0
        self.NrPIFlowPLTInvTransHospitalFromPreviousWholeProduction = 0
        # self.NrPIFlowPLTInvTransACFFromPreviousStage = 0
        # self.NrPIFlowApheresisAssignmentFromPreviousStage = 0
        
        ################## The start of the index of each variable
        self.StartACFEstablishment = 0
        self.StartVehicleAssignment = 0

        self.StartApheresisAssignment = 0
        self.StartTransshipmentHI = 0
        self.StartTransshipmentII = 0
        self.StartTransshipmentHH = 0

        self.StartPatientTransfer = 0     
        self.StartUnsatisfiedPatients = 0     
        self.StartPlateletInventory = 0     
        self.StartOutdatedPlatelet = 0     
        self.StartServedPatient = 0     
        self.StartPatientPostponement = 0     
        self.StartPlateletApheresisExtraction = 0     
        self.StartPlateletWholeExtraction = 0     

        self.StartCostToGo = 0

        self.StartFlowUnsatisfiedLowMedPatientsFromPreviousStage = 0
        self.StartFlowUnsatisfiedHighPatientsFromPreviousStage = 0
        self.StartFlowUnservedLowMedPatientsFromPreviousStage = 0
        self.StartFlowUnservedHighPatientsFromPreviousStage = 0
        self.StartFlowUnservedACFFromPreviousStage = 0
        self.StartFlowUnservedHospitalFromPreviousStage = 0
        self.StartFlowPLTInvTransHospitalFromPreviousStage = 0
        self.StartFlowPLTInvTransACFFromPreviousStage = 0
        self.StartFlowApheresisAssignmentFromPreviousStage = 0

        self.StartACFEstablishmentRHS_ACFTreatCapConst = 0
        self.StartACFEstablishmentRHS_ApheresisAssignCons = 0
        self.StartVehicleAssignmentRHS_ACFRescVehCapCons = 0


        self.StartEstmateCostToGoPerItemPeriod = 0

        self.StartPIACFEstablishment = 0
        self.StartPIVehicleAssignment = 0

        self.StartPIApheresisAssignment = 0
        self.StartPITransshipmentHI = 0
        self.StartPITransshipmentII = 0
        self.StartPITransshipmentHH = 0

        self.StartPIPatientTransfer = 0
        self.StartPIUnsatisfiedPatients = 0
        self.StartPIPlateletInventory = 0
        self.StartPIOutdatedPlatelet = 0
        self.StartPIServedPatient = 0
        self.StartPIPatientPostponement = 0
        self.StartPIPlateletApheresisExtraction = 0
        self.StartPIPlateletWholeExtraction = 0

        # self.StartPIFlowUnsatisfiedLowMedPatientsFromPreviousStage = 0
        # self.StartPIFlowUnsatisfiedHighPatientsFromPreviousStage = 0
        # self.StartPIFlowUnservedLowMedPatientsFromPreviousStage = 0
        # self.StartPIFlowUnservedHighPatientsFromPreviousStage = 0
        # self.StartPIFlowUnservedACFFromPreviousStage = 0
        # self.StartPIFlowUnservedHospitalFromPreviousStage = 0
        self.StartPIFlowPLTInvTransHospitalFromPreviousWholeProduction = 0
        # self.StartPIFlowPLTInvTransACFFromPreviousStage = 0
        # self.StartPIFlowApheresisAssignmentFromPreviousStage = 0


        self.StartPICostToGoEVPI = 0

        self.StartCutRHSVariable = 0

        # Demand and materials requirement: set the value of the invetory level and backorder quantity according to
        #  the quantities produced and the demand
        self.CurrentTrialNr = -1
        #The ACFEstablishmentValues & VehicleAssignmentValues (filled after having solve the MIPs for all scenario)
        self.ACFEstablishmentValues = []
        self.VehicleAssignmentValues = []

        # The ApheresisAssignmentValues and others  (filled after having solve the MIPs for all scenario)
        self.ApheresisAssignmentValues = []
        self.TransshipmentHIValues = []
        self.TransshipmentIIValues = []
        self.TransshipmentHHValues = []

        #The PatientTransferValues and others (filled after having solve the MIPs for all scenario)
        self.PatientTransferValues = []
        self.UnsatisfiedPatientsValues = []
        self.PlateletInventoryValues = []
        self.OutdatedPlateletValues = []
        self.ServedPatientValues = []
        self.PatientPostponementValues = []
        self.PlateletApheresisExtractionValues = []
        self.PlateletWholeExtractionValues = []
        
        ################## Try to use the corepoint method of papadakos, remove if it doesn't work
        self.CorePointACFEstablishmentValues = []
        self.CorePointVehicleAssignmentValues = []

        self.CorePointApheresisAssignmentValues = []   
        self.CorePointTransshipmentHIValues = []   
        self.CorePointTransshipmentIIValues = []   
        self.CorePointTransshipmentHHValues = []   

        self.CorePointPatientTransferValues = []
        self.CorePointUnsatisfiedPatientsValues = []
        self.CorePointPlateletInventoryValues = []
        self.CorePointOutdatedPlateletValues = []
        self.CorePointServedPatientValues = []
        self.CorePointPatientPostponementValues = []
        self.CorePointPlateletApheresisExtractionValues = []
        self.CorePointPlateletWholeExtractionValues = []

        ################## The cost of each scenario
        self.StageCostPerScenarioWithoutCostoGo = []
        self.StageCostPerScenarioWithCostoGo = []
        self.PartialCostPerScenario = []
        self.PassCost = -1
        self.NrTrialScenario = -1

        self.LastAddedConstraintIndex = 0

        ################## Related To BudgetConstraint
        self.IndexBudgetConstraint = []
        #self.IndexBudgetConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.BudgetConstraint_Names = []  
        #self.ConcernedScenarioBudgetConstraint= []
        #self.ConcernedTimeBudgetConstraint= [] 
        self.PIBudgetConstraint_Names = []
        self.IndexPIBudgetConstraint = []
        #self.IndexPIBudgetConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        #self.ConcernedScenarioPIBudgetConstraint= []
        #self.ConcernedTimePIBudgetConstraint= []

        ################## Related To VehicleAssignmentCapacityConstraint
        self.IndexVehicleAssignmentCapacityConstraint = []
        #self.IndexVehicleAssignmentCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.VehicleAssignmentCapacityConstraint_Names = []  
        self.ConcernedVehicleVehicleAssignmentCapacityConstraint = []
        #self.ConcernedScenarioVehicleAssignmentCapacityConstraint= []
        #self.ConcernedTimeVehicleAssignmentCapacityConstraint= [] 
        self.PIVehicleAssignmentCapacityConstraint_Names = []
        self.IndexPIVehicleAssignmentCapacityConstraint = []
        #self.IndexPIVehicleAssignmentCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedVehiclePIVehicleAssignmentCapacityConstraint = []
        #self.ConcernedScenarioPIVehicleAssignmentCapacityConstraint= []
        #self.ConcernedTimePIVehicleAssignmentCapacityConstraint= []

        ################## Related To VehicleAssignemntACFEstablishmentConstraint
        self.IndexVehicleAssignemntACFEstablishmentConstraint = []
        #self.IndexVehicleAssignemntACFEstablishmentConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.VehicleAssignemntACFEstablishmentConstraint_Names = []  
        self.ConcernedvehicleVehicleAssignemntACFEstablishmentConstraint = []
        self.ConcernedACFVehicleAssignemntACFEstablishmentConstraint = []
        #self.ConcernedScenarioVehicleAssignemntACFEstablishmentConstraint= []
        #self.ConcernedTimeVehicleAssignemntACFEstablishmentConstraint= [] 
        self.PIVehicleAssignemntACFEstablishmentConstraint_Names = []
        self.IndexPIVehicleAssignemntACFEstablishmentConstraint = []
        #self.IndexPIVehicleAssignemntACFEstablishmentConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedVehiclePIVehicleAssignemntACFEstablishmentConstraint = []
        self.ConcernedACFPIVehicleAssignemntACFEstablishmentConstraint = []
        #self.ConcernedScenarioPIVehicleAssignemntACFEstablishmentConstraint= []
        #self.ConcernedTimePIVehicleAssignemntACFEstablishmentConstraint= []

        ################## Related To LowMedPriorityPatientFlowConstraint
        self.LowMedPriorityPatientFlowConstraint_Objects = []
        self.IndexLowMedPriorityPatientFlowConstraint = []
        self.IndexLowMedPriorityPatientFlowConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.LowMedPriorityPatientFlowConstraint_Names = []  
        self.ConcernedInjuryLowMedPriorityPatientFlowConstraint = []
        self.ConcernedBloodGPLowMedPriorityPatientFlowConstraint = []
        self.ConcernedDemandLowMedPriorityPatientFlowConstraint = []
        self.ConcernedScenarioLowMedPriorityPatientFlowConstraint = []
        self.ConcernedTimeLowMedPriorityPatientFlowConstraint = [] 
        self.PILowMedPriorityPatientFlowConstraint_Names = []          
        self.IndexPILowMedPriorityPatientFlowConstraint = []
        self.IndexPILowMedPriorityPatientFlowConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedInjuryPILowMedPriorityPatientFlowConstraint = []
        self.ConcernedBloodGPPILowMedPriorityPatientFlowConstraint = []
        self.ConcernedDemandPILowMedPriorityPatientFlowConstraint = []
        self.ConcernedScenarioPILowMedPriorityPatientFlowConstraint = []
        self.ConcernedTimePILowMedPriorityPatientFlowConstraint = [] 
        self.ConcernedEVPIScenarioPILowMedPriorityPatientFlowConstraint = []  

        ################## Related To HighPriorityPatientFlowConstraint
        self.HighPriorityPatientFlowConstraint_Objects = []
        self.IndexHighPriorityPatientFlowConstraint = []
        self.IndexHighPriorityPatientFlowConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.HighPriorityPatientFlowConstraint_Names = []  # Store constraint names here
        self.PIHighPriorityPatientFlowConstraint_Names = []  # Store constraint names here
        self.ConcernedInjuryHighPriorityPatientFlowConstraint = []
        self.ConcernedBloodGPHighPriorityPatientFlowConstraint = []
        self.ConcernedDemandHighPriorityPatientFlowConstraint = []
        self.ConcernedScenarioHighPriorityPatientFlowConstraint = []
        self.ConcernedTimeHighPriorityPatientFlowConstraint = [] 
        self.IndexPIHighPriorityPatientFlowConstraint = []
        self.IndexPIHighPriorityPatientFlowConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedInjuryPIHighPriorityPatientFlowConstraint = []
        self.ConcernedBloodGPPIHighPriorityPatientFlowConstraint = []
        self.ConcernedDemandPIHighPriorityPatientFlowConstraint = []
        self.ConcernedScenarioPIHighPriorityPatientFlowConstraint = []
        self.ConcernedTimePIHighPriorityPatientFlowConstraint = [] 
        self.ConcernedEVPIScenarioPIHighPriorityPatientFlowConstraint = []   

        ################## Related To LowMedPriorityPatientServiceConstraint
        self.IndexLowMedPriorityPatientServiceConstraint = []
        self.IndexLowMedPriorityPatientServiceConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.LowMedPriorityPatientServiceConstraint_Names = [] 
        self.ConcernedInjuryLowMedPriorityPatientServiceConstraint = []
        self.ConcernedBloodGPLowMedPriorityPatientServiceConstraint = []
        self.ConcernedFacilityLowMedPriorityPatientServiceConstraint = []
        self.ConcernedScenarioLowMedPriorityPatientServiceConstraint= []
        self.ConcernedTimeLowMedPriorityPatientServiceConstraint= [] 
        self.PILowMedPriorityPatientServiceConstraint_Names = []
        self.IndexPILowMedPriorityPatientServiceConstraint = []
        self.IndexPILowMedPriorityPatientServiceConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedInjuryPILowMedPriorityPatientServiceConstraint = []
        self.ConcernedBloodGPPILowMedPriorityPatientServiceConstraint = []
        self.ConcernedFacilityPILowMedPriorityPatientServiceConstraint = []
        self.ConcernedScenarioPILowMedPriorityPatientServiceConstraint= []
        self.ConcernedTimePILowMedPriorityPatientServiceConstraint= [] 

        ################## Related To HighPriorityPatientServiceConstraint
        self.IndexHighPriorityPatientServiceConstraint = []
        self.IndexHighPriorityPatientServiceConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.HighPriorityPatientServiceConstraint_Names = [] 
        self.ConcernedInjuryHighPriorityPatientServiceConstraint = []
        self.ConcernedBloodGPHighPriorityPatientServiceConstraint = []
        self.ConcernedHospitalHighPriorityPatientServiceConstraint = []
        self.ConcernedScenarioHighPriorityPatientServiceConstraint= []
        self.ConcernedTimeHighPriorityPatientServiceConstraint= [] 
        self.PIHighPriorityPatientServiceConstraint_Names = []
        self.IndexPIHighPriorityPatientServiceConstraint = []
        self.IndexPIHighPriorityPatientServiceConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedInjuryPIHighPriorityPatientServiceConstraint = []
        self.ConcernedBloodGPPIHighPriorityPatientServiceConstraint = []
        self.ConcernedHospitalPIHighPriorityPatientServiceConstraint = []
        self.ConcernedScenarioPIHighPriorityPatientServiceConstraint= []
        self.ConcernedTimePIHighPriorityPatientServiceConstraint= [] 

        ################## Related To ACFTreatmentCapacityConstraint
        self.IndexACFTreatmentCapacityConstraint = []
        self.IndexACFTreatmentCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ACFTreatmentCapacityConstraint_Names = []  
        self.ConcernedACFACFTreatmentCapacityConstraint = []
        self.ConcernedScenarioACFTreatmentCapacityConstraint= []
        self.ConcernedTimeACFTreatmentCapacityConstraint= [] 
        self.PIACFTreatmentCapacityConstraint_Names = []
        self.IndexPIACFTreatmentCapacityConstraint = []
        self.IndexPIACFTreatmentCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedACFPIACFTreatmentCapacityConstraint = []
        self.ConcernedScenarioPIACFTreatmentCapacityConstraint= []
        self.ConcernedTimePIACFTreatmentCapacityConstraint= []      

        ################## Related To HospitalTreatmentCapacityConstraint
        self.HospitalTreatmentCapacityConstraint_Objects = []
        self.IndexHospitalTreatmentCapacityConstraint = []
        self.IndexHospitalTreatmentCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.HospitalTreatmentCapacityConstraint_Names = []  
        self.ConcernedHospitalHospitalTreatmentCapacityConstraint = []
        self.ConcernedScenarioHospitalTreatmentCapacityConstraint = []
        self.ConcernedTimeHospitalTreatmentCapacityConstraint = []  
        self.PIHospitalTreatmentCapacityConstraint_Names = []  
        self.IndexPIHospitalTreatmentCapacityConstraint = []
        self.IndexPIHospitalTreatmentCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedHospitalPIHospitalTreatmentCapacityConstraint = []
        self.ConcernedScenarioPIHospitalTreatmentCapacityConstraint = []
        self.ConcernedTimePIHospitalTreatmentCapacityConstraint = [] 
        self.ConcernedEVPIScenarioPIHospitalTreatmentCapacityConstraint = [] 

        ################## Related To HospitalPlateletFlowConstraint
        self.IndexHospitalPlateletFlowConstraint = []
        self.IndexHospitalPlateletFlowConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.HospitalPlateletFlowConstraint_Names = []  
        self.ConcernedBloodGPHospitalPlateletFlowConstraint = []
        self.ConcernedPLTAgeHospitalPlateletFlowConstraint = []
        self.ConcernedHospitalHospitalPlateletFlowConstraint = []
        self.ConcernedScenarioHospitalPlateletFlowConstraint= []
        self.ConcernedTimeHospitalPlateletFlowConstraint= [] 
        self.PIHospitalPlateletFlowConstraint_Names = []
        self.IndexPIHospitalPlateletFlowConstraint = []
        self.IndexPIHospitalPlateletFlowConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedBloodGPPIHospitalPlateletFlowConstraint = []
        self.ConcernedPLTAgePIHospitalPlateletFlowConstraint = []
        self.ConcernedHospitalPIHospitalPlateletFlowConstraint = []
        self.ConcernedScenarioPIHospitalPlateletFlowConstraint= []
        self.ConcernedTimePIHospitalPlateletFlowConstraint= []

        ################## Related To ACFPlateletFlowConstraint
        self.IndexACFPlateletFlowConstraint = []
        self.IndexACFPlateletFlowConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ACFPlateletFlowConstraint_Names = []  
        self.ConcernedBloodGPACFPlateletFlowConstraint = []
        self.ConcernedPLTAgeACFPlateletFlowConstraint = []
        self.ConcernedACFACFPlateletFlowConstraint = []
        self.ConcernedScenarioACFPlateletFlowConstraint= []
        self.ConcernedTimeACFPlateletFlowConstraint= [] 
        self.PIACFPlateletFlowConstraint_Names = []
        self.IndexPIACFPlateletFlowConstraint = []
        self.IndexPIACFPlateletFlowConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedBloodGPPIACFPlateletFlowConstraint = []
        self.ConcernedPLTAgePIACFPlateletFlowConstraint = []
        self.ConcernedACFPIACFPlateletFlowConstraint = []
        self.ConcernedScenarioPIACFPlateletFlowConstraint= []
        self.ConcernedTimePIACFPlateletFlowConstraint= []

        ################## Related To PlateletWastageConstraint
        self.IndexPlateletWastageConstraint = []
        self.IndexPlateletWastageConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.PlateletWastageConstraint_Names = []  
        self.ConcernedFacilityPlateletWastageConstraint = []
        self.ConcernedScenarioPlateletWastageConstraint= []
        self.ConcernedTimePlateletWastageConstraint= [] 
        self.PIPlateletWastageConstraint_Names = []
        self.IndexPIPlateletWastageConstraint = []
        self.IndexPIPlateletWastageConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedFacilityPIPlateletWastageConstraint = []
        self.ConcernedScenarioPIPlateletWastageConstraint= []
        self.ConcernedTimePIPlateletWastageConstraint= []

        ################## Related To HospitalRescueVehicleCapacityConstraint
        self.IndexHospitalRescueVehicleCapacityConstraint = []
        self.IndexHospitalRescueVehicleCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.HospitalRescueVehicleCapacityConstraint_Names = []  
        self.ConcernedHospitalHospitalRescueVehicleCapacityConstraint = []
        self.ConcernedVehicleHospitalRescueVehicleCapacityConstraint = []
        self.ConcernedScenarioHospitalRescueVehicleCapacityConstraint= []
        self.ConcernedTimeHospitalRescueVehicleCapacityConstraint= [] 
        self.PIHospitalRescueVehicleCapacityConstraint_Names = []
        self.IndexPIHospitalRescueVehicleCapacityConstraint = []
        self.IndexPIHospitalRescueVehicleCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedHospitalPIHospitalRescueVehicleCapacityConstraint = []
        self.ConcernedVehiclePIHospitalRescueVehicleCapacityConstraint = []
        self.ConcernedScenarioPIHospitalRescueVehicleCapacityConstraint= []
        self.ConcernedTimePIHospitalRescueVehicleCapacityConstraint= []

        ################## Related To ACFRescueVehicleCapacityConstraint
        self.IndexACFRescueVehicleCapacityConstraint = []
        self.IndexACFRescueVehicleCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ACFRescueVehicleCapacityConstraint_Names = []  
        self.ConcernedACFACFRescueVehicleCapacityConstraint = []
        self.ConcernedVehicleACFRescueVehicleCapacityConstraint = []
        self.ConcernedScenarioACFRescueVehicleCapacityConstraint= []
        self.ConcernedTimeACFRescueVehicleCapacityConstraint= [] 
        self.PIACFRescueVehicleCapacityConstraint_Names = []
        self.IndexPIACFRescueVehicleCapacityConstraint = []
        self.IndexPIACFRescueVehicleCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedACFPIACFRescueVehicleCapacityConstraint = []
        self.ConcernedVehiclePIACFRescueVehicleCapacityConstraint = []
        self.ConcernedScenarioPIACFRescueVehicleCapacityConstraint= []
        self.ConcernedTimePIACFRescueVehicleCapacityConstraint= []

        ################## Related To NrApheresisLimitConstraint
        self.IndexNrApheresisLimitConstraint = []
        self.IndexNrApheresisLimitConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.NrApheresisLimitConstraint_Names = []          
        self.ConcernedScenarioNrApheresisLimitConstraint= []
        self.ConcernedTimeNrApheresisLimitConstraint= [] 
        self.PINrApheresisLimitConstraint_Names = []
        self.IndexPINrApheresisLimitConstraint = []
        self.IndexPINrApheresisLimitConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedScenarioPINrApheresisLimitConstraint= []
        self.ConcernedTimePINrApheresisLimitConstraint= [] 

        ################## Related To ApheresisACFConstraint
        self.IndexApheresisACFConstraint = []
        self.IndexApheresisACFConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ApheresisACFConstraint_Names = []  
        self.ConcernedACFApheresisACFConstraint = []
        self.ConcernedScenarioApheresisACFConstraint= []
        self.ConcernedTimeApheresisACFConstraint= [] 
        self.PIApheresisACFConstraint_Names = []
        self.IndexPIApheresisACFConstraint = []
        self.IndexPIApheresisACFConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedACFPIApheresisACFConstraint = []
        self.ConcernedScenarioPIApheresisACFConstraint= []
        self.ConcernedTimePIApheresisACFConstraint= []

        ################## Related To ACFApheresisCapacityConstraint
        self.IndexACFApheresisCapacityConstraint = []
        self.IndexACFApheresisCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ACFApheresisCapacityConstraint_Names = []  
        self.ConcernedACFACFApheresisCapacityConstraint = []
        self.ConcernedScenarioACFApheresisCapacityConstraint= []
        self.ConcernedTimeACFApheresisCapacityConstraint= [] 
        self.PIACFApheresisCapacityConstraint_Names = []
        self.IndexPIACFApheresisCapacityConstraint = []
        self.IndexPIACFApheresisCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedACFPIACFApheresisCapacityConstraint = []
        self.ConcernedScenarioPIACFApheresisCapacityConstraint= []
        self.ConcernedTimePIACFApheresisCapacityConstraint= []

        ################## Related To HospitalApheresisCapacityConstraint
        self.IndexHospitalApheresisCapacityConstraint = []
        self.IndexHospitalApheresisCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.HospitalApheresisCapacityConstraint_Names = []  
        self.ConcernedHospitalHospitalApheresisCapacityConstraint = []
        self.ConcernedScenarioHospitalApheresisCapacityConstraint= []
        self.ConcernedTimeHospitalApheresisCapacityConstraint= [] 
        self.PIHospitalApheresisCapacityConstraint_Names = []
        self.IndexPIHospitalApheresisCapacityConstraint = []
        self.IndexPIHospitalApheresisCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedHospitalPIHospitalApheresisCapacityConstraint = []
        self.ConcernedScenarioPIHospitalApheresisCapacityConstraint= []
        self.ConcernedTimePIHospitalApheresisCapacityConstraint= []
                
        ################## Related To ApheresisCapacityDonorsConstraint
        self.ApheresisCapacityDonorsConstraint_Objects = []
        self.IndexApheresisCapacityDonorsConstraint = []
        self.IndexApheresisCapacityDonorsConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ApheresisCapacityDonorsConstraint_Names = []  
        self.ConcernedBloodGPApheresisCapacityDonorsConstraint = []
        self.ConcernedFacilityApheresisCapacityDonorsConstraint = []
        self.ConcernedScenarioApheresisCapacityDonorsConstraint = []
        self.ConcernedTimeApheresisCapacityDonorsConstraint = [] 
        self.PIApheresisCapacityDonorsConstraint_Names = [] 
        self.IndexPIApheresisCapacityDonorsConstraint = []
        self.IndexPIApheresisCapacityDonorsConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedBloodGPPIApheresisCapacityDonorsConstraint = []
        self.ConcernedFacilityPIApheresisCapacityDonorsConstraint = []
        self.ConcernedScenarioPIApheresisCapacityDonorsConstraint = []
        self.ConcernedTimePIApheresisCapacityDonorsConstraint = [] 
        self.ConcernedEVPIScenarioPIApheresisCapacityDonorsConstraint = []

        ################## Related To WholeCapacityDonorsConstraint
        self.WholeCapacityDonorsConstraint_Objects = []
        self.IndexWholeCapacityDonorsConstraint = []
        self.IndexWholeCapacityDonorsConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.WholeCapacityDonorsConstraint_Names = []  
        self.PIWholeCapacityDonorsConstraint_Names = [] 
        self.ConcernedBloodGPWholeCapacityDonorsConstraint = []
        self.ConcernedHospitalWholeCapacityDonorsConstraint = []
        self.ConcernedScenarioWholeCapacityDonorsConstraint = []
        self.ConcernedTimeWholeCapacityDonorsConstraint = []  
        self.IndexPIWholeCapacityDonorsConstraint = []
        self.IndexPIWholeCapacityDonorsConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedBloodGPPIWholeCapacityDonorsConstraint = []
        self.ConcernedHospitalPIWholeCapacityDonorsConstraint = []
        self.ConcernedScenarioPIWholeCapacityDonorsConstraint = []
        self.ConcernedTimePIWholeCapacityDonorsConstraint = [] 
        self.ConcernedEVPIScenarioPIWholeCapacityDonorsConstraint = []

        ################## Related To HospitalTransshipmentCapacityConstraint
        self.IndexHospitalTransshipmentCapacityConstraint = []
        self.IndexHospitalTransshipmentCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.HospitalTransshipmentCapacityConstraint_Names = [] 
        self.ConcernedBloodGPHospitalTransshipmentCapacityConstraint = []
        self.ConcernedPLTAgeHospitalTransshipmentCapacityConstraint = []
        self.ConcernedHospitalHospitalTransshipmentCapacityConstraint = []
        self.ConcernedScenarioHospitalTransshipmentCapacityConstraint= []
        self.ConcernedTimeHospitalTransshipmentCapacityConstraint= [] 
        self.PIHospitalTransshipmentCapacityConstraint_Names = []
        self.IndexPIHospitalTransshipmentCapacityConstraint = []
        self.IndexPIHospitalTransshipmentCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedBloodGPPIHospitalTransshipmentCapacityConstraint = []
        self.ConcernedPLTAgePIHospitalTransshipmentCapacityConstraint = []
        self.ConcernedHospitalPIHospitalTransshipmentCapacityConstraint = []
        self.ConcernedScenarioPIHospitalTransshipmentCapacityConstraint= []
        self.ConcernedTimePIHospitalTransshipmentCapacityConstraint= []

        ################## Related To ACFTransshipmentCapacityConstraint
        self.IndexACFTransshipmentCapacityConstraint = []
        self.IndexACFTransshipmentCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ACFTransshipmentCapacityConstraint_Names = [] 
        self.ConcernedBloodGPACFTransshipmentCapacityConstraint = []
        self.ConcernedPLTAgeACFTransshipmentCapacityConstraint = []
        self.ConcernedACFACFTransshipmentCapacityConstraint = []
        self.ConcernedScenarioACFTransshipmentCapacityConstraint= []
        self.ConcernedTimeACFTransshipmentCapacityConstraint= [] 
        self.PIACFTransshipmentCapacityConstraint_Names = []
        self.IndexPIACFTransshipmentCapacityConstraint = []
        self.IndexPIACFTransshipmentCapacityConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.ConcernedBloodGPPIACFTransshipmentCapacityConstraint = []
        self.ConcernedPLTAgePIACFTransshipmentCapacityConstraint = []
        self.ConcernedACFPIACFTransshipmentCapacityConstraint = []
        self.ConcernedScenarioPIACFTransshipmentCapacityConstraint= []
        self.ConcernedTimePIACFTransshipmentCapacityConstraint= []

        ################## Related to Cut Constraints        
        self.IndexCutConstraint = []
        self.IndexCutConstraintPerScenario = [[ ] for w in self.FixedScenarioSet]
        self.CutConstraint_Names = []  # Store constraint names here
        self.ConcernedCutinConstraint = []
        self.ConcernedScenarioCutConstraint = []



        self.RangePeriodApheresisAssignment = []
        self.RangePeriodPatientTransfer = []
        
        self.PeriodsInGlobalMIPApheresisAssignment = []
        self.PeriodsInGlobalMIPTransshipmentHI = []
        self.PeriodsInGlobalMIPTransshipmentII = []
        self.PeriodsInGlobalMIPTransshipmentHH = []

        self.PeriodsInGlobalMIPPatientTransfer = []
        self.PeriodsInGlobalMIPUnsatisfiedPatients = []
        self.PeriodsInGlobalMIPPlateletInventory = []
        self.PeriodsInGlobalMIPOutdatedPlatelet = []
        self.PeriodsInGlobalMIPServedPatient = []
        self.PeriodsInGlobalMIPPatientPostponement = []
        self.PeriodsInGlobalMIPPlateletApheresisExtraction = []
        self.PeriodsInGlobalMIPPlateletWholeExtraction = []

        #self.StockIndexArray = []

        self.FullTreeSolverDefine = False
        self.FullTreeSolver = None

        #self.Print_Attributes()

    #The variables are refered by indices to allow fast computation in GRB.
    #The method below create list to assosciate each variable to an index in the model
    def ComputeVariableIndices(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ComputeVariableIndices)")

        self.TimePeriodToGoApheresisAssignment = range(self.TimeDecisionStage + len(self.RangePeriodApheresisAssignment), self.Instance.NrTimeBucket)
        self.TimePeriodToGoTransshipmentHI = range(self.TimeDecisionStage + len(self.RangePeriodApheresisAssignment), self.Instance.NrTimeBucket)
        self.TimePeriodToGoTransshipmentII = range(self.TimeDecisionStage + len(self.RangePeriodApheresisAssignment), self.Instance.NrTimeBucket)
        self.TimePeriodToGoTransshipmentHH = range(self.TimeDecisionStage + len(self.RangePeriodApheresisAssignment), self.Instance.NrTimeBucket)

        self.TimePeriodToGoPatientTransfer = range(self.TimeObservationStage + 1, self.Instance.NrTimeBucket)
        self.TimePeriodToGoUnsatisfiedPatients = range(self.TimeObservationStage + 1, self.Instance.NrTimeBucket)
        self.TimePeriodToGoPlateletInventory = range(self.TimeObservationStage + 1, self.Instance.NrTimeBucket)
        self.TimePeriodToGoOutdatedPlatelet = range(self.TimeObservationStage + 1, self.Instance.NrTimeBucket)
        self.TimePeriodToGoServedPatient = range(self.TimeObservationStage + 1, self.Instance.NrTimeBucket)
        self.TimePeriodToGoPatientPostponement = range(self.TimeObservationStage + 1, self.Instance.NrTimeBucket)
        self.TimePeriodToGoPlateletApheresisExtraction = range(self.TimeObservationStage + 1, self.Instance.NrTimeBucket)
        self.TimePeriodToGoPlateletWholeExtraction = range(self.TimeObservationStage + 1, self.Instance.NrTimeBucket)

        self.TimePeriodToGo = range(self.TimeDecisionStage, self.Instance.NrTimeBucket)
        self.NrTimePeriodToGo = len(self.TimePeriodToGo)
        
        if Constants.Debug:
            print("RangePeriodApheresisAssignment: ",self.RangePeriodApheresisAssignment)
            print("len(self.RangePeriodVarTrans): ",len(self.RangePeriodApheresisAssignment))
            print("TimePeriodToGoApheresisAssignment: ", self.TimePeriodToGoApheresisAssignment)
            print("TimePeriodToGoTransshipmentHI: ", self.TimePeriodToGoTransshipmentHI)
            print("TimePeriodToGoTransshipmentII: ", self.TimePeriodToGoTransshipmentII)
            print("TimePeriodToGoTransshipmentHH: ", self.TimePeriodToGoTransshipmentHH)

            print("TimePeriodToGoPatientTransfer: ", self.TimePeriodToGoPatientTransfer)
            print("TimePeriodToGoUnsatisfiedPatients: ", self.TimePeriodToGoUnsatisfiedPatients)
            print("TimePeriodToGoPlateletInventory: ", self.TimePeriodToGoPlateletInventory)
            print("TimePeriodToGoOutdatedPlatelet: ", self.TimePeriodToGoOutdatedPlatelet)
            print("TimePeriodToGoServedPatient: ", self.TimePeriodToGoServedPatient)
            print("TimePeriodToGoPatientPostponement: ", self.TimePeriodToGoPatientPostponement)
            print("TimePeriodToGoPlateletApheresisExtraction: ", self.TimePeriodToGoPlateletApheresisExtraction)
            print("TimePeriodToGoPlateletWholeExtraction: ", self.TimePeriodToGoPlateletWholeExtraction)

            print("TimePeriodToGo: ", self.TimePeriodToGo)
            print("NrTimePeriodToGo: ", self.NrTimePeriodToGo)

        self.ComputeNrVariables()
        
        # The start of the index of each variable
        self.StartACFEstablishment = 0
        self.StartVehicleAssignment = self.StartACFEstablishment + self.NrACFEstablishmentVariable
        self.StartApheresisAssignment = self.StartVehicleAssignment + self.NrVehicleAssignmentVariable
        self.StartTransshipmentHI = self.StartApheresisAssignment + self.NrApheresisAssignmentVariable
        self.StartTransshipmentII = self.StartTransshipmentHI + self.NrTransshipmentHIVariable
        self.StartTransshipmentHH = self.StartTransshipmentII + self.NrTransshipmentIIVariable
        self.StartPatientTransfer = self.StartTransshipmentHH + self.NrTransshipmentHHVariable
        self.StartUnsatisfiedPatients = self.StartPatientTransfer + self.NrPatientTransferVariable
        self.StartPlateletInventory = self.StartUnsatisfiedPatients + self.NrUnsatisfiedPatientsVariable
        self.StartOutdatedPlatelet = self.StartPlateletInventory + self.NrPlateletInventoryVariable
        self.StartServedPatient = self.StartOutdatedPlatelet + self.NrOutdatedPlateletVariable
        self.StartPatientPostponement = self.StartServedPatient + self.NrServedPatientVariable
        self.StartPlateletApheresisExtraction = self.StartPatientPostponement + self.NrPatientPostponementVariable
        self.StartPlateletWholeExtraction = self.StartPlateletApheresisExtraction + self.NrPlateletApheresisExtractionVariable
        self.StartCostToGo = self.StartPlateletWholeExtraction + self.NrPlateletWholeExtractionVariable
        self.StartFlowUnsatisfiedLowMedPatientsFromPreviousStage = self.StartCostToGo + self.NrCostToGo
        self.StartFlowUnsatisfiedHighPatientsFromPreviousStage = self.StartFlowUnsatisfiedLowMedPatientsFromPreviousStage + self.NRFlowUnsatisfiedLowMedPatientsFromPreviousStage
        self.StartFlowUnservedLowMedPatientsFromPreviousStage = self.StartFlowUnsatisfiedHighPatientsFromPreviousStage + self.NRFlowUnsatisfiedHighPatientsFromPreviousStage
        self.StartFlowUnservedHighPatientsFromPreviousStage = self.StartFlowUnservedLowMedPatientsFromPreviousStage + self.NRFlowUnservedLowMedPatientsFromPreviousStage
        self.StartFlowUnservedACFFromPreviousStage = self.StartFlowUnservedHighPatientsFromPreviousStage + self.NRFlowUnservedHighPatientsFromPreviousStage
        self.StartFlowUnservedHospitalFromPreviousStage =  self.StartFlowUnservedACFFromPreviousStage + self.NRFlowUnservedACFFromPreviousStage
        self.StartFlowPLTInvTransHospitalFromPreviousStage = self.StartFlowUnservedHospitalFromPreviousStage + self.NRFlowUnservedHospitalFromPreviousStage
        self.StartFlowPLTInvTransACFFromPreviousStage = self.StartFlowPLTInvTransHospitalFromPreviousStage + self.NRFlowPLTInvTransHospitalFromPreviousStage
        self.StartFlowApheresisAssignmentFromPreviousStage = self.StartFlowPLTInvTransACFFromPreviousStage + self.NRFlowPLTInvTransACFFromPreviousStage
        self.StartACFEstablishmentRHS_ACFTreatCapConst = self.StartFlowApheresisAssignmentFromPreviousStage + self.NRFlowApheresisAssignmentFromPreviousStage
        self.StartACFEstablishmentRHS_ApheresisAssignCons = self.StartACFEstablishmentRHS_ACFTreatCapConst + self.NRACFEstablishmentRHS_ACFTreatCapConst
        self.StartVehicleAssignmentRHS_ACFRescVehCapCons = self.StartACFEstablishmentRHS_ApheresisAssignCons + self.NRACFEstablishmentRHS_ApheresisAssignCons
        self.StartEstmateCostToGoPerItemPeriod = self.StartVehicleAssignmentRHS_ACFRescVehCapCons + self.NRVehicleAssignmentRHS_ACFRescVehCapCons
        self.StartPIApheresisAssignment = self.StartEstmateCostToGoPerItemPeriod + self.NrEstmateCostToGoPerItemPeriod
        self.StartPITransshipmentHI = self.StartPIApheresisAssignment + self.NrPIApheresisAssignment
        self.StartPITransshipmentII = self.StartPITransshipmentHI + self.NrPITransshipmentHI
        self.StartPITransshipmentHH = self.StartPITransshipmentII + self.NrPITransshipmentII
        self.StartPIPatientTransfer = self.StartPITransshipmentHH + self.NrPITransshipmentHH
        self.StartPIUnsatisfiedPatients = self.StartPIPatientTransfer + self.NrPIPatientTransfer
        self.StartPIPlateletInventory = self.StartPIUnsatisfiedPatients + self.NrPIUnsatisfiedPatients
        self.StartPIOutdatedPlatelet = self.StartPIPlateletInventory + self.NrPIPlateletInventory
        self.StartPIServedPatient = self.StartPIOutdatedPlatelet + self.NrPIOutdatedPlatelet
        self.StartPIPatientPostponement = self.StartPIServedPatient + self.NrPIServedPatient
        self.StartPIPlateletApheresisExtraction = self.StartPIPatientPostponement + self.NrPIPatientPostponement
        self.StartPIPlateletWholeExtraction = self.StartPIPlateletApheresisExtraction + self.NrPIPlateletApheresisExtraction
        #self.StartPIFlowUnsatisfiedLowMedPatientsFromPreviousStage = self.StartPIPlateletWholeExtraction + self.NrPIPlateletWholeExtraction  
        #self.StartPIFlowUnsatisfiedHighPatientsFromPreviousStage = self.StartPIFlowUnsatisfiedLowMedPatientsFromPreviousStage + self.NrPIFlowUnsatisfiedLowMedPatientsFromPreviousStage  
        #self.StartPIFlowUnservedLowMedPatientsFromPreviousStage = self.StartPIFlowUnsatisfiedHighPatientsFromPreviousStage + self.NrPIFlowUnsatisfiedHighPatientsFromPreviousStage
        #self.StartPIFlowUnservedHighPatientsFromPreviousStage = self.StartPIFlowUnservedLowMedPatientsFromPreviousStage + self.NrPIFlowUnservedLowMedPatientsFromPreviousStage
        #self.StartPIFlowUnservedACFFromPreviousStage = self.StartPIFlowUnservedHighPatientsFromPreviousStage + self.NrPIFlowUnservedHighPatientsFromPreviousStage
        #self.StartPIFlowUnservedHospitalFromPreviousStage = self.StartPIFlowUnservedACFFromPreviousStage + self.NrPIFlowUnservedACFFromPreviousStage
        self.StartPIFlowPLTInvTransHospitalFromPreviousWholeProduction = self.StartPIPlateletWholeExtraction + self.NrPIPlateletWholeExtraction
        #self.StartPIFlowPLTInvTransACFFromPreviousStage = self.StartPIFlowPLTInvTransHospitalFromPreviousWholeProduction + self.NrPIFlowPLTInvTransHospitalFromPreviousStage
        #self.StartPIFlowApheresisAssignmentFromPreviousStage = self.StartPIFlowPLTInvTransACFFromPreviousStage + self.NrPIFlowPLTInvTransACFFromPreviousStage
        self.StartPICostToGoEVPI = self.StartPIFlowPLTInvTransHospitalFromPreviousWholeProduction + self.NrPIFlowPLTInvTransHospitalFromPreviousWholeProduction
        self.StartCutRHSVariable = self.StartPICostToGoEVPI + self.NrEstmateCostToGoEVPI

    #Compute the cost of the stage at the current iteration
    def ComputePassCost(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ComputePassCost)")

        if Constants.Debug:
            for w in self.TrialScenarioNrSet:
                print(f"self.PartialCostPerScenario[w={w}]: ", self.PartialCostPerScenario[w])
                print(f"self.StageCostPerScenarioWithCostoGo[w={w}]: ", self.StageCostPerScenarioWithCostoGo[w])
                print(f"self.SDDPOwner.CurrentSetOfTrialScenarios[w={w}].Probability: ", self.SDDPOwner.CurrentSetOfTrialScenarios[w].Probability)
        
        totalproba = sum(self.SDDPOwner.CurrentSetOfTrialScenarios[w].Probability
                            for w in self.TrialScenarioNrSet)
        
        self.PassCost = sum(self.PartialCostPerScenario[w] * self.SDDPOwner.CurrentSetOfTrialScenarios[w].Probability
                            for w in self.TrialScenarioNrSet) / totalproba

        self.PassCostWithAproxCosttoGo = sum(self.StageCostPerScenarioWithCostoGo[w]
                                             * self.SDDPOwner.CurrentSetOfTrialScenarios[w].Probability
                                             for w in self.TrialScenarioNrSet) / totalproba

    def Print_Attributes(self):
        if Constants.Debug: 
            print("\n We are in 'SDDPStage' Class -- (Print_Attributes)")
            print("\nSDDP Class Attributes:")
            for attr, value in self.__dict__.items():
                print(f"{attr}: {value}")        

    #This function modify the number of scenario in the stage
    def SetNrTrialScenario(self, nrscenario):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (SetNrTrialScenario)")
        self.NrTrialScenario = nrscenario
        self.CurrentTrialNr = 0
        self.TrialScenarioNrSet = range(nrscenario)

        #The value of the ACF Establishment and ... variables (filled after having solve the MIPs for all scenario)
        self.ACFEstablishmentValues = [[] for w in self.TrialScenarioNrSet]
        self.VehicleAssignmentValues = [[] for w in self.TrialScenarioNrSet]

        self.ApheresisAssignmentValues = [[] for w in self.TrialScenarioNrSet]
        self.TransshipmentHIValues = [[] for w in self.TrialScenarioNrSet]
        self.TransshipmentIIValues = [[] for w in self.TrialScenarioNrSet]
        self.TransshipmentHHValues = [[] for w in self.TrialScenarioNrSet]
        
        self.PatientTransferValues = [[] for w in self.TrialScenarioNrSet]
        self.UnsatisfiedPatientsValues = [[] for w in self.TrialScenarioNrSet]
        self.PlateletInventoryValues = [[] for w in self.TrialScenarioNrSet]
        self.OutdatedPlateletValues = [[] for w in self.TrialScenarioNrSet]
        self.ServedPatientValues = [[] for w in self.TrialScenarioNrSet]
        self.PatientPostponementValues = [[] for w in self.TrialScenarioNrSet]
        self.PlateletApheresisExtractionValues = [[] for w in self.TrialScenarioNrSet]
        self.PlateletWholeExtractionValues = [[] for w in self.TrialScenarioNrSet]
                
        # The cost of each scenario
        self.StageCostPerScenarioWithoutCostoGo = [-1 for w in self.TrialScenarioNrSet]
        self.StageCostPerScenarioWithCostoGo = [-1 for w in self.TrialScenarioNrSet]

        self.PartialCostPerScenario = [0 for w in self.TrialScenarioNrSet]

    #Return true if the current stage is the last
    def IsLastStage(self):
        return False
    
    #Return true if the current stage is the first
    def IsFirstStage(self):
        return self.DecisionStage == 0
    
    def IsPenultimateStage(self):
        return self.NextSDDPStage.IsLastStage()

    def IsInFutureStageForInv(self, t):
        # Checks if 't' is not among the periods considered for global MIP
        #is_external_demand_not_in_global_mip = t not in self.PeriodsInGlobalMIPInventory

        #result = not (is_external_demand_not_in_global_mip)
        result = True
        return result

    # The function "GetNumberOfPeriodWithApheresisAssignment(self)" is really important in definition the number of each variable at each stage in the model.
    # For example if you do not have variable x in the last stage, you should activate "return[]" otherwise, if you have only x_t, you have to activate "return[0]"
    # and if you have both x_t and x_(t-1) in one constraint, you have to activate "return range(self.Instance.NrTimeBucket - self.DecisionStage)"
    def GetNumberOfPeriodWithApheresisAssignment(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (GetNumberOfPeriodWithApheresisAssignment)")

        # IF in one constraint, you have for example, x_(t) and x_(t-1), then you should select: "return range(self.Instance.NrTimeBucket - self.DecisionStage)"
            # for that specific stages, HOWEVER, if you have only x_(t) or x_(t-1) you have to go with "return [0]"
        if self.IsFirstStage():
            if Constants.Debug: print("---It is the First Stage---")
            return range(1)
        if self.IsPenultimateStage():
            if Constants.Debug: print("---It is the Penaltimate Stage---") 
            #return range(self.Instance.NrTimeBucket - self.DecisionStage)       
            return [0]       
        elif not self.IsLastStage():
            if Constants.Debug: print("---It is between the First and the Pnaltymate Stage---")
            return [0]  
        else:
            if Constants.Debug: print("---It is the Last Stage---")
            return[]
        
    def GetNumberOfPeriodWithPatientTransfer(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (GetNumberOfPeriodWithPatientTransfer)")
        if self.IsFirstStage():
            return range(1, 1)
        elif not self.IsLastStage():
            return [0]
        else:
            #return [range(self.Instance.NrTimeBucket - self.DecisionStage + 1)]
            return [0]
    
    def GetNumberOfPeriodWithInventory(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (GetNumberOfPeriodWithInventory)")
        if self.IsFirstStage():
            return range(1, 1)
        elif not self.IsLastStage():
            return [0]
        else:
            #return [range(self.Instance.NrTimeBucket - self.DecisionStage + 1)]
            return [0]
    
    def ComputeVariablePeriods(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ComputeVariablePeriods)")

        self.RangePeriodApheresisAssignment = self.GetNumberOfPeriodWithApheresisAssignment()
        self.RangePeriodPatientTransfer = self.GetNumberOfPeriodWithPatientTransfer()

    def ComputeNrVariables(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ComputeNrVariables)")

        #number of variable at stage 1<t<T
        NrFixedScen = len(self.FixedScenarioSet)

        NrPeriodApheresisAssignment = len(self.RangePeriodApheresisAssignment)
        NrPeriodTransshipmentHI = len(self.RangePeriodApheresisAssignment)
        NrPeriodTransshipmentII = len(self.RangePeriodApheresisAssignment)
        NrPeriodTransshipmentHH = len(self.RangePeriodApheresisAssignment)

        NrPeriodPatientTransfer = len(self.RangePeriodPatientTransfer)
        NrPeriodUnsatisfiedPatients = len(self.RangePeriodPatientTransfer)
        NrPeriodPlateletInventory = len(self.RangePeriodPatientTransfer)
        NrPeriodOutdatedPlatelet = len(self.RangePeriodPatientTransfer)
        NrPeriodServedPatient = len(self.RangePeriodPatientTransfer)
        NrPeriodPatientPostponement = len(self.RangePeriodPatientTransfer)
        NrPeriodPlateletApheresisExtraction = len(self.RangePeriodPatientTransfer)
        NrPeriodPlateletWholeExtraction = len(self.RangePeriodPatientTransfer)

        self.NrApheresisAssignmentVariable = self.Instance.NrACFPPoints * NrFixedScen * NrPeriodApheresisAssignment
        self.NrTransshipmentHIVariable = self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrACFPPoints * (NrFixedScen * NrPeriodTransshipmentHI)
        self.NrTransshipmentIIVariable = self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints * (NrFixedScen * NrPeriodTransshipmentII)
        self.NrTransshipmentHHVariable = self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrHospitals * (NrFixedScen * NrPeriodTransshipmentHH)
        
        self.NrPatientTransferVariable =                self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * self.Instance.NrFacilities * self.Instance.NrRescueVehicles * (NrFixedScen * NrPeriodPatientTransfer)                             
        self.NrUnsatisfiedPatientsVariable =            self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * (NrFixedScen * NrPeriodUnsatisfiedPatients)                               
        self.NrPlateletInventoryVariable =              self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities * (NrFixedScen * NrPeriodPlateletInventory)                               
        self.NrOutdatedPlateletVariable =               self.Instance.NrFacilities * (NrFixedScen * NrPeriodOutdatedPlatelet)                               
        self.NrServedPatientVariable =                  self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities * (NrFixedScen * NrPeriodServedPatient)                               
        self.NrPatientPostponementVariable =            self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrFacilities * (NrFixedScen * NrPeriodPatientPostponement)                               
        self.NrPlateletApheresisExtractionVariable =    self.Instance.NRBloodGPs * self.Instance.NrFacilities * (NrFixedScen * NrPeriodPlateletApheresisExtraction)                              
        self.NrPlateletWholeExtractionVariable =        self.Instance.NRBloodGPs * self.Instance.NrHospitals * (NrFixedScen * NrPeriodPlateletWholeExtraction)                               
                               
        self.NrACFEstablishmentVariable = 0
        self.NrVehicleAssignmentVariable = 0

        self.NrEstmateCostToGoPerItemPeriod = 0

        #The variable FutureCostScenario represent an approximation of the future costs when multiple cuts are used for each scenario
        self.NrFutureCostScenario = len(self.FuturScenario)
        self.NrCostToGo = NrFixedScen * self.NrFutureCostScenario
        
        if self.IsLastStage():
            self.NrCostToGo = 0


        if self.NrPlateletInventoryVariable == 0:

            self.NRFlowUnsatisfiedLowMedPatientsFromPreviousStage = 0
            self.NRFlowUnsatisfiedHighPatientsFromPreviousStage = 0
            self.NRFlowUnservedLowMedPatientsFromPreviousStage = 0
            self.NRFlowUnservedHighPatientsFromPreviousStage = 0
            self.NRFlowUnservedACFFromPreviousStage = 0
            self.NRFlowUnservedHospitalFromPreviousStage = 0
            self.NRFlowPLTInvTransHospitalFromPreviousStage = 0
            self.NRFlowPLTInvTransACFFromPreviousStage = 0
            self.NRFlowApheresisAssignmentFromPreviousStage = 0
        else:
            self.NRFlowUnsatisfiedLowMedPatientsFromPreviousStage =  self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * NrPeriodPlateletInventory
            self.NRFlowUnsatisfiedHighPatientsFromPreviousStage =  self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * NrPeriodPlateletInventory
            self.NRFlowUnservedLowMedPatientsFromPreviousStage = self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrFacilities * NrPeriodPlateletInventory
            self.NRFlowUnservedHighPatientsFromPreviousStage = self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrHospitals * NrPeriodPlateletInventory
            self.NRFlowUnservedACFFromPreviousStage = self.Instance.NrACFPPoints * NrPeriodPlateletInventory
            self.NRFlowUnservedHospitalFromPreviousStage = self.Instance.NrHospitals * NrPeriodPlateletInventory
            self.NRFlowPLTInvTransHospitalFromPreviousStage = self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * NrPeriodPlateletInventory
            self.NRFlowPLTInvTransACFFromPreviousStage = self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrACFPPoints * NrPeriodPlateletInventory
            self.NRFlowApheresisAssignmentFromPreviousStage = self.Instance.NrACFPPoints * NrPeriodPlateletInventory

        self.NRACFEstablishmentRHS_ACFTreatCapConst = self.Instance.NrACFPPoints
        self.NRACFEstablishmentRHS_ApheresisAssignCons = self.Instance.NrACFPPoints
        self.NRVehicleAssignmentRHS_ACFRescVehCapCons = self.Instance.NrRescueVehicles * self.Instance.NrACFPPoints

        nrtimeperiodtogo = self.Instance.NrTimeBucket - (self.TimeDecisionStage)

        nrtimeperiodtogo_ApheresisAssignment = (nrtimeperiodtogo - len(self.RangePeriodApheresisAssignment))

        if Constants.SDDPUseEVPI and not self.IsLastStage():
            
            self.NrPIApheresisAssignment =  self.Instance.NrACFPPoints * (NrFixedScen * Constants.SDDPNrEVPIScenario * nrtimeperiodtogo_ApheresisAssignment)
            self.NrPITransshipmentHI =      self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrACFPPoints * (NrFixedScen * Constants.SDDPNrEVPIScenario * nrtimeperiodtogo_ApheresisAssignment)
            self.NrPITransshipmentII =      self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints * (NrFixedScen * Constants.SDDPNrEVPIScenario * nrtimeperiodtogo_ApheresisAssignment)
            self.NrPITransshipmentHH =      self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrHospitals * (NrFixedScen * Constants.SDDPNrEVPIScenario * nrtimeperiodtogo_ApheresisAssignment)

            self.NrPIPatientTransfer =              self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * self.Instance.NrFacilities * self.Instance.NrRescueVehicles * (NrFixedScen * Constants.SDDPNrEVPIScenario * nrtimeperiodtogo)
            self.NrPIUnsatisfiedPatients =          self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * (NrFixedScen * Constants.SDDPNrEVPIScenario * nrtimeperiodtogo)
            self.NrPIPlateletInventory =            self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities * (NrFixedScen * Constants.SDDPNrEVPIScenario * nrtimeperiodtogo)
            self.NrPIOutdatedPlatelet =             self.Instance.NrFacilities * (NrFixedScen * Constants.SDDPNrEVPIScenario * nrtimeperiodtogo)
            self.NrPIServedPatient =                self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities * (NrFixedScen * Constants.SDDPNrEVPIScenario * nrtimeperiodtogo)
            self.NrPIPatientPostponement =          self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrFacilities * (NrFixedScen * Constants.SDDPNrEVPIScenario * nrtimeperiodtogo)
            self.NrPIPlateletApheresisExtraction =  self.Instance.NRBloodGPs * self.Instance.NrFacilities * (NrFixedScen * Constants.SDDPNrEVPIScenario * nrtimeperiodtogo)
            self.NrPIPlateletWholeExtraction =      self.Instance.NRBloodGPs * self.Instance.NrHospitals * (NrFixedScen * Constants.SDDPNrEVPIScenario * nrtimeperiodtogo)
            
            self.NrEstmateCostToGoEVPI = NrFixedScen

            self.NRACFEstablishmentRHS_ACFTreatCapConst = self.Instance.NrACFPPoints
            self.NRACFEstablishmentRHS_ApheresisAssignCons = self.Instance.NrACFPPoints
            self.NRVehicleAssignmentRHS_ACFRescVehCapCons = self.Instance.NrRescueVehicles * self.Instance.NrACFPPoints

            # self.NRFlowUnsatisfiedLowMedPatientsFromPreviousStage =  self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * (self.Instance.NrTimeBucket - (nrtimeperiodtogo))
            # self.NRFlowUnsatisfiedHighPatientsFromPreviousStage =  self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * (self.Instance.NrTimeBucket - (nrtimeperiodtogo))
            # self.NRFlowUnservedLowMedPatientsFromPreviousStage = self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrFacilities * (self.Instance.NrTimeBucket - (nrtimeperiodtogo))
            # self.NRFlowUnservedHighPatientsFromPreviousStage = self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrHospitals * (self.Instance.NrTimeBucket - (nrtimeperiodtogo))
            # self.NRFlowUnservedACFFromPreviousStage = self.Instance.NrACFPPoints * (self.Instance.NrTimeBucket - (nrtimeperiodtogo))
            # self.NRFlowUnservedHospitalFromPreviousStage = self.Instance.NrHospitals * (self.Instance.NrTimeBucket - (nrtimeperiodtogo))
            self.NrPIFlowPLTInvTransHospitalFromPreviousWholeProduction = self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * (self.Instance.NrTimeBucket - (nrtimeperiodtogo))
            # self.NRFlowPLTInvTransACFFromPreviousStage = self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrACFPPoints * (self.Instance.NrTimeBucket - (nrtimeperiodtogo))
            # self.NRFlowApheresisAssignmentFromPreviousStage = self.Instance.NrACFPPoints * (self.Instance.NrTimeBucket - (nrtimeperiodtogo))
        
        # number of variable at stage 1
        if self.IsFirstStage():
            self.NrACFEstablishmentVariable = self.Instance.NrACFPPoints
            self.NrVehicleAssignmentVariable = self.Instance.NrRescueVehicles * self.Instance.NrACFPPoints

            self.NRACFEstablishmentRHS_ACFTreatCapConst = 0
            self.NRACFEstablishmentRHS_ApheresisAssignCons = 0
            self.NRVehicleAssignmentRHS_ACFRescVehCapCons = 0
        
        if Constants.Debug:
            print("NrACFEstablishmentVariable: ", self.NrACFEstablishmentVariable)
            print("NrVehicleAssignmentVariable: ", self.NrVehicleAssignmentVariable)

            print("NrApheresisAssignmentVariable: ", self.NrApheresisAssignmentVariable)
            print("NrTransshipmentHIVariable: ", self.NrTransshipmentHIVariable)
            print("NrTransshipmentIIVariable: ", self.NrTransshipmentIIVariable)
            print("NrTransshipmentHHVariable: ", self.NrTransshipmentHHVariable)

            print("NrPatientTransferVariable: ", self.NrPatientTransferVariable)
            print("NrUnsatisfiedPatientsVariable: ", self.NrUnsatisfiedPatientsVariable)
            print("NrPlateletInventoryVariable: ", self.NrPlateletInventoryVariable)
            print("NrOutdatedPlateletVariable: ", self.NrOutdatedPlateletVariable)
            print("NrServedPatientVariable: ", self.NrServedPatientVariable)
            print("NrPatientPostponementVariable: ", self.NrPatientPostponementVariable)
            print("NrPlateletApheresisExtractionVariable: ", self.NrPlateletApheresisExtractionVariable)
            print("NrPlateletWholeExtractionVariable: ", self.NrPlateletWholeExtractionVariable)
            print("-----")

    def ComputeVariablePeriodsInLargeMIP(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ComputeVariablePeriodsInLargeMIP)")

        self.PeriodsInGlobalMIPApheresisAssignment = [t + self.TimeDecisionStage for t in self.RangePeriodApheresisAssignment]
        self.PeriodsInGlobalMIPTransshipmentHI = [t + self.TimeDecisionStage for t in self.RangePeriodApheresisAssignment]
        self.PeriodsInGlobalMIPTransshipmentII = [t + self.TimeDecisionStage for t in self.RangePeriodApheresisAssignment]
        self.PeriodsInGlobalMIPTransshipmentHH = [t + self.TimeDecisionStage for t in self.RangePeriodApheresisAssignment]

        self.PeriodsInGlobalMIPPatientTransfer = [t + self.TimeDecisionStage - 1  for t in self.RangePeriodPatientTransfer]
        self.PeriodsInGlobalMIPUnsatisfiedPatients = [t + self.TimeDecisionStage - 1  for t in self.RangePeriodPatientTransfer]
        self.PeriodsInGlobalMIPPlateletInventory = [t + self.TimeDecisionStage - 1  for t in self.RangePeriodPatientTransfer]
        self.PeriodsInGlobalMIPOutdatedPlatelet = [t + self.TimeDecisionStage - 1  for t in self.RangePeriodPatientTransfer]
        self.PeriodsInGlobalMIPServedPatient = [t + self.TimeDecisionStage - 1  for t in self.RangePeriodPatientTransfer]
        self.PeriodsInGlobalMIPPatientPostponement = [t + self.TimeDecisionStage - 1  for t in self.RangePeriodPatientTransfer]
        self.PeriodsInGlobalMIPPlateletApheresisExtraction = [t + self.TimeDecisionStage - 1  for t in self.RangePeriodPatientTransfer]
        self.PeriodsInGlobalMIPPlateletWholeExtraction = [t + self.TimeDecisionStage - 1  for t in self.RangePeriodPatientTransfer]
        #Create the MIP

    def GetTimeIndexForPatientTransfer(self, time):

        result = time - self.TimeObservationStage
        
        return result
    
    def GetTimeIndexForInv(self, d, time):

        result = time - self.TimeObservationStage
        
        return result
    
    # Return the time period associated with Apheresis Assignment Variable decided at the current stage
    def GetTimePeriodAssociatedToApheresisAssignmentVariable(self, t):

        result = self.TimeDecisionStage + t
        
        return result
    
    def GetTimePeriodAssociatedToPatientTransferVariable(self, t):
        
        result = self.TimeObservationStage + t

        return result

    def GetTimePeriodRangeForInventoryVariable(self, d):
            
        result = [self.TimeObservationStage + t  for t in self.RangePeriodShortage]

        return result
    
    def GetTimePeriodRangeForPatientTransferVariable(self):
            
        result = [self.TimeObservationStage + t  for t in self.RangePeriodPatientTransfer]

        return result
        
    def GetRHSFlow_Demand(self, j, c, l, t, scenario, forwardpass):

        righthandside = 0

        if forwardpass:
                righthandside = righthandside + self.SDDPOwner.CurrentSetOfTrialScenarios[scenario].Demands[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][j][c][l]
        else:
            righthandside = righthandside + self.SDDPOwner.SetOfSAAScenarioDemand[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][scenario][j][c][l]

        return righthandside
    
    def GetRHSFlow_HospitalCap(self, h, t, scenario, forwardpass):

        righthandside = 0

        # Demand at period t for item i
        if forwardpass:
                righthandside = righthandside + self.SDDPOwner.CurrentSetOfTrialScenarios[scenario].HospitalCaps[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][h]
        else:
            righthandside = righthandside + self.SDDPOwner.SetOfSAAScenarioHospitalCapacity[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][scenario][h]

        return -1.0 * righthandside
    
    def GetRHSFlow_ApheresisDonor(self, c, u, t, scenario, forwardpass):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (GetRHSFlow_ApheresisDonor)")
        
        righthandside = 0

        # Demand at period t for item i
        if forwardpass:
                righthandside = righthandside + self.SDDPOwner.CurrentSetOfTrialScenarios[scenario].ApheresisDonors[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][c][u]
        else:
            righthandside = righthandside + self.SDDPOwner.SetOfSAAScenarioApheresisDonor[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][scenario][c][u]

        return -1.0 * self.Instance.Platelet_Units_Apheresis * righthandside
    
    def GetRHSFlow_WholeDonor(self, c, h, t, scenario, forwardpass):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (GetRHSFlow_WholeDonor)")
        
        righthandside = 0

        # Demand at period t for item i
        if forwardpass:
                righthandside = righthandside + self.SDDPOwner.CurrentSetOfTrialScenarios[scenario].WholeDonors[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][c][h]
        else:
            righthandside = righthandside + self.SDDPOwner.SetOfSAAScenarioWholeDonor[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][scenario][c][h]

        return -1.0 * righthandside
        
    def GetIndexACFEstablishmentRHS_ACFTreatCapConst(self, i):

        return self.StartACFEstablishmentRHS_ACFTreatCapConst + i
    
    def GetIndexACFEstablishmentRHS_ApheresisAssignCon(self, i):

        return self.StartACFEstablishmentRHS_ApheresisAssignCons + i
        
    def GetIndexVehicleAssignmentRHS_ACFRescVehCapCons(self, m, i):

        return self.StartVehicleAssignmentRHS_ACFRescVehCapCons \
            + m * self.Instance.NrACFPPoints \
            + i
                
    def GetIndexFixedTransRHS(self, s, d):
        return self.StartFixedTransRHS + s * self.Instance.NrDemandLocations + d
               
    def GetIndexACFEstablishmentVariable(self, i):
        if self.IsFirstStage():
            return self.StartACFEstablishment + i
        else:
            raise ValueError('ACFEstablishment variables are only defined at stage 0')
    
    def GetIndexVehicleAssignmentVariable(self, m, i):
        if self.IsFirstStage():
            return self.StartVehicleAssignment \
                    + m * self.Instance.NrACFPPoints \
                    + i
        else:
            raise ValueError('VehicleAssignment variables are only defined at stage 0')

    # return the index of the cost to go variable for scenario w
    def GetIndexCostToGo(self, w, futurcostscenario):
            return self.StartCostToGo + w * self.NrFutureCostScenario + futurcostscenario
    
    def GetIndexEVPICostToGo(self, w):
        return self.StartPICostToGoEVPI + w
                
    def GetIndexApheresisAssignmentVariable(self, i, t, w):

        return self.StartApheresisAssignment \
            + t * len(self.FixedScenarioSet) * self.Instance.NrACFPPoints \
            + w * self.Instance.NrACFPPoints \
            + i
      
    def GetIndexTransshipmentHIVariable(self, c, r, h, i, t, w):

        return self.StartTransshipmentHI \
            + t * len(self.FixedScenarioSet) * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrACFPPoints \
            + w * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrACFPPoints \
            + c * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrACFPPoints \
            + r * self.Instance.NrHospitals * self.Instance.NrACFPPoints \
            + h * self.Instance.NrACFPPoints \
            + i
    
    def GetIndexTransshipmentIIVariable(self, c, r, i, iprime, t, w):

        return self.StartTransshipmentII \
            + t * len(self.FixedScenarioSet) * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints \
            + w * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints \
            + c * self.Instance.NRPlateletAges * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints \
            + r * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints \
            + i * self.Instance.NrACFPPoints \
            + iprime
    
    def GetIndexTransshipmentHHVariable(self, c, r, h, hprime, t, w):

        return self.StartTransshipmentHH \
            + t * len(self.FixedScenarioSet) * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrHospitals \
            + w * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrHospitals \
            + c * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrHospitals \
            + r * self.Instance.NrHospitals * self.Instance.NrHospitals \
            + h * self.Instance.NrHospitals \
            + hprime

    def GetIndexPIApheresisAssignmentVariable(self, i, t, wevpi, w):

        if t in self.PeriodsInGlobalMIPApheresisAssignment:
            time = self.GetTimeIndexForApheresisAssignment(t)
            return self.GetIndexApheresisAssignmentVariable(i, time, w)
        else:
            timeperiodwithApheresisAssignment = self.NrTimePeriodToGo - len(self.RangePeriodApheresisAssignment)
            # Adjust 't' to make sure it starts from 0 for the first time period of interest
            adjusted_t = t - (self.TimeDecisionStage + len(self.RangePeriodApheresisAssignment))
            # Calculate the index
            index = self.StartPIApheresisAssignment \
                    + w * self.Instance.NrACFPPoints * timeperiodwithApheresisAssignment * Constants.SDDPNrEVPIScenario \
                    + wevpi * self.Instance.NrACFPPoints * timeperiodwithApheresisAssignment \
                    + adjusted_t * self.Instance.NrACFPPoints \
                    + i
            return index
    
    def GetIndexPITransshipmentHIVariable(self, c, r, h, i, t, wevpi, w):

        if t in self.PeriodsInGlobalMIPTransshipmentHI:
            time = self.GetTimeIndexForTransshipmentHI(t)
            return self.GetIndexTransshipmentHIVariable(c, r, h, i, time, w)
        else:
            timeperiodwithTransshipmentHI = self.NrTimePeriodToGo - len(self.RangePeriodApheresisAssignment)
            # Adjust 't' to make sure it starts from 0 for the first time period of interest
            adjusted_t = t - (self.TimeDecisionStage + len(self.RangePeriodApheresisAssignment))
            # Calculate the index
            index = self.StartPITransshipmentHI \
                    + w * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrACFPPoints * timeperiodwithTransshipmentHI * Constants.SDDPNrEVPIScenario \
                    + wevpi * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrACFPPoints * timeperiodwithTransshipmentHI \
                    + adjusted_t * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrACFPPoints \
                    + c * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrACFPPoints \
                    + r * self.Instance.NrHospitals * self.Instance.NrACFPPoints \
                    + h * self.Instance.NrACFPPoints \
                    + i
            return index
    
    def GetIndexPITransshipmentHHVariable(self, c, r, h, hprime, t, wevpi, w):

        if t in self.PeriodsInGlobalMIPTransshipmentHH:
            time = self.GetTimeIndexForTransshipmentHH(t)
            return self.GetIndexTransshipmentHHVariable(c, r, h, hprime, time, w)
        else:
            timeperiodwithTransshipmentHH = self.NrTimePeriodToGo - len(self.RangePeriodApheresisAssignment)
            # Adjust 't' to make sure it starts from 0 for the first time period of interest
            adjusted_t = t - (self.TimeDecisionStage + len(self.RangePeriodApheresisAssignment))
            # Calculate the index
            index = self.StartPITransshipmentHH \
                    + w * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrHospitals * timeperiodwithTransshipmentHH * Constants.SDDPNrEVPIScenario \
                    + wevpi * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrHospitals * timeperiodwithTransshipmentHH \
                    + adjusted_t * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrHospitals \
                    + c * self.Instance.NRPlateletAges * self.Instance.NrHospitals * self.Instance.NrHospitals \
                    + r * self.Instance.NrHospitals * self.Instance.NrHospitals \
                    + h * self.Instance.NrHospitals \
                    + hprime
            return index
    
    def GetIndexPITransshipmentIIVariable(self, c, r, i, iprime, t, wevpi, w):

        if t in self.PeriodsInGlobalMIPTransshipmentII:
            time = self.GetTimeIndexForTransshipmentII(t)
            return self.GetIndexTransshipmentIIVariable(c, r, i, iprime, time, w)
        else:
            timeperiodwithTransshipmentII = self.NrTimePeriodToGo - len(self.RangePeriodApheresisAssignment)
            # Adjust 't' to make sure it starts from 0 for the first time period of interest
            adjusted_t = t - (self.TimeDecisionStage + len(self.RangePeriodApheresisAssignment))
            # Calculate the index
            index = self.StartPITransshipmentII \
                    + w * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints * timeperiodwithTransshipmentII * Constants.SDDPNrEVPIScenario \
                    + wevpi * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints * timeperiodwithTransshipmentII \
                    + adjusted_t * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints \
                    + c * self.Instance.NRPlateletAges * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints \
                    + r * self.Instance.NrACFPPoints * self.Instance.NrACFPPoints \
                    + i * self.Instance.NrACFPPoints \
                    + iprime
            return index
    
    def GetIndexPIVariableTransVariable(self, s, d, t, wevpi, w):

        if t in self.PeriodsInGlobalMIPVarTrans:
            time = self.GetTimeIndexForVarTrans(d, t)
            return self.GetIndexVariableTransVariable(s, d, time, w)
        else:
            timeperiodwithvartrans = self.NrTimePeriodToGo - len(self.RangePeriodVarTrans)
            # Adjust 't' to make sure it starts from 0 for the first time period of interest
            adjusted_t = t - (self.TimeDecisionStage + len(self.RangePeriodVarTrans))
            # Calculate the index
            index = self.StartPIVariableTrans \
                    + w * self.Instance.NrSuppliers * self.Instance.NrDemandLocations * timeperiodwithvartrans * Constants.SDDPNrEVPIScenario \
                    + wevpi * self.Instance.NrSuppliers * self.Instance.NrDemandLocations * timeperiodwithvartrans \
                    + adjusted_t * self.Instance.NrSuppliers * self.Instance.NrDemandLocations \
                    + s * self.Instance.NrDemandLocations \
                    + d
            return index
        
    def GetIndexCutRHSFromPreviousSatge(self, cut):
        return self.StartCutRHSVariable + cut.Id
            
    def GetIndexPatientTransferVariable(self, j, c, l, u, m, t, w):

        return self.StartPatientTransfer \
            + t * len(self.FixedScenarioSet) * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * self.Instance.NrFacilities * self.Instance.NrRescueVehicles \
            + w * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * self.Instance.NrFacilities * self.Instance.NrRescueVehicles \
            + j * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * self.Instance.NrFacilities * self.Instance.NrRescueVehicles \
            + c * self.Instance.NrDemandLocations * self.Instance.NrFacilities * self.Instance.NrRescueVehicles \
            + l * self.Instance.NrFacilities * self.Instance.NrRescueVehicles \
            + u * self.Instance.NrRescueVehicles \
            + m
    
    def GetIndexUnsatisfiedPatientsVariable(self, j, c, l, t, w):

        return self.StartUnsatisfiedPatients \
            + t * len(self.FixedScenarioSet) * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations \
            + w * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations \
            + j * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations \
            + c * self.Instance.NrDemandLocations \
            + l \
    
    def GetIndexPlateletInventoryVariable(self, c, r, u, t, w):

        return self.StartPlateletInventory \
            + t * len(self.FixedScenarioSet) * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities \
            + w * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities \
            + c * self.Instance.NRPlateletAges * self.Instance.NrFacilities \
            + r * self.Instance.NrFacilities \
            + u \
    
    def GetIndexOutdatedPlateletVariable(self, u, t, w):

        return self.StartOutdatedPlatelet \
            + t * len(self.FixedScenarioSet) * self.Instance.NrFacilities \
            + w * self.Instance.NrFacilities \
            + u
    
    def GetIndexServedPatientVariable(self, j, cprime, c, r, u, t, w):

        return self.StartServedPatient \
                + t * len(self.FixedScenarioSet) * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities \
                + w * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities \
                + j * self.Instance.NRBloodGPs * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities \
                + cprime * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities \
                + c * self.Instance.NRPlateletAges * self.Instance.NrFacilities \
                + r * self.Instance.NrFacilities \
                + u
    
    def GetIndexPatientPostponementVariable(self, j, c, u, t, w):

        return self.StartPatientPostponement \
            + t * len(self.FixedScenarioSet) * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrFacilities \
            + w * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrFacilities \
            + j * self.Instance.NRBloodGPs * self.Instance.NrFacilities \
            + c * self.Instance.NrFacilities \
            + u \
    
    def GetIndexPlateletApheresisExtractionVariable(self, c, u, t, w):

        return self.StartPlateletApheresisExtraction \
                + t * len(self.FixedScenarioSet) * self.Instance.NRBloodGPs * self.Instance.NrFacilities \
                + w * self.Instance.NRBloodGPs * self.Instance.NrFacilities \
                + c * self.Instance.NrFacilities \
                + u
    
    def GetIndexPlateletWholeExtractionVariable(self, c, h, t, w):

        return self.StartPlateletWholeExtraction \
                + t * len(self.FixedScenarioSet) * self.Instance.NRBloodGPs * self.Instance.NrHospitals \
                + w * self.Instance.NRBloodGPs * self.Instance.NrHospitals \
                + c * self.Instance.NrHospitals \
                + h
    
    def GetIndexPIShortageVariable(self, d, t, wevpi, w):
        # Check if the period t is within the predefined shortage periods
        if t in self.PeriodsInGlobalMIPShortage:
            time = self.GetTimeIndexForShortage(d, t)
            index = self.GetIndexShortageVariable(d, time, w)
            return index
        else:
            calculated_index = self.StartPIShortage \
                + w * self.Instance.NrDemandLocations * len(self.TimePeriodToGoShortage) * Constants.SDDPNrEVPIScenario \
                + wevpi * self.Instance.NrDemandLocations * len(self.TimePeriodToGoShortage) \
                + d * len(self.TimePeriodToGoShortage) \
                + (t - self.TimePeriodToGoShortage[0])            
            return calculated_index
    
    def GetIndexPIPatientTransferVariable(self, j, c, l, u, m, t, wevpi, w):
        if t in self.PeriodsInGlobalMIPPatientTransfer:
            time = self.GetTimeIndexForPatientTransfer(t)
            index = self.GetIndexPatientTransferVariable(j, c, l, u, m, time, w)
            return index
        else:            
            calculated_index = self.StartPIPatientTransfer \
                + w * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * self.Instance.NrFacilities * self.Instance.NrRescueVehicles * len(self.TimePeriodToGoPatientTransfer) * Constants.SDDPNrEVPIScenario \
                + wevpi * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * self.Instance.NrFacilities * self.Instance.NrRescueVehicles * len(self.TimePeriodToGoPatientTransfer) \
                + j * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * self.Instance.NrFacilities * self.Instance.NrRescueVehicles * len(self.TimePeriodToGoPatientTransfer) \
                + c * self.Instance.NrDemandLocations * self.Instance.NrFacilities * self.Instance.NrRescueVehicles * len(self.TimePeriodToGoPatientTransfer) \
                + l * self.Instance.NrFacilities * self.Instance.NrRescueVehicles * len(self.TimePeriodToGoPatientTransfer) \
                + u * self.Instance.NrRescueVehicles * len(self.TimePeriodToGoPatientTransfer) \
                + m * len(self.TimePeriodToGoPatientTransfer) \
                + (t - self.TimePeriodToGoPatientTransfer[0])            
            return calculated_index
    
    def GetIndexPIServedPatientVariable(self, j, cprime, c, r, u, t, wevpi, w):
        if t in self.PeriodsInGlobalMIPServedPatient:
            time = self.GetTimeIndexForServedPatient(t)
            index = self.GetIndexServedPatientVariable(j, cprime, c, r, u, time, w)
            return index
        else:            
            calculated_index = self.StartPIServedPatient \
                + w * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities * len(self.TimePeriodToGoServedPatient) * Constants.SDDPNrEVPIScenario \
                + wevpi * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities * len(self.TimePeriodToGoServedPatient) \
                + j * self.Instance.NRBloodGPs * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities * len(self.TimePeriodToGoServedPatient) \
                + cprime * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities * len(self.TimePeriodToGoServedPatient) \
                + c * self.Instance.NRPlateletAges * self.Instance.NrFacilities * len(self.TimePeriodToGoServedPatient) \
                + r * self.Instance.NrFacilities * len(self.TimePeriodToGoServedPatient) \
                + u * len(self.TimePeriodToGoServedPatient) \
                + (t - self.TimePeriodToGoServedPatient[0])            
            return calculated_index
    
    def GetIndexPIPatientPostponementVariable(self, j, c, u, t, wevpi, w):
        if t in self.PeriodsInGlobalMIPPatientPostponement:
            time = self.GetTimeIndexForPatientPostponement(t)
            index = self.GetIndexPatientPostponementVariable(j, c, u, time, w)
            return index
        else:            
            calculated_index = self.StartPIPatientPostponement \
                + w * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrFacilities * len(self.TimePeriodToGoPatientPostponement) * Constants.SDDPNrEVPIScenario \
                + wevpi * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrFacilities * len(self.TimePeriodToGoPatientPostponement) \
                + j * self.Instance.NRBloodGPs * self.Instance.NrFacilities * len(self.TimePeriodToGoPatientPostponement) \
                + c * self.Instance.NrFacilities * len(self.TimePeriodToGoPatientPostponement) \
                + u * len(self.TimePeriodToGoPatientPostponement) \
                + (t - self.TimePeriodToGoPatientPostponement[0])            
            return calculated_index
    
    def GetIndexPIPlateletApheresisExtractionVariable(self, c, u, t, wevpi, w):
        if t in self.PeriodsInGlobalMIPPlateletApheresisExtraction:
            time = self.GetTimeIndexForPlateletApheresisExtraction(t)
            index = self.GetIndexPlateletApheresisExtractionVariable(c, u, time, w)
            return index
        else:            
            calculated_index = self.StartPIPlateletApheresisExtraction \
                + w * self.Instance.NRBloodGPs * self.Instance.NrFacilities * len(self.TimePeriodToGoPlateletApheresisExtraction) * Constants.SDDPNrEVPIScenario \
                + wevpi * self.Instance.NRBloodGPs * self.Instance.NrFacilities * len(self.TimePeriodToGoPlateletApheresisExtraction) \
                + c * self.Instance.NrFacilities * len(self.TimePeriodToGoPlateletApheresisExtraction) \
                + u * len(self.TimePeriodToGoPlateletApheresisExtraction) \
                + (t - self.TimePeriodToGoPlateletApheresisExtraction[0])            
            return calculated_index
    
    def GetIndexPIPlateletWholeExtractionVariable(self, c, h, t, wevpi, w):
        if t in self.PeriodsInGlobalMIPPlateletWholeExtraction:
            time = self.GetTimeIndexForPlateletWholeExtraction(t)
            index = self.GetIndexPlateletWholeExtractionVariable(c, h, time, w)
            return index
        else:            
            calculated_index = self.StartPIPlateletWholeExtraction \
                + w * self.Instance.NRBloodGPs * self.Instance.NrHospitals * len(self.TimePeriodToGoPlateletWholeExtraction) * Constants.SDDPNrEVPIScenario \
                + wevpi * self.Instance.NRBloodGPs * self.Instance.NrHospitals * len(self.TimePeriodToGoPlateletWholeExtraction) \
                + c * self.Instance.NrHospitals * len(self.TimePeriodToGoPlateletWholeExtraction) \
                + h * len(self.TimePeriodToGoPlateletWholeExtraction) \
                + (t - self.TimePeriodToGoPlateletWholeExtraction[0])            
            return calculated_index
    
    def GetIndexPIUnsatisfiedPatientsVariable(self, j, c, l, t, wevpi, w):
        if t in self.PeriodsInGlobalMIPUnsatisfiedPatients:
            time = self.GetTimeIndexForUnsatisfiedPatients(t)
            index = self.GetIndexUnsatisfiedPatientsVariable(j, c, l, time, w)
            return index
        else:                       
            calculated_index = self.StartPIUnsatisfiedPatients \
                + w * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * len(self.TimePeriodToGoUnsatisfiedPatients) * Constants.SDDPNrEVPIScenario \
                + wevpi * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * len(self.TimePeriodToGoUnsatisfiedPatients) \
                + j * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations * len(self.TimePeriodToGoUnsatisfiedPatients) \
                + c * self.Instance.NrDemandLocations * len(self.TimePeriodToGoUnsatisfiedPatients) \
                + l * len(self.TimePeriodToGoUnsatisfiedPatients) \
                + (t - self.TimePeriodToGoUnsatisfiedPatients[0])            
            return calculated_index
    
    def GetIndexPIPlateletInventoryVariable(self, c, r, u, t, wevpi, w):
        if t in self.PeriodsInGlobalMIPPlateletInventory:
            time = self.GetTimeIndexForPlateletInventory(t)
            index = self.GetIndexPlateletInventoryVariable(c, r, u, time, w)
            return index
        else:            
            calculated_index = self.StartPIPlateletInventory \
                + w * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities * len(self.TimePeriodToGoPlateletInventory) * Constants.SDDPNrEVPIScenario \
                + wevpi * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrFacilities * len(self.TimePeriodToGoPlateletInventory) \
                + c * self.Instance.NRPlateletAges * self.Instance.NrFacilities * len(self.TimePeriodToGoPlateletInventory) \
                + r * self.Instance.NrFacilities * len(self.TimePeriodToGoPlateletInventory) \
                + u * len(self.TimePeriodToGoPlateletInventory) \
                + (t - self.TimePeriodToGoPlateletInventory[0])            
            return calculated_index
    
    def GetIndexPIOutdatedPlateletVariable(self, u, t, wevpi, w):
        if t in self.PeriodsInGlobalMIPOutdatedPlatelet:
            time = self.GetTimeIndexForOutdatedPlatelet(t)
            index = self.GetIndexOutdatedPlateletVariable(u, time, w)
            return index
        else:            
            calculated_index = self.StartPIOutdatedPlatelet \
                + w * self.Instance.NrFacilities * len(self.TimePeriodToGoOutdatedPlatelet) * Constants.SDDPNrEVPIScenario \
                + wevpi * self.Instance.NrFacilities * len(self.TimePeriodToGoOutdatedPlatelet) \
                + u * len(self.TimePeriodToGoOutdatedPlatelet) \
                + (t - self.TimePeriodToGoOutdatedPlatelet[0])            
            return calculated_index
            
    def GetIndexPIInventoryVariable(self, d, t,  wevpi, w):
        if t in self.PeriodsInGlobalMIPInventory:
            time = self.GetTimeIndexForInv(d, t)
            return self.GetIndexInventoryVariable(d, time, w)
        else:
            return self.StartPIInventory \
                   + w * self.Instance.NrDemandLocations * len(self.TimePeriodToGoInventory) * Constants.SDDPNrEVPIScenario \
                   + wevpi * self.Instance.NrDemandLocations * len(self.TimePeriodToGoInventory) \
                    + d * len(self.TimePeriodToGoShortage) \
                    + (t - self.TimePeriodToGoShortage[0])
        
    def GetIndexFlowPLTInvTransHospitalFromPreviousStage(self, cprime, r, h, t):

        return self.FlowPLTInvTransHospitalArray[t][cprime][r][h]
    
    def GetIndexFlowPLTInvTransACFFromPreviousStage(self, cprime, r, i, t):

        return self.FlowPLTInvTransACFArray[t][cprime][r][i]
    
    def GetIndexFlowApheresisAssignmentFromPreviousStage(self, i, t):

        return self.FlowApheresisAssignmentArray[t][i]
    
    def GetIndexFlowUnsatisfiedLowMedPatientsFromPreviousStage(self, j, c, l, t):

        return self.FlowUnsatisfiedLowMedPatientsArray[t][j][c][l]
    
    def GetIndexFlowUnsatisfiedHighPatientsFromPreviousStage(self, j, c, l, t):

        return self.FlowUnsatisfiedHighPatientsArray[t][j][c][l]
    
    def GetIndexFlowUnservedLowMedPatientsFromPreviousStage(self, j, c, u, t):

        return self.FlowUnservedLowMedPatientsArray[t][j][c][u]
            
    def GetIndexFlowUnservedHighPatientsFromPreviousStage(self, j, c, h, t):

        return self.FlowUnservedHighPatientsArray[t][j][c][h]
    
    def GetIndexFlowUnservedACFFromPreviousStage(self, i, t):

        return self.FlowUnservedACFArray[t][i]
    
    def GetIndexFlowUnservedHospitalFromPreviousStage(self, h, t):

        return self.FlowUnservedHospitalArray[t][h]
    
    def GetIndexFlowFromPreviousStage(self, d, t):

        return self.FlowIndexArray[t][d]

    def GetIndexPIFlowPrevVarTrans(self, d, t):

        return self.StartPIFlowFromPreviouVarTrans \
                + t * self.Instance.NrDemandLocations \
                + d
    
    def GetIndexPIFlowPLTInvTransHospitalFromPreviousWholeProduction(self, cprime, r, h, t):

        return self.StartPIFlowPLTInvTransHospitalFromPreviousWholeProduction \
                + t * self.Instance.NRBloodGPs * self.Instance.NRPlateletAges * self.Instance.NrHospitals \
                + cprime * self.Instance.NRPlateletAges * self.Instance.NrHospitals \
                + r * self.Instance.NrHospitals \
                + h
    
    def GetIndexPIFlowUnsatisfiedLowMedPatientsFromPreviousStage(self, j, c, l, t):

        return self.StartPIFlowUnsatisfiedLowMedPatientsFromPreviousStage \
                + t * self.Instance.NRInjuryLevels * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations \
                + j * self.Instance.NRBloodGPs * self.Instance.NrDemandLocations \
                + c * self.Instance.NrDemandLocations \
                + l

    def GetIndexFixedTransVariableRHS(self, s, d):
        return self.StartFixedTransRHS + s * self.Instance.NrDemandLocations + d
        
    def ComputeFlowPLTInvTransHospitalArray(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ComputeFlowPLTInvTransHospitalArray)")

        iii = self.StartFlowPLTInvTransHospitalFromPreviousStage

        self.FlowPLTInvTransHospitalArray = [[[[-1 for h in self.Instance.HospitalSet]
                                                    for r in self.Instance.PlateletAgeSet]    
                                                    for cprime in self.Instance.BloodGPSet]    
                                                    for t in self.RangePeriodPatientTransfer]    
        
        for t in self.RangePeriodPatientTransfer:
            for cprime in self.Instance.BloodGPSet:
                for r in self.Instance.PlateletAgeSet:
                    for h in self.Instance.HospitalSet:
                        self.FlowPLTInvTransHospitalArray[t][cprime][r][h] = iii
                        iii = iii + 1
    
    def ComputeFlowPLTInvTransACFArray(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ComputeFlowPLTInvTransACFArray)")

        iii = self.StartFlowPLTInvTransACFFromPreviousStage

        self.FlowPLTInvTransACFArray = [[[[-1 for i in self.Instance.ACFPPointSet]
                                            for r in self.Instance.PlateletAgeSet]    
                                            for cprime in self.Instance.BloodGPSet]    
                                            for t in self.RangePeriodPatientTransfer]    

        for t in self.RangePeriodPatientTransfer:
            for cprime in self.Instance.BloodGPSet:
                for r in self.Instance.PlateletAgeSet:
                    for i in self.Instance.ACFPPointSet:
                        self.FlowPLTInvTransACFArray[t][cprime][r][i] = iii
                        iii = iii + 1
    
    def ComputeFlowApheresisAssignmentArray(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ComputeFlowApheresisAssignmentArray)")

        iii = self.StartFlowApheresisAssignmentFromPreviousStage

        self.FlowApheresisAssignmentArray = [[-1 for i in self.Instance.ACFPPointSet]   
                                            for t in self.RangePeriodPatientTransfer]    

        for t in self.RangePeriodPatientTransfer:
            for i in self.Instance.ACFPPointSet:
                self.FlowApheresisAssignmentArray[t][i] = iii
                iii = iii + 1
        
    def ComputeFlowUnsatisfiedLowMedPatientsArray(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ComputeFlowUnsatisfiedLowMedPatientsArray)")

        iii = self.StartFlowUnsatisfiedLowMedPatientsFromPreviousStage

        self.FlowUnsatisfiedLowMedPatientsArray = [[[[-1 
                                                        for l in self.Instance.DemandSet]   
                                                        for c in self.Instance.BloodGPSet]   
                                                        for j in self.Instance.InjuryLevelSet]   
                                                        for t in self.RangePeriodPatientTransfer]     
        
        for t in self.RangePeriodPatientTransfer:
            for j in self.Instance.InjuryLevelSet:
                for c in self.Instance.BloodGPSet:
                    for l in self.Instance.DemandSet:
                        self.FlowUnsatisfiedLowMedPatientsArray[t][j][c][l] = iii
                        iii = iii + 1
    
    def ComputeFlowUnsatisfiedHighPatientsArray(self):

        iii = self.StartFlowUnsatisfiedHighPatientsFromPreviousStage

        self.FlowUnsatisfiedHighPatientsArray = [[[[-1 
                                                    for l in self.Instance.DemandSet]   
                                                    for c in self.Instance.BloodGPSet]   
                                                    for j in self.Instance.InjuryLevelSet]   
                                                    for t in self.RangePeriodPatientTransfer]     
        
        for t in self.RangePeriodPatientTransfer:
            for j in self.Instance.InjuryLevelSet:
                for c in self.Instance.BloodGPSet:
                    for l in self.Instance.DemandSet:
                        self.FlowUnsatisfiedHighPatientsArray[t][j][c][l] = iii
                        iii = iii + 1
    
    def ComputeFlowUnservedLowMedPatientsArray(self):

        iii = self.StartFlowUnservedLowMedPatientsFromPreviousStage

        self.FlowUnservedLowMedPatientsArray = [[[[-1 
                                                    for u in self.Instance.FacilitySet]   
                                                    for c in self.Instance.BloodGPSet]   
                                                    for j in self.Instance.InjuryLevelSet]   
                                                    for t in self.RangePeriodPatientTransfer]     
        
        for t in self.RangePeriodPatientTransfer:
            for j in self.Instance.InjuryLevelSet:
                for c in self.Instance.BloodGPSet:
                    for u in self.Instance.FacilitySet:
                        self.FlowUnservedLowMedPatientsArray[t][j][c][u] = iii
                        iii = iii + 1
            
    def ComputeFlowUnservedHighPatientsArray(self):

        iii = self.StartFlowUnservedHighPatientsFromPreviousStage

        self.FlowUnservedHighPatientsArray = [[[[-1 
                                                    for h in self.Instance.HospitalSet]   
                                                    for c in self.Instance.BloodGPSet]   
                                                    for j in self.Instance.InjuryLevelSet]   
                                                    for t in self.RangePeriodPatientTransfer]     
        
        for t in self.RangePeriodPatientTransfer:
            for j in self.Instance.InjuryLevelSet:
                for c in self.Instance.BloodGPSet:
                    for h in self.Instance.HospitalSet:
                        self.FlowUnservedHighPatientsArray[t][j][c][h] = iii
                        iii = iii + 1
    
    def ComputeFlowUnservedACFArray(self):

        iii = self.StartFlowUnservedACFFromPreviousStage

        self.FlowUnservedACFArray = [[-1 
                                        for i in self.Instance.ACFPPointSet]   
                                        for t in self.RangePeriodPatientTransfer]     
        
        for t in self.RangePeriodPatientTransfer:
            for i in self.Instance.ACFPPointSet:
                self.FlowUnservedACFArray[t][i] = iii
                iii = iii + 1
    
    def ComputeFlowUnservedHospitalArray(self):

        iii = self.StartFlowUnservedHospitalFromPreviousStage

        self.FlowUnservedHospitalArray = [[-1 
                                        for h in self.Instance.HospitalSet]   
                                        for t in self.RangePeriodPatientTransfer]     
        
        for t in self.RangePeriodPatientTransfer:
            for h in self.Instance.HospitalSet:
                self.FlowUnservedHospitalArray[t][h] = iii
                iii = iii + 1

    def ComputeFlowIndexArray(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ComputeFlowIndexArray)")

        iii = self.StartFlowFromPreviousStage

        self.FlowIndexArray = [[-1 for d in self.Instance.DemandSet]
                                 for t in self.RangePeriodShortage]    
        
        for t in self.RangePeriodShortage:
                for d in self.Instance.DemandSet:
                    self.FlowIndexArray[t][d] = iii
                    iii = iii + 1
      
    def GetPatientFlowConstraintRHS(self, j, c, l, t, scenario, forwardpass):
        if Constants.Debug: print("We are in 'SDDPStage' Class -- GetPatientFlowConstraintRHS")

        righthandside = 0

        if not self.IsFirstStage():
            if forwardpass:
                #if Constants.Debug: 
                    # print("We are in Forward Pass!")
                    #print("Current Scenario Demands:", self.SDDPOwner.CurrentSetOfTrialScenarios[scenario].Demands)
                    #print("Time Period Associated:", self.GetTimePeriodAssociatedToPatientTransferVariable(t))
                # Print the demand for the specific demand location and time period in the scenario
                demand_value = self.SDDPOwner.CurrentSetOfTrialScenarios[scenario].Demands[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][j][c][l]
                righthandside += demand_value
            else:
                #if Constants.Debug: 
                    # print("We are in Backward Pass!")
                    # print("SetOfSAAScenarioDemand:", self.SDDPOwner.SetOfSAAScenarioDemand)
                    # print("Current Demand Scenario:", self.SDDPOwner.SetOfSAAScenarioDemand[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][scenario])
                    # print("Time Period Associated:", self.GetTimePeriodAssociatedToPatientTransferVariable(t))
                demand_value = self.SDDPOwner.SetOfSAAScenarioDemand[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][scenario][j][c][l]
                righthandside += demand_value

        
        #if Constants.Debug: print(f"Final RHS for w:{scenario}, t:{self.TimeDecisionStage + t}, j:{j}, c:{c}, l:{l}, forwardpass={forwardpass}: {righthandside}")
        
        return righthandside
    
    def GetHospitalTreatmentCapacityConstraintRHS(self, h, t, scenario, forwardpass):
        if Constants.Debug: print("We are in 'SDDPStage' Class -- GetHospitalTreatmentCapacityConstraintRHS")

        righthandside = 0

        if not self.IsFirstStage():
            if forwardpass:
                #if Constants.Debug: 
                    #print("We are in Forward Pass!")
                    #print("Current Scenario HospitalCaps:", self.SDDPOwner.CurrentSetOfTrialScenarios[scenario].HospitalCaps)
                    #print("Time Period Associated:", self.GetTimePeriodAssociatedToPatientTransferVariable(t))
                hospitalcap_value = self.SDDPOwner.CurrentSetOfTrialScenarios[scenario].HospitalCaps[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][h]
                righthandside += hospitalcap_value
            else:
                #if Constants.Debug: 
                    # print("We are in Backward Pass!")
                    # print("SetOfSAAScenarioHospitalCapacity:", self.SDDPOwner.SetOfSAAScenarioHospitalCapacity)
                    # print("Current Hospital Scenario:", self.SDDPOwner.SetOfSAAScenarioHospitalCapacity[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][scenario])
                    # print("Time Period Associated:", self.GetTimePeriodAssociatedToPatientTransferVariable(t))
                rhs_value = self.SDDPOwner.SetOfSAAScenarioHospitalCapacity[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][scenario][h]
                righthandside += rhs_value

        
        # if Constants.Debug: print(f"Final RHS for w:{scenario}, t:{self.TimeDecisionStage + t}, h:{h}, forwardpass={forwardpass}: {righthandside}")
        
        return righthandside
    
    def GetApheresisCapacityDonorsConstraintRHS(self, c, u, t, scenario, forwardpass):
        if Constants.Debug: print("We are in 'SDDPStage' Class -- GetApheresisCapacityDonorsConstraintRHS")

        righthandside = 0

        if not self.IsFirstStage():
            if forwardpass:
                #if Constants.Debug: 
                    #print("We are in Forward Pass!")
                    #print("Current Scenario ApheresisDonors:", self.SDDPOwner.CurrentSetOfTrialScenarios[scenario].ApheresisDonors)
                    #print("Time Period Associated:", self.GetTimePeriodAssociatedToPatientTransferVariable(t))
                ApheresisDonors_value = self.SDDPOwner.CurrentSetOfTrialScenarios[scenario].ApheresisDonors[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][c][u]
                righthandside += ApheresisDonors_value
            else:
                #if Constants.Debug: 
                    # print("We are in Backward Pass!")
                    # print("SetOfSAAScenarioApheresisDonor:", self.SDDPOwner.SetOfSAAScenarioApheresisDonor)
                    # print("Current Apheresis Donors Scenario:", self.SDDPOwner.SetOfSAAScenarioApheresisDonor[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][scenario])
                    # print("Time Period Associated:", self.GetTimePeriodAssociatedToPatientTransferVariable(t))
                ApheresisDonors_value = self.SDDPOwner.SetOfSAAScenarioApheresisDonor[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][scenario][c][u]
                righthandside += ApheresisDonors_value

        #if Constants.Debug: print(f"Final RHS for w:{scenario}, t:{self.TimeDecisionStage + t}, c:{c}, u:{u} forwardpass={forwardpass}: {righthandside}")
        
        return righthandside
    
    def GetWholeCapacityDonorsConstraintRHS(self, c, h, t, scenario, forwardpass):
        if Constants.Debug: print("We are in 'SDDPStage' Class -- GetWholeCapacityDonorsConstraintRHS")

        righthandside = 0

        if not self.IsFirstStage():
            if forwardpass:
                #if Constants.Debug: 
                    #print("We are in Forward Pass!")
                    #print("Current Scenario WholeDonors:", self.SDDPOwner.CurrentSetOfTrialScenarios[scenario].WholeDonors)
                    #print("Time Period Associated:", self.GetTimePeriodAssociatedToPatientTransferVariable(t))
                WholeDonors_value = self.SDDPOwner.CurrentSetOfTrialScenarios[scenario].WholeDonors[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][c][h]
                righthandside += WholeDonors_value
            else:
                #if Constants.Debug: 
                    # print("We are in Backward Pass!")
                    # print("SetOfSAAScenarioWholeDonor:", self.SDDPOwner.SetOfSAAScenarioWholeDonor)
                    # print("Current Whole Donors Scenario:", self.SDDPOwner.SetOfSAAScenarioWholeDonor[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][scenario])
                    # print("Time Period Associated:", self.GetTimePeriodAssociatedToPatientTransferVariable(t))
                rhs_value = self.SDDPOwner.SetOfSAAScenarioWholeDonor[self.GetTimePeriodAssociatedToPatientTransferVariable(t)][scenario][c][h]
                righthandside += rhs_value

        #if Constants.Debug: print(f"Final RHS for w:{scenario}, t:{self.TimeDecisionStage + t}, c:{c}, h:{h} forwardpass={forwardpass}: {righthandside}")
        
        return righthandside

    def GetTimeIndexForTransshipmentHH(self, time):

        result = time - self.TimeDecisionStage

        return result
    
    def GetTimeIndexForTransshipmentHI(self, time):

        result = time - self.TimeDecisionStage

        return result
    
    def GetTimeIndexForApheresisAssignment(self, time):

        result = time - self.TimeDecisionStage

        return result
    
    def GetTimeIndexForTransshipmentII(self, time):

        result = time - self.TimeDecisionStage

        return result
    
    def GetTimeIndexForVarTrans(self, d , time):

        result = time - self.TimeDecisionStage

        return result
    
    def GetTimeIndexForPatientTransfer(self, time):
        result = time - self.TimeObservationStage

        return result
    
    def GetTimeIndexForUnsatisfiedPatients(self, time):
        result = time - self.TimeObservationStage

        return result
    
    def GetTimeIndexForPlateletInventory(self, time):
        result = time - self.TimeObservationStage

        return result
    
    def GetTimeIndexForOutdatedPlatelet(self, time):
        result = time - self.TimeObservationStage

        return result
    
    def GetTimeIndexForServedPatient(self, time):
        result = time - self.TimeObservationStage

        return result
    
    def GetTimeIndexForPatientPostponement(self, time):
        result = time - self.TimeObservationStage

        return result
    
    def GetTimeIndexForPlateletApheresisExtraction(self, time):
        result = time - self.TimeObservationStage

        return result
    
    def GetTimeIndexForPlateletWholeExtraction(self, time):
        result = time - self.TimeObservationStage

        return result
    
    #This function returns the right hand side of the ACFTreatmentCapacity Constraint associated
    def GetACFTreatmentCapacityConstraintRHS(self, i):

        x_value = self.SDDPOwner.GetACFEstablishmentFixedEarlier(i, self.CurrentTrialNr)
        righthandside = self.Instance.ACF_Bed_Capacity[i] * x_value
        return righthandside
    
    #This function returns the right hand side of the ACFRescueVehicleCapacity Constraint associated
    def GetACFRescueVehicleCapacityConstraintRHS(self, m, i):

        thetavar_value = self.SDDPOwner.GetVehicleAssignmentFixedEarlier(m, i, self.CurrentTrialNr)
        righthandside = self.Instance.Rescue_Vehicle_Capacity[m] * thetavar_value
                        
        return righthandside
        
    #This function returns the right hand side of the CFPlateletFlow Constraint associated
    def GetACFApheresisCapConstraintRHS(self, i):

        x_value = self.SDDPOwner.GetACFEstablishmentFixedEarlier(i, self.CurrentTrialNr)
        righthandside =  self.Instance.Total_Apheresis_Machine_ACF[self.TimeDecisionStage] * x_value    
                        
        return righthandside
    
    #This function returns the right hand side of the BigM consraint associated
    def GetBigMConstrainRHS(self, s, d):

        if self.IsFirstStage():
            righthandside = 0.0
        else:
            yvalue = self.SDDPOwner.GetFixedTransVarFixedEarlier(s, d, self.CurrentTrialNr)
            righthandside = self.Instance.BigMValue * yvalue
                        
        return righthandside

    def CreateBudgetConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreateBudgetConstraint")
       
        vars_x = [self.GetIndexACFEstablishmentVariable(i) for i in self.Instance.ACFPPointSet]
        coeff_x = [-self.Instance.Fixed_Cost_ACF_Constraint[i] for i in self.Instance.ACFPPointSet]
                
        LeftHandSide = gp.quicksum(coeff_x[i] * self.ACFEstablishment_Var_SDDP[vars_x[i]] for i in range(len(vars_x)))

        # Define the right-hand side (RHS) of the constraint
        RightHandSide =  -1.0 * self.Instance.Total_Budget_ACF_Establishment

        #if Constants.Debug: 
            #print(f"Vars_x: {vars_x}")
            #print(f"Coeff_x: {coeff_x}")
            #print(f"RightHandSide: {RightHandSide}")

        # Add the constraint to the model
        constraint_name = f"Budget_index_{self.LastAddedConstraintIndex}"
        self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

        self.BudgetConstraint_Names.append(constraint_name)
        
        self.GurobiModel.update()
        self.IndexBudgetConstraint.append(self.LastAddedConstraintIndex)
        self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

    def CreateVehicleAssignmentCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreateVehicleAssignmentCapacityConstraint")

        for m in self.Instance.RescueVehicleSet:
            
            vars_theta = [self.GetIndexVehicleAssignmentVariable(m, i) for i in self.Instance.ACFPPointSet]
            coeff_theta = [-1.0 for i in self.Instance.ACFPPointSet]

            
            #Create the left-hand side of the constraint
            LeftHandSide = gp.quicksum(coeff_theta[i] * self.VehicleAssignment_Var_SDDP[vars_theta[i]] for i in range(len(vars_theta)))

            # Define the right-hand side (RHS) of the constraint
            RightHandSide = -1.0 * self.Instance.Number_Rescue_Vehicle_ACF[m]

            #if Constants.Debug: 
                #print(f"Vars_x: {vars_theta}")
                #print(f"Coefficients: {coeff_theta}")
                #print(f"RightHandSide: {RightHandSide}")

            # Add the constraint to the model
            constraint_name = f"VehicleAssignmentCapacity_m_{m}_index_{self.LastAddedConstraintIndex}"
            self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

            self.VehicleAssignmentCapacityConstraint_Names.append(constraint_name)
            
            self.GurobiModel.update()
            self.IndexVehicleAssignmentCapacityConstraint.append(self.LastAddedConstraintIndex)
            self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

            self.ConcernedVehicleVehicleAssignmentCapacityConstraint.append(m)

    def CreateVehicleAssignemntACFEstablishmentConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreateVehicleAssignemntACFEstablishmentConstraint")

        for i in self.Instance.ACFPPointSet:
            for m in self.Instance.RescueVehicleSet:

                vars_x = [self.GetIndexACFEstablishmentVariable(i)]
                coeff_x = [self.Instance.Number_Rescue_Vehicle_ACF[m]]
                
                vars_theta = [self.GetIndexVehicleAssignmentVariable(m, i)]
                coeff_theta = [-1.0]
                
                #Create the left-hand side of the constraint
                LeftHandSide_x = gp.quicksum(coeff_x[i] * self.ACFEstablishment_Var_SDDP[vars_x[i]] for i in range(len(vars_x)))
                LeftHandSide_theta = gp.quicksum(coeff_theta[i] * self.VehicleAssignment_Var_SDDP[vars_theta[i]] for i in range(len(vars_theta)))

                LeftHandSide = LeftHandSide_x + LeftHandSide_theta

                # Define the right-hand side (RHS) of the constraint
                RightHandSide = 0

                #if Constants.Debug: 
                    #print(f"Vars_x: {coeff_x} * {vars_x}")
                    #print(f"vars_theta: {coeff_theta} * {vars_theta}")
                    #print(f"RightHandSide: {RightHandSide}")

                # Add the constraint to the model
                constraint_name = f"VehicleAssignemntACFEstablishment_i_{i}_m_{m}_index_{self.LastAddedConstraintIndex}"
                self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                self.VehicleAssignemntACFEstablishmentConstraint_Names.append(constraint_name)

                self.GurobiModel.update()
                self.IndexVehicleAssignemntACFEstablishmentConstraint.append(self.LastAddedConstraintIndex)
                self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                self.ConcernedvehicleVehicleAssignemntACFEstablishmentConstraint.append(m)
                self.ConcernedACFVehicleAssignemntACFEstablishmentConstraint.append(i)

    def CreateNrApheresisLimitConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreateNrApheresisLimitConstraint")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodApheresisAssignment:
                
                vars_y = [self.GetIndexApheresisAssignmentVariable(i, t, w) for i in self.Instance.ACFPPointSet]
                coeff_y = [-1.0 for i in self.Instance.ACFPPointSet]
                
                #Create the left-hand side of the constraint
                LeftHandSide = gp.quicksum(coeff_y[i] * self.ApheresisAssignment_Var_SDDP[vars_y[i]] for i in range(len(vars_y)))

                # Define the right-hand side (RHS) of the constraint
                RightHandSide = -1.0 * self.Instance.Total_Apheresis_Machine_ACF[t] 

                #if Constants.Debug:  # Print the variables and coefficients for debugging
                    #print(f"LeftHandSide: {coeff_y} * {vars_y}")
                    #print(f"RightHandSide: {RightHandSide}")

                # Add the constraint to the model
                constraint_name = f"NrApheresisLimit_w_{w}_t_{self.TimeDecisionStage+t}_index_{self.LastAddedConstraintIndex}"
                self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                self.NrApheresisLimitConstraint_Names.append(constraint_name)
                
                self.GurobiModel.update()

                self.IndexNrApheresisLimitConstraint.append(self.LastAddedConstraintIndex)
                self.IndexNrApheresisLimitConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                self.ConcernedTimeNrApheresisLimitConstraint.append(self.GetTimePeriodAssociatedToApheresisAssignmentVariable(t)) 
                self.ConcernedScenarioNrApheresisLimitConstraint.append(w)

    def CreateApheresisACFConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (CreateApheresisACFConstraint)")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodApheresisAssignment:
                for i in self.Instance.ACFPPointSet:

                    if self.IsFirstStage():
                        #print("It is the First Stage!")

                        vars_y = [self.GetIndexApheresisAssignmentVariable(i, t, w)]
                        coeff_y = [-1.0]

                        vars_x = [self.GetIndexACFEstablishmentVariable(i)]
                        coeff_x = [self.Instance.Total_Apheresis_Machine_ACF[t]]

                        ############ Create the left-hand side of the constraint       
                        LeftHandSide_y = gp.quicksum(coeff_y[i] * self.ApheresisAssignment_Var_SDDP[vars_y[i]] for i in range(len(vars_y)))
                        LeftHandSide_x = gp.quicksum(coeff_x[i] * self.ACFEstablishment_Var_SDDP[vars_x[i]] for i in range(len(vars_x)))
                                                                                    
                        LeftHandSide = LeftHandSide_y + LeftHandSide_x
                        
                        ############ Define the right-hand side (RHS) of the constraint
                        RightHandSide = 0                   

                        ############ Add the constraint to the model
                        constraint_name = f"ApheresisACF_w_{w}_t_{self.TimeDecisionStage + t}_i_{i}_index_{self.LastAddedConstraintIndex}"
                        self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                        self.ApheresisACFConstraint_Names.append(constraint_name)

                    else:
                        #print("It is Not the First Stage!")
                        vars_y = [self.GetIndexApheresisAssignmentVariable(i, t, w)]
                        coeff_y = [-1.0]
                                                
                        vars_x = [self.GetIndexACFEstablishmentRHS_ApheresisAssignCon(i)]
                        coeff_x = [1.0]
                        
                        ########### Create the left-hand side of the constraint
                        LeftHandSide_y = gp.quicksum(coeff_y[i] * self.ApheresisAssignment_Var_SDDP[vars_y[i]] for i in range(len(vars_y)))
                        LeftHandSide_x = gp.quicksum(coeff_x[i] * self.ACFApheresisCapRHS_SDDP[vars_x[i]] for i in range(len(vars_x)))
                                                        
                        LeftHandSide = LeftHandSide_y + LeftHandSide_x

                        ############ Define the right-hand side (RHS) of the constraint
                        RightHandSide = 0.0                           

                        ############ Add the constraint to the model
                        constraint_name = f"ApheresisACF_w_{w}_t_{t}_i_{i}_index_{self.LastAddedConstraintIndex}"
                        self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                        self.ApheresisACFConstraint_Names.append(constraint_name)

                    self.GurobiModel.update()
                    self.IndexApheresisACFConstraint.append(self.LastAddedConstraintIndex)
                    self.IndexApheresisACFConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                    self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                    self.ConcernedACFApheresisACFConstraint.append(i)
                    self.ConcernedTimeApheresisACFConstraint.append(self.GetTimePeriodAssociatedToApheresisAssignmentVariable(t))
                    self.ConcernedScenarioApheresisACFConstraint.append(w)
    
    def CreateHospitalTransshipmentCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreateHospitalTransshipmentCapacityConstraint")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodApheresisAssignment:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        if r != 0:
                            for h in self.Instance.HospitalSet:
                                
                                vars_b = [self.GetIndexTransshipmentHIVariable(c, r, h, i, t, w)
                                            for i in self.Instance.ACFPPointSet]
                                coeff_b = [-1.0 for i in self.Instance.ACFPPointSet]                                             
                                
                                vars_b_DoublePrime = [self.GetIndexTransshipmentHHVariable(c, r, h, hprime, t, w)
                                                        for hprime in self.Instance.HospitalSet if hprime != h]
                                coeff_b_DoublePrime = [-1.0 for hprime in self.Instance.HospitalSet if hprime != h]                                             

                                vars_eta = []
                                coeff_eta = []
                                if not self.IsFirstStage():
                                    vars_eta = [self.GetIndexPlateletInventoryVariable(c, r-1, h, t, w)]
                                    coeff_eta = [1.0] 

                                #Create the left-hand side of the constraint
                                LeftHandSide_b = gp.quicksum(coeff_b[i] * self.TransshipmentHI_Var_SDDP[vars_b[i]] for i in range(len(vars_b)))
                                
                                LeftHandSide_b_DoublePrime = gp.quicksum(coeff_b_DoublePrime[i] * self.TransshipmentHH_Var_SDDP[vars_b_DoublePrime[i]] for i in range(len(vars_b_DoublePrime)))
                                
                                LeftHandSide_eta = gp.quicksum(coeff_eta[i] * self.PlateletInventory_Var_SDDP[vars_eta[i]] for i in range(len(vars_eta))) if vars_eta else 0
                                                                            
                                LeftHandSide = LeftHandSide_b + LeftHandSide_b_DoublePrime + LeftHandSide_eta
                                
                                ############ Define the right-hand side (RHS) of the constraint
                                RightHandSide = 0  
                                if self.IsFirstStage():
                                    RightHandSide = -1.0 * self.Instance.Initial_Platelet_Inventory[c][r][h]

                                # Add the constraint to the model
                                constraint_name = f"HospitalTransshipmentCapacity_w_{w}_t_{self.TimeDecisionStage+t}_c_{c}_r_{r}_h_{h}_index_{self.LastAddedConstraintIndex}"
                                self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                                self.HospitalTransshipmentCapacityConstraint_Names.append(constraint_name)

                                #print(f"Added constraint: {constraint_name}")
                                
                                self.GurobiModel.update()
                                self.IndexHospitalTransshipmentCapacityConstraint.append(self.LastAddedConstraintIndex)
                                self.IndexHospitalTransshipmentCapacityConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                                self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                                self.ConcernedHospitalHospitalTransshipmentCapacityConstraint.append(h)
                                self.ConcernedPLTAgeHospitalTransshipmentCapacityConstraint.append(r)
                                self.ConcernedBloodGPHospitalTransshipmentCapacityConstraint.append(c)
                                self.ConcernedTimeHospitalTransshipmentCapacityConstraint.append(self.GetTimePeriodAssociatedToApheresisAssignmentVariable(t)) 
                                self.ConcernedScenarioHospitalTransshipmentCapacityConstraint.append(w)

    def CreateACFTransshipmentCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreateACFTransshipmentCapacityConstraint")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodApheresisAssignment:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        if r != 0:
                            for i in self.Instance.ACFPPointSet:

                                vars_bprime = [self.GetIndexTransshipmentIIVariable(c, r, i, iprime, t, w)
                                                    for iprime in self.Instance.ACFPPointSet if iprime != i]
                                coeff_bprime = [-1.0 for iprime in self.Instance.ACFPPointSet if iprime != i]                                             
                                                                    
                                vars_eta = []
                                coeff_eta = []

                                acf = self.Instance.NrHospitals + i
                                if not self.IsFirstStage():
                                    vars_eta = [self.GetIndexPlateletInventoryVariable(c, r-1, acf, t, w)]
                                    coeff_eta = [1.0] 

                                ############ Create the left-hand side of the constraint       
                                LeftHandSide_bprime = gp.quicksum(coeff_bprime[i] * self.TransshipmentII_Var_SDDP[vars_bprime[i]] for i in range(len(vars_bprime)))
                                
                                LeftHandSide_eta = gp.quicksum(coeff_eta[i] * self.PlateletInventory_Var_SDDP[vars_eta[i]] for i in range(len(vars_eta))) if vars_eta else 0

                                LeftHandSide = LeftHandSide_bprime + LeftHandSide_eta
                                
                                ############ Define the right-hand side (RHS) of the constraint
                                RightHandSide = 0  

                                # Add the constraint to the model
                                constraint_name = f"ACFTransshipmentCapacity_w_{w}_t_{self.TimeDecisionStage + t}_c_{c}_r_{r}_i_{i}_index_{self.LastAddedConstraintIndex}"
                                self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                                self.ACFTransshipmentCapacityConstraint_Names.append(constraint_name)

                                #print(f"Added constraint: {constraint_name}")
                            
                                self.GurobiModel.update()
                                self.IndexACFTransshipmentCapacityConstraint.append(self.LastAddedConstraintIndex)
                                self.IndexACFTransshipmentCapacityConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                                self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                                self.ConcernedACFACFTransshipmentCapacityConstraint.append(i)
                                self.ConcernedPLTAgeACFTransshipmentCapacityConstraint.append(r)
                                self.ConcernedBloodGPACFTransshipmentCapacityConstraint.append(c)
                                self.ConcernedTimeACFTransshipmentCapacityConstraint.append(self.GetTimePeriodAssociatedToApheresisAssignmentVariable(t)) 
                                self.ConcernedScenarioACFTransshipmentCapacityConstraint.append(w)

    def CreateACFTreatmentCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (CreateACFTreatmentCapacityConstraint)")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for i in self.Instance.ACFPPointSet:
                    
                    acf = self.Instance.NrHospitals + i
                    vars_q = [self.GetIndexPatientTransferVariable(j, c, l , acf, m, t, w)
                                for j in self.Instance.InjuryLevelSet if self.Instance.J_u[acf][j] == 1
                                for c in self.Instance.BloodGPSet
                                for l in self.Instance.DemandSet
                                for m in self.Instance.RescueVehicleSet]                    
                    coeff_q = [-1.0 
                                for j in self.Instance.InjuryLevelSet if self.Instance.J_u[acf][j] == 1
                                for c in self.Instance.BloodGPSet
                                for l in self.Instance.DemandSet
                                for m in self.Instance.RescueVehicleSet]

                    vars_prev = [self.GetIndexFlowUnservedACFFromPreviousStage(i, t)]
                    coeff_prev = [-1.0]

                    vars_x = [self.GetIndexACFEstablishmentRHS_ACFTreatCapConst(i)]
                    coeff_x = [1.0]
                    
                    ########### Create the left-hand side of the constraint
                    LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var_SDDP[vars_q[i]] for i in range(len(vars_q)))
                    LeftHandSide_prev = gp.quicksum(coeff_prev[i] * self.flowUnservedACFFromPreviousStage_SDDP[vars_prev[i]] for i in range(len(vars_prev))) if vars_prev else 0                    
                    LeftHandSide_x = gp.quicksum(coeff_x[i] * self.ACFTreatmentCapRHS_SDDP[vars_x[i]] for i in range(len(vars_x)))

                    LeftHandSide = LeftHandSide_q + LeftHandSide_prev + LeftHandSide_x

                    ############ Define the right-hand side (RHS) of the constraint
                    RightHandSide = 0.0                           

                    ############ Add the constraint to the model
                    constraint_name = f"ACFTreatmentCapacityConstraint_w_{w}_t_{self.TimeDecisionStage+t}_i_{i}_index_{self.LastAddedConstraintIndex}"
                    self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                    self.ACFTreatmentCapacityConstraint_Names.append(constraint_name)

                    #print(f"Added constraint: {constraint_name}")
                    
                    self.GurobiModel.update()
                    self.IndexACFTreatmentCapacityConstraint.append(self.LastAddedConstraintIndex)
                    self.IndexACFTreatmentCapacityConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                    self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                    self.ConcernedACFACFTreatmentCapacityConstraint.append(i)
                    self.ConcernedTimeACFTreatmentCapacityConstraint.append(self.GetTimePeriodAssociatedToPatientTransferVariable(t))
                    self.ConcernedScenarioACFTreatmentCapacityConstraint.append(w)
    
    def CreateHospitalTreatmentCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (CreateHospitalTreatmentCapacityConstraint)")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for h in self.Instance.HospitalSet:
                    
                    vars_q = [self.GetIndexPatientTransferVariable(j, c, l , h, m, t, w)
                                for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1
                                for c in self.Instance.BloodGPSet
                                for l in self.Instance.DemandSet
                                for m in self.Instance.RescueVehicleSet]                  
                    coeff_q = [-1.0 
                                for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1
                                for c in self.Instance.BloodGPSet
                                for l in self.Instance.DemandSet
                                for m in self.Instance.RescueVehicleSet]

                    vars_prev = [self.GetIndexFlowUnservedHospitalFromPreviousStage(h, t)]
                    coeff_prev = [-1.0]
                    
                    ########### Create the left-hand side of the constraint
                    LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var_SDDP[vars_q[i]] for i in range(len(vars_q)))
                    LeftHandSide_prev = gp.quicksum(coeff_prev[i] * self.flowUnservedHospitalFromPreviousStage_SDDP[vars_prev[i]] for i in range(len(vars_prev))) if vars_prev else 0

                    LeftHandSide = LeftHandSide_q + LeftHandSide_prev

                    ############ Define the right-hand side (RHS) of the constraint
                    RightHandSide = -1.0 * self.GetHospitalTreatmentCapacityConstraintRHS(h, t, w, self.IsForward)                         

                    ############ Add the constraint to the model
                    constraint_name = f"HospitalTreatmentCapacityConstraint_w_{w}_t_{self.TimeDecisionStage+t}_h_{h}_index_{self.LastAddedConstraintIndex}"
                    constraint_obj = self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                    self.HospitalTreatmentCapacityConstraint_Objects.append(constraint_obj)         #This line of code make updating constraint in later stages easier

                    self.HospitalTreatmentCapacityConstraint_Names.append(constraint_name)

                    #print(f"Added constraint: {constraint_name}")
                    
                    self.GurobiModel.update()
                    self.IndexHospitalTreatmentCapacityConstraint.append(self.LastAddedConstraintIndex)
                    self.IndexHospitalTreatmentCapacityConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                    self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                    self.ConcernedHospitalHospitalTreatmentCapacityConstraint.append(h)
                    self.ConcernedTimeHospitalTreatmentCapacityConstraint.append(self.GetTimePeriodAssociatedToPatientTransferVariable(t))
                    self.ConcernedScenarioHospitalTreatmentCapacityConstraint.append(w)
                        
    def CreatePIApheresisACFConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (CreatePIApheresisACFConstraint)")
        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGoApheresisAssignment:  #We use "TimePeriodToGoApheresisAssignment" instead of "TimePeriodToGo", Because we already defined the same constraint for in the first stage!
                    for i in self.Instance.ACFPPointSet:
                        if self.IsFirstStage():
                            
                            ######### y
                            vars_y = [self.GetIndexPIApheresisAssignmentVariable(i, t, wevpi, w)]
                            coeff_y = [-1.0]
                            if t in self.PeriodsInGlobalMIPApheresisAssignment:
                                LeftHandSide_y = (coeff_y[0] * self.ApheresisAssignment_Var_SDDP[vars_y[0]])
                            else:
                                LeftHandSide_y = (coeff_y[0] * self.ApheresisAssignment_Var_SDDP_EVPI[vars_y[0]])

                            ########## x
                            vars_x = [self.GetIndexACFEstablishmentVariable(i)]
                            coeff_x = [self.Instance.Total_Apheresis_Machine_ACF[t]]
                            LeftHandSide_x = (coeff_x[0] * self.ACFEstablishment_Var_SDDP[vars_x[0]])

                            ############ Create the left-hand side of the constraint
                            LeftHandSide = LeftHandSide_y + LeftHandSide_x

                            ############ Define the right-hand side (RHS) of the constraint
                            RightHandSide = 0.0                           

                            ############ Add the constraint to the model
                            constraint_name = f"ApheresisACFConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_i_{i}_index_{self.LastAddedConstraintIndex}"
                            self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                        else:
                            #print("It is Not the First Stage!")
                            
                            ######### y
                            vars_y = [self.GetIndexPIApheresisAssignmentVariable(i, t, wevpi, w)]
                            coeff_y = [-1.0]
                            if t in self.PeriodsInGlobalMIPApheresisAssignment:
                                LeftHandSide_y = (coeff_y[0] * self.ApheresisAssignment_Var_SDDP[vars_y[0]])
                            else:
                                LeftHandSide_y = (coeff_y[0] * self.ApheresisAssignment_Var_SDDP_EVPI[vars_y[0]])

                            ########## x
                            vars_x = [self.GetIndexACFEstablishmentRHS_ApheresisAssignCon(i)]
                            coeff_x = [self.Instance.Total_Apheresis_Machine_ACF[t]]
                            LeftHandSide_x = (coeff_x[0] * self.ACFApheresisCapRHS_SDDP[vars_x[0]])

                            ############ Create the left-hand side of the constraint
                            LeftHandSide = LeftHandSide_y + LeftHandSide_x
                            
                            ############ Define the right-hand side (RHS) of the constraint
                            RightHandSide = 0.0                           

                            ############ Add the constraint to the model
                            constraint_name = f"ApheresisACFConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_i_{i}_index_{self.LastAddedConstraintIndex}"
                            self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)   
                        
                        self.GurobiModel.update()
                        self.PIApheresisACFConstraint_Names.append(constraint_name) 
                        self.IndexPIApheresisACFConstraint.append(self.LastAddedConstraintIndex)
                        self.IndexPIApheresisACFConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                        self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                        self.ConcernedACFPIApheresisACFConstraint.append(i)
                        self.ConcernedTimePIApheresisACFConstraint.append(t)
                        self.ConcernedScenarioPIApheresisACFConstraint.append(w)                            
    
    def CreatePIACFRescueVehicleCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (CreatePIACFRescueVehicleCapacityConstraint)")
        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for i in self.Instance.ACFPPointSet:
                        for m in self.Instance.RescueVehicleSet:
                            acf = self.Instance.NrHospitals + i

                            if self.IsFirstStage():
                                #if Constants.Debug: print("It is the First Stage!")
                                
                                ############ q
                                vars_q = [self.GetIndexPIPatientTransferVariable(j, c, l , acf, m, t, wevpi, w)
                                            for j in self.Instance.InjuryLevelSet if self.Instance.J_u[acf][j] == 1
                                            for c in self.Instance.BloodGPSet
                                            for l in self.Instance.DemandSet]
                                
                                coeff_q = [-1.0 * self.Instance.Distance_D_A[l][i] 
                                            for j in self.Instance.InjuryLevelSet if self.Instance.J_u[acf][j] == 1
                                            for c in self.Instance.BloodGPSet
                                            for l in self.Instance.DemandSet] 
                                if t in self.PeriodsInGlobalMIPPatientTransfer:
                                    LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var_SDDP[vars_q[i]] for i in range(len(vars_q)))
                                else:
                                    LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var_SDDP_EVPI[vars_q[i]] for i in range(len(vars_q)))

                                ########## thetavar
                                vars_thetavar = [self.GetIndexVehicleAssignmentVariable(m, i)]
                                coeff_thetavar = [+1.0 * self.Instance.Rescue_Vehicle_Capacity[m]]
                                LeftHandSide_thetavar = (coeff_thetavar[0] * self.VehicleAssignment_Var_SDDP[vars_thetavar[0]])

                                ############ Create the left-hand side of the constraint
                                LeftHandSide = LeftHandSide_q + LeftHandSide_thetavar

                                ############ Define the right-hand side (RHS) of the constraint
                                RightHandSide = 0.0                           

                                ############ Add the constraint to the model
                                constraint_name = f"ACFRescueVehicleCapacityConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_i_{i}_m_{m}_index_{self.LastAddedConstraintIndex}"
                                self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                            else:
                                #if Constants.Debug: print("It is Not the First Stage!")
                                ############ q
                                vars_q = [self.GetIndexPIPatientTransferVariable(j, c, l , acf, m, t, wevpi, w)
                                            for j in self.Instance.InjuryLevelSet if self.Instance.J_u[acf][j] == 1
                                            for c in self.Instance.BloodGPSet
                                            for l in self.Instance.DemandSet]
                                
                                coeff_q = [-1.0 * self.Instance.Distance_D_A[l][i] 
                                            for j in self.Instance.InjuryLevelSet if self.Instance.J_u[acf][j] == 1
                                            for c in self.Instance.BloodGPSet
                                            for l in self.Instance.DemandSet] 
                                if t in self.PeriodsInGlobalMIPPatientTransfer:
                                    LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var_SDDP[vars_q[i]] for i in range(len(vars_q)))
                                else:
                                    LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var_SDDP_EVPI[vars_q[i]] for i in range(len(vars_q)))

                                ########## thetavar
                                vars_thetavar = [self.GetIndexVehicleAssignmentRHS_ACFRescVehCapCons(m, i)]
                                coeff_thetavar = [+1.0 * self.Instance.Rescue_Vehicle_Capacity[m]]
                                LeftHandSide_thetavar = (coeff_thetavar[0] * self.ACFRescVehicCapRHS_SDDP[vars_thetavar[0]])

                                ############ Create the left-hand side of the constraint
                                LeftHandSide = LeftHandSide_q + LeftHandSide_thetavar
                                
                                ############ Define the right-hand side (RHS) of the constraint
                                RightHandSide = 0.0                           

                                ############ Add the constraint to the model
                                constraint_name = f"ACFRescueVehicleCapacityConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_i_{i}_m_{m}_index_{self.LastAddedConstraintIndex}"
                                self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)     

                            self.GurobiModel.update()
                            self.PIACFRescueVehicleCapacityConstraint_Names.append(constraint_name) 
                            self.IndexPIACFRescueVehicleCapacityConstraint.append(self.LastAddedConstraintIndex)
                            self.IndexPIACFRescueVehicleCapacityConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                            self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                            self.ConcernedACFPIACFRescueVehicleCapacityConstraint.append(i)
                            self.ConcernedVehiclePIACFRescueVehicleCapacityConstraint.append(m)
                            self.ConcernedTimePIACFRescueVehicleCapacityConstraint.append(t)
                            self.ConcernedScenarioPIACFRescueVehicleCapacityConstraint.append(w)                            
    
    def CreatePIACFTreatmentCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (CreatePIACFTreatmentCapacityConstraint)")
        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for i in self.Instance.ACFPPointSet:
                        acf = self.Instance.NrHospitals + i
                        if self.IsFirstStage():
                            #if Constants.Debug: print("It is the First Stage!")

                            LeftHandSide_q = gp.LinExpr()  
                            LeftHandSide_prev_zeta = gp.LinExpr()  

                            ##################### q
                            q_index = [self.GetIndexPIPatientTransferVariable(j, c, l , acf, m, t, wevpi, w)
                                        for j in self.Instance.InjuryLevelSet if self.Instance.J_u[acf][j] == 1
                                        for c in self.Instance.BloodGPSet
                                        for l in self.Instance.DemandSet
                                        for m in self.Instance.RescueVehicleSet]                    
                            if t in self.PeriodsInGlobalMIPPatientTransfer:
                                q_var = [self.PatientTransfer_Var_SDDP[q_index[i]] for i in range(len(q_index))]
                            else:
                                q_var = [self.PatientTransfer_Var_SDDP_EVPI[q_index[i]] for i in range(len(q_index))]
                            q_coeff = [-1.0 for i in range(len(q_index))]
                            LeftHandSide_q.addTerms(q_coeff, q_var)

                            ##################### Previous zeta
                            if t > 0:
                                prev_zeta_index = [self.GetIndexPIPatientPostponementVariable(j, c, acf, (t-1), wevpi, w)
                                                    for j in self.Instance.InjuryLevelSet if self.Instance.J_u[acf][j] == 1
                                                    for c in self.Instance.BloodGPSet]
                                if (t-1) in self.PeriodsInGlobalMIPPatientPostponement:
                                    prev_zeta_var = [self.PatientPostponement_Var_SDDP[prev_zeta_index[i]] for i in range(len(prev_zeta_index))]
                                else:
                                    prev_zeta_var = [self.PatientPostponement_Var_SDDP_EVPI[prev_zeta_index[i]] for i in range(len(prev_zeta_index))]
                                prev_zeta_coeff = [-1.0 for i in range(len(prev_zeta_index))]
                                LeftHandSide_prev_zeta.addTerms(prev_zeta_coeff, prev_zeta_var)

                            ##################### x
                            vars_x = [self.GetIndexACFEstablishmentVariable(i)]
                            coeff_x = [self.Instance.ACF_Bed_Capacity[i]]
                            LeftHandSide_x = (coeff_x[0] * self.ACFEstablishment_Var_SDDP[vars_x[0]])

                            ############ Create the left-hand side of the constraint
                            LeftHandSide = LeftHandSide_q + LeftHandSide_prev_zeta + LeftHandSide_x

                            ############ Define the right-hand side (RHS) of the constraint
                            RightHandSide = 0.0                           

                            ############ Add the constraint to the model
                            constraint_name = f"ACFTreatmentCapacityConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_i_{i}_index_{self.LastAddedConstraintIndex}"
                            self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                        else:
                            #if Constants.Debug: print("It is Not the First Stage!")
                            LeftHandSide_q = gp.LinExpr()  
                            LeftHandSide_prev_zeta = gp.LinExpr()  

                            ##################### q
                            q_index = [self.GetIndexPIPatientTransferVariable(j, c, l , (acf), m, t, wevpi, w)
                                        for j in self.Instance.InjuryLevelSet if self.Instance.J_u[acf][j] == 1
                                        for c in self.Instance.BloodGPSet
                                        for l in self.Instance.DemandSet
                                        for m in self.Instance.RescueVehicleSet]                    
                            if t in self.PeriodsInGlobalMIPPatientTransfer:
                                q_var = [self.PatientTransfer_Var_SDDP[q_index[i]] for i in range(len(q_index))]
                            else:
                                q_var = [self.PatientTransfer_Var_SDDP_EVPI[q_index[i]] for i in range(len(q_index))]
                            q_coeff = [-1.0 for i in range(len(q_index))]
                            LeftHandSide_q.addTerms(q_coeff, q_var)

                            ##################### Previous zeta
                            if t > 0:
                                prev_zeta_index = [self.GetIndexPIPatientPostponementVariable(j, c, (acf), (t-1), wevpi, w)
                                                    for j in self.Instance.InjuryLevelSet if self.Instance.J_u[acf][j] == 1
                                                    for c in self.Instance.BloodGPSet]
                                if (t-1) in self.PeriodsInGlobalMIPPatientPostponement:
                                    prev_zeta_var = [self.PatientPostponement_Var_SDDP[prev_zeta_index[i]] for i in range(len(prev_zeta_index))]
                                else:
                                    prev_zeta_var = [self.PatientPostponement_Var_SDDP_EVPI[prev_zeta_index[i]] for i in range(len(prev_zeta_index))]
                                prev_zeta_coeff = [-1.0 for i in range(len(prev_zeta_index))]
                                LeftHandSide_prev_zeta.addTerms(prev_zeta_coeff, prev_zeta_var)

                            ##################### x
                            vars_x = [self.GetIndexACFEstablishmentRHS_ACFTreatCapConst(i)]
                            coeff_x = [self.Instance.ACF_Bed_Capacity[i]]
                            LeftHandSide_x = (coeff_x[0] * self.ACFTreatmentCapRHS_SDDP[vars_x[0]])

                            ############ Create the left-hand side of the constraint
                            LeftHandSide = LeftHandSide_q + LeftHandSide_prev_zeta + LeftHandSide_x

                            ############ Define the right-hand side (RHS) of the constraint
                            RightHandSide = 0.0                           

                            ############ Add the constraint to the model
                            constraint_name = f"ACFTreatmentCapacityConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_i_{i}_index_{self.LastAddedConstraintIndex}"
                            self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                        self.GurobiModel.update()
                        self.PIACFTreatmentCapacityConstraint_Names.append(constraint_name)
                        self.IndexPIACFTreatmentCapacityConstraint.append(self.LastAddedConstraintIndex)
                        self.IndexPIACFTreatmentCapacityConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                        self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                        self.ConcernedACFPIACFTreatmentCapacityConstraint.append(i)
                        self.ConcernedTimePIACFTreatmentCapacityConstraint.append(t)
                        self.ConcernedScenarioPIACFTreatmentCapacityConstraint.append(w)                            
    
    def CreatePIHospitalTreatmentCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (CreatePIHospitalTreatmentCapacityConstraint)")
        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for h in self.Instance.HospitalSet:
                        LeftHandSide_q = gp.LinExpr()  
                        LeftHandSide_prev_zeta = gp.LinExpr()  

                        ##################### q
                        q_index = [self.GetIndexPIPatientTransferVariable(j, c, l , h, m, t, wevpi, w)
                                    for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1
                                    for c in self.Instance.BloodGPSet
                                    for l in self.Instance.DemandSet
                                    for m in self.Instance.RescueVehicleSet]                    
                        if t in self.PeriodsInGlobalMIPPatientTransfer:
                            q_var = [self.PatientTransfer_Var_SDDP[q_index[i]] for i in range(len(q_index))]
                        else:
                            q_var = [self.PatientTransfer_Var_SDDP_EVPI[q_index[i]] for i in range(len(q_index))]
                        q_coeff = [-1.0 for i in range(len(q_index))]
                        LeftHandSide_q.addTerms(q_coeff, q_var)

                        ##################### Previous zeta
                        if t > 0:
                            prev_zeta_index = [self.GetIndexPIPatientPostponementVariable(j, c, h, (t-1), wevpi, w)
                                                for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1
                                                for c in self.Instance.BloodGPSet]
                            if (t-1) in self.PeriodsInGlobalMIPPatientPostponement:
                                prev_zeta_var = [self.PatientPostponement_Var_SDDP[prev_zeta_index[i]] for i in range(len(prev_zeta_index))]
                            else:
                                prev_zeta_var = [self.PatientPostponement_Var_SDDP_EVPI[prev_zeta_index[i]] for i in range(len(prev_zeta_index))]
                            prev_zeta_coeff = [-1.0 for i in range(len(prev_zeta_index))]
                            LeftHandSide_prev_zeta.addTerms(prev_zeta_coeff, prev_zeta_var)

                        ############ Create the left-hand side of the constraint
                        LeftHandSide = LeftHandSide_q + LeftHandSide_prev_zeta

                        ############ Define the right-hand side (RHS) of the constraint
                        RightHandSide = -1.0 * self.EVPIScenarioSet[wevpi].HospitalCaps[t][h]                      

                        ############ Add the constraint to the model
                        constraint_name = f"HospitalTreatmentCapacityConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_h_{h}_index_{self.LastAddedConstraintIndex}"
                        self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                        self.GurobiModel.update()
                        self.PIHospitalTreatmentCapacityConstraint_Names.append(constraint_name)
                        self.IndexPIHospitalTreatmentCapacityConstraint.append(self.LastAddedConstraintIndex)
                        self.IndexPIHospitalTreatmentCapacityConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                        self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                        self.ConcernedHospitalPIHospitalTreatmentCapacityConstraint.append(h)
                        self.ConcernedTimePIHospitalTreatmentCapacityConstraint.append(t)
                        self.ConcernedScenarioPIHospitalTreatmentCapacityConstraint.append(w)                            
                        self.ConcernedEVPIScenarioPIHospitalTreatmentCapacityConstraint.append(wevpi)                            
    
    def CreatePIACFApheresisCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePIACFApheresisCapacityConstraint")

        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for i in self.Instance.ACFPPointSet: 
                        
                        acf = (self.Instance.NrHospitals + i)
                        ########## lambda
                        vars_lambda = [self.GetIndexPIPlateletApheresisExtractionVariable(c, acf, t, wevpi, w) 
                                        for c in self.Instance.BloodGPSet]
                        coeff_lambda = [-1.0 
                                        for c in self.Instance.BloodGPSet]
                        if t in self.PeriodsInGlobalMIPPlateletApheresisExtraction:
                            LeftHandSide_lambda = gp.quicksum(coeff_lambda[i] * self.PlateletApheresisExtraction_Var_SDDP[vars_lambda[i]] for i in range(len(vars_lambda)))
                        else:
                            LeftHandSide_lambda = gp.quicksum(coeff_lambda[i] * self.PlateletApheresisExtraction_Var_SDDP_EVPI[vars_lambda[i]] for i in range(len(vars_lambda)))

                        ########## y
                        vars_y = [self.GetIndexPIApheresisAssignmentVariable(i, t, wevpi, w)]
                        coeff_y = [self.Instance.Apheresis_Machine_Production_Capacity]
                        if t in self.PeriodsInGlobalMIPApheresisAssignment:
                            LeftHandSide_y= gp.quicksum(coeff_y[i] * self.ApheresisAssignment_Var_SDDP[vars_y[i]] for i in range(len(vars_y)))
                        else:
                            LeftHandSide_y = gp.quicksum(coeff_y[i] * self.ApheresisAssignment_Var_SDDP_EVPI[vars_y[i]] for i in range(len(vars_y)))


                        LeftHandSide = LeftHandSide_lambda + LeftHandSide_y

                        ########## RHS
                        RightHandSide = 0

                        # Add the constraint to the model
                        constraint_name = f"ACFApheresisCapacityConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_i_{i}_index_{self.LastAddedConstraintIndex}"
                        self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                        self.GurobiModel.update()
                        self.PIACFApheresisCapacityConstraint_Names.append(constraint_name) 
                        self.IndexPIACFApheresisCapacityConstraint.append(self.LastAddedConstraintIndex)
                        self.IndexPIACFApheresisCapacityConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                        self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                        self.ConcernedACFPIACFApheresisCapacityConstraint.append(i)
                        self.ConcernedTimePIACFApheresisCapacityConstraint.append(t) 
                        self.ConcernedScenarioPIACFApheresisCapacityConstraint.append(w)
    
    def CreatePIHospitalApheresisCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePIHospitalApheresisCapacityConstraint")

        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for h in self.Instance.HospitalSet: 
                        
                        ########## lambda
                        vars_lambda = [self.GetIndexPIPlateletApheresisExtractionVariable(c, h, t, wevpi, w) 
                                        for c in self.Instance.BloodGPSet]
                        coeff_lambda = [-1.0 
                                        for c in self.Instance.BloodGPSet]
                        if t in self.PeriodsInGlobalMIPPlateletApheresisExtraction:
                            LeftHandSide_lambda = gp.quicksum(coeff_lambda[i] * self.PlateletApheresisExtraction_Var_SDDP[vars_lambda[i]] for i in range(len(vars_lambda)))
                        else:
                            LeftHandSide_lambda = gp.quicksum(coeff_lambda[i] * self.PlateletApheresisExtraction_Var_SDDP_EVPI[vars_lambda[i]] for i in range(len(vars_lambda)))

                        LeftHandSide = LeftHandSide_lambda

                        ########## RHS
                        RightHandSide = -1.0 * self.Instance.Apheresis_Machine_Production_Capacity * self.Instance.Number_Apheresis_Machine_Hospital[h]

                        # Add the constraint to the model
                        constraint_name = f"HospitalApheresisCapacityConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_h_{h}_index_{self.LastAddedConstraintIndex}"
                        self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                        self.GurobiModel.update()
                        self.PIHospitalApheresisCapacityConstraint_Names.append(constraint_name) 
                        self.IndexPIHospitalApheresisCapacityConstraint.append(self.LastAddedConstraintIndex)
                        self.IndexPIHospitalApheresisCapacityConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                        self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                        self.ConcernedHospitalPIHospitalApheresisCapacityConstraint.append(h)
                        self.ConcernedTimePIHospitalApheresisCapacityConstraint.append(t) 
                        self.ConcernedScenarioPIHospitalApheresisCapacityConstraint.append(w)
    
    def CreatePIApheresisCapacityDonorsConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePIApheresisCapacityDonorsConstraint")

        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for c in self.Instance.BloodGPSet: 
                        for u in self.Instance.FacilitySet: 
                        
                            ########## lambda
                            vars_lambda = [self.GetIndexPIPlateletApheresisExtractionVariable(c, u, t, wevpi, w)]
                            coeff_lambda = [-1.0]
                            if t in self.PeriodsInGlobalMIPPlateletApheresisExtraction:
                                LeftHandSide_lambda = gp.quicksum(coeff_lambda[i] * self.PlateletApheresisExtraction_Var_SDDP[vars_lambda[i]] for i in range(len(vars_lambda)))
                            else:
                                LeftHandSide_lambda = gp.quicksum(coeff_lambda[i] * self.PlateletApheresisExtraction_Var_SDDP_EVPI[vars_lambda[i]] for i in range(len(vars_lambda)))

                            LeftHandSide = LeftHandSide_lambda

                            ########## RHS
                            RightHandSide = -1.0 * self.Instance.Platelet_Units_Apheresis * self.EVPIScenarioSet[wevpi].ApheresisDonors[t][c][u]

                            # Add the constraint to the model
                            constraint_name = f"ApheresisCapacityDonorsConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_c_{c}_u_{u}_index_{self.LastAddedConstraintIndex}"
                            self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                            self.GurobiModel.update()
                            self.PIApheresisCapacityDonorsConstraint_Names.append(constraint_name) 
                            self.IndexPIApheresisCapacityDonorsConstraint.append(self.LastAddedConstraintIndex)
                            self.IndexPIApheresisCapacityDonorsConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                            self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                            self.ConcernedBloodGPPIApheresisCapacityDonorsConstraint.append(c)
                            self.ConcernedFacilityPIApheresisCapacityDonorsConstraint.append(u)
                            self.ConcernedTimePIApheresisCapacityDonorsConstraint.append(t) 
                            self.ConcernedScenarioPIApheresisCapacityDonorsConstraint.append(w)
                            self.ConcernedEVPIScenarioPIApheresisCapacityDonorsConstraint.append(wevpi)
    
    def CreatePIWholeCapacityDonorsConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePIWholeCapacityDonorsConstraint")

        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for c in self.Instance.BloodGPSet: 
                        for h in self.Instance.HospitalSet: 
                        
                            ########## Rhovar
                            vars_Rhovar = [self.GetIndexPIPlateletWholeExtractionVariable(c, h, t, wevpi, w)]
                            coeff_Rhovar = [-1.0]
                            if t in self.PeriodsInGlobalMIPPlateletWholeExtraction:
                                LeftHandSide_Rhovar = gp.quicksum(coeff_Rhovar[i] * self.PlateletWholeExtraction_Var_SDDP[vars_Rhovar[i]] for i in range(len(vars_Rhovar)))
                            else:
                                LeftHandSide_Rhovar = gp.quicksum(coeff_Rhovar[i] * self.PlateletWholeExtraction_Var_SDDP_EVPI[vars_Rhovar[i]] for i in range(len(vars_Rhovar)))

                            LeftHandSide = LeftHandSide_Rhovar

                            ########## RHS
                            RightHandSide = -1.0 * self.EVPIScenarioSet[wevpi].WholeDonors[t][c][h]

                            # Add the constraint to the model
                            constraint_name = f"WholeCapacityDonorsConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_c_{c}_h_{h}_index_{self.LastAddedConstraintIndex}"
                            self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                            self.GurobiModel.update()
                            self.PIWholeCapacityDonorsConstraint_Names.append(constraint_name) 
                            self.IndexPIWholeCapacityDonorsConstraint.append(self.LastAddedConstraintIndex)
                            self.IndexPIWholeCapacityDonorsConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                            self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                            self.ConcernedBloodGPPIWholeCapacityDonorsConstraint.append(c)
                            self.ConcernedHospitalPIWholeCapacityDonorsConstraint.append(h)
                            self.ConcernedTimePIWholeCapacityDonorsConstraint.append(t) 
                            self.ConcernedScenarioPIWholeCapacityDonorsConstraint.append(w)
                            self.ConcernedEVPIScenarioPIWholeCapacityDonorsConstraint.append(wevpi)
    
    def CreatePINrApheresisLimitConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePINrApheresisLimitConstraint")

        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGoApheresisAssignment:  #We use "TimePeriodToGoApheresisAssignment" instead of "TimePeriodToGo", Because we already defined the same constraint for in the first stage!

                    ########## y 
                    vars_y = [self.GetIndexPIApheresisAssignmentVariable(i, t, wevpi, w) 
                              for i in self.Instance.ACFPPointSet]
                    coeff_y = [-1.0 
                               for i in self.Instance.ACFPPointSet]                    
                    if t in self.PeriodsInGlobalMIPApheresisAssignment:
                        LeftHandSide = gp.quicksum(coeff_y[i] * self.ApheresisAssignment_Var_SDDP[vars_y[i]] for i in range(len(vars_y)))
                    else:
                        LeftHandSide = gp.quicksum(coeff_y[i] * self.ApheresisAssignment_Var_SDDP_EVPI[vars_y[i]] for i in range(len(vars_y)))

                    # Define the right-hand side (RHS) of the constraint
                    RightHandSide = -1.0 * self.Instance.Total_Apheresis_Machine_ACF[t] 

                    # Add the constraint to the model
                    constraint_name = f"NrApheresisLimitConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_index_{self.LastAddedConstraintIndex}"
                    self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                    self.GurobiModel.update()
                    self.PINrApheresisLimitConstraint_Names.append(constraint_name)
                    self.IndexPINrApheresisLimitConstraint.append(self.LastAddedConstraintIndex)
                    self.IndexPINrApheresisLimitConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                    self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                    self.ConcernedTimePINrApheresisLimitConstraint.append(t) 
                    self.ConcernedScenarioPINrApheresisLimitConstraint.append(w)
    
    def CreatePIHospitalRescueVehicleCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePIHospitalRescueVehicleCapacityConstraint")

        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for h in self.Instance.HospitalSet:
                        for m in self.Instance.RescueVehicleSet:
                            
                            ################# q
                            vars_q = [self.GetIndexPIPatientTransferVariable(j, c, l, h, m, t, wevpi, w) 
                                        for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1
                                        for c in self.Instance.BloodGPSet
                                        for l in self.Instance.DemandSet]
                            coeff_q = [-1.0 * self.Instance.Distance_D_H[l][h] 
                                        for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1
                                        for c in self.Instance.BloodGPSet
                                        for l in self.Instance.DemandSet]    
                            if t in self.PeriodsInGlobalMIPPatientTransfer:
                                LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var_SDDP[vars_q[i]] for i in range(len(vars_q)))
                            else:
                                LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var_SDDP_EVPI[vars_q[i]] for i in range(len(vars_q)))

                            LeftHandSide = LeftHandSide_q

                            ################# RHS
                            RightHandSide = -1.0 * self.Instance.Rescue_Vehicle_Capacity[m] * self.Instance.Number_Rescue_Vehicle_Hospital[m][h]

                            # Add the constraint to the model
                            constraint_name = f"HospitalRescueVehicleCapacityConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_h_{h}_m_{m}_index_{self.LastAddedConstraintIndex}"
                            self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                            
                            self.GurobiModel.update()

                            self.PIHospitalRescueVehicleCapacityConstraint_Names.append(constraint_name)
                            self.IndexPIHospitalRescueVehicleCapacityConstraint.append(self.LastAddedConstraintIndex)
                            self.IndexPIHospitalRescueVehicleCapacityConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                            self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                            self.ConcernedHospitalPIHospitalRescueVehicleCapacityConstraint.append(h)
                            self.ConcernedVehiclePIHospitalRescueVehicleCapacityConstraint.append(m)
                            self.ConcernedTimePIHospitalRescueVehicleCapacityConstraint.append(t) 
                            self.ConcernedScenarioPIHospitalRescueVehicleCapacityConstraint.append(w)

    def GetPIFlowFromPreviousStage(self, d, t):
        result = self.SDDPOwner.GetVarTransFixedEarlier_ConsideringSumOnSuppliers(d, t, self.CurrentTrialNr)
        return result
    
    def GetPIFlowPLTInvTransHospitalFromPreviousStage(self, cprime, r, h, t):
        result = 0
        WholePLTProductionStartedTime = t - self.Instance.Whole_Blood_Production_Time
        #if WholePLTProductionStartedTime >= 0 and (WholePLTProductionStartedTime < self.TimeDecisionStage) and (r >= self.Instance.Whole_Blood_Production_Time):
        if WholePLTProductionStartedTime >= 0 and (r >= self.Instance.Whole_Blood_Production_Time):
            result = self.SDDPOwner.GetPIWholePLTProductionFixedEarlier(cprime, h, t, self.CurrentTrialNr)

        return result
    
    def GetFlowPLTInvTransHospitalFromPreviousStage(self, cprime, r, h, t):

        result = 0

        TransshipmenHHtStartedTime = self.GetTimePeriodAssociatedToPatientTransferVariable(t)        # Here, we are dealing with index (t-1)
        if TransshipmenHHtStartedTime >= 0 and (TransshipmenHHtStartedTime < self.TimeDecisionStage) and (r != 0):
            result = result + self.SDDPOwner.GetTransshipmentHHFixedEarlier_withSumOnHprime(cprime, r, h, TransshipmenHHtStartedTime, self.CurrentTrialNr)

        TransshipmenHItStartedTime = self.GetTimePeriodAssociatedToPatientTransferVariable(t)        # Here, we are dealing with index (t-1)
        if TransshipmenHItStartedTime >= 0 and (TransshipmenHItStartedTime < self.TimeDecisionStage) and (r != 0):
            result = result - self.SDDPOwner.GetTransshipmentHIFixedEarlier_withSumOnI(cprime, r, h, TransshipmenHItStartedTime, self.CurrentTrialNr)


        periodprevPLTinventory = self.GetTimePeriodAssociatedToPatientTransferVariable(t) - 1           # Here, we are dealing with index ((t-1)-1)
        if periodprevPLTinventory >= -1 and (periodprevPLTinventory < self.TimeObservationStage):
            result = result + self.SDDPOwner.GetHospitalPLTInventoryFixedEarlier(cprime, r, h, periodprevPLTinventory, self.CurrentTrialNr)

        WholePLTProductionStartedTime = self.GetTimePeriodAssociatedToPatientTransferVariable(t) - self.Instance.Whole_Blood_Production_Time    # Here, we deal with index ((t-1)-e)
        if WholePLTProductionStartedTime >= 0 and (WholePLTProductionStartedTime < self.TimeDecisionStage) and (r >= self.Instance.Whole_Blood_Production_Time):
            result = result + self.SDDPOwner.GetWholePLTProductionFixedEarlier(cprime, h, WholePLTProductionStartedTime, self.CurrentTrialNr)

        return result
    
    def GetFlowPLTInvTransACFFromPreviousStage(self, cprime, r, i, t):

        result = 0

        TransshipmenHItStartedTime = self.GetTimePeriodAssociatedToPatientTransferVariable(t)        # Here, we are dealing with index (t-1)
        if TransshipmenHItStartedTime >= 0 and (TransshipmenHItStartedTime < self.TimeDecisionStage) and (r != 0):
            result = result + self.SDDPOwner.GetTransshipmentHIFixedEarlier_withSumOnH(cprime, r, i, TransshipmenHItStartedTime, self.CurrentTrialNr)

        TransshipmenIItStartedTime = self.GetTimePeriodAssociatedToPatientTransferVariable(t)        # Here, we are dealing with index (t-1)
        if TransshipmenIItStartedTime >= 0 and (TransshipmenIItStartedTime < self.TimeDecisionStage) and (r != 0):
            result = result + self.SDDPOwner.GetTransshipmentIIFixedEarlier_withSumOnIprime(cprime, r, i, TransshipmenIItStartedTime, self.CurrentTrialNr)


        periodprevPLTinventory = self.GetTimePeriodAssociatedToPatientTransferVariable(t) - 1           # Here, we are dealing with index ((t-1)-1)
        if periodprevPLTinventory >= 0 and (periodprevPLTinventory < self.TimeObservationStage) and (r != 0):        # Note that here, we do not have initial inventory.
            result = result + self.SDDPOwner.GetACFPLTInventoryFixedEarlier(cprime, r, i, periodprevPLTinventory, self.CurrentTrialNr)

        return result
    
    def GetFlowApheresisAssignmentFromPreviousStage(self, i, t):

        result = 0

        ApheresisAssignmentTime = self.GetTimePeriodAssociatedToPatientTransferVariable(t)        # Here, we are dealing with index (t-1)
        if ApheresisAssignmentTime >= 0 and (ApheresisAssignmentTime < self.TimeDecisionStage):
            result = result + (self.Instance.Apheresis_Machine_Production_Capacity * self.SDDPOwner.GetApheresisAssignmentFixedEarlier(i, ApheresisAssignmentTime, self.CurrentTrialNr))

        return result
    
    def GetFlowUnsatisfiedPatientsFromPreviousStage(self, j, c, l, t):

        righthandside = 0

        periodprevunsatisfied = self.GetTimePeriodAssociatedToPatientTransferVariable(t) - 1    # Here, we are dealing with index (t-2)
        if periodprevunsatisfied >= 0 and (periodprevunsatisfied < self.TimeObservationStage):
            
            # Unsatisfied patients at period t - 2
            righthandside = righthandside + self.SDDPOwner.GetUnsatisfiedPatientFixedEarlier(j, c, l, periodprevunsatisfied, self.CurrentTrialNr)
            
        return righthandside
    
    def GetFlowUnservedPatientsFromPreviousStage(self, j, c, u, t):

        righthandside = 0

        periodprevunserved = self.GetTimePeriodAssociatedToPatientTransferVariable(t) - 1    # Here, we are dealing with index (t-2)
        if periodprevunserved >= 0 and (periodprevunserved < self.TimeObservationStage):
            
            # Unserved at period t - 2
            righthandside = righthandside + self.SDDPOwner.GetUnservedPatientFixedEarlier(j, c, u, periodprevunserved, self.CurrentTrialNr)
        
        return righthandside
    
    def GetFlowUnservedPatientCapFromPreviousStage(self, u, t):

        righthandside = 0

        periodprevunserved = self.GetTimePeriodAssociatedToPatientTransferVariable(t) - 1    # Here, we are dealing with index (t-2)
        if periodprevunserved >= 0 and (periodprevunserved < self.TimeObservationStage):
            
            # Unserved patients at period t - 2
            for j in self.Instance.InjuryLevelSet:
                if self.Instance.J_u[u][j] == 1:
                    for c in self.Instance.BloodGPSet:
                        righthandside = righthandside + self.SDDPOwner.GetUnservedPatientFixedEarlier(j, c, u, periodprevunserved, self.CurrentTrialNr)
        
        return righthandside
        
    def GetFlowFromPreviousStage(self, d, t):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- GetFlowFromPreviousStage")

        righthandside = 0

        VarTransStartedTime = self.GetTimePeriodAssociatedToShortageVariable(t)
        if VarTransStartedTime >= 0 and (VarTransStartedTime < self.TimeDecisionStage):
            
            righthandside = righthandside + self.SDDPOwner.GetVarTransFixedEarlier_ConsideringSumOnSuppliers(d, VarTransStartedTime, self.CurrentTrialNr)       
        
        periodprevinventory = self.GetTimePeriodAssociatedToInventoryVariable(t) - 1 
        
        if periodprevinventory >= -1 and (periodprevinventory < self.TimeObservationStage):
            
            # inventory at period t - 2
            righthandside = righthandside + self.SDDPOwner.GetInventoryFixedEarlier(d, periodprevinventory, self.CurrentTrialNr)
            
        return righthandside
    
    def CreateLowMedPriorityPatientFlowConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreateLowMedPriorityPatientFlowConstraint")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for j in self.Instance.InjuryLevelSet:
                    if j != 0:                         # Only for Low- and Med- Priority Patients
                        for c in self.Instance.BloodGPSet:
                            for l in self.Instance.DemandSet:

                                vars_q = [self.GetIndexPatientTransferVariable(j, c, l, u, m, t, w)
                                          for u in self.Instance.FacilitySet 
                                          for m in self.Instance.RescueVehicleSet]
                                coeff_q = [1.0  
                                          for u in self.Instance.FacilitySet 
                                          for m in self.Instance.RescueVehicleSet]
                                
                                vars_mu = [self.GetIndexUnsatisfiedPatientsVariable(j, c, l, t, w)]
                                coeff_mu = [+1.0]                  
                                
                                vars_prev = [self.GetIndexFlowUnsatisfiedLowMedPatientsFromPreviousStage(j, c, l, t)]
                                coeff_prev = [-1.0]
                                    
                                ############ Create the left-hand side of the constraint
                                LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var_SDDP[vars_q[i]] for i in range(len(vars_q)))
                                LeftHandSide_mu = gp.quicksum(coeff_mu[i] * self.UnsatisfiedPatients_Var_SDDP[vars_mu[i]] for i in range(len(vars_mu)))
                                LeftHandSide_prev = gp.quicksum(coeff_prev[i] * self.flowUnsatisfiedLowMedPatientsFromPreviousStage_SDDP[vars_prev[i]] for i in range(len(vars_prev))) if vars_prev else 0
                                
                                LeftHandSide = LeftHandSide_q + LeftHandSide_mu + LeftHandSide_prev
                                
                                ############ Define the right-hand side (RHS) of the constraint
                                RightHandSide = self.GetPatientFlowConstraintRHS(j, c, l, t, w, self.IsForward)
                                
                                ############ Add the constraint to the model
                                constraint_name = f"LowMedPriorityPatientFlowConstraint_w_{w}_t_{self.TimeDecisionStage+t}_j_{j}_c_{c}_l_{l}_index_{self.LastAddedConstraintIndex}"

                                constraint_obj = self.GurobiModel.addConstr(LeftHandSide == RightHandSide, name=constraint_name)
                                self.LowMedPriorityPatientFlowConstraint_Objects.append(constraint_obj)         #This line of code make updating constraint in later stages easier
                                
                                #if Constants.Debug: print(f"Added constraint: {constraint_name}")

                                self.GurobiModel.update()
                                self.LowMedPriorityPatientFlowConstraint_Names.append(constraint_name)


                                self.IndexLowMedPriorityPatientFlowConstraint.append(self.LastAddedConstraintIndex)
                                self.IndexLowMedPriorityPatientFlowConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                                self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                                self.ConcernedDemandLowMedPriorityPatientFlowConstraint.append(l)
                                self.ConcernedBloodGPLowMedPriorityPatientFlowConstraint.append(c)
                                self.ConcernedInjuryLowMedPriorityPatientFlowConstraint.append(j)
                                self.ConcernedScenarioLowMedPriorityPatientFlowConstraint.append(w)
                                self.ConcernedTimeLowMedPriorityPatientFlowConstraint.append(self.GetTimePeriodAssociatedToPatientTransferVariable(t))     
    
    def CreateHighPriorityPatientFlowConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreateHighPriorityPatientFlowConstraint")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for j in self.Instance.InjuryLevelSet:
                    if j == 0:                         # Only for High-Priority Patients
                        for c in self.Instance.BloodGPSet:
                            for l in self.Instance.DemandSet:

                                vars_q = [self.GetIndexPatientTransferVariable(j, c, l, h, m, t, w)
                                          for h in self.Instance.HospitalSet 
                                          for m in self.Instance.RescueVehicleSet]
                                coeff_q = [1.0  
                                          for h in self.Instance.HospitalSet 
                                          for m in self.Instance.RescueVehicleSet]
                                
                                vars_mu = [self.GetIndexUnsatisfiedPatientsVariable(j, c, l, t, w)]
                                coeff_mu = [1.0]                  
                                
                                vars_prev = [self.GetIndexFlowUnsatisfiedHighPatientsFromPreviousStage(j, c, l, t)]
                                coeff_prev = [-1.0]
                                                                        
                                ############ Create the left-hand side of the constraint
                                LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var_SDDP[vars_q[i]] for i in range(len(vars_q)))                                
                                LeftHandSide_mu = gp.quicksum(coeff_mu[i] * self.UnsatisfiedPatients_Var_SDDP[vars_mu[i]] for i in range(len(vars_mu)))                                
                                LeftHandSide_prev = gp.quicksum(coeff_prev[i] * self.flowUnsatisfiedHighPatientsFromPreviousStage_SDDP[vars_prev[i]] for i in range(len(vars_prev))) if vars_prev else 0
                                
                                LeftHandSide = LeftHandSide_q + LeftHandSide_mu + LeftHandSide_prev
                                
                                ############ Define the right-hand side (RHS) of the constraint
                                RightHandSide = self.GetPatientFlowConstraintRHS(j, c, l, t, w, self.IsForward)
                                
                                ############ Add the constraint to the model
                                constraint_name = f"HighPriorityPatientFlowConstraint_w_{w}_t_{self.TimeDecisionStage+t}_j_{j}_c_{c}_l_{l}_index_{self.LastAddedConstraintIndex}"

                                constraint_obj = self.GurobiModel.addConstr(LeftHandSide == RightHandSide, name=constraint_name)
                                self.HighPriorityPatientFlowConstraint_Objects.append(constraint_obj)         #This line of code make updating constraint in later stages easier
                                
                                #if Constants.Debug: print(f"Added constraint: {constraint_name}")

                                self.GurobiModel.update()
                                self.HighPriorityPatientFlowConstraint_Names.append(constraint_name)


                                self.IndexHighPriorityPatientFlowConstraint.append(self.LastAddedConstraintIndex)
                                self.IndexHighPriorityPatientFlowConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                                self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                                self.ConcernedDemandHighPriorityPatientFlowConstraint.append(l)
                                self.ConcernedBloodGPHighPriorityPatientFlowConstraint.append(c)
                                self.ConcernedInjuryHighPriorityPatientFlowConstraint.append(j)
                                self.ConcernedScenarioHighPriorityPatientFlowConstraint.append(w)
                                self.ConcernedTimeHighPriorityPatientFlowConstraint.append(self.GetTimePeriodAssociatedToPatientTransferVariable(t))     
            
    def CreateLowMedPriorityPatientServiceConstraint (self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreateLowMedPriorityPatientServiceConstraint ")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for j in self.Instance.InjuryLevelSet:
                    if j != 0:                         # Only for Low- and Med-Priority Patients
                        for c in self.Instance.BloodGPSet:
                            for u in self.Instance.FacilitySet:

                                vars_upsilon = [self.GetIndexServedPatientVariable(j, cprime, c, r, u, t, w)
                                                for cprime in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime] == 1
                                                for r in self.Instance.PlateletAgeSet if self.Instance.R_j[r][j] == 1]
                                coeff_upsilon = [1.0  
                                                for cprime in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime] == 1
                                                for r in self.Instance.PlateletAgeSet if self.Instance.R_j[r][j] == 1]
                                
                                vars_zeta = [self.GetIndexPatientPostponementVariable(j, c, u, t, w)]
                                coeff_zeta = [1.0]
                                
                                vars_q = [self.GetIndexPatientTransferVariable(j, c, l, u, m, t, w)
                                            for l in self.Instance.DemandSet
                                            for m in self.Instance.RescueVehicleSet]
                                coeff_q = [-1.0  
                                            for l in self.Instance.DemandSet
                                            for m in self.Instance.RescueVehicleSet]                  
                                
                                vars_prev = [self.GetIndexFlowUnservedLowMedPatientsFromPreviousStage(j, c, u, t)]
                                coeff_prev = [-1.0]              
                                    
                                ############ Create the left-hand side of the constraint
                                LeftHandSide_upsilon = gp.quicksum(coeff_upsilon[i] * self.ServedPatient_Var_SDDP[vars_upsilon[i]] for i in range(len(vars_upsilon)))
                                LeftHandSide_zeta = gp.quicksum(coeff_zeta[i] * self.PatientPostponement_Var_SDDP[vars_zeta[i]] for i in range(len(vars_zeta)))
                                LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var_SDDP[vars_q[i]] for i in range(len(vars_q)))
                                LeftHandSide_prev = gp.quicksum(coeff_prev[i] * self.flowUnservedLowMedPatientsFromPreviousStage_SDDP[vars_prev[i]] for i in range(len(vars_prev))) if vars_prev else 0
                                
                                LeftHandSide = LeftHandSide_upsilon + LeftHandSide_zeta + LeftHandSide_q + LeftHandSide_prev
                                
                                ############ Define the right-hand side (RHS) of the constraint
                                RightHandSide = 0
                                
                                ############ Add the constraint to the model
                                constraint_name = f"LowMedPriorityPatientServiceConstraint_w_{w}_t_{self.TimeDecisionStage+t}_j_{j}_c_{c}_u_{u}_index_{self.LastAddedConstraintIndex}"

                                self.GurobiModel.addConstr(LeftHandSide == RightHandSide, name=constraint_name)
                                
                                #if Constants.Debug: print(f"Added constraint: {constraint_name}")

                                self.GurobiModel.update()
                                self.LowMedPriorityPatientServiceConstraint_Names.append(constraint_name)

                                self.IndexLowMedPriorityPatientServiceConstraint.append(self.LastAddedConstraintIndex)
                                self.IndexLowMedPriorityPatientServiceConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                                self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                                self.ConcernedFacilityLowMedPriorityPatientServiceConstraint.append(u)
                                self.ConcernedBloodGPLowMedPriorityPatientServiceConstraint.append(c)
                                self.ConcernedInjuryLowMedPriorityPatientServiceConstraint.append(j)
                                self.ConcernedScenarioLowMedPriorityPatientServiceConstraint.append(w)
                                self.ConcernedTimeLowMedPriorityPatientServiceConstraint.append(self.GetTimePeriodAssociatedToPatientTransferVariable(t))     
            
    def CreateHighPriorityPatientServiceConstraint (self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreateHighPriorityPatientServiceConstraint ")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for j in self.Instance.InjuryLevelSet:
                    if j == 0:                         # Only for High-Priority Patients
                        for c in self.Instance.BloodGPSet:
                            for h in self.Instance.HospitalSet:

                                vars_upsilon = [self.GetIndexServedPatientVariable(j, cprime, c, r, h, t, w)
                                                for cprime in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime] == 1
                                                for r in self.Instance.PlateletAgeSet if self.Instance.R_j[r][j] == 1]
                                coeff_upsilon = [1.0  
                                                for cprime in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime] == 1
                                                for r in self.Instance.PlateletAgeSet if self.Instance.R_j[r][j] == 1]
                                
                                vars_zeta = [self.GetIndexPatientPostponementVariable(j, c, h, t, w)]
                                coeff_zeta = [1.0]
                                
                                vars_q = [self.GetIndexPatientTransferVariable(j, c, l, h, m, t, w)
                                            for l in self.Instance.DemandSet
                                            for m in self.Instance.RescueVehicleSet]
                                coeff_q = [-1.0  
                                            for l in self.Instance.DemandSet
                                            for m in self.Instance.RescueVehicleSet]

                                vars_prev = [self.GetIndexFlowUnservedHighPatientsFromPreviousStage(j, c, h, t)]
                                coeff_prev = [-1.0]
                                    
                                ############ Create the left-hand side of the constraint
                                LeftHandSide_upsilon = gp.quicksum(coeff_upsilon[i] * self.ServedPatient_Var_SDDP[vars_upsilon[i]] for i in range(len(vars_upsilon)))
                                LeftHandSide_zeta = gp.quicksum(coeff_zeta[i] * self.PatientPostponement_Var_SDDP[vars_zeta[i]] for i in range(len(vars_zeta)))
                                LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var_SDDP[vars_q[i]] for i in range(len(vars_q)))
                                LeftHandSide_prev = gp.quicksum(coeff_prev[i] * self.flowUnservedHighPatientsFromPreviousStage_SDDP[vars_prev[i]] for i in range(len(vars_prev))) if vars_prev else 0

                                LeftHandSide = LeftHandSide_upsilon + LeftHandSide_zeta + LeftHandSide_q + LeftHandSide_prev
                                
                                ############ Define the right-hand side (RHS) of the constraint
                                RightHandSide = 0
                                
                                ############ Add the constraint to the model
                                constraint_name = f"HighPriorityPatientServiceConstraint_w_{w}_t_{self.TimeDecisionStage+t}_j_{j}_c_{c}_h_{h}_index_{self.LastAddedConstraintIndex}"

                                self.GurobiModel.addConstr(LeftHandSide == RightHandSide, name=constraint_name)
                                
                                #if Constants.Debug: print(f"Added constraint: {constraint_name}")

                                self.GurobiModel.update()
                                self.HighPriorityPatientServiceConstraint_Names.append(constraint_name)

                                self.IndexHighPriorityPatientServiceConstraint.append(self.LastAddedConstraintIndex)
                                self.IndexHighPriorityPatientServiceConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                                self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                                self.ConcernedHospitalHighPriorityPatientServiceConstraint.append(h)
                                self.ConcernedBloodGPHighPriorityPatientServiceConstraint.append(c)
                                self.ConcernedInjuryHighPriorityPatientServiceConstraint.append(j)
                                self.ConcernedScenarioHighPriorityPatientServiceConstraint.append(w)
                                self.ConcernedTimeHighPriorityPatientServiceConstraint.append(self.GetTimePeriodAssociatedToPatientTransferVariable(t))     
            
    def CreateHospitalPlateletFlowConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreateHospitalPlateletFlowConstraint")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for cprime in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:                            
                            
                            vars_lambda = []
                            coeff_lambda = []
                            if r == 0:
                                vars_lambda = [self.GetIndexPlateletApheresisExtractionVariable(cprime, h, t, w)]
                                coeff_lambda = [1.0]

                            vars_prev = [self.GetIndexFlowPLTInvTransHospitalFromPreviousStage(cprime, r, h, t)]
                            coeff_prev = [1.0]

                            vars_upsilon = [self.GetIndexServedPatientVariable(j, cprime, c, r, h, t, w) 
                                            for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1 and self.Instance.J_r[j][r] == 1 
                                            for c in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime]==1]
                            coeff_upsilon = [-1.0 * self.Instance.Platelet_Units_Required_for_Injury[j] 
                                            for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1 and self.Instance.J_r[j][r] == 1 
                                            for c in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime]==1]                

                            vars_eta = [self.GetIndexPlateletInventoryVariable(cprime, r, h, t, w)]
                            coeff_eta = [-1.0] 
                                
                                
                            ############ Create the left-hand side of the constraint
                            LeftHandSide_lambda = gp.quicksum(coeff_lambda[i] * self.PlateletApheresisExtraction_Var_SDDP[vars_lambda[i]] for i in range(len(vars_lambda))) if vars_lambda else 0

                            LeftHandSide_prev = gp.quicksum(coeff_prev[i] * self.flowPLTInvTransHospitalFromPreviousStage_SDDP[vars_prev[i]] for i in range(len(vars_prev)))

                            LeftHandSide_upsilon = gp.quicksum(coeff_upsilon[i] * self.ServedPatient_Var_SDDP[vars_upsilon[i]] for i in range(len(vars_upsilon)))

                            LeftHandSide_eta = gp.quicksum(coeff_eta[i] * self.PlateletInventory_Var_SDDP[vars_eta[i]] for i in range(len(vars_eta)))

                            LeftHandSide = LeftHandSide_prev + LeftHandSide_lambda + LeftHandSide_upsilon + LeftHandSide_eta

                            ############ Define the right-hand side (RHS) of the constraint
                            RightHandSide = 0
                            
                            ############ Add the constraint to the model
                            constraint_name = f"HospitalPlateletFlow_w_{w}_t_{self.TimeDecisionStage+t}_c'_{cprime}_r_{r}_h_{h}_index_{self.LastAddedConstraintIndex}"

                            self.GurobiModel.addConstr(LeftHandSide == RightHandSide, name=constraint_name)
                            
                            #if Constants.Debug: print(f"Added constraint: {constraint_name}")

                            self.GurobiModel.update()
                            self.HospitalPlateletFlowConstraint_Names.append(constraint_name)

                            self.IndexHospitalPlateletFlowConstraint.append(self.LastAddedConstraintIndex)
                            self.IndexHospitalPlateletFlowConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                            self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                            self.ConcernedHospitalHospitalPlateletFlowConstraint.append(h)
                            self.ConcernedPLTAgeHospitalPlateletFlowConstraint.append(r)
                            self.ConcernedBloodGPHospitalPlateletFlowConstraint.append(cprime)
                            self.ConcernedScenarioHospitalPlateletFlowConstraint.append(w)
                            self.ConcernedTimeHospitalPlateletFlowConstraint.append(self.GetTimePeriodAssociatedToPatientTransferVariable(t))     
    
    def CreateACFPlateletFlowConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreateACFPlateletFlowConstraint")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for cprime in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for i in self.Instance.ACFPPointSet:                            
                            
                            acf = self.Instance.NrHospitals + i
                            vars_lambda = []
                            coeff_lambda = []
                            if r == 0:
                                vars_lambda = [self.GetIndexPlateletApheresisExtractionVariable(cprime, acf, t, w)]
                                coeff_lambda = [1.0]

                            vars_prev = [self.GetIndexFlowPLTInvTransACFFromPreviousStage(cprime, r, i, t)]
                            coeff_prev = [1.0]

                            vars_upsilon = [self.GetIndexServedPatientVariable(j, cprime, c, r, acf, t, w) 
                                            for j in self.Instance.InjuryLevelSet if self.Instance.J_u[acf][j] == 1 and self.Instance.J_r[j][r] == 1 
                                            for c in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime]==1]
                            coeff_upsilon = [-1.0 * self.Instance.Platelet_Units_Required_for_Injury[j] 
                                            for j in self.Instance.InjuryLevelSet if self.Instance.J_u[acf][j] == 1 and self.Instance.J_r[j][r] == 1 
                                            for c in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime]==1]               

                            vars_eta = [self.GetIndexPlateletInventoryVariable(cprime, r, acf, t, w)]
                            coeff_eta = [-1.0] 
                                

                            ############ Create the left-hand side of the constraint
                            LeftHandSide_lambda = gp.quicksum(coeff_lambda[i] * self.PlateletApheresisExtraction_Var_SDDP[vars_lambda[i]] for i in range(len(vars_lambda))) if vars_lambda else 0

                            LeftHandSide_prev = gp.quicksum(coeff_prev[i] * self.flowPLTInvTransACFFromPreviousStage_SDDP[vars_prev[i]] for i in range(len(vars_prev))) if vars_prev else 0

                            LeftHandSide_upsilon = gp.quicksum(coeff_upsilon[i] * self.ServedPatient_Var_SDDP[vars_upsilon[i]] for i in range(len(vars_upsilon)))

                            LeftHandSide_eta = gp.quicksum(coeff_eta[i] * self.PlateletInventory_Var_SDDP[vars_eta[i]] for i in range(len(vars_eta))) 

                            LeftHandSide = LeftHandSide_prev + LeftHandSide_lambda + LeftHandSide_upsilon + LeftHandSide_eta

                            ############ Define the right-hand side (RHS) of the constraint
                            RightHandSide = 0
                            
                            ############ Add the constraint to the model
                            constraint_name = f"ACFPlateletFlowConstraint_w_{w}_t_{self.TimeDecisionStage+t}_c'_{cprime}_r_{r}_i_{i}_index_{self.LastAddedConstraintIndex}"

                            self.GurobiModel.addConstr(LeftHandSide == RightHandSide, name=constraint_name)
                            
                            #if Constants.Debug: print(f"Added constraint: {constraint_name}")

                            self.GurobiModel.update()
                            self.ACFPlateletFlowConstraint_Names.append(constraint_name)

                            self.IndexACFPlateletFlowConstraint.append(self.LastAddedConstraintIndex)
                            self.IndexACFPlateletFlowConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                            self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                            self.ConcernedACFACFPlateletFlowConstraint.append(i)
                            self.ConcernedPLTAgeACFPlateletFlowConstraint.append(r)
                            self.ConcernedBloodGPACFPlateletFlowConstraint.append(cprime)
                            self.ConcernedScenarioACFPlateletFlowConstraint.append(w)
                            self.ConcernedTimeACFPlateletFlowConstraint.append(self.GetTimePeriodAssociatedToPatientTransferVariable(t))     
    
    def CreatePlateletWastageConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePlateletWastageConstraint")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for u in self.Instance.FacilitySet:

                    vars_sigmavar = [self.GetIndexOutdatedPlateletVariable(u, t, w)]
                    coeff_sigmavar = [1.0]

                    r_last = list(self.Instance.PlateletAgeSet)[-1]
                    vars_eta = [self.GetIndexPlateletInventoryVariable(c, r_last, u, t, w)
                                    for c in self.Instance.BloodGPSet]
                    coeff_eta = [-1.0
                                    for c in self.Instance.BloodGPSet]
                          
                    ############ Create the left-hand side of the constraint
                    LeftHandSide_sigmavar = gp.quicksum(coeff_sigmavar[i] * self.OutdatedPlatelet_Var_SDDP[vars_sigmavar[i]] for i in range(len(vars_sigmavar)))
                    LeftHandSide_eta = gp.quicksum(coeff_eta[i] * self.PlateletInventory_Var_SDDP[vars_eta[i]] for i in range(len(vars_eta)))
                    
                    LeftHandSide = LeftHandSide_sigmavar + LeftHandSide_eta
                    
                    ############ Define the right-hand side (RHS) of the constraint
                    RightHandSide = 0
                    
                    ############ Add the constraint to the model
                    constraint_name = f"PlateletWastageConstraint_w_{w}_t_{self.TimeDecisionStage+t}_u_{u}_index_{self.LastAddedConstraintIndex}"

                    self.GurobiModel.addConstr(LeftHandSide == RightHandSide, name=constraint_name)
                    
                    #if Constants.Debug: print(f"Added constraint: {constraint_name}")

                    self.GurobiModel.update()
                    self.PlateletWastageConstraint_Names.append(constraint_name)

                    self.IndexPlateletWastageConstraint.append(self.LastAddedConstraintIndex)
                    self.IndexPlateletWastageConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                    self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                    self.ConcernedFacilityPlateletWastageConstraint.append(u)
                    self.ConcernedScenarioPlateletWastageConstraint.append(w)
                    self.ConcernedTimePlateletWastageConstraint.append(self.GetTimePeriodAssociatedToPatientTransferVariable(t))     
    
    def CreateHospitalRescueVehicleCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreateHospitalRescueVehicleCapacityConstraint")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for h in self.Instance.HospitalSet:
                    for m in self.Instance.RescueVehicleSet:

                        vars_q = [self.GetIndexPatientTransferVariable(j, c, l, h, m, t, w)
                                    for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1
                                    for c in self.Instance.BloodGPSet
                                    for l in self.Instance.DemandSet]
                        
                        coeff_q = [-1.0 * self.Instance.Distance_D_H[l][h] 
                                    for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1
                                    for c in self.Instance.BloodGPSet
                                    for l in self.Instance.DemandSet]    
                            
                        ############ Create the left-hand side of the constraint
                        LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var_SDDP[vars_q[i]] for i in range(len(vars_q)))
                        
                        LeftHandSide = LeftHandSide_q
                        
                        ############ Define the right-hand side (RHS) of the constraint
                        RightHandSide = -1.0 * self.Instance.Rescue_Vehicle_Capacity[m] * self.Instance.Number_Rescue_Vehicle_Hospital[m][h]  
                        
                        ############ Add the constraint to the model
                        constraint_name = f"HospitalRescueVehicleCapacityConstraint_w_{w}_t_{self.TimeDecisionStage+t}_h_{h}_m_{m}_index_{self.LastAddedConstraintIndex}"

                        self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                        
                        #if Constants.Debug: print(f"Added constraint: {constraint_name}")

                        self.GurobiModel.update()
                        self.HospitalRescueVehicleCapacityConstraint_Names.append(constraint_name)

                        self.IndexHospitalRescueVehicleCapacityConstraint.append(self.LastAddedConstraintIndex)
                        self.IndexHospitalRescueVehicleCapacityConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                        self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                        self.ConcernedVehicleHospitalRescueVehicleCapacityConstraint.append(m)
                        self.ConcernedHospitalHospitalRescueVehicleCapacityConstraint.append(h)
                        self.ConcernedScenarioHospitalRescueVehicleCapacityConstraint.append(w)
                        self.ConcernedTimeHospitalRescueVehicleCapacityConstraint.append(self.GetTimePeriodAssociatedToPatientTransferVariable(t))     
    
    def CreateACFRescueVehicleCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreateACFRescueVehicleCapacityConstraint")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for i in self.Instance.ACFPPointSet:
                    for m in self.Instance.RescueVehicleSet:
                        
                        acf = self.Instance.NrHospitals + i
                        vars_q = [self.GetIndexPatientTransferVariable(j, c, l, acf, m, t, w)
                                    for j in self.Instance.InjuryLevelSet if self.Instance.J_u[acf][j] == 1
                                    for c in self.Instance.BloodGPSet
                                    for l in self.Instance.DemandSet]
                        
                        coeff_q = [-1.0 * self.Instance.Distance_D_A[l][i] 
                                    for j in self.Instance.InjuryLevelSet if self.Instance.J_u[acf][j] == 1
                                    for c in self.Instance.BloodGPSet
                                    for l in self.Instance.DemandSet] 

                        vars_thetavar = [self.GetIndexVehicleAssignmentRHS_ACFRescVehCapCons(m, i)]
                        coeff_thetavar = [1.0]

                        ############ Create the left-hand side of the constraint
                        LeftHandSide_q = gp.quicksum(coeff_q[i] * self.PatientTransfer_Var_SDDP[vars_q[i]] for i in range(len(vars_q)))
                        LeftHandSide_thetavar = gp.quicksum(coeff_thetavar[i] * self.ACFRescVehicCapRHS_SDDP[vars_thetavar[i]] for i in range(len(vars_thetavar)))
                        
                        LeftHandSide = LeftHandSide_q + LeftHandSide_thetavar
                        
                        ############ Define the right-hand side (RHS) of the constraint
                        RightHandSide = 0  
                        
                        ############ Add the constraint to the model
                        constraint_name = f"ACFRescueVehicleCapacityConstraint_w_{w}_t_{self.TimeDecisionStage+t}_i_{i}_m_{m}_index_{self.LastAddedConstraintIndex}"

                        self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                        
                        #if Constants.Debug: print(f"Added constraint: {constraint_name}")

                        self.GurobiModel.update()
                        self.ACFRescueVehicleCapacityConstraint_Names.append(constraint_name)

                        self.IndexACFRescueVehicleCapacityConstraint.append(self.LastAddedConstraintIndex)
                        self.IndexACFRescueVehicleCapacityConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                        self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                        self.ConcernedVehicleACFRescueVehicleCapacityConstraint.append(m)
                        self.ConcernedACFACFRescueVehicleCapacityConstraint.append(i)
                        self.ConcernedScenarioACFRescueVehicleCapacityConstraint.append(w)
                        self.ConcernedTimeACFRescueVehicleCapacityConstraint.append(self.GetTimePeriodAssociatedToPatientTransferVariable(t))     
    
    def CreateACFApheresisCapacityConstraint (self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreateACFApheresisCapacityConstraint")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for i in self.Instance.ACFPPointSet:
                    acf = self.Instance.NrHospitals + i
                    vars_lambda = [self.GetIndexPlateletApheresisExtractionVariable(c, acf, t, w)
                                   for c in self.Instance.BloodGPSet]
                    
                    coeff_lambda = [-1.0
                                    for c in self.Instance.BloodGPSet] 

                    vars_prev = [self.GetIndexFlowApheresisAssignmentFromPreviousStage(i, t)]
                    coeff_prev = [1.0]

                    ############ Create the left-hand side of the constraint
                    LeftHandSide_q = gp.quicksum(coeff_lambda[i] * self.PlateletApheresisExtraction_Var_SDDP[vars_lambda[i]] for i in range(len(vars_lambda)))
                    LeftHandSide_prev = gp.quicksum(coeff_prev[i] * self.flowApheresisAssignmentFromPreviousStage_SDDP[vars_prev[i]] for i in range(len(vars_prev)))
                    
                    LeftHandSide = LeftHandSide_q + LeftHandSide_prev
                    
                    ############ Define the right-hand side (RHS) of the constraint
                    RightHandSide = 0  
                    
                    ############ Add the constraint to the model
                    constraint_name = f"ACFApheresisCapacityConstraint_w_{w}_t_{self.TimeDecisionStage+t}_i_{i}_index_{self.LastAddedConstraintIndex}"

                    self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                    
                    #if Constants.Debug: print(f"Added constraint: {constraint_name}")

                    self.GurobiModel.update()
                    self.ACFApheresisCapacityConstraint_Names.append(constraint_name)

                    self.IndexACFApheresisCapacityConstraint.append(self.LastAddedConstraintIndex)
                    self.IndexACFApheresisCapacityConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                    self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                    self.ConcernedACFACFApheresisCapacityConstraint.append(i)
                    self.ConcernedScenarioACFApheresisCapacityConstraint.append(w)
                    self.ConcernedTimeACFApheresisCapacityConstraint.append(self.GetTimePeriodAssociatedToPatientTransferVariable(t))     
    
    def CreateHospitalApheresisCapacityConstraint (self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreateHospitalApheresisCapacityConstraint")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for h in self.Instance.HospitalSet:
                        
                    vars_lambda = [self.GetIndexPlateletApheresisExtractionVariable(c, h, t, w)
                                   for c in self.Instance.BloodGPSet]
                    
                    coeff_lambda = [-1.0
                                    for c in self.Instance.BloodGPSet]                                                                                                   

                    ############ Create the left-hand side of the constraint       
                    LeftHandSide_lambda = gp.quicksum(coeff_lambda[i] * self.PlateletApheresisExtraction_Var_SDDP[vars_lambda[i]] for i in range(len(vars_lambda)))
                                                                                
                    LeftHandSide = LeftHandSide_lambda
                    
                    ############ Define the right-hand side (RHS) of the constraint
                    RightHandSide = -1.0 * self.Instance.Apheresis_Machine_Production_Capacity * self.Instance.Number_Apheresis_Machine_Hospital[h]
                    
                    
                    ############ Add the constraint to the model
                    constraint_name = f"HospitalApheresisCapacityConstraint_w_{w}_t_{self.TimeDecisionStage+t}_h_{h}_index_{self.LastAddedConstraintIndex}"

                    self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                    
                    #if Constants.Debug: print(f"Added constraint: {constraint_name}")

                    self.GurobiModel.update()
                    self.HospitalApheresisCapacityConstraint_Names.append(constraint_name)

                    self.IndexHospitalApheresisCapacityConstraint.append(self.LastAddedConstraintIndex)
                    self.IndexHospitalApheresisCapacityConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                    self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                    self.ConcernedHospitalHospitalApheresisCapacityConstraint.append(h)
                    self.ConcernedScenarioHospitalApheresisCapacityConstraint.append(w)
                    self.ConcernedTimeHospitalApheresisCapacityConstraint.append(self.GetTimePeriodAssociatedToPatientTransferVariable(t))     
    
    def CreateApheresisCapacityDonorsConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (CreateApheresisCapacityDonorsConstraint)")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for c in self.Instance.BloodGPSet:
                    for u in self.Instance.FacilitySet:
                        
                        vars_lambda = [self.GetIndexPlateletApheresisExtractionVariable(c, u, t, w)]
                        
                        coeff_lambda = [-1.0]                                                                                                   

                        ############ Create the left-hand side of the constraint       
                        LeftHandSide_lambda = gp.quicksum(coeff_lambda[i] * self.PlateletApheresisExtraction_Var_SDDP[vars_lambda[i]] for i in range(len(vars_lambda)))
                                                                                    
                        LeftHandSide = LeftHandSide_lambda

                        ############ Define the right-hand side (RHS) of the constraint
                        RightHandSide = -1.0 * self.Instance.Platelet_Units_Apheresis * self.GetApheresisCapacityDonorsConstraintRHS(c, u, t, w, self.IsForward)                         

                        ############ Add the constraint to the model
                        constraint_name = f"ApheresisCapacityDonorsConstraint_w_{w}_t_{self.TimeDecisionStage+t}_c_{c}_u_{u}_index_{self.LastAddedConstraintIndex}"
                        constraint_obj = self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                        self.ApheresisCapacityDonorsConstraint_Objects.append(constraint_obj)         #This line of code make updating constraint in later stages easier

                        self.ApheresisCapacityDonorsConstraint_Names.append(constraint_name)

                        #if Constants.Debug: print(f"Added constraint: {constraint_name}")
                        
                        self.GurobiModel.update()
                        self.IndexApheresisCapacityDonorsConstraint.append(self.LastAddedConstraintIndex)
                        self.IndexApheresisCapacityDonorsConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                        self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                        self.ConcernedFacilityApheresisCapacityDonorsConstraint.append(u)
                        self.ConcernedBloodGPApheresisCapacityDonorsConstraint.append(c)
                        self.ConcernedScenarioApheresisCapacityDonorsConstraint.append(w)        
                        self.ConcernedTimeApheresisCapacityDonorsConstraint.append(self.GetTimePeriodAssociatedToPatientTransferVariable(t))
    
    def CreateWholeCapacityDonorsConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (CreateWholeCapacityDonorsConstraint)")

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for c in self.Instance.BloodGPSet:
                    for h in self.Instance.HospitalSet:
                        
                        vars_Rhovar = [self.GetIndexPlateletWholeExtractionVariable(c, h, t, w)]
                        
                        coeff_Rhovar = [-1.0]                                                                                                   

                        ############ Create the left-hand side of the constraint       
                        LeftHandSide_Rhovar = gp.quicksum(coeff_Rhovar[i] * self.PlateletWholeExtraction_Var_SDDP[vars_Rhovar[i]] for i in range(len(vars_Rhovar)))
                                                                                    
                        LeftHandSide = LeftHandSide_Rhovar
                        ############ Define the right-hand side (RHS) of the constraint
                        RightHandSide = -1.0 * self.GetWholeCapacityDonorsConstraintRHS(c, h, t, w, self.IsForward)                         

                        ############ Add the constraint to the model
                        constraint_name = f"WholeCapacityDonorsConstraint_w_{w}_t_{self.TimeDecisionStage+t}_c_{c}_h_{h}_index_{self.LastAddedConstraintIndex}"
                        constraint_obj = self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)
                        self.WholeCapacityDonorsConstraint_Objects.append(constraint_obj)         #This line of code make updating constraint in later stages easier

                        self.WholeCapacityDonorsConstraint_Names.append(constraint_name)

                        #if Constants.Debug: print(f"Added constraint: {constraint_name}")
                        
                        self.GurobiModel.update()
                        self.IndexWholeCapacityDonorsConstraint.append(self.LastAddedConstraintIndex)
                        self.IndexWholeCapacityDonorsConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                        self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                        self.ConcernedHospitalWholeCapacityDonorsConstraint.append(h)
                        self.ConcernedBloodGPWholeCapacityDonorsConstraint.append(c)
                        self.ConcernedScenarioWholeCapacityDonorsConstraint.append(w)        
                        self.ConcernedTimeWholeCapacityDonorsConstraint.append(self.GetTimePeriodAssociatedToPatientTransferVariable(t))

    def CreatePIHospitalTransshipmentCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePIHospitalTransshipmentCapacityConstraint")

        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGoApheresisAssignment:  #We use "TimePeriodToGoApheresisAssignment" instead of "TimePeriodToGo", Because we already defined the same constraint for in the first stage!
                    for c in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            if r != 0:
                                for h in self.Instance.HospitalSet:
                                    LeftHandSide_b = gp.LinExpr()  
                                    LeftHandSide_bDoublePrime = gp.LinExpr()  
                                    LeftHandSide_eta = gp.LinExpr()  

                                    ###################
                                    if t == 0:
                                        RightHandSide = -1.0 * self.Instance.Initial_Platelet_Inventory[c][r][h]
                                    else:
                                        RightHandSide = 0

                                    ################### b
                                    b_index = [self.GetIndexPITransshipmentHIVariable(c, r, h, i, t, wevpi, w) 
                                               for i in self.Instance.ACFPPointSet]
                                    if t in self.PeriodsInGlobalMIPTransshipmentHI:
                                        b_var = [self.TransshipmentHI_Var_SDDP[b_index[i]] for i in range(len(b_index))]
                                    else:
                                        b_var = [self.TransshipmentHI_Var_SDDP_EVPI[b_index[i]] for i in range(len(b_index))]
                                    b_coeff = [-1.0 for i in range(len(b_index))]
                                    LeftHandSide_b.addTerms(b_coeff, b_var)

                                    #####################
                                    bDoublePrime_index = [self.GetIndexPITransshipmentHHVariable(c, r, h, hprime, t, wevpi, w) 
                                                            for hprime in self.Instance.HospitalSet if hprime != h]
                                    if t in self.PeriodsInGlobalMIPTransshipmentHH:
                                        bDoublePrime_var = [self.TransshipmentHH_Var_SDDP[bDoublePrime_index[i]] for i in range(len(bDoublePrime_index))]
                                    else:
                                        bDoublePrime_var = [self.TransshipmentHH_Var_SDDP_EVPI[bDoublePrime_index[i]] for i in range(len(bDoublePrime_index))]
                                    bDoublePrime_coeff = [-1.0 for i in range(len(bDoublePrime_index))]
                                    LeftHandSide_bDoublePrime.addTerms(bDoublePrime_coeff, bDoublePrime_var)

                                    ######################
                                    if t > 0:
                                        eta_index = [self.GetIndexPIPlateletInventoryVariable(c, (r-1), h, (t-1), wevpi, w)]
                                        if (t-1) in self.PeriodsInGlobalMIPPlateletInventory:
                                            eta_var = [self.PlateletInventory_Var_SDDP[eta_index[i]] for i in range(len(eta_index))]
                                        else:
                                            eta_var = [self.PlateletInventory_Var_SDDP_EVPI[eta_index[i]] for i in range(len(eta_index))]
                                        eta_coeff = [1.0 for i in range(len(eta_index))]
                                        LeftHandSide_eta.addTerms(eta_coeff, eta_var)                            

                                    # Add constraint to Gurobi model
                                    LeftHandSide = LeftHandSide_b + LeftHandSide_bDoublePrime + LeftHandSide_eta

                                    constraint_name = f"HospitalTransshipmentCapacityConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_c_{c}_r_{r}_h_{h}_index_{self.LastAddedConstraintIndex}"
                                    self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                                    self.GurobiModel.update()
                                    self.PIHospitalTransshipmentCapacityConstraint_Names.append(constraint_name)
                                    self.IndexPIHospitalTransshipmentCapacityConstraint.append(self.LastAddedConstraintIndex)
                                    self.IndexPIHospitalTransshipmentCapacityConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                                    self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                                    self.ConcernedBloodGPPIHospitalTransshipmentCapacityConstraint.append(c)
                                    self.ConcernedPLTAgePIHospitalTransshipmentCapacityConstraint.append(r)
                                    self.ConcernedHospitalPIHospitalTransshipmentCapacityConstraint.append(h)
                                    self.ConcernedTimePIHospitalTransshipmentCapacityConstraint.append(t)
                                    self.ConcernedScenarioPIHospitalTransshipmentCapacityConstraint.append(w)
    
    def CreatePIACFTransshipmentCapacityConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePIACFTransshipmentCapacityConstraint")

        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGoApheresisAssignment:  #We use "TimePeriodToGoApheresisAssignment" instead of "TimePeriodToGo", Because we already defined the same constraint for in the first stage!
                    for c in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            if r != 0:
                                for i in self.Instance.ACFPPointSet:
                                    LeftHandSide_bPrime = gp.LinExpr()  
                                    LeftHandSide_eta = gp.LinExpr()  

                                    ################### RHS
                                    RightHandSide = 0

                                    ################### b
                                    bPrime_index = [self.GetIndexPITransshipmentIIVariable(c, r, i, iprime, t, wevpi, w) 
                                                    for iprime in self.Instance.ACFPPointSet if iprime != i]
                                    if t in self.PeriodsInGlobalMIPTransshipmentII:
                                        bPrime_var = [self.TransshipmentII_Var_SDDP[bPrime_index[i]] for i in range(len(bPrime_index))]
                                    else:
                                        bPrime_var = [self.TransshipmentII_Var_SDDP_EVPI[bPrime_index[i]] for i in range(len(bPrime_index))]
                                    bPrime_coeff = [-1.0 for i in range(len(bPrime_index))]
                                    LeftHandSide_bPrime.addTerms(bPrime_coeff, bPrime_var)

                                    ######################
                                    acf = (self.Instance.NrHospitals + i)
                                    if t > 0:
                                        eta_index = [self.GetIndexPIPlateletInventoryVariable(c, (r-1), acf, (t-1), wevpi, w)]
                                        if (t-1) in self.PeriodsInGlobalMIPPlateletInventory:
                                            eta_var = [self.PlateletInventory_Var_SDDP[eta_index[i]] for i in range(len(eta_index))]
                                        else:
                                            eta_var = [self.PlateletInventory_Var_SDDP_EVPI[eta_index[i]] for i in range(len(eta_index))]
                                        eta_coeff = [1.0 for i in range(len(eta_index))]
                                        LeftHandSide_eta.addTerms(eta_coeff, eta_var)                            

                                    # Add constraint to Gurobi model
                                    LeftHandSide = LeftHandSide_bPrime + LeftHandSide_eta

                                    constraint_name = f"ACFTransshipmentCapacityConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_c_{c}_r_{r}_i_{i}_index_{self.LastAddedConstraintIndex}"
                                    self.GurobiModel.addConstr(LeftHandSide >= RightHandSide, name=constraint_name)

                                    self.GurobiModel.update()
                                    self.PIACFTransshipmentCapacityConstraint_Names.append(constraint_name)
                                    self.IndexPIACFTransshipmentCapacityConstraint.append(self.LastAddedConstraintIndex)
                                    self.IndexPIACFTransshipmentCapacityConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                                    self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                                    self.ConcernedBloodGPPIACFTransshipmentCapacityConstraint.append(c)
                                    self.ConcernedPLTAgePIACFTransshipmentCapacityConstraint.append(r)
                                    self.ConcernedACFPIACFTransshipmentCapacityConstraint.append(i)
                                    self.ConcernedTimePIACFTransshipmentCapacityConstraint.append(t)
                                    self.ConcernedScenarioPIACFTransshipmentCapacityConstraint.append(w)
    
    def CreatePIHospitalPlateletFlowConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePIHospitalPlateletFlowConstraint")

        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for cprime in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for h in self.Instance.HospitalSet:
                                LeftHandSide_lambda = gp.LinExpr()  
                                LeftHandSide_prev_eta = gp.LinExpr()  
                                LeftHandSide_bDoublePrime = gp.LinExpr()  
                                LeftHandSide_bDoublePrime_rev = gp.LinExpr()  
                                LeftHandSide_b = gp.LinExpr()  
                                LeftHandSide_Rhovar = gp.LinExpr()  
                                LeftHandSide_upsilon = gp.LinExpr()  
                                LeftHandSide_eta = gp.LinExpr()  

                                ########### RHS
                                if t == 0:
                                    RightHandSide = -1.0 * self.Instance.Initial_Platelet_Inventory[cprime][r][h]
                                else:
                                    RightHandSide = 0

                                ########### lambda
                                if r == 0:
                                    lambda_index = [self.GetIndexPIPlateletApheresisExtractionVariable(cprime, h, t, wevpi, w)]
                                    if t in self.PeriodsInGlobalMIPPlateletApheresisExtraction:
                                        lambda_var = [self.PlateletApheresisExtraction_Var_SDDP[lambda_index[i]] for i in range(len(lambda_index))]
                                    else:
                                        lambda_var = [self.PlateletApheresisExtraction_Var_SDDP_EVPI[lambda_index[i]] for i in range(len(lambda_index))]
                                    lambda_coeff = [1.0 for i in range(len(lambda_index))]
                                    LeftHandSide_lambda.addTerms(lambda_coeff, lambda_var)

                                ########### Previous PLT Inventory
                                if t != 0:
                                    if r != 0:
                                        prev_eta_index = [self.GetIndexPIPlateletInventoryVariable(cprime, (r-1), h, (t-1), wevpi, w)]
                                        if (t-1) in self.PeriodsInGlobalMIPPlateletInventory:
                                            prev_eta_var = [self.PlateletInventory_Var_SDDP[prev_eta_index[i]] for i in range(len(prev_eta_index))]
                                        else:
                                            prev_eta_var = [self.PlateletInventory_Var_SDDP_EVPI[prev_eta_index[i]] for i in range(len(prev_eta_index))]
                                        prev_eta_coeff = [1.0 for i in range(len(prev_eta_index))]
                                        LeftHandSide_prev_eta.addTerms(prev_eta_coeff, prev_eta_var)

                                ########### b'' and b
                                if r != 0:
                                    ########### b''
                                    bDoublePrime_index = [self.GetIndexPITransshipmentHHVariable(cprime, r, hprime, h, t, wevpi, w)
                                                            for hprime in self.Instance.HospitalSet  if hprime != h]
                                    if t in self.PeriodsInGlobalMIPTransshipmentHH:
                                        bDoublePrime_var = [self.TransshipmentHH_Var_SDDP[bDoublePrime_index[i]] for i in range(len(bDoublePrime_index))]
                                    else:
                                        bDoublePrime_var = [self.TransshipmentHH_Var_SDDP_EVPI[bDoublePrime_index[i]] for i in range(len(bDoublePrime_index))]
                                    bDoublePrime_coeff = [1.0 for i in range(len(bDoublePrime_index))]
                                    LeftHandSide_bDoublePrime.addTerms(bDoublePrime_coeff, bDoublePrime_var)

                                    ########### b'' Reverse
                                    bDoublePrime_rev_index = [self.GetIndexPITransshipmentHHVariable(cprime, r, h, hprime, t, wevpi, w)
                                                                for hprime in self.Instance.HospitalSet  if hprime != h]
                                    if t in self.PeriodsInGlobalMIPTransshipmentHH:
                                        bDoublePrime_rev_var = [self.TransshipmentHH_Var_SDDP[bDoublePrime_rev_index[i]] for i in range(len(bDoublePrime_rev_index))]
                                    else:
                                        bDoublePrime_rev_var = [self.TransshipmentHH_Var_SDDP_EVPI[bDoublePrime_rev_index[i]] for i in range(len(bDoublePrime_rev_index))]
                                    bDoublePrime_rev_coeff = [-1.0 for i in range(len(bDoublePrime_rev_index))]
                                    LeftHandSide_bDoublePrime_rev.addTerms(bDoublePrime_rev_coeff, bDoublePrime_rev_var)

                                    ########### b
                                    b_index = [self.GetIndexPITransshipmentHIVariable(cprime, r, h, i, t, wevpi, w)
                                                            for i in self.Instance.ACFPPointSet]
                                    if t in self.PeriodsInGlobalMIPTransshipmentHI:
                                        b_var = [self.TransshipmentHI_Var_SDDP[b_index[i]] for i in range(len(b_index))]
                                    else:
                                        b_var = [self.TransshipmentHI_Var_SDDP_EVPI[b_index[i]] for i in range(len(b_index))]
                                    b_coeff = [-1.0 for i in range(len(b_index))]
                                    LeftHandSide_b.addTerms(b_coeff, b_var)
                                
                                ########### Rhovar
                                if r >= self.Instance.Whole_Blood_Production_Time:
                                    periodWholeproduction = t - self.Instance.Whole_Blood_Production_Time
                                    if periodWholeproduction >= self.GetTimePeriodAssociatedToPatientTransferVariable(0) and periodWholeproduction >= 0:
                                        Rhovar_index = [self.GetIndexPIPlateletWholeExtractionVariable(cprime, h, periodWholeproduction, wevpi, w)]
                                        if periodWholeproduction in self.PeriodsInGlobalMIPPlateletWholeExtraction:
                                            Rhovar_var = [self.PlateletWholeExtraction_Var_SDDP[Rhovar_index[i]] for i in range(len(Rhovar_index))]
                                        else:
                                            Rhovar_var = [self.PlateletWholeExtraction_Var_SDDP_EVPI[Rhovar_index[i]] for i in range(len(Rhovar_index))]
                                        Rhovar_coeff = [1.0 for i in range(len(Rhovar_index))]
                                        LeftHandSide_Rhovar.addTerms(Rhovar_coeff, Rhovar_var)
                                    elif periodWholeproduction >= 0:
                                        flowvar_index = self.GetIndexPIFlowPrevQty(p, periodproduction)
                                        flowvar = [self.flowfromprevioustage_SDDP[flowvar_index]]
                                        flowcoeff = [1.0]

                                ########### upsilon
                                upsilon_index = [self.GetIndexPIServedPatientVariable(j, cprime, c, r, h, t, wevpi, w)
                                                    for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1 and self.Instance.J_r[j][r] == 1 
                                                    for c in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime]==1]
                                if t in self.PeriodsInGlobalMIPServedPatient:
                                    upsilon_var = [self.ServedPatient_Var_SDDP[upsilon_index[i]] for i in range(len(upsilon_index))] 
                                else:
                                    upsilon_var = [self.ServedPatient_Var_SDDP_EVPI[upsilon_index[i]] for i in range(len(upsilon_index))]                            
                                upsilon_coeff = [-1.0 * self.Instance.Platelet_Units_Required_for_Injury[j] 
                                                for j in self.Instance.InjuryLevelSet if self.Instance.J_u[h][j] == 1 and self.Instance.J_r[j][r] == 1 
                                                for c in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime]==1]
                                LeftHandSide_upsilon.addTerms(upsilon_coeff, upsilon_var)

                                ########### eta
                                eta_index = [self.GetIndexPIPlateletInventoryVariable(cprime, r, h, t, wevpi, w)]
                                if t in self.PeriodsInGlobalMIPPlateletInventory:
                                    eta_var = [self.PlateletInventory_Var_SDDP[eta_index[i]] for i in range(len(eta_index))]
                                else:
                                    eta_var = [self.PlateletInventory_Var_SDDP_EVPI[eta_index[i]] for i in range(len(eta_index))]
                                eta_coeff = [-1.0 for i in range(len(eta_index))]
                                LeftHandSide_eta.addTerms(eta_coeff, eta_var)

                                # Add constraint to Gurobi model
                                LeftHandSide = LeftHandSide_lambda + LeftHandSide_prev_eta + LeftHandSide_bDoublePrime + LeftHandSide_bDoublePrime_rev \
                                                + LeftHandSide_b + LeftHandSide_Rhovar + LeftHandSide_upsilon + LeftHandSide_eta

                                constraint_name = f"HospitalPlateletFlowConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_c'_{cprime}_r_{r}_h_{h}_index_{self.LastAddedConstraintIndex}"
                                self.GurobiModel.addConstr(LeftHandSide == RightHandSide, name=constraint_name)

                                self.GurobiModel.update()
                                self.PIHospitalPlateletFlowConstraint_Names.append(constraint_name)
                                self.IndexPIHospitalPlateletFlowConstraint.append(self.LastAddedConstraintIndex)
                                self.IndexPIHospitalPlateletFlowConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                                self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                                
                                self.ConcernedBloodGPPIHospitalPlateletFlowConstraint.append(cprime)
                                self.ConcernedPLTAgePIHospitalPlateletFlowConstraint.append(r)
                                self.ConcernedHospitalPIHospitalPlateletFlowConstraint.append(h)
                                self.ConcernedTimePIHospitalPlateletFlowConstraint.append(t)
                                self.ConcernedScenarioPIHospitalPlateletFlowConstraint.append(w)

    def CreatePIACFPlateletFlowConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePIACFPlateletFlowConstraint")

        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for cprime in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for i in self.Instance.ACFPPointSet:
                                LeftHandSide_lambda = gp.LinExpr()  
                                LeftHandSide_prev_eta = gp.LinExpr()
                                LeftHandSide_b = gp.LinExpr()  
                                LeftHandSide_bPrime = gp.LinExpr()  
                                LeftHandSide_bPrime_rev = gp.LinExpr()  
                                LeftHandSide_upsilon = gp.LinExpr()  
                                LeftHandSide_eta = gp.LinExpr()  

                                acf = self.Instance.NrHospitals + i
                                ########### RHS
                                RightHandSide = 0

                                ########### lambda
                                if r == 0:
                                    lambda_index = [self.GetIndexPIPlateletApheresisExtractionVariable(cprime, acf, t, wevpi, w)]
                                    if t in self.PeriodsInGlobalMIPPlateletApheresisExtraction:
                                        lambda_var = [self.PlateletApheresisExtraction_Var_SDDP[lambda_index[i]] for i in range(len(lambda_index))]
                                    else:
                                        lambda_var = [self.PlateletApheresisExtraction_Var_SDDP_EVPI[lambda_index[i]] for i in range(len(lambda_index))]
                                    lambda_coeff = [1.0 for i in range(len(lambda_index))]
                                    LeftHandSide_lambda.addTerms(lambda_coeff, lambda_var)

                                ########### Previous PLT Inventory
                                if t != 0:
                                    if r != 0:
                                        prev_eta_index = [self.GetIndexPIPlateletInventoryVariable(cprime, (r-1), acf, (t-1), wevpi, w)]
                                        if (t-1) in self.PeriodsInGlobalMIPPlateletInventory:
                                            prev_eta_var = [self.PlateletInventory_Var_SDDP[prev_eta_index[i]] for i in range(len(prev_eta_index))]
                                        else:
                                            prev_eta_var = [self.PlateletInventory_Var_SDDP_EVPI[prev_eta_index[i]] for i in range(len(prev_eta_index))]
                                        prev_eta_coeff = [1.0 for i in range(len(prev_eta_index))]
                                        LeftHandSide_prev_eta.addTerms(prev_eta_coeff, prev_eta_var)

                                ########### b'' and b
                                if r != 0:
                                    ########### b
                                    b_index = [self.GetIndexPITransshipmentHIVariable(cprime, r, h, i, t, wevpi, w)
                                                            for h in self.Instance.HospitalSet]
                                    if t in self.PeriodsInGlobalMIPTransshipmentHI:
                                        b_var = [self.TransshipmentHI_Var_SDDP[b_index[i]] for i in range(len(b_index))]
                                    else:
                                        b_var = [self.TransshipmentHI_Var_SDDP_EVPI[b_index[i]] for i in range(len(b_index))]
                                    b_coeff = [+1.0 for i in range(len(b_index))]
                                    LeftHandSide_b.addTerms(b_coeff, b_var)
                                                                            
                                    ########### b'
                                    bPrime_index = [self.GetIndexPITransshipmentIIVariable(cprime, r, iprime, i, t, wevpi, w)
                                                            for iprime in self.Instance.ACFPPointSet  if iprime != i]
                                    if t in self.PeriodsInGlobalMIPTransshipmentII:
                                        bPrime_var = [self.TransshipmentII_Var_SDDP[bPrime_index[i]] for i in range(len(bPrime_index))]
                                    else:
                                        bPrime_var = [self.TransshipmentII_Var_SDDP_EVPI[bPrime_index[i]] for i in range(len(bPrime_index))]
                                    bPrime_coeff = [1.0 for i in range(len(bPrime_index))]
                                    LeftHandSide_bPrime.addTerms(bPrime_coeff, bPrime_var)

                                    ########### b' Reverse
                                    bPrime_rev_index = [self.GetIndexPITransshipmentIIVariable(cprime, r, i, iprime, t, wevpi, w)
                                                                for iprime in self.Instance.ACFPPointSet  if iprime != i]
                                    if t in self.PeriodsInGlobalMIPTransshipmentII:
                                        bPrime_rev_var = [self.TransshipmentII_Var_SDDP[bPrime_rev_index[i]] for i in range(len(bPrime_rev_index))]
                                    else:
                                        bPrime_rev_var = [self.TransshipmentII_Var_SDDP_EVPI[bPrime_rev_index[i]] for i in range(len(bPrime_rev_index))]
                                    bPrime_rev_coeff = [-1.0 for i in range(len(bPrime_rev_index))]
                                    LeftHandSide_bPrime_rev.addTerms(bPrime_rev_coeff, bPrime_rev_var)

                                ########### upsilon
                                upsilon_index = [self.GetIndexPIServedPatientVariable(j, cprime, c, r, acf, t, wevpi, w)
                                                    for j in self.Instance.InjuryLevelSet if self.Instance.J_u[acf][j] == 1 and self.Instance.J_r[j][r] == 1 
                                                    for c in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime]==1]
                                if t in self.PeriodsInGlobalMIPServedPatient:
                                    upsilon_var = [self.ServedPatient_Var_SDDP[upsilon_index[i]] for i in range(len(upsilon_index))] 
                                else:
                                    upsilon_var = [self.ServedPatient_Var_SDDP_EVPI[upsilon_index[i]] for i in range(len(upsilon_index))]                            
                                upsilon_coeff = [-1.0 * self.Instance.Platelet_Units_Required_for_Injury[j] 
                                                for j in self.Instance.InjuryLevelSet if self.Instance.J_u[acf][j] == 1 and self.Instance.J_r[j][r] == 1 
                                                for c in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime]==1]
                                LeftHandSide_upsilon.addTerms(upsilon_coeff, upsilon_var)

                                ########### eta
                                eta_index = [self.GetIndexPIPlateletInventoryVariable(cprime, r, acf, t, wevpi, w)]
                                if t in self.PeriodsInGlobalMIPPlateletInventory:
                                    eta_var = [self.PlateletInventory_Var_SDDP[eta_index[i]] for i in range(len(eta_index))]
                                else:
                                    eta_var = [self.PlateletInventory_Var_SDDP_EVPI[eta_index[i]] for i in range(len(eta_index))]
                                eta_coeff = [-1.0 for i in range(len(eta_index))]
                                LeftHandSide_eta.addTerms(eta_coeff, eta_var)

                                # Add constraint to Gurobi model
                                LeftHandSide = LeftHandSide_lambda + LeftHandSide_prev_eta + LeftHandSide_bPrime + LeftHandSide_bPrime_rev \
                                                + LeftHandSide_b + LeftHandSide_upsilon + LeftHandSide_eta

                                constraint_name = f"ACFPlateletFlowConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_c'_{cprime}_r_{r}_i_{i}_index_{self.LastAddedConstraintIndex}"
                                self.GurobiModel.addConstr(LeftHandSide == RightHandSide, name=constraint_name)

                                self.GurobiModel.update()
                                self.PIACFPlateletFlowConstraint_Names.append(constraint_name)
                                self.IndexPIACFPlateletFlowConstraint.append(self.LastAddedConstraintIndex)
                                self.IndexPIACFPlateletFlowConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                                self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                                self.ConcernedBloodGPPIACFPlateletFlowConstraint.append(cprime)
                                self.ConcernedPLTAgePIACFPlateletFlowConstraint.append(r)
                                self.ConcernedACFPIACFPlateletFlowConstraint.append(i)
                                self.ConcernedTimePIACFPlateletFlowConstraint.append(t)
                                self.ConcernedScenarioPIACFPlateletFlowConstraint.append(w)
    
    def CreatePILowMedPriorityPatientServiceConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePILowMedPriorityPatientServiceConstraint")

        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for j in self.Instance.InjuryLevelSet:
                        if j != 0:
                            for c in self.Instance.BloodGPSet:
                                for u in self.Instance.FacilitySet:
                                    LeftHandSide_upsilon = gp.LinExpr()  
                                    LeftHandSide_zeta = gp.LinExpr()  
                                    LeftHandSide_q = gp.LinExpr()  
                                    LeftHandSide_prev_zeta = gp.LinExpr()  

                                    ############# RHS
                                    RightHandSide = 0

                                    ############# upsilon 
                                    upsilon_index = [self.GetIndexPIServedPatientVariable(j, cprime, c, r, u, t, wevpi, w) 
                                                        for cprime in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime] == 1
                                                        for r in self.Instance.PlateletAgeSet if self.Instance.R_j[r][j] == 1]
                                    if t in self.PeriodsInGlobalMIPServedPatient:
                                        upsilon_var = [self.ServedPatient_Var_SDDP[upsilon_index[i]] for i in range(len(upsilon_index))]
                                    else:
                                        upsilon_var = [self.ServedPatient_Var_SDDP_EVPI[upsilon_index[i]] for i in range(len(upsilon_index))]
                                    upsilon_coeff = [1.0 for i in range(len(upsilon_index))]
                                    LeftHandSide_upsilon.addTerms(upsilon_coeff, upsilon_var)

                                    ############# zeta
                                    zeta_index = [self.GetIndexPIPatientPostponementVariable(j, c, u, t, wevpi, w)]
                                    if t in self.PeriodsInGlobalMIPPatientPostponement:
                                        zeta_var = [self.PatientPostponement_Var_SDDP[zeta_index[i]] for i in range(len(zeta_index))] 
                                    else:
                                        zeta_var = [self.PatientPostponement_Var_SDDP_EVPI[zeta_index[i]] for i in range(len(zeta_index))]                            
                                    zeta_coeff = [1.0 for i in range(len(zeta_index))]
                                    LeftHandSide_zeta.addTerms(zeta_coeff, zeta_var)

                                    ############# q 
                                    q_index = [self.GetIndexPIPatientTransferVariable(j, c, l, u, m, t, wevpi, w)
                                                for l in self.Instance.DemandSet
                                                for m in self.Instance.RescueVehicleSet]
                                    if t in self.PeriodsInGlobalMIPPatientTransfer:
                                        q_var = [self.PatientTransfer_Var_SDDP[q_index[i]] for i in range(len(q_index))]
                                    else:
                                        q_var = [self.PatientTransfer_Var_SDDP_EVPI[q_index[i]] for i in range(len(q_index))]
                                    q_coeff = [-1.0 for i in range(len(q_index))]
                                    LeftHandSide_q.addTerms(q_coeff, q_var)
                                    
                                    ############# Previous zeta 
                                    if t > 0:
                                        prev_zeta_index = [self.GetIndexPIPatientPostponementVariable(j, c, u, (t-1), wevpi, w)]
                                        if (t-1) in self.PeriodsInGlobalMIPPatientPostponement:
                                            prev_zeta_var = [self.PatientPostponement_Var_SDDP[prev_zeta_index[i]] for i in range(len(prev_zeta_index))]
                                        else:
                                            prev_zeta_var = [self.PatientPostponement_Var_SDDP_EVPI[prev_zeta_index[i]] for i in range(len(prev_zeta_index))]
                                        prev_zeta_coeff = [-1.0 for i in range(len(prev_zeta_index))]
                                        LeftHandSide_prev_zeta.addTerms(prev_zeta_coeff, prev_zeta_var)

                                    # Add constraint to Gurobi model
                                    LeftHandSide = LeftHandSide_upsilon + LeftHandSide_zeta + LeftHandSide_q + LeftHandSide_prev_zeta

                                    constraint_name = f"LowMedPriorityPatientServiceConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_j_{j}_c_{c}_u_{u}_index_{self.LastAddedConstraintIndex}"
                                    self.GurobiModel.addConstr(LeftHandSide == RightHandSide, name=constraint_name)

                                    self.GurobiModel.update()
                                    self.PILowMedPriorityPatientServiceConstraint_Names.append(constraint_name)
                                    self.IndexPILowMedPriorityPatientServiceConstraint.append(self.LastAddedConstraintIndex)
                                    self.IndexPILowMedPriorityPatientServiceConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                                    self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                                    self.ConcernedInjuryPILowMedPriorityPatientServiceConstraint.append(j)
                                    self.ConcernedBloodGPPILowMedPriorityPatientServiceConstraint.append(c)
                                    self.ConcernedFacilityPILowMedPriorityPatientServiceConstraint.append(u)
                                    self.ConcernedTimePILowMedPriorityPatientServiceConstraint.append(t)        
                                    self.ConcernedScenarioPILowMedPriorityPatientServiceConstraint.append(w)
    
    def CreatePIPlateletWastageConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePIPlateletWastageConstraint")

        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for u in self.Instance.FacilitySet:
                        
                        LeftHandSide_sigmavar = gp.LinExpr()  
                        LeftHandSide_eta = gp.LinExpr()  

                        ############# RHS
                        RightHandSide = 0

                        ############# sigmavar 
                        sigmavar_index = [self.GetIndexPIOutdatedPlateletVariable(u, t, wevpi, w)]
                        if t in self.PeriodsInGlobalMIPOutdatedPlatelet:
                            sigmavar_var = [self.OutdatedPlatelet_Var_SDDP[sigmavar_index[i]] for i in range(len(sigmavar_index))]
                        else:
                            sigmavar_var = [self.OutdatedPlatelet_Var_SDDP_EVPI[sigmavar_index[i]] for i in range(len(sigmavar_index))]
                        sigmavar_coeff = [1.0 for i in range(len(sigmavar_index))]
                        LeftHandSide_sigmavar.addTerms(sigmavar_coeff, sigmavar_var)

                        ############# eta
                        r_last = list(self.Instance.PlateletAgeSet)[-1]
                        eta_index = [self.GetIndexPIPlateletInventoryVariable(c, r_last, u, t, wevpi, w)
                                    for c in self.Instance.BloodGPSet]   
                        if t in self.PeriodsInGlobalMIPPlateletInventory:
                            eta_var = [self.PlateletInventory_Var_SDDP[eta_index[i]] for i in range(len(eta_index))] 
                        else:
                            eta_var = [self.PlateletInventory_Var_SDDP_EVPI[eta_index[i]] for i in range(len(eta_index))]   
                        eta_coeff = [-1.0 for i in range(len(eta_index))]
                        LeftHandSide_eta.addTerms(eta_coeff, eta_var)

                        # Add constraint to Gurobi model
                        LeftHandSide = LeftHandSide_sigmavar + LeftHandSide_eta

                        constraint_name = f"PlateletWastageConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_u_{u}_index_{self.LastAddedConstraintIndex}"
                        self.GurobiModel.addConstr(LeftHandSide == RightHandSide, name=constraint_name)

                        self.GurobiModel.update()
                        self.PIPlateletWastageConstraint_Names.append(constraint_name)
                        self.IndexPIPlateletWastageConstraint.append(self.LastAddedConstraintIndex)
                        self.IndexPIPlateletWastageConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                        self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                        self.ConcernedFacilityPIPlateletWastageConstraint.append(u)
                        self.ConcernedTimePIPlateletWastageConstraint.append(t)        
                        self.ConcernedScenarioPIPlateletWastageConstraint.append(w)
    
    def CreatePIHighPriorityPatientServiceConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePIHighPriorityPatientServiceConstraint")

        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for j in self.Instance.InjuryLevelSet:
                        if j == 0:
                            for c in self.Instance.BloodGPSet:
                                for h in self.Instance.HospitalSet:
                                    LeftHandSide_upsilon = gp.LinExpr()  
                                    LeftHandSide_zeta = gp.LinExpr()  
                                    LeftHandSide_q = gp.LinExpr()  
                                    LeftHandSide_prev_zeta = gp.LinExpr()  

                                    ############# RHS
                                    RightHandSide = 0

                                    ############# upsilon 
                                    upsilon_index = [self.GetIndexPIServedPatientVariable(j, cprime, c, r, h, t, wevpi, w) 
                                                        for cprime in self.Instance.BloodGPSet if self.Instance.G_c[c][cprime] == 1
                                                        for r in self.Instance.PlateletAgeSet if self.Instance.R_j[r][j] == 1]
                                    if t in self.PeriodsInGlobalMIPServedPatient:
                                        upsilon_var = [self.ServedPatient_Var_SDDP[upsilon_index[i]] for i in range(len(upsilon_index))]
                                    else:
                                        upsilon_var = [self.ServedPatient_Var_SDDP_EVPI[upsilon_index[i]] for i in range(len(upsilon_index))]
                                    upsilon_coeff = [1.0 for i in range(len(upsilon_index))]
                                    LeftHandSide_upsilon.addTerms(upsilon_coeff, upsilon_var)

                                    ############# zeta
                                    zeta_index = [self.GetIndexPIPatientPostponementVariable(j, c, h, t, wevpi, w)]
                                    if t in self.PeriodsInGlobalMIPPatientPostponement:
                                        zeta_var = [self.PatientPostponement_Var_SDDP[zeta_index[i]] for i in range(len(zeta_index))] 
                                    else:
                                        zeta_var = [self.PatientPostponement_Var_SDDP_EVPI[zeta_index[i]] for i in range(len(zeta_index))]                            
                                    zeta_coeff = [1.0 for i in range(len(zeta_index))]
                                    LeftHandSide_zeta.addTerms(zeta_coeff, zeta_var)

                                    ############# q 
                                    q_index = [self.GetIndexPIPatientTransferVariable(j, c, l, h, m, t, wevpi, w)
                                                for l in self.Instance.DemandSet
                                                for m in self.Instance.RescueVehicleSet]
                                    if t in self.PeriodsInGlobalMIPPatientTransfer:
                                        q_var = [self.PatientTransfer_Var_SDDP[q_index[i]] for i in range(len(q_index))]
                                    else:
                                        q_var = [self.PatientTransfer_Var_SDDP_EVPI[q_index[i]] for i in range(len(q_index))]
                                    q_coeff = [-1.0 for i in range(len(q_index))]
                                    LeftHandSide_q.addTerms(q_coeff, q_var)
                                    
                                    ############# Previous zeta 
                                    if t > 0:
                                        prev_zeta_index = [self.GetIndexPIPatientPostponementVariable(j, c, h, t-1, wevpi, w)]
                                        if (t-1) in self.PeriodsInGlobalMIPPatientPostponement:
                                            prev_zeta_var = [self.PatientPostponement_Var_SDDP[prev_zeta_index[i]] for i in range(len(prev_zeta_index))]
                                        else:
                                            prev_zeta_var = [self.PatientPostponement_Var_SDDP_EVPI[prev_zeta_index[i]] for i in range(len(prev_zeta_index))]
                                        prev_zeta_coeff = [-1.0 for i in range(len(prev_zeta_index))]
                                        LeftHandSide_prev_zeta.addTerms(prev_zeta_coeff, prev_zeta_var)

                                    # Add constraint to Gurobi model
                                    LeftHandSide = LeftHandSide_upsilon + LeftHandSide_zeta + LeftHandSide_q + LeftHandSide_prev_zeta

                                    constraint_name = f"HighPriorityPatientServiceConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_j_{j}_c_{c}_h_{h}_index_{self.LastAddedConstraintIndex}"
                                    self.GurobiModel.addConstr(LeftHandSide == RightHandSide, name=constraint_name)

                                    self.GurobiModel.update()
                                    self.PIHighPriorityPatientServiceConstraint_Names.append(constraint_name)
                                    self.IndexPIHighPriorityPatientServiceConstraint.append(self.LastAddedConstraintIndex)
                                    self.IndexPIHighPriorityPatientServiceConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                                    self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                                    self.ConcernedInjuryPIHighPriorityPatientServiceConstraint.append(j)
                                    self.ConcernedBloodGPPIHighPriorityPatientServiceConstraint.append(c)
                                    self.ConcernedHospitalPIHighPriorityPatientServiceConstraint.append(h)
                                    self.ConcernedTimePIHighPriorityPatientServiceConstraint.append(t)        
                                    self.ConcernedScenarioPIHighPriorityPatientServiceConstraint.append(w)
    
    def CreatePILowMedPriorityPatientFlowConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePILowMedPriorityPatientFlowConstraint")

        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for j in self.Instance.InjuryLevelSet:
                        if j != 0:
                            for c in self.Instance.BloodGPSet:
                                for l in self.Instance.DemandSet:
                                    LeftHandSide_q = gp.LinExpr()  
                                    LeftHandSide_mu = gp.LinExpr()  
                                    LeftHandSide_prev_mu = gp.LinExpr()  

                                    ############# Demand
                                    RightHandSide = self.EVPIScenarioSet[wevpi].Demands[t][j][c][l]

                                    ############# q
                                    q_index = [self.GetIndexPIPatientTransferVariable(j, c, l, u, m, t, wevpi, w) 
                                                for u in self.Instance.FacilitySet 
                                                for m in self.Instance.RescueVehicleSet]
                                    if t in self.PeriodsInGlobalMIPPatientTransfer:
                                        q_var = [self.PatientTransfer_Var_SDDP[q_index[i]] for i in range(len(q_index))]
                                    else:
                                        q_var = [self.PatientTransfer_Var_SDDP_EVPI[q_index[i]] for i in range(len(q_index))]
                                    q_coeff = [1.0 for i in range(len(q_index))]
                                    LeftHandSide_q.addTerms(q_coeff, q_var)

                                    ############# mu
                                    mu_index = [self.GetIndexPIUnsatisfiedPatientsVariable(j, c, l, t, wevpi, w)]
                                    if t in self.PeriodsInGlobalMIPUnsatisfiedPatients:
                                        mu_var = [self.UnsatisfiedPatients_Var_SDDP[mu_index[i]] for i in range(len(mu_index))] 
                                    else:
                                        mu_var = [self.UnsatisfiedPatients_Var_SDDP_EVPI[mu_index[i]] for i in range(len(mu_index))]                            
                                    mu_coeff = [1.0 for i in range(len(mu_index))]
                                    LeftHandSide_mu.addTerms(mu_coeff, mu_var)
                                    
                                    ############# Previous mu
                                    if t > 0:
                                        prev_mu_index = [self.GetIndexPIUnsatisfiedPatientsVariable(j, c, l, (t-1), wevpi, w)]
                                        if (t-1) in self.PeriodsInGlobalMIPUnsatisfiedPatients:
                                            prev_mu_var = [self.UnsatisfiedPatients_Var_SDDP[prev_mu_index[i]] for i in range(len(prev_mu_index))]
                                        else:
                                            prev_mu_var = [self.UnsatisfiedPatients_Var_SDDP_EVPI[prev_mu_index[i]] for i in range(len(prev_mu_index))]
                                        prev_mu_coeff = [-1.0 for i in range(len(prev_mu_index))]
                                        LeftHandSide_prev_mu.addTerms(prev_mu_coeff, prev_mu_var)

                                    # Add constraint to Gurobi model
                                    LeftHandSide = LeftHandSide_q + LeftHandSide_mu + LeftHandSide_prev_mu

                                    constraint_name = f"LowMedPriorityPatientFlowConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_j_{j}_c_{c}_l_{l}_index_{self.LastAddedConstraintIndex}"
                                    self.GurobiModel.addConstr(LeftHandSide == RightHandSide, name=constraint_name)

                                    self.GurobiModel.update()
                                    self.PILowMedPriorityPatientFlowConstraint_Names.append(constraint_name)
                                    self.IndexPILowMedPriorityPatientFlowConstraint.append(self.LastAddedConstraintIndex)
                                    self.IndexPILowMedPriorityPatientFlowConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                                    self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                                    self.ConcernedInjuryPILowMedPriorityPatientFlowConstraint.append(j)
                                    self.ConcernedBloodGPPILowMedPriorityPatientFlowConstraint.append(c)
                                    self.ConcernedDemandPILowMedPriorityPatientFlowConstraint.append(l)
                                    self.ConcernedTimePILowMedPriorityPatientFlowConstraint.append(t)        
                                    self.ConcernedScenarioPILowMedPriorityPatientFlowConstraint.append(w)
                                    self.ConcernedEVPIScenarioPILowMedPriorityPatientFlowConstraint.append(wevpi)

    def CreatePIHighPriorityPatientFlowConstraint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePIHighPriorityPatientFlowConstraint")

        for w in self.FixedScenarioSet:
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for j in self.Instance.InjuryLevelSet:
                        if j == 0:
                            for c in self.Instance.BloodGPSet:
                                for l in self.Instance.DemandSet:
                                    if self.IsInFutureStageForInv(t):

                                        LeftHandSide_q = gp.LinExpr()  
                                        LeftHandSide_mu = gp.LinExpr()  
                                        LeftHandSide_prev_mu = gp.LinExpr()  

                                        ############# Demand
                                        RightHandSide = self.EVPIScenarioSet[wevpi].Demands[t][j][c][l]

                                        ############# q
                                        q_index = [self.GetIndexPIPatientTransferVariable(j, c, l, h, m, t, wevpi, w) 
                                                    for h in self.Instance.HospitalSet 
                                                    for m in self.Instance.RescueVehicleSet]
                                        if t in self.PeriodsInGlobalMIPPatientTransfer:
                                            q_var = [self.PatientTransfer_Var_SDDP[q_index[i]] for i in range(len(q_index))]
                                        else:
                                            q_var = [self.PatientTransfer_Var_SDDP_EVPI[q_index[i]] for i in range(len(q_index))]
                                        q_coeff = [1.0 for i in range(len(q_index))]
                                        LeftHandSide_q.addTerms(q_coeff, q_var)

                                        ############# mu
                                        mu_index = [self.GetIndexPIUnsatisfiedPatientsVariable(j, c, l, t, wevpi, w)]
                                        if t in self.PeriodsInGlobalMIPUnsatisfiedPatients:
                                            mu_var = [self.UnsatisfiedPatients_Var_SDDP[mu_index[i]] for i in range(len(mu_index))] 
                                        else:
                                            mu_var = [self.UnsatisfiedPatients_Var_SDDP_EVPI[mu_index[i]] for i in range(len(mu_index))]                            
                                        mu_coeff = [1.0 for i in range(len(mu_index))]
                                        LeftHandSide_mu.addTerms(mu_coeff, mu_var)
                                        
                                        ############# Previous mu
                                        if t > 0:
                                            prev_mu_index = [self.GetIndexPIUnsatisfiedPatientsVariable(j, c, l, (t-1), wevpi, w)]
                                            if (t-1) in self.PeriodsInGlobalMIPUnsatisfiedPatients:
                                                prev_mu_var = [self.UnsatisfiedPatients_Var_SDDP[prev_mu_index[i]] for i in range(len(prev_mu_index))]
                                            else:
                                                prev_mu_var = [self.UnsatisfiedPatients_Var_SDDP_EVPI[prev_mu_index[i]] for i in range(len(prev_mu_index))]
                                            prev_mu_coeff = [-1.0 for i in range(len(prev_mu_index))]
                                            LeftHandSide_prev_mu.addTerms(prev_mu_coeff, prev_mu_var)

                                        # Add constraint to Gurobi model
                                        LeftHandSide = LeftHandSide_q + LeftHandSide_mu + LeftHandSide_prev_mu

                                        constraint_name = f"HighPriorityPatientFlowConstraint_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_j_{j}_c_{c}_l_{l}_index_{self.LastAddedConstraintIndex}"
                                        self.GurobiModel.addConstr(LeftHandSide == RightHandSide, name=constraint_name)

                                        self.GurobiModel.update()
                                        self.PIHighPriorityPatientFlowConstraint_Names.append(constraint_name)
                                        self.IndexPIHighPriorityPatientFlowConstraint.append(self.LastAddedConstraintIndex)
                                        self.IndexPIHighPriorityPatientFlowConstraintPerScenario[w].append(self.LastAddedConstraintIndex)
                                        self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1

                                        self.ConcernedInjuryPIHighPriorityPatientFlowConstraint.append(j)
                                        self.ConcernedBloodGPPIHighPriorityPatientFlowConstraint.append(c)
                                        self.ConcernedDemandPIHighPriorityPatientFlowConstraint.append(l)
                                        self.ConcernedTimePIHighPriorityPatientFlowConstraint.append(t)        
                                        self.ConcernedScenarioPIHighPriorityPatientFlowConstraint.append(w)
                                        self.ConcernedEVPIScenarioPIHighPriorityPatientFlowConstraint.append(wevpi)

    def CreatePIEstiamteEVPIConstraints(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- CreatePIEstiamteEVPIConstraints")

        for w in self.FixedScenarioSet:
            LeftHandSide_y = gp.LinExpr()  
            LeftHandSide_b = gp.LinExpr()  
            LeftHandSide_bPrime = gp.LinExpr()
            LeftHandSide_bDoublePrime = gp.LinExpr()
            LeftHandSide_q = gp.LinExpr()
            LeftHandSide_mu = gp.LinExpr()
            LeftHandSide_eta = gp.LinExpr()
            LeftHandSide_sigmavar = gp.LinExpr()
            LeftHandSide_upsilon = gp.LinExpr()
            LeftHandSide_zeta = gp.LinExpr()
            LeftHandSide_lambda = gp.LinExpr()
            LeftHandSide_Rhovar = gp.LinExpr()

            ############ y
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGoApheresisAssignment:
                    for i in self.Instance.ACFPPointSet:
                        index_var = self.GetIndexPIApheresisAssignmentVariable(i, t, wevpi, w)
                        if t in self.PeriodsInGlobalMIPApheresisAssignment:
                            var_y = self.ApheresisAssignment_Var_SDDP[index_var]
                        else:
                            var_y = self.ApheresisAssignment_Var_SDDP_EVPI[index_var]
                        coeff_y = (self.EVPIScenarioSet[wevpi].Probability * self.Instance.Fixed_Cost_ACF[i]
                                if t > self.GetTimePeriodAssociatedToApheresisAssignmentVariable(self.RangePeriodApheresisAssignment[-1]) else 0.0)
                        LeftHandSide_y.addTerms(coeff_y, var_y)
            ############ b
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGoTransshipmentHI:
                    for c in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for h in self.Instance.HospitalSet:
                                for i in self.Instance.ACFPPointSet:
                                    index_var = self.GetIndexPITransshipmentHIVariable(c, r, h, i, t, wevpi, w)
                                    if t in self.PeriodsInGlobalMIPTransshipmentHI:
                                        var_b = self.TransshipmentHI_Var_SDDP[index_var]
                                    else:
                                        var_b = self.TransshipmentHI_Var_SDDP_EVPI[index_var]
                                    coeff_b = (self.EVPIScenarioSet[wevpi].Probability * self.Instance.Distance_A_H[i][h]
                                            if t > self.GetTimePeriodAssociatedToApheresisAssignmentVariable(self.RangePeriodApheresisAssignment[-1]) else 0.0)
                                    LeftHandSide_b.addTerms(coeff_b, var_b)
            ############ b'
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGoTransshipmentII:
                    for c in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for i in self.Instance.ACFPPointSet:
                                for iprime in self.Instance.ACFPPointSet:
                                    index_var = self.GetIndexPITransshipmentIIVariable(c, r, i, iprime, t, wevpi, w)
                                    if t in self.PeriodsInGlobalMIPTransshipmentII:
                                        var_bPrime = self.TransshipmentII_Var_SDDP[index_var]
                                    else:
                                        var_bPrime = self.TransshipmentII_Var_SDDP_EVPI[index_var]
                                    coeff_bPrime = (self.EVPIScenarioSet[wevpi].Probability * self.Instance.Distance_A_A[i][iprime]
                                            if t > self.GetTimePeriodAssociatedToApheresisAssignmentVariable(self.RangePeriodApheresisAssignment[-1]) else 0.0)
                                    LeftHandSide_bPrime.addTerms(coeff_bPrime, var_bPrime)
            ############ b''
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGoTransshipmentHH:
                    for c in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for h in self.Instance.HospitalSet:
                                for hprime in self.Instance.HospitalSet:
                                    index_var = self.GetIndexPITransshipmentHHVariable(c, r, h, hprime, t, wevpi, w)
                                    if t in self.PeriodsInGlobalMIPTransshipmentHH:
                                        var_bDoublePrime = self.TransshipmentHH_Var_SDDP[index_var]
                                    else:
                                        var_bDoublePrime = self.TransshipmentHH_Var_SDDP_EVPI[index_var]
                                    coeff_bDoublePrime = (self.EVPIScenarioSet[wevpi].Probability * self.Instance.Distance_H_H[h][hprime]
                                            if t > self.GetTimePeriodAssociatedToApheresisAssignmentVariable(self.RangePeriodApheresisAssignment[-1]) else 0.0)
                                    LeftHandSide_bDoublePrime.addTerms(coeff_bDoublePrime, var_bDoublePrime)            
            ############ q
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for j in self.Instance.InjuryLevelSet:
                        for c in self.Instance.BloodGPSet:
                            for l in self.Instance.DemandSet:
                                for u in self.Instance.FacilitySet:
                                    for m in self.Instance.RescueVehicleSet:
                                        index_var = self.GetIndexPIPatientTransferVariable(j, c, l, u, m, t, wevpi, w)
                                        if t in self.PeriodsInGlobalMIPPatientTransfer:
                                            var_q = self.PatientTransfer_Var_SDDP[index_var]
                                        else:
                                            var_q = self.PatientTransfer_Var_SDDP_EVPI[index_var]

                                        if u < self.Instance.NrHospitals:
                                            CostInObj = self.Instance.Distance_D_H[l][u]
                                        else:
                                            CostInObj = self.Instance.Distance_D_A[l][u - self.Instance.NrHospitals]
                                        coeff_q = (self.EVPIScenarioSet[wevpi].Probability * CostInObj)
                                        LeftHandSide_q.addTerms(coeff_q, var_q)
            ############ mu
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for j in self.Instance.InjuryLevelSet:
                        for c in self.Instance.BloodGPSet:
                            for l in self.Instance.DemandSet:
                                index_var = self.GetIndexPIUnsatisfiedPatientsVariable(j, c, l, t, wevpi, w)
                                if t in self.PeriodsInGlobalMIPUnsatisfiedPatients:
                                    var_mu = self.UnsatisfiedPatients_Var_SDDP[index_var]
                                else:
                                    var_mu = self.UnsatisfiedPatients_Var_SDDP_EVPI[index_var]
                                coeff_mu = (self.EVPIScenarioSet[wevpi].Probability * self.Instance.Casualty_Shortage_Cost[j][l])
                                LeftHandSide_mu.addTerms(coeff_mu, var_mu)
            ############ eta
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for c in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for u in self.Instance.FacilitySet:
                                index_var = self.GetIndexPIPlateletInventoryVariable(c, r, u, t, wevpi, w)
                                if t in self.PeriodsInGlobalMIPPlateletInventory:
                                    var_eta = self.PlateletInventory_Var_SDDP[index_var]
                                else:
                                    var_eta = self.PlateletInventory_Var_SDDP_EVPI[index_var]
                                coeff_eta = (self.EVPIScenarioSet[wevpi].Probability * self.Instance.Platelet_Inventory_Cost[u])
                                LeftHandSide_eta.addTerms(coeff_eta, var_eta)
            ############ sigmavar
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for u in self.Instance.FacilitySet:
                        index_var = self.GetIndexPIOutdatedPlateletVariable(u, t, wevpi, w)
                        if t in self.PeriodsInGlobalMIPPlateletInventory:
                            var_sigmavar = self.OutdatedPlatelet_Var_SDDP[index_var]
                        else:
                            var_sigmavar = self.OutdatedPlatelet_Var_SDDP_EVPI[index_var]
                        coeff_sigmavar = (self.EVPIScenarioSet[wevpi].Probability * self.Instance.Platelet_Wastage_Cost[u])
                        LeftHandSide_sigmavar.addTerms(coeff_sigmavar, var_sigmavar)
            ############ upsilon
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for j in self.Instance.InjuryLevelSet:
                        for cprime in self.Instance.BloodGPSet:
                            for c in self.Instance.BloodGPSet:
                                for r in self.Instance.PlateletAgeSet:
                                    for u in self.Instance.FacilitySet:
                                        index_var = self.GetIndexPIServedPatientVariable(j, cprime, c, r, u, t, wevpi, w)
                                        if t in self.PeriodsInGlobalMIPServedPatient:
                                            var_upsilon = self.ServedPatient_Var_SDDP[index_var]
                                        else:
                                            var_upsilon = self.ServedPatient_Var_SDDP_EVPI[index_var]
                                        coeff_upsilon = (self.EVPIScenarioSet[wevpi].Probability * self.Instance.Substitution_Weight[cprime][c])
                                        LeftHandSide_upsilon.addTerms(coeff_upsilon, var_upsilon)
            ############ zeta
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for j in self.Instance.InjuryLevelSet:
                        for c in self.Instance.BloodGPSet:
                            for u in self.Instance.FacilitySet:
                                index_var = self.GetIndexPIPatientPostponementVariable(j, c, u, t, wevpi, w)
                                if t in self.PeriodsInGlobalMIPPatientPostponement:
                                    var_zeta = self.PatientPostponement_Var_SDDP[index_var]
                                else:
                                    var_zeta = self.PatientPostponement_Var_SDDP_EVPI[index_var]
                                coeff_zeta = (self.EVPIScenarioSet[wevpi].Probability * self.Instance.Postponing_Cost_Surgery[j])
                                LeftHandSide_zeta.addTerms(coeff_zeta, var_zeta)
            ############ lambda
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for c in self.Instance.BloodGPSet:
                        for u in self.Instance.FacilitySet:
                            index_var = self.GetIndexPIPlateletApheresisExtractionVariable(c, u, t, wevpi, w)
                            if t in self.PeriodsInGlobalMIPPlateletApheresisExtraction:
                                var_lambda = self.PlateletApheresisExtraction_Var_SDDP[index_var]
                            else:
                                var_lambda = self.PlateletApheresisExtraction_Var_SDDP_EVPI[index_var]
                            coeff_lambda = (self.EVPIScenarioSet[wevpi].Probability * self.Instance.ApheresisExtraction_Cost[u])
                            LeftHandSide_lambda.addTerms(coeff_lambda, var_lambda)
            ############ Rhovar
            for wevpi in self.EVPIScenarioRange:
                for t in self.TimePeriodToGo:
                    for c in self.Instance.BloodGPSet:
                        for h in self.Instance.HospitalSet:
                            index_var = self.GetIndexPIPlateletWholeExtractionVariable(c, h, t, wevpi, w)
                            if t in self.PeriodsInGlobalMIPPlateletWholeExtraction:
                                var_Rhovar = self.PlateletWholeExtraction_Var_SDDP[index_var]
                            else:
                                var_Rhovar = self.PlateletWholeExtraction_Var_SDDP_EVPI[index_var]
                            coeff_Rhovar = (self.EVPIScenarioSet[wevpi].Probability * self.Instance.WholeExtraction_Cost[h])
                            LeftHandSide_Rhovar.addTerms(coeff_Rhovar, var_Rhovar)
            ###################################################################################################################
            # Multi-cut constraint or similar logic
            multiCutLHS_EVPI = gp.LinExpr()
            costToGoIndex_EVPI = self.GetIndexEVPICostToGo(w)
            multiCutLHS_EVPI.addTerms(-1.0, self.Cost_To_Go_Var_SDDP_EVPI[costToGoIndex_EVPI])

            LeftHandSide = LeftHandSide_y + LeftHandSide_b + LeftHandSide_bPrime + LeftHandSide_bDoublePrime \
                            + LeftHandSide_q + LeftHandSide_mu + LeftHandSide_eta + LeftHandSide_sigmavar \
                                + LeftHandSide_upsilon + LeftHandSide_zeta + LeftHandSide_lambda + LeftHandSide_Rhovar \
                                    + multiCutLHS_EVPI

            self.GurobiModel.addConstr(LeftHandSide == 0, name=f"Estimate_EVPI_Constraint_w_{w}_index_{self.LastAddedConstraintIndex}")
            self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1
            self.GurobiModel.update()

            if Constants.SDDPUseMultiCut:
                for futrescenario in self.FuturScenario:
                    index_var = self.GetIndexCostToGo(w, futrescenario)
                    prob = self.FuturScenarProba[futrescenario]
                    multiCutLHS_EVPI.addTerms(prob, self.Cost_To_Go_Var_SDDP[index_var])
            else:
                index_var = self.GetIndexCostToGo(w, 0)
                multiCutLHS_EVPI.addTerms(1, self.Cost_To_Go_Var_SDDP[index_var])

            self.GurobiModel.addConstr(multiCutLHS_EVPI >= 0, name=f"CutConstraint_w_{w}_index_{self.LastAddedConstraintIndex}")
            self.LastAddedConstraintIndex = self.LastAddedConstraintIndex + 1
            self.GurobiModel.update()

    #Define the variables
    def DefineVariables_and_Objective_Function(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (DefineVariables_and_Objective_Function)")
        
        if self.IsFirstStage():
            ################################# ACF Establishment Variable #################################
            if Constants.SolveRelaxationFirst or Constants.WarmUp_SDDP:
                self.ACFEstablishment_Var_SDDP = {}
                for i in self.Instance.ACFPPointSet:
                    Index_Var = self.GetIndexACFEstablishmentVariable(i)
                    var_name = f"x_i_{i}_index_{Index_Var}"
                    self.ACFEstablishment_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, lb = 0, ub = 1, obj = self.Instance.Fixed_Cost_ACF[i], name = var_name)
            else:
                self.ACFEstablishment_Var_SDDP = {}
                for i in self.Instance.ACFPPointSet:
                    Index_Var = self.GetIndexACFEstablishmentVariable(i)
                    var_name = f"x_i_{i}_index_{Index_Var}"
                    self.ACFEstablishment_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.BINARY, lb = 0, ub = 1, obj = self.Instance.Fixed_Cost_ACF[i], name = var_name)

            
            self.GurobiModel.update()  
            #for var in self.ACFEstablishment_Var_SDDP.values():
                #if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            
            ################################# Vehicle Assignment Variables #################################
            if Constants.SolveRelaxationFirst or Constants.WarmUp_SDDP:
                self.VehicleAssignment_Var_SDDP = {}
                for m in self.Instance.RescueVehicleSet:
                    for i in self.Instance.ACFPPointSet:
                        Index_Var = self.GetIndexVehicleAssignmentVariable(m, i)
                        var_name = f"thetavar_m_{m}_i_{i}_index_{Index_Var}"
                        self.VehicleAssignment_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, lb = 0, ub = GRB.INFINITY, obj = self.Instance.VehicleAssignment_Cost[m], name = var_name)
            else:
                self.VehicleAssignment_Var_SDDP = {}
                for m in self.Instance.RescueVehicleSet:
                    for i in self.Instance.ACFPPointSet:
                        Index_Var = self.GetIndexVehicleAssignmentVariable(m, i)
                        var_name = f"thetavar_m_{m}_i_{i}_index_{Index_Var}"
                        self.VehicleAssignment_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.INTEGER, lb = 0, ub = GRB.INFINITY, obj = self.Instance.VehicleAssignment_Cost[m], name = var_name)

            
            self.GurobiModel.update()  
            # for var in self.VehicleAssignment_Var_SDDP.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")

        ################################# Apheresis Assignment Variables #################################
        self.ApheresisAssignment_Var_SDDP = {}

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodApheresisAssignment:
                for i in self.Instance.ACFPPointSet:
                    Index_Var = self.GetIndexApheresisAssignmentVariable(i, t, w)                        

                    var_name = f"y_w_{w}_t_{self.TimeDecisionStage + t}_i_{i}_index_{Index_Var}"

                    #self.ApheresisAssignment_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, obj = self.Instance.ApheresisMachineAssignment_Cost[i], lb = 0, ub = self.Instance.Total_Apheresis_Machine_ACF[t], name = var_name)
                    self.ApheresisAssignment_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, obj = self.Instance.ApheresisMachineAssignment_Cost[i], lb = 0, ub = GRB.INFINITY, name = var_name)

        self.GurobiModel.update()  
        
        # for var in self.ApheresisAssignment_Var_SDDP.values():
        #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
        
        ################################# TransshipmentHI Variables #################################
        self.TransshipmentHI_Var_SDDP = {}

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodApheresisAssignment:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:                         
                        for h in self.Instance.HospitalSet:                         
                            for i in self.Instance.ACFPPointSet:                         
                                Index_Var = self.GetIndexTransshipmentHIVariable(c, r, h, i, t, w)                        

                                var_name = f"b_w_{w}_t_{self.TimeDecisionStage + t}_c_{c}_r_{r}_h_{h}_i_{i}_index_{Index_Var}"                               


                                UBound = GRB.INFINITY
                                if Constants.Transshipment_Enabled == False:
                                    UBound = 0

                                self.TransshipmentHI_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype = GRB.CONTINUOUS, obj = self.Instance.Distance_A_H[i][h], lb = 0, ub = UBound, name = var_name)

        self.GurobiModel.update()  
        
        #for var in self.TransshipmentHI_Var_SDDP.values():
            #if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
        
        ################################# TransshipmentII Variables #################################
        self.TransshipmentII_Var_SDDP = {}

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodApheresisAssignment:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:                         
                        for i in self.Instance.ACFPPointSet:                         
                            for iprime in self.Instance.ACFPPointSet:                         
                                Index_Var = self.GetIndexTransshipmentIIVariable(c, r, i, iprime, t, w)                        

                                var_name = f"b'_w_{w}_t_{self.TimeDecisionStage + t}_c_{c}_r_{r}_i_{i}_i'_{iprime}_index_{Index_Var}"                               

                                if i == iprime:
                                    UBound = 0
                                else:
                                    UBound = GRB.INFINITY
                                
                                if Constants.Transshipment_Enabled == False:
                                    UBound = 0

                                self.TransshipmentII_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype = GRB.CONTINUOUS, obj = self.Instance.Distance_A_A[i][iprime], lb = 0, ub = UBound, name = var_name)

        self.GurobiModel.update()  
        
        #for var in self.TransshipmentII_Var_SDDP.values():
            #if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")

        ################################# TransshipmentHH Variables #################################
        self.TransshipmentHH_Var_SDDP = {}

        for w in self.FixedScenarioSet:
            for t in self.RangePeriodApheresisAssignment:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:                         
                        for h in self.Instance.HospitalSet:                         
                            for hprime in self.Instance.HospitalSet:                         
                                Index_Var = self.GetIndexTransshipmentHHVariable(c, r, h, hprime, t, w)                        

                                var_name = f"b''_w_{w}_t_{self.TimeDecisionStage + t}_c_{c}_r_{r}_h_{h}_h'_{hprime}_index_{Index_Var}"                               

                                if h == hprime:
                                    UBound = 0
                                else:
                                    UBound = GRB.INFINITY
                                
                                if Constants.Transshipment_Enabled == False:
                                    UBound = 0

                                self.TransshipmentHH_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype = GRB.CONTINUOUS, obj = self.Instance.Distance_H_H[h][hprime], lb = 0, ub = UBound, name = var_name)

        self.GurobiModel.update()  
        
        #for var in self.TransshipmentHH_Var_SDDP.values():
            #if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
        
        ################################# Patient Transfer Variable #################################
        self.PatientTransfer_Var_SDDP = {}
        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for j in self.Instance.InjuryLevelSet:
                    for c in self.Instance.BloodGPSet:
                        for l in self.Instance.DemandSet:
                            for u in self.Instance.FacilitySet:
                                for m in self.Instance.RescueVehicleSet:
                                    Index_Var = self.GetIndexPatientTransferVariable(j, c, l, u, m, t, w)                        

                                    var_name = f"q_w_{w}_t_{self.TimeObservationStage + t}_j_{j}_c_{c}_l_{l}_u_{u}_m_{m}_index_{Index_Var}"

                                    if u < self.Instance.NrHospitals:
                                        CostInObj = self.Instance.Distance_D_H[l][u]
                                    else:
                                        CostInObj = self.Instance.Distance_D_A[l][u - self.Instance.NrHospitals]
        
                                    self.PatientTransfer_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype = GRB.CONTINUOUS, obj = CostInObj, lb = 0, ub = GRB.INFINITY, name = var_name)
                        
        self.GurobiModel.update()  
        
        #for var in self.PatientTransfer_Var_SDDP.values():
            #if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
        
        ################################# Unsatisfied Patients Variable #################################
        self.UnsatisfiedPatients_Var_SDDP = {}
        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for j in self.Instance.InjuryLevelSet:
                    for c in self.Instance.BloodGPSet:
                        for l in self.Instance.DemandSet:
                                            
                            Index_Var = self.GetIndexUnsatisfiedPatientsVariable(j, c, l, t, w)                        

                            var_name = f"mu_w_{w}_t_{self.TimeObservationStage + t}_j_{j}_c_{c}_l_{l}_index_{Index_Var}"

                            self.UnsatisfiedPatients_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype = GRB.CONTINUOUS, obj = self.Instance.Casualty_Shortage_Cost[j][l], lb = 0, ub = GRB.INFINITY, name = var_name)
                
        self.GurobiModel.update() 
        
        #for var in self.UnsatisfiedPatients_Var_SDDP.values():
            #if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
        
        ################################# Platelet Inventory Variable #################################
        self.PlateletInventory_Var_SDDP = {}
        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for c in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for u in self.Instance.FacilitySet:
                                            
                            Index_Var = self.GetIndexPlateletInventoryVariable(c, r, u, t, w)                        

                            var_name = f"eta_w_{w}_t_{self.TimeObservationStage + t}_c_{c}_r_{r}_u_{u}_index_{Index_Var}"

                            self.PlateletInventory_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype = GRB.CONTINUOUS, obj = self.Instance.Platelet_Inventory_Cost[u], lb = 0, ub = GRB.INFINITY, name = var_name)
                
        self.GurobiModel.update() 
        
        #for var in self.PlateletInventory_Var_SDDP.values():
            #if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")

        ################################# Outdated Platelet Variable #################################
        self.OutdatedPlatelet_Var_SDDP = {}
        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for u in self.Instance.FacilitySet:
                                            
                    Index_Var = self.GetIndexOutdatedPlateletVariable(u, t, w)                        

                    var_name = f"Sigmavar_w_{w}_t_{self.TimeObservationStage + t}_u_{u}_index_{Index_Var}"

                    self.OutdatedPlatelet_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype = GRB.CONTINUOUS, obj = self.Instance.Platelet_Wastage_Cost[u], lb = 0, ub = GRB.INFINITY, name = var_name)
           
        self.GurobiModel.update() 
        
        #for var in self.OutdatedPlatelet_Var_SDDP.values():
            #if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
        
        ################################# Served Patient Variable #################################
        self.ServedPatient_Var_SDDP = {}
        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for j in self.Instance.InjuryLevelSet:
                    for cprime in self.Instance.BloodGPSet:
                        for c in self.Instance.BloodGPSet:
                            for r in self.Instance.PlateletAgeSet:
                                for u in self.Instance.FacilitySet:
                                            
                                    Index_Var = self.GetIndexServedPatientVariable(j, cprime, c, r, u, t, w)                        

                                    var_name = f"upsilon_w_{w}_t_{self.TimeObservationStage + t}_j_{j}_c'_{cprime}_c_{c}_r_{r}_u_{u}_index_{Index_Var}"

                                    self.ServedPatient_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype = GRB.CONTINUOUS, obj = self.Instance.Substitution_Weight[cprime][c], lb = 0, ub = GRB.INFINITY, name = var_name)
                        
        self.GurobiModel.update() 
        
        #for var in self.ServedPatient_Var_SDDP.values():
            #if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
        
        ################################# Patient Postponement Variable #################################
        self.PatientPostponement_Var_SDDP = {}
        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for j in self.Instance.InjuryLevelSet:
                    for c in self.Instance.BloodGPSet:
                        for u in self.Instance.FacilitySet:
                                            
                            Index_Var = self.GetIndexPatientPostponementVariable(j, c, u, t, w)                        

                            var_name = f"zeta_w_{w}_t_{self.TimeObservationStage + t}_j_{j}_c_{c}_u_{u}_index_{Index_Var}"

                            self.PatientPostponement_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype = GRB.CONTINUOUS, obj = self.Instance.Postponing_Cost_Surgery[j], lb = 0, ub = GRB.INFINITY, name = var_name)
                
        self.GurobiModel.update() 
        
        #for var in self.PatientPostponement_Var_SDDP.values():
            #if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
        
        ################################# Platelet Apheresis Extraction Variable #################################
        self.PlateletApheresisExtraction_Var_SDDP = {}
        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for c in self.Instance.BloodGPSet:
                    for u in self.Instance.FacilitySet:                 
                        Index_Var = self.GetIndexPlateletApheresisExtractionVariable(c, u, t, w)                        
                        var_name = f"lambda_w_{w}_t_{self.TimeObservationStage + t}_c_{c}_u_{u}_index_{Index_Var}"
                        self.PlateletApheresisExtraction_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype = GRB.CONTINUOUS, obj = self.Instance.ApheresisExtraction_Cost[u], lb = 0, ub = GRB.INFINITY, name = var_name) 
        self.GurobiModel.update() 
        # for var in self.PlateletApheresisExtraction_Var_SDDP.values():
        #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
        
        ################################# Platelet Whole Extraction Variable #################################
        self.PlateletWholeExtraction_Var_SDDP = {}
        for w in self.FixedScenarioSet:
            for t in self.RangePeriodPatientTransfer:
                for c in self.Instance.BloodGPSet:
                    for h in self.Instance.HospitalSet:                    
                        Index_Var = self.GetIndexPlateletWholeExtractionVariable(c, h, t, w)                        
                        var_name = f"Rhovar_w_{w}_t_{self.TimeObservationStage + t}_c_{c}_h_{h}_index_{Index_Var}"
                        self.PlateletWholeExtraction_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype = GRB.CONTINUOUS, obj = self.Instance.WholeExtraction_Cost[h], lb = 0, ub = GRB.INFINITY, name = var_name)      
        self.GurobiModel.update() 
        # for var in self.PlateletWholeExtraction_Var_SDDP.values():
        #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")

        ################################# Cost to Go Variable #################################
        if not self.IsLastStage():
            costtogoproba = []

            costtogoproba = [ self.FuturScenarProba[f] for w in self.FixedScenarioSet for f in self.FuturScenario] 

            self.Cost_To_Go_Var_SDDP = {}

            index = 0  # To track the index in the costtogoproba list
            # Loop through scenarios and future scenarios to create variables
            for w in self.FixedScenarioSet:
                for f in self.FuturScenario:      
                    Index_Var = self.GetIndexCostToGo(w, f)
                    var_name = f"Cost_To_Go_Var_SDDP_w_{w}_t_{self.DecisionStage + 1}_f_{f}_index_{Index_Var}"   

                    # Use the index to get the corresponding objective coefficient
                    obj_coeff = costtogoproba[index]
                    
                    # Create the variable and add it to the dictionary
                    self.Cost_To_Go_Var_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, obj=obj_coeff, lb = 0.0, ub = GRB.INFINITY, name=var_name)
                    
                    index += 1  # Move to the next coefficient for the next variable


            # Update the model to integrate the new variables
            self.GurobiModel.update()

            # for var in self.Cost_To_Go_Var_SDDP.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")

        ################################# Flows of different Variable from previous stages #################################
        if not self.IsFirstStage():   

            # Here, we are generating variables fixed in previous stage for thoes which are already decided in the first-stage and later like: ApheresisAssignment and Transshipment
            # In fact, whatever fixed variable decided earlier and have (t-1) in its index, are defined hereexcept for PLT Inventory, which we may have initial inventories.

            ################### flowPLTInvTransHospitalFromPreviousStage Variable ###################
            PLTInvTransHospital = [[[[self.GetFlowPLTInvTransHospitalFromPreviousStage(cprime, r, h, t)
                                        for h in self.Instance.HospitalSet]
                                        for r in self.Instance.PlateletAgeSet]
                                        for cprime in self.Instance.BloodGPSet]
                                        for t in self.RangePeriodPatientTransfer]            
            self.ComputeFlowPLTInvTransHospitalArray()            
            self.flowPLTInvTransHospitalFromPreviousStage_SDDP = {}
            for w in self.FixedScenarioSet:
                for t in self.RangePeriodPatientTransfer:
                    for cprime in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for h in self.Instance.HospitalSet:
                                Index_Var = self.GetIndexFlowPLTInvTransHospitalFromPreviousStage(cprime, r, h, t)                                  
                                var_name = f"flowPLTInvTransHospitalFromPreviousStage_w_{w}_t_{self.TimeObservationStage + t}_c'_{cprime}_r_{r}_h_{h}_index_{Index_Var}"
                                self.flowPLTInvTransHospitalFromPreviousStage_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, obj = 0, lb = PLTInvTransHospital[t][cprime][r][h], ub = PLTInvTransHospital[t][cprime][r][h], name=var_name)
            self.GurobiModel.update() 
            # for var in self.flowPLTInvTransHospitalFromPreviousStage_SDDP.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            
            ################### flowPLTInvTransACFFromPreviousStage  Variable ###################
            PLTInvTransACF = [[[[self.GetFlowPLTInvTransACFFromPreviousStage(cprime, r, i, t)
                                        for i in self.Instance.ACFPPointSet]
                                        for r in self.Instance.PlateletAgeSet]
                                        for cprime in self.Instance.BloodGPSet]
                                        for t in self.RangePeriodPatientTransfer] 
            self.ComputeFlowPLTInvTransACFArray()  
            self.flowPLTInvTransACFFromPreviousStage_SDDP = {}
            for w in self.FixedScenarioSet:
                for t in self.RangePeriodPatientTransfer:
                    for cprime in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for i in self.Instance.ACFPPointSet:
                                Index_Var = self.GetIndexFlowPLTInvTransACFFromPreviousStage(cprime, r, i, t)                                  
                                var_name = f"flowPLTInvTransACFFromPreviousStage_w_{w}_t_{self.TimeObservationStage + t}_c'_{cprime}_r_{r}_i_{i}_index_{Index_Var}"
                                self.flowPLTInvTransACFFromPreviousStage_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, obj = 0, lb = PLTInvTransACF[t][cprime][r][i], ub = PLTInvTransACF[t][cprime][r][i], name=var_name)
            self.GurobiModel.update() 
            # for var in self.flowPLTInvTransACFFromPreviousStage_SDDP.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")

            ################### flowApheresisAssignmentFromPreviousStage  Variable ###################
            ApheresisAssignment = [[self.GetFlowApheresisAssignmentFromPreviousStage(i, t)
                                        for i in self.Instance.ACFPPointSet]
                                        for t in self.RangePeriodPatientTransfer] 
            self.ComputeFlowApheresisAssignmentArray()  
            self.flowApheresisAssignmentFromPreviousStage_SDDP = {}
            for w in self.FixedScenarioSet:
                for t in self.RangePeriodPatientTransfer:
                    for i in self.Instance.ACFPPointSet:
                        Index_Var = self.GetIndexFlowApheresisAssignmentFromPreviousStage(i, t)                                  
                        var_name = f"flowApheresisAssignmentFromPreviousStage_w_{w}_t_{self.TimeObservationStage + t}_i_{i}_index_{Index_Var}"
                        self.flowApheresisAssignmentFromPreviousStage_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, obj = 0, lb = ApheresisAssignment[t][i], ub = ApheresisAssignment[t][i], name=var_name)
            self.GurobiModel.update() 
            # for var in self.flowApheresisAssignmentFromPreviousStage_SDDP.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")

            # Here, we are generating variables fixed in previous stage for thoes which are already decided in the second-stage and later like: ApheresisAssignment and Transshipment
            # In fact, whatever fixed variable decided earlier and have (t-2) in its index, are defined here; except for PLT Inventory, which we may have initial inventories.             

            ################### FlowUnsatisfiedLowMedPatientsFromPreviousStage  Variable ###################
            flowunsatisfiedpatientfromprevioustage = [[[[self.GetFlowUnsatisfiedPatientsFromPreviousStage(j, c, l, t)
                                                            for l in self.Instance.DemandSet]
                                                            for c in self.Instance.BloodGPSet]
                                                            for j in self.Instance.InjuryLevelSet]
                                                            for t in self.RangePeriodPatientTransfer]
            self.ComputeFlowUnsatisfiedLowMedPatientsArray()
            self.flowUnsatisfiedLowMedPatientsFromPreviousStage_SDDP = {}
            for w in self.FixedScenarioSet:
                for t in self.RangePeriodPatientTransfer:
                    for j in self.Instance.InjuryLevelSet:
                        if j != 0:
                            for c in self.Instance.BloodGPSet:
                                for l in self.Instance.DemandSet:
                                    Index_Var = self.GetIndexFlowUnsatisfiedLowMedPatientsFromPreviousStage(j, c, l, t)
                                    var_name = f"flowUnsatisfiedLowMedPatientsFromPreviousStage_w_{w}_t_{(self.TimeObservationStage + t) - 1}_j_{j}_c_{c}_l_{l}_index_{Index_Var}"  # We are using 't_{(self.TimeObservationStage + t) - 1}' bc we are dealing with (t-2) in its constraint
                                    LowerUpperBound = flowunsatisfiedpatientfromprevioustage[t][j][c][l]
                                    self.flowUnsatisfiedLowMedPatientsFromPreviousStage_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, obj=0, lb = LowerUpperBound, ub = LowerUpperBound, name=var_name)                 
            self.GurobiModel.update()  
            # for var in self.flowUnsatisfiedLowMedPatientsFromPreviousStage_SDDP.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            
            ################### flowUnsatisfiedHighPatientsFromPreviousStage  Variable ###################
            self.ComputeFlowUnsatisfiedHighPatientsArray()
            self.flowUnsatisfiedHighPatientsFromPreviousStage_SDDP = {}
            for w in self.FixedScenarioSet:
                for t in self.RangePeriodPatientTransfer:
                    for j in self.Instance.InjuryLevelSet:
                        if j == 0:
                            for c in self.Instance.BloodGPSet:
                                for l in self.Instance.DemandSet:
                                    Index_Var = self.GetIndexFlowUnsatisfiedHighPatientsFromPreviousStage(j, c, l, t)                                  
                                    var_name = f"flowUnsatisfiedHighPatientsFromPreviousStage_w_{w}_t_{(self.TimeObservationStage + t) - 1}_j_{j}_c_{c}_l_{l}_index_{Index_Var}" # We are using 't_{(self.TimeObservationStage + t) - 1}' bc we are dealing with (t-2) in its constraint
                                    LowerUpperBound = flowunsatisfiedpatientfromprevioustage[t][j][c][l]
                                    self.flowUnsatisfiedHighPatientsFromPreviousStage_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, obj=0, lb = LowerUpperBound, ub = LowerUpperBound, name=var_name)
            self.GurobiModel.update()  
            # for var in self.flowUnsatisfiedHighPatientsFromPreviousStage_SDDP.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")

            ################### FlowUnservedLowMedPatientsFromPreviousStage  Variable ###################
            flowunservedpatientfromprevioustage = [[[[self.GetFlowUnservedPatientsFromPreviousStage(j, c, u, t)
                                                            for u in self.Instance.FacilitySet]
                                                            for c in self.Instance.BloodGPSet]
                                                            for j in self.Instance.InjuryLevelSet]
                                                            for t in self.RangePeriodPatientTransfer]
            self.ComputeFlowUnservedLowMedPatientsArray()
            self.flowUnservedLowMedPatientsFromPreviousStage_SDDP = {}
            for w in self.FixedScenarioSet:
                for t in self.RangePeriodPatientTransfer:
                    for j in self.Instance.InjuryLevelSet:
                        if j != 0:
                            for c in self.Instance.BloodGPSet:
                                for u in self.Instance.FacilitySet:
                                    Index_Var = self.GetIndexFlowUnservedLowMedPatientsFromPreviousStage(j, c, u, t)                                  
                                    var_name = f"flowUnservedLowMedPatientsFromPreviousStage_w_{w}_t_{(self.TimeObservationStage + t) - 1}_j_{j}_c_{c}_u_{u}_index_{Index_Var}" # We are using 't_{(self.TimeObservationStage + t) - 1}' bc we are dealing with (t-2) in its constraint
                                    LowerUpperBound = flowunservedpatientfromprevioustage[t][j][c][u]
                                    self.flowUnservedLowMedPatientsFromPreviousStage_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, obj=0, lb = LowerUpperBound, ub = LowerUpperBound, name=var_name) 
            self.GurobiModel.update()  
            # for var in self.flowUnservedLowMedPatientsFromPreviousStage_SDDP.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            
            ################### FlowUnservedHighPatientsFromPreviousStage  Variable ###################
            self.ComputeFlowUnservedHighPatientsArray()
            self.flowUnservedHighPatientsFromPreviousStage_SDDP = {}
            for w in self.FixedScenarioSet:
                for t in self.RangePeriodPatientTransfer:
                    for j in self.Instance.InjuryLevelSet:
                        if j == 0:
                            for c in self.Instance.BloodGPSet:
                                for h in self.Instance.HospitalSet:
                                    Index_Var = self.GetIndexFlowUnservedHighPatientsFromPreviousStage(j, c, h, t)                                  
                                    var_name = f"flowUnservedHighPatientsFromPreviousStage_w_{w}_t_{(self.TimeObservationStage + t) - 1}_j_{j}_c_{c}_h_{h}_index_{Index_Var}" # We are using 't_{(self.TimeObservationStage + t) - 1}' bc we are dealing with (t-2) in its constraint
                                    LowerUpperBound = flowunservedpatientfromprevioustage[t][j][c][h]
                                    self.flowUnservedHighPatientsFromPreviousStage_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, obj = 0, lb = LowerUpperBound, ub = LowerUpperBound, name=var_name) 
            self.GurobiModel.update()  
            # for var in self.flowUnservedHighPatientsFromPreviousStage_SDDP.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            
            ################### FlowUnservedACFFromPreviousStage  Variable ###################
            flowunservedfromprevioustage_SumOnjc = [[self.GetFlowUnservedPatientCapFromPreviousStage(u, t)
                                                            for u in self.Instance.FacilitySet]
                                                            for t in self.RangePeriodPatientTransfer]
            self.ComputeFlowUnservedACFArray()
            self.flowUnservedACFFromPreviousStage_SDDP = {}
            for w in self.FixedScenarioSet:
                for t in self.RangePeriodPatientTransfer:
                    for i in self.Instance.ACFPPointSet:
                        Index_Var = self.GetIndexFlowUnservedACFFromPreviousStage(i, t)                                  
                        var_name = f"flowUnservedACFFromPreviousStage_w_{w}_t_{(self.TimeObservationStage + t) - 1}_i_{i}_index_{Index_Var}" # We are using 't_{(self.TimeObservationStage + t) - 1}' bc we are dealing with (t-2) in its constraint
                        LowerUpperBound = flowunservedfromprevioustage_SumOnjc[t][self.Instance.NrHospitals + i]
                        self.flowUnservedACFFromPreviousStage_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, obj = 0, lb = LowerUpperBound, ub = LowerUpperBound, name=var_name) 
            self.GurobiModel.update()  
            # for var in self.flowUnservedACFFromPreviousStage_SDDP.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")

            ################### FlowUnservedHospitalFromPreviousStage  Variable ###################
            self.ComputeFlowUnservedHospitalArray()
            self.flowUnservedHospitalFromPreviousStage_SDDP = {}
            for w in self.FixedScenarioSet:
                for t in self.RangePeriodPatientTransfer:
                    for h in self.Instance.HospitalSet:
                        Index_Var = self.GetIndexFlowUnservedHospitalFromPreviousStage(h, t)                                  
                        var_name = f"flowUnservedHospitalFromPreviousStage_w_{w}_t_{(self.TimeObservationStage + t) - 1}_h_{h}_index_{Index_Var}" # We are using 't_{(self.TimeObservationStage + t) - 1}' bc we are dealing with (t-2) in its constraint
                        LowerUpperBound = flowunservedfromprevioustage_SumOnjc[t][h]
                        self.flowUnservedHospitalFromPreviousStage_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, obj = 0, lb = LowerUpperBound, ub = LowerUpperBound, name=var_name) 
            self.GurobiModel.update()  
            # for var in self.flowUnservedHospitalFromPreviousStage_SDDP.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")

        ################################# Right Handsides (Which are obtained based on first-stage variables fixed now) #################################
        if not self.IsFirstStage():
            
            ################################# ACFTreatmentCapRHS Variable #################################
            acftreatmentcaprhs = [self.GetACFTreatmentCapacityConstraintRHS(i) 
                                  for i in self.Instance.ACFPPointSet]
            self.ACFTreatmentCapRHS_SDDP = {}
            for i in self.Instance.ACFPPointSet:
                Index_Var = self.GetIndexACFEstablishmentRHS_ACFTreatCapConst(i) 
                var_name = f"ACFTreatmentCapRHS_i_{i}_index_{Index_Var}"
                LowerUpperBound = acftreatmentcaprhs[i]
                self.ACFTreatmentCapRHS_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, obj = 0.0, lb = LowerUpperBound, ub = LowerUpperBound, name=var_name)
            self.GurobiModel.update()  
            # for var in self.ACFTreatmentCapRHS_SDDP.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            
            ################################# ACFRescueVehicleCapRHS Variable #################################
            acfrescVehicCapRHS_SDDP = [[self.GetACFRescueVehicleCapacityConstraintRHS(m, i) 
                                            for i in self.Instance.ACFPPointSet]
                                            for m in self.Instance.RescueVehicleSet]
            self.ACFRescVehicCapRHS_SDDP = {}
            for m in self.Instance.RescueVehicleSet:
                for i in self.Instance.ACFPPointSet:
                    Index_Var = self.GetIndexVehicleAssignmentRHS_ACFRescVehCapCons(m, i) 
                    var_name = f"ACFRescVehCapRHS_m_{m}_i_{i}_index_{Index_Var}"
                    LowerUpperBound = acfrescVehicCapRHS_SDDP[m][i]
                    self.ACFRescVehicCapRHS_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, obj = 0.0, lb = LowerUpperBound, ub = LowerUpperBound, name=var_name)
            self.GurobiModel.update()  
            
            # for var in self.ACFRescVehicCapRHS_SDDP.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
        

            if not self.IsLastStage():

                ################################# ACFApheresisCapRHS Variable #################################
                acfapheresisCapRHS_SDDP = [self.GetACFApheresisCapConstraintRHS(i) 
                                            for i in self.Instance.ACFPPointSet]
                
                self.ACFApheresisCapRHS_SDDP = {}
                for i in self.Instance.ACFPPointSet:
                    Index_Var = self.GetIndexACFEstablishmentRHS_ApheresisAssignCon(i) 
                    var_name = f"ACFApheresisCapRHS_i_{i}_index_{Index_Var}"
                    LowerUpperBound = acfapheresisCapRHS_SDDP[i]
                    self.ACFApheresisCapRHS_SDDP[Index_Var] = self.GurobiModel.addVar(vtype=GRB.CONTINUOUS, obj = 0.0, lb = LowerUpperBound, ub = LowerUpperBound, name=var_name)
                self.GurobiModel.update()  
                # for var in self.ACFApheresisCapRHS_SDDP.values():
                #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")

        #I just initialize CutRHSVariable_SDDP, it gets value later in SDDPCut class
        self.CutRHSVariable_SDDP = {}
    
        if Constants.SDDPUseEVPI and not self.IsLastStage():
            ################################# ApheresisAssignment_Var_SDDP_EVPI #################################
            self.ApheresisAssignment_Var_SDDP_EVPI = {}
            for w in self.FixedScenarioSet:
                for wevpi in self.EVPIScenarioRange:
                    for t in self.TimePeriodToGo:
                        for i in self.Instance.ACFPPointSet:
                            Index_Var = self.GetIndexPIApheresisAssignmentVariable(i, t, wevpi, w)                                                        
                            var_name = f"y_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_i_{i}_index_{Index_Var}"
                            #We areonly defining Var Trans Variables which we do not have in that specific stage, if we already defined for that specific (t), we are going to reuse them in the constraints.
                            if t not in self.PeriodsInGlobalMIPApheresisAssignment:
                                self.ApheresisAssignment_Var_SDDP_EVPI[Index_Var] = self.GurobiModel.addVar(obj = 0.0, lb = 0.0, ub = GRB.INFINITY, vtype = GRB.CONTINUOUS, name = var_name)
            self.GurobiModel.update()   
            # for var in self.ApheresisAssignment_Var_SDDP_EVPI.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            ################################# TransshipmentHI_Var_SDDP_EVPI #################################
            self.TransshipmentHI_Var_SDDP_EVPI = {}
            for w in self.FixedScenarioSet:
                for wevpi in self.EVPIScenarioRange:
                    for t in self.TimePeriodToGo:
                        for c in self.Instance.BloodGPSet:
                            for r in self.Instance.PlateletAgeSet:
                                for h in self.Instance.HospitalSet:
                                    for i in self.Instance.ACFPPointSet:
                                        Index_Var = self.GetIndexPITransshipmentHIVariable(c, r, h, i, t, wevpi, w)                                                        
                                        var_name = f"b_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_c_{c}_r_{r}_h_{h}_i_{i}_index_{Index_Var}"
                                        #We areonly defining Var Trans Variables which we do not have in that specific stage, if we already defined for that specific (t), we are going to reuse them in the constraints.
                                        if t not in self.PeriodsInGlobalMIPTransshipmentHI:
                                            self.TransshipmentHI_Var_SDDP_EVPI[Index_Var] = self.GurobiModel.addVar(obj = 0.0, lb = 0.0, ub = GRB.INFINITY, vtype = GRB.CONTINUOUS, name = var_name)
            self.GurobiModel.update()   
            # for var in self.TransshipmentHI_Var_SDDP_EVPI.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            ################################# TransshipmentII_Var_SDDP_EVPI #################################
            self.TransshipmentII_Var_SDDP_EVPI = {}
            for w in self.FixedScenarioSet:
                for wevpi in self.EVPIScenarioRange:
                    for t in self.TimePeriodToGo:
                        for c in self.Instance.BloodGPSet:
                            for r in self.Instance.PlateletAgeSet:
                                for i in self.Instance.ACFPPointSet:
                                    for iprime in self.Instance.ACFPPointSet:
                                        Index_Var = self.GetIndexPITransshipmentIIVariable(c, r, i, iprime, t, wevpi, w)                                                        
                                        var_name = f"b'_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_c_{c}_r_{r}_i_{i}_i'_{iprime}_index_{Index_Var}"
                                        #We areonly defining Var Trans Variables which we do not have in that specific stage, if we already defined for that specific (t), we are going to reuse them in the constraints.
                                        if t not in self.PeriodsInGlobalMIPTransshipmentII:
                                            self.TransshipmentII_Var_SDDP_EVPI[Index_Var] = self.GurobiModel.addVar(obj = 0.0, lb = 0.0, ub = GRB.INFINITY, vtype = GRB.CONTINUOUS, name = var_name)
            self.GurobiModel.update()   
            # for var in self.TransshipmentII_Var_SDDP_EVPI.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            ################################# TransshipmentHH_Var_SDDP_EVPI #################################
            self.TransshipmentHH_Var_SDDP_EVPI = {}
            for w in self.FixedScenarioSet:
                for wevpi in self.EVPIScenarioRange:
                    for t in self.TimePeriodToGo:
                        for c in self.Instance.BloodGPSet:
                            for r in self.Instance.PlateletAgeSet:
                                for h in self.Instance.HospitalSet:
                                    for hprime in self.Instance.HospitalSet:
                                        Index_Var = self.GetIndexPITransshipmentHHVariable(c, r, h, hprime, t, wevpi, w)                                                        
                                        var_name = f"b''_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_c_{c}_r_{r}_h_{h}_h'_{hprime}_index_{Index_Var}"
                                        #We areonly defining Var Trans Variables which we do not have in that specific stage, if we already defined for that specific (t), we are going to reuse them in the constraints.
                                        if t not in self.PeriodsInGlobalMIPTransshipmentHH:
                                            self.TransshipmentHH_Var_SDDP_EVPI[Index_Var] = self.GurobiModel.addVar(obj = 0.0, lb = 0.0, ub = GRB.INFINITY, vtype = GRB.CONTINUOUS, name = var_name)
            self.GurobiModel.update()   
            # for var in self.TransshipmentHH_Var_SDDP_EVPI.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            ################################# PatientTransfer_Var_SDDP_EVPI #################################
            self.PatientTransfer_Var_SDDP_EVPI = {}
            for w in self.FixedScenarioSet:
                for wevpi in self.EVPIScenarioRange:
                    for t in self.TimePeriodToGoPatientTransfer:
                        for j in self.Instance.InjuryLevelSet:                
                            for c in self.Instance.BloodGPSet:                
                                for l in self.Instance.DemandSet:                
                                    for u in self.Instance.FacilitySet:                
                                        for m in self.Instance.RescueVehicleSet:                
                                            Index_Var = self.GetIndexPIPatientTransferVariable(j, c, l, u, m, t, wevpi, w)   
                                            var_name = f"q_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_j_{j}_C_{c}_l_{l}_u_{u}_m_{m}_index_{Index_Var}"
                                            if t not in self.PeriodsInGlobalMIPPatientTransfer:
                                                self.PatientTransfer_Var_SDDP_EVPI[Index_Var] = self.GurobiModel.addVar(obj = 0.0, lb = 0.0, ub = GRB.INFINITY, vtype = GRB.CONTINUOUS, name = var_name)   
            self.GurobiModel.update()  # Ensure all pending model changes are applied
            # for var in self.PatientTransfer_Var_SDDP_EVPI.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            ################################# UnsatisfiedPatients_Var_SDDP_EVPI #################################
            self.UnsatisfiedPatients_Var_SDDP_EVPI = {}
            for w in self.FixedScenarioSet:
                for wevpi in self.EVPIScenarioRange:
                    for t in self.TimePeriodToGoUnsatisfiedPatients:
                        for j in self.Instance.InjuryLevelSet:                
                            for c in self.Instance.BloodGPSet:                
                                for l in self.Instance.DemandSet:                
                                    Index_Var = self.GetIndexPIUnsatisfiedPatientsVariable(j, c, l, t, wevpi, w)   
                                    var_name = f"mu_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_j_{j}_C_{c}_l_{l}_index_{Index_Var}"
                                    if t not in self.PeriodsInGlobalMIPUnsatisfiedPatients:
                                        self.UnsatisfiedPatients_Var_SDDP_EVPI[Index_Var] = self.GurobiModel.addVar(obj = 0.0, lb = 0.0, ub = GRB.INFINITY, vtype = GRB.CONTINUOUS, name = var_name)   
            self.GurobiModel.update()  # Ensure all pending model changes are applied
            # for var in self.UnsatisfiedPatients_Var_SDDP_EVPI.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            ################################# PlateletInventory_Var_SDDP_EVPI #################################
            self.PlateletInventory_Var_SDDP_EVPI = {}
            for w in self.FixedScenarioSet:
                for wevpi in self.EVPIScenarioRange:
                    for t in self.TimePeriodToGoPlateletInventory:
                        for c in self.Instance.BloodGPSet:                
                            for r in self.Instance.PlateletAgeSet:                
                                for u in self.Instance.FacilitySet:                
                                    Index_Var = self.GetIndexPIPlateletInventoryVariable(c, r, u, t, wevpi, w)   
                                    var_name = f"eta_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_c_{c}_r_{r}_u_{u}_index_{Index_Var}"
                                    if t not in self.PeriodsInGlobalMIPPlateletInventory:
                                        self.PlateletInventory_Var_SDDP_EVPI[Index_Var] = self.GurobiModel.addVar(obj = 0.0, lb = 0.0, ub = GRB.INFINITY, vtype = GRB.CONTINUOUS, name = var_name)   
            self.GurobiModel.update()  # Ensure all pending model changes are applied
            # for var in self.PlateletInventory_Var_SDDP_EVPI.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            ################################# OutdatedPlatelet_Var_SDDP_EVPI #################################
            self.OutdatedPlatelet_Var_SDDP_EVPI = {}
            for w in self.FixedScenarioSet:
                for wevpi in self.EVPIScenarioRange:
                    for t in self.TimePeriodToGoOutdatedPlatelet:
                        for u in self.Instance.FacilitySet:                
                            Index_Var = self.GetIndexPIOutdatedPlateletVariable(u, t, wevpi, w)   
                            var_name = f"sigmavar_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_u_{u}_index_{Index_Var}"
                            if t not in self.PeriodsInGlobalMIPOutdatedPlatelet:
                                self.OutdatedPlatelet_Var_SDDP_EVPI[Index_Var] = self.GurobiModel.addVar(obj = 0.0, lb = 0.0, ub = GRB.INFINITY, vtype = GRB.CONTINUOUS, name = var_name)   
            self.GurobiModel.update()  # Ensure all pending model changes are applied
            # for var in self.OutdatedPlatelet_Var_SDDP_EVPI.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            ################################# ServedPatient_Var_SDDP_EVPI #################################
            self.ServedPatient_Var_SDDP_EVPI = {}
            for w in self.FixedScenarioSet:
                for wevpi in self.EVPIScenarioRange:
                    for t in self.TimePeriodToGoServedPatient:
                        for j in self.Instance.InjuryLevelSet:                
                            for cprime in self.Instance.BloodGPSet:                
                                for c in self.Instance.BloodGPSet:                
                                    for r in self.Instance.PlateletAgeSet:                
                                        for u in self.Instance.FacilitySet:                
                                            Index_Var = self.GetIndexPIServedPatientVariable(j, cprime, c, r, u, t, wevpi, w)   
                                            var_name = f"upsilon_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_j_{j}_C'_{cprime}_c_{c}_r_{r}_u_{u}_index_{Index_Var}"
                                            if t not in self.PeriodsInGlobalMIPServedPatient:
                                                self.ServedPatient_Var_SDDP_EVPI[Index_Var] = self.GurobiModel.addVar(obj = 0.0, lb = 0.0, ub = GRB.INFINITY, vtype = GRB.CONTINUOUS, name = var_name)   
            self.GurobiModel.update()  # Ensure all pending model changes are applied
            # for var in self.ServedPatient_Var_SDDP_EVPI.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            ################################# PatientPostponement_Var_SDDP_EVPI #################################
            self.PatientPostponement_Var_SDDP_EVPI = {}
            for w in self.FixedScenarioSet:
                for wevpi in self.EVPIScenarioRange:
                    for t in self.TimePeriodToGoPatientPostponement:
                        for j in self.Instance.InjuryLevelSet:                
                            for c in self.Instance.BloodGPSet:                
                                for u in self.Instance.FacilitySet:                
                                    Index_Var = self.GetIndexPIPatientPostponementVariable(j, c, u, t, wevpi, w)   
                                    var_name = f"zeta_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_j_{j}_c_{c}_u_{u}_index_{Index_Var}"
                                    if t not in self.PeriodsInGlobalMIPPatientPostponement:
                                        self.PatientPostponement_Var_SDDP_EVPI[Index_Var] = self.GurobiModel.addVar(obj = 0.0, lb = 0.0, ub = GRB.INFINITY, vtype = GRB.CONTINUOUS, name = var_name)   
            self.GurobiModel.update()  # Ensure all pending model changes are applied
            # for var in self.PatientPostponement_Var_SDDP_EVPI.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            ################################# PlateletApheresisExtraction_Var_SDDP_EVPI #################################
            self.PlateletApheresisExtraction_Var_SDDP_EVPI = {}
            for w in self.FixedScenarioSet:
                for wevpi in self.EVPIScenarioRange:
                    for t in self.TimePeriodToGoPlateletApheresisExtraction:
                        for c in self.Instance.BloodGPSet:                
                            for u in self.Instance.FacilitySet:                
                                Index_Var = self.GetIndexPIPlateletApheresisExtractionVariable(c, u, t, wevpi, w)   
                                var_name = f"lambda_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_c_{c}_u_{u}_index_{Index_Var}"
                                if t not in self.PeriodsInGlobalMIPPlateletApheresisExtraction:
                                    self.PlateletApheresisExtraction_Var_SDDP_EVPI[Index_Var] = self.GurobiModel.addVar(obj = 0.0, lb = 0.0, ub = GRB.INFINITY, vtype = GRB.CONTINUOUS, name = var_name)   
            self.GurobiModel.update()  # Ensure all pending model changes are applied
            # for var in self.PlateletApheresisExtraction_Var_SDDP_EVPI.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            ################################# PlateletWholeExtraction_Var_SDDP_EVPI #################################
            self.PlateletWholeExtraction_Var_SDDP_EVPI = {}
            for w in self.FixedScenarioSet:
                for wevpi in self.EVPIScenarioRange:
                    for t in self.TimePeriodToGoPlateletWholeExtraction:
                        for c in self.Instance.BloodGPSet:                
                            for h in self.Instance.HospitalSet:                
                                Index_Var = self.GetIndexPIPlateletWholeExtractionVariable(c, h, t, wevpi, w)   
                                var_name = f"Rhovar_EVPI_w_{w}_wevpi_{wevpi}_t_{t}_c_{c}_h_{h}_index_{Index_Var}"
                                if t not in self.PeriodsInGlobalMIPPlateletWholeExtraction:
                                    self.PlateletWholeExtraction_Var_SDDP_EVPI[Index_Var] = self.GurobiModel.addVar(obj = 0.0, lb = 0.0, ub = GRB.INFINITY, vtype = GRB.CONTINUOUS, name = var_name)   
            self.GurobiModel.update()  # Ensure all pending model changes are applied
            # for var in self.PlateletWholeExtraction_Var_SDDP_EVPI.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")

            ################################# EVPI flowfromprevioustage #################################              
            self.flowPLTInvTransHospitalFromPreviousStageWholeProduction_SDDP_EVPI = {}  
            for t in range(0, self.TimeDecisionStage):
                for cprime in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                            Index_Var = self.GetIndexPIFlowPLTInvTransHospitalFromPreviousWholeProduction(cprime, r, h, t) 
                            flow_value = self.GetPIFlowPLTInvTransHospitalFromPreviousStage(cprime, r, h, t)
                            var_name = f"flowPLTInvTransHospitalFromPreviousStageWholeProduction_EVPI_t_{t}_j_{j}_c'_{cprime}_r_{r}_h_{h}_index_{Index_Var}"
                            UB_LB = flow_value
                            self.flowPLTInvTransHospitalFromPreviousStageWholeProduction_SDDP_EVPI[Index_Var] = self.GurobiModel.addVar(obj = 0.0, lb = UB_LB, ub = UB_LB, vtype = GRB.CONTINUOUS, name = var_name)
            self.GurobiModel.update()
            # for var_name, var_obj in self.flowPLTInvTransHospitalFromPreviousStageWholeProduction_SDDP_EVPI.items():
            #     if Constants.Debug: print(f"Var Name: {var_name}, LB: {var_obj.lb}, UB: {var_obj.ub}")
        ################################# EVPI Cost to Go Variable #################################
            self.Cost_To_Go_Var_SDDP_EVPI = {}
            index = 0  # To track the index in the costtogoproba list
            for w in self.FixedScenarioSet:
                Index_Var = self.GetIndexEVPICostToGo(w)
                var_name = f"Cost_To_Go_Var_SDDP_EVPI_w_{w}_index_{Index_Var}"   
                # Create the variable and add it to the dictionary
                self.Cost_To_Go_Var_SDDP_EVPI[Index_Var] = self.GurobiModel.addVar(obj=0.0, lb = 0.0, ub = GRB.INFINITY, vtype=GRB.CONTINUOUS, name=var_name)
                index += 1  # Move to the next coefficient for the next variable
            self.GurobiModel.update()
            # for var in self.Cost_To_Go_Var_SDDP_EVPI.values():
            #     if Constants.Debug: print(f"Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")

    def DefineMIP(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (DefineMIP)")        
        if Constants.Debug: print("Define the MIP of stage %d" % self.DecisionStage)
        
        self.DefineVariables_and_Objective_Function()

        if (self.SDDPOwner.TestIdentifier.Model == Constants.ModelHeuristicMulti_Stage \
            or self.SDDPOwner.TestIdentifier.Method == Constants.Hybrid
            or self.SDDPOwner.EvaluationMode
            #or self.SDDPOwner.TestIdentifier.Method == Constants.MLLocalSearch
            ) and self.IsFirstStage() :
            
                self.ChangeACFEstablishmentToValueOfTwoStage()
                self.ChangeVehicleAssignmentToValueOfTwoStage()
                self.SDDPOwner.HasFixed_ACFEstablishmentVar = True
                self.SDDPOwner.HasFixed_VehicleAssignmentVar = True

        if self.IsFirstStage():
            self.CreateBudgetConstraint()
            self.CreateVehicleAssignmentCapacityConstraint()
            self.CreateVehicleAssignemntACFEstablishmentConstraint()
        
        if not self.IsLastStage():
            self.CreateNrApheresisLimitConstraint()
            self.CreateApheresisACFConstraint()
            self.CreateHospitalTransshipmentCapacityConstraint()
            self.CreateACFTransshipmentCapacityConstraint()
            
        
            for c in self.SDDPCuts:
                c.AddCut()
        
        self.GurobiModel.update()

        if not self.IsFirstStage():
            self.CreateLowMedPriorityPatientFlowConstraint()
            self.CreateHighPriorityPatientFlowConstraint()
            self.CreateLowMedPriorityPatientServiceConstraint()
            self.CreateHighPriorityPatientServiceConstraint()
            self.CreateACFTreatmentCapacityConstraint()
            self.CreateHospitalTreatmentCapacityConstraint()
            self.CreateHospitalPlateletFlowConstraint()
            self.CreateACFPlateletFlowConstraint()
            self.CreatePlateletWastageConstraint()
            self.CreateHospitalRescueVehicleCapacityConstraint()
            self.CreateACFRescueVehicleCapacityConstraint()
            self.CreateACFApheresisCapacityConstraint()
            self.CreateHospitalApheresisCapacityConstraint()
            self.CreateApheresisCapacityDonorsConstraint()
            self.CreateWholeCapacityDonorsConstraint()          

        if (not self.IsLastStage()) and Constants.SDDPUseEVPI:

            self.EVPIScenarioSet = []
            for w in range(Constants.SDDPNrEVPIScenario):
                selected = self.SDDPOwner.CreateRandomScenarioFromSAA()
                selected.Probability = 1.0 / Constants.SDDPNrEVPIScenario
                self.EVPIScenarioSet.append(selected)

            #####################################            
            # Define the desired percentage (40%, 50%, or 60%)
            percentage = 100  # Convex combination of scenarios which are considered in LBF determination! Change this value to 40, 50, or 60 as needed            
            if self.Instance.NrDemandLocations == 15:   
                percentage = Constants.LBFPercentage
            elif self.Instance.NrDemandLocations >= 20:
                percentage = Constants.LBFPercentage

            scenario = self.EVPIScenarioSet[0]

            # Calculate the total demands for each scenario
            scenario_total_demands = []
            for t in self.Instance.TimeBucketSet:
                for w in self.SDDPOwner.SAAScenarioNrSetInPeriod[t]:
                    total_demand = sum(self.SDDPOwner.SetOfSAAScenarioDemand[t][w][j][c][l]
                                    for j in self.Instance.InjuryLevelSet
                                    for c in self.Instance.BloodGPSet
                                    for l in self.Instance.DemandSet)
                    scenario_total_demands.append((w, total_demand))

            # Sort scenarios by total demand in ascending order
            scenario_total_demands.sort(key=lambda x: x[1])

            # Select bottom y% of scenarios
            num_lowest_scenarios = int(len(scenario_total_demands) * (percentage / 100.0))
            lowest_scenarios = scenario_total_demands[:num_lowest_scenarios]
            selected_scenario_ids = [scenario[0] for scenario in lowest_scenarios]

            # Calculate average demands using the lowest y% scenarios
            for t in self.Instance.TimeBucketSet:
                for j in self.Instance.InjuryLevelSet:
                    for c in self.Instance.BloodGPSet:
                        for l in self.Instance.DemandSet:
                            scenario.Demands[t][j][c][l] = sum(self.SDDPOwner.SetOfSAAScenarioDemand[t][w][j][c][l] for w in selected_scenario_ids) \
                                                            / len(selected_scenario_ids)

            if Constants.Debug: print("Average Demands: ", scenario.Demands)

            ####################################################
            # Average HospitalCaps
            scenario = self.EVPIScenarioSet[0]
            for t in self.Instance.TimeBucketSet:
                num_scenarios = len(self.SDDPOwner.SAAScenarioNrSetInPeriod[t])
                num_included_scenarios = int(num_scenarios * (percentage / 100.0))
                selected_scenarios = self.SDDPOwner.SAAScenarioNrSetInPeriod[t][:num_included_scenarios]

                for h in self.Instance.HospitalSet:
                    scenario.HospitalCaps[t][h] = sum(self.SDDPOwner.SetOfSAAScenarioHospitalCapacity[t][w][h] for w in selected_scenario_ids) \
                                                    / len(selected_scenario_ids)

            if Constants.Debug: print("Average HospitalCaps: ", scenario.HospitalCaps)

            # Average WholeDonors
            scenario = self.EVPIScenarioSet[0]
            for t in self.Instance.TimeBucketSet:
                num_scenarios = len(self.SDDPOwner.SAAScenarioNrSetInPeriod[t])
                num_included_scenarios = int(num_scenarios * (percentage / 100.0))
                selected_scenarios = self.SDDPOwner.SAAScenarioNrSetInPeriod[t][:num_included_scenarios]

                for c in self.Instance.BloodGPSet:
                    for h in self.Instance.HospitalSet:
                        scenario.WholeDonors[t][c][h] = sum(self.SDDPOwner.SetOfSAAScenarioWholeDonor[t][w][c][h] for w in selected_scenario_ids) \
                                                        / len(selected_scenario_ids)

            if Constants.Debug: print("Average WholeDonors: ", scenario.WholeDonors)

            # Average ApheresisDonors
            scenario = self.EVPIScenarioSet[0]
            for t in self.Instance.TimeBucketSet:
                num_scenarios = len(self.SDDPOwner.SAAScenarioNrSetInPeriod[t])
                num_included_scenarios = int(num_scenarios * (percentage / 100.0))
                selected_scenarios = self.SDDPOwner.SAAScenarioNrSetInPeriod[t][:num_included_scenarios]

                for c in self.Instance.BloodGPSet:
                    for u in self.Instance.FacilitySet:
                        scenario.ApheresisDonors[t][c][u] = sum(self.SDDPOwner.SetOfSAAScenarioApheresisDonor[t][w][c][u] for w in selected_scenario_ids) \
                                                            / len(selected_scenario_ids)

            if Constants.Debug:  print("Average ApheresisDonors: ", scenario.ApheresisDonors)

            ###############################################
            self.CreatePILowMedPriorityPatientFlowConstraint()
            self.CreatePIHighPriorityPatientFlowConstraint()
            self.CreatePILowMedPriorityPatientServiceConstraint()
            self.CreatePIHighPriorityPatientServiceConstraint()
            self.CreatePIACFTreatmentCapacityConstraint()
            self.CreatePIHospitalTreatmentCapacityConstraint()
            self.CreatePIHospitalPlateletFlowConstraint()
            self.CreatePIACFPlateletFlowConstraint()
            self.CreatePIPlateletWastageConstraint()
            self.CreatePIHospitalRescueVehicleCapacityConstraint()
            self.CreatePIACFRescueVehicleCapacityConstraint()
            self.CreatePINrApheresisLimitConstraint()
            self.CreatePIApheresisACFConstraint()
            self.CreatePIACFApheresisCapacityConstraint()
            self.CreatePIHospitalApheresisCapacityConstraint()
            self.CreatePIApheresisCapacityDonorsConstraint()
            self.CreatePIWholeCapacityDonorsConstraint()
            self.CreatePIHospitalTransshipmentCapacityConstraint()
            self.CreatePIACFTransshipmentCapacityConstraint()
            self.CreatePIEstiamteEVPIConstraints()            

        self.MIPDefined = True

    def ParameterTunning_and_ConfigureGurobiModel(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ParameterTunning_and_ConfigureGurobiModel)")        

        # Set the log file path. This will overwrite the log file for each scenario.
        if Constants.SDDPPrintDebugLPFiles:  # or self.IsFirstStage():
            logFilePath = f"./GurobiLog/stage_{self.DecisionStage}_iter_{self.SDDPOwner.CurrentIteration}.log"
            self.GurobiModel.setParam('LogFile', logFilePath)
        else:
            # Disable logging to the console
            if not Constants.Debug:
                self.GurobiModel.setParam('OutputFlag', Constants.ModelOutputFlag)

        if self.IsFirstStage():
            # For the first stage, ensure logging is enabled and directed to a specific file
            logFilePath = "./GurobiLog/first_stage_log.log"
            self.GurobiModel.setParam('LogFile', logFilePath)
            self.GurobiModel.setParam('OutputFlag', Constants.ModelOutputFlag)

        # Set optimization parameters
        # Gurobi does not use 'advance' parameter like CPLEX, but you can set specific optimization methods or control parallelism
        # self.GurobiModel.setParam('Method', 2)  # For example, setting to Barrier method. Commented out as it's just an example.
        self.GurobiModel.setParam('Threads', 1)  # Control the number of threads
        self.GurobiModel.setParam('FeasibilityTol', 0.00001) 
        self.GurobiModel.update()

    def CheckSolutionAndWrite(self, w):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (CheckSolutionAndWrite)")        

        # Print the solution status
        status = self.GurobiModel.Status
        statusStr = self.GurobiModel.Status
        #if status == GRB.OPTIMAL:
        #    print("Solution status: OPTIMAL")
        #elif status == GRB.INF_OR_UNBD:
        if status == GRB.INF_OR_UNBD:
            print("Solution status: INFEASIBLE OR UNBOUNDED")
        elif status == GRB.INFEASIBLE:
            print("Solution status: INFEASIBLE")
            # Save the LP file for debugging
            lpFilePath = f"./Temp/INFEASIBLEModel_stage_{self.DecisionStage}.lp"
            self.GurobiModel.write(lpFilePath)
            print(f"LP file written to: {lpFilePath}")            
            print("Model is infeasible. Identifying conflicts...")
            # Compute the IIS (Irreducible Inconsistent Subsystem)
            self.GurobiModel.computeIIS()
            for c in self.GurobiModel.getConstrs():
                if c.IISConstr:
                    print(f"Infeasible constraint!!!!!!!!!!!!!!: {c.constrName}")
        elif status == GRB.UNBOUNDED:
            print("Solution status: UNBOUNDED")
        #else:
        #    print(f"Solution status: {statusStr}")

        # Write the solution file if debug flags are set
        if Constants.SDDPPrintDebugLPFiles:  # or self.IsFirstStage():
            solutionFilePath = f"./Temp/Sol_stage_{self.DecisionStage}_iter_{self.SDDPOwner.CurrentIteration}_scenar_{w}.sol"
            self.GurobiModel.write(solutionFilePath)
            print(f"Solution written to: {solutionFilePath}")

    def UpdateMipForTrialInBackward(self, trial):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (UpdateMipForTrialInBackward)") 
        self.CurrentTrialNr = trial

        ################## FlowUnsatisfiedPatientsFromPreviousStage
        for t in self.RangePeriodPatientTransfer:
            for j in self.Instance.InjuryLevelSet:
                for c in self.Instance.BloodGPSet:
                    for l in self.Instance.DemandSet:
                        if j != 0:
                            # Retrieve the variable from the dictionary
                            flowVarIndex = self.GetIndexFlowUnsatisfiedLowMedPatientsFromPreviousStage(j, c, l, t)
                            flowVar = self.flowUnsatisfiedLowMedPatientsFromPreviousStage_SDDP[flowVarIndex]
                        else:
                            # Retrieve the variable from the dictionary
                            flowVarIndex = self.GetIndexFlowUnsatisfiedHighPatientsFromPreviousStage(j, c, l, t)
                            flowVar = self.flowUnsatisfiedHighPatientsFromPreviousStage_SDDP[flowVarIndex]                    
                            
                        # Retrieve the flow value from the previous stage
                        flowValue = self.GetFlowUnsatisfiedPatientsFromPreviousStage(j, c, l, t)

                        # Set the lower and upper bounds of the variable to this flow value
                        flowVar.lb = flowValue
                        flowVar.ub = flowValue
        self.GurobiModel.update()
        
        ################## FlowUnservedPatientsFromPreviousStage
        for t in self.RangePeriodPatientTransfer:
            for j in self.Instance.InjuryLevelSet:
                for c in self.Instance.BloodGPSet:
                    if j!= 0:
                        for u in self.Instance.FacilitySet:
                            # Retrieve the variable from the dictionary
                            flowVarIndex = self.GetIndexFlowUnservedLowMedPatientsFromPreviousStage(j, c, u, t)
                            flowVar = self.flowUnservedLowMedPatientsFromPreviousStage_SDDP[flowVarIndex]
                            
                            # Retrieve the flow value from the previous stage
                            flowValue = self.GetFlowUnservedPatientsFromPreviousStage(j, c, u, t)

                            # Set the lower and upper bounds of the variable to this flow value
                            flowVar.lb = flowValue
                            flowVar.ub = flowValue
                    else:
                        for h in self.Instance.HospitalSet:
                            # Retrieve the variable from the dictionary
                            flowVarIndex = self.GetIndexFlowUnservedHighPatientsFromPreviousStage(j, c, h, t)
                            flowVar = self.flowUnservedHighPatientsFromPreviousStage_SDDP[flowVarIndex]
                            
                            # Retrieve the flow value from the previous stage
                            flowValue = self.GetFlowUnservedPatientsFromPreviousStage(j, c, h, t)

                            # Set the lower and upper bounds of the variable to this flow value
                            flowVar.lb = flowValue
                            flowVar.ub = flowValue
        self.GurobiModel.update()
        
        ################## FlowUnservedPatientCapFromPreviousStage
        for t in self.RangePeriodPatientTransfer:
            for u in self.Instance.FacilitySet:
                if u < self.Instance.NrHospitals:
                    # Retrieve the variable from the dictionary
                    flowVarIndex = self.GetIndexFlowUnservedHospitalFromPreviousStage(u, t)
                    flowVar = self.flowUnservedHospitalFromPreviousStage_SDDP[flowVarIndex]
                else:
                    # Retrieve the variable from the dictionary
                    acf = u - self.Instance.NrHospitals
                    flowVarIndex = self.GetIndexFlowUnservedACFFromPreviousStage(acf, t)
                    flowVar = self.flowUnservedACFFromPreviousStage_SDDP[flowVarIndex]

                # Retrieve the flow value from the previous stage
                flowValue = self.GetFlowUnservedPatientCapFromPreviousStage(u, t)

                # Set the lower and upper bounds of the variable to this flow value
                flowVar.lb = flowValue
                flowVar.ub = flowValue

        self.GurobiModel.update()
        
        ################## FlowPLTInvTransHospitalFromPreviousStage
        for t in self.RangePeriodPatientTransfer:
            for cprime in self.Instance.BloodGPSet:
                for r in self.Instance.PlateletAgeSet:
                    for h in self.Instance.HospitalSet:
                        # Retrieve the variable from the dictionary
                        flowVarIndex = self.GetIndexFlowPLTInvTransHospitalFromPreviousStage(cprime, r, h, t)
                        flowVar = self.flowPLTInvTransHospitalFromPreviousStage_SDDP[flowVarIndex]

                        # Retrieve the flow value from the previous stage
                        flowValue = self.GetFlowPLTInvTransHospitalFromPreviousStage(cprime, r, h, t)

                        # Set the lower and upper bounds of the variable to this flow value
                        flowVar.lb = flowValue
                        flowVar.ub = flowValue
        self.GurobiModel.update()
        
        ################## FlowPLTInvTransACFFromPreviousStage
        for t in self.RangePeriodPatientTransfer:
            for cprime in self.Instance.BloodGPSet:
                for r in self.Instance.PlateletAgeSet:
                    for i in self.Instance.ACFPPointSet:
                        # Retrieve the variable from the dictionary
                        flowVarIndex = self.GetIndexFlowPLTInvTransACFFromPreviousStage(cprime, r, i, t)
                        flowVar = self.flowPLTInvTransACFFromPreviousStage_SDDP[flowVarIndex]

                        # Retrieve the flow value from the previous stage
                        flowValue = self.GetFlowPLTInvTransACFFromPreviousStage(cprime, r, i, t)

                        # Set the lower and upper bounds of the variable to this flow value
                        flowVar.lb = flowValue
                        flowVar.ub = flowValue
        self.GurobiModel.update()
        
        ################## FlowApheresisAssignmentFromPreviousStage
        for t in self.RangePeriodPatientTransfer:
            for i in self.Instance.ACFPPointSet:
                # Retrieve the variable from the dictionary
                flowVarIndex = self.GetIndexFlowApheresisAssignmentFromPreviousStage(i, t)
                flowVar = self.flowApheresisAssignmentFromPreviousStage_SDDP[flowVarIndex]

                # Retrieve the flow value from the previous stage
                flowValue = self.GetFlowApheresisAssignmentFromPreviousStage(i, t)

                # Set the lower and upper bounds of the variable to this flow value
                flowVar.lb = flowValue
                flowVar.ub = flowValue
        self.GurobiModel.update()


        constraintuples = []

        if len(self.SDDPCuts) > 0:

            for cut in self.SDDPCuts:
                if cut.IsActive:
                    index_var = self.GetIndexCutRHSFromPreviousSatge(cut)
                    New_LB_UB = cut.ComputeRHSFromPreviousStage(False)                    

                    variable_to_update = self.CutRHSVariable_SDDP.get(index_var)
                                        
                    variable_to_update.setAttr(GRB.Attr.LB, New_LB_UB)
                    variable_to_update.setAttr(GRB.Attr.UB, New_LB_UB)
                    self.GurobiModel.update()

        if Constants.SDDPModifyBackwardScenarioAtEachIteration:
            for scenario in self.SDDPOwner.SAAScenarioNrSet:
                for i in range(len(self.IndexFlowConstraint)):
                    constr = self.IndexFlowConstraint[i]
                    p = self.ConcernedProductFlowConstraint[i]
                    t = self.ConcernedTimeFlowConstraint[i]
                    tindex = self.GetTimeIndexForInv(p, t)
                    rhs = self.GetRHSFlow(p, tindex, scenario, False)

                    constraintuples.append((constr, rhs))

        if len(constraintuples) > 0:
                self.Cplex.linear_constraints.set_rhs(constraintuples)

    #This function update the MIP for the current stage, taking into account the new value fixedin the previous stage
    def UpdateMIPForStage(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (UpdateMIPForStage)")        

        #if not self.IsFirstStage() and not self.IsLastStage():
        if not self.IsFirstStage():
            
            if Constants.SDDPUseEVPI:

                ############### ACF Treatment Cap RHS Update
                for i in self.Instance.ACFPPointSet:
                    Index_Var = self.GetIndexACFEstablishmentRHS_ACFTreatCapConst(i)
                    New_UBLB_Treat=self.GetACFTreatmentCapacityConstraintRHS(i)
                    variable_to_update = self.ACFTreatmentCapRHS_SDDP.get(Index_Var)
                    variable_to_update.setAttr(GRB.Attr.LB, New_UBLB_Treat)
                    variable_to_update.setAttr(GRB.Attr.UB, New_UBLB_Treat) 
                    self.GurobiModel.update()
                
                ############### Rescue Vehicle Cap RHS Update
                for m in self.Instance.RescueVehicleSet:
                    for i in self.Instance.ACFPPointSet:
                        Index_Var = self.GetIndexVehicleAssignmentRHS_ACFRescVehCapCons(m, i)
                        New_UBLB_Res=self.GetACFRescueVehicleCapacityConstraintRHS(m, i)
                        variable_to_update = self.ACFRescVehicCapRHS_SDDP.get(Index_Var)
                        variable_to_update.setAttr(GRB.Attr.LB, New_UBLB_Res)
                        variable_to_update.setAttr(GRB.Attr.UB, New_UBLB_Res) 
                        self.GurobiModel.update()
                
                if not self.IsLastStage():
                    ############### ACF  Cap RHS Update
                    for i in self.Instance.ACFPPointSet:
                        Index_Var = self.GetIndexACFEstablishmentRHS_ApheresisAssignCon(i)
                        New_UBLB_Aph=self.GetACFApheresisCapConstraintRHS(i)
                        variable_to_update = self.ACFApheresisCapRHS_SDDP.get(Index_Var)
                        variable_to_update.setAttr(GRB.Attr.LB, New_UBLB_Aph)
                        variable_to_update.setAttr(GRB.Attr.UB, New_UBLB_Aph) 
                        self.GurobiModel.update()

                    # Update flow variables from previous stages
                    for cprime in self.Instance.BloodGPSet:
                        for r in self.Instance.PlateletAgeSet:
                            for h in self.Instance.HospitalSet:
                                for t in range(0, self.TimeDecisionStage):
                                    index_var = self.GetIndexPIFlowPLTInvTransHospitalFromPreviousWholeProduction(cprime, r, h, t)
                                    rhs_value = self.GetPIFlowPLTInvTransHospitalFromPreviousStage(cprime, r, h, t)
                                    variable_to_update = self.flowPLTInvTransHospitalFromPreviousStageWholeProduction_SDDP_EVPI.get(index_var)
                                    variable_to_update.setAttr(GRB.Attr.LB, rhs_value)
                                    variable_to_update.setAttr(GRB.Attr.UB, rhs_value)
                                    self.GurobiModel.update()
            else:
                ############### ACF Treatment Cap RHS Update
                for i in self.Instance.ACFPPointSet:
                    Index_Var = self.GetIndexACFEstablishmentRHS_ACFTreatCapConst(i)
                    New_UBLB_Treat=self.GetACFTreatmentCapacityConstraintRHS(i)
                    variable_to_update = self.ACFTreatmentCapRHS_SDDP.get(Index_Var)
                    variable_to_update.setAttr(GRB.Attr.LB, New_UBLB_Treat)
                    variable_to_update.setAttr(GRB.Attr.UB, New_UBLB_Treat) 
                    self.GurobiModel.update()
                
                ############### Rescue Vehicle Cap RHS Update
                for m in self.Instance.RescueVehicleSet:
                    for i in self.Instance.ACFPPointSet:
                        Index_Var = self.GetIndexVehicleAssignmentRHS_ACFRescVehCapCons(m, i)
                        New_UBLB_Res=self.GetACFRescueVehicleCapacityConstraintRHS(m, i)
                        variable_to_update = self.ACFRescVehicCapRHS_SDDP.get(Index_Var)
                        variable_to_update.setAttr(GRB.Attr.LB, New_UBLB_Res)
                        variable_to_update.setAttr(GRB.Attr.UB, New_UBLB_Res) 
                        self.GurobiModel.update()
                
                if not self.IsLastStage():
                    ############### ACF  Cap RHS Update
                    for i in self.Instance.ACFPPointSet:
                        Index_Var = self.GetIndexACFEstablishmentRHS_ApheresisAssignCon(i)
                        New_UBLB_Aph=self.GetACFApheresisCapConstraintRHS(i)
                        variable_to_update = self.ACFApheresisCapRHS_SDDP.get(Index_Var)
                        variable_to_update.setAttr(GRB.Attr.LB, New_UBLB_Aph)
                        variable_to_update.setAttr(GRB.Attr.UB, New_UBLB_Aph) 
                        self.GurobiModel.update()

    #The function below update the constraint of the MIP to correspond to the new scenario
    def UpdateMIPForScenarioAndTrialSolution(self, scenarionr, trial, forward):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (UpdateMIPForScenarioAndTrialSolution)")        

        self.CurrentTrialNr = trial

        constraintuples = []

        ############# updating flow for 'LowMedPriorityPatientFlowConstraint'
        for t in self.RangePeriodPatientTransfer:
            for j in self.Instance.InjuryLevelSet:
                if j != 0:
                    for c in self.Instance.BloodGPSet:
                        for l in self.Instance.DemandSet:
                            Index_Var = self.GetIndexFlowUnsatisfiedLowMedPatientsFromPreviousStage(j, c, l, t)
                            New_LB_UB = self.GetFlowUnsatisfiedPatientsFromPreviousStage(j, c, l, t)
                            variable_to_update = self.flowUnsatisfiedLowMedPatientsFromPreviousStage_SDDP.get(Index_Var)
                            variable_to_update.setAttr(GRB.Attr.LB, New_LB_UB)
                            variable_to_update.setAttr(GRB.Attr.UB, New_LB_UB)
        ############# updating flow for 'HighPriorityPatientFlowConstraint'
        for t in self.RangePeriodPatientTransfer:
            for j in self.Instance.InjuryLevelSet:
                if j == 0:
                    for c in self.Instance.BloodGPSet:
                        for l in self.Instance.DemandSet:
                            Index_Var = self.GetIndexFlowUnsatisfiedHighPatientsFromPreviousStage(j, c, l, t)
                            New_LB_UB = self.GetFlowUnsatisfiedPatientsFromPreviousStage(j, c, l, t)
                            variable_to_update = self.flowUnsatisfiedHighPatientsFromPreviousStage_SDDP.get(Index_Var)
                            variable_to_update.setAttr(GRB.Attr.LB, New_LB_UB)
                            variable_to_update.setAttr(GRB.Attr.UB, New_LB_UB)
        ############# updating flow for 'LowMedPriorityPatientServiceConstraint'
        for t in self.RangePeriodPatientTransfer:
            for j in self.Instance.InjuryLevelSet:
                if j != 0:
                    for c in self.Instance.BloodGPSet:
                        for u in self.Instance.FacilitySet:
                            Index_Var = self.GetIndexFlowUnservedLowMedPatientsFromPreviousStage(j, c, u, t)
                            New_LB_UB = self.GetFlowUnservedPatientsFromPreviousStage(j, c, u, t)
                            variable_to_update = self.flowUnservedLowMedPatientsFromPreviousStage_SDDP.get(Index_Var)
                            variable_to_update.setAttr(GRB.Attr.LB, New_LB_UB)
                            variable_to_update.setAttr(GRB.Attr.UB, New_LB_UB)
        ############# updating flow for 'HighPriorityPatientServiceConstraint'
        for t in self.RangePeriodPatientTransfer:
            for j in self.Instance.InjuryLevelSet:
                if j == 0:
                    for c in self.Instance.BloodGPSet:
                        for h in self.Instance.HospitalSet:
                            Index_Var = self.GetIndexFlowUnservedHighPatientsFromPreviousStage(j, c, h, t)
                            New_LB_UB = self.GetFlowUnservedPatientsFromPreviousStage(j, c, u, t)
                            variable_to_update = self.flowUnservedHighPatientsFromPreviousStage_SDDP.get(Index_Var)
                            variable_to_update.setAttr(GRB.Attr.LB, New_LB_UB)
                            variable_to_update.setAttr(GRB.Attr.UB, New_LB_UB)
        ############# updating flow for 'ACFTreatmentCapacityConstraint'
        for t in self.RangePeriodPatientTransfer:
            for i in self.Instance.ACFPPointSet:
                Index_Var = self.GetIndexFlowUnservedACFFromPreviousStage(i, t)
                New_LB_UB = self.GetFlowUnservedPatientCapFromPreviousStage(self.Instance.NrHospitals + i, t)
                variable_to_update = self.flowUnservedACFFromPreviousStage_SDDP.get(Index_Var)
                variable_to_update.setAttr(GRB.Attr.LB, New_LB_UB)
                variable_to_update.setAttr(GRB.Attr.UB, New_LB_UB)
        ############# updating flow for 'HospitalTreatmentCapacityConstraint'
        for t in self.RangePeriodPatientTransfer:
            for h in self.Instance.HospitalSet:
                Index_Var = self.GetIndexFlowUnservedHospitalFromPreviousStage(h, t)
                New_LB_UB = self.GetFlowUnservedPatientCapFromPreviousStage(h, t)
                variable_to_update = self.flowUnservedHospitalFromPreviousStage_SDDP.get(Index_Var)
                variable_to_update.setAttr(GRB.Attr.LB, New_LB_UB)
                variable_to_update.setAttr(GRB.Attr.UB, New_LB_UB)
        ############# updating flow for 'HospitalPlateletFlowConstraint'
        for t in self.RangePeriodPatientTransfer:
            for cprime in self.Instance.BloodGPSet:
                for r in self.Instance.PlateletAgeSet:
                    for h in self.Instance.HospitalSet:
                        Index_Var = self.GetIndexFlowPLTInvTransHospitalFromPreviousStage(cprime, r, h, t)
                        New_LB_UB = self.GetFlowPLTInvTransHospitalFromPreviousStage(cprime, r, h, t)
                        variable_to_update = self.flowPLTInvTransHospitalFromPreviousStage_SDDP.get(Index_Var)
                        variable_to_update.setAttr(GRB.Attr.LB, New_LB_UB)
                        variable_to_update.setAttr(GRB.Attr.UB, New_LB_UB)
        ############# updating flow for 'ACFPlateletFlowConstraint'
        for t in self.RangePeriodPatientTransfer:
            for cprime in self.Instance.BloodGPSet:
                for r in self.Instance.PlateletAgeSet:
                    for i in self.Instance.ACFPPointSet:
                        Index_Var = self.GetIndexFlowPLTInvTransACFFromPreviousStage(cprime, r, i, t)
                        New_LB_UB = self.GetFlowPLTInvTransACFFromPreviousStage(cprime, r, i, t)
                        variable_to_update = self.flowPLTInvTransACFFromPreviousStage_SDDP.get(Index_Var)
                        variable_to_update.setAttr(GRB.Attr.LB, New_LB_UB)
                        variable_to_update.setAttr(GRB.Attr.UB, New_LB_UB)
        ############# updating flow for 'ACFApheresisCapacityConstraint'
        for t in self.RangePeriodPatientTransfer:
            for i in self.Instance.ACFPPointSet:
                Index_Var = self.GetIndexFlowApheresisAssignmentFromPreviousStage(i, t)
                New_LB_UB = self.GetFlowApheresisAssignmentFromPreviousStage(i, t)
                variable_to_update = self.flowApheresisAssignmentFromPreviousStage_SDDP.get(Index_Var)
                variable_to_update.setAttr(GRB.Attr.LB, New_LB_UB)
                variable_to_update.setAttr(GRB.Attr.UB, New_LB_UB)


        if Constants.SDDPUseEVPI and not self.IsFirstStage() and not self.IsLastStage():
            for t in range(0, self.TimeDecisionStage):
                for cprime in self.Instance.BloodGPSet:
                    for r in self.Instance.PlateletAgeSet:
                        for h in self.Instance.HospitalSet:
                    
                            Index_Var = self.GetIndexPIFlowPLTInvTransHospitalFromPreviousWholeProduction(cprime, r, h, t)
                            New_LB_UB = self.GetPIFlowPLTInvTransHospitalFromPreviousStage(cprime, r, h, t)
                            
                            variable_to_update = self.flowPLTInvTransHospitalFromPreviousStageWholeProduction_SDDP_EVPI.get(Index_Var)

                            if variable_to_update is not None:
                                variable_to_update.setAttr(GRB.Attr.LB, New_LB_UB)
                                variable_to_update.setAttr(GRB.Attr.UB, New_LB_UB)
                                self.GurobiModel.update() 

        ############################## Updating the Uncertain RHS of Constraint 'LowMedPriorityPatientFlowConstraint'
        for i in range(len(self.IndexLowMedPriorityPatientFlowConstraint)):
            # Retrieve the constraint object directly, assuming it was stored correctly
            constr_obj = self.LowMedPriorityPatientFlowConstraint_Objects[i]
            j = self.ConcernedInjuryLowMedPriorityPatientFlowConstraint[i]
            c = self.ConcernedBloodGPLowMedPriorityPatientFlowConstraint[i]
            l = self.ConcernedDemandLowMedPriorityPatientFlowConstraint[i]
            t = self.ConcernedTimeLowMedPriorityPatientFlowConstraint[i]
            tindex = self.GetTimeIndexForPatientTransfer(t)
            rhs = self.GetRHSFlow_Demand(j, c, l, tindex, scenarionr, forward)
            # Update the RHS of the constraint
            self.GurobiModel.setAttr("RHS", [constr_obj], [rhs])
            self.GurobiModel.update()  
        
        ############################## Updating the Uncertain RHS of Constraint 'HighPriorityPatientFlowConstraint'
        for i in range(len(self.IndexHighPriorityPatientFlowConstraint)):
            # Retrieve the constraint object directly, assuming it was stored correctly
            constr_obj = self.HighPriorityPatientFlowConstraint_Objects[i]
            j = self.ConcernedInjuryHighPriorityPatientFlowConstraint[i]
            c = self.ConcernedBloodGPHighPriorityPatientFlowConstraint[i]
            l = self.ConcernedDemandHighPriorityPatientFlowConstraint[i]
            t = self.ConcernedTimeHighPriorityPatientFlowConstraint[i]
            tindex = self.GetTimeIndexForPatientTransfer(t)
            rhs = self.GetRHSFlow_Demand(j, c, l, tindex, scenarionr, forward)
            # Update the RHS of the constraint
            self.GurobiModel.setAttr("RHS", [constr_obj], [rhs])
            self.GurobiModel.update()
        
        ############################## Updating the Uncertain RHS of Constraint 'HospitalTreatmentCapacityConstraint'
        for i in range(len(self.IndexHospitalTreatmentCapacityConstraint)):
            # Retrieve the constraint object directly, assuming it was stored correctly
            constr_obj = self.HospitalTreatmentCapacityConstraint_Objects[i]
            h = self.ConcernedHospitalHospitalTreatmentCapacityConstraint[i]
            t = self.ConcernedTimeHospitalTreatmentCapacityConstraint[i]
            tindex = self.GetTimeIndexForPatientTransfer(t)
            rhs = self.GetRHSFlow_HospitalCap(h, tindex, scenarionr, forward)
            # Update the RHS of the constraint
            self.GurobiModel.setAttr("RHS", [constr_obj], [rhs])
            self.GurobiModel.update()  
        
        ############################## Updating the Uncertain RHS of Constraint 'ApheresisCapacityDonorsConstraint'
        for i in range(len(self.IndexApheresisCapacityDonorsConstraint)):
            # Retrieve the constraint object directly, assuming it was stored correctly
            constr_obj = self.ApheresisCapacityDonorsConstraint_Objects[i]
            c = self.ConcernedBloodGPApheresisCapacityDonorsConstraint[i]
            u = self.ConcernedFacilityApheresisCapacityDonorsConstraint[i]
            t = self.ConcernedTimeApheresisCapacityDonorsConstraint[i]
            tindex = self.GetTimeIndexForPatientTransfer(t)
            rhs = self.GetRHSFlow_ApheresisDonor(c, u, tindex, scenarionr, forward)
            # Update the RHS of the constraint
            self.GurobiModel.setAttr("RHS", [constr_obj], [rhs])
            self.GurobiModel.update()  

        ############################## Updating the Uncertain RHS of Constraint 'WholeCapacityDonorsConstraint'
        for i in range(len(self.IndexWholeCapacityDonorsConstraint)):
            # Retrieve the constraint object directly, assuming it was stored correctly
            constr_obj = self.WholeCapacityDonorsConstraint_Objects[i]
            c = self.ConcernedBloodGPWholeCapacityDonorsConstraint[i]
            h = self.ConcernedHospitalWholeCapacityDonorsConstraint[i]
            t = self.ConcernedTimeWholeCapacityDonorsConstraint[i]
            tindex = self.GetTimeIndexForPatientTransfer(t)
            rhs = self.GetRHSFlow_WholeDonor(c, h, tindex, scenarionr, forward)
            # Update the RHS of the constraint
            self.GurobiModel.setAttr("RHS", [constr_obj], [rhs])
            self.GurobiModel.update()  
                    

        if len(self.SDDPCuts) > 0:
            for cut in self.SDDPCuts:
                if cut.IsActive:
                    Index_Var = self.GetIndexCutRHSFromPreviousSatge(cut)
                    New_LB_UB = cut.ComputeRHSFromPreviousStage(forward)
                    variable_to_update = self.CutRHSVariable_SDDP.get(Index_Var)
                    variable_to_update.setAttr(GRB.Attr.LB, New_LB_UB)
                    variable_to_update.setAttr(GRB.Attr.UB, New_LB_UB)
        
        
        if len(constraintuples) > 0:
           self.Cplex.linear_constraints.set_rhs(constraintuples)

    #This run the MIP of the current stage (one for each scenario)
    def RunForwardPassMIP(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (RunForwardPassMIP)")
        if Constants.Debug: print(" Build the MIP of stage %d" %self.DecisionStage)

        averagecostofthesubproblem = 0
        if self.MIPDefined:
            self.UpdateMIPForStage()

        if self.IsFirstStage():
            consideredscenario = [0]
        else:
            consideredscenario = range(len(self.SDDPOwner.CurrentSetOfTrialScenarios))

        for w in consideredscenario:
            
            if not self.MIPDefined:
                self.CurrentTrialNr = w
                self.DefineMIP()
            else:
                self.UpdateMIPForScenarioAndTrialSolution(w, w, True)

            self.ParameterTunning_and_ConfigureGurobiModel()

            self.GurobiModel.optimize()

            self.CheckSolutionAndWrite(w)

            if Constants.SDDPPrintDebugLPFiles:  # or self.IsFirstStage():
                self.GurobiModel.write("./Temp/Stage_%d_iter_%d_scenar_%d.lp" % (self.DecisionStage, self.SDDPOwner.CurrentIteration, w))

            if self.IsFirstStage():
                self.CurrentTrialNr = 0
                self.SaveSolutionForScenario()
                self.CopyDecisionOfScenario0ToAllScenario()
            else:
                self.SaveSolutionForScenario()

            averagecostofthesubproblem += self.GurobiModel.ObjVal * self.SDDPOwner.CurrentSetOfTrialScenarios[w].Probability
            
            #update the last iteration where dual were used
            if Constants.SDDPCleanCuts and not self.IsLastStage() and len(self.IndexCutConstraint)>0:
                sol = self.Cplex.solution
                duals = sol.get_linear_slacks(self.IndexCutConstraint)
                for i in range(len(duals)):
                    if duals[i] != 0:
                        c = self.ConcernedCutinConstraint[i]
                        c.LastIterationWithDual = self.SDDPOwner.CurrentIteration

    def CopyDecisionOfScenario0ToAllScenario(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (CopyDecisionOfScenario0ToAllScenario)")

        for w2 in range(1, len(self.SDDPOwner.CurrentSetOfTrialScenarios)):
            self.CurrentTrialNr = w2
            self.StageCostPerScenarioWithCostoGo[self.CurrentTrialNr] = self.StageCostPerScenarioWithCostoGo[0]
            self.PartialCostPerScenario[self.CurrentTrialNr] = self.PartialCostPerScenario[0]
            
            self.ACFEstablishmentValues[self.CurrentTrialNr] = self.ACFEstablishmentValues[0]
            self.VehicleAssignmentValues[self.CurrentTrialNr] = self.VehicleAssignmentValues[0]

            self.ApheresisAssignmentValues[self.CurrentTrialNr] = self.ApheresisAssignmentValues[0]
            self.TransshipmentHIValues[self.CurrentTrialNr] = self.TransshipmentHIValues[0]
            self.TransshipmentIIValues[self.CurrentTrialNr] = self.TransshipmentIIValues[0]
            self.TransshipmentHHValues[self.CurrentTrialNr] = self.TransshipmentHHValues[0]

            self.PatientTransferValues[self.CurrentTrialNr] = self.PatientTransferValues[0]
            self.UnsatisfiedPatientsValues[self.CurrentTrialNr] = self.UnsatisfiedPatientsValues[0]
            self.PlateletInventoryValues[self.CurrentTrialNr] = self.PlateletInventoryValues[0]
            self.OutdatedPlateletValues[self.CurrentTrialNr] = self.OutdatedPlateletValues[0]
            self.ServedPatientValues[self.CurrentTrialNr] = self.ServedPatientValues[0]
            self.PatientPostponementValues[self.CurrentTrialNr] = self.PatientPostponementValues[0]
            self.PlateletApheresisExtractionValues[self.CurrentTrialNr] = self.PlateletApheresisExtractionValues[0]
            self.PlateletWholeExtractionValues[self.CurrentTrialNr] = self.PlateletWholeExtractionValues[0]

    def GetVariableValue(self, model):
        if Constants.Debug:  print("\n We are in 'SDDPStage' Class -- (GetVariableValue)")

        if self.IsFirstStage():
            
            ######################################## ACFEstablishmentValues
            scenario_acfestablishment_values = []  
            for i in self.Instance.ACFPPointSet:
                Index_Var = self.GetIndexACFEstablishmentVariable(i)
                variable_value = self.ACFEstablishment_Var_SDDP[Index_Var].X
                if(variable_value < 0.5 ):
                    variable_value = 0
                else:
                    variable_value = 1
                scenario_acfestablishment_values.append(variable_value)
            # Assign the structured list directly to the specified trial number
            self.ACFEstablishmentValues[self.CurrentTrialNr] = scenario_acfestablishment_values
            
            ######################################## VehicleAssignmentValues
            scenario_vehicleassignment_values = []  
            for m in self.Instance.RescueVehicleSet:
                vehicle_vehicleassignment_values = []
                for i in self.Instance.ACFPPointSet:
                    Index_Var = self.GetIndexVehicleAssignmentVariable(m, i)
                    variable_value = self.VehicleAssignment_Var_SDDP[Index_Var].X
                    if abs(variable_value) < 1e-5:
                        variable_value = 0
                    vehicle_vehicleassignment_values.append(variable_value)
                scenario_vehicleassignment_values.append(vehicle_vehicleassignment_values)
            # Assign the structured list directly to the specified trial number
            self.VehicleAssignmentValues[self.CurrentTrialNr] = scenario_vehicleassignment_values

        if len(self.RangePeriodApheresisAssignment) > 0:
                  
            ######################################## ApheresisAssignmentValues
            scenario_values = []  
            for t in self.RangePeriodApheresisAssignment:
                time_period_values = []  
                for i in self.Instance.ACFPPointSet:
                    Index_Var = self.GetIndexApheresisAssignmentVariable(i, t, w=0)  # Assuming w=0 is your scenario index here
                    variable = self.ApheresisAssignment_Var_SDDP[Index_Var]
                    variable_value = variable.X
                    if abs(variable_value) < 1e-5:
                        variable_value = 0                    
                    time_period_values.append(variable_value)
                scenario_values.append(time_period_values)        
            self.ApheresisAssignmentValues[self.CurrentTrialNr] = scenario_values
            
            ######################################## TransshipmentHIValues
            scenario_values = []
            for t in self.RangePeriodApheresisAssignment:
                time_values = []
                for c in self.Instance.BloodGPSet:
                    bloodgp_values = []
                    for r in self.Instance.PlateletAgeSet:
                        plateletage_values = []
                        for h in self.Instance.HospitalSet:  
                            hospital_values = []
                            for i in self.Instance.ACFPPointSet:
                                Index_Var = self.GetIndexTransshipmentHIVariable(c, r, h, i, t, w=0)
                                variable = self.TransshipmentHI_Var_SDDP[Index_Var]
                                variable_value = variable.X
                                if abs(variable_value) < 1e-5:
                                    variable_value = 0                                
                                hospital_values.append(variable_value)
                            plateletage_values.append(hospital_values)
                        bloodgp_values.append(plateletage_values)
                    time_values.append(bloodgp_values)
                scenario_values.append(time_values)
            self.TransshipmentHIValues[self.CurrentTrialNr] = scenario_values
            
            ######################################## TransshipmentIIValues
            scenario_values = []
            for t in self.RangePeriodApheresisAssignment:
                time_period_values = []
                for c in self.Instance.BloodGPSet:
                    bloodgp_values = []
                    for r in self.Instance.PlateletAgeSet:
                        plateletage_values = []
                        for i in self.Instance.ACFPPointSet:  
                            acf_values = []
                            for iprime in self.Instance.ACFPPointSet:
                                Index_Var = self.GetIndexTransshipmentIIVariable(c, r, i, iprime, t, w=0)
                                variable = self.TransshipmentII_Var_SDDP[Index_Var]
                                variable_value = variable.X
                                if abs(variable_value) < 1e-5:
                                    variable_value = 0                                 
                                acf_values.append(variable_value)
                            plateletage_values.append(acf_values)
                        bloodgp_values.append(plateletage_values)
                    time_period_values.append(bloodgp_values)
                scenario_values.append(time_period_values)
            self.TransshipmentIIValues[self.CurrentTrialNr] = scenario_values

            ######################################## TransshipmentHHValues
            scenario_values = []
            for t in self.RangePeriodApheresisAssignment:
                time_period_values = []
                for c in self.Instance.BloodGPSet:
                    bloodgp_values = []
                    for r in self.Instance.PlateletAgeSet:
                        plateletage_values = []
                        for h in self.Instance.HospitalSet:  
                            hospital_values = []
                            for hprime in self.Instance.HospitalSet:
                                Index_Var = self.GetIndexTransshipmentHHVariable(c, r, h, hprime, t, w=0)
                                variable = self.TransshipmentHH_Var_SDDP[Index_Var]
                                variable_value = variable.X
                                if abs(variable_value) < 1e-5:
                                    variable_value = 0                           
                                hospital_values.append(variable_value)
                            plateletage_values.append(hospital_values)
                        bloodgp_values.append(plateletage_values)
                    time_period_values.append(bloodgp_values)
                scenario_values.append(time_period_values)
            self.TransshipmentHHValues[self.CurrentTrialNr] = scenario_values
        
        if len(self.RangePeriodPatientTransfer) > 0:
            
            ######################################## PatientTransferValues
            scenario_values = []
            for t in self.RangePeriodPatientTransfer:
                time_period_values = []
                for j in self.Instance.InjuryLevelSet:
                    injury_values = []
                    for c in self.Instance.BloodGPSet:
                        bloodgp_values = []
                        for l in self.Instance.DemandSet:
                            demand_values = []
                            for u in self.Instance.FacilitySet:
                                facility_values = []
                                for m in self.Instance.RescueVehicleSet:  
                                    Index_Var = self.GetIndexPatientTransferVariable(j, c, l, u, m, t, w=0)  
                                    variable = self.PatientTransfer_Var_SDDP[Index_Var]
                                    variable_value = variable.X
                                    if abs(variable_value) < 1e-5:
                                        variable_value = 0                                     
                                    facility_values.append(variable_value)
                                demand_values.append(facility_values)
                            bloodgp_values.append(demand_values)
                        injury_values.append(bloodgp_values)
                    time_period_values.append(injury_values)
                scenario_values.append(time_period_values)
            self.PatientTransferValues[self.CurrentTrialNr] = scenario_values

            ######################################## UnsatisfiedPatientsValues
            scenario_values = []
            for t in self.RangePeriodPatientTransfer:
                time_period_values = []
                for j in self.Instance.InjuryLevelSet:
                    injury_values = []
                    for c in self.Instance.BloodGPSet:
                        bloodgp_values = []
                        for l in self.Instance.DemandSet:
                            Index_Var = self.GetIndexUnsatisfiedPatientsVariable(j, c, l, t, w=0)  
                            variable = self.UnsatisfiedPatients_Var_SDDP[Index_Var]
                            variable_value = variable.X
                            if abs(variable_value) < 1e-5:
                                variable_value = 0                              
                            bloodgp_values.append(variable_value)
                        injury_values.append(bloodgp_values)
                    time_period_values.append(injury_values)
                scenario_values.append(time_period_values)
            self.UnsatisfiedPatientsValues[self.CurrentTrialNr] = scenario_values
            
            ######################################## PlateletInventoryValues
            scenario_values = []
            for t in self.RangePeriodPatientTransfer:
                time_period_values = []
                for c in self.Instance.BloodGPSet:
                    bloodgp_values = []
                    for r in self.Instance.PlateletAgeSet:
                        pltage_values = []
                        for u in self.Instance.FacilitySet:
                            Index_Var = self.GetIndexPlateletInventoryVariable(c, r, u, t, w=0)  
                            variable = self.PlateletInventory_Var_SDDP[Index_Var]
                            variable_value = variable.X
                            if abs(variable_value) < 1e-5:
                                variable_value = 0                              
                            pltage_values.append(variable_value)
                        bloodgp_values.append(pltage_values)
                    time_period_values.append(bloodgp_values)
                scenario_values.append(time_period_values)
            self.PlateletInventoryValues[self.CurrentTrialNr] = scenario_values

            ######################################## OutdatedPlateletValues
            scenario_values = []  
            for t in self.RangePeriodPatientTransfer:
                time_period_values = []
                for u in self.Instance.FacilitySet:
                    Index_Var = self.GetIndexOutdatedPlateletVariable(u, t, w=0)  # Assuming w=0 is your specific scenario index
                    variable_value = self.OutdatedPlatelet_Var_SDDP[Index_Var].X
                    if abs(variable_value) < 1e-5:
                        variable_value = 0                     
                    time_period_values.append(variable_value)
                scenario_values.append(time_period_values)
            self.OutdatedPlateletValues[self.CurrentTrialNr] = scenario_values  
            
            ######################################## ServedPatientValues
            scenario_values = []
            for t in self.RangePeriodPatientTransfer:
                time_period_values = []
                for j in self.Instance.InjuryLevelSet:
                    injury_values = []
                    for cprime in self.Instance.BloodGPSet:
                        bloodgp_values = []
                        for c in self.Instance.BloodGPSet:
                            bloodgp2_values = []
                            for r in self.Instance.PlateletAgeSet:
                                pltage_values = []
                                for u in self.Instance.FacilitySet:  
                                    Index_Var = self.GetIndexServedPatientVariable(j, cprime, c, r, u, t, w=0)  
                                    variable = self.ServedPatient_Var_SDDP[Index_Var]
                                    variable_value = variable.X
                                    if abs(variable_value) < 1e-5:
                                        variable_value = 0                          
                                    pltage_values.append(variable_value)
                                bloodgp2_values.append(pltage_values)
                            bloodgp_values.append(bloodgp2_values)
                        injury_values.append(bloodgp_values)
                    time_period_values.append(injury_values)
                scenario_values.append(time_period_values)
            self.ServedPatientValues[self.CurrentTrialNr] = scenario_values

            ######################################## PatientPostponementValues
            scenario_values = []
            for t in self.RangePeriodPatientTransfer:
                time_period_values = []
                for j in self.Instance.InjuryLevelSet:
                    injury_values = []
                    for c in self.Instance.BloodGPSet:
                        bloodgp_values = []
                        for u in self.Instance.FacilitySet:
                            Index_Var = self.GetIndexPatientPostponementVariable(j, c, u, t, w=0)  
                            variable = self.PatientPostponement_Var_SDDP[Index_Var]
                            variable_value = variable.X
                            if abs(variable_value) < 1e-5:
                                variable_value = 0                              
                            bloodgp_values.append(variable_value)
                        injury_values.append(bloodgp_values)
                    time_period_values.append(injury_values)
                scenario_values.append(time_period_values)
            self.PatientPostponementValues[self.CurrentTrialNr] = scenario_values

            ######################################## PlateletApheresisExtractionValues
            scenario_values = []
            for t in self.RangePeriodPatientTransfer:
                time_period_values = []
                for c in self.Instance.BloodGPSet:
                    bloodgp_values = []
                    for u in self.Instance.FacilitySet:
                        Index_Var = self.GetIndexPlateletApheresisExtractionVariable(c, u, t, w=0)  
                        variable = self.PlateletApheresisExtraction_Var_SDDP[Index_Var]
                        variable_value = variable.X
                        if abs(variable_value) < 1e-5:
                            variable_value = 0                      
                        bloodgp_values.append(variable_value)
                    time_period_values.append(bloodgp_values)
                scenario_values.append(time_period_values)
            self.PlateletApheresisExtractionValues[self.CurrentTrialNr] = scenario_values

            ######################################## PlateletWholeExtractionValues
            scenario_values = []
            for t in self.RangePeriodPatientTransfer:
                time_period_values = []
                for c in self.Instance.BloodGPSet:
                    bloodgp_values = []
                    for h in self.Instance.HospitalSet:
                        Index_Var = self.GetIndexPlateletWholeExtractionVariable(c, h, t, w=0)  
                        variable = self.PlateletWholeExtraction_Var_SDDP[Index_Var]
                        variable_value = variable.X
                        if abs(variable_value) < 1e-5:
                            variable_value = 0                          
                        bloodgp_values.append(variable_value)
                    time_period_values.append(bloodgp_values)
                scenario_values.append(time_period_values)
            self.PlateletWholeExtractionValues[self.CurrentTrialNr] = scenario_values
            
    # This function run the MIP of the current stage
    def SaveSolutionForScenario(self):
        if Constants.Debug:  print("\n We are in 'SDDPStage' Class -- (SaveSolutionForScenario)")

        if Constants.SDDPPrintDebugLPFiles:
            self.GurobiModel.write("./Temp/FCTPsolution.sol")
        
        # Directly pass the model to SaveSolutionFromSol since there's no separate solution object in Gurobi
        self.SaveSolutionFromSol(self.GurobiModel)
    
    def SaveSolutionFromSol(self, model):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (SaveSolutionFromSol)")
        
        # Get objective value directly from the model
        obj = model.ObjVal
        self.StageCostPerScenarioWithCostoGo[self.CurrentTrialNr] = obj
        self.StageCostPerScenarioWithoutCostoGo[self.CurrentTrialNr] = self.StageCostPerScenarioWithCostoGo[self.CurrentTrialNr]   

        if not self.IsLastStage():
            if Constants.SDDPUseMultiCut:
                cost_to_go_sum = 0
                for w in self.FixedScenarioSet:
                    for futurescenario in self.FuturScenario:
                        cost_to_go_sum += self.FuturScenarProba[w] * self.Cost_To_Go_Var_SDDP[self.GetIndexCostToGo(w, futurescenario)].X
                self.StageCostPerScenarioWithoutCostoGo[self.CurrentTrialNr] = self.StageCostPerScenarioWithCostoGo[self.CurrentTrialNr] - cost_to_go_sum
            else:
                cost_to_go_sum = 0
                for w in self.FixedScenarioSet:
                    cost_to_go_sum += self.FuturScenarProba[w] * self.Cost_To_Go_Var_SDDP[self.GetIndexCostToGo(w, 0)].X
                self.StageCostPerScenarioWithoutCostoGo[self.CurrentTrialNr] = self.StageCostPerScenarioWithCostoGo[self.CurrentTrialNr] - cost_to_go_sum

        if self.IsFirstStage():
            self.PartialCostPerScenario[self.CurrentTrialNr] = self.StageCostPerScenarioWithoutCostoGo[self.CurrentTrialNr]
        else:
            self.PartialCostPerScenario[self.CurrentTrialNr] = self.StageCostPerScenarioWithoutCostoGo[self.CurrentTrialNr] \
                                                                + self.PreviousSDDPStage.PartialCostPerScenario[self.CurrentTrialNr]
        
        self.GetVariableValue(model)

        if Constants.Debug:
            cotogo = 0
            if not self.IsLastStage():
                cotogo_var = model.getVarByName("cost_to_go_var_name_here")  
                cotogo = cotogo_var.X if cotogo_var else 0

            if Constants.Debug: print(f"******************** Solution at stage {self.DecisionStage} cost: {obj} cost to go {cotogo} *********************")

    def ImproveCutFromSolution(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ImproveCutFromSolution)")

        self.IncreaseCutWithLowMedPriorityPatientFlowDual(cuts, GurobiModel)
        self.IncreaseCutWithHighPriorityPatientFlowDual(cuts, GurobiModel)
        self.IncreaseCutWithLowMedPriorityPatientServiceDual(cuts, GurobiModel)
        self.IncreaseCutWithHighPriorityPatientServiceDual(cuts, GurobiModel)
        self.IncreaseCutWithACFTreatmentCapacityDual(cuts, GurobiModel)
        self.IncreaseCutWithHospitalTreatmentCapacityDual(cuts, GurobiModel)
        self.IncreaseCutWithHospitalPlateletFlowDual(cuts, GurobiModel)
        self.IncreaseCutWithACFPlateletFlowDual(cuts, GurobiModel)
        self.IncreaseCutWithHospitalRescueVehicleCapacityDual(cuts, GurobiModel)
        self.IncreaseCutWithACFRescueVehicleCapacityDual(cuts, GurobiModel)
        self.IncreaseCutWithACFApheresisCapacityDual(cuts, GurobiModel)
        self.IncreaseCutWithHospitalApheresisCapacityDual(cuts, GurobiModel)
        self.IncreaseCutWithApheresisCapacityDonorsDual(cuts, GurobiModel)
        self.IncreaseCutWithWholeCapacityDonorsDual(cuts, GurobiModel)
        
        if not self.IsLastStage():
            self.IncreaseCutWithNrApheresisLimitDual(cuts, GurobiModel)
            self.IncreaseCutWithApheresisACFDual(cuts, GurobiModel)
            self.IncreaseCutWithCutDuals(cuts, GurobiModel)

            if Constants.SDDPUseEVPI:
                self.IncreaseCutWithPILowMedPriorityPatientFlowDual(cuts, GurobiModel)
                self.IncreaseCutWithPIHighPriorityPatientFlowDual(cuts, GurobiModel)
                self.IncreaseCutWithPILowMedPriorityPatientServiceDual(cuts, GurobiModel)
                self.IncreaseCutWithPIHighPriorityPatientServiceDual(cuts, GurobiModel)
                self.IncreaseCutWithPIACFTreatmentCapacityDual(cuts, GurobiModel)
                self.IncreaseCutWithPIHospitalTreatmentCapacityDual(cuts, GurobiModel)
                self.IncreaseCutWithPIHospitalPlateletFlowDual(cuts, GurobiModel)
                self.IncreaseCutWithPIACFPlateletFlowDual(cuts, GurobiModel)
                self.IncreaseCutWithPIHospitalRescueVehicleCapacityDual(cuts, GurobiModel)
                self.IncreaseCutWithPIACFRescueVehicleCapacityDual(cuts, GurobiModel)
                self.IncreaseCutWithPIACFApheresisCapacityDual(cuts, GurobiModel)
                self.IncreaseCutWithPIHospitalApheresisCapacityDual(cuts, GurobiModel)
                self.IncreaseCutWithPIApheresisCapacityDonorsDual(cuts, GurobiModel)
                self.IncreaseCutWithPIWholeCapacityDonorsDual(cuts, GurobiModel)

                if len(self.TimePeriodToGoApheresisAssignment) >= 1:
                    self.IncreaseCutWithPINrApheresisLimitDual(cuts, GurobiModel)
                    self.IncreaseCutWithPIApheresisACFDual(cuts, GurobiModel)

    #Generate the Benders cut
    def GernerateCut(self, trial, returncut=False):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (GernerateCut)")
        if Constants.Debug: print("Generating a cut and adding it to stage %d" % self.PreviousSDDPStage.DecisionStage)

        if not self.IsFirstStage():
            # Re-run the MIP to take into account the just added cut
            # Solve the problem for each scenario
            self.UpdateMIPForStage()

            cutsets = []
            avgcostssubprob = []

            for trial in self.SDDPOwner.ConsideredTrialForBackward:

                    self.SAAStageCostPerScenarioWithoutCostoGopertrial[trial] = 0
                    self.CurrentTrialNr = trial
                    # Create a cute for the previous stage problem
                    averagecostofthesubproblem = 0

                    # Update the MIP model for the current trial in the backward pass
                    if Constants.Debug: print(f"Updating MIP for trial {trial} in backward pass for stage {self.DecisionStage}")

                    self.UpdateMipForTrialInBackward(trial) 

                    if Constants.SDDPPrintDebugLPFiles:
                        if Constants.Debug: print("Resolve for backward pass the MIP of stage %d " % (self.DecisionStage))
                        self.GurobiModel.write("./Temp/backward_stage_%d_iter_%d.lp"
                                         % (self.DecisionStage, self.SDDPOwner.CurrentIteration))

                    if not Constants.Debug:
                        self.GurobiModel.setParam('OutputFlag', Constants.ModelOutputFlag)

                    self.GurobiModel.setParam('Threads', 1)

                    self.GurobiModel.optimize()

                    self.CheckSolutionAndWrite(trial)

                    #sol = self.Cplex.solution
                    
                    sol_obj_value = self.GurobiModel.ObjVal  

                    if Constants.Debug: print("cost of subproblem: {}".format(sol_obj_value))

                    averagecostofthesubproblem += sol_obj_value
                    # Assuming `SAAStageCostPerScenarioWithoutCostoGopertrial` is a dictionary and `trial` is defined
                    self.SAAStageCostPerScenarioWithoutCostoGopertrial[trial] = sol_obj_value
                    if Constants.Debug: print(f"SAA Stage Cost Per Scenario Without CostoGo per trial [{trial}]=\n{self.SAAStageCostPerScenarioWithoutCostoGopertrial[trial]}")
                    
                    if not self.IsLastStage():
                        if Constants.SDDPUseMultiCut:
                            Cost_To_Go_values = 0
                            for w in self.FixedScenarioSet:
                                for futurescenario in self.FuturScenario:
                                    Index_Var = self.GetIndexCostToGo(w, futurescenario)
                                    variable = self.Cost_To_Go_Var_SDDP[Index_Var]
                                    Cost_To_Go_values += self.FuturScenarProba[futurescenario] * variable.X
                            
                            self.SAAStageCostPerScenarioWithoutCostoGopertrial[trial] -= Cost_To_Go_values
                        else:
                            Cost_To_Go_values = 0
                            for w in self.FixedScenarioSet:
                                Index_Var = self.GetIndexCostToGo(w, 0)  # Assuming 0 indexes the default future scenario when not using multi-cut
                                variable = self.Cost_To_Go_Var_SDDP[Index_Var]
                                Cost_To_Go_values += variable.X  # Directly add the value of the variable, no scenario probability needed

                            self.SAAStageCostPerScenarioWithoutCostoGopertrial[trial] -= Cost_To_Go_values
                                            
                    if Constants.SDDPPrintDebugLPFiles:
                        self.GurobiModel.write("./Temp/backward_FCTPsolution_stage_{}_iter_{}.sol".format(self.DecisionStage, self.SDDPOwner.CurrentIteration))

                    if Constants.SDDPUseMultiCut:
                        cuts = [SDDPCut(self.PreviousSDDPStage, self.PreviousSDDPStage.CorrespondingForwardStage, trial, backwardscenario) for  backwardscenario in self.FixedScenarioSet]
                        self.ImproveCutFromSolution(cuts, self.GurobiModel)
                            #Average by the number of scenario
                        for backwardscenario in self.FixedScenarioSet:
                            cut = cuts[backwardscenario]
                            cut.UpdateRHS()
                            if Constants.Debug:
                               #print("THERE IS NO CHECK That cuts are well generated!!!!!!!!!!!!!!")
                               self.checknewcut(cut, averagecostofthesubproblem,  self.PreviousSDDPStage.GurobiModel, trial)    
                            cut.AddCut()
                            if Constants.SDDPPrintDebugLPFiles:
                                filename = f"./Temp/PreviousstageWithCut_stage_{self.DecisionStage}_iter_{self.SDDPOwner.CurrentIteration}.lp"
                                self.PreviousSDDPStage.GurobiModel.write(filename)       
                            cutsets.append(cut)
                    else:                        
                        # Creating a single cut for the non-multi-cut scenario
                        cut = SDDPCut(self.PreviousSDDPStage, self.PreviousSDDPStage.CorrespondingForwardStage, trial, 0)
                        cuts = [cut for backwardscenario in self.FixedScenarioSet]
                        
                        # Improving the cut based on the solution of the Gurobi model
                        self.ImproveCutFromSolution(cuts, self.GurobiModel)
                        # Updating the RHS of the cut
                        cut.UpdateRHS()
                        if Constants.Debug:
                            # Check the newly generated cut
                            self.checknewcut(cut, averagecostofthesubproblem, self.PreviousSDDPStage.GurobiModel, trial)
                        # Adding the cut to the model
                        cut.AddCut()
                        if Constants.SDDPPrintDebugLPFiles:
                            filename = f"./Temp/PreviousstageWithCut_stage_{self.DecisionStage}_iter_{self.SDDPOwner.CurrentIteration}.lp"
                            self.PreviousSDDPStage.GurobiModel.write(filename)
                        cutsets.append(cut)
                    avgcostssubprob.append(averagecostofthesubproblem)


            return cutsets, avgcostssubprob
            #print("cut added")

    def checknewcut(self, cut, averagecostofthesubproblem, sol, trial, withcorpoint=True):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (checknewcut)")

        currentcosttogo = sum(self.SDDPOwner.BackwardStage[t].SAAStageCostPerScenarioWithoutCostoGopertrial[trial]
                             for t in range(self.DecisionStage, len(self.SDDPOwner.StagesSet)))
        
        avgcorpoint = 0
        avg = 0
        avg += cut.GetCostToGoLBInCUrrentSolution(trial)

        if Constants.GenerateStrongCut and withcorpoint:
            avgcorpoint += cut.GetCostToGoLBInCorePoint(trial)


        if Constants.Debug: print("Cut added, cost to go with trial sol: %r cost to go corepoint: %r  (actual of backward pass sol: %r, avg of subproblems : %r)" % (
              avg, avgcorpoint, currentcosttogo, averagecostofthesubproblem))
          
    def IncreaseCutWithLowMedPriorityPatientFlowDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithLowMedPriorityPatientFlowDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.LowMedPriorityPatientFlowConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:
                       
                scenario = self.ConcernedScenarioLowMedPriorityPatientFlowConstraint[i]

                cut = cuts[scenario]

                j = self.ConcernedInjuryLowMedPriorityPatientFlowConstraint[i]
                c = self.ConcernedBloodGPLowMedPriorityPatientFlowConstraint[i]
                l = self.ConcernedDemandLowMedPriorityPatientFlowConstraint[i]
                
                period_q = self.ConcernedTimeLowMedPriorityPatientFlowConstraint[i]
                period_mu  = self.ConcernedTimeLowMedPriorityPatientFlowConstraint[i]
                period_prev_mu  = self.ConcernedTimeLowMedPriorityPatientFlowConstraint[i] - 1

                if period_prev_mu >= 0:
                    cut.IncreaseCoefficientUnsatisfiedPatients(j, c, l, period_prev_mu, -1.0 * duals[i])
                
                demand_increase = duals[i] * self.SDDPOwner.SetOfSAAScenarioDemand[self.ConcernedTimeLowMedPriorityPatientFlowConstraint[i]][scenario][j][c][l]
                cut.IncreaseDemandRHS(demand_increase)
    
    def IncreaseCutWithPILowMedPriorityPatientFlowDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithPILowMedPriorityPatientFlowDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.PILowMedPriorityPatientFlowConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:
                       
                scenario = self.ConcernedScenarioPILowMedPriorityPatientFlowConstraint[i]
                wevpi = self.ConcernedEVPIScenarioPILowMedPriorityPatientFlowConstraint[i]

                cut = cuts[scenario]

                j = self.ConcernedInjuryPILowMedPriorityPatientFlowConstraint[i]
                c = self.ConcernedBloodGPPILowMedPriorityPatientFlowConstraint[i]
                l = self.ConcernedDemandPILowMedPriorityPatientFlowConstraint[i]
                
                period_q = self.ConcernedTimePILowMedPriorityPatientFlowConstraint[i]
                period_mu  = self.ConcernedTimePILowMedPriorityPatientFlowConstraint[i]
                period_prev_mu  = self.ConcernedTimePILowMedPriorityPatientFlowConstraint[i] - 1

                if period_prev_mu >= 0 and period_prev_mu < self.GetTimePeriodRangeForPatientTransferVariable()[0]:
                    cut.IncreaseCoefficientUnsatisfiedPatients(j, c, l, period_prev_mu, -1.0 * duals[i])
                
                demand_increase = duals[i] * self.EVPIScenarioSet[wevpi].Demands[self.ConcernedTimePILowMedPriorityPatientFlowConstraint[i]][j][c][l]
                cut.IncreaseDemandRHS(demand_increase)
    
    def IncreaseCutWithPIHighPriorityPatientFlowDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithPIHighPriorityPatientFlowDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.PIHighPriorityPatientFlowConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:
                       
                scenario = self.ConcernedScenarioPIHighPriorityPatientFlowConstraint[i]
                wevpi = self.ConcernedEVPIScenarioPIHighPriorityPatientFlowConstraint[i]

                cut = cuts[scenario]

                j = self.ConcernedInjuryPIHighPriorityPatientFlowConstraint[i]
                c = self.ConcernedBloodGPPIHighPriorityPatientFlowConstraint[i]
                l = self.ConcernedDemandPIHighPriorityPatientFlowConstraint[i]
                
                period_q = self.ConcernedTimePIHighPriorityPatientFlowConstraint[i]
                period_mu  = self.ConcernedTimePIHighPriorityPatientFlowConstraint[i]
                period_prev_mu  = self.ConcernedTimePIHighPriorityPatientFlowConstraint[i] - 1

                if period_prev_mu >= 0 and period_prev_mu < self.GetTimePeriodRangeForPatientTransferVariable()[0]:
                    cut.IncreaseCoefficientUnsatisfiedPatients(j, c, l, period_prev_mu, -1.0 * duals[i])
                
                demand_increase = duals[i] * self.EVPIScenarioSet[wevpi].Demands[self.ConcernedTimePIHighPriorityPatientFlowConstraint[i]][j][c][l]
                cut.IncreaseDemandRHS(demand_increase)
    
    def IncreaseCutWithHighPriorityPatientFlowDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithHighPriorityPatientFlowDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.HighPriorityPatientFlowConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:
                    
                scenario = self.ConcernedScenarioHighPriorityPatientFlowConstraint[i]
                cut = cuts[scenario]
                j = self.ConcernedInjuryHighPriorityPatientFlowConstraint[i]
                c = self.ConcernedBloodGPHighPriorityPatientFlowConstraint[i]
                l = self.ConcernedDemandHighPriorityPatientFlowConstraint[i]
                
                period_q = self.ConcernedTimeHighPriorityPatientFlowConstraint[i]
                period_mu  = self.ConcernedTimeHighPriorityPatientFlowConstraint[i]
                period_prev_mu  = self.ConcernedTimeHighPriorityPatientFlowConstraint[i] - 1

                if period_prev_mu >= 0:
                    cut.IncreaseCoefficientUnsatisfiedPatients(j, c, l, period_prev_mu, -1.0 * duals[i])
                
                demand_increase = duals[i] * self.SDDPOwner.SetOfSAAScenarioDemand[self.ConcernedTimeHighPriorityPatientFlowConstraint[i]][scenario][j][c][l]
                cut.IncreaseDemandRHS(demand_increase)
    
    def IncreaseCutWithLowMedPriorityPatientServiceDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithLowMedPriorityPatientServiceDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.LowMedPriorityPatientServiceConstraint_Names]

        for i in range(len(duals)):
            if duals[i] != 0: 
                    
                scenario = self.ConcernedScenarioLowMedPriorityPatientServiceConstraint[i]
                cut = cuts[scenario]

                j = self.ConcernedInjuryLowMedPriorityPatientServiceConstraint[i]
                c = self.ConcernedBloodGPLowMedPriorityPatientServiceConstraint[i]
                u = self.ConcernedFacilityLowMedPriorityPatientServiceConstraint[i]
                
                period_upsilon = self.ConcernedTimeLowMedPriorityPatientServiceConstraint[i]
                period_zeta  = self.ConcernedTimeLowMedPriorityPatientServiceConstraint[i]
                period_q  = self.ConcernedTimeLowMedPriorityPatientServiceConstraint[i]
                period_prev_zeta  = self.ConcernedTimeLowMedPriorityPatientServiceConstraint[i] - 1

                if period_prev_zeta >= 0:
                    cut.IncreaseCoefficientPatientPostponement(j, c, u, period_prev_zeta, -1.0 * duals[i])
                    
    def IncreaseCutWithPILowMedPriorityPatientServiceDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithPILowMedPriorityPatientServiceDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.PILowMedPriorityPatientServiceConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0: 
                    
                scenario = self.ConcernedScenarioPILowMedPriorityPatientServiceConstraint[i]
                cut = cuts[scenario]

                j = self.ConcernedInjuryPILowMedPriorityPatientServiceConstraint[i]
                c = self.ConcernedBloodGPPILowMedPriorityPatientServiceConstraint[i]
                u = self.ConcernedFacilityPILowMedPriorityPatientServiceConstraint[i]
                
                period_upsilon = self.ConcernedTimePILowMedPriorityPatientServiceConstraint[i]
                period_zeta  = self.ConcernedTimePILowMedPriorityPatientServiceConstraint[i]
                period_q  = self.ConcernedTimePILowMedPriorityPatientServiceConstraint[i]
                period_prev_zeta  = self.ConcernedTimePILowMedPriorityPatientServiceConstraint[i] - 1

                if period_prev_zeta >= 0 and period_prev_zeta < self.GetTimePeriodRangeForPatientTransferVariable()[0]:
                    cut.IncreaseCoefficientPatientPostponement(j, c, u, period_prev_zeta, -1.0 * duals[i])
                    
    def IncreaseCutWithPIHighPriorityPatientServiceDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithPIHighPriorityPatientServiceDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.PIHighPriorityPatientServiceConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0: 
                    
                scenario = self.ConcernedScenarioPIHighPriorityPatientServiceConstraint[i]
                cut = cuts[scenario]

                j = self.ConcernedInjuryPIHighPriorityPatientServiceConstraint[i]
                c = self.ConcernedBloodGPPIHighPriorityPatientServiceConstraint[i]
                h = self.ConcernedHospitalPIHighPriorityPatientServiceConstraint[i]
                
                period_upsilon = self.ConcernedTimePIHighPriorityPatientServiceConstraint[i]
                period_zeta  = self.ConcernedTimePIHighPriorityPatientServiceConstraint[i]
                period_q  = self.ConcernedTimePIHighPriorityPatientServiceConstraint[i]
                period_prev_zeta  = self.ConcernedTimePIHighPriorityPatientServiceConstraint[i] - 1

                if period_prev_zeta >= 0 and period_prev_zeta < self.GetTimePeriodRangeForPatientTransferVariable()[0]:
                    cut.IncreaseCoefficientPatientPostponement(j, c, h, period_prev_zeta, -1.0 * duals[i])
                    
    def IncreaseCutWithHighPriorityPatientServiceDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithHighPriorityPatientServiceDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.HighPriorityPatientServiceConstraint_Names]

        for i in range(len(duals)):
            if duals[i] != 0:   
                    
                scenario = self.ConcernedScenarioHighPriorityPatientServiceConstraint[i]
                cut = cuts[scenario]

                j = self.ConcernedInjuryHighPriorityPatientServiceConstraint[i]
                c = self.ConcernedBloodGPHighPriorityPatientServiceConstraint[i]
                h = self.ConcernedHospitalHighPriorityPatientServiceConstraint[i]
                
                period_upsilon = self.ConcernedTimeHighPriorityPatientServiceConstraint[i]
                period_zeta  = self.ConcernedTimeHighPriorityPatientServiceConstraint[i]
                period_q  = self.ConcernedTimeHighPriorityPatientServiceConstraint[i]
                period_prev_zeta  = self.ConcernedTimeHighPriorityPatientServiceConstraint[i] - 1

                if period_prev_zeta >= 0:
                    cut.IncreaseCoefficientPatientPostponement(j, c, h, period_prev_zeta, -1.0 * duals[i])
                    
    def IncreaseCutWithHospitalPlateletFlowDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithHospitalPlateletFlowDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.HospitalPlateletFlowConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0: 
                    
                duals[i] = duals[i]
                scenario = self.ConcernedScenarioHospitalPlateletFlowConstraint[i]
                cut = cuts[scenario]

                cprime = self.ConcernedBloodGPHospitalPlateletFlowConstraint[i]
                r = self.ConcernedPLTAgeHospitalPlateletFlowConstraint[i]
                h = self.ConcernedHospitalHospitalPlateletFlowConstraint[i]
                
                period_lambda = self.ConcernedTimeHospitalPlateletFlowConstraint[i]
                period_bDoublePrime = self.ConcernedTimeHospitalPlateletFlowConstraint[i]
                period_b = self.ConcernedTimeHospitalPlateletFlowConstraint[i]
                period_eta  = self.ConcernedTimeHospitalPlateletFlowConstraint[i]
                period_upsilon  = self.ConcernedTimeHospitalPlateletFlowConstraint[i]
                period_Rhovar = self.ConcernedTimeHospitalPlateletFlowConstraint[i] - self.Instance.Whole_Blood_Production_Time
                period_previous_eta  = self.ConcernedTimeHospitalPlateletFlowConstraint[i] - 1

                if period_previous_eta < 0:
                    cut.IncreaseInitInventryRHS(-1.0 * self.Instance.Initial_Platelet_Inventory[cprime][r][h] * duals[i])                   #Initial Inventory Here!

                if r != 0:
                    if period_previous_eta >= 0:                    
                        cut.IncreaseCoefficientPlateletInventory(cprime, r-1, h, period_previous_eta, 1.0 * duals[i])
                
                    if period_bDoublePrime >= 0:
                        for hprime in self.Instance.HospitalSet:
                            if hprime != h:
                                cut.IncreaseCoefficientTransshipmentHH(cprime, r, hprime, h, period_bDoublePrime, 1.0 * duals[i])
                                cut.IncreaseCoefficientTransshipmentHH(cprime, r, h, hprime, period_bDoublePrime, -1.0 * duals[i])
                    
                    if period_b >= 0:
                        for i in self.Instance.ACFPPointSet:
                            cut.IncreaseCoefficientTransshipmentHI(cprime, r, h, i, period_b, -1.0 * duals[i])
                
                if r >= self.Instance.Whole_Blood_Production_Time:
                    if period_Rhovar >= 0:
                        cut.IncreaseCoefficientPlateletWholeExtractionVariable(cprime, h, period_Rhovar, +1.0 * duals[i])
    
    def IncreaseCutWithPIHospitalPlateletFlowDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithPIHospitalPlateletFlowDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.PIHospitalPlateletFlowConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0: 
                    
                duals[i] = duals[i]
                scenario = self.ConcernedScenarioPIHospitalPlateletFlowConstraint[i]

                cut = cuts[scenario]

                cprime = self.ConcernedBloodGPPIHospitalPlateletFlowConstraint[i]
                r = self.ConcernedPLTAgePIHospitalPlateletFlowConstraint[i]
                h = self.ConcernedHospitalPIHospitalPlateletFlowConstraint[i]
                
                period_lambda = self.ConcernedTimePIHospitalPlateletFlowConstraint[i]
                period_bDoublePrime = self.ConcernedTimePIHospitalPlateletFlowConstraint[i]
                period_b = self.ConcernedTimePIHospitalPlateletFlowConstraint[i]
                period_eta  = self.ConcernedTimePIHospitalPlateletFlowConstraint[i]
                period_upsilon  = self.ConcernedTimePIHospitalPlateletFlowConstraint[i]
                period_Rhovar = self.ConcernedTimePIHospitalPlateletFlowConstraint[i] - self.Instance.Whole_Blood_Production_Time
                period_previous_eta  = self.ConcernedTimePIHospitalPlateletFlowConstraint[i] - 1

                if period_previous_eta < 0:
                    cut.IncreaseInitInventryRHS(-1.0 * self.Instance.Initial_Platelet_Inventory[cprime][r][h] * duals[i])                   #Initial Inventory Here!

                if r != 0:
                    if period_previous_eta >= 0 and period_previous_eta < self.GetTimePeriodRangeForPatientTransferVariable()[0]:                    
                        cut.IncreaseCoefficientPlateletInventory(cprime, r-1, h, period_previous_eta, 1.0 * duals[i])
                
                    if period_bDoublePrime >= 0 and (len(self.PeriodsInGlobalMIPTransshipmentHH) == 0 or period_bDoublePrime < self.PeriodsInGlobalMIPTransshipmentHH[0]):
                        for hprime in self.Instance.HospitalSet:
                            if hprime != h:
                                cut.IncreaseCoefficientTransshipmentHH(cprime, r, hprime, h, period_bDoublePrime, 1.0 * duals[i])
                                cut.IncreaseCoefficientTransshipmentHH(cprime, r, h, hprime, period_bDoublePrime, -1.0 * duals[i])
                    
                    if period_b >= 0 and (len(self.PeriodsInGlobalMIPTransshipmentHI) == 0 or period_b < self.PeriodsInGlobalMIPTransshipmentHI[0]):
                        for i in self.Instance.ACFPPointSet:
                            cut.IncreaseCoefficientTransshipmentHI(cprime, r, h, i, period_b, -1.0 * duals[i])
                
                if r >= self.Instance.Whole_Blood_Production_Time:
                    if period_Rhovar >= 0 and period_previous_eta < self.GetTimePeriodRangeForPatientTransferVariable()[0]:
                        cut.IncreaseCoefficientPlateletWholeExtractionVariable(cprime, h, period_Rhovar, +1.0 * duals[i])
    
    def IncreaseCutWithACFPlateletFlowDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithACFPlateletFlowDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.ACFPlateletFlowConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:
                    
                duals[i] = duals[i]
                scenario = self.ConcernedScenarioACFPlateletFlowConstraint[i]
                cut = cuts[scenario]

                cprime = self.ConcernedBloodGPACFPlateletFlowConstraint[i]
                r = self.ConcernedPLTAgeACFPlateletFlowConstraint[i]
                acf = self.ConcernedACFACFPlateletFlowConstraint[i]
                
                period_lambda = self.ConcernedTimeACFPlateletFlowConstraint[i]
                period_b = self.ConcernedTimeACFPlateletFlowConstraint[i]
                period_bPrime = self.ConcernedTimeACFPlateletFlowConstraint[i]
                period_eta  = self.ConcernedTimeACFPlateletFlowConstraint[i]
                period_upsilon  = self.ConcernedTimeACFPlateletFlowConstraint[i]
                period_previous_eta  = self.ConcernedTimeACFPlateletFlowConstraint[i] - 1

                if r != 0:
                    if period_previous_eta >= 0:                    
                        cut.IncreaseCoefficientPlateletInventory(cprime, r-1, (self.Instance.NrHospitals + acf), period_previous_eta, +1.0 * duals[i])
                    
                    if period_b >= 0:

                        for h in self.Instance.HospitalSet:
                            cut.IncreaseCoefficientTransshipmentHI(cprime, r, h, acf, period_b, +1.0 * duals[i])
                    
                    if period_bPrime >= 0:
                        for acfprime in self.Instance.ACFPPointSet:
                            if acf != acfprime:
                                cut.IncreaseCoefficientTransshipmentII(cprime, r, acfprime, acf, period_bPrime, +1.0 * duals[i])
                                cut.IncreaseCoefficientTransshipmentII(cprime, r, acf, acfprime, period_bPrime, -1.0 * duals[i])
    
    def IncreaseCutWithPIACFPlateletFlowDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithPIACFPlateletFlowDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.PIACFPlateletFlowConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:
                    
                duals[i] = duals[i]
                scenario = self.ConcernedScenarioPIACFPlateletFlowConstraint[i]
                cut = cuts[scenario]

                cprime = self.ConcernedBloodGPPIACFPlateletFlowConstraint[i]
                r = self.ConcernedPLTAgePIACFPlateletFlowConstraint[i]
                acf = self.ConcernedACFPIACFPlateletFlowConstraint[i]
                
                period_lambda = self.ConcernedTimePIACFPlateletFlowConstraint[i]
                period_b = self.ConcernedTimePIACFPlateletFlowConstraint[i]
                period_bPrime = self.ConcernedTimePIACFPlateletFlowConstraint[i]
                period_eta  = self.ConcernedTimePIACFPlateletFlowConstraint[i]
                period_upsilon  = self.ConcernedTimePIACFPlateletFlowConstraint[i]
                period_previous_eta  = self.ConcernedTimePIACFPlateletFlowConstraint[i] - 1

                if r != 0:
                    if period_previous_eta >= 0 and period_previous_eta < self.GetTimePeriodRangeForPatientTransferVariable()[0]:                    
                        cut.IncreaseCoefficientPlateletInventory(cprime, r-1, (self.Instance.NrHospitals + acf), period_previous_eta, +1.0 * duals[i])
                    
                    if period_b >= 0 and (len(self.PeriodsInGlobalMIPTransshipmentHI) == 0 or period_b < self.PeriodsInGlobalMIPTransshipmentHI[0]):
                        for h in self.Instance.HospitalSet:
                            cut.IncreaseCoefficientTransshipmentHI(cprime, r, h, acf, period_b, +1.0 * duals[i])
                    
                    if period_bPrime >= 0 and (len(self.PeriodsInGlobalMIPTransshipmentII) == 0 or period_bPrime < self.PeriodsInGlobalMIPTransshipmentII[0]):
                        for acfprime in self.Instance.ACFPPointSet:
                            if acf != acfprime:
                                cut.IncreaseCoefficientTransshipmentII(cprime, r, acfprime, acf, period_bPrime, +1.0 * duals[i])
                                cut.IncreaseCoefficientTransshipmentII(cprime, r, acf, acfprime, period_bPrime, -1.0 * duals[i])
    
    def IncreaseCutWithACFApheresisCapacityDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithACFApheresisCapacityDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.ACFApheresisCapacityConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:
                   
                duals[i] = duals[i]
                scenario = self.ConcernedScenarioACFApheresisCapacityConstraint[i]
                cut = cuts[scenario]

                acf = self.ConcernedACFACFApheresisCapacityConstraint[i]
                period_y = self.ConcernedTimeACFApheresisCapacityConstraint[i]

                if period_y >= 0:
                    cut.IncreaseCoefficientApheresisAssignment(acf, period_y, +1.0 * self.Instance.Apheresis_Machine_Production_Capacity * duals[i])
    
    def IncreaseCutWithPIACFApheresisCapacityDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithPIACFApheresisCapacityDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.PIACFApheresisCapacityConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:
                   
                duals[i] = duals[i]
                scenario = self.ConcernedScenarioPIACFApheresisCapacityConstraint[i]
                cut = cuts[scenario]

                acf = self.ConcernedACFPIACFApheresisCapacityConstraint[i]
                period_y = self.ConcernedTimePIACFApheresisCapacityConstraint[i]

                if period_y >= 0 and (len(self.PeriodsInGlobalMIPApheresisAssignment) == 0 or period_y < self.PeriodsInGlobalMIPApheresisAssignment[0]):
                    cut.IncreaseCoefficientApheresisAssignment(acf, period_y, +1.0 * self.Instance.Apheresis_Machine_Production_Capacity * duals[i])

    def IncreaseCutWithApheresisCapacityDonorsDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithApheresisCapacityDonorsDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.ApheresisCapacityDonorsConstraint_Names]

        for i in range(len(duals)):
            if duals[i] != 0:                
                    
                duals[i] = duals[i]
                scenario = self.ConcernedScenarioApheresisCapacityDonorsConstraint[i]
                cut = cuts[scenario]
                c = self.ConcernedBloodGPApheresisCapacityDonorsConstraint[i]
                u = self.ConcernedFacilityApheresisCapacityDonorsConstraint[i]
                t = self.ConcernedTimeApheresisCapacityDonorsConstraint[i]
                
                increaseApheresisDonorRHS = -1.0 * self.Instance.Platelet_Units_Apheresis * self.SDDPOwner.SetOfSAAScenarioApheresisDonor[t][scenario][c][u] * duals[i]
                cut.IncreaseApheresisDonorRHS(increaseApheresisDonorRHS)
    
    def IncreaseCutWithPIApheresisCapacityDonorsDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithPIApheresisCapacityDonorsDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.PIApheresisCapacityDonorsConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:                
                    
                duals[i] = duals[i]
                scenario = self.ConcernedScenarioPIApheresisCapacityDonorsConstraint[i]
                wevpi = self.ConcernedEVPIScenarioPIApheresisCapacityDonorsConstraint[i]
                cut = cuts[scenario]
                c = self.ConcernedBloodGPPIApheresisCapacityDonorsConstraint[i]
                u = self.ConcernedFacilityPIApheresisCapacityDonorsConstraint[i]
                t = self.ConcernedTimePIApheresisCapacityDonorsConstraint[i]
                
                increaseApheresisDonorRHS = -1.0 * self.Instance.Platelet_Units_Apheresis * self.EVPIScenarioSet[wevpi].ApheresisDonors[t][c][u] * duals[i]
                cut.IncreaseApheresisDonorRHS(increaseApheresisDonorRHS)

    def IncreaseCutWithWholeCapacityDonorsDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithWholeCapacityDonorsDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.WholeCapacityDonorsConstraint_Names]

        for i in range(len(duals)):
            if duals[i] != 0:                
                    
                duals[i] = duals[i]
                scenario = self.ConcernedScenarioWholeCapacityDonorsConstraint[i]
                cut = cuts[scenario]
                c = self.ConcernedBloodGPWholeCapacityDonorsConstraint[i]
                h = self.ConcernedHospitalWholeCapacityDonorsConstraint[i]
                t = self.ConcernedTimeWholeCapacityDonorsConstraint[i]
                
                increaseWholeDonorRHS = -1.0 * self.SDDPOwner.SetOfSAAScenarioWholeDonor[t][scenario][c][h] * duals[i]
                cut.IncreaseWholeDonorRHS(increaseWholeDonorRHS)
    
    def IncreaseCutWithPIWholeCapacityDonorsDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithPIWholeCapacityDonorsDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.PIWholeCapacityDonorsConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:                
                    
                duals[i] = duals[i]
                scenario = self.ConcernedScenarioPIWholeCapacityDonorsConstraint[i]
                wevpi = self.ConcernedEVPIScenarioPIWholeCapacityDonorsConstraint[i]
                cut = cuts[scenario]
                c = self.ConcernedBloodGPPIWholeCapacityDonorsConstraint[i]
                h = self.ConcernedHospitalPIWholeCapacityDonorsConstraint[i]
                t = self.ConcernedTimePIWholeCapacityDonorsConstraint[i]
                
                increaseWholeDonorRHS = -1.0 * self.EVPIScenarioSet[wevpi].WholeDonors[t][c][h] * duals[i]
                cut.IncreaseWholeDonorRHS(increaseWholeDonorRHS)
    
    def IncreaseCutWithACFTreatmentCapacityDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithACFTreatmentCapacityDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.ACFTreatmentCapacityConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:
 
                duals[i] = duals[i]
                
                scenario = self.ConcernedScenarioACFTreatmentCapacityConstraint[i]
                cut = cuts[scenario]

                acf = self.ConcernedACFACFTreatmentCapacityConstraint[i]   

                period_q  = self.ConcernedTimeACFTreatmentCapacityConstraint[i]
                period_x = self.ConcernedTimeACFTreatmentCapacityConstraint[i]
                period_prev_zeta  = self.ConcernedTimeACFTreatmentCapacityConstraint[i] - 1

                if period_prev_zeta >= 0:

                    for j in self.Instance.InjuryLevelSet:
                        if self.Instance.J_u[self.Instance.NrHospitals + acf][j] == 1:
                            for c in self.Instance.BloodGPSet:
                                cut.IncreaseCoefficientPatientPostponement(j, c, (self.Instance.NrHospitals + acf), period_prev_zeta, -1.0 * duals[i])

                increase_coeff_x = +1.0 * self.Instance.ACF_Bed_Capacity[acf] * duals[i]
                cut.IncreaseCoefficientACFEstablishmentVariable(acf, period_x, increase_coeff_x)
    
    def IncreaseCutWithPIACFTreatmentCapacityDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithPIACFTreatmentCapacityDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.PIACFTreatmentCapacityConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:
 
                duals[i] = duals[i]
                
                scenario = self.ConcernedScenarioPIACFTreatmentCapacityConstraint[i]
                cut = cuts[scenario]

                acf = self.ConcernedACFPIACFTreatmentCapacityConstraint[i]   

                period_q  = self.ConcernedTimePIACFTreatmentCapacityConstraint[i]
                period_x = self.ConcernedTimePIACFTreatmentCapacityConstraint[i]
                period_prev_zeta  = self.ConcernedTimePIACFTreatmentCapacityConstraint[i] - 1

                if period_prev_zeta >= 0 and period_prev_zeta < self.GetTimePeriodRangeForPatientTransferVariable()[0]:
                    for j in self.Instance.InjuryLevelSet:
                        if self.Instance.J_u[self.Instance.NrHospitals + acf][j] == 1:
                            for c in self.Instance.BloodGPSet:
                                cut.IncreaseCoefficientPatientPostponement(j, c, (self.Instance.NrHospitals + acf), period_prev_zeta, -1.0 * duals[i])

                increase_coeff_x = +1.0 * self.Instance.ACF_Bed_Capacity[acf] * duals[i]
                cut.IncreaseCoefficientACFEstablishmentVariable(acf, period_x, increase_coeff_x)
    
    def IncreaseCutWithACFRescueVehicleCapacityDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithACFRescueVehicleCapacityDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.ACFRescueVehicleCapacityConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:
 
                duals[i] = duals[i]
                
                scenario = self.ConcernedScenarioACFRescueVehicleCapacityConstraint[i]
                cut = cuts[scenario]

                acf = self.ConcernedACFACFRescueVehicleCapacityConstraint[i]   
                m = self.ConcernedVehicleACFRescueVehicleCapacityConstraint[i] 
                t = self.ConcernedTimeACFRescueVehicleCapacityConstraint[i] 

                increaseVehicleAssignmentCoeff = +1.0 * self.Instance.Rescue_Vehicle_Capacity[m] * duals[i]
                cut.IncreaseCoefficientVehicleAssignment(m, acf, t, increaseVehicleAssignmentCoeff)
    
    def IncreaseCutWithPIACFRescueVehicleCapacityDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithPIACFRescueVehicleCapacityDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.PIACFRescueVehicleCapacityConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:
 
                duals[i] = duals[i]
                
                scenario = self.ConcernedScenarioPIACFRescueVehicleCapacityConstraint[i]
                cut = cuts[scenario]

                acf = self.ConcernedACFPIACFRescueVehicleCapacityConstraint[i]   
                m = self.ConcernedVehiclePIACFRescueVehicleCapacityConstraint[i] 
                t = self.ConcernedTimePIACFRescueVehicleCapacityConstraint[i] 

                increaseVehicleAssignmentCoeff = +1.0 * self.Instance.Rescue_Vehicle_Capacity[m] * duals[i]
                cut.IncreaseCoefficientVehicleAssignment(m, acf, t, increaseVehicleAssignmentCoeff)
    
    def IncreaseCutWithApheresisACFDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithApheresisACFDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.ApheresisACFConstraint_Names]

        for i in range(len(duals)):
            if duals[i] != 0:
 
                duals[i] = duals[i]
                
                scenario = self.ConcernedScenarioApheresisACFConstraint[i]
                cut = cuts[scenario]

                acf = self.ConcernedACFApheresisACFConstraint[i]   
                t = self.ConcernedTimeApheresisACFConstraint[i] 

                cut.IncreaseCoefficientACFEstablishmentVariable(acf, t, +1.0 * self.Instance.Total_Apheresis_Machine_ACF[t] * duals[i])
    
    def IncreaseCutWithPIApheresisACFDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithPIApheresisACFDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.PIApheresisACFConstraint_Names]


        for i in range(len(duals)):
            if duals[i] != 0:
 
                duals[i] = duals[i]
                
                scenario = self.ConcernedScenarioPIApheresisACFConstraint[i]
                cut = cuts[scenario]

                acf = self.ConcernedACFPIApheresisACFConstraint[i]   
                t = self.ConcernedTimePIApheresisACFConstraint[i] 

                cut.IncreaseCoefficientACFEstablishmentVariable(acf, t, +1.0 * self.Instance.Total_Apheresis_Machine_ACF[t] * duals[i])
               
    def IncreaseCutWithHospitalTreatmentCapacityDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithHospitalTreatmentCapacityDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.HospitalTreatmentCapacityConstraint_Names]
                
        for i in range(len(duals)):
            if duals[i] != 0:

                duals[i] = duals[i]

                scenario = self.ConcernedScenarioHospitalTreatmentCapacityConstraint[i]
                cut = cuts[scenario]

                h = self.ConcernedHospitalHospitalTreatmentCapacityConstraint[i]
                period_q  = self.ConcernedTimeHospitalTreatmentCapacityConstraint[i]
                period_prev_zeta  = self.ConcernedTimeHospitalTreatmentCapacityConstraint[i] - 1                

                if period_prev_zeta >= 0:
                    for j in self.Instance.InjuryLevelSet:
                        if self.Instance.J_u[h][j] == 1:
                            for c in self.Instance.BloodGPSet:
                                cut.IncreaseCoefficientPatientPostponement(j, c, h, period_prev_zeta, -1.0 * duals[i])

                increase_HospitalTreatmentCapRHS = (-1.0 * 
                                                    duals[i] * 
                                                    self.SDDPOwner.SetOfSAAScenarioHospitalCapacity[self.ConcernedTimeHospitalTreatmentCapacityConstraint[i]][scenario][h])
                cut.IncreaseHospitalTreatmentCapacityRHS(increase_HospitalTreatmentCapRHS)
    
    def IncreaseCutWithPIHospitalTreatmentCapacityDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithPIHospitalTreatmentCapacityDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.PIHospitalTreatmentCapacityConstraint_Names]
                
        for i in range(len(duals)):
            if duals[i] != 0:

                duals[i] = duals[i]

                scenario = self.ConcernedScenarioPIHospitalTreatmentCapacityConstraint[i]
                wevpi = self.ConcernedEVPIScenarioPIHospitalTreatmentCapacityConstraint[i]
                cut = cuts[scenario]

                h = self.ConcernedHospitalPIHospitalTreatmentCapacityConstraint[i]

                period_q  = self.ConcernedTimePIHospitalTreatmentCapacityConstraint[i]
                period_prev_zeta  = self.ConcernedTimePIHospitalTreatmentCapacityConstraint[i] - 1                

                if period_prev_zeta >= 0 and period_prev_zeta < self.GetTimePeriodRangeForPatientTransferVariable()[0]:
                    for j in self.Instance.InjuryLevelSet:
                        if self.Instance.J_u[h][j] == 1:
                            for c in self.Instance.BloodGPSet:
                                cut.IncreaseCoefficientPatientPostponement(j, c, h, period_prev_zeta, -1.0 * duals[i])

                increase_HospitalTreatmentCapRHS = (-1.0 * 
                                                    duals[i] * 
                                                    self.EVPIScenarioSet[wevpi].HospitalCaps[self.ConcernedTimePIHospitalTreatmentCapacityConstraint[i]][h])
                cut.IncreaseHospitalTreatmentCapacityRHS(increase_HospitalTreatmentCapRHS)
    
    def IncreaseCutWithHospitalRescueVehicleCapacityDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithHospitalRescueVehicleCapacityDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.HospitalRescueVehicleCapacityConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:

                    
                duals[i] = duals[i]

                scenario = self.ConcernedScenarioHospitalRescueVehicleCapacityConstraint[i]
                cut = cuts[scenario]

                h = self.ConcernedHospitalHospitalRescueVehicleCapacityConstraint[i]
                m = self.ConcernedVehicleHospitalRescueVehicleCapacityConstraint[i]
                t = self.ConcernedTimeHospitalRescueVehicleCapacityConstraint[i]

                increaseHospitalRescueVehicleCapacityRHS = -1.0 * self.Instance.Rescue_Vehicle_Capacity[m] * self.Instance.Number_Rescue_Vehicle_Hospital[m][h] * duals[i]
                cut.IncreaseHospitalRescueVehicleCapacityRHS(increaseHospitalRescueVehicleCapacityRHS)
    
    def IncreaseCutWithPIHospitalRescueVehicleCapacityDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithPIHospitalRescueVehicleCapacityDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.PIHospitalRescueVehicleCapacityConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:

                    
                duals[i] = duals[i]

                scenario = self.ConcernedScenarioPIHospitalRescueVehicleCapacityConstraint[i]
                cut = cuts[scenario]

                h = self.ConcernedHospitalPIHospitalRescueVehicleCapacityConstraint[i]
                m = self.ConcernedVehiclePIHospitalRescueVehicleCapacityConstraint[i]
                t = self.ConcernedTimePIHospitalRescueVehicleCapacityConstraint[i]

                increaseHospitalRescueVehicleCapacityRHS = -1.0 * self.Instance.Rescue_Vehicle_Capacity[m] * self.Instance.Number_Rescue_Vehicle_Hospital[m][h] * duals[i]
                cut.IncreaseHospitalRescueVehicleCapacityRHS(increaseHospitalRescueVehicleCapacityRHS)
    
    def IncreaseCutWithHospitalApheresisCapacityDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithHospitalApheresisCapacityDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.HospitalApheresisCapacityConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:
   
                duals[i] = duals[i]

                scenario = self.ConcernedScenarioHospitalApheresisCapacityConstraint[i]
                cut = cuts[scenario]

                h = self.ConcernedHospitalHospitalApheresisCapacityConstraint[i]
                time = self.ConcernedTimeHospitalApheresisCapacityConstraint[i]

                increaseHospitalApheresisCapacityRHS = -1.0 * self.Instance.Apheresis_Machine_Production_Capacity * self.Instance.Number_Apheresis_Machine_Hospital[h] * duals[i]
                cut.IncreaseHospitalApheresisCapacityRHS(increaseHospitalApheresisCapacityRHS)
    
    def IncreaseCutWithPIHospitalApheresisCapacityDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithPIHospitalApheresisCapacityDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.PIHospitalApheresisCapacityConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:
   
                duals[i] = duals[i]

                scenario = self.ConcernedScenarioPIHospitalApheresisCapacityConstraint[i]
                cut = cuts[scenario]

                h = self.ConcernedHospitalPIHospitalApheresisCapacityConstraint[i]
                time = self.ConcernedTimePIHospitalApheresisCapacityConstraint[i]

                increaseHospitalApheresisCapacityRHS = -1.0 * self.Instance.Apheresis_Machine_Production_Capacity * self.Instance.Number_Apheresis_Machine_Hospital[h] * duals[i]
                cut.IncreaseHospitalApheresisCapacityRHS(increaseHospitalApheresisCapacityRHS)

    def IncreaseCutWithNrApheresisLimitDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithNrApheresisLimitDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.NrApheresisLimitConstraint_Names]
                
        for i in range(len(duals)):
            if duals[i] != 0:
   
                duals[i] = duals[i]

                scenario = self.ConcernedScenarioNrApheresisLimitConstraint[i]
                cut = cuts[scenario]
                time = self.ConcernedTimeNrApheresisLimitConstraint[i]

                cut.IncreaseNrApheresisLimitRHS(-1.0 * self.Instance.Total_Apheresis_Machine_ACF[time] * duals[i])
    
    def IncreaseCutWithPINrApheresisLimitDual(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithPINrApheresisLimitDual)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.PINrApheresisLimitConstraint_Names]
                
        for i in range(len(duals)):
            if duals[i] != 0:
   
                duals[i] = duals[i]

                scenario = self.ConcernedScenarioPINrApheresisLimitConstraint[i]
                cut = cuts[scenario]
                time = self.ConcernedTimePINrApheresisLimitConstraint[i]

                cut.IncreaseNrApheresisLimitRHS(-1.0 * self.Instance.Total_Apheresis_Machine_ACF[time] * duals[i])
    
    def IncreaseCutWithCutDuals(self, cuts, GurobiModel):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (IncreaseCutWithCutDuals)")

        duals = [self.GurobiModel.getConstrByName(name).Pi for name in self.CutConstraint_Names]
        
        for i in range(len(duals)):
            if duals[i] != 0:
   
                duals[i] = duals[i]
                
                scenario = self.ConcernedScenarioCutConstraint[i]
                cut = cuts[scenario]
                c = self.ConcernedCutinConstraint[i]
                c.LastIterationWithDual = self.SDDPOwner.CurrentIteration

                #In the new cut the contribution of C to the RHS is the RHS of C plus the value of the variable of the current stage.
                cut.IncreasePReviousCutRHS(c.GetRHS() * duals[i]) #( c.GetRHS() + valueofvarsinconsraint )* duals[i])

                #if Constants.Debug:
                    # print("NonZeroFixedEarlierACFEstablishmentVariable: ", c.NonZeroFixedEarlierACFEstablishmentVariable)
                    # print("NonZeroFixedEarlierVehicleAssignmentVariable: ", c.NonZeroFixedEarlierVehicleAssignmentVariable)

                    # print("NonZeroFixedEarlierApheresisAssignmentVariable: ", c.NonZeroFixedEarlierApheresisAssignmentVariable)
                    # print("NonZeroFixedEarlierTransshipmentHIVariable: ", c.NonZeroFixedEarlierTransshipmentHIVariable)
                    # print("NonZeroFixedEarlierTransshipmentIIVariable: ", c.NonZeroFixedEarlierTransshipmentIIVariable)
                    # print("NonZeroFixedEarlierTransshipmentHHVariable: ", c.NonZeroFixedEarlierTransshipmentHHVariable)

                    # print("NonZeroFixedEarlierPatientTransferVariable: ", c.NonZeroFixedEarlierPatientTransferVariable)
                    # print("NonZeroFixedEarlierUnsatisfiedPatientsVariable: ", c.NonZeroFixedEarlierUnsatisfiedPatientsVariable)
                    # print("NonZeroFixedEarlierPlateletInventoryVariable: ", c.NonZeroFixedEarlierPlateletInventoryVariable)
                    # print("NonZeroFixedEarlierOutdatedPlateletVariable: ", c.NonZeroFixedEarlierOutdatedPlateletVariable)
                    # print("NonZeroFixedEarlierServedPatientVariable: ", c.NonZeroFixedEarlierServedPatientVariable)
                    # print("NonZeroFixedEarlierPatientPostponementVariable: ", c.NonZeroFixedEarlierPatientPostponementVariable)
                    # print("NonZeroFixedEarlierPlateletApheresisExtractionVariable: ", c.NonZeroFixedEarlierPlateletApheresisExtractionVariable)
                    # print("NonZeroFixedEarlierPlateletWholeExtractionVariable: ", c.NonZeroFixedEarlierPlateletWholeExtractionVariable)

                #######################################
                for tuple in c.NonZeroFixedEarlierACFEstablishmentVariable:
                    acf = tuple[0]; t = tuple[1]
                    cut.IncreaseCoefficientACFEstablishmentVariable(acf, t, c.CoefficientACFEstablishmentVariable[acf] * duals[i])
                
                for tuple in c.NonZeroFixedEarlierVehicleAssignmentVariable:
                    m = tuple[0]; acf = tuple[1]; t = tuple[2]
                    cut.IncreaseCoefficientVehicleAssignment(m, acf, t, c.CoefficientVehicleAssignmentVariable[m][acf] * duals[i])
                
                #######################################
                for tuple in c.NonZeroFixedEarlierApheresisAssignmentVariable:
                    d = tuple[0]; t = tuple[1]
                    cut.IncreaseCoefficientVarTrans(d, t, c.CoefficientVarTransVariable[t][d] * duals[i])
                
                for tuple in c.NonZeroFixedEarlierTransshipmentHIVariable:
                    d = tuple[0]; t = tuple[1]
                    cut.IncreaseCoefficientVarTrans(d, t, c.CoefficientVarTransVariable[t][d] * duals[i])
                
                for tuple in c.NonZeroFixedEarlierTransshipmentIIVariable:
                    d = tuple[0]; t = tuple[1]
                    cut.IncreaseCoefficientVarTrans(d, t, c.CoefficientVarTransVariable[t][d] * duals[i])
                
                for tuple in c.NonZeroFixedEarlierTransshipmentHHVariable:
                    d = tuple[0]; t = tuple[1]
                    cut.IncreaseCoefficientVarTrans(d, t, c.CoefficientVarTransVariable[t][d] * duals[i])
                
                #######################################
                for tuple in c.NonZeroFixedEarlierPatientTransferVariable:
                    p = tuple[0]; t = tuple[1]
                    cut.IncreaseCoefficientBackorder(p, t, c.CoefficientBackorderyVariable[t][p] * duals[i])

                for tuple in c.NonZeroFixedEarlierUnsatisfiedPatientsVariable:
                    p = tuple[0]; t = tuple[1]
                    cut.IncreaseCoefficientBackorder(p, t, c.CoefficientBackorderyVariable[t][p] * duals[i])

                for tuple in c.NonZeroFixedEarlierPlateletInventoryVariable:
                    p = tuple[0]; t = tuple[1]
                    cut.IncreaseCoefficientBackorder(p, t, c.CoefficientBackorderyVariable[t][p] * duals[i])

                for tuple in c.NonZeroFixedEarlierOutdatedPlateletVariable:
                    p = tuple[0]; t = tuple[1]
                    cut.IncreaseCoefficientBackorder(p, t, c.CoefficientBackorderyVariable[t][p] * duals[i])

                for tuple in c.NonZeroFixedEarlierServedPatientVariable:
                    p = tuple[0]; t = tuple[1]
                    cut.IncreaseCoefficientBackorder(p, t, c.CoefficientBackorderyVariable[t][p] * duals[i])

                for tuple in c.NonZeroFixedEarlierPatientPostponementVariable:
                    p = tuple[0]; t = tuple[1]
                    cut.IncreaseCoefficientBackorder(p, t, c.CoefficientBackorderyVariable[t][p] * duals[i])

                for tuple in c.NonZeroFixedEarlierPlateletApheresisExtractionVariable:
                    p = tuple[0]; t = tuple[1]
                    cut.IncreaseCoefficientBackorder(p, t, c.CoefficientBackorderyVariable[t][p] * duals[i])

                for tuple in c.NonZeroFixedEarlierPlateletWholeExtractionVariable:
                    p = tuple[0]; t = tuple[1]
                    cut.IncreaseCoefficientBackorder(p, t, c.CoefficientBackorderyVariable[t][p] * duals[i])

    def ChangeACFEstablishmentVarToBinary(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ChangeACFEstablishmentVarToBinary)")

        for i in self.Instance.ACFPPointSet:

                Index_Var = self.GetIndexACFEstablishmentVariable(i)

                variable_to_update = self.ACFEstablishment_Var_SDDP[Index_Var]

                variable_to_update.setAttr(GRB.Attr.VType, GRB.BINARY)
                variable_to_update.setAttr(GRB.Attr.LB, 0.0)
                variable_to_update.setAttr(GRB.Attr.UB, 1.0)
                self.GurobiModel.update()
    
    def ChangeVehicleAssignmentVarToInteger(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ChangeVehicleAssignmentVarToInteger)")

        for m in self.Instance.RescueVehicleSet:
            for i in self.Instance.ACFPPointSet:

                Index_Var = self.GetIndexVehicleAssignmentVariable(m, i)

                variable_to_update = self.VehicleAssignment_Var_SDDP[Index_Var]

                variable_to_update.setAttr(GRB.Attr.VType, GRB.INTEGER)
                variable_to_update.setAttr(GRB.Attr.LB, 0.0)
                variable_to_update.setAttr(GRB.Attr.UB, GRB.INFINITY)
                self.GurobiModel.update()

    def ChangeACFEstablishmentVarToContinous(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ChangeFixedTransVarToContinous)")

        for i in self.Instance.ACFPPointSet:

            Index_Var = self.GetIndexACFEstablishmentVariable(i)

            variable_to_update = self.ACFEstablishment_Var_SDDP[Index_Var]

            variable_to_update.setAttr(GRB.Attr.VType, GRB.CONTINUOUS)
            variable_to_update.setAttr(GRB.Attr.LB, 0.0)
            variable_to_update.setAttr(GRB.Attr.UB, 1.0)
            self.GurobiModel.update()
    
    def ChangeVehicleAssignmentVarToContinous(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ChangeFixedTransVarToContinous)")

        for m in self.Instance.RescueVehicleSet:
            for i in self.Instance.ACFPPointSet:

                Index_Var = self.GetIndexVehicleAssignmentVariable(m, i)

                variable_to_update = self.VehicleAssignment_Var_SDDP[Index_Var]

                variable_to_update.setAttr(GRB.Attr.VType, GRB.CONTINUOUS)
                variable_to_update.setAttr(GRB.Attr.LB, 0.0)
                variable_to_update.setAttr(GRB.Attr.UB, GRB.INFINITY)
                self.GurobiModel.update()

    # Try to use the corepoint method of papadakos, remove if it doesn't work
    # average current solution with last core point
    def UpdateCorePoint(self):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (UpdateCorePoint)")
        CoreCoeff = Constants.CorePointCoeff

        if len(self.CorePointApheresisAssignmentValues) >= self.SDDPOwner.CurrentForwardSampleSize:
            
            if self.IsFirstStage():
                self.CorePointACFEstablishmentValues = [[max((1) * self.ACFEstablishmentValues[w][i] + 0 * self.CorePointACFEstablishmentValues[w][i], 0.0)
                                                            for i in self.Instance.ACFPPointSet]
                                                            for w in self.TrialScenarioNrSet]
                self.CorePointVehicleAssignmentValues = [[[max((1 - CoreCoeff) * self.VehicleAssignmentValues[w][m][i] + CoreCoeff * self.CorePointVehicleAssignmentValues[w][m][i], 0.0)
                                                            for i in self.Instance.ACFPPointSet]
                                                            for m in self.Instance.RescueVehicleSet]
                                                            for w in self.TrialScenarioNrSet]
            # Try to use the corepoint method of papadakos, remove if it doesn't work
            if not self.IsLastStage():
                  self.CorePointApheresisAssignmentValues = [[[(1 - CoreCoeff) * self.ApheresisAssignmentValues[w][t][i] + CoreCoeff * self.CorePointApheresisAssignmentValues[w][t][i]
                                                                for i in self.Instance.ACFPPointSet]
                                                                for t in self.RangePeriodApheresisAssignment]
                                                                for w in self.TrialScenarioNrSet]
                  self.CorePointTransshipmentHIValues = [[[[[[(1 - CoreCoeff) * self.TransshipmentHIValues[w][t][c][r][h][i] + CoreCoeff * self.CorePointTransshipmentHIValues[w][t][c][r][h][i]
                                                                for i in self.Instance.ACFPPointSet]
                                                                for h in self.Instance.HospitalSet]
                                                                for r in self.Instance.PlateletAgeSet]
                                                                for c in self.Instance.BloodGPSet]
                                                                for t in self.RangePeriodApheresisAssignment]
                                                                for w in self.TrialScenarioNrSet]
                  self.CorePointTransshipmentIIValues = [[[[[[(1 - CoreCoeff) * self.TransshipmentIIValues[w][t][c][r][i][iprime] + CoreCoeff * self.CorePointTransshipmentIIValues[w][t][c][r][i][iprime]
                                                                for iprime in self.Instance.ACFPPointSet]
                                                                for i in self.Instance.ACFPPointSet]
                                                                for r in self.Instance.PlateletAgeSet]
                                                                for c in self.Instance.BloodGPSet]
                                                                for t in self.RangePeriodApheresisAssignment]
                                                                for w in self.TrialScenarioNrSet]
                  self.CorePointTransshipmentHHValues = [[[[[[(1 - CoreCoeff) * self.TransshipmentHHValues[w][t][c][r][h][hprime] + CoreCoeff * self.CorePointTransshipmentHHValues[w][t][c][r][h][hprime]
                                                                for hprime in self.Instance.HospitalSet]
                                                                for h in self.Instance.HospitalSet]
                                                                for r in self.Instance.PlateletAgeSet]
                                                                for c in self.Instance.BloodGPSet]
                                                                for t in self.RangePeriodApheresisAssignment]
                                                                for w in self.TrialScenarioNrSet]

            # The value of the backorder variable (filled after having solve the MIPs for all scenario)
            self.CorePointPatientTransferValues = [[[[[[[(1 - CoreCoeff) * self.PatientTransferValues[w][t][j][c][l][u][m] + CoreCoeff * self.CorePointPatientTransferValues[w][t][j][c][l][u][m]
                                                        for m in self.Instance.RescueVehicleSet]
                                                        for u in self.Instance.FacilitySet]
                                                        for l in self.Instance.DemandSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for j in self.Instance.InjuryLevelSet]
                                                        for t in self.RangePeriodPatientTransfer]
                                                        for w in self.TrialScenarioNrSet]
            self.CorePointUnsatisfiedPatientsValues = [[[[[(1 - CoreCoeff) * self.UnsatisfiedPatientsValues[w][t][j][c][l] + CoreCoeff * self.CorePointUnsatisfiedPatientsValues[w][t][j][c][l]
                                                        for l in self.Instance.DemandSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for j in self.Instance.InjuryLevelSet]
                                                        for t in self.RangePeriodPatientTransfer]
                                                        for w in self.TrialScenarioNrSet]
            self.CorePointPlateletInventoryValues = [[[[[(1 - CoreCoeff) * self.PlateletInventoryValues[w][t][c][r][u] + CoreCoeff * self.CorePointPlateletInventoryValues[w][t][c][r][u]
                                                        for u in self.Instance.FacilitySet]
                                                        for r in self.Instance.PlateletAgeSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for t in self.RangePeriodPatientTransfer]
                                                        for w in self.TrialScenarioNrSet]
            self.CorePointOutdatedPlateletValues = [[[(1 - CoreCoeff) * self.OutdatedPlateletValues[w][t][u] + CoreCoeff * self.CorePointOutdatedPlateletValues[w][t][u]
                                                        for u in self.Instance.FacilitySet]
                                                        for t in self.RangePeriodPatientTransfer]
                                                        for w in self.TrialScenarioNrSet]
            self.CorePointServedPatientValues = [[[[[[[(1 - CoreCoeff) * self.ServedPatientValues[w][t][j][cprime][c][r][u] + CoreCoeff * self.CorePointServedPatientValues[w][t][j][cprime][c][r][u]
                                                        for u in self.Instance.FacilitySet]
                                                        for r in self.Instance.PlateletAgeSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for cprime in self.Instance.BloodGPSet]
                                                        for j in self.Instance.InjuryLevelSet]
                                                        for t in self.RangePeriodPatientTransfer]
                                                        for w in self.TrialScenarioNrSet]
            self.CorePointPatientPostponementValues = [[[[[(1 - CoreCoeff) * self.PatientPostponementValues[w][t][j][c][u] + CoreCoeff * self.CorePointPatientPostponementValues[w][t][j][c][u]
                                                        for u in self.Instance.FacilitySet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for j in self.Instance.InjuryLevelSet]
                                                        for t in self.RangePeriodPatientTransfer]
                                                        for w in self.TrialScenarioNrSet]
            self.CorePointPlateletApheresisExtractionValues = [[[[(1 - CoreCoeff) * self.PlateletApheresisExtractionValues[w][t][c][u] + CoreCoeff * self.CorePointPlateletApheresisExtractionValues[w][t][c][u]
                                                        for u in self.Instance.FacilitySet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for t in self.RangePeriodPatientTransfer]
                                                        for w in self.TrialScenarioNrSet]
            self.CorePointPlateletWholeExtractionValues = [[[[(1 - CoreCoeff) * self.PlateletWholeExtractionValues[w][t][c][h] + CoreCoeff * self.CorePointPlateletWholeExtractionValues[w][t][c][h]
                                                        for h in self.Instance.HospitalSet]
                                                        for c in self.Instance.BloodGPSet]
                                                        for t in self.RangePeriodPatientTransfer]
                                                        for w in self.TrialScenarioNrSet]
        else:
            if self.IsFirstStage():
                self.CorePointACFEstablishmentValues = [[self.ACFEstablishmentValues[w][i]
                                                            for i in self.Instance.ACFPPointSet]
                                                            for w in self.TrialScenarioNrSet]
                self.CorePointVehicleAssignmentValues = [[[self.VehicleAssignmentValues[w][m][i]
                                                            for i in self.Instance.ACFPPointSet]
                                                            for m in self.Instance.RescueVehicleSet]
                                                            for w in self.TrialScenarioNrSet]

            if not self.IsLastStage():
                self.CorePointApheresisAssignmentValues = [[[self.ApheresisAssignmentValues[w][t][i]
                                                                for i in self.Instance.ACFPPointSet]
                                                                for t in self.RangePeriodApheresisAssignment]
                                                                for w in self.TrialScenarioNrSet]
                self.CorePointTransshipmentHIValues = [[[[[[self.TransshipmentHIValues[w][t][c][r][h][i]
                                                            for i in self.Instance.ACFPPointSet]
                                                            for h in self.Instance.HospitalSet]
                                                            for r in self.Instance.PlateletAgeSet]
                                                            for c in self.Instance.BloodGPSet]
                                                            for t in self.RangePeriodApheresisAssignment]
                                                            for w in self.TrialScenarioNrSet]
                self.CorePointTransshipmentIIValues = [[[[[[self.TransshipmentIIValues[w][t][c][r][i][iprime]
                                                            for iprime in self.Instance.ACFPPointSet]
                                                            for i in self.Instance.ACFPPointSet]
                                                            for r in self.Instance.PlateletAgeSet]
                                                            for c in self.Instance.BloodGPSet]
                                                            for t in self.RangePeriodApheresisAssignment]
                                                            for w in self.TrialScenarioNrSet]
                self.CorePointTransshipmentHHValues = [[[[[[self.TransshipmentHHValues[w][t][c][r][h][hprime]
                                                            for hprime in self.Instance.HospitalSet]
                                                            for h in self.Instance.HospitalSet]
                                                            for r in self.Instance.PlateletAgeSet]
                                                            for c in self.Instance.BloodGPSet]
                                                            for t in self.RangePeriodApheresisAssignment]
                                                            for w in self.TrialScenarioNrSet]
            
            # The value of the Patient Transfer variable (filled after having solve the MIPs for all scenario)
            self.CorePointPatientTransferValues = [[[[[[[self.PatientTransferValues[w][t][j][c][l][u][m]
                                                            for m in self.Instance.RescueVehicleSet]
                                                            for u in self.Instance.FacilitySet]
                                                            for l in self.Instance.DemandSet]
                                                            for c in self.Instance.BloodGPSet]
                                                            for j in self.Instance.InjuryLevelSet]
                                                            for t in self.RangePeriodPatientTransfer]
                                                            for w in self.TrialScenarioNrSet]
            self.CorePointUnsatisfiedPatientsValues = [[[[[self.UnsatisfiedPatientsValues[w][t][j][c][l]
                                                            for l in self.Instance.DemandSet]
                                                            for c in self.Instance.BloodGPSet]
                                                            for j in self.Instance.InjuryLevelSet]
                                                            for t in self.RangePeriodPatientTransfer]
                                                            for w in self.TrialScenarioNrSet]
            self.CorePointPlateletInventoryValues = [[[[[self.PlateletInventoryValues[w][t][c][r][u]
                                                            for u in self.Instance.FacilitySet]
                                                            for r in self.Instance.PlateletAgeSet]
                                                            for c in self.Instance.BloodGPSet]
                                                            for t in self.RangePeriodPatientTransfer]
                                                            for w in self.TrialScenarioNrSet]
            self.CorePointOutdatedPlateletValues = [[[self.OutdatedPlateletValues[w][t][u]
                                                            for u in self.Instance.FacilitySet]
                                                            for t in self.RangePeriodPatientTransfer]
                                                            for w in self.TrialScenarioNrSet]
            self.CorePointServedPatientValues = [[[[[[[self.ServedPatientValues[w][t][j][cprime][c][r][u]
                                                            for u in self.Instance.FacilitySet]
                                                            for r in self.Instance.PlateletAgeSet]
                                                            for c in self.Instance.BloodGPSet]
                                                            for cprime in self.Instance.BloodGPSet]
                                                            for j in self.Instance.InjuryLevelSet]
                                                            for t in self.RangePeriodPatientTransfer]
                                                            for w in self.TrialScenarioNrSet]
            self.CorePointPatientPostponementValues = [[[[[self.PatientPostponementValues[w][t][j][c][u]
                                                            for u in self.Instance.FacilitySet]
                                                            for c in self.Instance.BloodGPSet]
                                                            for j in self.Instance.InjuryLevelSet]
                                                            for t in self.RangePeriodPatientTransfer]
                                                            for w in self.TrialScenarioNrSet]
            self.CorePointPlateletApheresisExtractionValues = [[[[self.PlateletApheresisExtractionValues[w][t][c][u]
                                                                    for u in self.Instance.FacilitySet]
                                                                    for c in self.Instance.BloodGPSet]
                                                                    for t in self.RangePeriodPatientTransfer]
                                                                    for w in self.TrialScenarioNrSet]
            self.CorePointPlateletWholeExtractionValues = [[[[self.PlateletWholeExtractionValues[w][t][c][h]
                                                                    for h in self.Instance.HospitalSet]
                                                                    for c in self.Instance.BloodGPSet]
                                                                    for t in self.RangePeriodPatientTransfer]
                                                                    for w in self.TrialScenarioNrSet]

    def ChangeACFEstablishmentToValueOfTwoStage(self, makecontinuous=True):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ChangeACFEstablishmentToValueOfTwoStage)")

        # Update variable bounds and types
        for i in self.Instance.ACFPPointSet:

            index_var = self.GetIndexACFEstablishmentVariable(i)
            variable_to_update = self.ACFEstablishment_Var_SDDP[index_var]

            # Set the variable to the heuristic fixed transportation value
            fixed_value = float(self.SDDPOwner.HeuristicACFEstablishmentValue[i])
            variable_to_update.setAttr(GRB.Attr.LB, fixed_value)
            variable_to_update.setAttr(GRB.Attr.UB, fixed_value)
            if makecontinuous:
                variable_to_update.setAttr(GRB.Attr.VType, GRB.CONTINUOUS)
            self.GurobiModel.update()

        if Constants.Debug:
            for var in self.ACFEstablishment_Var_SDDP.values():
                print(f"Updated Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            print("\n--------------\n")  
    
    def ChangeVehicleAssignmentToValueOfTwoStage(self, makecontinuous=True):
        if Constants.Debug: print("\n We are in 'SDDPStage' Class -- (ChangeVehicleAssignmentToValueOfTwoStage)")

        # Update variable bounds and types
        for m in self.Instance.RescueVehicleSet:
            for i in self.Instance.ACFPPointSet:

                index_var = self.GetIndexVehicleAssignmentVariable(m, i)
                variable_to_update = self.VehicleAssignment_Var_SDDP[index_var]

                # Set the variable to the heuristic fixed transportation value
                fixed_value = float(self.SDDPOwner.HeuristicVehicleAssignmentValue[m][i])
                variable_to_update.setAttr(GRB.Attr.LB, fixed_value)
                variable_to_update.setAttr(GRB.Attr.UB, fixed_value)
                if makecontinuous:
                    # Change variable type to continuous if requested
                    variable_to_update.setAttr(GRB.Attr.VType, GRB.CONTINUOUS)
                self.GurobiModel.update()

        if Constants.Debug:
            for var in self.VehicleAssignment_Var_SDDP.values():
                print(f"Updated Var Name: {var.VarName}, Obj: {var.Obj}, LB: {var.LB}, UB: {var.UB}, VType: {var.VType}")
            print("\n--------------\n")
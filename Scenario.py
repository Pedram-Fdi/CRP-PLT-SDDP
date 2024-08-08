from Constants import Constants
import pandas as pd


class Scenario(object):

    NrScenario = 0
    #Constructor
    def __init__( self, owner=None, 
                 demand=None, 
                 hospitalcap=None, 
                 wholedonor=None, 
                 apheresisdonor=None, 
                 proabability=-1, 
                 acfestablishment_variable=None,  
                 vehicleassignment_variable=None, 
                 apheresisAssignment_variable=None, 
                 transshipmentHI_variable=None, 
                 transshipmentII_variable=None, 
                 transshipmentHH_variable=None,
                 
                 patientTransfer_variable=None, 
                 unsatisfiedPatients_variable=None, 
                 plateletInventory_vriable=None, 
                 outdatedPlatelet_variable=None, 
                 servedPatient_variable=None, 
                 patientPostponement_variable=None, 
                 plateletApheresisExtraction_variable=None, 
                 plateletWholeExtraction_variable=None, 

                 nodesofscenario=None ):

        if Constants.Debug: print("\n We are in 'Scenario' Class -- Constructor")
        self.Owner = owner
        # The  demand in the scenario for each time period
        self.Demands = demand
        self.HospitalCaps = hospitalcap
        self.WholeDonors = wholedonor
        self.ApheresisDonors = apheresisdonor
        # The probability of the partial scenario
        self.Probability = proabability
        
        # The attribute below contains the index of the CPLEX variables (quanity, production, invenotry) for each product and time.
        self.ACFEstablishmentVariable = acfestablishment_variable
        self.VehicleAssignmentVariable = vehicleassignment_variable

        self.ApheresisAssignmentVariable = apheresisAssignment_variable
        self.TransshipmentHIVariable = transshipmentHI_variable
        self.TransshipmentIIVariable = transshipmentII_variable
        self.TransshipmentHHVariable = transshipmentHH_variable
        
        self.PatientTransferVariable = patientTransfer_variable
        self.UnsatisfiedPatientsVariable = unsatisfiedPatients_variable
        self.PlateletInventoryVariable = plateletInventory_vriable
        self.OutdatedPlateletVariable = outdatedPlatelet_variable
        self.ServedPatientVariable = servedPatient_variable
        self.PatientPostponementVariable = patientPostponement_variable
        self.PlateletApheresisExtractionVariable = plateletApheresisExtraction_variable
        self.PlateletWholeExtractionVariable = plateletWholeExtraction_variable
        
        Scenario.NrScenario = Scenario.NrScenario +1
        self.Nodes = nodesofscenario
        if not self.Nodes is None:
            for n in self.Nodes:
                n.OneOfScenario = self
                n.Scenarios.append(self)
        self.ScenarioId = Scenario.NrScenario   

    def DisplayScenario(self):
        if Constants.Debug: print("\n We are in 'Scenario' Class -- DisplayScenario")
        # print("Scenario %d" %self.ScenarioId)
        # print("Demands of scenario(%d): %r" %(self.ScenarioId, self.Demands))
        # print("HospitalCaps of scenario(%d): %r" %(self.ScenarioId, self.HospitalCaps))
        # print("WholeDonors of scenario(%d): %r" %(self.ScenarioId, self.WholeDonors))
        # print("ApheresisDonors of scenario(%d): %r" %(self.ScenarioId, self.ApheresisDonors))
        # print("Probability of scenario(%d): %r" %(self.ScenarioId, self.Probability))

        # print("ACFEstablishmentVariable of scenario(%d): %r" % (self.ScenarioId, self.ACFEstablishmentVariable))
        # print("VehicleAssignmentVariable of scenario(%d): %r" % (self.ScenarioId, self.VehicleAssignmentVariable))

        # print("ApheresisAssignmentVariable of scenario(%d): %r" % (self.ScenarioId, self.ApheresisAssignmentVariable))
        # print("TransshipmentHIVariable of scenario(%d): %r" % (self.ScenarioId, self.TransshipmentHIVariable))
        # print("TransshipmentIIVariable of scenario(%d): %r" % (self.ScenarioId, self.TransshipmentIIVariable))
        # print("TransshipmentHHVariable of scenario(%d): %r" % (self.ScenarioId, self.TransshipmentHHVariable))

        # print("PatientTransferVariable of scenario(%d): %r" % (self.ScenarioId, self.PatientTransferVariable))
        # print("UnsatisfiedPatientsVariable of scenario(%d): %r" % (self.ScenarioId, self.UnsatisfiedPatientsVariable))
        # print("PlateletInventoryVariable of scenario(%d): %r" % (self.ScenarioId, self.PlateletInventoryVariable))
        # print("OutdatedPlateletVariable of scenario(%d): %r" % (self.ScenarioId, self.OutdatedPlateletVariable))
        # print("ServedPatientVariable of scenario(%d): %r" % (self.ScenarioId, self.ServedPatientVariable))
        # print("PatientPostponementVariable of scenario(%d): %r" % (self.ScenarioId, self.PatientPostponementVariable))
        # print("PlateletApheresisExtractionVariable of scenario(%d): %r" % (self.ScenarioId, self.PlateletApheresisExtractionVariable))
        # print("PlateletWholeExtractionVariable of scenario(%d): %r" % (self.ScenarioId, self.PlateletWholeExtractionVariable))


    def PrintScenarioToText(self, file):
        #if Constants.Debug: print("\n We are in 'Scenario' Class -- PrintScenarioToText")

        # Lists are adjusted to match the time bucket set length here
        time_buckets = list(self.Owner.Instance.TimeBucketSet)
        demands = self.Demands + [0] * (len(time_buckets) - len(self.Demands))
        hospitalcaps = self.HospitalCaps + [0] * (len(time_buckets) - len(self.HospitalCaps))
        wholedonors = self.WholeDonors + [0] * (len(time_buckets) - len(self.WholeDonors))
        apheresisdonors = self.ApheresisDonors + [0] * (len(time_buckets) - len(self.ApheresisDonors))

        acf_establishment = self.ACFEstablishmentVariable + [0] * (len(time_buckets) - len(self.ACFEstablishmentVariable))
        Vehicle_Assignment = self.VehicleAssignmentVariable + [0] * (len(time_buckets) - len(self.VehicleAssignmentVariable))

        apheresisassignment = self.ApheresisAssignmentVariable + [0] * (len(time_buckets) - len(self.ApheresisAssignmentVariable))
        transshipmentHI = self.TransshipmentHIVariable + [0] * (len(time_buckets) - len(self.TransshipmentHIVariable))
        transshipmentIIVariable = self.TransshipmentIIVariable + [0] * (len(time_buckets) - len(self.TransshipmentIIVariable))
        transshipmentHHVariable = self.TransshipmentHHVariable + [0] * (len(time_buckets) - len(self.TransshipmentHHVariable))
        
        patientTransferVariable = self.PatientTransferVariable + [0] * (len(time_buckets) - len(self.PatientTransferVariable))
        unsatisfiedPatientsVariable = self.UnsatisfiedPatientsVariable + [0] * (len(time_buckets) - len(self.UnsatisfiedPatientsVariable))
        plateletInventoryVariable = self.PlateletInventoryVariable + [0] * (len(time_buckets) - len(self.PlateletInventoryVariable))
        outdatedPlateletVariable = self.OutdatedPlateletVariable + [0] * (len(time_buckets) - len(self.OutdatedPlateletVariable))
        servedPatientVariable = self.ServedPatientVariable + [0] * (len(time_buckets) - len(self.ServedPatientVariable))
        patientPostponementVariable = self.PatientPostponementVariable + [0] * (len(time_buckets) - len(self.PatientPostponementVariable))
        plateletApheresisExtractionVariable = self.PlateletApheresisExtractionVariable + [0] * (len(time_buckets) - len(self.PlateletApheresisExtractionVariable))
        plateletWholeExtractionVariable = self.PlateletWholeExtractionVariable + [0] * (len(time_buckets) - len(self.PlateletWholeExtractionVariable))

        # Write directly to the file object passed as an argument
        file.write(f"Scenario {self.ScenarioId + 1}:\n")
        file.write("Time Buckets: {}\n".format(', '.join(map(str, time_buckets))))

        file.write("Demands: {}\n".format(', '.join(map(str, demands))))
        file.write("HospitalCaps: {}\n".format(', '.join(map(str, hospitalcaps))))
        file.write("WholeDonors: {}\n".format(', '.join(map(str, wholedonors))))
        file.write("ApheresisDonors: {}\n".format(', '.join(map(str, apheresisdonors))))

        # file.write("ACFEstablishmentVariable: {}\n".format(', '.join(map(str, acf_establishment))))
        # file.write("VehicleAssignmentVariable: {}\n".format(', '.join(map(str, Vehicle_Assignment))))

        # file.write("ApheresisAssignmentVariable: {}\n".format(', '.join(map(str, apheresisassignment))))
        # file.write("TransshipmentHIVariable: {}\n".format(', '.join(map(str, transshipmentHI))))
        # file.write("TransshipmentIIVariable: {}\n".format(', '.join(map(str, transshipmentIIVariable))))
        # file.write("TransshipmentHHVariable: {}\n".format(', '.join(map(str, transshipmentHHVariable))))

        # file.write("PatientTransferVariable: {}\n".format(', '.join(map(str, patientTransferVariable))))
        # file.write("UnsatisfiedPatientsVariable: {}\n".format(', '.join(map(str, unsatisfiedPatientsVariable))))
        # file.write("PlateletInventoryVariable: {}\n".format(', '.join(map(str, plateletInventoryVariable))))
        # file.write("OutdatedPlateletVariable: {}\n".format(', '.join(map(str, outdatedPlateletVariable))))
        # file.write("ServedPatientVariable: {}\n".format(', '.join(map(str, servedPatientVariable))))
        # file.write("PatientPostponementVariable: {}\n".format(', '.join(map(str, patientPostponementVariable))))
        # file.write("PlateletApheresisExtractionVariable: {}\n".format(', '.join(map(str, plateletApheresisExtractionVariable))))
        # file.write("PlateletWholeExtractionVariable: {}\n".format(', '.join(map(str, plateletWholeExtractionVariable))))

        
        file.write("\n")

       
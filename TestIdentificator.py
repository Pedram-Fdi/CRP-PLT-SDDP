#This object contains all the information which allow to identify the test
from Constants import Constants

class TestIdentificator( object ):
    
    # Constructor
    def __init__(self, instancename, model, method, sampling, nrscenario, scenarioseed, useevpi, nrscenarioforward, mipsetting, sddpsetting, hybridphsetting, mllocalsearchsetting, sequencetype, lbfpercentage, ClusteringMethod, InitNumScenCoeff):
        if Constants.Debug: print("\n We are in 'TestIdentificator' Class -- Constructor")
        self.InstanceName = instancename
        self.Model = model
        self.Method = method
        self.ScenarioSampling = sampling
        self.NrScenario = nrscenario
        self.ScenarioSeed = scenarioseed
        self.EVPI = useevpi
        self.MIPSetting = mipsetting
        self.NrScenarioForward = nrscenarioforward
        self.SDDPSetting = sddpsetting
        self.HybridPHSetting = hybridphsetting
        self.MLLocalSearchSetting = mllocalsearchsetting        
        self.SequenceType = sequencetype        
        self.LBFPercentage = lbfpercentage        
        self.ClusteringMethod = ClusteringMethod        
        self.InitNumScenCoeff = InitNumScenCoeff        
        self.Print_Attributes()

    def GetAsStringList(self):
        if Constants.Debug: print("\n We are in 'TestIdentificator' Class -- GetAsStringList")
        result = [self.InstanceName,
                  self.Model,
                  self.Method,
                  self.ScenarioSampling,
                  self.NrScenario,
                  "%s"%self.ScenarioSeed,
                  "%s"%self.EVPI,
                  "%s"%self.NrScenarioForward,
                  self.MIPSetting,
                  self.SDDPSetting,
                  self.HybridPHSetting,
                  self.MLLocalSearchSetting,
                  self.SequenceType,
                  "%s"%self.LBFPercentage,
                  self.ClusteringMethod,
                  "%s"%self.InitNumScenCoeff]
        return result
 
    def GetAsString(self):
        if Constants.Debug: print("\n We are in 'TestIdentificator' Class -- GetAsString")
        result = "_".join([self.InstanceName,
                           self.Model,
                           self.Method,
                           self.ScenarioSampling,
                           self.NrScenario,
                           "%s"%self.ScenarioSeed,
                           "%s"%self.EVPI,
                           "%s"%self.NrScenarioForward,
                           self.MIPSetting,
                           self.SDDPSetting,
                           self.HybridPHSetting,
                           self.MLLocalSearchSetting,
                           self.SequenceType,
                           "%s"%self.LBFPercentage,
                           self.ClusteringMethod,
                           "%s"%self.InitNumScenCoeff])
        return result
    
    def Print_Attributes(self):
        if Constants.Debug: 
            print("\n We are in 'TestIdentificator' Class -- Print_Attributes")
            print("\n------")
            print("Instance Name:", self.InstanceName)
            print("Model:", self.Model)
            print("Method:", self.Method)
            print("Scenario Sampling:", self.ScenarioSampling)
            print("Number of Scenarios:", self.NrScenario)
            print("Scenario Seed:", self.ScenarioSeed)
            print("EVPI:", self.EVPI)
            print("Number of Scenarios Forward:", self.NrScenarioForward)
            print("MIP Setting:", self.MIPSetting)
            print("SDDP Setting:", self.SDDPSetting)
            print("HybridPHSetting:", self.HybridPHSetting)
            print("MLLocalSearchSetting:", self.MLLocalSearchSetting)
            print("SequenceType:", self.SequenceType)
            print("LBFPercentage:", self.LBFPercentage)
            print("ClusteringMethod:", self.ClusteringMethod)
            print("InitNumScenCoeff:", self.InitNumScenCoeff)
            print("------\n")
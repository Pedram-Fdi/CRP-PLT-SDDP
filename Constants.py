#This Class define a set of constant/parameters used in the rest of the code.


class Constants( object ):


    PathInstances = "./Instances/"

    #Scenario sampling methods:
    MonteCarlo = "MC"
    QMC = "QMC"
    RQMC = "RQMC"
    All = "all"

    #low-discrepancy sequence type to generate QMC or RQMC: (This part is inactive now)
    SequenceTypee = "Halton"                     # Do not Change it, You can Modify it in main.py


    #Method
    MIP = "MIP"
    SDDP = "SDDP"
    NBD = "NBD"
    ProgressiveHedging = "PH"
    Hybrid = "Hybrid"                           #Fixing First-stage Variables with PH first, then solving SDDP to obtain others!
    SDDP_VSS = "SDDP_VSS"
    


    #Demand distributions:
    Lumpy = "Lumpy"
    SlowMoving = "SlowMoving"
    Uniform = "Uniform"
    Normal = "Normal"
    Binomial = "Binomial"
    NonStationary = "NonStationary"

    #Model
    Average = "Average"
    Two_Stage = "Two_Stage"
    ModelMulti_Stage = "Multi_Stage"
    ModelHeuristicMulti_Stage = "HeuristicMulti_Stage"        #Here, we fix first-stage variables by solving the Two-stage model first, and then obtain other variables by solving Multi-stage model.
    MLLocalSearch = "MLLocalSearch"
    JustYFix = "JustYFix"

    #Action
    Solve ="Solve"
    Evaluate = "Evaluate"
    VSS = "VSS"

    #Decision Framework
    RollingHorizon = "RH"
    Fix = "Fix"
    Resolve = "Re-solve"

    #The set of seeds used for random number generator
    SeedArray = [42]        #[2934, 875, 3545, 765, 546, 768, 242, 375, 142, 236, 788]
    EvaluationScenarioSeed = 3545

    ######################## START OF DO NOT CHANGING PART ########################
    Evaluation_Part = False

    ######################## END OF DO NOT CHANGING PART ########################


    #Running option
    Debug = False
    PrintSolutionFileToExcel = False            #If you set this 'True', then all final values of variables and objective function will be printed in Excel too.
    PrintSolutionFileToPickle = True
    PrintDetailsExcelFiles = False               #Here, you save some statistics which is useful for analytical part of the paper!
    PrintOnlyFirstStageDecision = True
    RunEvaluationInSeparatedJob = False
    PrintScenarios = True
    PrintSolutionFileInTMP = False
    LauchEvalAfterSolve = True  

    #Code parameter
    Infinity = 9999999999999999
    AlgorithmTimeLimit = 0.5 * 60     #Whatever you have here, then in the SDDP algorithm, (AlgorithmTimeLimit * |T|) will be used as time limit.
    MIPTimeLimit = 12 * 3600            #This is only a time limit to solve the extended model via MIP.

    MIPBasedOnSymetricTree = True 
    RQMCAggregate = False

    #Nested Benders Decomposition
    NestedBenders = False           #Do not Change, It gets value in the code!
    #SDDPparameters
    AlgorithmOptimalityTolerence = 0.0005        #It is not Active Now! 
    AlgorithmOptimalityTolerenceTest = 0.001     # it is used for Convergency test based on in-sample scenarios
    SDDPIterationLimit = 500                    #It is not active now!
    SDDPPrintDebugLPFiles = False
    PrintSDDPTrace = True
    SDDPRunSingleTree = False
    SDDPModifyBackwardScenarioAtEachIteration = False

    #SDDP/NBD Enhancements (Accelerators)
    SDDPUseMultiCut = False              # Do NOt Change!
    GenerateStrongCut = False            # Do NOt Change!
    CorePointCoeff = 0.5                 # The coefficient of the previous core point value, which should be less than 1!
    SDDPUseEVPI = False                  # Do NOt Change! (Lower bounding Functional (LBF))
    LBFPercentage = 100                  # Do Not Change! (You have to modify it in the main.py file)   
    WarmUp_SDDP = False                  #Do NOt Change!
    SDDPNrIterationRelax = 9            # 10 to 50, for Warm-up    

    #HeuristicMulti_Stage/MLLocalSearch
    AlgorithmTimeLimit_MLTabu_Part = 10 * 3600            # It should be tuned (in sec)
    NrScenarioinHeuristicTwoStageModel = 4                # Previously 4 (it is a default value, but it will be updated in the text according to the number of time periods)
    MLLSNrIterationBeforeTabu = 50                       # Previously 50
    LimitNrIterWithoutImprovmentMLLocalSearch = 5        # Previously 10
    VehicleChangesinTabu = 10                            # The number of vehicles increased or decreased each time in tabu searching!
    MLLSTabuList = 5
    MLLSNrIterationTabu = 50                             # Previously 50                
    MLLSPercentFilter  = 80                             # Previously 50
    MLType = "NN"
    ScailingDataML = 1

    #SDDPNrScenarioForwardPass = 10
    #SDDPNrScenarioBackwardPass = 10
    SDDPForwardPassInSAATree = True                 #Do Not Change it: It should be always true!
    SDDPPerformConvergenceTestDuringRun = True
    SDDPIncreaseNrScenarioTest = 100
    SDDPInitNrScenarioTest = 1000                   # (Previously set to 1000) At the end of the algorithm, this test will be done to obtain the lower bound and upper bound based on large number of instances! Not only based on 1 instance in each forward pass!

    SolveRelaxationFirst = False
    SDDPGapRelax = 0.01 
    SDDPUseValidInequalities = False
    SDDPGenerateCutWith2Stage = False
    SDDPCleanCuts = False
    SDDPNrEVPIScenario = 1
    SDDPDebugSolveAverage = False
    SDDPMinimumNrIterationBetweenTest = 200
    SDDPNrItNoImproveLBBeforeTest = 150
    PercentageInSampleScnearioTest = 100             # Do Not Change it, The next one is important which shows the minimum number of in-sample scenarios used to test convergence!
    NrInSampleScnearioTest = 1000                    # In fact we use min(NrofTotalInSampleScenarios, 1000)
    SDDPDurationBeforeIncreaseForwardSample = 3600
    SDDPSaveInExcel = False
    SDDPFixSetupStrategy = False
    SDDPFirstForwardWithEVPI = False

    #PHA Algorithm
    PHIterationLimit = 1100                # Previosly set to 10000
    PHConvergenceTolerence = 0.01        
    Rho_PH_PenaltyParameter= 0.1             # The best: 0.1
    PHCoeeff_QuadraticPart = 1               # The best: 1
    Dynamic_rho_PenaltyParameter = True

    ################ MIP Setting (My Specific Model)
    IntegerRecourse = False         #If it set to True, then the y_{tiw} would take integer values otherwise, it is going to be continuous!
    Transshipment_Enabled = True    #If it set to False, then the Lb and Ub of Transshipment Variables will be set to 0, and therefore we will not have any transshipment in the Supply chain!
    ModelOutputFlag = 0             #If it is 0, Prevents Gurobi from showing the optimization process!
    UsingRelaxedMIPGapforTwoStageHeuristic = False      # When we wanna fixed our first stage variables with a 2-stage model first, it takes time to solve. So we kind of make it easier in terms of optimality gap at this stage. Note: It should be always set to False Here. Then, in the code, it gets the right value accordingly
    
    GeneratingHospitalUncertainCapacity = False         # Do not change this! I will uses it, bacause, after disasters, in the first period, we face hospital uncartainty, but, in the next periods, the uncertainty is done, and they start to increase the hospitals capacities, and that is what we are considering in our model!
    @staticmethod
    def IsDeterministic(s):
        result = s == Constants.Average
        return result
    
    @staticmethod
    def IsSDDPBased(s):
        result = s == Constants.SDDP \
                 or s == Constants.MLLocalSearch \
                 or s == Constants.Hybrid
        return result
    
    @staticmethod
    def IsNBDBased(s):
        result = s == Constants.NBD
        return result
    
    @staticmethod
    def IsQMCMethos(s):
       result = s in [Constants.QMC, Constants.RQMC]
       return result

    @staticmethod
    def IsRule(s):
        return False

    @staticmethod
    def GetEvaluationFolder():
        if Constants.PrintSolutionFileInTMP:
            return "/tmp/Pedram/Evaluations/"
        else:
            return "./Evaluations/"
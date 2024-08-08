class Explanation:
    @staticmethod
    def display():
        explanation = """
        This script is designed to handle various tasks related to the optimization and evaluation of instances using different methods such as MIP, NBD, SDDP, PH, Hybrid, and MLLocalSearch. Below is an explanation of each component and its role in the script.

        1. **Action == Solve**:
            a. When you are trying to solve a problem, first of all, you have to generate an instance which can be done with:
                i. "--Action" == "GenerateInstances"
            b. Once instances are generated, you choose which instance to be solved!
                i. "--Instance" == "Name of your desired instance to be solved"
            c. Then, you choose which model will be built?
                i. If "--Model" == "Two_Stage": then a two-stage model is built and solved exactly via Gurobi optimization. Here, no algorithm is developed for that, so you have to remember to 
                    set "method" to MIP. The scenarios? The scenarios are created based on "NrScenario", e.g., all4, and number of periods (T), i.e., T^4.
                ii. If "--Model" == "Average": it solves the MIP model for only one scenario, which is set to the average value of the uncertain parameters. Why is it useful? It is beneficial for when
                    you are trying to solve Multi-stage and then evaluate the model. You solve your model with "Average" and then evaluate solutions with 5000 out-of-sample scenarios, and then solve
                    the Multi-stage version of your model and again evaluate your fixed first-stage solutions with the same 5000 out-of-sample scenarios, and you will see the value of solving a stochastic problem
                    instead of solving with the average values!
                iii. If "--Model" == "Multi_Stage": Here is the main functionality of this set of files, with the following abilities:
                    a. If "--method" == MIP: The code solves an MIP Model using Gurobi Solver and by considering non-anticipativity constraints!
                    b. If "--method" == NBD: The code solves an MIP Model using the Nested Benders Decomposition algorithm!
                    c. If "--method" == SDDP: The code solves an MIP Model using the Stochastic Dual Dynamic Programming algorithm!
                    d. If "--method" == PH: The code solves an MIP Model using Progressive Hedging algorithm.
                    e. If "--method" == Hybrid: The code first solves the problem with PH algoeithm, then it fixes the first stage variables to the values obtained via PH and use it for the SDDP algorithm!
                    f. If "--method" == MLLocalSearch: The code Integrates Machine Learning (NN), Tabu Search, and SDDP (In which the first stage variables are fixed in SDDP using ML-Enhanced Tabu Search Algorithm)
                iv. If "--Model" == "HeuristicMulti_Stage":
                    When you set the model to this option, at first, a 2-stage model with the total number of scenarios "Constants.NrScenarioinHeuristicTwoStageModel^self.Instance.NrTimeBucket" will be solved.
                    Then, the first-stage variables (which are binary or/and integer) are fixed to the values obtained from this model, and in the following, the develped algorithms are used to solve the multi-stage model.
                    a. If "--method" == SDDP: The code solve a two-stage model first (with limited number of scenarios), then fixed first stage variables to what it already obtained from the 2-stage and then solve the Multi-stage version using SDDP! 
                    b. If "--method" != SDDP: It is not working with other methods!
            d. "--NrScenario" == "all...": Here, you determine the number of scenarios in each time period.
            e. "--ScenarioGeneration": Here you can specify which scenario generation method will be used for in-sample scenarios. However, for evaluation (out-of-sample scenarios),
                always the Monte Carlo (MC) method is used.
            f. "--nrevaluation": Number of out-of-sample scenarios used for evaluation.
            g. "--mipsetting": Different enhancements considered for SDDP and NBD.
            h. "--nrforward": Number of scenarios in the forward pass of SDDP.
            i. Other parts of arguments have no ability now!

        2. **Action == DebugLPFile**:
            - During developing your code, whenever you face a model which is infeasible, you can make "SDDPPrintDebugLPFiles" in the Constants.py class True, and then after the LP model which is infeasible
              is created, you write its name in "--Instance" and set action to "DebugLPFile". It finally tells you which constraints in the LP file cause the infeasibility.

        3. **Action == Explanation**:
            - You can see this file on your screen.
        """
        print(explanation)

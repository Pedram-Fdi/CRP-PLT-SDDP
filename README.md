
# CRP-PLT-SDDP

**Casualty Response Planning and Platelet Inventory Management via SDDP**

## Overview

This project focuses on the optimization and evaluation of instances related to Casualty Response Planning (CRP) and Platelet Inventory Management using various methods such as MIP, NBD, SDDP, PH, Hybrid, and MLLocalSearch. Below is a detailed explanation of each component and its role within the script.

## Components and Actions

### 1. Action: Solve

This action is used for solving different models within the project. Here’s a step-by-step guide:

#### a. Generate Instances

Before solving any problem, you must generate instances using:

\`\`\`bash
--Action="GenerateInstances"
\`\`\`

#### b. Choose an Instance

After generating instances, select the specific instance to solve:

\`\`\`bash
--Instance="Name_of_your_desired_instance"
\`\`\`

#### c. Choose a Model

- **Two_Stage Model**:
  - Solved exactly via Gurobi with the method set to MIP.
  - Scenarios are generated based on \`NrScenario\` and the number of periods (T), e.g., T^4.

- **Average Model**:
  - Solves the MIP model for a single scenario using the average value of uncertain parameters.
  - Useful for comparing Multi-stage solutions against a deterministic average scenario solution.

- **Multi_Stage Model**:
  - The primary functionality with multiple solving methods:
    - \`--method=MIP\`: Solves using Gurobi with non-anticipativity constraints.
    - \`--method=NBD\`: Uses Nested Benders Decomposition.
    - \`--method=SDDP\`: Employs Stochastic Dual Dynamic Programming.
    - \`--method=PH\`: Uses the Progressive Hedging algorithm.
    - \`--method=Hybrid\`: First uses PH to solve, then fixes first-stage variables for SDDP.
    - \`--method=MLLocalSearch\`: Integrates Machine Learning, Tabu Search, and SDDP for enhanced optimization.

- **HeuristicMulti_Stage Model**:
  - First solves a 2-stage model with a limited number of scenarios.
  - Then uses the solutions to fix first-stage variables for the Multi-stage model using SDDP.
  - Only compatible with SDDP as the method.

#### d. Scenario and Evaluation Settings

- **NrScenario**: Specifies the number of scenarios for each time period.
- **ScenarioGeneration**: Defines the scenario generation method for in-sample scenarios. Monte Carlo is always used for out-of-sample evaluation.
- **nrevaluation**: Number of out-of-sample scenarios used for evaluation.
- **mipsetting**: Enhancements for SDDP and NBD.
- **nrforward**: Number of scenarios in the forward pass of SDDP.

### 2. Action: DebugLPFile

If you encounter an infeasible model during development, enable \`SDDPPrintDebugLPFiles\` in the \`Constants.py\` class. After the infeasible LP model is created, set the action to \`DebugLPFile\` and provide the instance name. This will identify which constraints are causing the infeasibility.

### 3. Action: Explanation

Displays the detailed explanation of each component of the script, as provided here.

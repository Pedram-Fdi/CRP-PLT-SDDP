import gurobipy as gp
from gurobipy import GRB

class DebugLPFile:
    def __init__(self, lp_file_path):
        self.lp_file_path = lp_file_path

    def solve_lp_file(self):
        try:
            # Read the LP file
            model = gp.read(self.lp_file_path)
            
            # Optimize the model
            model.optimize()
            
            # Check the optimization status
            if model.status == GRB.OPTIMAL:
                print("Optimal solution found.")
                for v in model.getVars():
                    print(f"{v.varName}: {v.x}")
                print(f"Objective Value: {model.objVal}")
            elif model.status == GRB.INFEASIBLE:
                print("Model is infeasible. Identifying conflicts...")
                # Compute the IIS (Irreducible Inconsistent Subsystem)
                model.computeIIS()
                for c in model.getConstrs():
                    if c.IISConstr:
                        print(f"Infeasible constraint: {c.constrName}")
            elif model.status == GRB.UNBOUNDED:
                print("Model is unbounded.")
            else:
                print(f"Optimization was stopped with status {model.status}")

        except gp.GurobiError as e:
            print(f"Gurobi error: {e}")
        except AttributeError as e:
            print(f"Attribute error: {e}")

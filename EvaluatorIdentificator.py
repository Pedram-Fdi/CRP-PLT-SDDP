#This object contains all the information which allow to identify the evaluator
from Constants import Constants

class EvaluatorIdentificator( object ):

    # Constructor
    def __init__( self, policygeneration, nrevaluation, timehorizon, allscenario):
        if Constants.Debug: print("\n We are in 'EvaluatorIdentificator' Class -- Constructor")
        self.PolicyGeneration = policygeneration
        self.NrEvaluation = nrevaluation
        self.TimeHorizon = timehorizon
        self.AllScenario = allscenario

    def GetAsStringList(self):
        result = [self.PolicyGeneration,
                  "%s" % self.NrEvaluation,
                  "%s" % self.TimeHorizon,
                  "%s" % self.AllScenario]
        return result

    def GetAsString(self):
        result = "_".join(self.GetAsStringList())
        return result

    def Print_Attributes(self):
        if Constants.Debug: 
            print("\n We are in 'EvaluatorIdentificator' Class -- Print_Attributes")
            print("\n------")
            print("Policy Generation:", self.PolicyGeneration)
            print("Number of Evaluations:", self.NrEvaluation)
            print("Time Horizon:", self.TimeHorizon)
            print("All Scenario:", self.AllScenario)
            print("------\n")



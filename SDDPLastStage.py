import math
from Constants import Constants
from SDDPStage import SDDPStage
import numpy as np
import gurobipy as gp
from gurobipy import *
import os

# This class contains the attributes and methodss allowing to define one stage of the SDDP algorithm.
class SDDPLastStage( SDDPStage ):
    if Constants.Debug: print("\n We are in 'SDDPLastStage' Class")

    def IsLastStage(self):
        return True 

    def IsFirstStage(self):
        return False  

    def CreateBigMConstraint(self):
        print("Not in last period")


    def IsPenultimateStage(self):
        return False     
import os
import platform
import pandas as pd
from Constants import Constants
import random
import math
import numpy as np
import pickle

class Instance(object):

    # Constructor
    def __init__(self, instanceName):
        if Constants.Debug: print("\n We are in 'Instance' Class -- Constructor")
        
        self.InstanceName = instanceName

        self.NrTimeBucket = -1
        self.NrACFPPoints = -1
        self.NrHospitals = -1
        self.NrDemandLocations = -1
        self.NrFacilities = -1    #In facilities, We have Hospitals first, and then, ACFs ----->>> {HOSPITALs + ACFs}
        self.NrRescueVehicles = -1
        self.NRBloodGPs = -1
        self.NRInjuryLevels = -1
        self.NRPlateletAges = -1 
        self.G_c = []
        self.J_u = []
        self.J_r = []
        self.R_j = []
        self.Distribution = "Uniform"
        #self.Distribution = "Normal"
        self.Gamma = -1
        
        self.TimeBucketSet = []
        self.ACFPPointSet = []
        self.HospitalSet = []
        self.DemandSet = []
        self.FacilitySet = []
        self.RescueVehicleSet = []
        self.BloodGPSet = []
        self.InjuryLevelSet = []
        self.PlateletAgeSet = []

        # Random Setting
        self.Do_you_need_point_plot = 0                 # To draw Hospitals, ACFs, and demand locations on the Map
        self.Speed = 70;                                # (km/h) #Harewood (2002) considers a range from 10 to 80 km/h for emergency ambulance in Barbados we consider 50 because we are dealing with disasters.// //65 km\h According to "Designing a Reliable and Dynamic Multimodal Transportation Network for Biofuel Supply Chains"
        self.Square_Dimension = 50;                     # In KM
        self.Working_Hours_per_Day = 15;                # working Hours for vehicles 
        self.Working_Hours_per_Day_Apheresis = 24;      # working Hours for Apheresis Machines
        self.Number_of_Planning_Days = 1;               # Each stage is one day

        self.Do_you_want_Random_Initial_Platelet_Inventory = 1
        self.Do_you_want_Dependent_Hospital_Capacities_based_on_Demands = 1
        self.Safety_Factor_Initital_Platelet = 1
        self.Safety_Factor_Rescue_Vehicle_ACF = 5           #For having 0 Shortage (For demand between [50,200], its defaul is on 3)
        self.Safety_Factor_Rescue_Vehicle_Hospital = 2.5      #For having 0 Shortage (For demand between [50,200], its defaul is on 1.5)
        self.Rquired_Time_For_One_Apheresis_collection = 90   # In Minutes        
        
        # The two attributes below define the number of periods where the demand is known with certainty at the
        # beginning and at the end of the horizon
        self.NrTimeBucketWithoutUncertaintyAfter = -1
        self.NrTimeBucketWithoutUncertaintyBefore = -1
        self.NrTimeBucketWithoutUncertainty = -1

        #Domain of Parameters
        self.Min_ACF_Bed_Capacity = 100
        self.Max_ACF_Bed_Capacity = 400

        self.m2_Required_for_Each_Patient = 1.3
        self.Cost_of_Each_m2 = 25

        self.Min_Platelet_Wastage_Cost = 20
        self.Max_Platelet_Wastage_Cost = 20

        self.Min_Platelet_Inventory_Cost = 10
        self.Max_Platelet_Inventory_Cost = 10

        self.Min_VehicleAssignment_Cost = 0.001
        self.Max_VehicleAssignment_Cost = 0.001
        
        self.Min_ApheresisMachineAssignment_Cost = 0.001
        self.Max_ApheresisMachineAssignment_Cost = 0.001
        
        self.Min_ApheresisExtraction_Cost = 0.0001
        self.Max_ApheresisExtraction_Cost = 0.0001
        
        self.Min_WholeExtraction_Cost = 0.0001
        self.Max_WholeExtraction_Cost = 0.0001

        self.Min_Total_Apheresis_Machine_ACF = 40 
        self.Max_Total_Apheresis_Machine_ACF = 40 
        
        self.Min_Demand_in_Each_Location = 0
        self.Max_Demand_in_Each_Location = 250

        self.blood_group_percentages_8 = {
             "O+": 0.39, "A+": 0.36, "B+": 0.076, "AB+": 0.025,
             "O-": 0.07, "A-": 0.06, "B-": 0.014, "AB-": 0.005
         }
        self.blood_groups_8 = list(self.blood_group_percentages_8.keys())
        
        self.blood_group_percentages_4 = {"O": 0.46, "A": 0.42, "B": 0.09, "AB": 0.03}
        self.blood_groups_4 = list(self.blood_group_percentages_4.keys())

        # Injury level percentages
        self.Priority_Patient_Percent = {
            0: 0.30,  # High priority
            1: 0.30,  # Medium priority
            2: 0.40   # Low priority
        }

        self.Min_Initial_Platelet_Inventory = 50
        self.Max_Initial_Platelet_Inventory = 50

        self.Min_Hospital_Bed_Capacity = 200
        self.Max_Hospital_Bed_Capacity = 300
        self.Hospital_Bed_Capacity_STD_Coeff = 0.50

        self.Nominal_Rescue_Vehicle_Capacity = -1
        self.Hospital_Position = []
        self.Min_Casualty_Shortage_Cost = 150000
        self.Max_Casualty_Shortage_Cost = 150000

        self.High_Priority_Postponement_Cost = 9000

        self.Min_Number_of_Apheresis_Machines_Hospital = 10
        self.Max_Number_of_Apheresis_Machines_Hospital = 10

        #References for the number of blood donors:
        # https://www.popsci.com/health/donate-blood-mass-shootings-disasters/

        self.Min_Number_of_Whole_Blood_Donors_in_Each_Period_in_Each_Location = 200 
        self.Max_Number_of_Whole_Blood_Donors_in_Each_Period_in_Each_Location = 600 

        self.Min_Number_of_Apheresis_Donors_in_Each_Period_in_Each_Location = 100
        self.Max_Number_of_Apheresis_Donors_in_Each_Period_in_Each_Location = 500

        # Only Parameters used in the Mathematical Model
        self.Total_Budget_ACF_Establishment = -1
        self.Platelet_Units_Apheresis = -1        
        self.Whole_Blood_Production_Time = -1 
        self.Apheresis_Machine_Production_Capacity = -1
        self.Fixed_Cost_ACF = []
        self.Fixed_Cost_ACF_Constraint = []
        self.Platelet_Wastage_Cost = []
        self.Platelet_Inventory_Cost = []
        self.VehicleAssignment_Cost = []
        self.ApheresisMachineAssignment_Cost = []
        self.ApheresisExtraction_Cost = []
        self.WholeExtraction_Cost = []
        self.Platelet_Units_Required_for_Injury = []
        self.Postponing_Cost_Surgery = []
        self.Total_Apheresis_Machine_ACF = []
        self.Substitution_Weight = []
        self.ACF_Bed_Capacity = []
        self.Initial_Platelet_Inventory = []
        self.ForecastedAverageDemand = []
        self.ForecastedStandardDeviationDemand = []
        self.ForecastedAverageHospital_Bed_Capacity = []
        self.ForecastedSTDHospital_Bed_Capacity = []
        self.Rescue_Vehicle_Capacity = []
        self.Distance_D_A = []
        self.Distance_A_H = []
        self.Distance_D_H = []
        self.Distance_A_A = []
        self.Distance_H_H = []
        self.Casualty_Shortage_Cost = []
        self.Number_Apheresis_Machine_Hospital = []
        self.Number_Rescue_Vehicle_ACF = []
        self.Number_Rescue_Vehicle_Hospital = []
        self.ForecastedAverageWhole_Blood_Donors = []
        self.ForecastedSTDWhole_Blood_Donors = []
        self.ForecastedAverageApheresis_Donors = []
        self.ForecastedSTDApheresis_Donors = []

        # This variable is true if the end of horizon in the instance is the actual end of horizon
        # (False in a rolling horizon framework)
        self.ActualEndOfHorizon = True

        ###################################################################################################
        # The data below are not given with the instance, but computed as they help to build the model
        ###################################################################################################
        self.Gamma = 1  # Discount Factor
        self.My_EpGap= 0.0001
        self.My_EpGap_Heuristic= 0.0001           #previosly: 0.01

    def Generate_Data(self, seed=None):
        if Constants.Debug: print("\n We are in 'Instance' Class -- Generate_Data")

        if seed is not None:
            random.seed(seed)
        
        ################################## Generate G_c
        # In this matrix, if G_c[c][cprime]==1, it means c can be substituted by cprime!
        self.G_c = np.zeros((len(self.BloodGPSet), len(self.BloodGPSet)))

        if len(self.BloodGPSet) == 8:
            for c in self.BloodGPSet:
                if c <= 3: # Positive blood groups can be substituted by any other blood groups
                    for cPrime in self.BloodGPSet:
                        self.G_c[c][cPrime] = 1
                else:
                    for cPrime in self.BloodGPSet:
                        if cPrime > 3:
                            self.G_c[c][cPrime] = 1
        else:
            for c in self.BloodGPSet:
                for cPrime in self.BloodGPSet:
                    self.G_c[c][cPrime] = 1
          
        ################################## Generate J_u
        self.J_u = np.zeros((len(self.FacilitySet), len(self.InjuryLevelSet)))

        for u in self.FacilitySet:
            if u < self.NrHospitals:
                for j in self.InjuryLevelSet:
                    self.J_u[u][j] = 1
            else:
                for j in self.InjuryLevelSet:
                    if j != 0:
                        self.J_u[u][j] = 1

        ################################## Generate J_r
        self.J_r = np.zeros((len(self.InjuryLevelSet), len(self.PlateletAgeSet)))

        for j in self.InjuryLevelSet:
            if(j==0):       # High-Priority
                self.J_r[j][0] = 1
            elif (j==1):    # Medium-Priority
                self.J_r[j][0] = 1
                self.J_r[j][1] = 1
                self.J_r[j][2] = 1    
            elif(j==2):     # Low-Priority    
                self.J_r[j][0] = 1
                self.J_r[j][1] = 1
                self.J_r[j][2] = 1 
                self.J_r[j][3] = 1 
                self.J_r[j][4] = 1 

        ################################## Generate R_j
        self.R_j = np.zeros((len(self.PlateletAgeSet), len(self.InjuryLevelSet)))

        for r in self.PlateletAgeSet:
            for j in self.InjuryLevelSet:
                if(j==0):       # High-Priority
                    self.R_j[0][j] = 1
                elif (j==1):    # Medium-Priority
                    self.R_j[0][j] = 1
                    self.R_j[1][j] = 1
                    self.R_j[2][j] = 1    
                elif(j==2):     # Low-Priority                        
                    self.R_j[0][j] = 1
                    self.R_j[1][j] = 1
                    self.R_j[2][j] = 1
                    self.R_j[3][j] = 1
                    self.R_j[4][j] = 1

        ################################## Generate nr.Platelet Extraction by Apheresis
        self.Platelet_Units_Apheresis = 8               # The number of units of platelets extracted from one person by Apheresis machine*/

        ################################## Generate ACF Bed Capacities
        for i in self.ACFPPointSet:
            New_ACF_Bed_Capacity = random.randint(self.Min_ACF_Bed_Capacity, (self.Max_ACF_Bed_Capacity * max(1, round(self.NrDemandLocations/10))))
            self.ACF_Bed_Capacity.append(New_ACF_Bed_Capacity)

        ################################## Generate Fixed Costs ACF based on ACF Bed Capacities
        for i in self.ACFPPointSet:
            New_Fixed_Cost_ACF = self.ACF_Bed_Capacity[i] * self.m2_Required_for_Each_Patient * self.Cost_of_Each_m2 * 0.00001
            New_Fixed_Cost_ACF = math.floor(1000 * New_Fixed_Cost_ACF) / 1000
            #self.Fixed_Cost_ACF.append(New_Fixed_Cost_ACF)     #if you wanna consider the cost of ACF openning in the obj function, uncomment this and comment next line.
            self.Fixed_Cost_ACF.append(New_Fixed_Cost_ACF)
        
        ################################## Generate Fixed Costs ACF based on ACF Bed Capacities
        for i in self.ACFPPointSet:
            New_Fixed_Cost_ACF_Constraint = self.ACF_Bed_Capacity[i] * self.m2_Required_for_Each_Patient * self.Cost_of_Each_m2
            New_Fixed_Cost_ACF_Constraint = math.floor(1000 * New_Fixed_Cost_ACF_Constraint) / 1000
            self.Fixed_Cost_ACF_Constraint.append(New_Fixed_Cost_ACF_Constraint)

        ################################## Generate Available Budget for ACFs
        Total_Required_Budget_for_ACF_Establishment = 0
        for i in self.ACFPPointSet:
            Total_Required_Budget_for_ACF_Establishment += self.Fixed_Cost_ACF_Constraint[i]
        Total_Required_Budget_for_ACF_Establishment = ((Total_Required_Budget_for_ACF_Establishment * 17) / 20)
        Max_Required_Budget_for_ACF_Establishment = max(self.Fixed_Cost_ACF_Constraint)
        print("Total_Required_Budget_for_ACF_Establishment: ", Total_Required_Budget_for_ACF_Establishment)
        print("Max_Required_Budget_for_ACF_Establishment: ", Max_Required_Budget_for_ACF_Establishment)
        
        self.Total_Budget_ACF_Establishment = max(Total_Required_Budget_for_ACF_Establishment, Max_Required_Budget_for_ACF_Establishment)   # The total available budget to establish ACFs*/
        

        ################################## Generate Platelet_Wastage_Cost       
        for u in self.FacilitySet:  # Start from 1 to skip the first element as in C++
            New_Platelet_Wastage_Cost = random.uniform(self.Min_Platelet_Wastage_Cost, self.Max_Platelet_Wastage_Cost)
            New_Platelet_Wastage_Cost = math.floor(1000 * New_Platelet_Wastage_Cost) / 1000
            self.Platelet_Wastage_Cost.append(New_Platelet_Wastage_Cost)
        
        ################################## Generate Platelet_Inventory_Cost       
        for u in self.FacilitySet:  # Start from 1 to skip the first element as in C++
            New_Platelet_Inventory_Cost = random.uniform(self.Min_Platelet_Inventory_Cost, self.Max_Platelet_Inventory_Cost)
            New_Platelet_Inventory_Cost = math.floor(1000 * New_Platelet_Inventory_Cost) / 1000
            self.Platelet_Inventory_Cost.append(New_Platelet_Inventory_Cost)
        ################################## Generate VehicleAssignment_Cost       
        for m in self.RescueVehicleSet:  # Start from 1 to skip the first element as in C++
            New_VehicleAssignment_Cost = random.uniform(self.Min_VehicleAssignment_Cost, self.Max_VehicleAssignment_Cost)
            New_VehicleAssignment_Cost = math.floor(1000 * New_VehicleAssignment_Cost) / 1000
            self.VehicleAssignment_Cost.append(New_VehicleAssignment_Cost)
        ################################## Generate ApheresisMachineAssignment_Cost       
        for i in self.ACFPPointSet:  # Start from 1 to skip the first element as in C++
            New_ApheresisMachineAssignment_Cost = random.uniform(self.Min_ApheresisMachineAssignment_Cost, self.Max_ApheresisMachineAssignment_Cost)
            New_ApheresisMachineAssignment_Cost = math.floor(1000 * New_ApheresisMachineAssignment_Cost) / 1000
            self.ApheresisMachineAssignment_Cost.append(New_ApheresisMachineAssignment_Cost)        
        ################################## Generate ApheresisExtraction_Cost       
        for u in self.FacilitySet:  # Start from 1 to skip the first element as in C++
            New_ApheresisExtraction_Cost = random.uniform(self.Min_ApheresisExtraction_Cost, self.Max_ApheresisExtraction_Cost)
            New_ApheresisExtraction_Cost = math.floor(1000 * New_ApheresisExtraction_Cost) / 1000
            self.ApheresisExtraction_Cost.append(New_ApheresisExtraction_Cost)
        ################################## Generate WholeExtraction_Cost       
        for h in self.HospitalSet:  # Start from 1 to skip the first element as in C++
            New_WholeExtraction_Cost = random.uniform(self.Min_WholeExtraction_Cost, self.Max_WholeExtraction_Cost)
            New_WholeExtraction_Cost = math.floor(1000 * New_WholeExtraction_Cost) / 1000
            self.WholeExtraction_Cost.append(New_WholeExtraction_Cost)
        ################################## Generate Platelet_Units_Required_for_Injury from reference: "Analysis of the Blood Consumption for Surgical Programs"
        for j in self.InjuryLevelSet:
            if j==0:
               New_Platelet_Units_Required_for_Injury = 3
            elif j==1:
                New_Platelet_Units_Required_for_Injury = 2
            else:
                New_Platelet_Units_Required_for_Injury = 1
            
            self.Platelet_Units_Required_for_Injury.append(New_Platelet_Units_Required_for_Injury)
        
        ################################## Generate Postponing_Cost_Surgery
        for j in self.InjuryLevelSet:
            if j==0:
               New_Postponing_Cost_Surgery = self.High_Priority_Postponement_Cost
            elif j==1:
                New_Postponing_Cost_Surgery = (self.High_Priority_Postponement_Cost/2)
            else:
                New_Postponing_Cost_Surgery = (self.High_Priority_Postponement_Cost/3)
            
            self.Postponing_Cost_Surgery.append(New_Postponing_Cost_Surgery * 2)

        ################################## Generate Total_Apheresis_Machine_ACF
        for t in self.TimeBucketSet:
            New_Total_Apheresis_Machine_ACF = random.randint(self.Min_Total_Apheresis_Machine_ACF, self.Max_Total_Apheresis_Machine_ACF)
            self.Total_Apheresis_Machine_ACF.append(New_Total_Apheresis_Machine_ACF)

        ################################## Define blood group headers for rows (Donors) and columns (Recipients)
        if len(self.BloodGPSet) == 8:
            blood_groups = ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"]
        else:
            blood_groups = ["O", "A", "B", "AB"]

        # Generate Substitution Weight Matrix
        if len(self.BloodGPSet) == 4:
            self.Substitution_Weight = [
                [0, 15, 15, 30],  # O is more flexible as a donor, so lower penalties
                [10, 0, 20, 30],  # A to B is a bit less flexible
                [20, 20, 0, 10],  # B to A is similar, with some flexibility to AB
                [30, 15, 15, 0]]  # AB, being the universal recipient, has the highest penalties for substitution
        else:
            self.Substitution_Weight = [
                [0, 30, 30, 30, 20, 35, 35, 35],
                [10, 0, 20, 20, 25, 20, 30, 30],
                [20, 20, 0, 10, 30, 30, 20, 25],
                [30, 10, 10, 0, 35, 25, 25, 20],
                [5, 35, 35, 35, 0, 15, 15, 15],
                [15, 5, 25, 25, 5, 0, 10, 10],
                [25, 25, 5, 15, 10, 10, 0, 5],
                [35, 15, 15, 5, 15, 5, 5, 0]]   
                     
        self.Substitution_Weight = [[element * 5 for element in row] for row in self.Substitution_Weight]
        
        ##################################  Calculating Forecasted Average Demand
        self.ForecastedAverageDemand = np.zeros((len(self.TimeBucketSet), len(self.InjuryLevelSet), len(self.BloodGPSet), len(self.DemandSet)))
        
        for t in self.TimeBucketSet:
            for l in self.DemandSet:
                # Generate total demand for each location and time period
                #total_demand = random.randint(self.Min_Demand_in_Each_Location, self.Max_Demand_in_Each_Location)   #For normal Distribution 
                total_demand = (self.Min_Demand_in_Each_Location + self.Max_Demand_in_Each_Location) / 2               #For uniform Distribution 
                for j in self.InjuryLevelSet:
                    # Allocate a portion of total demand to each injury level
                    demand_for_injury_level = round(total_demand * self.Priority_Patient_Percent[j])

                    # Distribute this demand across blood groups
                    for c, bg in enumerate(blood_groups):
                        if len(self.BloodGPSet) == 8:
                            demand_for_bg = round(demand_for_injury_level * self.blood_group_percentages_8[bg])
                        else:
                            demand_for_bg = round(demand_for_injury_level * self.blood_group_percentages_4[bg])
                        
                        self.ForecastedAverageDemand[t][j][c][l] = demand_for_bg
        
        ##################################  Calculating Forecasted Average Standard Deviation Demand
        self.ForecastedStandardDeviationDemand = np.zeros((len(self.TimeBucketSet), len(self.InjuryLevelSet), len(self.BloodGPSet), len(self.DemandSet)))
        
        for t in self.TimeBucketSet:
            for l in self.DemandSet:
                # Generate total demand for each location and time period
                # total_STD_demand = (self.Max_Demand_in_Each_Location - self.Min_Demand_in_Each_Location) / np.sqrt(12)
                total_STD_demand = (self.Max_Demand_in_Each_Location - self.Min_Demand_in_Each_Location) / 2
                
                for j in self.InjuryLevelSet:
                    # Allocate a portion of total demand to each injury level
                    STD_demand_for_injury_level = round(total_STD_demand * self.Priority_Patient_Percent[j])

                    # Distribute this demand across blood groups
                    for c, bg in enumerate(blood_groups):
                        
                        if len(self.BloodGPSet) == 8:
                            STD_demand_for_bg = round(STD_demand_for_injury_level * self.blood_group_percentages_8[bg])
                        else:
                            STD_demand_for_bg = round(STD_demand_for_injury_level * self.blood_group_percentages_4[bg])
                        self.ForecastedStandardDeviationDemand[t][j][c][l] = STD_demand_for_bg

        ################################## Generate the initial inventory structure
        self.Initial_Platelet_Inventory = np.zeros((len(self.BloodGPSet), len(self.PlateletAgeSet), len(self.HospitalSet)))
        
        if (self.Do_you_want_Random_Initial_Platelet_Inventory == 1):
            
            for c in self.BloodGPSet:
                for r in self.PlateletAgeSet:
                    for h in self.HospitalSet:
                        Initial_Inventory = random.randint(self.Min_Initial_Platelet_Inventory, self.Max_Initial_Platelet_Inventory)
                        self.Initial_Platelet_Inventory[c][r][h] = Initial_Inventory
        else:
            # Calculate initial inventory for the first time period (t=0) based on forecasted average demand
            for c, bg in enumerate(self.BloodGPSet):
                for r in self.PlateletAgeSet:
                    for h in self.HospitalSet:
                        if h < self.NrHospitals:
                            # Sum forecasted demand for the first time period across all demand locations and injury levels
                            sum_forecasted_demand = sum(self.ForecastedAverageDemand[0, :, c, :].flatten())
                            # Apply safety factor only for the high-priority demand in the first age category at hospital facilities
                            if r == 1:
                                initial_inventory = round(sum_forecasted_demand * self.Safety_Factor_Initital_Platelet / self.NrHospitals)
                            else:
                                initial_inventory = round(sum_forecasted_demand / (self.NrHospitals + 3))  # Assume 3 ACFs for medium and low priority
                        else:
                            # ACF facilities: apply a different division factor if needed
                            sum_forecasted_demand = sum(self.ForecastedAverageDemand[0, :, c, :].flatten())
                            initial_inventory = round(sum_forecasted_demand * self.Safety_Factor_Initital_Platelet / 4)  # Assume 4 ACFs
                        # Set the initial inventory
                        self.Initial_Platelet_Inventory[c][r][h] = round(initial_inventory)

        ##################################  Calculating Average Hospital Bed Capacity
        self.ForecastedAverageHospital_Bed_Capacity = np.zeros((len(self.TimeBucketSet), len(self.HospitalSet)))
        
        for t in self.TimeBucketSet:
            for h in self.HospitalSet:
                # Generate total bed for each location and time period
                if t == 0:
                    if self.Do_you_want_Dependent_Hospital_Capacities_based_on_Demands == 1:
                        AvgDemand = (self.Min_Demand_in_Each_Location + self.Max_Demand_in_Each_Location) / 2
                        HighMedPriority = self.Priority_Patient_Percent[0] + self.Priority_Patient_Percent[1]
                        total_bed_2 = round(((AvgDemand * HighMedPriority * self.NrDemandLocations) / self.NrHospitals) * (1.1 ** (self.NrTimeBucket - 1)))
                        total_bed_lower_bound = round(total_bed_2 * 0.9)
                        total_bed_upper_bound = round(total_bed_2 * 1.1)
                        total_bed = random.randint(total_bed_lower_bound, total_bed_upper_bound)
                        #total_bed = round((total_bed_2 + (random.uniform(2, 2) * total_bed_2)) / 2)
                        self.ForecastedAverageHospital_Bed_Capacity[t][h] = total_bed 
                    else:
                        #total_bed = random.randint(self.Min_Hospital_Bed_Capacity, self.Max_Hospital_Bed_Capacity)
                        total_bed = (self.Min_Hospital_Bed_Capacity + self.Max_Hospital_Bed_Capacity) / 2
                        self.ForecastedAverageHospital_Bed_Capacity[t][h] = total_bed   
                else:
                    self.ForecastedAverageHospital_Bed_Capacity[t][h] = self.ForecastedAverageHospital_Bed_Capacity[0][h]  # Because, once any disaster happens, after the first stage, the hospital treatment capacities will be seen and fixed therefore!

        ##################################  Calculating STD Hospital Bed Capacity
        self.ForecastedSTDHospital_Bed_Capacity = np.zeros((len(self.TimeBucketSet), len(self.HospitalSet)))
        
        # The standard deviation is constant for a uniform distribution between a and b
        # std_dev = (self.Max_Hospital_Bed_Capacity - self.Min_Hospital_Bed_Capacity) / (np.sqrt(12))
        std_dev = (self.Max_Hospital_Bed_Capacity - self.Min_Hospital_Bed_Capacity) / 2
        
        # Assign the constant standard deviation to each entry
        for t in self.TimeBucketSet:
            for h in self.HospitalSet:
                if self.Do_you_want_Dependent_Hospital_Capacities_based_on_Demands == 1:
                    if t == 0:
                        self.ForecastedSTDHospital_Bed_Capacity[t][h] = round(self.Hospital_Bed_Capacity_STD_Coeff * self.ForecastedAverageHospital_Bed_Capacity[t][h]) #50% variance in Hospital capacities after disaster!
                    else:
                        self.ForecastedSTDHospital_Bed_Capacity[t][h] = 0               # Because, once any disaster happens, after the first stage, the hospital treatment capacities will be seen and fixed therefore!                    
                else:
                    if t == 0:
                        self.ForecastedSTDHospital_Bed_Capacity[t][h] = round(std_dev)
                    else:
                        self.ForecastedSTDHospital_Bed_Capacity[t][h] = 0               # Because, once any disaster happens, after the first stage, the hospital treatment capacities will be seen and fixed therefore!
            
        ##################################  Calculating Rescue Vehicle Capacity

        a = (self.Square_Dimension / 2)
        nominal_Rescue_Vehicle_Capacity = math.floor(0.5 * (self.Speed / a) * self.Working_Hours_per_Day * self.Number_of_Planning_Days)    # Approximate number of patients transferred in the planning Horizon (Ex: 1 week)
        
        for m in self.RescueVehicleSet:  # Assuming Number_Vehicle_Mode means there are four modes (0 to 3)
            new_Rescue_Vehicle_Capacity = 0
            if m == 0:
                new_Rescue_Vehicle_Capacity = 1 * nominal_Rescue_Vehicle_Capacity
            elif m == 1:
                new_Rescue_Vehicle_Capacity = 2 * nominal_Rescue_Vehicle_Capacity
            elif m == 2:
                new_Rescue_Vehicle_Capacity = 3 * nominal_Rescue_Vehicle_Capacity
            elif m >= 3:
                print("\nThe number of Vehicles (index m) cannot be more than 3!!!!!!!!!\n")
                input("Press Enter to continue...")  # system("Pause") equivalent in Python
            self.Rescue_Vehicle_Capacity.append(new_Rescue_Vehicle_Capacity)
        
        ##################################  Calculating Distances

        self.Hospital_Position = self.Generate_Positions(self.NrHospitals)
        #print("Hospital_Positions: \n", self.Hospital_Position)

        self.ACF_Position = self.Generate_Positions(self.NrACFPPoints)
        #print("ACF_Position: \n", self.ACF_Position)

        self.DemandLocation_Position = self.Generate_Positions(self.NrDemandLocations)
        #print("DemandLocation_position: \n", self.DemandLocation_Position)

        # Generate plotting data if required
        if self.Do_you_need_point_plot == 1:
            self.Plot_Positions()

        self.Distance_D_A = self.Calculate_Distances(self.DemandLocation_Position, self.ACF_Position)
        self.Distance_A_H = self.Calculate_Distances(self.ACF_Position, self.Hospital_Position)
        self.Distance_D_H = self.Calculate_Distances(self.DemandLocation_Position, self.Hospital_Position)
        self.Distance_A_A = self.Calculate_Distances_Within_Same(self.ACF_Position)
        self.Distance_H_H = self.Calculate_Distances_Within_Same(self.Hospital_Position)

        ##################################  Calculating Casualty_Shortage_Cost
        self.Casualty_Shortage_Cost = np.zeros((len(self.InjuryLevelSet), len(self.DemandSet)))
        
        for j in self.InjuryLevelSet:
            for l in self.DemandSet:
                New_Casualty_Shortage_Cost = random.randint(self.Min_Casualty_Shortage_Cost, self.Max_Casualty_Shortage_Cost)
                if j == 0:
                    self.Casualty_Shortage_Cost[j][l] = New_Casualty_Shortage_Cost
                if j == 1:
                    self.Casualty_Shortage_Cost[j][l] = (New_Casualty_Shortage_Cost * 3)/ 4
                if j == 2:
                    self.Casualty_Shortage_Cost[j][l] = (New_Casualty_Shortage_Cost / 2)
                   
        ##################################  Calculating Number_Apheresis_Machine_Hospital
        self.Number_Apheresis_Machine_Hospital = np.zeros((len(self.HospitalSet)))
        
        for h in self.HospitalSet:
            self.Number_Apheresis_Machine_Hospital[h] = random.randint(self.Min_Number_of_Apheresis_Machines_Hospital, self.Max_Number_of_Apheresis_Machines_Hospital)
                   
        ##################################  Calculating Number_Rescue_Vehicle_ACF
        self.Number_Rescue_Vehicle_ACF = np.zeros((len(self.RescueVehicleSet)))
        #print("Number_Rescue_Vehicle_ACF[m]: ", self.Number_Rescue_Vehicle_ACF[m])
        
        Total_Demand_Per_Period = self.ForecastedAverageDemand.sum(axis=(1, 2, 3))
        #print("Total_Demand_Per_Period: ", Total_Demand_Per_Period)

        max_demand = Total_Demand_Per_Period.max()
        #print("max_demand: ", max_demand)
        
        a = 0
        for m in self.RescueVehicleSet:
            a = a + math.ceil(max_demand / self.Rescue_Vehicle_Capacity[m])
        a = math.ceil((a / self.NrRescueVehicles) * self.Safety_Factor_Rescue_Vehicle_ACF)

        for m in self.RescueVehicleSet:
            if a > 0 and m != (self.NrRescueVehicles - 1):
                c = round(a / self.NrRescueVehicles)
                self.Number_Rescue_Vehicle_ACF[m] = 4 * c  # Create random number between 0 and a!
                a -= c
            elif a > 0 and m == self.NrRescueVehicles - 1:
                self.Number_Rescue_Vehicle_ACF[m] = 4 * a

        ##################################  Calculating Number_Rescue_Vehicle_Hospital
        self.Number_Rescue_Vehicle_Hospital = np.zeros((len(self.RescueVehicleSet), len(self.HospitalSet)))
        
        for h in self.HospitalSet:
            a = 0
            for m in self.RescueVehicleSet:
                b = self.ForecastedAverageHospital_Bed_Capacity[0][h]
                a = a + math.ceil( b / self.Rescue_Vehicle_Capacity[m] )
            
            a = a + math.ceil((b / self.NrRescueVehicles) * self.Safety_Factor_Rescue_Vehicle_Hospital)
            remaining_b  = a
            for m in self.RescueVehicleSet:
                if remaining_b > 0 and m != (self.NrRescueVehicles - 1):
                    c = random.randint(0, remaining_b)  # Generate a random number between 0 and remaining_b
                    self.Number_Rescue_Vehicle_Hospital[m][h] = c
                    remaining_b -= c
                elif remaining_b > 0 and m == (self.NrRescueVehicles - 1):
                    self.Number_Rescue_Vehicle_Hospital[m][h] = int(self.Safety_Factor_Rescue_Vehicle_Hospital * remaining_b)
                    
        ##################################  Calculating ForecastedAverageWhole_Blood_Donors and ForecastedSTDWhole_Blood_Donors
        self.Apheresis_Machine_Production_Capacity = round((self.Working_Hours_per_Day_Apheresis * 60) / self.Rquired_Time_For_One_Apheresis_collection);

        ##################################  Calculating ForecastedAverageWhole_Blood_Donors
        self.ForecastedAverageWhole_Blood_Donors_In_Each_Period = np.zeros(len(self.TimeBucketSet))
        self.ForecastedAverageWhole_Blood_Donors = np.zeros((len(self.TimeBucketSet), len(self.BloodGPSet), len(self.HospitalSet)))
        self.ForecastedSTDWhole_Blood_Donors = np.zeros((len(self.TimeBucketSet), len(self.BloodGPSet), len(self.HospitalSet)))

        # Calculate theoretical standard deviation
        theoretical_std = ((self.Max_Number_of_Whole_Blood_Donors_in_Each_Period_in_Each_Location - self.Min_Number_of_Whole_Blood_Donors_in_Each_Period_in_Each_Location) / 2) * self.NrDemandLocations
        
        for t in self.TimeBucketSet:
            self.ForecastedAverageWhole_Blood_Donors_In_Each_Period[t] = ((self.Min_Number_of_Whole_Blood_Donors_in_Each_Period_in_Each_Location + self.Max_Number_of_Whole_Blood_Donors_in_Each_Period_in_Each_Location) / 2) * self.NrDemandLocations

            donors_remaining = self.ForecastedAverageWhole_Blood_Donors_In_Each_Period[t]
            donors_remaining_STD = theoretical_std
            if len(self.BloodGPSet) == 8:
                allocations = np.random.multinomial(donors_remaining, list(self.blood_group_percentages_8.values()))
                allocations_STD = np.random.multinomial(donors_remaining_STD, list(self.blood_group_percentages_8.values()))
            else:
                allocations = np.random.multinomial(donors_remaining, list(self.blood_group_percentages_4.values()))
                allocations_STD = np.random.multinomial(donors_remaining_STD, list(self.blood_group_percentages_4.values()))

            if len(self.BloodGPSet) == 8:
                for i, c in enumerate(self.blood_group_percentages_8):
                    allocations_per_hospital = np.random.multinomial(allocations[i], [1/len(self.HospitalSet)]*len(self.HospitalSet))
                    allocations_per_hospital_STD = np.random.multinomial(allocations_STD[i], [1/len(self.HospitalSet)]*len(self.HospitalSet))
                    for h, hospital in enumerate(self.HospitalSet):
                        self.ForecastedAverageWhole_Blood_Donors[t, i, h] = round(allocations_per_hospital[h])
                        self.ForecastedSTDWhole_Blood_Donors[t, i, h] = round(allocations_per_hospital_STD[h] * np.sqrt(self.blood_group_percentages_8[c]))
            else:
                for i, c in enumerate(self.blood_group_percentages_4):
                    allocations_per_hospital = np.random.multinomial(allocations[i], [1/len(self.HospitalSet)]*len(self.HospitalSet))
                    allocations_per_hospital_STD = np.random.multinomial(allocations_STD[i], [1/len(self.HospitalSet)]*len(self.HospitalSet))
                    for h, hospital in enumerate(self.HospitalSet):
                        self.ForecastedAverageWhole_Blood_Donors[t, i, h] = round(allocations_per_hospital[h])
                        self.ForecastedSTDWhole_Blood_Donors[t, i, h] = round(allocations_per_hospital_STD[h] * np.sqrt(self.blood_group_percentages_4[c]))
            
        print("ForecastedAverageWhole_Blood_Donors:\n", self.ForecastedAverageWhole_Blood_Donors)
        print("ForecastedSTDWhole_Blood_Donors:\n", self.ForecastedSTDWhole_Blood_Donors)
        print("---------------------------")
        ##################################  Calculating ForecastedAverageApheresis_Donors
        self.ForecastedAverageApheresis_Donors_In_Each_Period = np.zeros(len(self.TimeBucketSet))
        self.ForecastedAverageApheresis_Donors = np.zeros((len(self.TimeBucketSet), len(self.BloodGPSet), len(self.FacilitySet)))
        self.ForecastedSTDApheresis_Donors = np.zeros((len(self.TimeBucketSet), len(self.BloodGPSet), len(self.FacilitySet)))

        # Calculate theoretical standard deviation
        theoretical_std = ((self.Max_Number_of_Apheresis_Donors_in_Each_Period_in_Each_Location - self.Min_Number_of_Apheresis_Donors_in_Each_Period_in_Each_Location) / 2) * self.NrDemandLocations
        
        for t in self.TimeBucketSet:
            self.ForecastedAverageApheresis_Donors_In_Each_Period[t] = ((self.Min_Number_of_Apheresis_Donors_in_Each_Period_in_Each_Location + self.Max_Number_of_Apheresis_Donors_in_Each_Period_in_Each_Location) / 2) * self.NrDemandLocations

            donors_remaining = self.ForecastedAverageApheresis_Donors_In_Each_Period[t]
            donors_remaining_STD = theoretical_std
            if len(self.BloodGPSet) == 8:
                allocations = np.random.multinomial(donors_remaining, list(self.blood_group_percentages_8.values()))
                allocations_STD = np.random.multinomial(donors_remaining_STD, list(self.blood_group_percentages_8.values()))
            else:
                allocations = np.random.multinomial(donors_remaining, list(self.blood_group_percentages_4.values()))
                allocations_STD = np.random.multinomial(donors_remaining_STD, list(self.blood_group_percentages_4.values()))

            if len(self.BloodGPSet) == 8:
                for i, c in enumerate(self.blood_group_percentages_8):
                    allocations_per_facility = np.random.multinomial(allocations[i], [1/len(self.FacilitySet)]*len(self.FacilitySet))
                    allocations_per_facility_STD = np.random.multinomial(allocations_STD[i], [1/len(self.FacilitySet)]*len(self.FacilitySet))
                    for u, facility in enumerate(self.FacilitySet):
                        self.ForecastedAverageApheresis_Donors[t, i, u] = round(allocations_per_facility[u])
                        self.ForecastedSTDApheresis_Donors[t, i, u] = round(allocations_per_facility_STD[u] * np.sqrt(self.blood_group_percentages_8[c]))
            else:
                for i, c in enumerate(self.blood_group_percentages_4):
                    allocations_per_facility = np.random.multinomial(allocations[i], [1/len(self.FacilitySet)]*len(self.FacilitySet))
                    allocations_per_facility_STD = np.random.multinomial(allocations_STD[i], [1/len(self.FacilitySet)]*len(self.FacilitySet))
                    for u, facility in enumerate(self.FacilitySet):
                        self.ForecastedAverageApheresis_Donors[t, i, u] = round(allocations_per_facility[u])
                        self.ForecastedSTDApheresis_Donors[t, i, u] = round(allocations_per_facility_STD[u] * np.sqrt(self.blood_group_percentages_4[c]))
            
        print("ForecastedAverageApheresis_Donors:\n", self.ForecastedAverageApheresis_Donors)
        print("ForecastedSTDApheresis_Donors:\n", self.ForecastedSTDApheresis_Donors)
        print("---------------------------")        
        ##################################  Calculating Whole_Blood_Production_Time
        self.Whole_Blood_Production_Time = 1        #Reference for 1 day production time: "Collaborative activities for matching supply and demand in the platelet network"
        self.Print_Attributes()
            
        if Constants.Debug:  print("-------------")
  
    def Generate_Positions(self, number):
        if Constants.Debug: print("\n We are in 'Instance' Class -- Generate_Positions")

        positions = []
        for i in range(number):
            pos = []
            for j in range(2):  
                vv = random.random() * self.Square_Dimension
                vv = int(vv * 100) / 100.0  
                pos.append(vv)
            positions.append(pos)
        return positions

    def Calculate_Distances(self, set1, set2):
        distances = []
        for pos1 in set1:
            row = []
            for pos2 in set2:
                distance = math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
                row.append(round(distance, 2))
            distances.append(row)
        return distances

    def Calculate_Distances_Within_Same(self, positions):
        distances = []
        for i, pos1 in enumerate(positions):
            row = []
            for j, pos2 in enumerate(positions):
                if i == j:
                    distance = 1000  # Special case for distance to itself
                else:
                    distance = math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
                row.append(round(distance, 2))
            distances.append(row)
        return distances
        
    def Plot_Positions(self):
        if Constants.Debug: print("\nWe are in 'Instance' Class -- Plot_Positions")

        # Correct the indices in list comprehensions for plotting positions
        hospital_plot = [[pos[0], pos[1]] for pos in self.Hospital_Position]
        acf_plot = [[pos[0], pos[1]] for pos in self.ACF_Position]
        demand_location_plot = [[pos[0], pos[1]] for pos in self.DemandLocation_position]

        # Print positions for verification
        print("Hospital Plotting Positions:", hospital_plot)
        print("ACF Plotting Positions:", acf_plot)
        print("Demand Location Plotting Positions:", demand_location_plot)

        # Call to actual plotting method, assuming it uses matplotlib to plot
        self.Plot_Points_matplotlib(hospital_plot, acf_plot, demand_location_plot)

    def Plot_Points_matplotlib(self, hospital, acf, demand_location):
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 6))
        plt.scatter(*zip(*hospital), c='blue', label='Hospitals')
        plt.scatter(*zip(*acf), c='green', label='ACFs')
        plt.scatter(*zip(*demand_location), c='red', label='Demand Locations')
        plt.legend()
        plt.xlabel('X Coordinate')
        plt.ylabel('Y Coordinate')
        plt.title('Facility Positions')
        plt.grid(True)
        plt.show()

    def SaveInstanceToPickle(self):
        # Define the filename using the instance name with a .pkl extension
        filename = f"./Instances/{self.InstanceName}.pkl"
        
        # Use 'wb' to write in binary mode
        with open(filename, 'wb') as file:
            data_to_save = {
                'NrTimeBucket': self.NrTimeBucket,
                'NrACFPPoints': self.NrACFPPoints,
                'NrHospitals': self.NrHospitals,
                'NrDemandLocations': self.NrDemandLocations,
                'NrFacilities': self.NrFacilities,
                'NrRescueVehicles': self.NrRescueVehicles,
                'NRBloodGPs': self.NRBloodGPs,
                'NRInjuryLevels': self.NRInjuryLevels,
                'NRPlateletAges': self.NRPlateletAges,
                'G_c': self.G_c,
                'J_u': self.J_u,
                'J_r': self.J_r,               
                'R_j': self.R_j,               
                'Total_Budget_ACF_Establishment': self.Total_Budget_ACF_Establishment,
                'Platelet_Units_Apheresis': self.Platelet_Units_Apheresis,
                'Whole_Blood_Production_Time': self.Whole_Blood_Production_Time,
                'Apheresis_Machine_Production_Capacity': self.Apheresis_Machine_Production_Capacity,
                'Fixed_Cost_ACF': self.Fixed_Cost_ACF,
                'Fixed_Cost_ACF_Constraint': self.Fixed_Cost_ACF_Constraint,
                'Platelet_Wastage_Cost': self.Platelet_Wastage_Cost,
                'Platelet_Inventory_Cost': self.Platelet_Inventory_Cost,
                'VehicleAssignment_Cost': self.VehicleAssignment_Cost,
                'ApheresisMachineAssignment_Cost': self.ApheresisMachineAssignment_Cost,
                'ApheresisExtraction_Cost': self.ApheresisExtraction_Cost,
                'WholeExtraction_Cost': self.WholeExtraction_Cost,
                'Platelet_Units_Required_for_Injury': self.Platelet_Units_Required_for_Injury,
                'Postponing_Cost_Surgery': self.Postponing_Cost_Surgery,
                'Total_Apheresis_Machine_ACF': self.Total_Apheresis_Machine_ACF,
                'Substitution_Weight': self.Substitution_Weight,
                'ACF_Bed_Capacity': self.ACF_Bed_Capacity,
                'Initial_Platelet_Inventory': self.Initial_Platelet_Inventory,
                'ForecastedAverageDemand': self.ForecastedAverageDemand,
                'ForecastedStandardDeviationDemand': self.ForecastedStandardDeviationDemand,
                'ForecastedAverageHospital_Bed_Capacity': self.ForecastedAverageHospital_Bed_Capacity,
                'ForecastedSTDHospital_Bed_Capacity': self.ForecastedSTDHospital_Bed_Capacity,
                'Rescue_Vehicle_Capacity': self.Rescue_Vehicle_Capacity,
                'Distance_D_A': self.Distance_D_A,
                'Distance_A_H': self.Distance_A_H,
                'Distance_D_H': self.Distance_D_H,
                'Distance_A_A': self.Distance_A_A,
                'Distance_H_H': self.Distance_H_H,
                'Casualty_Shortage_Cost': self.Casualty_Shortage_Cost,
                'Number_Apheresis_Machine_Hospital': self.Number_Apheresis_Machine_Hospital,
                'Number_Rescue_Vehicle_ACF': self.Number_Rescue_Vehicle_ACF,
                'Number_Rescue_Vehicle_Hospital': self.Number_Rescue_Vehicle_Hospital,
                'ForecastedAverageWhole_Blood_Donors': self.ForecastedAverageWhole_Blood_Donors,
                'ForecastedSTDWhole_Blood_Donors': self.ForecastedSTDWhole_Blood_Donors,
                'ForecastedAverageApheresis_Donors': self.ForecastedAverageApheresis_Donors,
                'ForecastedSTDApheresis_Donors': self.ForecastedSTDApheresis_Donors
            }
            
            # Save the data using pickle
            pickle.dump(data_to_save, file)

        print(f"Data saved to {filename}")

    def SaveInstanceToTXTFileWithExplaination(self):
        if Constants.Debug: print("\n We are in 'Instance' Class -- SaveInstanceToTXTFileWithExplaination")

        filename = f"./Instances/{self.InstanceName}_WithExplaination.DATA"
        with open(filename, 'w') as file:
            # Writing integers with labels
            file.write(f"NrTimeBucket:\n{self.NrTimeBucket}\n\n")
            file.write(f"NrACFPPoints:\n{self.NrACFPPoints}\n\n")
            file.write(f"NrHospitals:\n{self.NrHospitals}\n\n")
            file.write(f"NrDemandLocations:\n{self.NrDemandLocations}\n\n")
            file.write(f"NrFacilities:\n{self.NrFacilities}\n\n")
            file.write(f"NrRescueVehicles:\n{self.NrRescueVehicles}\n\n")
            file.write(f"NRBloodGPs:\n{self.NRBloodGPs}\n\n")
            file.write(f"NRInjuryLevels:\n{self.NRInjuryLevels}\n\n")
            file.write(f"NRPlateletAges:\n{self.NRPlateletAges}\n\n")
            file.write(f"G_c:\n{self.G_c}\n\n")
            file.write(f"J_u:\n{self.J_u}\n\n")
            file.write(f"J_r:\n{self.J_r}\n\n")             
            file.write(f"R_j:\n{self.R_j}\n\n")             
            file.write(f"Total_Budget_ACF_Establishment:\n{self.Total_Budget_ACF_Establishment}\n\n")
            file.write(f"Platelet_Units_Apheresis:\n{self.Platelet_Units_Apheresis}\n\n")
            file.write(f"Whole_Blood_Production_Time:\n{self.Whole_Blood_Production_Time}\n\n")
            file.write(f"Apheresis_Machine_Production_Capacity:\n{self.Apheresis_Machine_Production_Capacity}\n\n")            
            # Writing lists and matrices with labels and formatting
            file.write("Fixed_Cost_ACF:\n")
            file.write(f"{self.Fixed_Cost_ACF}\n\n")
            file.write("Fixed_Cost_ACF_Constraint:\n")
            file.write(f"{self.Fixed_Cost_ACF_Constraint}\n\n")
            file.write("Platelet_Wastage_Cost:\n")
            file.write(f"{self.Platelet_Wastage_Cost}\n\n")
            file.write("Platelet_Inventory_Cost:\n")
            file.write(f"{self.Platelet_Inventory_Cost}\n\n")
            file.write("VehicleAssignment_Cost:\n")
            file.write(f"{self.VehicleAssignment_Cost}\n\n")
            file.write("ApheresisMachineAssignment_Cost:\n")
            file.write(f"{self.ApheresisMachineAssignment_Cost}\n\n")
            file.write("ApheresisExtraction_Cost:\n")
            file.write(f"{self.ApheresisExtraction_Cost}\n\n")
            file.write("WholeExtraction_Cost:\n")
            file.write(f"{self.WholeExtraction_Cost}\n\n")
            file.write("Platelet_Units_Required_for_Injury:\n")
            file.write(f"{self.Platelet_Units_Required_for_Injury}\n\n")
            file.write("Postponing_Cost_Surgery:\n")
            file.write(f"{self.Postponing_Cost_Surgery}\n\n")
            file.write("Total_Apheresis_Machine_ACF:\n")
            file.write(f"{self.Total_Apheresis_Machine_ACF}\n\n")
            file.write("Substitution_Weight:\n")
            file.write(f"{self.Substitution_Weight}\n\n")
            file.write("ACF_Bed_Capacity:\n")
            file.write(f"{self.ACF_Bed_Capacity}\n\n")
            file.write("Initial_Platelet_Inventory:\n")
            file.write(f"{self.Initial_Platelet_Inventory}\n\n")
            file.write("ForecastedAverageDemand:\n")
            file.write(f"{self.ForecastedAverageDemand}\n\n")
            file.write("ForecastedStandardDeviationDemand:\n")
            file.write(f"{self.ForecastedStandardDeviationDemand}\n\n")
            file.write("ForecastedAverageHospital_Bed_Capacity:\n")
            file.write(f"{self.ForecastedAverageHospital_Bed_Capacity}\n\n")
            file.write("ForecastedSTDHospital_Bed_Capacity:\n")
            file.write(f"{self.ForecastedSTDHospital_Bed_Capacity}\n\n")
            file.write("Rescue_Vehicle_Capacity:\n")
            file.write(f"{self.Rescue_Vehicle_Capacity}\n\n")
            file.write("Distance_D_A:\n")
            file.write(f"{self.Distance_D_A}\n\n")
            file.write("Distance_A_H:\n")
            file.write(f"{self.Distance_A_H}\n\n")
            file.write("Distance_D_H:\n")
            file.write(f"{self.Distance_D_H}\n\n")
            file.write("Distance_A_A:\n")
            file.write(f"{self.Distance_A_A}\n\n")
            file.write("Distance_H_H:\n")
            file.write(f"{self.Distance_H_H}\n\n")
            file.write("Casualty_Shortage_Cost:\n")
            file.write(f"{self.Casualty_Shortage_Cost}\n\n")
            file.write("Number_Apheresis_Machine_Hospital:\n")
            file.write(f"{self.Number_Apheresis_Machine_Hospital}\n\n")
            file.write("Number_Rescue_Vehicle_ACF:\n")
            file.write(f"{self.Number_Rescue_Vehicle_ACF}\n\n")
            file.write("Number_Rescue_Vehicle_Hospital:\n")
            file.write(f"{self.Number_Rescue_Vehicle_Hospital}\n\n")
            file.write("ForecastedAverageWhole_Blood_Donors:\n")
            file.write(f"{self.ForecastedAverageWhole_Blood_Donors}\n\n")
            file.write("ForecastedSTDWhole_Blood_Donors:\n")
            file.write(f"{self.ForecastedSTDWhole_Blood_Donors}\n\n")
            file.write("ForecastedAverageApheresis_Donors:\n")
            file.write(f"{self.ForecastedAverageApheresis_Donors}\n\n")
            file.write("ForecastedSTDApheresis_Donors:\n")
            file.write(f"{self.ForecastedSTDApheresis_Donors}\n\n")
            file.write("Whole_Blood_Production_Time:\n")
            file.write(f"{self.Whole_Blood_Production_Time}\n\n")

            print(f"Instance saved to {filename}")

    # This function print the instance on the screen
    def PrintInstance(self):
        if Constants.Debug: print("\n We are in 'Instance' Class -- PrintInstance")
        
        print("instance: %s" % self.InstanceName)
        print("Instance with %d Time Periods, %d ACF Points, %d Hospitals, %d Demand Locations" % (self.NrTimeBucket, self.NrACFPPoints, self.NrHospitals, self.NrDemandLocations))

    def ComputeIndices(self):
        if Constants.Debug: print("\n We are in 'Instance' Class -- ComputeIndices")
        self.NrTimeBucketWithoutUncertainty = self.NrTimeBucketWithoutUncertaintyAfter + self.NrTimeBucketWithoutUncertaintyBefore
        self.TimeBucketSet = range(self.NrTimeBucket)
        self.ACFPPointSet = range(self.NrACFPPoints)
        self.HospitalSet = range(self.NrHospitals)
        self.DemandSet = range(self.NrDemandLocations)
        self.FacilitySet = range(self.NrFacilities)
        self.RescueVehicleSet = range(self.NrRescueVehicles)
        self.BloodGPSet = range(self.NRBloodGPs)
        self.InjuryLevelSet = range(self.NRInjuryLevels)
        self.PlateletAgeSet = range(self.NRPlateletAges)

    # This function print the instance on the screen
    def Print_Attributes(self):
        if Constants.Debug: print("\n We are in 'Instance' Class -- Print_Attributes")

        print("\n------")

        print("NrTimeBucket: ", self.NrTimeBucket)
        print("NrACFPPoints: ", self.NrACFPPoints)
        print("NrHospitals: ", self.NrHospitals)
        print("NrDemandLocations: ", self.NrDemandLocations)
        print("NrFacilities: ", self.NrFacilities)
        print("NrRescueVehicles: ", self.NrRescueVehicles)
        print("NRBloodGPs: ", self.NRBloodGPs)
        print("NRInjuryLevels: ", self.NRInjuryLevels)
        print("NRPlateletAges: ", self.NRPlateletAges) 
        print("G_c:\n", self.G_c) 
        print("J_u:\n", self.J_u) 
        print("J_r:\n", self.J_r) 
        print("R_j:\n", self.R_j) 
        print("Total_Budget_ACF_Establishment: ", self.Total_Budget_ACF_Establishment) 
        print("Platelet_Units_Apheresis: ", self.Platelet_Units_Apheresis) 
        print("Whole_Blood_Production_Time: ", self.Whole_Blood_Production_Time) 
        print("Apheresis_Machine_Production_Capacity:", self.Apheresis_Machine_Production_Capacity)
        print("Fixed_Cost_ACF[i]:\n", self.Fixed_Cost_ACF)        
        print("Fixed_Cost_ACF_Constraint[i]:\n", self.Fixed_Cost_ACF_Constraint)        
        print("Platelet_Wastage_Cost[u]:\n", self.Platelet_Wastage_Cost)
        print("Platelet_Inventory_Cost[u]:\n", self.Platelet_Inventory_Cost)
        print("VehicleAssignment_Cost[m]:\n", self.VehicleAssignment_Cost)
        print("ApheresisMachineAssignment_Cost[u]:\n", self.ApheresisMachineAssignment_Cost)
        print("ApheresisExtraction_Cost[u]:\n", self.ApheresisExtraction_Cost)
        print("WholeExtraction_Cost[u]:\n", self.WholeExtraction_Cost)
        print("Platelet_Units_Required_for_Injury:\n", self.Platelet_Units_Required_for_Injury)
        print("Postponing_Cost_Surgery:\n", self.Postponing_Cost_Surgery)
        print("Total_Apheresis_Machine_ACF[t]:\n", self.Total_Apheresis_Machine_ACF)
        print("Substitution_Weight:\n", self.Substitution_Weight)
        print("ACF_Bed_Capacity:\n", self.ACF_Bed_Capacity)
        print("Initial_Platelet_Inventory[c][r][h]:\n", self.Initial_Platelet_Inventory)
        print("ForecastedAverageDemand[t][j][c][l]:\n", self.ForecastedAverageDemand)     
        print("ForecastedStandardDeviationDemand[t][j][c][l]:\n", self.ForecastedStandardDeviationDemand)
        print("ForecastedAverageHospital_Bed_Capacity[t][h]:\n ", self.ForecastedAverageHospital_Bed_Capacity)
        print("ForecastedSTDHospital_Bed_Capacity[t][h]:\n", self.ForecastedSTDHospital_Bed_Capacity)
        print("Rescue_Vehicle_Capacity: ", self.Rescue_Vehicle_Capacity)
        print("Distance_D_A:\n", self.Distance_D_A)
        print("Distance_A_H:\n", self.Distance_A_H)
        print("Distance_D_H:\n", self.Distance_D_H)
        print("Distance_A_A:\n", self.Distance_A_A)
        print("Distance_H_H:\n", self.Distance_H_H)
        print("Casualty_Shortage_Cost[j][l]:\n ", self.Casualty_Shortage_Cost)
        print("Number_Apheresis_Machine_Hospital[h]:\n", self.Number_Apheresis_Machine_Hospital)
        print("Number_Rescue_Vehicle_ACF[m]:\n", self.Number_Rescue_Vehicle_ACF)
        print("Number_Rescue_Vehicle_Hospital[m][h]: \n", self.Number_Rescue_Vehicle_Hospital)
        print("ForecastedAverageWhole_Blood_Donors:\n", self.ForecastedAverageWhole_Blood_Donors)
        print("ForecastedSTDWhole_Blood_Donors:\n", self.ForecastedSTDWhole_Blood_Donors)
        print("ForecastedAverageApheresis_Donors:\n", self.ForecastedAverageApheresis_Donors)  
        print("ForecastedSTDApheresis_Donors:\n", self.ForecastedSTDApheresis_Donors)        
        
        print("------\n")

    def LoadInstanceFromPickle(self,instancename):
        # Define the filename using the instance name with a .pkl extension

        if platform.system() == "Linux":
            # Use the absolute path for the Linux system
            instances_dir = "/home/pfarghad/Myschedulingmodel_2/SDDP/Instances"
        else:
            # Use the desired path for your local system (Windows in this case)
            instances_dir = r"C:\PhD\Thesis\Papers\2nd\Code\SDDP\Instances"
        
        # Define the filename using the instance name with a .pkl extension
        filename = os.path.join(instances_dir, f"{instancename}.pkl")
        print(f"Loading instance from {filename}")  # Debugging line

        # filename = f"./Instances/{instancename}.pkl"
        
        # Use 'rb' to read in binary mode
        with open(filename, 'rb') as file:
            # Load the data using pickle
            data_loaded = pickle.load(file)
            
            # Assign the loaded data back to the instance attributes
            self.NrTimeBucket = data_loaded['NrTimeBucket']
            self.NrACFPPoints = data_loaded['NrACFPPoints']
            self.NrHospitals = data_loaded['NrHospitals']
            self.NrDemandLocations = data_loaded['NrDemandLocations']
            self.NrFacilities = data_loaded['NrFacilities']
            self.NrRescueVehicles = data_loaded['NrRescueVehicles']
            self.NRBloodGPs = data_loaded['NRBloodGPs']
            self.NRInjuryLevels = data_loaded['NRInjuryLevels']
            self.NRPlateletAges = data_loaded['NRPlateletAges']
            self.G_c = data_loaded['G_c']
            self.J_u = data_loaded['J_u']
            self.J_r = data_loaded['J_r']           
            self.R_j = data_loaded['R_j']           
            self.Total_Budget_ACF_Establishment = data_loaded['Total_Budget_ACF_Establishment']
            self.Platelet_Units_Apheresis = data_loaded['Platelet_Units_Apheresis']
            self.Whole_Blood_Production_Time = data_loaded['Whole_Blood_Production_Time']
            self.Apheresis_Machine_Production_Capacity = data_loaded['Apheresis_Machine_Production_Capacity']
            self.Fixed_Cost_ACF = data_loaded['Fixed_Cost_ACF']
            self.Fixed_Cost_ACF_Constraint = data_loaded['Fixed_Cost_ACF_Constraint']
            self.Platelet_Wastage_Cost = data_loaded['Platelet_Wastage_Cost']
            self.Platelet_Inventory_Cost = data_loaded['Platelet_Inventory_Cost']
            self.VehicleAssignment_Cost = data_loaded['VehicleAssignment_Cost']
            self.ApheresisMachineAssignment_Cost = data_loaded['ApheresisMachineAssignment_Cost']
            self.ApheresisExtraction_Cost = data_loaded['ApheresisExtraction_Cost']
            self.WholeExtraction_Cost = data_loaded['WholeExtraction_Cost']
            self.Platelet_Units_Required_for_Injury = data_loaded['Platelet_Units_Required_for_Injury']
            self.Postponing_Cost_Surgery = data_loaded['Postponing_Cost_Surgery']
            self.Total_Apheresis_Machine_ACF = data_loaded['Total_Apheresis_Machine_ACF']
            self.Substitution_Weight = data_loaded['Substitution_Weight']
            self.ACF_Bed_Capacity = data_loaded['ACF_Bed_Capacity']
            self.Initial_Platelet_Inventory = data_loaded['Initial_Platelet_Inventory']
            self.ForecastedAverageDemand = data_loaded['ForecastedAverageDemand']
            self.ForecastedStandardDeviationDemand = data_loaded['ForecastedStandardDeviationDemand']
            self.ForecastedAverageHospital_Bed_Capacity = data_loaded['ForecastedAverageHospital_Bed_Capacity']
            self.ForecastedSTDHospital_Bed_Capacity = data_loaded['ForecastedSTDHospital_Bed_Capacity']
            self.Rescue_Vehicle_Capacity = data_loaded['Rescue_Vehicle_Capacity']
            self.Distance_D_A = data_loaded['Distance_D_A']
            self.Distance_A_H = data_loaded['Distance_A_H']
            self.Distance_D_H = data_loaded['Distance_D_H']
            self.Distance_A_A = data_loaded['Distance_A_A']
            self.Distance_H_H = data_loaded['Distance_H_H']
            self.Casualty_Shortage_Cost = data_loaded['Casualty_Shortage_Cost']
            self.Number_Apheresis_Machine_Hospital = data_loaded['Number_Apheresis_Machine_Hospital']
            self.Number_Rescue_Vehicle_ACF = data_loaded['Number_Rescue_Vehicle_ACF']
            self.Number_Rescue_Vehicle_Hospital = data_loaded['Number_Rescue_Vehicle_Hospital']
            self.ForecastedAverageWhole_Blood_Donors = data_loaded['ForecastedAverageWhole_Blood_Donors']
            self.ForecastedSTDWhole_Blood_Donors = data_loaded['ForecastedSTDWhole_Blood_Donors']
            self.ForecastedAverageApheresis_Donors = data_loaded['ForecastedAverageApheresis_Donors']
            self.ForecastedSTDApheresis_Donors = data_loaded['ForecastedSTDApheresis_Donors']

        self.ComputeIndices()
        self.Print_Attributes()
        print(f"Data loaded from {filename}")
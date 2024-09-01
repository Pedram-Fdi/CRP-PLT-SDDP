import os
import pandas as pd

# This file integrates the results in "folder_path" which are obtained from running the code for different instances with different methods and finally saves the result in the same folder!

# Directory containing the Excel files
folder_path = r"C:\PhD\Thesis\Papers\2nd\Code\Results\Computational Results_Apheresis_40_[50,250]\Test"

# Output file
output_file = os.path.join(folder_path, "TotalData.xlsx")

# Columns for the summary DataFrame
columns = [
    "Instance", 
    "Model", 
    "Method", 
    "ScenarioGeneration", 
    "mipsetting",
    "SDDP LB", "SDDP Exp UB", "SDDP Safe UB", "SDDP Time",
    "Mean", "LB", "UB", "% On-Time Transfer", "% On-Time Surgery", "% Same BloodTypeInfusion"
]

# Initialize an empty DataFrame for the summary
summary_df = pd.DataFrame(columns=columns)

# Iterate through all Excel files in the folder
for file_name in os.listdir(folder_path):
    if file_name.endswith(".xlsx") and file_name != "TotalData.xlsx":
        file_path = os.path.join(folder_path, file_name)
        
        try:
            # Read the Generic Information sheet
            generic_info_df = pd.read_excel(file_path, sheet_name="Generic Information")
            print(f"Processing file: {file_name}")
            print("Generic Information DataFrame:\n", generic_info_df)
            
            if generic_info_df.shape[0] < 1:
                print(f"Warning: Generic Information sheet in {file_name} does not have enough rows.")
                continue

            instance = generic_info_df.at[0, 'Instance']
            model = generic_info_df.at[0, 'Model']
            method = generic_info_df.at[0, 'Method']
            scenario_generation = generic_info_df.at[0, 'ScenarioGeneration']
            mipsetting = generic_info_df.at[0, 'mipsetting']
                
            # Read the InSample sheet
            insample_df = pd.read_excel(file_path, sheet_name="InSample")
            print("InSample DataFrame:\n", insample_df)
            
            sddp_lb = insample_df.at[0, 'SDDP LB']
            sddp_exp_ub = insample_df.at[0, 'SDDP Exp UB']
            sddp_safe_ub = insample_df.at[0, 'SDDP Safe UB']
            sddp_time_backward = insample_df.at[0, 'SDDP Time Backward']
            sddp_time_forward_no_test = insample_df.at[0, 'SDDP Time Forward No Test']
            sddp_total_time = sddp_time_backward + sddp_time_forward_no_test
            
            # Read the OutOfSample sheet
            outofsample_df = pd.read_excel(file_path, sheet_name="OutOfSample")
            print("OutOfSample DataFrame:\n", outofsample_df)
            

            mean = outofsample_df.at[0, 'Mean']
            lb = outofsample_df.at[0, 'LB']
            ub = outofsample_df.at[0, 'UB']
            on_time_transfer = outofsample_df.at[0, '% On-Time Transfer']
            on_time_surgery = outofsample_df.at[0, '% On-Time Surgery']
            same_bloodtype_infusion = outofsample_df.at[0, '% Same BloodTypeInfusion']
            
            # Create a dictionary for the current instance's data
            instance_data = {
                "Instance": instance,
                "Model": model,
                "Method": method,
                "ScenarioGeneration": scenario_generation,
                "mipsetting": mipsetting,
                "SDDP LB": sddp_lb,
                "SDDP Exp UB": sddp_exp_ub,
                "SDDP Safe UB": sddp_safe_ub,
                "SDDP Time": sddp_total_time,
                "Mean": mean,
                "LB": lb,
                "UB": ub,
                "% On-Time Transfer": on_time_transfer,
                "% On-Time Surgery": on_time_surgery,
                "% Same BloodTypeInfusion": same_bloodtype_infusion
            }
            
            # Append the data to the summary DataFrame
            summary_df = pd.concat([summary_df, pd.DataFrame([instance_data])], ignore_index=True)
        except Exception as e:
            print(f"Error processing file {file_name}: {e}")

# Write the summary DataFrame to an Excel file
summary_df.to_excel(output_file, index=False)

print("Summary file created successfully.")

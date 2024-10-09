import os
import re
import matplotlib.pyplot as plt

# Function to parse data from file with a maximum iteration limit
def parse_data(file_content, max_iterations=None):
    iterations = []
    lower_bounds = []
    upper_bounds = []
    gaps = []
    gaps_iterations = []
    durations = []
    
    # Read the file line by line
    for line in file_content.splitlines():
        if line.startswith("Iteration"):
            parts = line.split(',')
            if len(parts) >= 4:  # Ensure there are enough parts to parse
                iteration = int(parts[0].split(':')[1].strip())
                
                # If max_iterations is defined, skip data beyond that iteration
                if max_iterations and iteration > max_iterations:
                    continue

                duration = int(parts[1].split(':')[1].strip())
                lb = float(parts[2].split(':')[1].strip())
                ub_part = parts[3].strip()
                ub_number = ub_part.split(':')[1].strip(')')
                ub = float(ub_number)
                gap = 100 * float(parts[4].split(':')[1].strip())

                iterations.append(iteration)
                durations.append(duration)
                lower_bounds.append(lb)
                upper_bounds.append(ub)

                if gap >= 0:  # Only consider non-negative gaps
                    gaps.append(gap)
                    gaps_iterations.append(iteration)
    return iterations, lower_bounds, upper_bounds, gaps, gaps_iterations, durations

# Function to automatically generate dataset names from file names
def get_dataset_name(filename):
    # Define the list of possible labels
    possible_labels = ["JustStrongCut", "JustLBF", "JustWarmUp", "JustMultiCut", 
                       "NoEnhancements", "NoStrongCut", "NoLBF", "NoWarmUp", 
                       "NoMultiCut", "AllEnhancements"]
    
    # Search for any label from the possible_labels in the filename
    for label in possible_labels:
        if label in filename:
            return label
    return filename  # If no match is found, return the whole filename (fallback)

# Function to plot and save lower bounds
def plot_data(iterations, lower_bounds, labels, colors, markers, marker_interval=20, save_dir="", filename=""):
    plt.figure(figsize=(12, 6))
    for i, data in enumerate(zip(iterations, lower_bounds)):
        if data[0] and data[1]:
            plt.plot(data[0], data[1], linestyle='-', color=colors[i], linewidth=1)
            plt.plot(data[0][::marker_interval], data[1][::marker_interval], linestyle='None', marker=markers[i], color=colors[i])
            plt.plot([], [], linestyle='None', marker=markers[i], color=colors[i], label=labels[i])  # Invisible plot for legend
    plt.title('Comparison of Lower Bounds')
    plt.xlabel('Iteration')
    plt.ylabel('Lower Bound Value')
    plt.legend()
    plt.grid(True)
    
    # Save the plot with the desired filename format
    save_path = os.path.join(save_dir, f"LowerBounds_{filename}.png")
    plt.savefig(save_path)
    print(f"Lower Bounds plot saved as {save_path}")
    plt.show()

# Function to plot gaps
def plot_gaps(gaps_iterations, gaps, labels, colors, markers, marker_interval=20, save_dir="", filename=""):
    plt.figure(figsize=(12, 6))
    for i, gap_data in enumerate(gaps):
        if gap_data:
            sorted_gaps = sorted(gap_data, reverse=True)
            plt.plot(range(len(sorted_gaps)), sorted_gaps, linestyle='-', color=colors[i], linewidth=1)
            plt.plot(range(len(sorted_gaps))[::marker_interval], sorted_gaps[::marker_interval], linestyle='None', marker=markers[i], color=colors[i])
            plt.plot([], [], linestyle='None', marker=markers[i], color=colors[i], label=labels[i])  # Invisible plot for legend
    plt.title('Comparison of Gaps (Decreasing Order)')
    plt.xlabel('Sorted Index')
    plt.ylabel('Gap Value')
    plt.legend()
    plt.grid(True)

    # Save the plot with the desired filename format
    save_path = os.path.join(save_dir, f"Gaps_{filename}.png")
    plt.savefig(save_path)
    print(f"Gaps plot saved as {save_path}")
    plt.show()

# Function to plot and save durations
def plot_durations(iterations, durations, labels, colors, markers, marker_interval=20, save_dir="", filename=""):
    plt.figure(figsize=(12, 6))
    for i, data in enumerate(zip(iterations, durations)):
        if data[0] and data[1]:
            plt.plot(data[0], data[1], linestyle='-', color=colors[i], linewidth=1)
            plt.plot(data[0][::marker_interval], data[1][::marker_interval], linestyle='None', marker=markers[i], color=colors[i])
            plt.plot([], [], linestyle='None', marker=markers[i], color=colors[i], label=labels[i])  # Invisible plot for legend
    plt.title('Solution Time per Iteration')
    plt.xlabel('Iteration')
    plt.ylabel('Duration')
    plt.legend()
    plt.grid(True)

    # Save the plot with the desired filename format
    save_path = os.path.join(save_dir, f"Durations_{filename}.png")
    plt.savefig(save_path)
    print(f"Durations plot saved as {save_path}")
    plt.show()

# Function to read files from the directory and extract data
def process_files(directory, filenames, max_iterations=None):
    datasets = {}
    for filename in filenames:
        filepath = os.path.join(directory, filename)
        # Debug: print the full file path being checked
        print(f"Looking for file: {filepath}")
        try:
            with open(filepath, 'r') as file:
                file_content = file.read()
                iterations, lower_bounds, upper_bounds, gaps, gaps_iterations, durations = parse_data(file_content, max_iterations)
                
                # Automatically generate the dataset name
                dataset_name = get_dataset_name(filename)
                
                # Store parsed data into the datasets dictionary
                datasets[dataset_name] = {
                    'iterations': iterations,
                    'lower_bounds': lower_bounds,
                    'upper_bounds': upper_bounds,
                    'gaps': gaps,
                    'gaps_iterations': gaps_iterations,
                    'durations': durations
                }
                
                print(f"Processed {filename} and stored data as {dataset_name}")
        except FileNotFoundError:
            print(f"File {filename} not found in directory {directory}")
    
    return datasets

# Main function to execute the code
def main():
    # Example directory and filenames (update these based on your input)
    directory = r'C:\PhD\Thesis\Papers\2nd\Code\Results\Results\Beluga'
    filenames = [
        "SDDPtrace_2_15_5_5_3_4_1_CRP_Multi_Stage_SDDP_RQMC_all10_42_False_1_AllEnhancements_JustYFix___Halton_100_KMeansPP_10.txt",
        "SDDPtrace_2_15_5_5_3_4_1_CRP_Multi_Stage_SDDP_RQMC_all10_42_False_1_NoStrongCut_JustYFix___Halton_100_KMeansPP_10.txt"
    ]
    
    # Set a maximum iteration limit (None means no limit)
    max_iterations = 200  # Adjust this to your desired max iteration
    
    # Process the files and extract data
    datasets = process_files(directory, filenames, max_iterations=max_iterations)
    
    # Extract iterations, lower bounds, gaps, and durations for plotting
    iterations = [datasets[name]['iterations'] for name in datasets]
    lower_bounds = [datasets[name]['lower_bounds'] for name in datasets]
    gaps = [datasets[name]['gaps'] for name in datasets]
    gaps_iterations = [datasets[name]['gaps_iterations'] for name in datasets]
    durations = [datasets[name]['durations'] for name in datasets]
    
    # Define labels, colors, and markers for the plot
    labels = list(datasets.keys())  # Automatically use dataset names as labels
    colors = ['blue', 'green', 'orange', 'purple', 'grey']
    markers = ['o', 'v', '^', '<', '>']
    
    # Define filename for saving
    save_filename = filenames[0].split('_JustYFix')[0]

    # Plot and save the lower bounds comparison
    plot_data(iterations, lower_bounds, labels, colors, markers, save_dir=directory, filename=save_filename)
    
    # Plot and save the gaps comparison
    plot_gaps(gaps_iterations, gaps, labels, colors, markers, save_dir=directory, filename=save_filename)
    
    # Plot and save the durations comparison
    plot_durations(iterations, durations, labels, colors, markers, save_dir=directory, filename=save_filename)

if __name__ == "__main__":
    main()

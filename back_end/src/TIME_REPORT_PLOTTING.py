import sys
import pandas as pd
import matplotlib.pyplot as plt

def main():
    print("CL: Start with time plotting.")
    time_report = sys.argv[1]

    # Get time input values from textfile
    time_input = pd.read_csv(time_report, sep= '\t')
    
    # Plot bar graph
    plt.figure(figsize=(8,4))
    plt.bar(time_input["Sample name"], time_input["Total time (s)"])
    # Plot threshold line at 30 seconds
    plt.axhline(y=100, color="red", linestyle="--", linewidth=2, label="Threshold")

    # Display preferences 
    plt.xlabel("Sample name")
    plt.ylabel("Execution time (s)")
    plt.title("Pipeline execution time for each sample")
    plt.legend()
    plt.tight_layout()
    
    plt.savefig("./Output/INT26_TIME_REPORT_GRAPH.png", dpi=300)
    #plt.show()

    print("CL: Done with time plotting.")

if __name__ == "__main__" : main()
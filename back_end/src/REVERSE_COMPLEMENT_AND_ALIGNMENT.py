import sys
import time
from datetime import datetime
from Bio import SeqIO
#from Bio.Align.Applications import ClustalOmegaCommandline
import subprocess
import glob

def main():
    """
        Takes 2 arguments with names of input files.
        argv[1] = Forward primer's sequence reading file name
        argv[2] = Reverse primer's sequence reading file name
        Get the reverse complements of the reverse primer seqeucing and save as fasta file.
        Make alignment of forward primer sequence and reverse complement of reverse primer sequence 
        and save alignment.
    """
    print("CL: Reverse complement and alignment starting.")
    start_time = time.perf_counter()
    ############################ Arguments #####################################
    s_forward_primer_input_file = "./Input/" + sys.argv[1]
    s_reverse_primer_input_file = "./Input/" + sys.argv[2]
    #################### Establish how files will be named #####################
    i_name_start = s_forward_primer_input_file.find("_") + 1
    i_name_end = s_forward_primer_input_file.find("_", i_name_start)
    i_primer_end = s_reverse_primer_input_file.find("___", i_name_end)
    if ((i_name_start != -1) and (i_name_end != -1)):
        s_sample_name = s_forward_primer_input_file[i_name_start:i_name_end]
        s_reverse_primer_name = s_reverse_primer_input_file[i_name_end + 1: i_primer_end]
        s_reverse_complement_output_file = "./Output/Cleanup/INT26_" + s_sample_name + "_" + s_reverse_primer_name + "_RC.fas"
        s_alignment_output_file = "./Output/Cleanup/INT26_" + s_sample_name + "_ALIGNMENT.aln"
        s_performance_report = "./Output/Final/INT26_" + s_sample_name + "_PERFORMANCE_REPORT.txt"
    else: 
        sys.stderr.write("Error: Invalid starting file argument. Does not follow structure of INT26_{}_{}.seq\n")
        sys.exit()    
    ####################### Make reverse complement file #######################
    get_reverse_complement_fasta(s_reverse_primer_input_file, s_reverse_complement_output_file)
    print("CL: Reverse complement completed.")
    ####################### Make alignment using CrustalO ######################
    align_sequences(s_sample_name, s_forward_primer_input_file, s_reverse_complement_output_file, s_alignment_output_file)
    print("CL: Alignment completed.")
    ####################### Performance report #################################
    end_time = time.perf_counter()
    with open(s_performance_report, "w") as performance_output:
        performance_output.write("###################### Complete performance report "+ s_sample_name + " #####################\n")
        performance_output.write("--------------------- Reverse complement and alignment ---------------------\n")
        performance_output.write(f"Date and time of alignment algorithm end:\t{datetime.now():%Y-%m-%d %H:%M}\n")
        performance_output.write(f"Elapsed time for alignment algorithm: \t{end_time-start_time:.2f} seconds\n")
        performance_output.write("--------------------- Reverse complement and alignment ---------------------\n")
    performance_output.close()
    print("CL: Reverse complement and alignment ending.")

def get_reverse_complement_fasta(s_reverse_primer_input_file, s_reverse_complement_output_file):    
    """
        Take s_reverse_primer_input_file as reverse primer's sequence input file name.
        Takes output_file_name to be used when writing to output file.
    """
    with open(s_reverse_complement_output_file, "w") as output:
        for record in SeqIO.parse(s_reverse_primer_input_file, "fasta"):
            record.seq = record.seq.reverse_complement()
            record.id += "_RC"
            record.description += " reverse complement"

            SeqIO.write(record, output, "fasta")

def get_reverse_complement_fastq(s_reverse_primer_input_file, s_reverse_complement_output_file):    
    """
        Take s_reverse_primer_input_file as reverse primer's sequence input file name.
        Takes output_file_name to be used when writing to output file.
    """
    with open(s_reverse_complement_output_file, "w") as output:
        for record in SeqIO.parse(s_reverse_primer_input_file, "fastq"):
            record.seq = record.seq.reverse_complement()
            record.id += "_RC"
            record.description += " reverse complement"

            SeqIO.write(record, output, "fastq")


def align_sequences(s_sample_name, s_forward_primer_input_file, s_reverse_complement_output_file, s_alignment_output_file, s_combined_file):
    """
        Take forward primer sequence, reverse complement of reverse primer sequence and align using the ClustalW
        algorithm. The algorithm is then saved in the s_alignment_output_file.
    """
    input_files = [s_forward_primer_input_file, s_reverse_complement_output_file]  #glob.glob("../Input/*.seq")
    #combined_file = "./Output/Cleanup/INT26_" + s_sample_name + "_COMBINED.fas"
    with open(s_combined_file, "w") as combined:
        for infile in input_files:
            with open(infile) as f:
                combined.write(f.read().strip() + "\n")

    cmd = ["clustalo", "-i", s_combined_file, "-o", s_alignment_output_file, "--force", "--outfmt=fa"]

    try:
        subprocess.run(cmd, check = True) #capture_output = True, text = True)
        print(f"Aligned {infile} to {s_alignment_output_file}")
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error aligning {infile}: {e}\n")
        sys.exit()

if __name__ == "__main__" : main()
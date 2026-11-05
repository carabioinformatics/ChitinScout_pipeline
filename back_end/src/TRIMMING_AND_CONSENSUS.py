import sys
import time
from datetime import datetime
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from Bio import AlignIO
from Bio.Seq import Seq
import REVERSE_COMPLEMENT_AND_ALIGNMENT
from pipeline_status import report_step
import os
sample = os.environ.get("CURRENT_SAMPLE", "")

# Map used to reference when making the consensus sequence
IUPAC = {
    "A": "A", "C": "C", "G": "G", "T": "T",
    "R": "AG", "Y": "CT", "S": "CG", "W": "AT", "K": "GT", "M": "AC",
    "B": "CGT", "D": "AGT", "H": "ACT", "V": "ACG", "N": "ACGT",
}
BASE_SETS = {k: frozenset(v) for k, v in IUPAC.items()}
CODE_FOR_SET = {s: k for k, s in BASE_SETS.items()}
ANY = BASE_SETS["N"]

def main():
    """
        Take alignment file, make a consensus sequence, and trim all low quality regions.
    """
    print("log: Trimming and consensus starting.")
    start_time = time.perf_counter()
    ############################ Arguments #####################################
    s_forward_file = sys.argv[1]
    s_reverse_file = sys.argv[2]
    max_trimming = int(sys.argv[3])
    window_size = int(sys.argv[4])            #between 5 - 10: good for short reads, 10-20 smoother, more conservative
    quality_threshold = int(sys.argv[5])      #Could go up to 30 for stricter trimming; 20 standard
    cleanup_directory_extension = sys.argv[6]
    final_directory_extension = sys.argv[7]
    blast_directory_extension = sys.argv[8]

    #################### Establish how files will be named #####################
    i_name_start = s_forward_file.find("_") + 1
    i_name_end = s_forward_file.find("_", i_name_start)
    i_primer_end = s_reverse_file.find("___", i_name_end)
    if ((i_name_start != -1) and (i_name_end != -1)):
        s_sample_name = s_forward_file[i_name_start:i_name_end]
        s_forward_primer_name = s_forward_file[i_name_end + 1: i_primer_end]
        s_reverse_primer_name = s_reverse_file[i_name_end + 1: i_primer_end]
        s_forward_trim_output_fastq = cleanup_directory_extension + "/INT26_" + s_sample_name + "_" + s_forward_primer_name + "_TRIM.fastq"
        s_reverse_trim_output_fastq = cleanup_directory_extension + "/INT26_" + s_sample_name + "_" + s_reverse_primer_name + "_TRIM.fastq"
        s_forward_trim_output_fasta = cleanup_directory_extension + "/INT26_" + s_sample_name + "_" + s_forward_primer_name + "_TRIM.fas"
        s_reverse_trim_output_fasta = cleanup_directory_extension + "/INT26_" + s_sample_name + "_" + s_reverse_primer_name + "_TRIM.fas"
        s_combined_file = cleanup_directory_extension + "/INT26_" + s_sample_name + "_COMBINED.fas"
        s_reverse_complement_output_file_fasta = cleanup_directory_extension + "/INT26_" + s_sample_name + "_" + s_reverse_primer_name + "_RC.fas"
        s_reverse_complement_output_file_fastq = cleanup_directory_extension + "/INT26_" + s_sample_name + "_" + s_reverse_primer_name + "_RC.fastq"
        s_alignment_output_file = cleanup_directory_extension + "/INT26_" + s_sample_name + "_ALIGNMENT.aln"
        s_consensus_file = blast_directory_extension + "/INT26_" + s_sample_name + "_CONSENSUS.fas"
        s_performance_report = final_directory_extension + "/INT26_" + s_sample_name + "_PERFORMANCE_REPORT.txt"
    else: 
        sys.stderr.write("Error: Invalid starting file argument. Does not follow structure of INT26_{}_ALIGNMENT.aln")
        return 1
        #sys.exit()   
 
    ############################# Trimming #####################################
    report_step(sample, "trimming", "running")
    forward_record = SeqIO.read(s_forward_file, "abi")
    reverse_record = SeqIO.read(s_reverse_file, "abi")
    initial_forward_length = len(forward_record.seq)
    initial_reverse_length = len(reverse_record.seq)
    sliding_window_trim(s_forward_trim_output_fastq, s_forward_trim_output_fasta, forward_record, window_size, quality_threshold)
    sliding_window_trim(s_reverse_trim_output_fastq, s_reverse_trim_output_fasta, reverse_record, window_size, quality_threshold)
    trimmed_forward_record = SeqIO.read(s_forward_trim_output_fasta, "fasta")
    trimmed_forward_length = len(trimmed_forward_record)
    trimmed_reverse_record = SeqIO.read(s_reverse_trim_output_fasta, "fasta")
    trimmed_reverse_length = len(trimmed_reverse_record)
    report_step(sample, "trimming", "done")
    print("log: Trimming complete.")

    ################ Get reverse complement of reverse sequence ################
    REVERSE_COMPLEMENT_AND_ALIGNMENT.get_reverse_complement_fastq(s_reverse_trim_output_fastq, s_reverse_complement_output_file_fastq)
    REVERSE_COMPLEMENT_AND_ALIGNMENT.get_reverse_complement_fasta(s_reverse_trim_output_fasta, s_reverse_complement_output_file_fasta)
    fwd_fastq = SeqIO.read(s_forward_trim_output_fastq, "fastq")
    rc_fastq  = SeqIO.read(s_reverse_complement_output_file_fastq, "fastq")
    records_by_id = {fwd_fastq.id: fwd_fastq, rc_fastq.id: rc_fastq}    
    print("log: Reverse complement completed.")

    ####################### Make alignment using CrustalO ######################
    report_step(sample, "alignment", "running")
    REVERSE_COMPLEMENT_AND_ALIGNMENT.align_sequences(s_forward_trim_output_fasta, s_reverse_complement_output_file_fasta, s_alignment_output_file, s_combined_file)
    report_step(sample, "alignment", "done")
    print("log: Alignment completed.")

    ########################### Make consensus sequence ########################
    report_step(sample, "consensus", "running")
    alignment_record = AlignIO.read(s_alignment_output_file, "fasta")
    consensus_sequence = consensus(alignment_record, records_by_id, quality_threshold)
    consensus_record = SeqRecord(
        Seq(consensus_sequence), 
        id = s_sample_name,
        description = "consensus"
    )
    consensus_length = len(consensus_sequence)
    SeqIO.write(consensus_record, s_consensus_file, "fasta")
    report_step(sample, "consensus", "done")
    print("log: Consensus completed.")

    ####################### Performance report #################################
    end_time = time.perf_counter()
    with open(s_performance_report, "w") as performance_output:
        performance_output.write("###################### Complete performance report "+ s_sample_name + " #####################\n")
        performance_output.write("--------------------- Trimming, alignment and consensus ---------------------\n")
        performance_output.write(f"Date and time of processing end:\t{datetime.now():%Y-%m-%d %H:%M}\n")
        performance_output.write(f"Elapsed time for processing: \t{end_time-start_time:.2f} seconds\n")
        performance_output.write("Input file used for forward: " + s_forward_file + "\n")
        performance_output.write("Input file used for reverse: " + s_reverse_file + "\n")
        performance_output.write("Window size used for sliding window trim: " + str(window_size) +"\n")
        performance_output.write("Quality threshold used for trimming: "+ str(quality_threshold) + "\n")
        performance_output.write("Length of forward sequence before trim: " + str(initial_forward_length) + "\t After trim: " + str(trimmed_forward_length) + "\n")
        performance_output.write("Length of reverse sequence before trim: " + str(initial_reverse_length) + "\t After trim: " + str(trimmed_reverse_length) + "\n")
        performance_output.write(f"'%' Forward sequence remaining: {(trimmed_forward_length/initial_forward_length)*100:.2f}\n")
        performance_output.write(f"'%' Reverse sequence remaining: {(trimmed_reverse_length/initial_reverse_length)*100:.2f}\n")
        performance_output.write("Length of consensus sequence: " + str(consensus_length) + "\n")
        performance_output.write("--------------------- Trimming, alignment and consensus ---------------------\n")
    performance_output.close()
    print("log: Trimming and consensus ending.")
    if (((trimmed_forward_length/initial_forward_length)*100 > max_trimming) and ((trimmed_reverse_length/initial_reverse_length)*100 > max_trimming)):
        return 0
    else:
        return 2

def sliding_window_trim(s_output_fastq_file, s_output_fasta_file, cur_record, window_size, quality_threshold):
    """
        Takes a file and trims all low resolution reads.
        Takes regions of size window_size, get's the average quality score
        for that region, and if the region has a low quality score, then the first nucleotide
        of that region gets removed. This works for low quality reads at the start
        and end of Sanger sequencing. It then makes a trim of the sequence
        and the phred_quality file. This is so that indexing in the trimmed 
        sequence is still correct.
    """
    arr_qualities = cur_record.letter_annotations["phred_quality"]
    sequence = cur_record.seq

    # Find start location 
    i_start = 0
    for i in range(len(arr_qualities) - window_size + 1):
        window = arr_qualities[i: i + window_size]
        avg_quality = sum(window) / window_size
        if (avg_quality >= quality_threshold):
            i_start = i
            break

    # Find end location; going in reverse order
    i_end = 0
    for i in range(len(arr_qualities) - window_size, -1, -1):
        window = arr_qualities[i: i + window_size]
        avg_quality = sum(window) / window_size
        if (avg_quality >= quality_threshold):
            i_end = i + window_size
            break

    # Trim sequence + quality array
    trimmed_sequence = sequence[i_start:i_end]
    trimmed_arr_qualities = arr_qualities[i_start: i_end]

    # Make new SeqRecord and save to document
    trimmed_record = SeqRecord(
        trimmed_sequence, 
        id = cur_record.id,
        description = "trimmed"
    )
    trimmed_record.letter_annotations["phred_quality"] = trimmed_arr_qualities

    SeqIO.write(trimmed_record, s_output_fastq_file, "fastq")
    SeqIO.write(trimmed_record, s_output_fasta_file, "fasta")

def consensus(alignment, records_by_id, quality_threshold):
    """
        Makes consensus sequence between an alignment. If nucleotides don't agree, then takes the
        nucleotide with the best quality at that position. If not an A, C, T or G, but rather placeholder
        then uses above map to find a representing nucleotide that is inclusive of the read in sequence
        1 and 2. 
    """
    # Build the sequence 
    by_seq = {str(r.seq).upper(): r for r in records_by_id.values()}

    def find_source(rec):
        ungapped = str(rec.seq).replace("-", "").upper()
        src = records_by_id.get(rec.id)
        if src is not None and str(src.seq).upper() == ungapped:
            return src
        src = by_seq.get(ungapped)
        if src is None:
            raise ValueError(f"No FASTQ record matches alignment row {rec.id!r}")
        return src

    rows = [(str(rec.seq), find_source(rec).letter_annotations["phred_quality"])
            for rec in alignment]

    pointers = [0] * len(rows)
    out = []

    for col in range(alignment.get_alignment_length()):
        # Saves quality then base
        obs = []
        for r, (aligned, quals) in enumerate(rows):
            b = aligned[col]
            if b == "-":
                continue
            obs.append((quals[pointers[r]], b.upper()))
            pointers[r] += 1

        if not obs:
            continue

        if len({b for _, b in obs}) == 1:
            out.append(obs[0][1])
            continue

        # Find the nucleotide with the best quality first
        obs.sort(key=lambda x: x[0], reverse=True)
        if obs[0][0] < quality_threshold:
            out.append("N")
            continue

        current = BASE_SETS.get(obs[0][1], ANY)
        for q, b in obs[1:]:
            if q < quality_threshold:
                break
            narrowed = current & BASE_SETS.get(b, ANY)
            if narrowed:
                current = narrowed
        out.append(CODE_FOR_SET[current])

    return "".join(out)

if __name__ == "__main__" : sys.exit(main())
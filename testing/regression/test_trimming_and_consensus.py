import pytest
import back_end.src.TRIMMING_AND_CONSENSUS as TRIMMING
import back_end.src.REVERSE_COMPLEMENT_AND_ALIGNMENT as REVERSE_COMPLEMENT_AND_ALIGNMENT
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from Bio import AlignIO
from Bio.Seq import Seq

MIN_REMAINING_FRACTION = 0.5

def read_single_record(path, fmt):
    """
        Read the first record of the file in the specified format.
    """
    records = list(SeqIO.parse(path, fmt))
    assert len(records) <= 1, f"{path} contains more than one record"
    return records[0] if records else None

def generate_trimmed_files(s_trim_output_fastq, s_trim_output_fasta, record):
    """
        Make trimmed fasta and fastq files using standard parameters.
    """
    TRIMMING.sliding_window_trim(str(s_trim_output_fastq), str(s_trim_output_fasta), record, 10, 20)
    # Confirm that output files were created
    for path in (s_trim_output_fasta, s_trim_output_fastq):
        assert path.exists(), f"Trimming did not create {path.name}"

def read_alignment(s_alignment_file):
    """
        Read an aligned FASTA file and return a list of (header, sequence) tuples.
    """
    records = []
    header, seq = None, []
    with open(s_alignment_file) as file:
        for line in file:
            line = line.strip()    
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    records.append((header, "".join(seq)))
                header, seq = line[1:], []
            else:
                seq.append(line)
    if header is not None:
        records.append((header, "".join(seq)))
    return records

def count_mismatches(s_alignment_file):
    """
        Compare the two consensus sequences column by column. Return a dictionary with:
        mismatches: when both have bases but differ,
        gaps: when one sequence has a gap
        matches: when both are identical
        aligned length: total alignment columns
    """
    records = read_alignment(s_alignment_file)
    assert len(records) == 2, f"Expected 2 sequences but found {len(records)}."

    seq1, seq2 = records[0][1].upper(), records[0][1].upper()
    assert len(seq1) == len(seq2), "Aligned sequences must be the same length."

    mismatches = gaps = matches = 0
    for a, b in zip(seq1, seq2):
        if a == "-" and b == "-":
            continue
        elif a == "-" or b == "-":
            gaps += 1
        elif a == b:
            matches += 1
        else: 
            mismatches += 1

    return {
        "mismatches": mismatches,
        "gaps": gaps,
        "matches": matches,
        "aligned_length": len(seq1)
    }

@pytest.mark.regression
def test_faulty_file_trimming(resource_dir, output_dir):
    """"
        This test confirms that the sliding window trimming picks up when one
        of the files have inadequate quality and length to continue with further processing.
        In this example, the forward file has very scattered reads and the reverse is completely normal.
        Test pair used for this test: 1.
    """
    input_forward_file = resource_dir / "faulty/test_1_ITS1___1.fastq"
    input_reverse_file = resource_dir / "faulty/test_1_ITS4___1.fastq"

    s_forward_trim_output_fasta = output_dir / "test_1_ITS1_TRIM.fas"
    s_forward_trim_output_fastq = output_dir / "test_1_ITS1_TRIM.fastq"
    s_reverse_trim_output_fasta = output_dir / "test_1_ITS4_TRIM.fas"
    s_reverse_trim_output_fastq = output_dir / "test_1_ITS4_TRIM.fastq"

    forward_record = SeqIO.read(input_forward_file, "fastq")
    reverse_record = SeqIO.read(input_reverse_file, "fastq")
    initial_forward_length = len(forward_record.seq)
    initial_reverse_length = len(reverse_record.seq)

    generate_trimmed_files(s_forward_trim_output_fastq, s_forward_trim_output_fasta, forward_record)
    generate_trimmed_files(s_reverse_trim_output_fastq, s_reverse_trim_output_fasta, reverse_record)
    
    trimmed_forward_record = read_single_record(s_forward_trim_output_fasta, "fasta")
    trimmed_reverse_record = read_single_record(s_reverse_trim_output_fasta, "fasta")
    trimmed_forward_length = len(trimmed_forward_record) if trimmed_forward_record else 0
    trimmed_reverse_length = len(trimmed_reverse_record) if trimmed_reverse_record else 0

    forward_fraction = trimmed_forward_length/initial_forward_length
    reverse_fraction = trimmed_reverse_length/initial_reverse_length

    print(f"Faulty file trimming: Original forward length: {initial_forward_length}, Trimmed forward length: {trimmed_forward_length}.")
    print(f"Faulty file trimming: Original reverse length: {initial_reverse_length}, Trimmed reverse length: {trimmed_reverse_length}.")

    # Confirm that too little of forward remained to continue
    assert forward_fraction < MIN_REMAINING_FRACTION, (
        f"Forward read kept {forward_fraction:.0%} of its length "
        f"({trimmed_forward_length}/{initial_forward_length}); expected under "
        f"{MIN_REMAINING_FRACTION:.0%}"
    )
    # Confirm that reverse had adequate remaining bases
    assert reverse_fraction > MIN_REMAINING_FRACTION, (
        f"Reverse read kept only {reverse_fraction:.0%} of its length "
        f"({trimmed_reverse_length}/{initial_reverse_length}); expected over "
        f"{MIN_REMAINING_FRACTION:.0%}"
    )
    
@pytest.mark.regression
def test_manual_vs_pipeline_trimming(resource_dir, output_dir):
    """
        This test compares how much the pipeline trimmed compared to a manual trimming that happened completely independently.
        The input files are trimmed and then the length is compared to the lenght of the manually trimmed input file. The pipeline
        trimming length needs to be within a range of 10% difference of the manual length to pass.
        Test pair used for this test: 2
    """
    input_forward_file = resource_dir / "valid/test_2_ITS1___1.fastq"
    input_reverse_file = resource_dir / "valid/test_2_ITS4___1.fastq"
    input_manual_trim_forward_file = resource_dir / "valid/test_2_ITS1___1_MTRIM.fasta"
    input_manual_trim_reverse_file = resource_dir / "valid/test_2_ITS4___1_MTRIM.fasta"

    s_forward_trim_output_fasta = output_dir / "test_2_ITS1_TRIM.fas"
    s_forward_trim_output_fastq = output_dir / "test_2_ITS1_TRIM.fastq"
    s_reverse_trim_output_fasta = output_dir / "test_2_ITS4_TRIM.fas"
    s_reverse_trim_output_fastq = output_dir / "test_2_ITS4_TRIM.fastq"

    forward_record = SeqIO.read(input_forward_file, "fastq")
    reverse_record = SeqIO.read(input_reverse_file, "fastq")

    generate_trimmed_files(s_forward_trim_output_fastq, s_forward_trim_output_fasta, forward_record)
    generate_trimmed_files(s_reverse_trim_output_fastq, s_reverse_trim_output_fasta, reverse_record)

    trimmed_forward_record = read_single_record(s_forward_trim_output_fasta, "fasta")
    trimmed_reverse_record = read_single_record(s_reverse_trim_output_fasta, "fasta")
    manual_trimmed_forward_record = read_single_record(input_manual_trim_forward_file, "fasta")
    manual_trimmed_reverse_record = read_single_record(input_manual_trim_reverse_file, "fasta")
    trimmed_forward_length = len(trimmed_forward_record) if trimmed_forward_record else 0
    trimmed_reverse_length = len(trimmed_reverse_record) if trimmed_reverse_record else 0
    manual_trimmed_forward_length = len(manual_trimmed_forward_record) if manual_trimmed_forward_record else 0
    manual_trimmed_reverse_length = len(manual_trimmed_reverse_record) if manual_trimmed_reverse_record else 0

    forward_fraction = 0.1 * manual_trimmed_forward_length
    reverse_fraction = 0.1 * manual_trimmed_reverse_length

    print(f"Trimming comparison: Trimmed forward length using pipeline: {trimmed_forward_length}, Trimmed forward length from manual: {manual_trimmed_forward_length}")
    print(f"Trimming comparison: Trimmed reverse length using pipeline: {trimmed_reverse_length}, Trimmed reverse length from manual: {manual_trimmed_reverse_length}")
    print(f"Trimming comparison: Allowed forward length range {manual_trimmed_forward_length - forward_fraction} - {manual_trimmed_forward_length + forward_fraction}")
    print(f"Trimming comparison: Allowed reverse length range {manual_trimmed_reverse_length - reverse_fraction} - {manual_trimmed_reverse_length + reverse_fraction}")

    # Confirm that forward trimming is within range
    assert (trimmed_forward_length > (manual_trimmed_forward_length - forward_fraction)) and (trimmed_forward_length < (manual_trimmed_forward_length + forward_fraction)), (
        f"Manual trimming produced a forward sequence of length: {manual_trimmed_forward_length} and "
        f"the pipeline trimming produced a forward sequence of length: {trimmed_forward_length}. It was expected "
        f"that the pipeline's length should be within a range of 10% above or below the length of the manual sequence length. "
        f"This test failed because the pipeline trimming length was not within this range."
    )

    # Confirm that reverse trimming is within range
    assert (trimmed_reverse_length > (manual_trimmed_reverse_length - reverse_fraction)) and (trimmed_reverse_length < (manual_trimmed_reverse_length + reverse_fraction)), (
        f"Manual trimming produced a reverse sequence of length: {manual_trimmed_reverse_length} and "
        f"the pipeline trimming produced a reverse sequence of length: {trimmed_reverse_length}. It was expected "
        f"that the pipeline's length should be within a range of 10% above or below the length of the manual sequence length. "
        f"This test failed because the pipeline trimming length was not within this range."
    )

@pytest.mark.regression
def test_manual_vs_pipeline_consensus(resource_dir, output_dir):
    # Get input files
    manual_consensus_file = resource_dir / "valid/test_2_CONSENSUS.fas"

    # File naming
    s_forward_trim_output_fasta = output_dir / "test_2_ITS1_TRIM.fas"
    s_forward_trim_output_fastq = output_dir / "test_2_ITS1_TRIM.fastq"
    s_reverse_trim_output_fasta = output_dir / "test_2_ITS4_TRIM.fas"
    s_reverse_trim_output_fastq = output_dir / "test_2_ITS4_TRIM.fastq"
    s_combined_file = output_dir / "test_2_COMBINED.fas"
    s_reverse_complement_output_file_fasta = output_dir / "test_2_ITS4_RC.fas"
    s_reverse_complement_output_file_fastq = output_dir / "test_2_ITS4_RC.fastq"
    s_alignment_output_file = output_dir / "test_2_ALIGNMENT.aln"
    s_consensus_file = output_dir / "test_2_CONSENSUS.fas"
    s_comparison_combined_file = output_dir / "test_2_COMPARISON_COMBINED.fas"
    s_comparison_alignment_file = output_dir / "test_2_COMPARISON_ALIGNMENT.fas"

    # Get alignment and consensus to compare
    REVERSE_COMPLEMENT_AND_ALIGNMENT.get_reverse_complement_fastq(s_reverse_trim_output_fastq, s_reverse_complement_output_file_fastq)
    REVERSE_COMPLEMENT_AND_ALIGNMENT.get_reverse_complement_fasta(s_reverse_trim_output_fasta, s_reverse_complement_output_file_fasta)
    fwd_fastq = SeqIO.read(s_forward_trim_output_fastq, "fastq")
    rc_fastq  = SeqIO.read(s_reverse_complement_output_file_fastq, "fastq")
    records_by_id = {fwd_fastq.id: fwd_fastq, rc_fastq.id: rc_fastq}    
    
    REVERSE_COMPLEMENT_AND_ALIGNMENT.align_sequences(s_forward_trim_output_fasta, s_reverse_complement_output_file_fasta, s_alignment_output_file, s_combined_file)
    
    alignment_record = AlignIO.read(s_alignment_output_file, "fasta")
    consensus_sequence = TRIMMING.consensus(alignment_record, records_by_id, 20)
    consensus_record = SeqRecord(
        Seq(consensus_sequence), 
        id = "test_2",
        description = "consensus"
    )
    # consensus_length = len(consensus_sequence)
    SeqIO.write(consensus_record, s_consensus_file, "fasta")

    # Make an alignment between the 2 consensus and compare
    REVERSE_COMPLEMENT_AND_ALIGNMENT.align_sequences(manual_consensus_file, s_consensus_file, str(s_comparison_alignment_file), str(s_comparison_combined_file))
    comparison_result = count_mismatches(str(s_comparison_alignment_file))
    # compared_columns = comparison_result["matches"] + comparison_result["mismatches"]
    differences = comparison_result["mismatches"] + comparison_result["gaps"]
    fraction_mismatch = differences/comparison_result["aligned_length"]

    max_mismatch_fraction = 0.05

    print(f"Consensus comparison: Amount of differences: {differences}")
    print(f"Consensus comparison: Fraction mismatch calculated: {fraction_mismatch}")
    print(f"Consensus comparison: Max fraction mismatch: {max_mismatch_fraction}")
    assert (fraction_mismatch <= max_mismatch_fraction),(
        f"A total number of {differences} mismatches was found between the manual generated consensus and the pipeline "
        f"generated consensus. A mismatch fraction maximum of {max_mismatch_fraction} is allowed. The actual mismatch fraction is calculated "
        f"by dividing the counted differences (mismatches and gaps) by the length of the aligned sequence. In this case, the counted differences"
        f"was more than the allowed mismatches. This could mean that the code to make the reverse complement, align and make the "
        f"the sequence showed unexpected behavior."
    )

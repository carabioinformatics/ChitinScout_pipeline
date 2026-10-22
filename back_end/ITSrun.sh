#!/bin/bash

echo "Start main run script"

# Get command line arguments
taxonomy_mode=$1
database_mode=$2

today_date=$(date +"%Y-%m-%d_%H:%M")
mkdir -p "./Output/$today_date"

# Set thresholds for search specificity, can be changed
window_size=${3:-5}
quality_threshold=${4:-20}
e_value_threshold=${5:-1e-15}
identity_threshold=${6:-90}
coverage_threshold=${7:-90}
time_limit=${8:-200}

pipeline_report="./Output/$today_date/INT26_PIPELINE_REPORT.txt"
echo -e "Pipeline started" > "$pipeline_report"
timing_report="./Output/$today_date/INT26_TIME_REPORT.txt"
timing_plot="./Output/$today_date/INT26_TIME_REPORT_GRAPH.png"
echo -e "Sample name\tCleanup time (s)\tBLAST time (s)\tTotal time (s)" > "$timing_report"

process_sample() {
    local forward=$1

    total_start_time=$(date +%s.%N)
    # Extract sample name
    sample_name=$(basename "$forward" | cut -d'_' -f2)

    # Find reverse filename
    reverse=$(find . -name "*_${sample_name}_ITS4___1.ab1")

    # Get consensus file name
    consensus_name=$"INT26_${sample_name}_CONSENSUS.fas"

    # Start printing
    echo "================================================="
    echo "Processing sample: $sample_name"
    echo "Forward input file: $forward"
    echo "Reverse input file: $reverse"

    # Check if reverse file exists
    if [[ -z "$reverse" ]]; then
        echo -e "--$sample_name terminated." >> "$pipeline_report"
        echo -e "Error: Reverse read file not found for $sample_name." >> "$pipeline_report"
        return
    fi

    # Make relevant directories
    mkdir -p ./Output/$today_date/$sample_name/BLAST
    mkdir -p ./Output/$today_date/$sample_name/Cleanup
    mkdir -p ./Output/$today_date/$sample_name/Final
    mkdir -p ./Output/$today_date/$sample_name/Comparison
    blast_attachment="./Output/$today_date/$sample_name/BLAST"
    cleanup_attachment="./Output/$today_date/$sample_name/Cleanup"
    final_attachment="./Output/$today_date/$sample_name/Final"
    comparison_attachment="./Output/$today_date/$sample_name/Comparison"
    
    echo -e "-$sample_name start" >> "$pipeline_report"
    
    # Run trimming script
    cleanup_start_time=$(date +%s.%N)
    timeout "$time_limit" python3 ./src/TRIMMING_AND_CONSENSUS.py "$forward" "$reverse" "$window_size" "$quality_threshold" "$cleanup_attachment" "$final_attachment" "$blast_attachment"
    trimming_return_code=$?
    cleanup_end_time=$(date +%s.%N)
    
    case $trimming_return_code in 
        0)
            # Successful trimming of sample
            echo -e "---$sample_name Trimming and consensus successful." >> "$pipeline_report"
            ;;
        1)
            # No input file found
            echo -e "---$sample_name terminated." >> "$pipeline_report"
            echo -e "-----Error: Invalid starting file argument." >> "$pipeline_report"
            return
            ;;
        2) 
            # Chosen error code for unsuccessful trimming
            echo -e "---$sample_name terminated." >> "$pipeline_report"
            echo -e "-----Error: Too large amount of original read was trimmed. Should manually check this sample." >> "$pipeline_report"
            return
            ;;
        124)
            # Timeout error code
            echo -e "---$sample_name terminated." >> "$pipeline_report"
            echo -e "-----Error: Trimming and consensus timed out after ${time_limit} seconds" >> "$pipeline_report"
            return
            ;;
        *)
            echo -e "---$sample_name terminated." >> "$pipeline_report"
            echo -e "-----Error: Unknown exit code for $sample_name" >> "$pipeline_report"
            return
            ;;
    esac
    
    # Run BLAST script
    BLAST_start_time=$(date +%s.%N)
    timeout "$time_limit" python3 ./src/BLAST_AND_TAXONOMY.py ./Output/$today_date/$sample_name/BLAST/$consensus_name "$sample_name" "$taxonomy_mode" "$database_mode" "$e_value_threshold" "$identity_threshold" "$coverage_threshold" "$final_attachment" "$blast_attachment" "$comparison_attachment"
    blast_return_code=$?
    BLAST_end_time=$(date +%s.%N)

    case $blast_return_code in
        0)
            # Successful BLAST search
            echo -e "---$sample_name BLAST successful." >> "$pipeline_report"
            ;;
        1)
            # Error code for incorrect input file
            echo -e "---$sample_name terminated." >> "$pipeline_report"
            echo -e "-----Error: Invalid starting file argument." >> "$pipeline_report"
            return
            ;;
        2)
            # Chosen error code for unsuccessful search
            echo -e "---$sample_name unsuccessful." >> "$pipeline_report"
            echo -e "-----Requires attention: No BLAST hits were found following required thresholds." >> "$pipeline_report"
            return
            ;;
        124)
            # Timeout error code
            echo -e "---$sample_name terminated." >> "$pipeline_report"
            echo -e "-----Error: BLAST timed out after ${time_limit} seconds" >> "$pipeline_report"
            return
            ;;
        *)
            echo -e "---$sample_name terminated." >> "$pipeline_report"
            echo -e "-----Error: Unknown exit code for $sample_name" >> "$pipeline_report"
            return
            ;;
    esac

    # Timing report printing
    cleanup_time=$(awk "BEGIN {print $cleanup_end_time - $cleanup_start_time}")
    BLAST_time=$(awk "BEGIN {print $BLAST_end_time - $BLAST_start_time}")
    total_end_time=$(date +%s.%N)
    total_time=$(awk "BEGIN {print $total_end_time - $total_start_time}")
    echo -e "$sample_name\t$cleanup_time\t$BLAST_time\t$total_time" >> "$timing_report"

    echo -e "-$sample_name end" >> "$pipeline_report"
    
    # Ending
    echo "$sample_name complete!"
    echo "================================================="
}
draw_progress() {
    local current=$1
    local total=$2

    local width=40

    local percent=$((100 * current / total))
    local filled=$((width * current / total))
    local empty=$((width - filled))

    printf "\r["

    printf "%0.s#" $(seq 1 $filled)
    printf "%0.s-" $(seq 1 $empty)

    printf "] %3d%% (%d/%d samples)\n" \
     "$percent" "$current" "$total"
}

# Find all the forward files
forward_files=()
if [[ -n "$SAMPLE_LIST_FILE" && -f "$SAMPLE_LIST_FILE" ]]; then
    while IFS= read -r wanted_sample || [[ -n "$wanted_sample" ]]; do
        [[ -z "$wanted_sample" ]] && continue
        for file in ./Input/*_"${wanted_sample}"_ITS1___1.ab1; do
            [[ -e "$file" ]] && forward_files+=("$file")
        done
    done < "$SAMPLE_LIST_FILE"
else
    for file in ./Input/*ITS1___1.ab1; do
        [[ -e "$file" ]] && forward_files+=("$file")
    done
fi

num_samples=${#forward_files[@]}
current_sample_number=0
echo "Samples to process: $num_samples"

# Go through the list of forward files and process each
for forward in "${forward_files[@]}"; 
do
    process_sample "$forward"
    current_sample_number=$((current_sample_number + 1))
    draw_progress "$current_sample_number" "$num_samples"
done

echo -e "Pipeline ended" >> "$pipeline_report"
echo "Pipeline finished"

python3 ./src/TIME_REPORT_PLOTTING.py "$timing_report" "$timing_plot"
plot_file=$(ls -t "./Output/$today_date"/*.png "./Output/$today_date"/*.jpg 2>/dev/null | head -n 1)
if [[ -n "$plot_file" ]]; then
    echo "PLOT_FILE: $plot_file"
fi
echo "================================================="
echo "End main run script"

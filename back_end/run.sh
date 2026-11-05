#!/bin/bash

# This run.sh file is used to start up the pipeline. The execution is then redirected to the next Bash
# script depending on the primer choice.
echo "Start by picking a primer"

# Error when no command line arguments are found.
if [[ $# -lt 1 ]]; then
    echo "Command line arguments required"
    echo "Usage: $0 <0|1> [taxonomy_mode] [database_mode] [trim_window_size] [quality_threshold] [e_value_threshold] [identity_threshold] [coverage_threshold] [ncbi_word_size] [time_limit]"
    echo "  0 = ITS pipeline"
    echo "  1 = TEF pipeline"
    echo "  2 = LSU pipeline"
    echo "  3 = B-Tub pipeline"
    exit 1
fi

# 0 - ITS, 1 - TEF, 2 - LSU, 3 - B-tub
primer_mode=$1 
shift

case $primer_mode in
    0)
        echo "Running ITS pipeline..."
        bash ./allprimersrun.sh ITS1___1.ab1 ITS4___1.ab1 "$@"
        ;;
    1)
        echo "Running TEF pipeline..."
        bash ./allprimersrun.sh TEF_forward___1.ab1 TEF_reverse___1.ab1 "$@"
        ;;
    2)
        echo "Running LSU pipeline..."
        bash ./allprimersrun.sh LSU_forward___1.ab1 LSU_reverse___1.ab1 "$@"
        ;;
    3)
        echo "Running B-Tub pipeline..."
        bash ./allprimersrun.sh B_Tub_forward_Primer__1.ab1 B_Tub_reverse_primer__1.ab1 "$@"
        ;;
    *)
        echo "Error: invalid region '$primer_mode'. Use 0 - 3 for different modes."
        exit 1
        ;;
esac
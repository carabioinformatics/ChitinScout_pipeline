#!/bin/bash

# This run.sh file is used to start up the pipeline. The execution is then redirected to the next Bash
# script depending on the primer choice.
echo "Start by picking a primer"

# Error when no command line arguments are found.
if [[ $# -lt 1 ]]; then
    echo "Command line arguments required"
    echo "Usage: $0 <forward_suffix> <reverse_suffix> [taxonomy_mode] [database_mode] [trim_window_size] [quality_threshold] [e_value_threshold] [identity_threshold] [coverage_threshold] [ncbi_word_size] [time_limit]"
    echo "  0 = ITS pipeline"
    echo "  1 = TEF pipeline"
    echo "  2 = LSU pipeline"
    echo "  3 = B-Tub pipeline"
    exit 1
fi

# 0 - ITS, 1 - TEF, 2 - LSU, 3 - B-tub, or other
forward_suffix=$1
reverse_suffix=$2 
shift 2

echo "Running pipeline with forward suffix '$forward_suffix' and reverse suffix '$reverse_suffix'..."
bash ./allprimersrun.sh "$forward_suffix" "$reverse_suffix" "$@"
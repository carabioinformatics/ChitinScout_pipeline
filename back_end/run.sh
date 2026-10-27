#!/bin/bash

echo "Start by picking a primer"

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
        bash ./ITSrun.sh "$@"
        ;;
    1)
        echo "Running TEF pipeline..."
        bash ./TEFrun.sh "$@"
        ;;
    2)
        echo "Running LSU pipeline..."
        bash ./generalrun.sh LSU_forward___1.ab1 LSU_reverse___1.ab1 "$@"
        ;;
    3)
        echo "Running B-Tub pipeline..."
        bash ./generalrun.sh B-Tub_forward___1.ab1 B-Tub_forward___1.ab1 "$@"
        ;;
    *)
        echo "Error: invalid region '$primer_mode'. Use 0 - 3 for different modes."
        exit 1
        ;;
esac
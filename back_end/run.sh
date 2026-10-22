#!/bin/bash

echo "Start by picking a primer"

if [[ $# -lt 1 ]]; then
    echo "Command line arguments required"
    echo "Usage: $0 <0|1> [taxonomy_mode] [database_mode] [window_size] [quality_threshold] [e_value_threshold] [identity_threshold] [coverage_threshold] [time_limit]"
    echo "  0 = ITS pipeline"
    echo "  1 = TEF pipeline"
    exit 1
fi

primer_mode=$1 # 0 - ITS, 1 - TEF
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
    *)
        echo "Error: invalid region '$primer_mode'. Use 0 for ITS or 1 for TEF."
        exit 1
        ;;
esac
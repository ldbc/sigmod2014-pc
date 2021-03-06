#!/bin/bash

TOOLS=${1:-cpp/cmake-build-release/sigmod2014pc_cpp}

SIZES=${2:-1,10,100,1000}
SIZES="${SIZES//,/ }"

CSVS_BASE_FOLDER=${3:-csvs}

ITERATION_COUNT=${ITERATION_COUNT:-1}

SCRIPTS_FOLDER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# To limit the number of parameters, set the PARAMS_NUMBER environment variable

for ((CURRENT_ITERATION=1; CURRENT_ITERATION<=ITERATION_COUNT; CURRENT_ITERATION++))
do
  for SIZE in $SIZES
  do
    echo "======================================================================"
    echo "Iteration: $CURRENT_ITERATION/$ITERATION_COUNT"
    echo "Size: $SIZE of {$SIZES}"
    echo "======================================================================"
    echo

    for TOOL in $TOOLS
    do
      "$SCRIPTS_FOLDER"/run-tool.sh "$TOOL" p${SIZE}k "$CSVS_BASE_FOLDER"
    done
  done
done

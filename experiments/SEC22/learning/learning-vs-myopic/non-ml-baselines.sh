#!/bin/bash
NUM_TRIALS=4
EXPERIMENT_PATH=${PWD}
# arg1: migration cost
MIGRATION_COST=$1

if [[ -z $1 ]]
  then
    echo "ERROR: The migration cost must be specified as an argument!"
    exit 1
fi

EXPERIMENT_FILES_DIR='experiment_configs'
TIME_STAMP=$(date +%d.%m.%y_%H.%M.%S)

CONFIGS[1]='non-ml-greedy-migration-cost-0.json'
CONFIGS[2]='non-ml-displacing-migration-cost-0.json'
CONFIGS[3]='non-ml-optimal-migration-cost-0.json'
CONFIGS[4]='non-ml-neighborhood-optimal-migration-cost-0.json'

mkdir -p auto-generated
#sudo apt-install jq moreutils

for TASK in "${CONFIGS[@]}"
do
    TESTFILE=auto-generated/${TASK/cost-0.json/"cost-$MIGRATION_COST-learn.json"}
    TASK_NAME=${TASK/cost-0.json/"cost-$MIGRATION_COST"}
    echo $TESTFILE
    cp $EXPERIMENT_FILES_DIR/$TASK $TESTFILE
    jq ".cost_function.migration_cost=$MIGRATION_COST" $TESTFILE | sponge $TESTFILE

    for TRIAL in $(seq 1 $NUM_TRIALS)
    do
    	OUTPUT_DIR="$EXPERIMENT_PATH/output/non_ml/$TIME_STAMP/$TASK_NAME/$TRIAL"
    	(cd ../../../.. &&
    		mkdir -p $OUTPUT_DIR &&
    		python3 main.py --headless --configuration="$EXPERIMENT_PATH/$TESTFILE" --output="$OUTPUT_DIR" > "$OUTPUT_DIR/out.txt") &
    done
done

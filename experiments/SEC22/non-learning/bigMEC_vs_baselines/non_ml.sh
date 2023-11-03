#!/bin/bash
EXPERIMENT_PATH=${PWD}
NUM_TRIALS=4

EXPERIMENT_FILES_DIR='../experiment_configs'
TIME_STAMP=$(date +%d.%m.%y_%H.%M.%S)

CONFIGS[1]='greedy.json'
CONFIGS[2]='displacing.json'
CONFIGS[3]='optimal_baseline.json'
CONFIGS[4]='neighborhood-optimal_baseline.json'
CONFIGS[5]='no_migration_baseline.json'
CONFIGS[6]='greedy_uncongested.json'
CONFIGS[7]='displacing_uncongested.json'
CONFIGS[8]='optimal_baseline_uncongested.json'
CONFIGS[9]='neighborhood-optimal_baseline_uncongested.json'
CONFIGS[10]='no_migration_baseline_uncongested.json'

cd ../../../..
for TASK in "${CONFIGS[@]}"
do
    for TRIAL in $(seq 1 $NUM_TRIALS)
    do
        OUTPUT_DIR="$EXPERIMENT_PATH/output/$TIME_STAMP/${TASK%.*}/$TRIAL"
        mkdir -p $OUTPUT_DIR
        python3 main.py --headless --configuration="$EXPERIMENT_PATH/$EXPERIMENT_FILES_DIR/$TASK" --output="$OUTPUT_DIR" > "$OUTPUT_DIR/out.txt" &
    done
done


#echo python3 main.py --headless --configuration="experiments/communication_advantage/${CONFIGS[TASK_ID]}" --output="output/${CONFIGS[TASK_ID]}/$TRIAL_ID"

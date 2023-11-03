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

CONFIGS[1]='isa-nonrec-migration-cost-0.json'
CONFIGS[2]='isa-recursive-1-migration-cost-0.json'

mkdir -p auto-generated

#sudo apt-install jq moreutils

for TASK in "${CONFIGS[@]}"
do
    TESTFILE_LEARN=auto-generated/${TASK/cost-0.json/"cost-$MIGRATION_COST-learn.json"}
    TASK_LEARN=${TASK/cost-0.json/"cost-$MIGRATION_COST"}
    cp $EXPERIMENT_FILES_DIR/$TASK $TESTFILE_LEARN
    jq ".cost_function.migration_cost=$MIGRATION_COST |.migration_strategy.epsilon=0.05 | .num_simulation_steps = 21700" $TESTFILE_LEARN | sponge $TESTFILE_LEARN
    # I've removed the always-migration-trigger from here. if the results are bad, reinstate it.
    for TRIAL in $(seq 1 $NUM_TRIALS)
    do
        TESTFILE_TEST=auto-generated/${TASK/cost-0.json/"cost-$MIGRATION_COST-test-$TRIAL.json"}
        cp $TESTFILE_LEARN $TESTFILE_TEST
        OUTPUT_DIR_LEARN="$EXPERIMENT_PATH/output/ml/$TIME_STAMP/$TASK_LEARN/$TRIAL/learn"
        OUTPUT_DIR_TEST="$EXPERIMENT_PATH/output/ml/$TIME_STAMP/$TASK_LEARN/$TRIAL/test"
        jq ".migration_strategy.enable_learning=false | .migration_strategy.weights=\"$OUTPUT_DIR_LEARN/weights_at_step_21600.pickle\" | .migration_strategy.epsilon=0 | .migration_strategy.exp_boost=0 | .migration_strategy.migration_trigger=\"bs_changed\" | .num_simulation_steps = 86400" $TESTFILE_TEST | sponge $TESTFILE_TEST
    
        mkdir -p $OUTPUT_DIR_LEARN
        mkdir -p $OUTPUT_DIR_TEST
        (cd ../../../.. &&
            mkdir -p $OUTPUT_DIR_LEARN &&
            mkdir -p $OUTPUT_DIR_TEST &&
            python3 main.py --headless --configuration="$EXPERIMENT_PATH/$TESTFILE_LEARN" --output="$OUTPUT_DIR_LEARN" > "$OUTPUT_DIR_LEARN/out.txt" &&
            echo "Experiment $TIME_STAMP ($OUTPUT_DIR_LEARN) has transitioned from learning to testing." | mail -s '[BigMEC report] experiment learning->testing' brandherm@tk.tu-darmstadt.de &&
            python3 main.py --headless --configuration="$EXPERIMENT_PATH/$TESTFILE_TEST" --output="$OUTPUT_DIR_TEST" > "$OUTPUT_DIR_TEST/out.txt" &&
            echo "Experiment $TIME_STAMP ($OUTPUT_DIR_TEST) has finished." | mail -s '[BigMEC report] experiment has finished' brandherm@tk.tu-darmstadt.de ) &
    done
done

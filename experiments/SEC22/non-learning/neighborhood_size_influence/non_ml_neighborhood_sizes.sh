#!/bin/bash
EXPERIMENT_PATH=${PWD}
EXPERIMENT_FILES_DIR='../experiment_configs'

if [ $1 = "small" ]; then
  echo "using small n_sizes"
  N_SIZES[2]=2
  N_SIZES[4]=4
  N_SIZES[6]=6
  N_SIZES[8]=8
else
  echo "using large n_sizes"
  N_SIZES[1]=10
  N_SIZES[2]=20
  N_SIZES[3]=30
  N_SIZES[4]=40
  N_SIZES[5]=50
fi


TIME_STAMP=$(date +%d.%m.%y_%H.%M.%S)

CONFIGS[1]='greedy.json'
CONFIGS[2]='displacing.json'
CONFIGS[3]='neighborhood-optimal_baseline.json'
CONFIGS[4]='no_migration_baseline.json'
CONFIGS[5]='greedy_uncongested.json'
CONFIGS[6]='displacing_uncongested.json'
CONFIGS[7]='neighborhood-optimal_baseline_uncongested.json'
CONFIGS[8]='no_migration_baseline_uncongested.json'

mkdir -p auto-generated
#sudo apt-install jq moreutils


for N_SIZE in ${N_SIZES[@]}
do
    for TASK in "${CONFIGS[@]}"
    do
        MODTASK=auto-generated/${TASK/.json/"-N-$N_SIZE.json"}
        TASK_NAME=${TASK/.json/"-N-$N_SIZE.json"}
        echo $MODTASK
        cp "$EXPERIMENT_FILES_DIR/$TASK" $MODTASK
        jq ".migration_strategy.neighborhood_size=$N_SIZE" $MODTASK | sponge $MODTASK
        jq ".service_placement_strategy.neighborhood_size=$N_SIZE" $MODTASK | sponge $MODTASK

        OUTPUT_DIR="$EXPERIMENT_PATH/output/$TIME_STAMP/${TASK%.*}/n-${N_SIZE}"
        mkdir -p $OUTPUT_DIR
        (cd ../../../.. &&
            mkdir -p $OUTPUT_DIR &&
            python3 main.py --headless --configuration="$EXPERIMENT_PATH/$MODTASK" --output="$OUTPUT_DIR" > "$OUTPUT_DIR/out.txt") &
    done
done
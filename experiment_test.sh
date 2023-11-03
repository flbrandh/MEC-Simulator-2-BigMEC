#!/bin/bash

#SBATCH --mail-type=NONE
#SBATCH -a 1-4
#SBATCH -n 1
#SBATCH -c 4
#SBATCH -C avx
#SBATCH --mem-per-cpu=1600
#SBATCH -t 01:00:00
#SBATCH -J edgecomputingsimulation_1
#SBATCH -e /work/scratch/su78ypez/edgecomputingsimulation_1/err.%A_%a.txt
#SBATCH -o /work/scratch/su78ypez/edgecomputingsimulation_1/out.%A_%a.txt
#SBATCH -A project00979

module purge
module load gcc python/3.6.8
#srun echo "bla,... $SLURM_ARRAY_JOB_ID $SLURM_ARRAY_TASK_ID"
#srun echo "starting"
BASEDIR=$HOME/edge_computing/master
BASEOUTDIR=$HPC_SCRATCH/edgecomputingsimulation_1
#srun python -c "print('hello world')"
srun python $BASEDIR/main.py --headless --configuration="$BASEDIR/defaultExperimentConfigurations/isa-nonrecursive.json" --output="$BASEOUTDIR/output-$SLURM_ARRAY_JOB_ID-$SLURM_ARRAY_TASK_ID"


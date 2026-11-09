#!/bin/bash
#SBATCH --job-name=cs596-final-viz
#SBATCH --account=anakano_429
#SBATCH --partition=debug
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:20:00
#SBATCH --output=results/job-%j.log
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
module purge
module load gcc/13.3.0 openmpi/5.0.5
mkdir -p bin results/production results/baseline results/instrumented-check
date -Is
hostname
scontrol show job "$SLURM_JOB_ID" > "results/scheduler-${SLURM_JOB_ID}.txt"
mpicc -std=c99 -O3 -Wall -Wextra src/pmd.c -lm -o bin/pmd 2> results/build.log
cp original/pmd.c bin/reference.c
cp src/pmd.h bin/pmd.h
mpicc -std=c99 -O3 bin/reference.c -lm -o bin/pmd_reference
for sub in baseline instrumented-check; do cp inputs/check.in "results/$sub/pmd.in"; done
(cd results/baseline; mpirun --map-by slot --bind-to none -np 4 ../../bin/pmd_reference > pmd.out)
(cd results/instrumented-check; VIZ_ENABLE=0 mpirun --map-by slot --bind-to none -np 4 ../../bin/pmd > pmd.out)
cp inputs/production.in results/production/pmd.in
(cd results/production; mpirun --map-by slot --bind-to none -np 4 ../../bin/pmd > pmd.out)
sacct -j "$SLURM_JOB_ID" --format=JobID,JobName,State,ExitCode,AllocCPUS,Elapsed,NodeList -P > "results/accounting-${SLURM_JOB_ID}.txt"
sha256sum src/* inputs/* scripts/run.sl > results/run-inputs.sha256
date -Is

#!/bin/bash
#SBATCH -J smc-gboth-s2-withomni-ft
#SBATCH -p gpu-ms,gpu-troja
#SBATCH -N 1
#SBATCH --gpus=1
#SBATCH --constraint="gpuram48G|gpuram24G"
#SBATCH --mem=32G
#SBATCH -o logs/slurm-%x.%j.out
#SBATCH -e logs/slurm-%x.%j.err
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mayer@ufal.mff.cuni.cz
#SBATCH --time="14-0"

# make cuda available
module load cuda/11.8-cudnn8.6

time .venv-zeus/bin/zeus train \
    --experiment smc-gboth-s2-withomni-ft \
    --model-snapshot logs/smc-gboth-s2-withomni-261027_145838/snapshots/final.model \
    --train \
        datasets/omniomr/samples.train.pickle \
    --augment "h:8,rotate:1,v:4,de,en3:0.2,n:0.01,c:-1:1,b:-0.5:0.2" \
    --dev \
        datasets/omniomr/samples.validation.pickle \
        datasets/omniomr/samples_rendered.validation.pickle \
        datasets/dolores/samples.validation.pickle \
        datasets/dolores/samples_rendered.validation.pickle \
        datasets/olimpic-scanned/samples.validation.pickle \
        datasets/olimpic-synthetic/samples.validation.pickle \
    --test \
        datasets/omniomr/samples.test.pickle \
        datasets/omniomr/samples_rendered.test.pickle \
        datasets/dolores/samples.test.pickle \
        datasets/dolores/samples_rendered.test.pickle \
        datasets/olimpic-scanned/samples.test.pickle \
        datasets/olimpic-synthetic/samples.test.pickle \
    --early-stopping datasets/omniomr/samples.validation.pickle \
    --stopping-patience 10 \
    --evaluation-from 1 \
    --evaluation-each 1 \
    --metrics SER,SERpitchonly \
    --batch-size 32 \
    --learning-rate 1e-4 \
    --lr-decay none \
    --quiet-tf

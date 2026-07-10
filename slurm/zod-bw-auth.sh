#!/bin/bash
#SBATCH -J zod-bw-auth
#SBATCH -p gpu-ms,gpu-troja
#SBATCH -N 1
#SBATCH --gpus=1
#SBATCH --constraint="gpuram48G"
#SBATCH --mem=32G
#SBATCH -o logs/slurm-%x.%j.out
#SBATCH -e logs/slurm-%x.%j.err
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mayer@ufal.mff.cuni.cz
#SBATCH --time="14-0"

# make cuda available
module load cuda/11.8-cudnn8.6

time .venv-zeus/bin/zeus train \
    --experiment zod-bw-auth \
    --new_model solo26 \
    --train \
        datasets/dolores/samples_rendered.train.pickle \
        datasets/dolores/samples_rendered.test.pickle \
        datasets/dolores/samples.train.pickle \
        datasets/dolores/samples.test.pickle \
    --augment "h:8,rotate:1,v:4,de,en3:0.2,n:0.01,c:-1:1,b:-0.5:0.2" \
    --dev \
        datasets/dolores/samples_rendered.validation.pickle \
        datasets/dolores/samples.validation.pickle \
    --test \
        datasets/omniomr/samples_rendered.test.pickle \
        datasets/omniomr/samples.test.pickle \
    --epochs 430 \
    --evaluation_from 10 \
    --evaluation_each 10 \
    --batch_size 32 \
    --learning_rate 1e-3 \
    --lr_decay cos \
    --quiet_tf

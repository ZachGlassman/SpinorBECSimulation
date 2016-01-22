#!/bin/bash
#SLURM -p debug
#SLURM -n 1
#SLURM -t :60
#SLURM --mem 1000

.~/.profile
cd /lustre/zachg
module load python/3.2.3
python FockStateMinDep.py  -t .01 -dt 1e-6 -name testing -q -5 -n 4000

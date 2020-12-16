#!/bin/sh

ENRL=$1
PREF=$3
CONS=$2
SCHE=$4

python3 get_haverford_info.py $ENRL $PREF $CONS

python3 main_hc.py $PREF $CONS $SCHE

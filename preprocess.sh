#!/bin/bash

python create_flowline.py
DATANAME=kennicott_flowline.nc
PISM_DATANAME=pism_$DATANAME
python flowline.py -e -o $PISM_DATANAME $DATANAME

# config file
CDLCONFIG=psg_config.cdl
PCONFIG=psg_config.nc
ncgen -o $PCONFIG $CDLCONFIG

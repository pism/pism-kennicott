#!/usr/bin/env python
# Copyright (C) 2019-23 Andy Aschwanden

#  Perform "quasi steady-state" simulation for Kennicott Glacier

"""
Perform "quasi steady-state" simulation for Kennicott Glacier
"""

import inspect
import os
import shlex
import subprocess as sub
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from os.path import abspath, dirname, join, realpath
from typing import Any, Dict, List, Union

import pandas as pd
import xarray as xr

parser = ArgumentParser()
parser.description = "Generate UQ using Latin Hypercube or Sobol Sequences."
parser.add_argument(
    "-s",
    "--n_samples",
    dest="n_samples",
    type=int,
    help="""number of samples to draw. default=10.""",
    default=10,
)
parser.add_argument(
    "-e",
    "--ensemble_file",
    dest="ensemble_file",
    help="""Choose set.""",
    default="ensemble_kennicott_climate_flow_lhs_1000.csv",
)
options = parser.parse_args()
ensemble_file = options.ensemble_file

uq_df = pd.read_csv(ensemble_file)
uq_df.fillna(False, inplace=True)

scripts = []
runlength = 5000
odir = "2023_06_23_uq_climate_flow"

for d in [odir, f"{odir}/state",f"{odir}/spatial",f"{odir}/scalar", f"{odir}/run_scripts"]:
    if os.path.isdir(d) == False:
        os.mkdir(d)

    
z_max = 3500
z_min = 0

for n, row in enumerate(uq_df.iterrows()):
    combination = row[1]
    print(combination)

    m_id = int(combination["id"])

    b_low = combination["b_low"]
    b_high = combination["b_high"]
    ela = combination["ela"]
    temp_ela = combination["temp_ela"]
    lapse_rate = combination["lapse_rate"]
    temp_max = temp_ela - lapse_rate / 1e3 * (z_max - ela)
    temp_min = temp_ela - lapse_rate / 1e3 * (z_min - ela)
    phi = combination["phi"]
    q = combination["pseudo_plastic_q"]
    
    outfile = f"kennicott_id_{m_id}_0_{runlength}.nc"
    script = f"{odir}/run_scripts/kennicott_id_{m_id}_0_{runlength}.sh"
    cmd = f"pismr -bootstrap -config_override psg_config.nc -cfbc -sia_e 1.0 -skip -skip_max 5000 -i 2023_06_20_init/state/sia_2000a.nc -surface elevation -ice_surface_temp {temp_min},{temp_max},{z_min},{z_max} -climatic_mass_balance {b_low},{b_high},250,{ela},3250 -climatic_mass_balance_limits -10,0 -stress_balance ssa+sia -pseudo_plastic -pseudo_plastic_q {q} -pseudo_plastic_uthreshold 100.0 -yield_stress mohr_coulomb -plastic_phi {phi} -ssafd_ksp_type gmres -ssafd_ksp_norm_type unpreconditioned -ssafd_ksp_pc_side right -ssafd_pc_type asm -ssafd_sub_pc_type lu -periodicity y   -stress_balance.sia.bed_smoother.range 100 -grid.registration corner  -extra_times 100 -extra_file {odir}/spatial/spatial_{outfile} -extra_vars thk,topg,usurf,velbase_mag,velsurf_mag -ts_times yearly -ts_file {odir}/scalar/ts_{outfile} -y {runlength} -o {odir}/state/{outfile}"
    with open(script, "w", encoding="utf-8") as f:
        f.write(cmd)
        f.write("\n")
        for p_cmd in [f"ncatted -a id,global,a,c,{m_id}", f"ncatted -a b_low,global,a,c,{b_low}", f"ncatted -a b_high,global,a,c,{b_high}", f"ncatted -a ela,global,a,c,{ela}"]:
            cmd = f"{p_cmd} {odir}/state/{outfile}\n"
            f.write(cmd)



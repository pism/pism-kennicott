#!/bin/bash

odir=2023_06_20_init
mkdir -p $odir
mkdir -p $odir/state
mkdir -p $odir/spatial
mkdir -p $odir/scalar


mpirun -np 2 pismr -config_override psg_config.nc -cfbc -sia_e 1.0 -skip -skip_max 1000 -bootstrap -i pism_kennicott_flowline.nc -surface elevation -ice_surface_temp -2,-20,0,3500 -climatic_mass_balance -3,3,250,1000,3250 -climatic_mass_balance_limits -3,0 -stress_balance sia -periodicity y  -Mx 240 -My 3 -Mz 401 -Ly 0.1 -Lz 2000 -z_spacing equal -stress_balance.sia.bed_smoother.range 100 -grid.registration corner -ts_times yearly -ts_file $odir/scalar/scalar_sia_2000a.nc  -extra_file $odir/spatial/spatial_sia_2000a.nc -extra_times 100 -extra_vars topg,thk,usurf,velbase_mag,velsurf_mag,climatic_mass_balance -y 2000 -o $odir/state/sia_2000a.nc

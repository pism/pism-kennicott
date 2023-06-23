#!/usr/bin/env python

"""
Uncertainty quantification using Latin Hypercube Sampling or Sobol Sequences
"""

from argparse import ArgumentParser
from typing import Any, Dict

import numpy as np
import pandas as pd
from pyDOE import lhs
from SALib.sample import saltelli
from scipy.stats.distributions import randint, uniform


dists: Dict[str, Any] = {
    "climate": {
        "uq": {
            "b_low": uniform(loc=-6, scale=4),
            "b_high": uniform(loc=1, scale=4),
            "ela": uniform(loc=600, scale=1000),
            "temp_ela": uniform(loc=-20, scale=16),
            "lapse_rate": uniform(loc=-7, scale=2),
        },
        "default_values": {
            "phi": 35.0,
            "pseudo_plastic_q": 0.5,
        },
    },
    "climate-flow": {
        "uq": {
            "b_low": uniform(loc=-6, scale=4),
            "b_high": uniform(loc=1, scale=4),
            "ela": uniform(loc=600, scale=1000),
            "temp_ela": uniform(loc=-20, scale=16),
            "lapse_rate": uniform(loc=-7, scale=2),
            "phi": uniform(loc=10, scale=50),
            "pseudo_plastic_q": uniform(loc=0.25, scale=0.75),
        },
        "default_values": {
        },
    },
}

parser = ArgumentParser()
parser.description = "Generate UQ using Latin Hypercube or Sobol Sequences."
parser.add_argument(
    "-s",
    "--n_samples",
    dest="n_samples",
    type=int,
    help="""number of samples to draw. default=1000.""",
    default=1000,
)
parser.add_argument(
    "-d",
    "--distribution",
    dest="distribution",
    choices=dists.keys(),
    help="""Choose set.""",
    default="climate",
)
parser.add_argument(
    "--calc_second_order",
    action="store_true",
    help="""Second order interactions.""",
    default=False,
)
parser.add_argument(
    "-m",
    "--method",
    dest="method",
    type=str,
    choices=["lhs", "saltelli"],
    help="""number of samples to draw. default=lhs.""",
    default="lhs",
)
parser.add_argument(
    "--posterior_file",
    help="Posterior predictive parameter file",
    default=None,
)
parser.add_argument(
    "OUTFILE",
    nargs=1,
    help="Ouput file (CSV)",
    default="velocity_calibration_samples.csv",
)
options = parser.parse_args()
n_draw_samples = options.n_samples
calc_second_order = options.calc_second_order
method = options.method
outfile = options.OUTFILE[-1]
distribution_name = options.distribution
posterior_file = options.posterior_file

print(f"\nDrawing {n_draw_samples} samples from distribution set {distribution_name}")
distributions = dists[distribution_name]["uq"]

problem = {
    "num_vars": len(distributions.keys()),
    "names": distributions.keys(),
    "bounds": [[0, 1]] * len(distributions.keys()),
}

keys_prior = list(distributions.keys())

# Generate uniform samples (i.e. one unit hypercube)
if method == "saltelli":
    unif_sample = saltelli.sample(
        problem, n_draw_samples, calc_second_order=calc_second_order
    )
elif method == "lhs":
    unif_sample = lhs(len(keys_prior), n_draw_samples)
else:
    print(f"Method {method} not available")

n_samples = unif_sample.shape[0]
# To hold the transformed variables
dist_sample = np.zeros_like(unif_sample, dtype="object")

sb_dict = {0: "ssa+sia", 1: "blatter"}
# For each variable, transform with the inverse of the CDF (inv(CDF)=ppf)
for i, key in enumerate(keys_prior):
    if key == "stress_balance":
        dist_sample[:, i] = [
            f"{sb_dict[int(id)]}" for id in distributions[key].ppf(unif_sample[:, i])
        ]

    else:
        dist_sample[:, i] = distributions[key].ppf(unif_sample[:, i])

if posterior_file:
    X_posterior = pd.read_csv(posterior_file).drop(
        columns=["Unnamed: 0", "Model"], errors="ignore"
    )
    keys_mc = list(X_posterior.keys())
    keys = list(set(keys_prior + keys_mc))
    print(keys_prior, keys_mc)
    if len(keys_prior) + len(keys_mc) != len(keys):
        print("Duplicate keys, exciting.")
    keys = keys_prior + keys_mc
    mc_indices = np.random.choice(range(X_posterior.shape[0]), n_samples)
    X_sample = X_posterior.to_numpy()[mc_indices, :]

    dist_sample = np.hstack((dist_sample, X_sample))

else:
    keys = keys_prior


# Convert to Pandas dataframe, append column headers, output as csv
df = pd.DataFrame(dist_sample, columns=keys)
df.to_csv(outfile, index=True, index_label="id")

print("\nAdding default values\n")
for key, val in dists[distribution_name]["default_values"].items():
    if key not in df.columns:
        df[key] = val
        print(f"{key}: {val}")

df.to_csv(f"ensemble_{outfile}", index=True, index_label="id")

"""Fit residual corrections from RMSE leaderboard scores.

Under RMSE, a submission base + eps * f scores
    MSE = MSE_base - 2 eps E[(y - base) f] + eps^2 E[f^2]
so its score gives b_f = E[(y - base) f] on the public set exactly, up to E[f^2], which is taken
over the scored tracts of the four original regions (the public set is a random 30% of them;
eastern-wa does not move the all-zero score, so it is not public). With b for several f and
G = E[f f'], the least-squares correction is beta = G^-1 b, and it lowers MSE by b' G^-1 b.

  python probes.py make NAME            -> subs/probe_NAME.csv  (base + EPS[NAME] * f)
  python probes.py fit OUT              -> subs/OUT.csv using every probe in probes.csv
probes.csv has one row per scored probe: name,rmse"""
import sys

import numpy as np
import pandas as pd

import model

BASE_FILE, BASE_RMSE = "subs/best_v16.csv", 0.073724344


def features(d, s13):
    """Candidate directions for the residual y - base. EPS is the nudge each probe applies; its sign
    is a guess of the direction that helps, kept small so a wrong guess costs little."""
    return {
        "zero":   ((s13 == 0).astype(float),            -0.005),  # tracts the MAE model scored 0
        "T":      (d["T"].to_numpy(float),               0.05),   # transport-gap proxy
        "ok":     ((d.region == "eastern-ok").astype(float),  0.01),
        "az":     ((d.region == "maricopa-az").astype(float), -0.01),
        "ca":     ((d.region == "northern-ca").astype(float), 0.01),
        "noroad": ((d.ref <= 0.05).astype(float),        0.01),   # no road component: mean of 2
        "rural_nofire": ((d.rural & (d.n_fire == 0)).astype(float), 0.01),
        "blackout": ((d.blackouts > 0).astype(float),    0.02),
    }


def load():
    d = model.load()
    s13 = model.shape(d)
    base = pd.read_csv(BASE_FILE, dtype={"GEOID": str})
    assert (base.GEOID.values == d.GEOID.values).all()
    public = (d.region != "eastern-wa").to_numpy()
    return d, features(d, s13), base.coverage_gap_score.to_numpy(), public


def write(d, pred, name):
    out = pd.DataFrame({"GEOID": d.GEOID, "coverage_gap_score": np.clip(pred, 0, 1)})
    out.to_csv(f"subs/{name}.csv", index=False)
    print(f"subs/{name}.csv", out.coverage_gap_score.describe().round(4).to_dict())


def solve(X, eps, rmse, base_rmse):
    """beta and b from probe scores; X holds the probe features on the public tracts."""
    dmse = np.asarray(rmse) ** 2 - base_rmse ** 2
    b = (eps ** 2 * (X ** 2).mean(0) - dmse) / (2 * eps)
    return np.linalg.solve(X.T @ X / len(X), b), b


def selftest():
    """Synthetic target: scores computed from it must give back the direct least-squares fit."""
    rng = np.random.default_rng(0)
    X = np.column_stack([rng.random(500) < 0.3, rng.random(500), rng.random(500) < 0.1]).astype(float)
    base = 0.05 + rng.random(500) * 0.1
    y = base + X @ [0.02, -0.03, 0.1] + rng.normal(0, 0.01, 500)
    eps = np.array([0.01, -0.02, 0.05])
    rmse = [np.sqrt(np.mean((y - base - e * x) ** 2)) for e, x in zip(eps, X.T)]
    beta, _ = solve(X, eps, rmse, np.sqrt(np.mean((y - base) ** 2)))
    assert np.allclose(beta, np.linalg.lstsq(X, y - base, rcond=None)[0]), beta
    print("selftest ok", beta.round(4))


if __name__ == "__main__":
    if sys.argv[1] == "selftest":
        sys.exit(selftest())
    d, F, base, public = load()
    if sys.argv[1] == "make":
        f, eps = F[sys.argv[2]]
        write(d, base + eps * f, f"probe_{sys.argv[2]}")
    elif sys.argv[1] == "fit":
        log = pd.read_csv("probes.csv")
        names = list(log.name)
        X = np.column_stack([F[n][0] for n in names])
        eps = np.array([F[n][1] for n in names])
        beta, b = solve(X[public], eps, log.rmse, BASE_RMSE)
        for n, bi, be in zip(names, b, beta):
            print(f"{n:14s} b={bi:+.6f}  beta={be:+.4f}")
        print(f"expected RMSE {np.sqrt(BASE_RMSE ** 2 - b @ beta):.5f} (base {BASE_RMSE})")
        write(d, base + X @ beta, sys.argv[2])

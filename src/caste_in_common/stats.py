"""Weighted empirical distributions, with explicit ties and denominators."""

import numpy as np


def distribution(values, weights):
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if values.ndim != 1 or values.shape != weights.shape or not len(values):
        raise ValueError("Expected nonempty, equally sized vectors")
    if not np.isfinite(values).all() or not np.isfinite(weights).all():
        raise ValueError("Missing or nonfinite values must be handled explicitly")
    if (weights < 0).any() or weights.sum() <= 0:
        raise ValueError("Weights must be nonnegative with positive total")
    keep = weights > 0
    values, weights = values[keep], weights[keep]
    order = np.argsort(values, kind="stable")
    return values[order], weights[order] / weights.sum()


def cdf(values, weights, thresholds, *, inclusive=True):
    values, weights = distribution(values, weights)
    thresholds = np.asarray(thresholds, dtype=float)
    if np.isnan(thresholds).any():
        raise ValueError("Thresholds cannot be missing")
    indices = np.searchsorted(values, thresholds, side="right" if inclusive else "left")
    return np.r_[0.0, weights.cumsum()][indices].clip(0, 1)


def quantile(values, weights, probability):
    if not 0 <= probability <= 1:
        raise ValueError("Probability must lie in [0, 1]")
    values, weights = distribution(values, weights)
    i = np.searchsorted(weights.cumsum(), probability, side="left")
    return float(values[min(i, len(values) - 1)])


def pairwise(a, wa, b, wb):
    """Independent draws: P(A<B), P(A=B), P(A>B), and half-tie score."""
    a, wa = distribution(a, wa)
    b, wb = distribution(b, wb)
    below = cdf(b, wb, a, inclusive=False)
    at_or_below = cdf(b, wb, a)
    less = float(wa @ (1 - at_or_below))
    equal = float(wa @ (at_or_below - below))
    greater = float(wa @ below)
    return less, equal, greater, less + 0.5 * equal


def binned_overlap(a, wa, b, wb, edges):
    """Shared probability mass in fixed bins; depends on the chosen bins."""
    edges = np.asarray(edges, float)
    if (
        len(edges) < 2
        or edges[0] != -np.inf
        or edges[-1] != np.inf
        or not (np.diff(edges) > 0).all()
    ):
        raise ValueError("Bin edges must increase from -inf to +inf")
    a, wa = distribution(a, wa)
    b, wb = distribution(b, wb)
    return float(
        np.minimum(
            np.histogram(a, bins=edges, weights=wa)[0],
            np.histogram(b, bins=edges, weights=wb)[0],
        ).sum()
    )


def binned_superiority_bounds(mass_a, mass_b):
    """Sharp bounds on P(A>B), and tie-adjusted AUC, from ordered interval bins.

    Both distributions must use the same nonoverlapping ordered bins, each
    admitting at least two distinct values. Same-bin pairs are unresolved, not
    observed ties. Bounds for exact-value bins require their known ties instead.
    """
    a = np.asarray(mass_a, dtype=float)
    b = np.asarray(mass_b, dtype=float)
    if a.ndim != 1 or a.shape != b.shape or not len(a):
        raise ValueError("Expected matching nonempty bin-mass vectors")
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("Nonfinite bin masses")
    if (a < 0).any() or (b < 0).any() or a.sum() <= 0 or b.sum() <= 0:
        raise ValueError("Invalid bin masses")
    a, b = a / a.sum(), b / b.sum()
    lower = float(a @ np.r_[0, b.cumsum()[:-1]])
    return lower, min(1.0, lower + float(a @ b))

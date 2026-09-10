"""Build the first NSS land and consumption exhibits and a generated note."""

import argparse
import json
from importlib.metadata import version
from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .nss import GROUPS, build_households  # noqa: E402
from .stats import binned_overlap, cdf, pairwise, quantile  # noqa: E402

OUTCOMES = {
    "owned_land_acres": ([0, 0.1, 0.5, 1, 2, 5], "Owned land (acres)", 5),
    "consumption_pc_monthly": (
        [500, 1000, 1500, 2000, 3000, 5000],
        "Consumption per person per month (survey-year rupees)",
        5000,
    ),
}
NAMES = {
    "owned_land_acres": "owned land",
    "consumption_pc_monthly": "per-person consumption",
}
COLORS = ["#0072B2", "#D55E00", "#009E73", "#6F4E7C"]
STYLES = ["-", "--", "-.", ":"]
BOOT_NOTE = (
    "Approximate 95% pointwise percentile intervals: 999 PSU bootstrap draws within "
    "states, fixed household weights; seed 20260910. This approximation does not "
    "reproduce NSS substratification, later sampling stages, or finite-population "
    "corrections. It is not an official NSS variance estimate."
)


def threshold_table(frame, rng, n_boot=999):
    psus = frame[["State", "FSU_Slno"]].drop_duplicates().reset_index(drop=True)
    psus["psu_index"] = np.arange(len(psus))
    frame = frame.merge(psus, on=["State", "FSU_Slno"], validate="many_to_one")
    counts = np.zeros((n_boot, len(psus)))
    for _, state in psus.groupby("State", sort=True):
        ix = state.psu_index.to_numpy()
        if len(ix) < 2:
            raise ValueError("Bootstrap requires multiple PSUs in every state")
        counts[:, ix] = rng.multinomial(len(ix), np.full(len(ix), 1 / len(ix)), n_boot)
    rows, numerators, denominators = [], [], []
    for outcome, (thresholds, _, _) in OUTCOMES.items():
        for group in GROUPS.values():
            base = frame[frame.group.eq(group)]
            d = base[base[outcome].notna()]
            if d.empty:
                raise ValueError(f"No observations for {group}/{outcome}")
            v, w = d[outcome].to_numpy(), d.weight.to_numpy()
            missing_w = base.weight.sum() - w.sum()
            den = np.bincount(d.psu_index, weights=w, minlength=len(psus))
            for t in thresholds:
                for relation in ("<", "<="):
                    indicator = v < t if relation == "<" else v <= t
                    num = np.bincount(
                        d.psu_index, weights=w * indicator, minlength=len(psus)
                    )
                    p = w[indicator].sum() / w.sum()
                    rows.append(
                        {
                            "outcome": outcome,
                            "group": group,
                            "relation": relation,
                            "threshold": t,
                            "percent": 100 * p,
                            "n": len(d),
                            "n_missing": len(base) - len(d),
                            "psus": d.psu_index.nunique(),
                            "weight_sum": w.sum(),
                            "missing_weight_percent": 100
                            * missing_w
                            / base.weight.sum(),
                            "missing_bound_low": 100
                            * w[indicator].sum()
                            / base.weight.sum(),
                            "missing_bound_high": 100
                            * (w[indicator].sum() + missing_w)
                            / base.weight.sum(),
                        }
                    )
                    numerators.append(num)
                    denominators.append(den)
    bn, bd = counts @ np.array(numerators).T, counts @ np.array(denominators).T
    if (bd <= 0).any():
        raise ValueError("A bootstrap draw has no observations in a reported domain")
    draws = 100 * bn / bd
    out = pd.DataFrame(rows)
    out["ci_low"], out["ci_high"] = np.quantile(draws, [0.025, 0.975], axis=0)
    contrasts = []
    for _, cell in out.groupby(["outcome", "relation", "threshold"], sort=False):
        for i, j in combinations(cell.index, 2):
            a, b = out.loc[i], out.loc[j]
            lo, hi = np.quantile(draws[:, i] - draws[:, j], [0.025, 0.975])
            contrasts.append(
                {
                    "outcome": a.outcome,
                    "relation": a.relation,
                    "threshold": a.threshold,
                    "group_a": a.group,
                    "group_b": b.group,
                    "difference_pp": a.percent - b.percent,
                    "ci_low": lo,
                    "ci_high": hi,
                }
            )
    return out, pd.DataFrame(contrasts)


def comparisons(frame):
    pairs, ranks, curves, diagnostics = [], [], [], []
    for outcome, (thresholds, _, _) in OUTCOMES.items():
        d = frame[frame[outcome].notna()]
        pooled = {q: quantile(d[outcome], d.weight, q) for q in (0.25, 0.5, 0.75)}
        for group, g in d.groupby("group", sort=False):
            values = np.unique(g[outcome])
            curves.extend(
                {"outcome": outcome, "group": group, "value": v, "percent": 100 * p}
                for v, p in zip(values, cdf(g[outcome], g.weight, values))
            )
            diagnostics.append(
                {
                    "outcome": outcome,
                    "group": group,
                    "n": len(g),
                    "zero_percent": 100 * cdf(g[outcome], g.weight, 0),
                    "min": g[outcome].min(),
                    "max": g[outcome].max(),
                    "median": quantile(g[outcome], g.weight, 0.5),
                    "weight_only_effective_n": g.weight.sum() ** 2
                    / (g.weight**2).sum(),
                }
            )
            for q, threshold in pooled.items():
                ranks.append(
                    {
                        "outcome": outcome,
                        "group": group,
                        "pooled_quantile": q,
                        "threshold": threshold,
                        "percent_strictly_below": 100
                        * cdf(g[outcome], g.weight, threshold, inclusive=False),
                    }
                )
        edges = [-np.inf, *thresholds, np.inf]
        for a, b in combinations(GROUPS.values(), 2):
            ga, gb = d[d.group.eq(a)], d[d.group.eq(b)]
            less, equal, greater, score = pairwise(
                ga[outcome], ga.weight, gb[outcome], gb.weight
            )
            pairs.append(
                {
                    "outcome": outcome,
                    "group_a": a,
                    "group_b": b,
                    "a_less_percent": 100 * less,
                    "equal_percent": 100 * equal,
                    "a_greater_percent": 100 * greater,
                    "a_less_half_ties_percent": 100 * score,
                    "binned_overlap_percent": 100
                    * binned_overlap(
                        ga[outcome], ga.weight, gb[outcome], gb.weight, edges
                    ),
                    "bin_edges": json.dumps(["-inf", *thresholds, "inf"]),
                }
            )
    return [pd.DataFrame(x) for x in (pairs, ranks, curves, diagnostics)]


def plot(curves, thresholds, region, output):
    region_label = region.replace("_", " ").title()
    plt.rcParams.update(
        {"font.size": 11, "axes.spines.top": False, "axes.spines.right": False}
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.6), sharey=True)
    for ax, (outcome, (_, label, xmax)) in zip(axes, OUTCOMES.items()):
        for group, color, style in zip(GROUPS.values(), COLORS, STYLES):
            c = curves[curves.outcome.eq(outcome) & curves.group.eq(group)]
            ax.step(
                np.r_[0, c.value],
                np.r_[0, c.percent],
                where="post",
                label=group,
                color=color,
                linestyle=style,
                linewidth=2,
            )
        ax.set(xlim=(0, xmax), ylim=(0, 100), xlabel=label)
        ax.grid(axis="y", alpha=0.2)
    axes[0].set_ylabel("Households at or below threshold (%)")
    axes[0].legend(frameon=False, loc="lower right")
    fig.suptitle(
        f"Caste in Common · {region_label}\nDifferent distributions can share "
        f"much of their range",
        fontsize=16,
    )
    fig.text(
        0.06,
        0.03,
        "NSS 77 (2019), visit 1 · Household weights · Descriptive ECDFs; no "
        "confidence bands\nReported zeros included; missing land excluded. "
        "Others is the residual social group.\nAxes zoom in; upper tails "
        "remain in denominators.",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.13, 1, 0.88))
    for ext in ("png", "svg"):
        fig.savefig(output / f"{region}_distributions.{ext}", dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharex=True)
    for ax, (outcome, cutoff, label) in zip(
        axes,
        [
            ("owned_land_acres", 1, "Owns less than 1 acre"),
            (
                "consumption_pc_monthly",
                2000,
                "Consumes less than Rs 2,000/person/month",
            ),
        ],
    ):
        t = (
            thresholds[
                thresholds.outcome.eq(outcome)
                & thresholds.relation.eq("<")
                & thresholds.threshold.eq(cutoff)
            ]
            .set_index("group")
            .loc[list(GROUPS.values())]
        )
        for y, (group, row), color in zip(range(4), t.iterrows(), COLORS):
            ax.plot([row.ci_low, row.ci_high], [y, y], color=color, linewidth=2)
            ax.plot(row.percent, y, "o", color=color)
            ax.annotate(
                f"{row.percent:.1f}%",
                (row.percent, y),
                xytext=(0, 9),
                textcoords="offset points",
                ha="center",
            )
        ax.set(
            yticks=range(4),
            yticklabels=list(GROUPS.values()),
            xlim=(0, 100),
            ylim=(-0.6, 3.7),
            xlabel="Households (%)",
            title=label,
        )
        ax.invert_yaxis()
        ax.grid(axis="x", alpha=0.15)
    fig.suptitle(f"The same threshold, every group · {region_label}", fontsize=16)
    fig.text(
        0.06,
        0.025,
        "NSS 77 (2019), visit 1 · Household weights · Approximate 95% "
        "pointwise intervals\n999 PSU bootstrap draws within states; fixed "
        "weights. Not official NSS design-based intervals.\nSurvey-year "
        "rupees; consumption is not income. Others is the residual social "
        "group; missing land is excluded.",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.19, 1, 0.92))
    for ext in ("png", "svg"):
        fig.savefig(output / f"{region}_thresholds.{ext}", dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--nss-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("output"))
    parser.add_argument("--data-output", type=Path, default=Path("data"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    args.data_output.mkdir(parents=True, exist_ok=True)
    hh, manifest = build_households(args.nss_dir)
    hh.to_parquet(args.data_output / "nss77_households.parquet", index=False)
    if not pd.read_parquet(args.data_output / "nss77_households.parquet").equals(hh):
        raise ValueError("Parquet round-trip changed data")
    metadata = {
        "source_files": manifest,
        "packages": {
            name: version(name) for name in ["numpy", "pandas", "matplotlib", "pyarrow"]
        },
        "rows": len(hh),
        "zero_weight_rows": int(hh.weight.eq(0).sum()),
        "land_missing": int((~hh.land_observed).sum()),
        "bootstrap": BOOT_NOTE,
    }
    (args.output / "provenance.json").write_text(json.dumps(metadata, indent=2) + "\n")
    note = [
        "# First look: land and consumption\n",
        "Exploratory estimates from NSS 77, visit 1. Social groups are the "
        "survey's reported ST, SC, OBC and Others categories. Others is not a "
        "verified upper-caste category.\n",
        BOOT_NOTE + "\n",
    ]
    hh = hh[hh.weight.gt(0)].copy()
    rng = np.random.default_rng(20260910)
    for region, frame in [("rural_india", hh), ("rural_bihar", hh[hh.State.eq("10")])]:
        print(f"Building {region}: {len(frame):,} households", flush=True)
        thresholds, contrasts = threshold_table(frame, rng)
        pairs, ranks, curves, diagnostics = comparisons(frame)
        for name, table in [
            ("thresholds", thresholds),
            ("threshold_differences", contrasts),
            ("pairwise", pairs),
            ("pooled_ranks", ranks),
            ("ecdf", curves),
            ("diagnostics", diagnostics),
        ]:
            table.to_csv(args.output / f"{region}_{name}.csv", index=False)
        plot(curves, thresholds, region, args.output)
        note.extend(
            [
                f"\n## {region.replace('_', ' ').title()}\n",
                f"{len(frame):,} households; {int((~frame.land_observed).sum()):,} "
                f"lack a land block and are excluded from land denominators. "
                f"Consumption includes all households.\n",
                "| Group | Owns <1 acre | Consumes <Rs 2,000/person/month "
                "|\n|---|---:|---:|",
            ]
        )
        for group in GROUPS.values():
            cells = []
            for outcome, cutoff in [
                ("owned_land_acres", 1),
                ("consumption_pc_monthly", 2000),
            ]:
                row = thresholds[
                    thresholds.group.eq(group)
                    & thresholds.outcome.eq(outcome)
                    & thresholds.relation.eq("<")
                    & thresholds.threshold.eq(cutoff)
                ].iloc[0]
                cells.append(
                    f"{row.percent:.1f}% [{row.ci_low:.1f}, {row.ci_high:.1f}]"
                )
            note.append(f"| {group} | {' | '.join(cells)} |")
        note.extend(
            [
                f"\n![Common thresholds]({region}_thresholds.png)\n",
                f"![Distributions]({region}_distributions.png)\n",
            ]
        )
        for outcome in OUTCOMES:
            p = pairs[
                pairs.outcome.eq(outcome)
                & pairs.group_a.eq("SC")
                & pairs.group_b.eq("Others")
            ].iloc[0]
            note.append(
                f"For {NAMES[outcome]}, an independently drawn SC household has a "
                f"larger value than an Others household in "
                f"**{p.a_greater_percent:.1f}%** of pairs, a smaller value in "
                f"**{p.a_less_percent:.1f}%**, and ties in **{p.equal_percent:.1f}%**. "
                f"These pairwise estimates are descriptive and have no intervals in "
                f"this pilot.\n"
            )
    note.extend(
        [
            "\n## Reading the results\n",
            "Substantial overlap can coexist with large gaps in typical resources "
            "and threshold rates. The comparisons do not estimate an effect of "
            "caste, establish equal opportunity, or evaluate a reservation "
            "policy. Land quantity is not land value or total wealth; consumption "
            "is not earnings. Rupee thresholds are historical nominal benchmarks, "
            "not present-day poverty lines.\n",
            "Reported zero land includes amounts rounded to 0.00 acres by the "
            "source. Sparse land categories are filled with zero only after "
            "reconciliation to the reported household total; wholly absent land "
            "blocks remain missing. The threshold CSVs provide worst-case bounds "
            "for those missing outcomes.\n",
            "The pairwise CSV separately reports ties and a fixed-bin overlap "
            "coefficient. Its value depends on bin edges and is not a percentage "
            "of people who are economically identical. Pooled-rank thresholds use "
            "the inverse weighted ECDF; ties mean a pooled quartile need not "
            "contain exactly 25% strictly below it.\n",
            "See [the design](../docs/design.md) and [source "
            "audit](../docs/sources.md) for scope, definitions and the next data "
            "sources.",
        ]
    )
    (args.output / "first-look.md").write_text("\n".join(note) + "\n")


if __name__ == "__main__":
    main()

"""Reproduce income, reported-jati, tail-composition, and prediction exhibits."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .ihds import GROUPS, read_households
from .prediction import evaluate
from .stats import cdf, pairwise, quantile

plt.switch_backend("Agg")


def support(d, weight_name="weight"):
    w = d[weight_name].to_numpy(float)
    return {"n": len(d), "psus": d.psu.nunique(), "weight_ess": w.sum() ** 2 / (w @ w)}


def summarize(d):
    rows, pairs = [], []
    for scope, frame in [
        ("India", d),
        ("Rural India", d[d.urban == 0]),
        ("Bihar", d[d.state == 10]),
    ]:
        for weight_name in ["weight", "person_weight"]:
            groups = dict(tuple(frame.groupby("group")))
            for label, g in groups.items():
                for cutoff in [1000, 2000, 5000, 10000]:
                    rows.append(
                        {
                            "scope": scope,
                            "group": label,
                            "weighting": weight_name,
                            **support(g, weight_name),
                            "cutoff": cutoff,
                            "operator": "<",
                            "pct": 100
                            * float(
                                cdf(
                                    g.income_monthly_pc,
                                    g[weight_name],
                                    cutoff,
                                    inclusive=False,
                                )
                            ),
                        }
                    )
            for a in GROUPS.values():
                for b in GROUPS.values():
                    if a not in groups or b not in groups:
                        continue
                    ga, gb = groups[a], groups[b]
                    less, ties, greater, _ = pairwise(
                        ga.income_monthly_pc,
                        ga[weight_name],
                        gb.income_monthly_pc,
                        gb[weight_name],
                    )
                    pairs.append(
                        {
                            "scope": scope,
                            "weighting": weight_name,
                            "a": a,
                            "b": b,
                            "a_less_pct": 100 * less,
                            "ties_pct": 100 * ties,
                            "a_greater_pct": 100 * greater,
                            "a_auc": greater + ties / 2,
                        }
                    )
    return pd.DataFrame(rows), pd.DataFrame(pairs)


def labels(d):
    rows = []
    for (state, label), g in d.groupby(["state_name", "jati_label"]):
        s = support(g)
        if not label or s["n"] < 100 or s["psus"] < 20 or s["weight_ess"] < 50:
            continue
        rows.append(
            {
                "state": state,
                "reported_label": label,
                **s,
                "median": quantile(g.income_monthly_pc, g.weight, 0.5),
                "p10": quantile(g.income_monthly_pc, g.weight, 0.1),
                "p90": quantile(g.income_monthly_pc, g.weight, 0.9),
                "below_2000_pct": 100
                * float(cdf(g.income_monthly_pc, g.weight, 2000, inclusive=False)),
                "below_5000_pct": 100
                * float(cdf(g.income_monthly_pc, g.weight, 5000, inclusive=False)),
            }
        )
    return pd.DataFrame(rows).sort_values(["median", "state", "reported_label"])


def label_pairs(d, table):
    rows = []
    for state, eligible in table.groupby("state", sort=True):
        ordered = eligible.sort_values("median").reported_label.tolist()
        frame = d[d.state_name == state]
        for a in ordered:
            for b in ordered:
                ga, gb = frame[frame.jati_label == a], frame[frame.jati_label == b]
                less, ties, greater, _ = pairwise(
                    ga.income_monthly_pc, ga.weight, gb.income_monthly_pc, gb.weight
                )
                rows.append(
                    {
                        "state": state,
                        "a": a,
                        "b": b,
                        "a_greater_pct": greater * 100,
                        "ties_pct": ties * 100,
                        "a_less_pct": less * 100,
                        "a_auc": greater + ties / 2,
                    }
                )
    return pd.DataFrame(rows)


def plot_label_pairs(pairs, table, out):
    counts = (
        table.groupby("state", sort=True)
        .size()
        .sort_values(ascending=False, kind="stable")
    )
    states = counts.head(4).index
    fig, axes = plt.subplots(2, 2, figsize=(11, 10))
    for ax, state in zip(axes.flat, states):
        order = table[table.state == state].sort_values("median").reported_label
        m = pairs[pairs.state == state].pivot(index="a", columns="b", values="a_auc")
        m = m.loc[order, order]
        ax.imshow(m, cmap="RdBu", vmin=0, vmax=1)
        for i in range(len(order)):
            for j in range(len(order)):
                ax.text(j, i, f"{m.iloc[i, j]:.0%}", ha="center", va="center")
        ax.set_xticks(range(len(order)), order.str.title(), rotation=35, ha="right")
        ax.set_yticks(range(len(order)), order.str.title())
        ax.set_title(state, loc="left")
    fig.suptitle(
        "Within-state reported-label comparisons\n"
        "Probability that row income exceeds column income; half ties",
        x=0.02,
        ha="left",
        fontsize=15,
    )
    fig.text(
        0.02,
        0.015,
        "IHDS-II 2011–12; household weights; "
        "annual per-capita income ÷ 12.\n"
        "Four states with the most eligible labels (n≥100, PSUs≥20, weight ESS≥50). "
        "Rows/columns sorted by sample median.\n"
        "Literal responses, not harmonized identities; some are broad labels. "
        "Descriptive estimates without sampling intervals.",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.085, 1, 0.94))
    for extension in ["png", "svg"]:
        fig.savefig(out / f"ihds_reported_jati_pairwise.{extension}", dpi=160)
    plt.close(fig)


def tail_composition(d):
    rows = []
    total = d.weight.sum()
    for cutoff in [1000, 2000, 5000, 10000]:
        for side in ["below", "at_or_above"]:
            mask = d.income_monthly_pc < cutoff
            if side == "at_or_above":
                mask = ~mask
            tail_total = d.loc[mask, "weight"].sum()
            for label, g in d.groupby("group"):
                tail = g.loc[mask.loc[g.index]]
                prior = g.weight.sum() / total
                posterior = tail.weight.sum() / tail_total if tail_total else np.nan
                rows.append(
                    {
                        "cutoff": cutoff,
                        "side": side,
                        "group": label,
                        "n_in_tail": len(tail),
                        "psus_in_tail": tail.psu.nunique(),
                        "population_share_pct": 100 * prior,
                        "tail_composition_pct": 100 * posterior,
                        "lift": posterior / prior,
                        "group_in_tail_pct": 100 * tail.weight.sum() / g.weight.sum(),
                        "all_households_in_tail_pct": 100 * tail_total / total,
                    }
                )
    return pd.DataFrame(rows)


def plot_pairs(pairs, out):
    groups = list(GROUPS.values())
    p = pairs.query("scope == 'India' and weighting == 'weight'")
    m = p.pivot(index="a", columns="b", values="a_auc").loc[groups, groups]
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    im = ax.imshow(m, cmap="RdBu", vmin=0, vmax=1)
    for i in range(len(groups)):
        for j in range(len(groups)):
            ax.text(
                j,
                i,
                f"{m.iloc[i, j]:.0%}",
                ha="center",
                va="center",
                color="black" if 0.2 < m.iloc[i, j] < 0.8 else "white",
            )
    ax.set_xticks(range(len(groups)), groups, rotation=30, ha="right")
    ax.set_yticks(range(len(groups)), groups)
    ax.set_xlabel("Draw a household from this column group")
    ax.set_ylabel("Draw a household from this row group")
    ax.set_title(
        "How often does the row group have more income?\n"
        "Independent household draws; ties count as half a win",
        loc="left",
    )
    fig.colorbar(im, ax=ax, label="Tie-adjusted probability", shrink=0.8)
    fig.text(
        0.02,
        0.015,
        "IHDS-II 2011–12 • annual household income per person ÷ 12 • "
        "household weights\nDescriptive estimates; no sampling intervals. "
        "IHDS ‘Others’ differs from NSS ‘Others’.",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    for extension in ["png", "svg"]:
        fig.savefig(out / f"ihds_income_pairwise.{extension}", dpi=160)
    plt.close(fig)


def plot_labels(table, out):
    shown = table.nlargest(24, "n").sort_values("median").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10, 10))
    y = np.arange(len(shown))
    ax.hlines(y, shown.p10, shown.p90, color="#8bacc2", linewidth=5)
    ax.scatter(shown["median"], y, color="#123f59", zorder=3)
    ax.axvline(2000, color="#a84b2c", linestyle="--", linewidth=1)
    ax.axvline(5000, color="#a84b2c", linestyle=":", linewidth=1)
    ax.set_yticks(
        y,
        [
            f"{r.reported_label.title()} · {r.state}\n" f"n={r.n:,}, PSUs={r.psus}"
            for r in shown.itertuples()
        ],
    )
    ax.invert_yaxis()
    ax.set_xlabel("Average monthly income per person (nominal 2011–12 rupees)")
    ax.set_title(
        "Reported jati labels: different medians, overlapping ranges\n"
        "Dot: median • line: 10th–90th percentile",
        loc="left",
    )
    ax.grid(axis="x", alpha=0.2)
    fig.text(
        0.02,
        0.015,
        "24 largest eligible state–label cells by sample size; sorted "
        "descriptively on this sample.\n"
        "At least 100 households, 20 PSUs, weight ESS 50. "
        "Spelling variants unmerged; some responses are broad labels.\n"
        "Household weights. Lines show within-group spread, not confidence intervals. "
        "Extreme 20% outside lines.",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.085, 1, 1))
    for extension in ["png", "svg"]:
        fig.savefig(out / f"ihds_reported_jati_ranges.{extension}", dpi=160)
    plt.close(fig)


def write_note(d, thresholds, pairs, label_table, scores, out, audit):
    lines = [
        "# IHDS-II: income and reported jati labels",
        "",
        "Generated from ICPSR 36151 DS0002. Survey period: 2011–12. "
        "Income is annual net household income divided by household size and 12, "
        "not observed month-by-month cash flow. "
        "Amounts are nominal survey-year rupees.",
        "",
        "## Same cutoff, different groups",
        "",
        "Percent of households below the cutoff; household weights, all India "
        "(rural and urban). These are illustrative cutoffs, "
        "not official poverty lines.",
        "",
        "| Group | Below ₹2,000/person/month | Below ₹5,000/person/month |",
        "|---|---:|---:|",
    ]
    t = thresholds.query("scope == 'India' and weighting == 'weight'")
    for label in GROUPS.values():
        v = t[t.group == label].set_index("cutoff").pct
        lines.append(f"| {label} | {v[2000]:.1f}% | {v[5000]:.1f}% |")
    p = pairs.query(
        "scope == 'India' and weighting == 'weight' "
        "and a == 'Forward/General' and b == 'OBC'"
    ).iloc[0]
    lines += [
        "",
        "## Two random draws",
        "",
        f"Forward/General (excluding Brahmins) has greater per-person income than "
        f"OBC in **{p.a_greater_pct:.1f}%** of independent household pairs; "
        f"OBC has greater income in **{p.a_less_pct:.1f}%**; "
        f"**{p.ties_pct:.2f}%** tie. Half-tie AUC: **{p.a_auc:.3f}**.",
        "",
        "![Pairwise income probabilities](ihds_income_pairwise.png)",
        "",
        "## Reported labels, ordered descriptively",
        "",
        f"{len(label_table)} state–label cells meet n≥100, PSU≥20, Kish weight ESS≥50. "
        "Kish ESS describes unequal weights, not clustering-adjusted precision. "
        "Only case and whitespace are normalized; these are not harmonized jati "
        "identities. Spelling variants and broad/religious responses remain separate.",
        "",
        "![Sorted reported-label ranges](ihds_reported_jati_ranges.png)",
        "",
        "![Within-state pairwise comparisons](ihds_reported_jati_pairwise.png)",
        "",
        "## Held-out prediction",
        "",
        "Fixed bins: <0; [0,1000); [1000,2000); [2000,5000); [5000,10000); "
        "≥10000 rupees/person/month. Five folds hold complete PSUs out. "
        "Every household is evaluated, including missing/unseen-label fallbacks. "
        "Each eligible training cell needs 30 households and 5 PSUs; its "
        "probabilities shrink toward its parent using weight ESS and a prior of "
        "10, 30, or 100 effective households. Scores are model-dependent, not an "
        "estimate of all information potentially contained in actual jati.",
        "",
        "Mean across three splits, prior=30. Lower log loss is better. "
        "Coverage is the household-weighted share receiving an eligible cell's "
        "prediction at that level; the rest use a parent prediction.",
        "",
        "| Information supplied | Log loss (nats) | Own-level coverage |",
        "|---|---:|---:|",
    ]
    names = {
        "pooled": "None",
        "broad": "Broad caste only",
        "geography": "State × rural/urban",
        "geography_broad": "Geography + broad caste",
        "geography_broad_label": "Geography + broad caste + literal jati response",
    }
    for model, label in names.items():
        s = scores[(scores.model == model) & (scores.prior_effective_households == 30)]
        lines.append(
            f"| {label} | {s.log_loss_nats.mean():.4f} | "
            f"{s.own_level_coverage_pct.mean():.1f}% |"
        )
    lines += [
        "",
        "All seeds and prior sensitivities are in `ihds_prediction.csv`. "
        "Split variation is not a confidence interval. Geographic adjustment "
        "removes part of what a geographically concentrated jati may predict. "
        "This resolution cannot measure distinctions within the top ₹10,000+ bin.",
        "",
    ]
    tails = tail_composition(d)
    lines += [
        "",
        "## Does higher income identify a caste?",
        "",
        "Households at or above ₹10,000 per person per month, in 2011–12 rupees. "
        "Composition is P(group | in tail); lift divides it by the population share. "
        "Recall is P(in tail | group). "
        "These describe different directions of inference.",
        "",
        "| Group | Population share | Tail composition | Lift | Group in tail |",
        "|---|---:|---:|---:|---:|",
    ]
    for label in GROUPS.values():
        row = tails[
            (tails.cutoff == 10000)
            & (tails.side == "at_or_above")
            & (tails.group == label)
        ].iloc[0]
        lines.append(
            f"| {label} | {row.population_share_pct:.1f}% | "
            f"{row.tail_composition_pct:.1f}% | {row.lift:.2f} | "
            f"{row.group_in_tail_pct:.1f}% |"
        )
    lines += [
        "",
        "The denominator includes missing broad groups; therefore displayed "
        "composition shares need not sum to 100%. Detailed-jati inference "
        "requires a reviewed label crosswalk.",
    ]
    lines += [
        "",
        "## Audit and limitations",
        "",
        f"- {len(d):,} unique households; {audit['bihar_households']:,} in Bihar; "
        f"{d.psu.nunique():,} complete PSU identifiers.",
        f"- {audit['negative_income_households']} negative and "
        f"{audit['zero_income_households']} zero annual income reports retained.",
        f"- {audit['missing_broad_group']} missing broad groups are an explicit "
        "category in prediction and tail denominators.",
        "- IHDS Others is code 6, distinct from both Forward/General and the NSS "
        "residual Others. No upper-caste merge is imposed.",
        "- Threshold and pairwise CSVs include household and person weighting; "
        "plots use household weights. Person draws assign household per-capita income.",
        "- Tail CSV includes prior shares, posterior composition, lift, group recall, "
        "and unweighted household/PSU support. It tests the reverse conditional.",
        "- These are descriptive pilot estimates without sampling "
        "confidence intervals. "
        "Do not interpret sample median ordering as a precise population hierarchy.",
        "- No present-day rupee conversion or annual mobility has been estimated.",
        "",
        "See [methods and wider data search](../docs/informativeness.md) and "
        "[IHDS ingestion audit](../docs/ihds-audit.md).",
    ]
    (out / "ihds-first-look.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("output"))
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    d = read_households(args.source)
    if len(d) != 42152 or (d.state == 10).sum() != 1547:
        raise ValueError("Unexpected IHDS-II sample frame")
    Path("data").mkdir(exist_ok=True)
    d.to_parquet("data/ihds2_income_households.parquet", index=False)
    thresholds, pairs = summarize(d)
    label_table = labels(d)
    jati_pairs = label_pairs(d, label_table)
    tails = tail_composition(d)
    scores = evaluate(d)
    for name, table in [
        ("thresholds", thresholds),
        ("pairwise", pairs),
        ("reported_labels", label_table),
        ("reported_jati_pairwise", jati_pairs),
        ("tails", tails),
        ("prediction", scores),
    ]:
        table.to_csv(out / f"ihds_{name}.csv", index=False)
    audit = {
        "source": str(args.source.resolve()),
        "sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
        "households": len(d),
        "bihar_households": int((d.state == 10).sum()),
        "psus": int(d.psu.nunique()),
        "negative_income_households": int((d.income_annual_hh < 0).sum()),
        "zero_income_households": int((d.income_annual_hh == 0).sum()),
        "missing_broad_group": int((d.group == "Not reported").sum()),
        "blank_jati_labels": int((d.jati_label == "").sum()),
        "unique_normalized_jati_labels": int(d.jati_label.nunique()),
        "eligible_state_label_cells": len(label_table),
    }
    (out / "ihds_provenance.json").write_text(json.dumps(audit, indent=2) + "\n")
    plot_pairs(pairs, out)
    plot_labels(label_table, out)
    plot_label_pairs(jati_pairs, label_table, out)
    write_note(d, thresholds, pairs, label_table, scores, out, audit)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()

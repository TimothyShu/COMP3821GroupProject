"""Report figures and tables from the benchmark CSVs.

Usage: PYTHONPATH=src uv run python experiments/plot.py [--csv CSV] [--no-relabel-csv CSV] [--n N]
Reads results/raw/benchmark_ratios.csv (and benchmark_ratios_no_relabel.csv for F6, if present).
Writes results/figures/f*.pdf and results/tables/*.csv / *.tex:

  F1 f1_ratio_vs_n.pdf      rounds / b (n <= 30) or rounds / L(G) per family; error bars = sd over seeds
  F2 f2_gap_vs_structure.pdf 3-approx rounds / best rounds against diam / sqrt(n), coloured by max/avg degree
  F3 f3_runtime.pdf         median runtime against n, log-log, pooled over families
  F4 f4_hybrids.pdf         hybrid rounds / plain 3-approx rounds per family
  F5 f5_spread.pdf          sd of rounds over relabellings per algorithm and family
  F6 f6_labelling.pdf       rounds with generator labels against relabelled
  T1 t1_small_exact.*       mean rounds / b per algorithm and family, n <= 30
  summary.csv               per-algorithm headline numbers (for the hypothesis table)
F2, F4, F5 and F6 use the largest size in the CSV unless --n is given.
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "results" / "figures"
TABLES = ROOT / "results" / "tables"

ALGS = {  # column order, display name, colour
    "three_approx": ("3-approx", "#1f77b4"),
    "three_approx_degree": ("3-approx (degree order)", "#6baed6"),
    "three_approx_eigen": ("3-approx (eigen order)", "#08519c"),
    "three_approx_farthest": ("3-approx (farthest order)", "#9ecae1"),
    "max_degree": ("Max degree", "#d62728"),
    "farthest_first": ("Farthest-first", "#2ca02c"),
    "eigen_centrality": ("Eigenvector centrality", "#ff7f0e"),
}
HYBRIDS = ["three_approx_degree", "three_approx_eigen", "three_approx_farthest"]
FAMILIES = {
    "path": "Path", "star": "Star", "dary_tree": "d-ary tree", "grid": "Grid",
    "spider": "Spider", "centipede": "Centipede", "barbell": "Barbell", "cluster": "Cluster",
    "small_world": "Small-world", "scale_free": "Scale-free",
}
GRAPH = ["family", "n_target", "seed"]  # one benchmark graph


def name(alg: str) -> str:
    return ALGS[alg][0]


def colour(alg: str) -> str:
    return ALGS[alg][1]


def ordered(values) -> list[str]:
    present = set(values)
    return [f for f in FAMILIES if f in present] + sorted(present - set(FAMILIES))


def label(family: str) -> str:
    return FAMILIES.get(family, family)


def save(fig: plt.Figure, file: str) -> None:
    fig.savefig(FIGURES / file, bbox_inches="tight")
    plt.close(fig)
    print(f"  {FIGURES.relative_to(ROOT) / file}")


def f1_ratio_vs_n(df: pd.DataFrame) -> None:
    families = ordered(df.family)
    cols = 5
    rows = -(-len(families) // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(3.2 * cols, 2.6 * rows), sharex=True, squeeze=False)
    stats = df.groupby(["family", "alg", "n_target"]).ratio.agg(["mean", "std"]).reset_index()
    small, large = df.n_target[df.n_target <= 30], df.n_target[df.n_target > 30]
    split = np.sqrt(small.max() * large.min()) if len(small) and len(large) else None
    for ax, family in zip(axes.flat, families):
        for alg in ALGS:
            s = stats[(stats.family == family) & (stats.alg == alg)]
            if not s.empty:
                ax.errorbar(s.n_target, s["mean"], yerr=s["std"].fillna(0), color=colour(alg),
                            marker="o", ms=2.5, lw=1, capsize=1.5, label=name(alg))
        ax.axhline(3, ls="--", color="grey", lw=0.8)
        if split:
            ax.axvline(split, ls=":", color="grey", lw=0.6)
        ax.set_xscale("log")
        ax.set_title(label(family), fontsize=9)
        ax.tick_params(labelsize=7)
    for ax in axes.flat[len(families):]:
        ax.set_visible(False)
    for ax in axes[:, 0]:
        ax.set_ylabel("rounds / b  or  / L(G)", fontsize=8)
    for ax in axes[-1]:
        ax.set_xlabel("n", fontsize=8)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, fontsize=8, frameon=False,
               bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("Ratio against n. Left of the dotted line: rounds / exact b; right: rounds / L(G) "
                 "(exact b for path and star). Dashed: 3-approx guarantee", fontsize=9)
    fig.tight_layout()
    save(fig, "f1_ratio_vs_n.pdf")


def f2_gap_vs_structure(big: pd.DataFrame) -> None:
    best = big.groupby(GRAPH).rounds.min().rename("best")
    apx = big[big.alg == "three_approx"].set_index(GRAPH).join(best)
    apx["gap"] = apx.rounds / apx.best
    per = apx.groupby("family")[["diam_over_sqrt_n", "maxdeg_over_avgdeg", "gap"]].mean()
    fig, ax = plt.subplots(figsize=(5.5, 4))
    points = ax.scatter(per.diam_over_sqrt_n, per.gap, c=per.maxdeg_over_avgdeg, s=60,
                        cmap="viridis", norm=matplotlib.colors.LogNorm(), edgecolor="k", lw=0.5)
    nudge = {"centipede": (4, -9), "spider": (4, 5)}  # these two sit almost on top of each other
    for family, row in per.iterrows():
        ax.annotate(label(family), (row.diam_over_sqrt_n, row.gap), fontsize=7,
                    xytext=nudge.get(family, (4, 3)), textcoords="offset points")
    ax.set_xscale("log")
    ax.set_xlabel(r"diam(G) / $\sqrt{n}$")
    ax.set_ylabel("3-approx rounds / best rounds (any algorithm)")
    fig.colorbar(points, ax=ax, label=r"$\Delta(G)\,/\,\bar d(G)$")
    ax.set_title(f"Gap against structure, n = {big.n_target.iloc[0]}, mean over seeds", fontsize=9)
    fig.tight_layout()
    save(fig, "f2_gap_vs_structure.pdf")


def slope(t: pd.Series) -> float:
    t = t[t.index >= 50]
    return np.polyfit(np.log(t.index), np.log(t.values), 1)[0] if len(t) > 1 else float("nan")


def f3_runtime(df: pd.DataFrame) -> dict[str, float]:
    fig, ax = plt.subplots(figsize=(5.5, 4))
    slopes = {}
    for alg in ALGS:
        t = df[df.alg == alg].groupby("n_target").runtime_s.median()
        if t.empty:
            continue
        slopes[alg] = slope(t)
        ax.plot(t.index, t.values, marker="o", ms=3, color=colour(alg),
                label=f"{name(alg)} (slope {slopes[alg]:.2f})")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("n")
    ax.set_ylabel("median runtime (s)")
    ax.legend(fontsize=7, frameon=False)
    ax.set_title("Runtime, median over families and seeds; slope fitted for n >= 50", fontsize=9)
    fig.tight_layout()
    save(fig, "f3_runtime.pdf")
    return slopes


def f4_hybrids(big: pd.DataFrame) -> None:
    rounds = big.pivot_table(index=GRAPH, columns="alg", values="rounds")
    rel = rounds[HYBRIDS].div(rounds["three_approx"], axis=0).groupby(level="family").mean()
    rel = rel.loc[ordered(rel.index)]
    fig, ax = plt.subplots(figsize=(8, 3.5))
    x = np.arange(len(rel))
    width = 0.8 / len(HYBRIDS)
    for i, alg in enumerate(HYBRIDS):
        ax.bar(x + (i - 1) * width, rel[alg], width, color=colour(alg), label=name(alg))
    ax.axhline(1, color="k", lw=0.8)
    ax.set_ylim(0.5, 1.25)
    ax.set_xticks(x, [label(f) for f in rel.index], rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("rounds / plain 3-approx rounds")
    ax.legend(fontsize=7, frameon=False, ncol=3, loc="upper center")
    ax.set_title(f"Hybrid scan orders against plain 3-approx, n = {big.n_target.iloc[0]} "
                 "(below 1: hybrid better)", fontsize=9)
    fig.tight_layout()
    save(fig, "f4_hybrids.pdf")


def f5_spread(big: pd.DataFrame) -> pd.DataFrame:
    sd = big.pivot_table(index="family", columns="alg", values="rounds", aggfunc="std")
    sd = sd.loc[ordered(sd.index), [a for a in ALGS if a in sd.columns]]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.imshow(sd.values, cmap="Reds", aspect="auto")
    for (i, j), v in np.ndenumerate(sd.values):
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7)
    ax.set_xticks(range(sd.shape[1]), [name(a) for a in sd.columns], rotation=30, ha="right",
                  fontsize=7)
    ax.set_yticks(range(sd.shape[0]), [label(f) for f in sd.index], fontsize=8)
    ax.set_title(f"sd of rounds over relabellings (and random draws), n = {big.n_target.iloc[0]}",
                 fontsize=9)
    fig.tight_layout()
    save(fig, "f5_spread.pdf")
    return sd


def f6_labelling(big: pd.DataFrame, plain: pd.DataFrame) -> None:
    plain = plain[plain.n_target == big.n_target.iloc[0]]
    families = ordered(plain.family)
    if not families:
        return
    fig, axes = plt.subplots(1, len(families), figsize=(4 * len(families), 3.2), squeeze=False)
    algs = [a for a in ALGS if a in set(plain.alg)]
    x = np.arange(len(algs))
    for ax, family in zip(axes[0], families):
        gen = plain[plain.family == family].groupby("alg").rounds.mean().reindex(algs)
        rel = big[big.family == family].groupby("alg").rounds.agg(["mean", "std"]).reindex(algs)
        ax.bar(x - 0.2, gen, 0.4, color="#bbbbbb", label="generator labels")
        ax.bar(x + 0.2, rel["mean"], 0.4, yerr=rel["std"], color=[colour(a) for a in algs],
               capsize=2, label="relabelled (mean, sd)")
        ax.set_xticks(x, [name(a) for a in algs], rotation=40, ha="right", fontsize=7)
        for xi, v in zip(x, gen):
            ax.text(xi - 0.2, v * 1.05, f"{v:.0f}", ha="center", fontsize=6)
        log = gen.max() > 4 * rel["mean"].min()  # one bar dwarfs the rest
        if log:
            ax.set_yscale("log")
            ticks = [t for t in (10, 20, 50, 100, 200, 500, 1000, 2000, 5000) if t <= 2 * gen.max()]
            ax.set_yticks(ticks, [str(t) for t in ticks])
            ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.set_title(label(family), fontsize=9)
        ax.set_ylabel("rounds (log scale)" if log else "rounds", fontsize=8)
    axes[0, 0].legend(fontsize=7, frameon=False, loc="upper left")
    fig.suptitle(f"Labelling artefact, n = {big.n_target.iloc[0]}", fontsize=9)
    fig.tight_layout()
    save(fig, "f6_labelling.pdf")


def write_table(table: pd.DataFrame, stem: str, caption: str, fmt: str = "{:.2f}") -> None:
    table.to_csv(TABLES / f"{stem}.csv", float_format="%.4f")
    header = " & ".join(["Family", *table.columns]) + r" \\"
    body = [" & ".join([str(i), *(fmt.format(v) if pd.notna(v) else "--" for v in row)]) + r" \\"
            for i, row in zip(table.index, table.values)]
    tex = [
        r"\begin{table}[ht]", r"\centering\small",
        r"\begin{tabular}{l" + "r" * table.shape[1] + "}", r"\toprule", header, r"\midrule",
        *body[:-1], r"\midrule", body[-1], r"\bottomrule", r"\end{tabular}",
        rf"\caption{{{caption}}}", rf"\label{{tab:{stem}}}", r"\end{table}",
    ]
    (TABLES / f"{stem}.tex").write_text("\n".join(tex) + "\n")
    print(f"  {TABLES.relative_to(ROOT)}/{stem}.csv, .tex")


def t1_small_exact(df: pd.DataFrame) -> None:
    small = df[df.ratio_is_exact & (df.n_target <= 30)]
    table = small.pivot_table(index="family", columns="alg", values="ratio", aggfunc="mean")
    table = table.loc[ordered(table.index), [a for a in ALGS if a in table.columns]]
    table.loc["All"] = small.groupby("alg").ratio.mean()
    table.index = [label(f) for f in table.index]
    table.columns = [name(a) for a in table.columns]
    write_table(table, "t1_small_exact",
                r"Mean rounds\,/\,$b(G)$ for $n \le 30$ (exact $b$), over sizes and seeds.")


def summary(df: pd.DataFrame, slopes: dict[str, float]) -> None:
    small = df[df.ratio_is_exact & (df.n_target <= 30)]
    big = df[df.n_target >= 50]
    best = big.groupby(GRAPH).rounds.transform("min")
    rows = {}
    for alg in ALGS:
        s, b = small[small.alg == alg], big[big.alg == alg]
        if s.empty and b.empty:
            continue
        rows[name(alg)] = {
            "small_mean_ratio": s.ratio.mean(), "small_max_ratio": s.ratio.max(),
            "small_optimal_share": (s.ratio == 1).mean(),
            "big_mean_ratio": b.ratio.mean(), "big_max_ratio": b.ratio.max(),
            "best_or_tied_share": (b.rounds == best[b.index]).mean(),
            "runtime_slope": slopes.get(alg),
            "median_runtime_s_at_max_n": b[b.n_target == b.n_target.max()].runtime_s.median(),
            "valid_share": df[df.alg == alg].valid.mean(),
        }
    pd.DataFrame(rows).T.to_csv(TABLES / "summary.csv", float_format="%.4f")
    print(f"  {TABLES.relative_to(ROOT)}/summary.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description="Report figures and tables.")
    parser.add_argument("--csv", type=Path, default=ROOT / "results/raw/benchmark_ratios.csv")
    parser.add_argument("--no-relabel-csv", type=Path,
                        default=ROOT / "results/raw/benchmark_ratios_no_relabel.csv")
    parser.add_argument("--n", type=int, help="size for F2, F4, F5, F6 (default: largest)")
    args = parser.parse_args()

    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.csv)
    big = df[df.n_target == (args.n or df.n_target.max())]
    f1_ratio_vs_n(df)
    f2_gap_vs_structure(big)
    slopes = f3_runtime(df)
    f4_hybrids(big)
    f5_spread(big).to_csv(TABLES / "f5_spread.csv", float_format="%.4f")
    if args.no_relabel_csv.exists():
        f6_labelling(big, pd.read_csv(args.no_relabel_csv))
    t1_small_exact(df)
    summary(df, slopes)


if __name__ == "__main__":
    main()

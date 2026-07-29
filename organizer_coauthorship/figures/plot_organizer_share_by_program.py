#!/usr/bin/env python3
"""Annual organizer-coauthorship rates by NBER SI program; series sized by papers.

Adds a paper-weighted average series (total organizer-authored papers /
total papers across programs in that year).
"""

from __future__ import annotations

import tempfile
import zipfile
from collections.abc import Iterable
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "figures"
OLD_ZIP = Path("/Users/jmfletcher/Downloads/nber_si_2000_2019_csv_bundle.zip")
OLD_CSV = Path("/tmp/nber_si_bundle/nber_si_program_year_summary_2000_2019.csv")

# Expanded colorblind-friendly palette; program colors are assigned once and
# reused across every figure (see build_program_color_map). Keep this longer
# than the set of large co-plotted programs so the top ranks stay unique.
PALETTE = [
    "#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7",
    "#56B4E9", "#F0E442", "#44AA99", "#882255", "#117733",
    "#332288", "#88CCEE", "#AA4499", "#661100", "#6699CC",
    "#999933", "#CC6677", "#888888", "#DDCC77", "#EE7733",
    "#0077BB", "#33BBEE", "#EE3377", "#009988", "#BBBBBB",
    "#CC3311", "#22A884", "#7AA6DC", "#DAA520", "#8B4513",
    "#1B9E77", "#D95F02", "#7570B3", "#E7298A", "#66A61E",
    "#E6AB02", "#A6761D", "#666666", "#A6CEE3", "#1F78B4",
    "#B2DF8A", "#33A02C", "#FB9A99", "#E31A1C", "#FDBF6F",
    "#FF7F00", "#CAB2D6", "#6A3D9A", "#FFFF99", "#B15928",
]
AVG_COLOR = "#1A1A1A"
# Grey used for non-focus background series (not a program identity color).
BG_COLOR = "#B8B8B8"


def build_program_color_map(
    program_codes: Iterable[str],
    papers_by_code: dict[str, float] | None = None,
) -> dict[str, str]:
    """Stable color for each program_code, identical across all figures.

    When paper totals are supplied, larger programs get the first (unique) palette
    slots so series that co-appear on figures are less likely to share a color.
    Assignment is deterministic given the same program set and paper totals.
    """
    codes = {str(c) for c in program_codes if pd.notna(c)}
    if papers_by_code:
        ordered = sorted(codes, key=lambda c: (-float(papers_by_code.get(c, 0.0)), c))
    else:
        ordered = sorted(codes)
    return {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(ordered)}


def colors_for(codes: list[str], color_map: dict[str, str]) -> dict[str, str]:
    """Subset of the global map for the codes plotted in one figure."""
    return {c: color_map[c] for c in codes if c in color_map}


def load_old_program_year() -> pd.DataFrame:
    if OLD_CSV.exists():
        return pd.read_csv(OLD_CSV)
    with zipfile.ZipFile(OLD_ZIP) as z, tempfile.TemporaryDirectory() as tmp:
        z.extract("nber_si_program_year_summary_2000_2019.csv", tmp)
        return pd.read_csv(Path(tmp) / "nber_si_program_year_summary_2000_2019.csv")


def load_combined() -> pd.DataFrame:
    old = load_old_program_year()
    new_path = DATA / "nber_si_program_year_summary_2020_2026.csv"
    if not new_path.exists():
        new_path = DATA / "nber_si_program_year_summary_2020_2025.csv"
    new = pd.read_csv(new_path)
    old2 = old.loc[
        old["organizer_data_available"] == 1,
        [
            "year", "program_code", "program_name", "papers_total",
            "papers_with_program_year_organizer", "program_year_organizer_share",
        ],
    ].copy()
    new2 = new.loc[
        new["agenda_captured"] == 1,
        [
            "year", "program_code", "program_name", "papers_total",
            "papers_with_program_year_organizer", "program_year_organizer_share",
        ],
    ].copy()
    df = pd.concat([old2, new2], ignore_index=True)
    df = df.dropna(subset=["program_year_organizer_share", "papers_total"])
    df["papers_total"] = df["papers_total"].astype(float)
    df["papers_with_program_year_organizer"] = df["papers_with_program_year_organizer"].astype(float)
    df["share"] = df["program_year_organizer_share"].astype(float)
    return df


def weighted_average_by_year(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("year", as_index=False).agg(
        papers_total=("papers_total", "sum"),
        papers_with_organizer=("papers_with_program_year_organizer", "sum"),
        n_programs=("program_code", "nunique"),
    )
    g["share"] = g["papers_with_organizer"] / g["papers_total"]
    return g


def size_scale(n: float, nmin: float, nmax: float) -> tuple[float, float]:
    t = np.sqrt((n - nmin) / (nmax - nmin + 1e-9))
    return 0.5 + 3.5 * t, 3.5 + 10.0 * t


def draw_sized_series(ax, sub: pd.DataFrame, color: str, nmin: float, nmax: float, z: int = 3, alpha: float = 0.9) -> None:
    sub = sub.sort_values("year")
    years = sub["year"].to_numpy()
    shares = sub["share"].to_numpy()
    papers = sub["papers_total"].to_numpy()
    for i in range(len(sub) - 1):
        lw, _ = size_scale(0.5 * (papers[i] + papers[i + 1]), nmin, nmax)
        ax.plot(
            years[i:i + 2], shares[i:i + 2],
            color=color, linewidth=lw, solid_capstyle="round",
            alpha=alpha, zorder=z,
        )
    for y, s, n in zip(years, shares, papers):
        _, ms = size_scale(n, nmin, nmax)
        ax.plot(
            y, s, marker="o", markersize=ms, color=color,
            markeredgecolor="white", markeredgewidth=0.45,
            linestyle="None", alpha=min(alpha + 0.05, 1.0), zorder=z + 1,
        )


def draw_weighted_average(ax, avg: pd.DataFrame, z: int = 10) -> None:
    """Paper-weighted annual average: prominent series on top."""
    avg = avg.sort_values("year")
    ax.plot(
        avg["year"], avg["share"],
        color=AVG_COLOR, linewidth=3.2, solid_capstyle="round",
        zorder=z, label="Paper-weighted average",
    )
    # Size average markers by total papers that year (relative within avg)
    nmin, nmax = avg["papers_total"].min(), avg["papers_total"].max()
    for _, row in avg.iterrows():
        t = np.sqrt((row["papers_total"] - nmin) / (nmax - nmin + 1e-9))
        ms = 6.5 + 5.0 * t
        ax.plot(
            row["year"], row["share"],
            marker="o", markersize=ms, color=AVG_COLOR,
            markeredgecolor="white", markeredgewidth=0.7,
            linestyle="None", zorder=z + 1,
        )


def style_axes(ax, title: str, subtitle: str, ymax: float = 0.42) -> None:
    ax.set_ylim(-0.01, ymax)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0, decimals=0))
    ax.set_ylabel("Share of papers with a program-year organizer as author")
    ax.set_title(title, loc="left", pad=14, fontweight="semibold")
    ax.text(0, 1.015, subtitle, transform=ax.transAxes, fontsize=9, color="#444444")
    ax.axhline(0, color="#333333", linewidth=0.6, zorder=0)
    ax.grid(axis="y", color="#EEEEEE", linewidth=0.8, zorder=0)


def classify_low_programs(
    df: pd.DataFrame,
    threshold: float = 0.05,
    nearly_always: float = 0.80,
) -> tuple[list[str], list[str], pd.DataFrame]:
    """Programs with share < threshold in >= nearly_always of years are 'low' (not plotted)."""
    g = (
        df.groupby("program_code", as_index=False)
        .agg(
            papers=("papers_total", "sum"),
            years=("year", "nunique"),
            mean_share=("share", "mean"),
            max_share=("share", "max"),
            pct_below=("share", lambda s: float((s < threshold).mean())),
            name=("program_name", "last"),
        )
        .sort_values(["papers", "program_code"], ascending=[False, True])
    )
    g["is_low"] = g["pct_below"] >= nearly_always
    keep = g.loc[~g["is_low"], "program_code"].tolist()
    low = g.loc[g["is_low"], "program_code"].tolist()
    return keep, low, g


def short_label(code: str, names: dict[str, str], maxlen: int = 42) -> str:
    label = f"{code}  {names.get(code, '')}"
    return label if len(label) <= maxlen else label[: maxlen - 3] + "..."


def three_year_program_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Centered 3-year paper-weighted averages by program.

    For year t: sum(org papers in {t-1,t,t+1}) / sum(papers in window).
    Edges use the available 1–2 years.
    """
    rows = []
    for code, g in df.groupby("program_code"):
        g = g.sort_values("year").set_index("year")
        years = g.index.to_numpy()
        name = g["program_name"].iloc[-1]
        for t in years:
            window = [y for y in (t - 1, t, t + 1) if y in g.index]
            papers = float(g.loc[window, "papers_total"].sum())
            org_papers = float(g.loc[window, "papers_with_program_year_organizer"].sum())
            if papers <= 0:
                continue
            rows.append({
                "year": int(t),
                "program_code": code,
                "program_name": name,
                "papers_total": papers,
                "papers_with_program_year_organizer": org_papers,
                "share": org_papers / papers,
                "n_years_in_window": len(window),
            })
    return pd.DataFrame(rows)


def three_year_overall_average(df: pd.DataFrame) -> pd.DataFrame:
    """Centered 3-year paper-weighted average across all programs."""
    annual = weighted_average_by_year(df).set_index("year")
    rows = []
    years = annual.index.to_numpy()
    for t in years:
        window = [y for y in (t - 1, t, t + 1) if y in annual.index]
        papers = float(annual.loc[window, "papers_total"].sum())
        org_papers = float(annual.loc[window, "papers_with_organizer"].sum())
        rows.append({
            "year": int(t),
            "papers_total": papers,
            "papers_with_organizer": org_papers,
            "n_programs": float(annual.loc[window, "n_programs"].mean()),
            "share": org_papers / papers if papers else 0.0,
            "n_years_in_window": len(window),
        })
    return pd.DataFrame(rows)


def make_filtered_figure(
    df: pd.DataFrame,
    avg: pd.DataFrame,
    names: dict[str, str],
    color_map: dict[str, str],
    *,
    year_min: int,
    year_max: int,
    out_stem: str,
    title: str,
    max_legend: int = 14,
) -> None:
    """Plot programs not nearly-always below 5%; readable scale; no omitted list in legend."""
    sub = df[df["year"].between(year_min, year_max)].copy()
    avg_sub = weighted_average_by_year(sub)
    keep, low, summary = classify_low_programs(sub)
    names_local = {
        **names,
        **summary.set_index("program_code")["name"].to_dict(),
    }

    keep_ordered = (
        summary[summary["program_code"].isin(keep)]
        .sort_values("papers", ascending=False)["program_code"]
        .tolist()
    )
    # Among programs that pass the filter, plot only the largest for readability
    plot_codes = keep_ordered[:max_legend]
    colors = colors_for(plot_codes, color_map)

    plotted = sub[sub["program_code"].isin(plot_codes)]
    nmin = float(plotted["papers_total"].min())
    nmax = float(plotted["papers_total"].max())

    # Data-driven y-scale with modest headroom (avoid empty upper half)
    y_hi = float(max(plotted["share"].max(), avg_sub["share"].max()))
    ymax = min(0.36, max(0.15, y_hi * 1.08 + 0.015))

    fig, ax = plt.subplots(figsize=(11.2, 5.8))

    for code in plot_codes:
        draw_sized_series(
            ax, sub[sub["program_code"] == code], colors[code], nmin, nmax, z=4, alpha=0.88
        )

    # Annotate a few high recent points only
    recent = plotted[plotted["year"] == year_max].sort_values("share", ascending=False)
    for _, row in recent.head(5).iterrows():
        code = row["program_code"]
        ax.annotate(
            code,
            (row["year"], row["share"]),
            textcoords="offset points",
            xytext=(6, 2),
            fontsize=8,
            color=colors[code],
            fontweight="semibold",
        )

    draw_weighted_average(ax, avg_sub, z=12)
    last = avg_sub.sort_values("year").iloc[-1]
    ax.annotate(
        f"Avg {last['share']:.1%}",
        (last["year"], last["share"]),
        textcoords="offset points",
        xytext=(8, 8),
        fontsize=9,
        fontweight="semibold",
        color=AVG_COLOR,
    )

    ax.set_xlim(year_min - 0.35, year_max + 0.65)
    ax.set_ylim(0.0, ymax)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0, decimals=0))
    ax.set_ylabel("Share of papers with a program-year organizer as author")
    ax.set_title(title, loc="left", pad=10, fontweight="semibold")
    n_omitted_filter = len(low)
    n_omitted_display = max(0, len(keep_ordered) - len(plot_codes))
    ax.text(
        0, 1.012,
        "Omits programs with share <5% in ≥80% of years"
        + (f" (and {n_omitted_display} smaller remaining programs for readability)" if n_omitted_display else "")
        + f". Black: paper-weighted average across all programs.",
        transform=ax.transAxes, fontsize=8.5, color="#444444",
    )
    ax.axhline(0, color="#333333", linewidth=0.6, zorder=0)
    ax.grid(axis="y", color="#EEEEEE", linewidth=0.8, zorder=0)

    handles: list[Line2D] = [
        Line2D(
            [0], [0],
            color=AVG_COLOR, marker="o", markersize=7, linewidth=3.0,
            label="Paper-weighted average",
        ),
    ]
    for code in plot_codes:
        handles.append(
            Line2D(
                [0], [0],
                color=colors[code], marker="o", markersize=5.5,
                linewidth=1.8, label=short_label(code, names_local),
            )
        )

    ax.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        frameon=False,
        fontsize=8,
        title="Series",
        title_fontsize=9,
        labelspacing=0.35,
        handlelength=1.8,
        borderaxespad=0.0,
    )
    ax.text(
        0.0, -0.10,
        "Thicker line / larger point = more papers that year",
        transform=ax.transAxes, ha="left", fontsize=8, color="#555555",
    )

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / f"{out_stem}.png", bbox_inches="tight", facecolor="white", dpi=160)
    fig.savefig(OUT / f"{out_stem}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)

    summary.assign(
        plotted=lambda d: d["program_code"].isin(plot_codes),
        passes_filter=lambda d: ~d["is_low"],
    ).to_csv(OUT / f"{out_stem}_program_filter.csv", index=False)
    print(
        f"wrote {out_stem}: plotted {len(plot_codes)}, "
        f"filter-omitted {n_omitted_filter}, display-omitted {n_omitted_display}, ymax={ymax:.2f}"
    )


def make_filtered_3yr_figure(
    df: pd.DataFrame,
    names: dict[str, str],
    color_map: dict[str, str],
    *,
    year_min: int,
    year_max: int,
    out_stem: str,
    title: str,
    max_legend: int = 14,
) -> None:
    """Like the filtered figure, but series are centered 3-year paper-weighted averages."""
    sub = df[df["year"].between(year_min, year_max)].copy()
    keep, low, summary = classify_low_programs(sub)
    names_local = {
        **names,
        **summary.set_index("program_code")["name"].to_dict(),
    }

    keep_ordered = (
        summary[summary["program_code"].isin(keep)]
        .sort_values("papers", ascending=False)["program_code"]
        .tolist()
    )
    plot_codes = keep_ordered[:max_legend]
    colors = colors_for(plot_codes, color_map)

    smooth = three_year_program_averages(sub)
    smooth = smooth[smooth["program_code"].isin(plot_codes)].copy()
    avg3 = three_year_overall_average(sub)

    # Save underlying series for reuse / QC
    smooth.to_csv(OUT / f"{out_stem}_series.csv", index=False)
    avg3.to_csv(OUT / f"{out_stem}_average.csv", index=False)

    nmin = float(smooth["papers_total"].min())
    nmax = float(smooth["papers_total"].max())
    y_hi = float(max(smooth["share"].max(), avg3["share"].max()))
    ymax = min(0.28, max(0.12, y_hi * 1.10 + 0.01))

    fig, ax = plt.subplots(figsize=(11.2, 5.8))
    for code in plot_codes:
        draw_sized_series(
            ax, smooth[smooth["program_code"] == code], colors[code], nmin, nmax, z=4, alpha=0.9
        )

    recent = smooth[smooth["year"] == year_max].sort_values("share", ascending=False)
    for _, row in recent.head(5).iterrows():
        code = row["program_code"]
        ax.annotate(
            code,
            (row["year"], row["share"]),
            textcoords="offset points",
            xytext=(6, 2),
            fontsize=8,
            color=colors[code],
            fontweight="semibold",
        )

    draw_weighted_average(ax, avg3, z=12)
    last = avg3.sort_values("year").iloc[-1]
    ax.annotate(
        f"Avg {last['share']:.1%}",
        (last["year"], last["share"]),
        textcoords="offset points",
        xytext=(8, 8),
        fontsize=9,
        fontweight="semibold",
        color=AVG_COLOR,
    )

    ax.set_xlim(year_min - 0.35, year_max + 0.65)
    ax.set_ylim(0.0, ymax)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0, decimals=0))
    ax.set_ylabel("3-year avg share with a program-year organizer as author")
    ax.set_title(title, loc="left", pad=10, fontweight="semibold")
    n_omitted_display = max(0, len(keep_ordered) - len(plot_codes))
    ax.text(
        0, 1.012,
        "Centered 3-year paper-weighted averages. "
        "Omits programs with annual share <5% in ≥80% of years"
        + (f" (and {n_omitted_display} smaller remaining programs)" if n_omitted_display else "")
        + ". Black: 3-year paper-weighted average across all programs.",
        transform=ax.transAxes, fontsize=8.5, color="#444444",
    )
    ax.axhline(0, color="#333333", linewidth=0.6, zorder=0)
    ax.grid(axis="y", color="#EEEEEE", linewidth=0.8, zorder=0)

    handles: list[Line2D] = [
        Line2D(
            [0], [0],
            color=AVG_COLOR, marker="o", markersize=7, linewidth=3.0,
            label="Paper-weighted average (3-year)",
        ),
    ]
    for code in plot_codes:
        handles.append(
            Line2D(
                [0], [0],
                color=colors[code], marker="o", markersize=5.5,
                linewidth=1.8, label=short_label(code, names_local),
            )
        )
    ax.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        frameon=False,
        fontsize=8,
        title="Series",
        title_fontsize=9,
        labelspacing=0.35,
        handlelength=1.8,
        borderaxespad=0.0,
    )
    ax.text(
        0.0, -0.10,
        "Point size scales with papers in the 3-year window",
        transform=ax.transAxes, ha="left", fontsize=8, color="#555555",
    )

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / f"{out_stem}.png", bbox_inches="tight", facecolor="white", dpi=160)
    fig.savefig(OUT / f"{out_stem}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {out_stem}: plotted {len(plot_codes)}, ymax={ymax:.2f}")


def rank_large_programs(
    d: pd.DataFrame,
    *,
    min_papers: int,
    min_years: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (top5, eligible) among large programs by paper-weighted share."""
    g = d.groupby("program_code").agg(
        papers=("papers_total", "sum"),
        years=("year", "nunique"),
        org=("papers_with_program_year_organizer", "sum"),
        name=("program_name", "last"),
        mean_py=("papers_total", "mean"),
    )
    g["mean_w"] = g["org"] / g["papers"]
    eligible = g[(g["papers"] >= min_papers) & (g["years"] >= min_years)].copy()
    top = eligible.sort_values("mean_w", ascending=False).head(5)
    return top, eligible


def make_top5_figures(
    df: pd.DataFrame,
    names: dict[str, str],
    color_map: dict[str, str],
) -> pd.DataFrame:
    """Annual + 3yr top-5 among large programs; uses global program colors."""
    rules = {
        "2000-2026": dict(year_min=2000, year_max=2026, min_papers=150, min_years=8),
        "2020-2026": dict(year_min=2020, year_max=2026, min_papers=70, min_years=5),
    }
    rows: list[dict] = []

    for window, rule in rules.items():
        d = df[df["year"].between(rule["year_min"], rule["year_max"])].copy()
        top, eligible = rank_large_programs(
            d, min_papers=rule["min_papers"], min_years=rule["min_years"]
        )
        codes = top.index.tolist()
        colors = colors_for(codes, color_map)
        avg = weighted_average_by_year(d)
        note = (
            f"Large programs: ≥{rule['min_papers']} papers and ≥{rule['min_years']} years "
            f"(n={len(eligible)} eligible). Top 5 by paper-weighted organizer share. "
            f"Program colors are stable across figures. Grey points: other programs."
        )
        stem = f"nber_si_top5_programs_{window.replace('-', '_')}"

        # Annual
        nmin = float(d["papers_total"].min())
        nmax = float(d["papers_total"].max())
        ymax = max(0.20, float(d[d["program_code"].isin(codes)]["share"].max()) * 1.12)
        fig, ax = plt.subplots(figsize=(11.0, 6.4))
        bg = d[~d["program_code"].isin(codes)]
        ax.scatter(
            bg["year"], bg["share"],
            s=8 + 40 * np.sqrt((bg["papers_total"] - nmin) / (nmax - nmin + 1e-9)),
            c=BG_COLOR, alpha=0.22, linewidths=0, zorder=1,
        )
        for code in codes:
            draw_sized_series(
                ax, d[d["program_code"] == code], colors[code], nmin, nmax, z=4, alpha=0.85
            )
            lastp = d[d["program_code"] == code].sort_values("year").iloc[-1]
            ax.annotate(
                code, (lastp["year"], lastp["share"]),
                textcoords="offset points", xytext=(6, 0),
                fontsize=9, color=colors[code], fontweight="semibold",
            )
        draw_weighted_average(ax, avg, z=12)
        ax.set_xlim(rule["year_min"] - 0.5, rule["year_max"] + 0.55)
        ax.set_ylim(0, ymax)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.set_title(
            f"Top 5 large programs by organizer-authored share, {window}",
            fontsize=13, pad=10,
        )
        ax.set_ylabel("Share of papers with a program-year organizer as author")
        ax.text(0.0, -0.08, note, transform=ax.transAxes, ha="left", fontsize=8, color="#555555")
        handles = [
            Line2D(
                [0], [0], color=AVG_COLOR, marker="o", markersize=7, linewidth=3.0,
                label="Paper-weighted average (all programs)",
            ),
        ]
        for code in codes:
            handles.append(
                Line2D(
                    [0], [0], color=colors[code], marker="o", markersize=6,
                    linewidth=2.0, label=short_label(code, names),
                )
            )
        ax.legend(
            handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.02),
            frameon=False, fontsize=8, title="Top 5 large programs", title_fontsize=9,
        )
        fig.tight_layout()
        fig.savefig(OUT / f"{stem}.png", bbox_inches="tight", facecolor="white", dpi=160)
        fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight", facecolor="white")
        plt.close(fig)

        # 3-year
        smooth = three_year_program_averages(d)
        smooth = smooth[smooth["program_code"].isin(codes)].copy()
        avg_s = three_year_overall_average(d)
        nmin_s = float(smooth["papers_total"].min())
        nmax_s = float(smooth["papers_total"].max())
        ymax_s = max(0.15, float(smooth["share"].max()) * 1.15)
        fig3, ax3 = plt.subplots(figsize=(11.0, 6.4))
        for code in codes:
            g = smooth[smooth["program_code"] == code].sort_values("year")
            if g.empty:
                continue
            draw_sized_series(ax3, g, colors[code], nmin_s, nmax_s, z=4, alpha=0.9)
            lastp = g.iloc[-1]
            ax3.annotate(
                code, (lastp["year"], lastp["share"]),
                textcoords="offset points", xytext=(6, 0),
                fontsize=9, color=colors[code], fontweight="semibold",
            )
        draw_weighted_average(ax3, avg_s, z=12)
        ax3.set_xlim(rule["year_min"] - 0.5, rule["year_max"] + 0.55)
        ax3.set_ylim(0, ymax_s)
        ax3.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax3.set_title(
            f"Top 5 large programs (3-year averages), {window}",
            fontsize=13, pad=10,
        )
        ax3.set_ylabel("3-year paper-weighted organizer-authored share")
        ax3.text(
            0.0, -0.08,
            note + " Shares are centered 3-year paper-weighted averages.",
            transform=ax3.transAxes, ha="left", fontsize=8, color="#555555",
        )
        handles3 = [
            Line2D(
                [0], [0], color=AVG_COLOR, marker="o", markersize=7, linewidth=3.0,
                label="Paper-weighted average (all programs)",
            ),
        ]
        for code in codes:
            handles3.append(
                Line2D(
                    [0], [0], color=colors[code], marker="o", markersize=6,
                    linewidth=2.0, label=short_label(code, names),
                )
            )
        ax3.legend(
            handles=handles3, loc="upper left", bbox_to_anchor=(1.01, 1.02),
            frameon=False, fontsize=8, title="Top 5 large programs", title_fontsize=9,
        )
        fig3.tight_layout()
        fig3.savefig(OUT / f"{stem}_3yr.png", bbox_inches="tight", facecolor="white", dpi=160)
        fig3.savefig(OUT / f"{stem}_3yr.pdf", bbox_inches="tight", facecolor="white")
        plt.close(fig3)
        print(f"wrote {stem} (+ _3yr)")

        for code, r in top.iterrows():
            rows.append({
                "program_code": code,
                "papers": r["papers"],
                "years": r["years"],
                "org": r["org"],
                "name": r["name"],
                "mean_w": r["mean_w"],
                "mean_papers_per_year": r["mean_py"],
                "window": window,
                "min_papers": rule["min_papers"],
                "min_years": rule["min_years"],
                "n_eligible_large": len(eligible),
                "color": color_map[code],
            })

    summary = pd.DataFrame(rows)
    summary.to_csv(OUT / "nber_si_top5_programs_summary.csv", index=False)
    return summary


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_combined()
    avg = weighted_average_by_year(df)
    avg.to_csv(OUT / "nber_si_weighted_average_by_year.csv", index=False)

    names = (
        df.sort_values("year")
        .groupby("program_code", as_index=False)
        .tail(1)
        .set_index("program_code")["program_name"]
        .to_dict()
    )
    color_map = build_program_color_map(
        df["program_code"],
        papers_by_code=df.groupby("program_code")["papers_total"].sum().to_dict(),
    )
    pd.DataFrame(
        [
            {"program_code": c, "program_name": names.get(c, ""), "color": color_map[c]}
            for c in sorted(color_map)
        ]
    ).to_csv(OUT / "nber_si_program_colors.csv", index=False)

    nmin, nmax = df["papers_total"].min(), df["papers_total"].max()

    prog = (
        df.groupby("program_code", as_index=False)
        .agg(
            papers=("papers_total", "sum"),
            years=("year", "nunique"),
            mean_share=("share", "mean"),
        )
        .sort_values("papers", ascending=False)
    )
    focus_codes = prog.query("papers >= 150 and years >= 8").head(14)["program_code"].tolist()
    for extra in ["PE", "REAL", "DEV", "URB"]:
        if extra in set(prog["program_code"]) and extra not in focus_codes:
            focus_codes.append(extra)
    focus_codes = focus_codes[:16]
    colors = colors_for(focus_codes, color_map)

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.labelsize": 11,
        "axes.titlesize": 13,
        "figure.dpi": 150,
    })

    # --- Figure 1: 2000-2026 ---
    fig, ax = plt.subplots(figsize=(11.4, 6.8))
    bg = df[~df["program_code"].isin(focus_codes)]
    ax.scatter(
        bg["year"], bg["share"],
        s=10 + 55 * np.sqrt((bg["papers_total"] - nmin) / (nmax - nmin + 1e-9)),
        c=BG_COLOR, alpha=0.18, linewidths=0, zorder=1,
    )
    for code in focus_codes:
        draw_sized_series(
            ax, df[df["program_code"] == code], colors[code], nmin, nmax, z=3, alpha=0.55
        )
    draw_weighted_average(ax, avg, z=12)

    ax.set_xlim(1999.5, 2026.5)
    style_axes(
        ax,
        "NBER Summer Institute: organizer-authored papers by program, 2000–2026",
        "Colored series: large programs (line/point size = papers that year). "
        "Black: paper-weighted average across all programs. Grey points: other programs.",
        ymax=0.45,
    )
    last = avg.sort_values("year").iloc[-1]
    ax.annotate(
        f"Avg {last['share']:.1%}",
        (last["year"], last["share"]),
        textcoords="offset points", xytext=(8, 6),
        fontsize=9, fontweight="semibold", color=AVG_COLOR,
    )

    handles = [
        Line2D([0], [0], color=AVG_COLOR, marker="o", markersize=7, linewidth=3.0,
               label="Paper-weighted average"),
    ]
    for code in focus_codes:
        handles.append(Line2D(
            [0], [0], color=colors[code], marker="o", markersize=5.5,
            linewidth=1.8, alpha=0.8, label=short_label(code, names),
        ))
    ax.legend(
        handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.02),
        frameon=False, fontsize=8, title="Series", title_fontsize=9,
    )
    ax.text(
        0.99, -0.07,
        "Thicker program line / larger point = more papers that year. "
        "Program colors are stable across figures.",
        transform=ax.transAxes, ha="right", fontsize=8, color="#555555",
    )
    fig.tight_layout()
    fig.savefig(OUT / "nber_si_organizer_share_by_program_year.png", bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / "nber_si_organizer_share_by_program_year.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # --- Figure 2: 2020-2026 ---
    d2 = df[df["year"].between(2020, 2026)].copy()
    avg2 = weighted_average_by_year(d2)
    nmin2, nmax2 = d2["papers_total"].min(), d2["papers_total"].max()
    tot2 = (
        d2.groupby("program_code")
        .agg(papers=("papers_total", "sum"), mean_share=("share", "mean"))
        .sort_values("papers", ascending=False)
    )
    top2 = tot2.head(12).index.tolist()
    for extra in ["PE", "REAL"]:
        if extra in tot2.index and extra not in top2:
            top2.append(extra)
    colors2 = colors_for(top2, color_map)

    fig2, ax2 = plt.subplots(figsize=(11.2, 6.6))
    for code, sub in d2.groupby("program_code"):
        if code in top2:
            continue
        draw_sized_series(ax2, sub, BG_COLOR, nmin2, nmax2, z=2, alpha=0.35)
    for code in top2:
        draw_sized_series(ax2, d2[d2["program_code"] == code], colors2[code], nmin2, nmax2, z=4, alpha=0.7)
        lastp = d2[d2["program_code"] == code].sort_values("year").iloc[-1]
        ax2.annotate(
            code, (lastp["year"], lastp["share"]),
            textcoords="offset points", xytext=(6, 0),
            fontsize=8, color=colors2[code], fontweight="semibold",
        )
    draw_weighted_average(ax2, avg2, z=12)
    last2 = avg2.sort_values("year").iloc[-1]
    ax2.annotate(
        f"Avg {last2['share']:.1%}",
        (last2["year"], last2["share"]),
        textcoords="offset points", xytext=(8, 8),
        fontsize=9, fontweight="semibold", color=AVG_COLOR,
    )

    ax2.set_xlim(2019.7, 2026.55)
    style_axes(
        ax2,
        "Organizer-authored share by program, 2020–2026",
        "Each series is a program (size = papers that year). "
        "Black: paper-weighted average across all captured programs.",
        ymax=0.45,
    )

    handles2 = [
        Line2D([0], [0], color=AVG_COLOR, marker="o", markersize=7, linewidth=3.0,
               label="Paper-weighted average"),
    ]
    for code in top2:
        handles2.append(Line2D(
            [0], [0], color=colors2[code], marker="o", markersize=5.5,
            linewidth=1.8, label=short_label(code, names),
        ))
    ax2.legend(
        handles=handles2, loc="upper left", bbox_to_anchor=(1.01, 1.02),
        frameon=False, fontsize=8, title="Series", title_fontsize=9,
    )
    ax2.text(
        0.99, -0.07,
        "Thicker program line / larger point = more papers that year. "
        "Program colors are stable across figures.",
        transform=ax2.transAxes, ha="right", fontsize=8, color="#555555",
    )
    fig2.tight_layout()
    fig2.savefig(OUT / "nber_si_organizer_share_by_program_2020_2026.png", bbox_inches="tight", facecolor="white")
    fig2.savefig(OUT / "nber_si_organizer_share_by_program_2020_2026.pdf", bbox_inches="tight", facecolor="white")
    fig2.savefig(OUT / "nber_si_organizer_share_by_program_2020_2025.png", bbox_inches="tight", facecolor="white")
    fig2.savefig(OUT / "nber_si_organizer_share_by_program_2020_2025.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig2)

    # --- Filtered figures ---
    make_filtered_figure(
        df, avg, names, color_map,
        year_min=2000, year_max=2026,
        out_stem="nber_si_organizer_share_by_program_year_filtered",
        title="NBER Summer Institute: organizer-authored papers by program, 2000–2026",
    )
    make_filtered_figure(
        df, avg, names, color_map,
        year_min=2020, year_max=2026,
        out_stem="nber_si_organizer_share_by_program_2020_2026_filtered",
        title="Organizer-authored share by program, 2020–2026",
    )

    # --- 3-year average versions ---
    make_filtered_3yr_figure(
        df, names, color_map,
        year_min=2000, year_max=2026,
        out_stem="nber_si_organizer_share_by_program_year_3yr",
        title="NBER Summer Institute: 3-year average organizer-authored share by program, 2000–2026",
    )
    make_filtered_3yr_figure(
        df, names, color_map,
        year_min=2020, year_max=2026,
        out_stem="nber_si_organizer_share_by_program_2020_2026_3yr",
        title="Organizer-authored share by program, 3-year averages, 2020–2026",
    )

    # --- Top 5 large programs ---
    make_top5_figures(df, names, color_map)

    print("Weighted average by year:")
    print(avg.to_string(index=False))
    print("wrote figures to", OUT)
    print("program color map:", OUT / "nber_si_program_colors.csv")


if __name__ == "__main__":
    main()

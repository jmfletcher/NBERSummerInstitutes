#!/usr/bin/env python3
"""Annual organizer-coauthorship rates by NBER SI program; series sized by papers.

Adds a paper-weighted average series (total organizer-authored papers /
total papers across programs in that year).
"""

from __future__ import annotations

import zipfile
import tempfile
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

PALETTE = [
    "#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7",
    "#56B4E9", "#000000", "#F0E442", "#999999", "#44AA99",
    "#882255", "#117733", "#332288", "#88CCEE", "#AA4499",
]
AVG_COLOR = "#1A1A1A"


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
    colors = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(focus_codes)}

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
        c="#B8B8B8", alpha=0.18, linewidths=0, zorder=1,
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
    # Annotate latest average
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
        label = f"{code}  {names.get(code, '')}"
        if len(label) > 44:
            label = label[:42] + "..."
        handles.append(Line2D(
            [0], [0], color=colors[code], marker="o", markersize=5.5,
            linewidth=1.8, alpha=0.8, label=label,
        ))
    ax.legend(
        handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.02),
        frameon=False, fontsize=8, title="Series", title_fontsize=9,
    )
    ax.text(
        0.99, -0.07,
        "Thicker program line / larger point = more papers that year",
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
    colors2 = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(top2)}

    fig2, ax2 = plt.subplots(figsize=(11.2, 6.6))
    for code, sub in d2.groupby("program_code"):
        if code in top2:
            continue
        draw_sized_series(ax2, sub, "#C8C8C8", nmin2, nmax2, z=2, alpha=0.35)
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
        label = f"{code}  {names.get(code, '')}"
        if len(label) > 44:
            label = label[:42] + "..."
        handles2.append(Line2D(
            [0], [0], color=colors2[code], marker="o", markersize=5.5,
            linewidth=1.8, label=label,
        ))
    ax2.legend(
        handles=handles2, loc="upper left", bbox_to_anchor=(1.01, 1.02),
        frameon=False, fontsize=8, title="Series", title_fontsize=9,
    )
    ax2.text(
        0.99, -0.07,
        "Thicker program line / larger point = more papers that year",
        transform=ax2.transAxes, ha="right", fontsize=8, color="#555555",
    )
    fig2.tight_layout()
    fig2.savefig(OUT / "nber_si_organizer_share_by_program_2020_2026.png", bbox_inches="tight", facecolor="white")
    fig2.savefig(OUT / "nber_si_organizer_share_by_program_2020_2026.pdf", bbox_inches="tight", facecolor="white")
    # keep old filename as alias for recent window
    fig2.savefig(OUT / "nber_si_organizer_share_by_program_2020_2025.png", bbox_inches="tight", facecolor="white")
    fig2.savefig(OUT / "nber_si_organizer_share_by_program_2020_2025.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig2)

    print("Weighted average by year:")
    print(avg.to_string(index=False))
    print("wrote figures to", OUT)


if __name__ == "__main__":
    main()

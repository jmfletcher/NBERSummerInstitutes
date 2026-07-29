# NBER SI organizer coauthorship (Substack)

Short descriptive post: how often Summer Institute papers list a program-year organizer as an author. **Posted on Substack** (draft text kept in `NBER_SI_Organizer_Coauthors_Substack_Draft.md`).

## Folder contents

| Path | What it is |
|------|------------|
| `NBER_SI_Organizer_Coauthors_Substack_Draft.md` | Posted Substack text (local copy) |
| `build_nber_si_2020_2025.py` | Scrape + measure pipeline for 2020–2026 |
| `data/` | Output CSVs, QC JSON, conf_id overrides |
| `cache/agendas/` | Cached printable HTML (not in git) |
| `figures/` | Annual-by-program charts + weighted average |

## Headline results

| Window | Papers | Organizer-coauthored | Share |
|--------|--------|----------------------|-------|
| 2000–2019 (Rose archive) | 9,601 | 364 | 3.79% |
| 2020–2026 (NBER printable agendas) | 4,322 | 105 | 2.43% |
| Pooled 2000–2026 | 13,923 | 469 | 3.37% |

2020–2026 coverage: **339 / 342** in-scope program-years (missing: CRIW Pre-Conference 2023–2025).

2026 alone (agendas as posted): **27 / 645 = 4.19%**.

## Measure

Distinct research papers with ≥1 program-year organizer among authors ÷ distinct included papers in that program-year.

**Paper-weighted average (figures):** each year, sum organizer-authored papers across programs ÷ sum of all papers that year (large programs count more).

## Figures

Program colors are stable across all charts (`figures/nber_si_program_colors.csv`).

| File | What it shows |
|------|----------------|
| `figures/nber_si_organizer_share_by_program_year.png` | 2000–2026; size ∝ papers; **black = paper-weighted average** |
| `figures/nber_si_organizer_share_by_program_2020_2026.png` | 2020–2026 only |
| `figures/nber_si_organizer_share_by_program_*_filtered.png` | Omits programs with share &lt;5% in ≥80% of years |
| `figures/nber_si_organizer_share_by_program_*_3yr.png` | Centered 3-year paper-weighted averages |
| `figures/nber_si_top5_programs_*.png` | Top 5 **large** programs by paper-weighted share |
| `figures/nber_si_health_programs_organizer_share*.png` | HE / HC / EH (annual and 3-year) |
| `figures/nber_si_weighted_average_by_year.csv` | Annual weighted-average series |

Filtered/3-year legends force-include **PE** (and a few other priority programs) so mid-sized high-share series are not dropped by the paper-count cap.
```bash
python3 figures/plot_organizer_share_by_program.py
```

## Program-year regressions

| Spec | Model |
|------|--------|
| 1 | `share ~ program FE + year FE` |
| 2 | Spec 1 + program-specific linear time trends (`program × (year−2000)`) |

OLS and paper-weighted WLS; SEs clustered by program. Outputs: `data/nber_si_reg_*.csv`.
## Rebuild

```bash
python3 build_nber_si_2020_2025.py
```

Uses `data/nber_si_confid_overrides_2020_2026.json` for nonstandard conference IDs.

## Spot checks & organizer frequency

See `data/SPOT_CHECKS_AND_ORGANIZER_FREQUENCY.md`.

| File | What it is |
|------|------------|
| `data/nber_si_organizer_own_paper_frequency_2020_2026.csv` | All organizers 2020–2026: years as organizer, own-paper counts |
| `data/nber_si_organizers_with_own_papers_2020_2026.md` | Readable table of organizers with ≥1 own paper |
| `data/nber_si_organizer_own_papers_detail_2020_2026.csv` | Paper titles behind those counts |
| `data/nber_si_organizer_own_paper_frequency_2000_2019.csv` | Same for 2000–2019 Rose archive |

## Sources

- 2000–2019: https://github.com/Michael-E-Rose/NBERSummerInstitutes
- 2020–2026 agendas: `https://conference.nber.org/agenda/simple_printable?conf_id=...`
- Organizer roster seed: ChatGPT working coverage file in Downloads

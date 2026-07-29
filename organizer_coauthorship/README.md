# Organizer coauthorship at NBER Summer Institute

Extension of this repository measuring how often Summer Institute papers list a **program-year organizer** as an author.

Built on top of the Rose–Opolot–Georg presentation archive (2000–2019 in `../output/`) plus a scrape of NBER printable agendas for **2020–2026**.

## Headline results

| Window | Papers | Organizer-coauthored | Share |
|--------|--------|----------------------|-------|
| 2000–2019 (this repo’s archive) | 9,601 | 364 | 3.79% |
| 2020–2026 (printable agendas) | 4,322 | 105 | 2.43% |
| Pooled 2000–2026 | 13,923 | 469 | 3.37% |

2020–2026 coverage: **339 / 342** in-scope program-years (missing: CRIW Pre-Conference 2023–2025).

## Measure

Distinct research papers with ≥1 program-year organizer among authors ÷ distinct included papers in that program-year.

**Paper-weighted average:** each year, sum organizer-authored papers across programs ÷ sum of all papers that year.

## Contents

| Path | What it is |
|------|------------|
| `build_nber_si_2020_2025.py` | Scrape + measure pipeline for 2020–2026 |
| `data/` | Paper/author/organizer CSVs, QC, organizer frequency tables |
| `figures/` | Annual-by-program charts + weighted average |
| `NBER_SI_Organizer_Coauthors_Substack_Draft.md` | Short Substack draft |
| `data/SPOT_CHECKS_AND_ORGANIZER_FREQUENCY.md` | Live spot checks + organizer frequency notes |

## Rebuild 2020–2026

```bash
python3 build_nber_si_2020_2025.py
python3 figures/plot_organizer_share_by_program.py
```

Requires `requests`, `beautifulsoup4`, `lxml`, `pandas`, `matplotlib`. Uses `data/nber_si_confid_overrides_2020_2026.json` for nonstandard conference IDs. Agenda HTML is cached under `cache/agendas/` (gitignored).

Organizer roster seed for 2020–2026 program lists: published NBER SI pages / coverage file used in construction.

## Citation

Please continue to cite the underlying archive:

Rose, ME, DC Opolot and C-P Georg, “Discussants”, *Research Policy* 51(10), 104587, December 2022.

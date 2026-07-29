# Spot checks and organizer frequency

## Spot checks against original sources (2026-07-29)

### 2020–2026 printable agendas (live `conference.nber.org`)
Twelve program-years re-fetched and re-parsed independently. Paper counts and organizer-match counts matched our dataset exactly in all twelve cases:

| Year | Program | Live papers | Ours | Live matches | Ours | Share |
|------|---------|-------------|------|--------------|------|-------|
| 2020 | PE | 12 | 12 | 3 | 3 | 25.0% |
| 2020 | ME | 19 | 19 | 0 | 0 | 0% |
| 2020 | DAE | 24 | 24 | 0 | 0 | 0% |
| 2021 | PRIT | 37 | 37 | 1 | 1 | 2.7% |
| 2022 | URB | 28 | 28 | 0 | 0 | 0% |
| 2023 | EH | 14 | 14 | 1 | 1 | 7.1% |
| 2024 | URB | 26 | 26 | 0 | 0 | 0% |
| 2025 | LS | 27 | 27 | 2 | 2 | 7.4% |
| 2026 | PE | 11 | 11 | 1 | 1 | 9.1% |
| 2026 | REAL | 16 | 16 | 0 | 0 | 0% |
| 2026 | LS | 29 | 29 | 7 | 7 | 24.1% |
| 2026 | CRI | 12 | 12 | 2 | 2 | 16.7% |

Organizer names on the live pages also matched the roster for these cases.

### 2000–2019 Rose archive
Recomputed from `nber_si_papers_2000_2019.csv` and compared to year/program summaries; also pulled the live GitHub source `by_title.csv` (HTTP 200).

- Overall: **364 / 9,601 = 3.791%** (matches README/QC)
- 2019: **15 / 605 = 2.479%** (matches year summary)
- High-share program-years (2006 EFMPL 4/18; 2002 EFDIS 3/15; 2005 EFACR 3/15) recompute exactly

## Organizer frequency files

- `nber_si_organizer_own_paper_frequency_2020_2026.csv` — all organizers; years as organizer; own-paper counts
- `nber_si_organizer_own_papers_detail_2020_2026.csv` — paper titles behind the counts
- `nber_si_organizer_own_paper_frequency_2000_2019.csv` — same for Rose archive window

### Definitions (2020–2026)
- **n_organizer_program_years**: distinct program-year slots as listed organizer
- **years_as_organizer**: calendar years appearing in those slots
- **n_own_papers_on_organized_programs**: distinct papers on a program-year they organized where they are an author
- **n_organizer_program_years_with_own_paper**: slots with ≥1 such paper
- **share_of_organizer_program_years_with_own_paper**: that count ÷ organizer-program-years

### Headline (2020–2026)
- Distinct organizers: **378**
- With ≥1 own paper on an organized program: **77**
- Sum of own papers across organizers: **108** (can exceed paper-level 105 when co-organizers share a paper? wait - each paper attributed to matched organizer; a paper with one organizer-author counts once per such organizer)

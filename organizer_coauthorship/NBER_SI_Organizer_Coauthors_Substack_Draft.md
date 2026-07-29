# Do NBER Summer Institute organizers put their own papers on the program?

### Usually no. Labor Studies this year looks different. Public Economics has looked different for a while.

Peter Hull noticed that this year’s Labor Studies Summer Institute had a lot of organizer work on the program. Fair enough, if you were looking at that agenda.

The question I wanted was broader: how often do SI papers list a current program organizer as an author? Does it differ across programs? Does it change over time?

I thought this would be easy. It wasn’t.

Michael Rose and coauthors already have a public [NBER Summer Institutes archive](https://github.com/Michael-E-Rose/NBERSummerInstitutes) through 2019—agendas, authors, organizers. That got me most of the way. For 2020–2026 I needed NBER’s printable agendas. ChatGPT Pro chewed on that for hours and never finished. I ended up having Cursor pull and match the remaining years. Code, data, and figures are here: [jmfletcher/NBERSummerInstitutes](https://github.com/jmfletcher/NBERSummerInstitutes/tree/master/organizer_coauthorship).

---

## The measure

Take the organizers listed for a program-year. Count a research paper if one of those people is also an author. Divide by the number of research papers on the agenda.

Discussants don’t count. Panels and lectures don’t count. Each paper counts once.

This only catches **same organizer, same program, same year, on the author line.** It says nothing about how the paper got accepted. It misses students, frequent coauthors, same-department networks, and the rest of the soft stuff people actually care about when they worry about “who gets on.”

Some meetings are joint across programs, and then it is not obvious whose organizer list should count. A few conference IDs are messy. Treat program-year shares with some caution. The averages are still in the right ballpark.

---

## How often?

**2000–2019:** about **3.8%** of papers (364 of 9,601).

**2020–2026:** about **2.4%** of papers (105 of 4,322). I got 339 of 342 program-years; three CRIW pre-conferences are still missing.

Pool the whole 2000–2026 span and you are around **3–4%**—one paper in twenty-five to forty, depending on the cut. Weight by papers so large meetings count more, and most years sit in that range. The 2026 agendas, as posted, are about **4.2%**.

Most meetings have **zero** organizer-authored papers. In the recent window, only about one in five program-years has even one. The median is zero.

A high year is not the same thing as a high program.

---

## Labor Studies 2026

Labor 2026 is about **7 of 29 papers (~24%)** with a program-year organizer as an author. Relative to the SI average, that is high. Peter was looking at a real spike.

Across years, Labor is not special. Over 2000–2026, LS is about **3%**—near the average, and a bit below typical once you allow for program fixed effects. The 2026 bump is in the series. The long run is not.

**Conspicuous year. Ordinary program.**

---

## Public Economics

Among larger programs, **Public Economics** is the one that stays high.

Over 2000–2026, PE is around **10%**—double or triple a typical 3–5% rate. In a program-year regression with year fixed effects, PE is about **five percentage points** above the average program. That is a level, not one weird summer.

Real Estate, CRIW, and a few applied macro meetings also run high. Aging has been drifting up. Labor has too, recently. Still: for most programs this is uncommon. A few do it more. SI agendas are not mostly organizer papers.

---

## What I am not saying

A low rate has several readings. Organizers may have presented elsewhere. They may save slots for juniors. Submissions may just get screened out.

A positive rate is not automatic evidence of a problem. Organizers are active people in the field. Sometimes their paper belongs on the program.

I would not read the long series as “organizers load the agenda with their own work.” I also would not read it as a hard norm of zero.

The more interesting version—and harder—would match papers to organizers through departments, PhD lineages, and coauthor networks, not just same-year names on the byline. Someone else can do that.

---

## Figures

The GitHub folder has the full series, a filtered cut that drops programs that are almost always near zero, three-year averages, and top-5 charts among *large* programs (so a six-paper workshop cannot look like a structural fact). Program colors are the same across figures; the black line is the paper-weighted average.

**One paper in twenty-five to forty** has an organizer on the author list, depending on the years. Most meetings have none. Labor 2026 is a spike. Public Economics is the steadier high end.

What the rate *should* be is a different argument.

---

*2000–2019: [Rose archive](https://github.com/Michael-E-Rose/NBERSummerInstitutes). 2020–2026: NBER printable agendas (2026 as posted). Count: research papers with at least one program-year organizer among authors.*

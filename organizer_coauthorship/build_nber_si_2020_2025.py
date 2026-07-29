#!/usr/bin/env python3
"""Scrape NBER SI printable agendas 2020–2026 and measure organizer coauthorship.

Primary measure (aligned with 2000–2019 Rose archive build):
  share of distinct research papers in a program-year that list at least one
  person in the program-year organizer union among the authors.

Sources:
  Organizer roster: nber_si_program_year_coverage_2020_2026.csv (ChatGPT working file)
  Paper/author census: https://conference.nber.org/agenda/simple_printable?conf_id=SI{YY}{CODE}
"""

from __future__ import annotations

import csv
import difflib
import hashlib
import json
import re
import time
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
COVERAGE = Path("/Users/jmfletcher/Downloads/nber_si_program_year_coverage_2020_2026.csv")
OUT = ROOT / "data"
CACHE = ROOT / "cache" / "agendas"
OVERRIDES_PATH = OUT / "nber_si_confid_overrides_2020_2026.json"
if not OVERRIDES_PATH.exists():
    OVERRIDES_PATH = OUT / "nber_si_confid_overrides_2020_2025.json"

YEARS = range(2020, 2027)
BASE_PRINT = "https://conference.nber.org/agenda/simple_printable?conf_id="
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nber.org/",
}

PARTICLES = {"de", "del", "della", "di", "da", "dos", "du", "la", "le", "van", "von", "der", "den", "ter", "ten", "of"}
SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "phd"}
NICKNAME_GROUPS = [
    {"bob", "rob", "robert", "bobby"}, {"bill", "will", "william", "billy"}, {"jim", "james", "jimmy"},
    {"joe", "joey", "joseph"}, {"josh", "joshua"}, {"jon", "john", "johnny", "jonathan"}, {"pete", "peter"},
    {"dick", "rich", "rick", "richard"}, {"ed", "eddie", "edward"}, {"ted", "theodore", "edward"},
    {"tom", "thomas", "tommy"}, {"mike", "michael"}, {"steve", "steven", "stephen"},
    {"dan", "daniel", "danny"}, {"dave", "david"}, {"chris", "christopher", "christine"},
    {"kate", "katie", "katherine", "kathryn", "catherine", "cathy"}, {"judy", "judith"},
    {"liz", "beth", "elizabeth", "betsy"}, {"matt", "matthew"}, {"nick", "nicholas"},
    {"tony", "anthony"}, {"larry", "lawrence"}, {"greg", "gregory"}, {"jeff", "jeffrey"},
    {"andy", "andrew"}, {"alex", "alexander", "alexandra"}, {"ben", "benjamin"},
    {"sam", "samuel", "samantha"}, {"pat", "patrick", "patricia"}, {"ron", "ronald"},
    {"phil", "philip", "phillip"}, {"charlie", "charles"}, {"doug", "douglas"},
    {"ken", "kenneth"}, {"ray", "raymond"}, {"gerry", "gerald", "jerry"}, {"art", "arthur"},
    {"stan", "stanley"}, {"frank", "francis"}, {"jack", "john"}, {"sue", "susan"},
]
NICKNAME_CANON: dict[str, str] = {}
for group in NICKNAME_GROUPS:
    root = sorted(group)[0]
    for name in group:
        NICKNAME_CANON[name] = root

# Agenda italic notes that are not paper titles.
NON_PAPER_EM = {
    "this paper will not be livestreamed",
    "this session will not be livestreamed",
    "paper will not be livestreamed",
}


def clean_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\u00a0", " ")).strip()


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def normalize_text(s: str) -> str:
    s = strip_accents(s or "").lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return clean_space(s)


def name_tokens(name: str) -> list[str]:
    s = strip_accents(name or "").lower()
    s = s.replace("'", "").replace("’", "")
    s = re.sub(r"[^a-z0-9-]+", " ", s)
    toks = [t.strip("-") for t in s.split() if t.strip("-")]
    return [t for t in toks if t not in SUFFIXES]


def normalize_name(name: str) -> str:
    return " ".join(name_tokens(name))


def first_last(name: str) -> tuple[str, str]:
    toks = name_tokens(name)
    if not toks:
        return "", ""
    if len(toks) == 1:
        return toks[0], toks[0]
    return toks[0], toks[-1]


def nickname_key(first: str) -> str:
    return NICKNAME_CANON.get(first, first)


def match_names(author: str, organizer: str) -> tuple[bool, str, float]:
    an = normalize_name(author)
    on = normalize_name(organizer)
    if not an or not on:
        return False, "", 0.0
    if an == on:
        return True, "exact_normalized", 1.0
    af, al = first_last(author)
    of, ol = first_last(organizer)
    if not af or not of or not al or not ol:
        return False, "", 0.0
    if al == ol == "rios-rull" and {af, of} <= {"jose-victor", "victor", "jose"}:
        return True, "nickname", 0.98
    if al == ol and af == of:
        return True, "first_last", 0.97
    if al == ol and nickname_key(af) == nickname_key(of):
        return True, "nickname", 0.94
    if al == ol and (af[0] == of[0]) and (len(af) == 1 or len(of) == 1):
        return True, "first_initial_last", 0.91
    if al == ol and len(af) >= 4 and len(of) >= 4:
        score = difflib.SequenceMatcher(None, af, of).ratio()
        if score >= 0.85:
            return True, "fuzzy_first_last", round(score * 0.93, 4)
    if af == of and len(al) >= 5 and len(ol) >= 5:
        score = difflib.SequenceMatcher(None, al, ol).ratio()
        if score >= 0.93:
            return True, "fuzzy_first_last", round(score * 0.92, 4)
    return False, "", 0.0


def stable_paper_id(year: int, program: str, title: str, authors: list[str]) -> str:
    key = f"{year}|{program}|{normalize_text(title)}|{'|'.join(sorted(normalize_name(a) for a in authors))}"
    return f"SI{year}-{program}-{hashlib.sha1(key.encode('utf-8')).hexdigest()[:10]}"


def conf_id(year: int, code: str, overrides: dict[str, str] | None = None) -> str:
    if overrides:
        key = f"{year}-{code}"
        if key in overrides:
            return overrides[key]
    return f"SI{str(year)[2:]}{code}"


def split_organizers(raw: str) -> list[str]:
    if not raw:
        return []
    parts = re.split(r"\s*;\s*", raw)
    return [clean_space(p) for p in parts if clean_space(p)]


def fetch_agenda(session: requests.Session, cid: str, force: bool = False) -> tuple[str, int, bool]:
    """Return (html, http_status, from_cache)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{cid}.html"
    if path.exists() and not force and path.stat().st_size > 400:
        text = path.read_text(encoding="utf-8", errors="replace")
        # Infer prior status from tiny error pages vs real agendas.
        status = 200 if len(text) > 800 and "Organized by" in text else (400 if len(text) < 800 else 200)
        return text, status, True
    url = BASE_PRINT + cid
    last_status = 0
    for attempt in range(5):
        try:
            resp = session.get(url, timeout=45)
            last_status = resp.status_code
            if resp.status_code == 200 and len(resp.text) > 800:
                path.write_text(resp.text, encoding="utf-8")
                return resp.text, 200, False
            if resp.status_code in {400, 404}:
                path.write_text(resp.text, encoding="utf-8")
                return resp.text, resp.status_code, False
            if resp.status_code in {403, 429, 500, 502, 503, 504}:
                time.sleep(2 ** attempt)
                continue
            path.write_text(resp.text, encoding="utf-8")
            return resp.text, resp.status_code, False
        except requests.RequestException:
            time.sleep(2 ** attempt)
    return "", last_status or 0, False


def parse_agenda(html: str) -> tuple[list[dict[str, Any]], str]:
    """Return (papers, organizer_line_from_page)."""
    soup = BeautifulSoup(html, "lxml")
    organizer_line = ""
    m = re.search(r"Organized by\s+(.+?)(?:<br|/span)", html, flags=re.I | re.S)
    if m:
        organizer_line = clean_space(BeautifulSoup(m.group(1), "lxml").get_text(" ", strip=True))
        organizer_line = re.sub(r"\s+and\s+", "; ", organizer_line)
        organizer_line = organizer_line.replace(",", ";")
        # undo over-split of initials like "Ralph S; J; Koijen" — keep roster organizers authoritative

    papers: list[dict[str, Any]] = []
    for entry in soup.select("tr.agenda-entry"):
        authors_block = entry.select_one(".paper-authors")
        if not authors_block:
            continue
        authors = [clean_space(s.get_text(" ", strip=True)) for s in authors_block.select(".author-name")]
        authors = [a for a in authors if a]
        if not authors:
            continue
        title = ""
        for em in entry.select("em"):
            cand = clean_space(em.get_text(" ", strip=True))
            if not cand:
                continue
            if normalize_text(cand) in NON_PAPER_EM:
                continue
            if cand.lower().startswith("format:"):
                continue
            title = cand
            break
        if not title:
            # fallback: first italic-like strong/paragraph text
            p = entry.select_one("p")
            if p:
                title = clean_space(p.get_text(" ", strip=True))
        if not title:
            continue
        # skip obvious non-papers
        nt = normalize_text(title)
        if nt.startswith("panel ") or nt.startswith("master lecture") or nt in {
            "welcome and introduction", "welcome announcements", "adjourn"
        }:
            continue
        papers.append({"title": title, "authors": authors})
    return papers, organizer_line


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({h: row.get(h, "") for h in headers})


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    coverage_rows = list(csv.DictReader(COVERAGE.open(encoding="utf-8-sig")))
    roster = [
        r for r in coverage_rows
        if r["year"].isdigit()
        and int(r["year"]) in YEARS
        and r.get("included_in_target_scope") == "1"
    ]
    overrides: dict[str, str] = {}
    if OVERRIDES_PATH.exists():
        overrides = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))

    session = requests.Session()
    session.headers.update(HEADERS)

    papers_out: list[dict[str, Any]] = []
    authors_out: list[dict[str, Any]] = []
    organizers_out: list[dict[str, Any]] = []
    program_year_out: list[dict[str, Any]] = []
    name_match_audit: list[dict[str, Any]] = []
    fetch_log: list[dict[str, Any]] = []

    total = len(roster)
    for i, row in enumerate(roster, 1):
        year = int(row["year"])
        code = row["program_code"]
        name = row["program_name"]
        organizers = split_organizers(row.get("organizer_names", ""))
        cid = conf_id(year, code, overrides)
        url = BASE_PRINT + cid
        print(f"[{i}/{total}] {cid} {name}", flush=True)

        html, status, from_cache = fetch_agenda(session, cid)
        papers, _page_org = parse_agenda(html) if (status == 200 or "Organized by" in html) else ([], "")
        captured = 1 if "Organized by" in html else 0
        if status == 200 and not papers and "Organized by" not in html and len(html) < 1000:
            captured = 0

        fetch_log.append({
            "year": year,
            "program_code": code,
            "conference_id": cid,
            "http_status": status,
            "agenda_captured": captured,
            "papers_parsed": len(papers),
            "html_bytes": len(html),
            "source_url": url,
        })

        for org in organizers:
            organizers_out.append({
                "year": year,
                "program_code": code,
                "program_name": name,
                "organizer_name": org,
                "organizer_name_normalized": normalize_name(org),
                "agenda_captured": captured,
                "papers_total": len(papers) if captured else "",
                "source_url": url,
            })

        matched_papers = 0
        for paper in papers:
            pid = stable_paper_id(year, code, paper["title"], paper["authors"])
            matched_authors: list[str] = []
            matched_orgs: list[str] = []
            methods: list[str] = []
            for pos, author in enumerate(paper["authors"], 1):
                is_match = 0
                matched_org = ""
                method = ""
                conf = ""
                for org in organizers:
                    ok, meth, score = match_names(author, org)
                    if ok:
                        is_match = 1
                        matched_org = org
                        method = meth
                        conf = score
                        matched_authors.append(author)
                        matched_orgs.append(org)
                        methods.append(meth)
                        if meth != "exact_normalized":
                            name_match_audit.append({
                                "paper_id": pid,
                                "year": year,
                                "program_code": code,
                                "program_name": name,
                                "conference_id": cid,
                                "paper_title": paper["title"],
                                "author_position": pos,
                                "author_name": author,
                                "author_name_normalized": normalize_name(author),
                                "matched_organizer_name": org,
                                "match_method": meth,
                                "match_confidence": score,
                                "source_url": url,
                            })
                        break
                authors_out.append({
                    "paper_id": pid,
                    "year": year,
                    "program_code": code,
                    "program_name": name,
                    "conference_id": cid,
                    "paper_title": paper["title"],
                    "author_position": pos,
                    "author_name": author,
                    "author_name_normalized": normalize_name(author),
                    "is_program_year_organizer_author": is_match,
                    "matched_organizer_name": matched_org,
                    "match_method": method,
                    "match_confidence": conf,
                    "source_url": url,
                })

            has_org = int(bool(matched_authors))
            matched_papers += has_org
            papers_out.append({
                "paper_id": pid,
                "year": year,
                "program_code": code,
                "program_name": name,
                "conference_id": cid,
                "title": paper["title"],
                "author_count": len(paper["authors"]),
                "author_names": "; ".join(paper["authors"]),
                "program_year_organizers": "; ".join(organizers),
                "organizer_coauthored_program_year": has_org,
                "matched_author_names_program_year": "; ".join(dict.fromkeys(matched_authors)),
                "matched_organizer_names_program_year": "; ".join(dict.fromkeys(matched_orgs)),
                "match_methods": "; ".join(dict.fromkeys(methods)),
                "included_in_measure": 1,
                "source_url": url,
            })

        share = (matched_papers / len(papers)) if papers else ""
        program_year_out.append({
            "year": year,
            "program_code": code,
            "program_name": name,
            "organizer_names": "; ".join(organizers),
            "organizer_count": len(organizers),
            "included_in_target_scope": 1,
            "agenda_captured": captured,
            "http_status": status,
            "papers_total": len(papers) if captured else "",
            "papers_with_program_year_organizer": matched_papers if captured else "",
            "program_year_organizer_share": share if captured and papers else ("" if not captured else 0.0),
            "source_url": url,
            "coverage_note": (
                "captured official printable agenda" if captured
                else f"not captured; http_status={status}; blank is not zero"
            ),
        })

        # Be polite to NBER; skip delay on cache hits.
        if not from_cache:
            time.sleep(0.4)

    # Deduplicate papers within program-year by normalized title + author set
    deduped: list[dict[str, Any]] = []
    seen_keys: set[tuple] = set()
    dup_audit: list[dict[str, Any]] = []
    for p in papers_out:
        key = (
            p["year"], p["program_code"],
            normalize_text(p["title"]),
            tuple(sorted(normalize_name(a) for a in p["author_names"].split("; ") if a)),
        )
        if key in seen_keys:
            dup_audit.append(p)
            continue
        seen_keys.add(key)
        deduped.append(p)
    papers_out = deduped

    # Recompute program-year shares after dedup
    by_py: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for p in papers_out:
        by_py[(p["year"], p["program_code"])].append(p)
    py_map = {(r["year"], r["program_code"]): r for r in program_year_out}
    for (year, code), plist in by_py.items():
        r = py_map[(year, code)]
        if r["agenda_captured"] != 1:
            continue
        matched = sum(int(p["organizer_coauthored_program_year"]) for p in plist)
        r["papers_total"] = len(plist)
        r["papers_with_program_year_organizer"] = matched
        r["program_year_organizer_share"] = matched / len(plist) if plist else 0.0

    # Year summary
    year_summary: list[dict[str, Any]] = []
    for year in YEARS:
        rows = [r for r in program_year_out if r["year"] == year]
        captured = [r for r in rows if r["agenda_captured"] == 1 and r["papers_total"] != ""]
        papers = [p for p in papers_out if p["year"] == year]
        matched = sum(int(p["organizer_coauthored_program_year"]) for p in papers)
        shares = [float(r["program_year_organizer_share"]) for r in captured if r["papers_total"]]
        year_summary.append({
            "year": year,
            "program_years_total": len(rows),
            "program_years_captured": len(captured),
            "coverage": (len(captured) / len(rows)) if rows else 0.0,
            "papers_total": len(papers),
            "papers_coauthored_by_organizer": matched,
            "weighted_organizer_share": (matched / len(papers)) if papers else "",
            "unweighted_mean_program_share": (sum(shares) / len(shares)) if shares else "",
        })

    # Program overall summary across years
    prog_codes = sorted({r["program_code"] for r in program_year_out})
    program_overall: list[dict[str, Any]] = []
    for code in prog_codes:
        rows = [r for r in program_year_out if r["program_code"] == code and r["agenda_captured"] == 1 and r["papers_total"] != ""]
        papers = [p for p in papers_out if p["program_code"] == code]
        if not papers:
            continue
        matched = sum(int(p["organizer_coauthored_program_year"]) for p in papers)
        shares = [float(r["program_year_organizer_share"]) for r in rows if r["papers_total"]]
        program_overall.append({
            "program_code": code,
            "program_name": rows[0]["program_name"] if rows else papers[0]["program_name"],
            "program_years_captured": len(rows),
            "papers_total": len(papers),
            "papers_coauthored_by_organizer": matched,
            "weighted_organizer_share": matched / len(papers),
            "unweighted_mean_program_share": (sum(shares) / len(shares)) if shares else "",
        })
    program_overall.sort(key=lambda r: (-r["weighted_organizer_share"], r["program_code"]))

    write_csv(OUT / "nber_si_papers_2020_2026.csv", list(papers_out[0].keys()) if papers_out else [
        "paper_id", "year", "program_code", "title"
    ], papers_out)
    write_csv(OUT / "nber_si_authors_2020_2026.csv", list(authors_out[0].keys()) if authors_out else [
        "paper_id", "author_name"
    ], authors_out)
    write_csv(OUT / "nber_si_organizers_2020_2026.csv", list(organizers_out[0].keys()), organizers_out)
    write_csv(OUT / "nber_si_program_year_summary_2020_2026.csv", list(program_year_out[0].keys()), program_year_out)
    write_csv(OUT / "nber_si_year_summary_2020_2026.csv", list(year_summary[0].keys()), year_summary)
    write_csv(OUT / "nber_si_program_overall_summary_2020_2026.csv", list(program_overall[0].keys()) if program_overall else [
        "program_code"
    ], program_overall)
    write_csv(OUT / "nber_si_name_match_audit_2020_2026.csv",
              list(name_match_audit[0].keys()) if name_match_audit else [
                  "paper_id", "author_name", "matched_organizer_name", "match_method"
              ], name_match_audit)
    write_csv(OUT / "nber_si_duplicates_audit_2020_2026.csv",
              list(dup_audit[0].keys()) if dup_audit else ["paper_id"], dup_audit)
    write_csv(OUT / "nber_si_fetch_log_2020_2026.csv", list(fetch_log[0].keys()), fetch_log)

    captured_n = sum(1 for r in program_year_out if r["agenda_captured"] == 1)
    total_papers = len(papers_out)
    total_matched = sum(int(p["organizer_coauthored_program_year"]) for p in papers_out)
    qc = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "years": list(YEARS),
        "in_scope_program_years": len(program_year_out),
        "captured_program_years": captured_n,
        "coverage": captured_n / len(program_year_out) if program_year_out else 0,
        "papers_included": total_papers,
        "author_rows": len(authors_out),
        "organizer_coauthored_papers": total_matched,
        "weighted_organizer_share": (total_matched / total_papers) if total_papers else None,
        "non_exact_name_matches": len(name_match_audit),
        "duplicate_listings_collapsed": len(dup_audit),
        "source_printable_pattern": BASE_PRINT + "SI{YY}{CODE}",
        "organizer_roster_source": str(COVERAGE),
        "measure": (
            "distinct papers with at least one program-year organizer among authors "
            "/ distinct included papers"
        ),
    }
    (OUT / "nber_si_qc_2020_2026.json").write_text(json.dumps(qc, indent=2), encoding="utf-8")

    print("\n=== DONE ===")
    print(json.dumps(qc, indent=2))
    print("\nYear summary:")
    for y in year_summary:
        print(y)


if __name__ == "__main__":
    main()

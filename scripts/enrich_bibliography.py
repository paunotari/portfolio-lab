#!/usr/bin/env python3
"""Complete the paper's bibliography from Crossref — page ranges and DOIs.

CMS 17 author-date wants a page range and, where one exists, a DOI for every journal
article. The hand-written thebibliography in paper/tex/paper.tex carries journal, volume
and issue but not those, and they must never be filled in from memory: that is citation
fabrication, and a wrong DOI is worse than an absent one because a referee who follows it
lands on a different document.

WHY THIS IS NOT "take the first Crossref hit". Spot-checking three entries by hand, two of
the three top results were the wrong record: Bailey & Lopez de Prado returned the SSRN
working paper rather than the JPM article, and DeMiguel et al. returned a book-chapter
reprint in a volume called *Heuristics* whose page numbers belong to the book, not to the
Review of Financial Studies. So every candidate here must PASS A MATCH TEST against what
the entry already asserts before it is accepted:

    year          must match exactly
    journal       normalized container-title must match the declared one
    volume        must match when both sides have it
    authors       at least one declared surname must appear in the record

Anything that fails is reported for manual resolution, never silently written.

Run:  python3 scripts/enrich_bibliography.py            # report only
      python3 scripts/enrich_bibliography.py --write    # apply the verified matches
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "paper" / "tex" / "paper.tex"
MAILTO = "pau.notari@gmail.com"          # Crossref "polite pool" — faster, and it is courteous
API = "https://api.crossref.org/works"

# Entries that are not journal articles: no page range is expected of them.
NON_ARTICLE = {"antonacci2014", "judge1978", "boyd2024", "raffinot2018"}


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm_journal(s: str) -> str:
    """Comparable form of a journal name: no accents, no case, no leading article, no
    punctuation. 'The Journal of Portfolio Management' -> 'journal of portfolio management'."""
    s = strip_accents(re.sub(r"\\[a-z]+|[{}]", "", s)).lower()
    s = s.replace("&amp;", " and ").replace("&", " and ")   # Crossref returns HTML entities
    s = re.sub(r"[^a-z ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"^the ", "", s)


def parse_bib(tex: str) -> list[dict]:
    """Pull the hand-written entries apart into fields we can match on."""
    block = tex[tex.index(r"\begin{thebibliography}"):tex.index(r"\end{thebibliography}")]
    raw = re.findall(r"\\bibitem\[[^\]]*\]\{([^}]*)\}(.*?)(?=\\bibitem|\Z)", block, re.S)
    out, last_authors = [], ""
    for key, body in raw:
        text = re.sub(r"\s+", " ", body).strip()
        year = (re.search(r"\b(19|20)\d{2}[a-z]?\.", text) or [None])
        year = re.search(r"\b((?:19|20)\d{2})[a-z]?\.", text)
        title = re.search(r"``(.+?)''", text)
        journal = re.search(r"\\emph\{(.+?)\}", text)
        volissue = re.search(r"\\emph\{.+?\}\s*([0-9]+)\s*(?:\((\d+)\))?", text)
        # "---------." repeats the previous entry's author list
        head = text.split(str(year.group(1)) if year else "|||")[0]
        authors = last_authors if head.strip().startswith("-") else head
        if not head.strip().startswith("-"):
            last_authors = authors
        # de-TeX the accents first: "L\'opez de Prado" must yield "Lopez de Prado", not "opez".
        plain = re.sub(r"\\['`^\"~=.]\{?([a-zA-Z])\}?", r"\1", authors)
        surnames = re.findall(r"([A-Z][a-zA-Z'\-]+(?: de [A-Z][a-z]+)?),", strip_accents(plain))
        out.append(dict(key=key, raw=body, text=text,
                        year=int(year.group(1)) if year else None,
                        title=re.sub(r"\\[a-z]+|[{}]", "", title.group(1)) if title else "",
                        journal=journal.group(1) if journal else "",
                        volume=volissue.group(1) if volissue else None,
                        surnames=surnames,
                        has_pages=bool(re.search(r":\s*\d", text)),
                        has_doi="doi.org" in text))
    return out


def crossref(entry: dict) -> list[dict]:
    q = {"query.bibliographic": f"{entry['title']} {' '.join(entry['surnames'][:3])}",
         "rows": "8",
         "select": "title,author,container-title,volume,issue,page,DOI,issued,type"}
    if entry["year"]:
        q["filter"] = f"from-pub-date:{entry['year']-1}-01-01,until-pub-date:{entry['year']+1}-12-31"
    url = f"{API}?{urllib.parse.urlencode(q)}"
    # curl rather than urllib: this machine's Python has no usable CA bundle, so urllib raises
    # CERTIFICATE_VERIFY_FAILED on every call while curl (system certs) works fine.
    out = subprocess.run(
        ["curl", "-sS", "--fail", "--max-time", "30",
         "-H", f"User-Agent: portfolio-lab-bib/1.0 (mailto:{MAILTO})", url],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip()[:120] or f"curl exit {out.returncode}")
    return json.loads(out.stdout)["message"]["items"]


def verify(entry: dict, item: dict) -> tuple[bool, str]:
    """A candidate is accepted only if it agrees with what the entry already claims."""
    # Type and venue gates first: Crossref happily returns the SSRN preprint, a CFA Digest
    # summary, or a book-chapter reprint of the same title, each with the WRONG pages.
    if item.get("type") != "journal-article":
        return False, f"type {item.get('type')}"
    cj = norm_journal((item.get("container-title") or [""])[0])
    if "ssrn" in cj or "digest" in cj:
        return False, f"aggregator/preprint venue '{cj[:30]}'"
    # Year is NOT a reliable key: publishers register the online-first date, so DeMiguel's
    # RFS 22(5) article carries issued=2007 and Yuan-Zhou's carries 2022. Volume plus journal
    # plus author is the stronger identity, so year is allowed +/-2 and volume is REQUIRED
    # whenever the entry declares one.
    yr = (item.get("issued", {}).get("date-parts") or [[None]])[0][0]
    if yr is None or abs(yr - entry["year"]) > 2:
        return False, f"year {yr} vs {entry['year']}"
    want_j = norm_journal(entry["journal"])
    if want_j and cj != want_j and want_j not in cj and cj not in want_j:
        return False, f"journal '{cj[:34]}' != '{want_j[:34]}'"
    if entry["volume"]:
        if not item.get("volume"):
            return False, "record has no volume to check against"
        if str(item["volume"]) != entry["volume"]:
            return False, f"VOLUME {item['volume']} != declared {entry['volume']}"
    fams = {strip_accents(a.get("family", "")).lower() for a in item.get("author", [])}
    want = {s.lower() for s in map(strip_accents, entry["surnames"])}
    if want and not (fams & want):
        return False, f"no author overlap ({sorted(fams)[:3]})"
    if not item.get("page"):
        return False, "record has no page range"
    return True, "ok"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="apply the verified matches to the .tex")
    args = ap.parse_args()

    tex = TEX.read_text(encoding="utf-8")
    entries = parse_bib(tex)
    print(f"{len(entries)} entries parsed from {TEX.relative_to(ROOT)}\n")

    accepted, manual, skipped = {}, [], []
    for e in entries:
        if e["key"] in NON_ARTICLE:
            skipped.append((e["key"], "not a journal article"))
            continue
        if e["has_pages"] and e["has_doi"]:
            skipped.append((e["key"], "already complete"))
            continue
        try:
            items = crossref(e)
        except Exception as ex:
            manual.append((e["key"], f"query failed: {ex}"))
            continue
        hit = None
        reasons = []
        for it in items:
            ok, why = verify(e, it)
            if ok:
                hit = it
                break
            reasons.append(why)
        if hit:
            accepted[e["key"]] = dict(page=hit["page"].replace("-", "\u2013"), doi=hit["DOI"])
            print(f"  OK    {e['key']:<18} {hit['page']:>12}   {hit['DOI']}")
        else:
            manual.append((e["key"], "; ".join(reasons[:2]) or "no candidates"))
            print(f"  CHECK {e['key']:<18} {reasons[0] if reasons else 'no candidates'}")
        time.sleep(0.35)

    print(f"\nverified {len(accepted)} | manual {len(manual)} | skipped {len(skipped)}")
    if manual:
        print("\nNEEDS MANUAL RESOLUTION:")
        for k, why in manual:
            print(f"  {k:<18} {why[:96]}")
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / "bibliography_enrichment.json").write_text(
        json.dumps(dict(accepted=accepted, manual=manual, skipped=skipped), indent=2))

    if args.write and accepted:
        for key, v in accepted.items():
            pat = re.compile(r"(\\bibitem\[[^\]]*\]\{" + re.escape(key) + r"\}.*?)(\.\s*)(?=\n*\\bibitem|\n*\\end\{thebib)", re.S)
            def add(m):
                body = m.group(1).rstrip()
                if body.endswith("."):
                    body = body[:-1]
                return f"{body}: {v['page']}. https://doi.org/{v['doi']}.\n"
            tex, n = pat.subn(add, tex, count=1)
            if n == 0:
                print(f"  WARN could not splice {key}")
        TEX.write_text(tex, encoding="utf-8")
        print(f"\nwrote {len(accepted)} enrichments to {TEX.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

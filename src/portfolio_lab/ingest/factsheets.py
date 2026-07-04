"""Ingest sector weights, country weights and top-10 constituents from MSCI factsheet PDFs.

Region is taken from the parent folder (data/raw/msci_indexes/<REGION>/*.pdf); the index name
and factor type come from the PDF title. Handles the three constituent-table layouts MSCI uses:

  1. multi-country:      NAME  CC  mktcap  weight  Sector
  2. single-country ref: NAME  mktcap  weight  Sector          (World / USA reference)
  3. single-country fac: NAME  weight  parentWeight  Sector     (USA Momentum / Quality)

pdfplumber merges the left stats column into some rows; clean_name() strips the leading run of
stat-label words / numbers so company names come out clean. Emits four CSVs to data/processed.

Run:  python -m portfolio_lab.ingest.factsheets
"""
from __future__ import annotations
import re
import csv
import pdfplumber

from portfolio_lab import config as C

# label:pct pairs in the SECTOR/COUNTRY legend (integer or decimal %)
_PAIR = re.compile(r"([A-Za-z][A-Za-z\.\&\-\s]+?)\s+(\d{1,2}(?:\.\d{1,2})?)%")
# layout 1: 2-letter country code present
_CONS_CC = re.compile(r"^(.+?)\s+([A-Z]{2})\s+([\d,]+\.\d+)\s+(\d+\.\d+)\s+([A-Za-z].+)$")
_SEC_SHORT = "|".join(re.escape(s) for s in C.GICS_SECTORS_SHORT)
# layout 3: two weight columns
_CONS_2W = re.compile(r"([A-Z][A-Za-z&\.\-' ]+?)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(" + _SEC_SHORT + r")")
# layout 2: mktcap + single weight
_CONS_MC = re.compile(r"([A-Z][A-Za-z&\.\-' ]+?)\s+([\d,]+\.\d+)\s+(\d+\.\d+)\s+(" + _SEC_SHORT + r")")

_NOISE = {"Constituents", "Number", "of", "Weight", "Largest", "Smallest", "Average",
          "Median", "Cap", "Float", "Adj", "Mkt", "Millions", "Billions", "USD", "Index"}


def clean_name(nm: str) -> str:
    w = nm.split()
    while len(w) > 1 and (w[0] in _NOISE or re.match(r"^[\d,]+\.?\d*$", w[0])):
        w = w[1:]
    return " ".join(w)


def _parse_pdf(path, region):
    with pdfplumber.open(path) as pdf:
        p0 = pdf.pages[0].extract_text()
        p1 = pdf.pages[1].extract_text() if len(pdf.pages) > 1 else ""
    idx_name = p0.split("\n")[1].replace(" (USD)", "").replace(" (AUD)", "").strip()
    ft = C.factor_type(idx_name)

    sectors, countries, constituents = [], [], []

    # sector & country legend
    blk = p1[p1.index("SECTOR WEIGHTS"):] if "SECTOR WEIGHTS" in p1 else p1
    for m in _PAIR.finditer(blk):
        label, pct = m.group(1).strip(), float(m.group(2))
        if label in ("Since", "Dec") or any(w in label.upper() for w in ("WEIGHT", "SECTOR", "COUNTRY")):
            continue
        if label in C.GICS_SECTORS:
            sectors.append((label, pct))
        elif len(label) >= 2:
            countries.append((label, pct))

    # constituents — layout 1 first
    for line in p1.split("\n"):
        cm = _CONS_CC.match(line.strip())
        if cm:
            nm = clean_name(cm.group(1).strip())
            if nm.upper() in ("TOTAL", "NUMBER OF") or not nm:
                continue
            constituents.append((nm, cm.group(2), float(cm.group(3).replace(",", "")),
                                 float(cm.group(4)), cm.group(5).strip()))
    # fallback: single-country layouts (2 or 3), pick whichever yields more rows
    if not constituents:
        def collect(rx, has_mktcap):
            out, seen = [], set()
            for cm in rx.finditer(p1):
                nm = clean_name(cm.group(1).strip())
                if not nm or nm in seen:
                    continue
                seen.add(nm)
                mc = float(cm.group(2).replace(",", "")) if has_mktcap else ""
                wt = float(cm.group(3)) if has_mktcap else float(cm.group(2))
                out.append((nm, "US", mc, wt, cm.group(4)))
            return out[:10]
        a, b = collect(_CONS_2W, False), collect(_CONS_MC, True)
        constituents = a if len(a) >= len(b) else b

    return idx_name, ft, sectors, countries, constituents


def build():
    C.ensure_dirs()
    sec_rows, ctry_rows, cons_rows, meta_rows = [], [], [], []
    n_pdf = 0
    for region in C.REGIONS:
        for path in sorted((C.RAW_DIR / region).glob("*.pdf")):
            n_pdf += 1
            idx_name, ft, sectors, countries, cons = _parse_pdf(path, region)
            src, asof = "factsheet_pdf", C.FACTSHEET_ASOF
            for s, p in sectors:
                sec_rows.append([idx_name, region, ft, s, p, asof, src])
            for c, p in countries:
                ctry_rows.append([idx_name, region, ft, c, p, asof, src])
            for nm, cc, mc, wt, sec in cons:
                cons_rows.append([idx_name, region, ft, nm, cc, mc, wt, sec, asof, src])
            meta_rows.append([idx_name, region, ft, path.name, "", asof, src])

    def dump(path, header, rows):
        with open(path, "w", newline="") as f:
            w = csv.writer(f); w.writerow(header); w.writerows(rows)

    dump(C.SECTOR_WEIGHTS, ["index_name", "region", "factor_type", "sector", "weight_pct", "asof_date", "source"], sec_rows)
    dump(C.COUNTRY_WEIGHTS, ["index_name", "region", "factor_type", "country", "weight_pct", "asof_date", "source"], ctry_rows)
    dump(C.TOP_CONSTITUENTS, ["index_name", "region", "factor_type", "constituent", "country", "float_mktcap_usd_bn", "weight_pct", "sector", "asof_date", "source"], cons_rows)
    dump(C.INDEX_META, ["index_name", "region", "factor_type", "source_pdf", "num_constituents", "asof_date", "source"], meta_rows)
    print(f"[factsheets] {n_pdf} pdfs -> sectors {len(sec_rows)}, countries {len(ctry_rows)}, "
          f"constituents {len(cons_rows)}, meta {len(meta_rows)}")


if __name__ == "__main__":
    build()

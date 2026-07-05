"""Append the two AC Asia ex Japan factor indices that have no PDF factsheet.

MSCI does not publish factsheets for AC Asia ex Japan Enhanced Value / Momentum, so these
weights were transcribed from the MSCI website screenshots (1-decimal precision -> sector sums
round to ~99.5%, not a data error). Marked source='msci_web_image'. Run AFTER factsheets.run().

Run:  python -m portfolio_lab.ingest.asia_images
"""
from __future__ import annotations
import csv
from portfolio_lab import config as C

REGION, SRC = "AC_Asia_ex_Japan", "msci_web_image"

DATA = {
    "MSCI AC Asia ex Japan Enhanced Value Index": {
        "ft": "Enhanced Value",
        "sectors": [("Information Technology", 53.1), ("Financials", 14.3), ("Industrials", 8.6),
                    ("Consumer Discretionary", 7.9), ("Communication Services", 5.0), ("Materials", 2.4),
                    ("Health Care", 2.1), ("Consumer Staples", 1.8), ("Energy", 1.8),
                    ("Utilities", 1.3), ("Real Estate", 1.1)],
        "countries": [("Korea", 65.1), ("China", 25.4), ("Taiwan", 4.2), ("Hong Kong", 3.4),
                      ("Thailand", 0.7), ("Other", 1.2)],
        "cons": [("SAMSUNG ELECTRONICS CO", 23.25), ("SK HYNIX", 22.44), ("CHINA CONSTRUCTION BK H", 4.94),
                 ("SK SQUARE CO", 3.88), ("SAMSUNG ELECTRONICS PREF", 2.94), ("ICBC H", 2.76),
                 ("KIA CORP", 2.47), ("BANK OF CHINA H", 2.34), ("CHINA TOWER CORP H", 2.08),
                 ("HYUNDAI MOBIS", 2.00)],
    },
    "MSCI AC Asia ex Japan Momentum Index": {
        "ft": "Momentum",
        "sectors": [("Information Technology", 78.4), ("Industrials", 10.3), ("Financials", 5.1),
                    ("Materials", 2.1), ("Consumer Discretionary", 1.7), ("Energy", 1.0),
                    ("Real Estate", 0.5), ("Consumer Staples", 0.2), ("Utilities", 0.2),
                    ("Communication Services", 0.1)],
        "countries": [("Korea", 51.6), ("Taiwan", 38.9), ("China", 4.6), ("Singapore", 2.2),
                      ("Hong Kong", 1.3), ("Other", 1.4)],
        "cons": [("SK HYNIX", 20.09), ("TAIWAN SEMICONDUCTOR MFG", 14.77), ("SAMSUNG ELECTRONICS CO", 14.50),
                 ("DELTA ELECTRONICS", 4.63), ("SK SQUARE CO", 4.31), ("SAMSUNG ELECTRO-MECH. CO", 3.08),
                 ("ASE TECHNOLOGY HOLDING", 2.33), ("MEDIATEK INC", 2.24), ("ELITE MATERIAL CO", 2.08),
                 ("UNIMICRON TECHNOLOGY", 1.69)],
    },
}


def run():
    asof = C.FACTSHEET_ASOF

    def append(path, rows):
        with open(path, "a", newline="") as f:
            csv.writer(f).writerows(rows)

    for name, d in DATA.items():
        append(C.SECTOR_WEIGHTS, [[name, REGION, d["ft"], s, p, asof, SRC] for s, p in d["sectors"]])
        append(C.COUNTRY_WEIGHTS, [[name, REGION, d["ft"], c, p, asof, SRC] for c, p in d["countries"]])
        append(C.TOP_CONSTITUENTS, [[name, REGION, d["ft"], n, "", "", w, "", asof, SRC] for n, w in d["cons"]])
        append(C.INDEX_META, [[name, REGION, d["ft"], "", "", asof, SRC]])
    print(f"[asia_images] appended {len(DATA)} image-sourced indices")


if __name__ == "__main__":
    run()

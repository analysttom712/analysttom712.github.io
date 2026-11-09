"""Reads the Vendor 1 and Vendor 2 PDF reports back into rows.

Neither vendor sends the person number, and both mask the SSN to the last 4 digits
(XXX-XX-1234). Matching to a person happens later, in SQL, on last 4 + name.

Each file is checked against its own footer (record count and report total) before any row
is used. Synthetic data only.
"""
import datetime as dt
import os
import re

from pypdf import PdfReader

COLS = re.compile(r"\s{2,}")   # columns in layout text are separated by 2+ spaces
SSN_MASKED = re.compile(r"XXX-XX-(\d{4})")


def _lines(path):
    for page in PdfReader(path).pages:
        for line in page.extract_text(extraction_mode="layout").splitlines():
            if line.strip():
                yield line.strip()


def _money(text):
    """'$1,416.00' -> 1416.0 ; '42.50-' -> -42.5"""
    text = text.replace("$", "").replace(",", "").strip()
    neg = text.endswith("-") or text.startswith("(")
    value = float(text.strip("-()"))
    return -value if neg else value


def parse_vendor1(path):
    rows, draft, foot = [], None, None
    for line in _lines(path):
        if m := re.search(r"Draft date: (\d{2}/\d{2}/\d{4})", line):
            draft = dt.datetime.strptime(m.group(1), "%m/%d/%Y").date()
        elif m := re.match(r"Report total: (\$[\d,.\-()]+)\s+Members: (\d+)", line):
            foot = (_money(m.group(1)), int(m.group(2)))
        else:
            parts = COLS.split(line)
            if len(parts) == 4 and (m := SSN_MASKED.fullmatch(parts[2])):
                rows.append({"first_name": parts[0], "last_name": parts[1], "ssn_last4": m.group(1),
                             "amount": _money(parts[3]), "draft_date": draft})
    return rows, foot


def parse_vendor2(path):
    rows, foot = [], None
    for line in _lines(path):
        if m := re.match(r"TOTAL COLLECTED ([\d.\-]+)\s+COUNT (\d+)", line):
            foot = (_money(m.group(1)), int(m.group(2)))
            continue
        parts = COLS.split(line)
        if len(parts) == 4 and (m := SSN_MASKED.fullmatch(parts[1])):
            first, last = parts[2].split(" ", 1)
            rows.append({"first_name": first, "last_name": last, "ssn_last4": m.group(1),
                         "amount": _money(parts[3]), "draft_date": dt.date.fromisoformat(parts[0])})
    return rows, foot


PARSERS = {"Vendor 1": parse_vendor1, "Vendor 2": parse_vendor2}


def extract(vendor, path):
    """Returns (rows, check): check says whether the rows agree with the report's own footer."""
    rows, foot = PARSERS[vendor](path)
    total = round(sum(r["amount"] for r in rows), 2)
    check = {"rows": len(rows), "total": total, "footer_rows": foot and foot[1], "footer_total": foot and foot[0]}
    if foot is None:
        check["status"] = "FAIL: no footer found"
    elif foot[1] != len(rows) or round(foot[0], 2) != total:
        check["status"] = "FAIL: rows or total disagree with the footer"
    else:
        check["status"] = "OK"
    return rows, check


if __name__ == "__main__":
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Data", "Vendor PDFs")
    for vendor in PARSERS:
        for name in sorted(os.listdir(os.path.join(root, vendor))):
            _, check = extract(vendor, os.path.join(root, vendor, name))
            print(f"{vendor:9} {name:18} {check['status']:4} rows={check['rows']:4} total={check['total']:>12,.2f}")

"""Builds Output/recon.db from the source files: the Excel reports and the vendor PDFs.

Steps
  1. Create the tables (SQL/01_schema.sql).
  2. Load the worker list as person + assignment_history, with effective dates.
  3. Collapse the 12 monthly billing reports into benefit_enrollment_history (date ranges),
     then prove nothing was lost: rebuilding each month from the ranges gives back the report.
  4. Extract the vendor PDFs (extract_vendor_pdfs.py); load them with Internal ACH into receipt_staging.
  5. Load the payment log, ledger detail and ledger postings.
  6. Log every file in load_log.

Synthetic data only. Uses openpyxl and pypdf; no pandas. Run:  python load_db.py
"""
import datetime as dt
import os
import sqlite3

import openpyxl

import extract_vendor_pdfs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "Data")
SQL = os.path.join(ROOT, "SQL")
DB = os.path.join(ROOT, "Output", "recon.db")
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
OPEN_END = "9999-12-31"


def iso(d):
    return d.date().isoformat() if isinstance(d, dt.datetime) else (d.isoformat() if d else None)


def month_of(file_name):
    parts = os.path.splitext(file_name)[0].split(" ")
    year = int(parts[1]) if len(parts) > 1 else 2025
    return dt.date(year, MONTHS.index(parts[0]) + 1, 1)


def month_end(d):
    nxt = dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return nxt - dt.timedelta(days=1)


def sheet(path):
    ws = openpyxl.load_workbook(path, read_only=True).active
    rows = ws.iter_rows(values_only=True)
    head = next(rows)
    return [dict(zip(head, r)) for r in rows if r[0] is not None]


def monthly_files(folder):
    path = os.path.join(DATA, folder)
    for name in sorted(os.listdir(path), key=lambda n: month_of(n)):
        if name.endswith(".xlsx") and not name.startswith("~$"):
            yield name, month_of(name), sheet(os.path.join(path, name))


def log(db, source, name, month, rows, total=None, footer=None, status="OK"):
    db.execute("INSERT INTO load_log VALUES (?,?,?,?,?,?,?)",
               (source, name, iso(month), rows, None if total is None else round(total, 2), footer, status))


def load_people(db):
    rows = sheet(os.path.join(DATA, "Worker List.xlsx"))
    by_person = {}
    for r in rows:
        by_person.setdefault(r["Person Number"], []).append(r)
    for pn, rels in by_person.items():
        rels.sort(key=lambda r: r["Most Recent Hire Date"])
        latest = rels[-1]
        db.execute("INSERT INTO person VALUES (?,?,?,?,?,?)",
                   (pn, latest["First Name"], latest["Last Name"], latest["SSN (synthetic 900-range)"],
                    iso(latest["Date of Birth"]), iso(latest["Date of Death"])))
        for i, r in enumerate(rels):
            end = iso(rels[i + 1]["Most Recent Hire Date"] - dt.timedelta(days=1)) if i + 1 < len(rels) else OPEN_END
            db.execute("INSERT INTO assignment_history VALUES (?,?,?,?,?,?,?,?,?)",
                       (pn, r["Payroll Relationship"], r["Region"], r["Division"], r["Legal Entity"],
                        r["Business Unit"], r["Employee Status"], iso(r["Most Recent Hire Date"]), end))
    log(db, "Worker List", "Worker List.xlsx", None, len(rows))
    deps = sheet(os.path.join(DATA, "Dependents.xlsx"))
    db.executemany("INSERT INTO dependent VALUES (?,?,?,?,?)",
                   [(d["Person Number"], d["Dependent First Name"], d["Dependent Last Name"],
                     d["Relationship"], iso(d["Date of Birth"])) for d in deps])
    log(db, "Dependents", "Dependents.xlsx", None, len(deps))


ENROLL_COLS = ["Worker Type", "Payment Method", "Division", "Medical", "Dental", "Total Premium",
               "Medicare Eligible", "Dependent Turning 26"]


def load_enrollment(db):
    """Collapses consecutive months with identical values into one date range per person."""
    snapshots = {}                       # month -> {person: values}
    for name, month, rows in monthly_files("Premium Billing"):
        for r in rows:
            assert iso(r["Effective Date"]) == month.isoformat(), (name, r["Person Number"])
        snapshots[month] = {r["Person Number"]: tuple(r[c] for c in ENROLL_COLS) for r in rows}
        log(db, "Premium Billing", name, month, len(rows), sum(r["Total Premium"] for r in rows))

    months = sorted(snapshots)
    ranges = []                          # [person, values, start, end]
    open_ranges = {}
    for i, month in enumerate(months):
        for pn, values in snapshots[month].items():
            cur = open_ranges.get(pn)
            if cur and cur[1] == values and cur[3] == months[i - 1]:
                cur[3] = month           # same values as last month: extend the range
            else:
                cur = [pn, values, month, month]
                ranges.append(cur)
                open_ranges[pn] = cur
    db.executemany("INSERT INTO benefit_enrollment_history VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                   [(pn, *values, start.isoformat(), month_end(end).isoformat()) for pn, values, start, end in ranges])

    # Lossless check: each month rebuilt from the ranges must equal that month's report
    for month in months:
        got = {r[0]: tuple(r[1:]) for r in db.execute(
            "SELECT person_number, worker_type, payment_method, division, medical, dental, total_premium, "
            "medicare_eligible, dependent_turning_26 FROM benefit_enrollment_history "
            "WHERE ? BETWEEN effective_start_date AND effective_end_date", (month.isoformat(),))}
        assert got == snapshots[month], f"enrollment ranges don't rebuild {month:%B}"
    return sum(len(s) for s in snapshots.values()), len(ranges)


def load_receipts(db):
    pdf_root = os.path.join(DATA, "Vendor PDFs")
    for vendor in ("Vendor 1", "Vendor 2"):
        for name in sorted(os.listdir(os.path.join(pdf_root, vendor)), key=month_of):
            month = month_of(name)
            rows, check = extract_vendor_pdfs.extract(vendor, os.path.join(pdf_root, vendor, name))
            log(db, vendor, name, month, check["rows"], check["total"], check["footer_total"], check["status"])
            if check["status"] != "OK":
                continue                 # a file that fails its own footer is not loaded
            db.executemany("INSERT INTO receipt_staging VALUES (?,?,?,?,?,?,?,?,?)",
                           [(vendor, name, month.isoformat(), None, r["first_name"], r["last_name"],
                             r["ssn_last4"], r["amount"], r["draft_date"].isoformat()) for r in rows])
    for name, month, rows in monthly_files("Internal ACH"):
        db.executemany("INSERT INTO receipt_staging VALUES (?,?,?,?,?,?,?,?,?)",
                       [("Internal ACH", name, month.isoformat(), r["Person Number"], r["First Name"], r["Last Name"],
                         None, r["Premium Received"], iso(r["Draft Date"])) for r in rows])
        log(db, "Internal ACH", name, month, len(rows), sum(r["Premium Received"] for r in rows))


def load_ledger(db):
    rows = sheet(os.path.join(DATA, "Payment Log.xlsx"))
    db.executemany("INSERT INTO payment_log VALUES (?,?,?,?,?,?,?)",
                   [(r["Person Number"], r["First Name"], r["Last Name"], r["Account Number Affected"],
                     r["Action"], iso(r["Date"]), r["Amount"]) for r in rows])
    log(db, "Payment Log", "Payment Log.xlsx", None, len(rows), sum(r["Amount"] for r in rows))
    for name, month, rows in monthly_files("Ledger Detail"):
        db.executemany("INSERT INTO ledger_detail VALUES (?,?,?,?,?)",
                       [(month.isoformat(), r["Person Number"], r["Account Number"], r["Business Unit"], r["Debit"])
                        for r in rows])
        log(db, "Ledger Detail", name, month, len(rows), sum(r["Debit"] for r in rows))
    for name, month, rows in monthly_files("Ledger Postings"):
        db.executemany("INSERT INTO ledger_posting VALUES (?,?,?,?,?,?,?,?)",
                       [(month.isoformat(), r["Transaction ID"], r["Post Number"], iso(r["Accounting Date"]),
                         r["Account Number"], r["Description"], r["Debit"] or 0, r["Credit"] or 0) for r in rows])
        log(db, "Ledger Postings", name, month, len(rows))


def main():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    if os.path.exists(DB):
        os.remove(DB)
    db = sqlite3.connect(DB)
    db.executescript(open(os.path.join(SQL, "01_schema.sql"), encoding="utf-8").read())
    m = dt.date(2024, 12, 1)
    while m <= dt.date(2026, 1, 1):
        db.execute("INSERT INTO month_calendar VALUES (?,?)", (m.isoformat(), month_end(m).isoformat()))
        m = month_end(m) + dt.timedelta(days=1)
    load_people(db)
    billing_rows, ranges = load_enrollment(db)
    load_receipts(db)
    load_ledger(db)
    db.commit()
    failed = db.execute("SELECT COUNT(*) FROM load_log WHERE status <> 'OK'").fetchone()[0]
    print(f"recon.db built: {billing_rows:,} billing rows held as {ranges:,} enrollment ranges (rebuilds every month exactly); "
          f"{db.execute('SELECT COUNT(*) FROM load_log').fetchone()[0]} files loaded, {failed} failed checks")
    db.close()


if __name__ == "__main__":
    main()

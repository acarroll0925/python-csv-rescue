#!/usr/bin/env python3
"""CSV Rescue — a rerunnable cleaning pipeline for messy CSV exports.

Usage:
    python3 csv_rescue.py orders_messy.csv [output_dir]

Reads a messy orders CSV and writes three files (default: next to the input):

    clean.csv          normalized, deduplicated rows
    rejected_rows.csv  every row that could not be safely cleaned,
                       original values preserved, plus a `reason` column
    run_summary.txt    rows in / out / rejected, duplicates removed,
                       rejections counted by reason

Design rules:
  * Standard library only. Runs anywhere Python 3.9+ runs.
  * The source file is never modified.
  * Nothing is guessed: a row that cannot be normalized with certainty is
    rejected with a specific reason, not silently dropped or "fixed".
  * Rerunnable: same input -> same output, byte for byte.

If the input is missing a required column, the script stops with a single
clear error line and writes NO partial output.
"""
import csv
import os
import re
import sys
from datetime import datetime

REQUIRED_COLUMNS = ["order_id", "order_date", "customer_name", "email",
                    "state", "product", "quantity", "unit_price"]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%b %d %Y", "%d-%b-%y"]

STATE_CODES = {
    "ga": "GA", "georgia": "GA",
    "tn": "TN", "tennessee": "TN",
    "al": "AL", "alabama": "AL",
    "fl": "FL", "florida": "FL",
    "sc": "SC", "south carolina": "SC",
    "nc": "NC", "north carolina": "NC",
    "tx": "TX", "texas": "TX",
    "ca": "CA", "california": "CA",
}


def parse_date(raw):
    """Return ISO date string, or None if the value is not a known date."""
    text = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_money(raw):
    """'$1,299.00' / 'USD 45.50' / '1299' -> '1299.00'. None if not money."""
    text = raw.strip().replace(",", "")
    if text.upper().startswith("USD"):
        text = text[3:].strip()
    text = text.lstrip("$").strip()
    try:
        return "%.2f" % float(text)
    except ValueError:
        return None


def normalize_state(raw):
    key = raw.strip().rstrip(".").strip().lower()
    return STATE_CODES.get(key)


def clean_row(row):
    """Return (cleaned_dict, None) or (None, reason). One reason, the first
    problem found, checked in key-field order so reports are stable."""
    order_id = row["order_id"].strip()
    if not order_id:
        return None, "missing order_id"

    iso_date = parse_date(row["order_date"])
    if iso_date is None:
        return None, "unparseable date: '%s'" % row["order_date"].strip()

    email = row["email"].strip().lower()
    if not email:
        return None, "missing email"
    if not EMAIL_RE.match(email):
        return None, "invalid email"

    state = normalize_state(row["state"])
    if state is None:
        return None, "unrecognized state: '%s'" % row["state"].strip()

    qty_raw = row["quantity"].strip()
    try:
        qty = int(qty_raw)
    except ValueError:
        return None, "invalid quantity: '%s'" % qty_raw
    if qty < 0:
        return None, "negative quantity"

    price = parse_money(row["unit_price"])
    if price is None:
        return None, "unparseable price: '%s'" % row["unit_price"].strip()

    name = " ".join(row["customer_name"].split()).title()
    cleaned = {
        "order_id": order_id,
        "order_date": iso_date,
        "customer_name": name,
        "email": email,
        "state": state,
        "product": " ".join(row["product"].split()),
        "quantity": str(qty),
        "unit_price": price,
    }
    return cleaned, None


def main(argv):
    if len(argv) < 2:
        print("usage: python3 csv_rescue.py <input.csv> [output_dir]",
              file=sys.stderr)
        return 2
    src = argv[1]
    out_dir = argv[2] if len(argv) > 2 else os.path.dirname(os.path.abspath(src))

    with open(src, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for col in REQUIRED_COLUMNS:
            if col not in fieldnames:
                # Wrong-shaped file: one clear line, no partial output.
                print("Error: missing required column: %s" % col,
                      file=sys.stderr)
                return 1
        raw_rows = list(reader)

    clean, rejected, seen_ids = [], [], set()
    duplicates = 0
    for row in raw_rows:
        cleaned, reason = clean_row(row)
        if reason is not None:
            rejected.append((row, reason))
        elif cleaned["order_id"] in seen_ids:
            duplicates += 1
        else:
            seen_ids.add(cleaned["order_id"])
            clean.append(cleaned)

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "clean.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
        w.writeheader()
        w.writerows(clean)

    with open(os.path.join(out_dir, "rejected_rows.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS + ["reason"])
        w.writeheader()
        for row, reason in rejected:
            out = {c: row.get(c, "") for c in REQUIRED_COLUMNS}
            out["reason"] = reason
            w.writerow(out)

    by_reason = {}
    for _, reason in rejected:
        by_reason[reason] = by_reason.get(reason, 0) + 1
    lines = [
        "CSV Rescue — run summary",
        "input file: %s" % os.path.basename(src),
        "rows in: %d" % len(raw_rows),
        "rows out (clean): %d" % len(clean),
        "rows rejected: %d" % len(rejected),
        "duplicates removed: %d" % duplicates,
        "rejections by reason:",
    ]
    for reason in sorted(by_reason):
        lines.append("  %s: %d" % (reason, by_reason[reason]))
    with open(os.path.join(out_dir, "run_summary.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")

    print("rows in: %d | clean: %d | rejected: %d | duplicates removed: %d"
          % (len(raw_rows), len(clean), len(rejected), duplicates))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

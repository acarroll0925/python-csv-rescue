# CSV Rescue — a rerunnable Python cleaning pipeline

Give it a messy CSV export. Get back a clean file, a report explaining every
row that couldn't be saved, and a summary of exactly what happened.
Nothing disappears silently.

Demo project. The sample data is fictional (Copperline Outdoor Supply);
the script is the real deliverable pattern.

## Quick start

```bash
python3 csv_rescue.py orders_messy.csv
```

Outputs (written next to the input, source file never modified):

| File | Contents |
|---|---|
| `clean.csv` | Normalized, deduplicated rows |
| `rejected_rows.csv` | Every rejected row, original values intact, plus a `reason` column |
| `run_summary.txt` | Rows in / out / rejected, duplicates removed, rejections by reason |

**Requirements:** Python 3.9+. Standard library only — no pip installs.

## What it fixes

- **Duplicates** — exact and near-duplicates (whitespace/casing) on the key column
- **Dates** — `03/04/2026`, `Mar 4 2026`, `4-Mar-26` → ISO `2026-03-04`
- **Currency** — `$1,299.00`, `USD 45.50` → plain numbers
- **Casing/codes** — `Georgia`, `ga.` → `GA`; emails lowercased; names title-cased

## What it rejects (and why you'll know)

A row is rejected — never guessed at — when it has:

- a missing key field (`missing order_id`)
- an unparseable or non-date value (`unparseable date: 'TBD'`)
- a malformed email, or a negative quantity
- any value the script cannot normalize with certainty

Each rejected row keeps its original values and gains a plain-English
`reason`. Rejection counts by reason are in `run_summary.txt`.

If the file is missing a required column entirely, the script stops with a
single clear error and writes **no** partial output.

## Guarantees

- **Rerunnable** — same input produces byte-identical outputs
- **Non-destructive** — the source file is opened read-only
- **No silent drops** — rows in = clean rows + rejected rows + duplicates removed

## Files

- `csv_rescue.py` — the pipeline
- `generate_messy_data.py` — regenerates the sample dataset (seeded, reproducible)
- `orders_messy.csv` — sample input with a known defect census
- `sample_output/` — expected outputs for the sample input

## Using it on your file

Required columns for the orders profile: `order_id, order_date, customer_name,
email, state, product, quantity, unit_price`. Column profiles for other exports
(CRM contacts, inventory, payouts) are a configuration change at the top of
the script — that's the client version of this demo.

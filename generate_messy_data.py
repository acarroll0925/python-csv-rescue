#!/usr/bin/env python3
"""Generate orders_messy.csv for the CSV Rescue demo.

Fictional business: Copperline Outdoor Supply. Every name, email, and order
is invented. The file is seeded with a KNOWN defect census so the cleaning
script's output can be verified against exact expected counts:

  rows in file ............ 120
  exact duplicates ........ 8   (byte-identical copies of earlier rows)
  near duplicates ......... 4   (same order_id; whitespace/casing drift)
  missing email ........... 5   -> rejected
  malformed email ......... 3   -> rejected
  unparseable date ........ 2   ('TBD', 'next week') -> rejected
  negative quantity ....... 2   -> rejected
  missing order_id ........ 1   -> rejected
  expected clean rows ..... 120 - 12 duplicates - 13 rejected = 95

Run:  python3 generate_messy_data.py   (writes orders_messy.csv beside it)
Seeded RNG: the file is reproducible byte for byte.
"""
import csv
import os
import random

random.seed(20261030)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "orders_messy.csv")

FIRST = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
         "Linda", "David", "Elizabeth", "William", "Barbara", "Richard",
         "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen",
         "Daniel", "Nancy", "Matthew", "Lisa", "Anthony", "Betty", "Mark",
         "Margaret", "Donald", "Sandra"]
LAST = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
        "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson",
        "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez",
        "Clark", "Lewis", "Robinson", "Walker"]
PRODUCTS = [("Ridgeline 3P Tent", 289.00), ("Trailhead 65L Pack", 179.50),
            ("Meridian Boots", 139.95), ("Ember Down Jacket", 219.00),
            ("Cascade Rain Shell", 129.00), ("Summit Trek Poles", 64.50),
            ("Basecamp Lantern", 39.95), ("Drift Sleeping Bag", 159.00),
            ("Ridgeline 2P Tent", 229.00), ("Trailhead 45L Pack", 139.50),
            ("Ember Insulated Vest", 119.00), ("Cascade Dry Duffel", 89.95),
            ("Summit Insoles", 34.50), ("Basecamp Stove Kit", 74.00),
            ("Drift Hammock", 59.95), ("Meridian Trail Shoes", 119.95)]
STATES = [("GA", "Georgia"), ("TN", "Tennessee"), ("AL", "Alabama"),
          ("FL", "Florida"), ("SC", "South Carolina"), ("NC", "North Carolina"),
          ("TX", "Texas"), ("CA", "California")]

HEADER = ["order_id", "order_date", "customer_name", "email", "state",
          "product", "quantity", "unit_price"]


def money_variants(amount):
    """Return several renderings of the same amount; [0] is canonical."""
    return ["%.2f" % amount,
            "$%s" % format(amount, ",.2f"),
            "USD %.2f" % amount,
            "%d" % amount if amount == int(amount) else "%.2f" % amount]


def date_variants(y, m, d):
    """Four renderings of one date; index 0 = ISO. All unambiguous US forms."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return ["%04d-%02d-%02d" % (y, m, d),
            "%02d/%02d/%04d" % (m, d, y),
            "%s %d %04d" % (months[m - 1], d, y),
            "%d-%s-%02d" % (d, months[m - 1], y % 100)]


rows = []

# --- 95 valid, unique orders (the expected clean.csv population) -----------
# Format-drift counters guarantee the >= minimums in the SPEC census:
# >=6 non-ISO dates, >=8 non-plain currency values, >=6 non-code states.
for i in range(95):
    oid = "CO-%04d" % (1001 + i)
    first = random.choice(FIRST)
    last = random.choice(LAST)
    product, price = random.choice(PRODUCTS)
    code, fullname = random.choice(STATES)
    y, m, d = 2026, random.randint(1, 9), random.randint(1, 28)

    date_s = date_variants(y, m, d)[i % 4]              # 71 non-ISO dates
    state_s = [code, fullname, code.lower() + "."][i % 3]  # 63 non-code
    price_s = money_variants(price)[i % 4]              # 71 non-plain

    name = "%s %s" % (first, last)
    if i % 5 == 0:
        name = name.upper()
    email = "%s.%s%d@example.com" % (first.lower(), last.lower(), i)
    if i % 4 == 0:
        email = email.upper()
    rows.append([oid, date_s, name, email, state_s, product,
                 str(random.randint(1, 4)), price_s])

base = list(rows)

# --- 8 exact duplicates ------------------------------------------------------
for idx in (3, 17, 28, 41, 52, 66, 77, 89):
    rows.append(list(base[idx]))

# --- 4 near duplicates (same order_id, whitespace / casing drift) -----------
for idx in (9, 33, 58, 83):
    r = list(base[idx])
    r[2] = "  " + r[2].title() + " "        # padded, re-cased name
    r[3] = r[3].upper()                      # shouted email
    r[4] = r[4] + " "                        # trailing space on state
    rows.append(r)

# --- 13 rejected rows, exactly one defect each ------------------------------
def defect(**over):
    r = ["CO-9%03d" % random.randint(100, 999), "2026-05-14", "Test Buyer",
         "test.buyer@example.com", "GA", "Ridgeline 3P Tent", "1", "289.00"]
    for k, v in over.items():
        r[HEADER.index(k)] = v
    return r

for n in range(5):   # missing email
    rows.append(defect(order_id="CO-91%02d" % n, email="",
                       customer_name="No Email %d" % n))
for n in range(3):   # malformed email
    rows.append(defect(order_id="CO-92%02d" % n,
                       email=["not-an-email", "missing-at.example.com".replace("missing-at", "missingat"),
                              "two@@example.com"][n],
                       customer_name="Bad Email %d" % n))
rows.append(defect(order_id="CO-9301", order_date="TBD",
                   customer_name="Date TBD"))
rows.append(defect(order_id="CO-9302", order_date="next week",
                   customer_name="Date Vague"))
rows.append(defect(order_id="CO-9401", quantity="-2",
                   customer_name="Negative Qty One"))
rows.append(defect(order_id="CO-9402", quantity="-1",
                   customer_name="Negative Qty Two"))
rows.append(defect(order_id="", customer_name="Missing Order Id"))

assert len(rows) == 120, len(rows)

random.shuffle(rows)

with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(HEADER)
    w.writerows(rows)

print("wrote %s (%d data rows)" % (OUT, len(rows)))
print("census: 95 valid + 8 exact dup + 4 near dup + 13 rejected = 120")

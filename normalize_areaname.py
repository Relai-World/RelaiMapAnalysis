"""
normalize_areaname.py
─────────────────────
Cleans the 'areaname' column in properties_final:
  1. Strips leading/trailing whitespace & tabs
  2. Resolves case-insensitive duplicates → picks the canonical form
     (whichever variant has the most rows, falling back to title-case)
  3. Applies a manual typo/spelling correction map
  4. Prints a full dry-run diff, then applies with a single transaction

Run:  python -X utf8 normalize_areaname.py
"""

import sys, psycopg2, os
from collections import defaultdict
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# ─────────────────────────────────────────────
# Manual spelling corrections  (wrong → right)
# Only Hyderabad + Bangalore locations in scope
# ─────────────────────────────────────────────
MANUAL_FIXES = {
    # Hyderabad typos / near-duplicates
    "Seriingampally":          "Serilingampally",
    "Serilingampally\t":       "Serilingampally",
    "Peeranchuruvu":           "Peeramcheruvu",
    "Gundlapochampally\t":     "Gundlapochampally",
    "Gundlapochampalli":       "Gundlapochampally",
    "quthbullapur":            "Quthbullapur",
    "suchitra":                "Suchitra",
    "gourelly":                "Gourelly",
    "mokila":                  "Mokila",
    "velmala":                 "Velmala",
    "shankarpalle":            "Shankarpalli",
    "Osman nagar":             "Osman Nagar",
    "Manikonda Road":          "Manikonda",
    "Hitec city":              "Hi Tech City",
    "Hi Tech City":            "Hitech City",
    "Hi tech City":            "Hitech City",
    "Hitech City":             "Hitech City",
    # Bangalore typos / near-duplicates
    "AnjanaPura":              "Anjanapura",
    "jakkuru":                 "Jakkur",
    "Hosahalli":               "Hosahalli",     # keep as-is (both same)
    "ittamadu":                "Ittamadu",
    "thyayakana halli":        "Thyagarajanagar",  # leave as-is if unsure
    "Bengaluru urban":         "Bengaluru Urban",
    "MAHADEVAPURA ZONE":       "Mahadevapura",
    "TALAGHATTAPURA":          "Talaghattapura",
    "Thambu Chetty Palya,":    "Thambu Chetty Palya",
    "UTTARAHALLI":             "Uttarahalli",
    "UTTARHALLI HOBLI":        "Uttarahalli Hobli",
    "YELAHANKA":               "Yelahanka",
    "BIDARAHALLI":             "Bidarahalli",
    "BOMMANAHALLI":            "Bommanahalli",
    "KEMPALINGAPURA":          "Kempalingapura",
    "K.R.PURAM":               "KR Puram",
    "Sahakara Nagar":          "Sahakar Nagar",
    "CHIKKANAYAKANAHALLI":     "Chikkanayakanhalli",
    "Konadasapura":            "Konadasapura",  # keep
    "KANNAMANGALA":            "Kannamangala",
    "VARTHUR":                 "Varthur",
    "SARJAPURA":               "Sarjapura",
    "Sarjapur":                "Sarjapura",
    "Sarjapur Road":           "Sarjapura Road",
}

def connect():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'post@123'),
        dbname=os.getenv('DB_NAME', 'real_estate_intelligence'),
        port=os.getenv('DB_PORT', '5432'),
        sslmode='prefer'
    )

def build_normalization_map(cur):
    """
    Returns dict: original_value → normalized_value
    Only includes values that will actually change.
    """
    cur.execute("""
        SELECT areaname, COUNT(*) AS cnt
        FROM properties_final
        WHERE areaname IS NOT NULL
        GROUP BY areaname
        ORDER BY cnt DESC, areaname;
    """)
    rows = cur.fetchall()          # [(value, count), ...]
    all_vals = {v: c for v, c in rows}

    changes = {}   # old → new

    # ── Pass 1: trim whitespace / tabs ──────────────────────────
    for val in list(all_vals.keys()):
        stripped = val.strip()
        if stripped != val:
            changes[val] = stripped

    # ── Pass 2: manual fixes ─────────────────────────────────────
    for val in list(all_vals.keys()):
        effective = changes.get(val, val)   # use already-stripped if applicable
        if effective in MANUAL_FIXES:
            target = MANUAL_FIXES[effective]
            if target != val:
                changes[val] = target

    # ── Pass 3: case-insensitive grouping ────────────────────────
    # Group all values (after applying known changes so far) by lowercase
    # Pick the "winner" = variant with highest original row count
    groups = defaultdict(list)
    for val, cnt in all_vals.items():
        effective = changes.get(val, val)
        groups[effective.lower()].append((effective, cnt, val))

    for lower_key, variants in groups.items():
        if len(variants) <= 1:
            continue
        # Sort by count desc, then by "looks proper" (title case) desc
        def score(t):
            eff, cnt, orig = t
            return (cnt, eff == eff.title())
        variants.sort(key=score, reverse=True)
        winner = variants[0][0]
        for eff, cnt, orig in variants:
            if eff != winner:
                changes[orig] = winner

    # Remove no-ops
    changes = {k: v for k, v in changes.items() if k != v}
    return changes, all_vals

def main():
    conn = connect()
    cur  = conn.cursor()

    changes, all_vals = build_normalization_map(cur)

    if not changes:
        print("✅  No changes needed — areaname is already clean.")
        cur.close(); conn.close(); return

    # ── Dry-run report ───────────────────────────────────────────
    print(f"{'='*72}")
    print(f"  DRY RUN — {len(changes)} areaname values will be normalized")
    print(f"{'='*72}")
    print(f"  {'CURRENT VALUE':<45} → {'NEW VALUE':<35} | Rows affected")
    print(f"  {'-'*45}   {'-'*35}-+-------------")
    total_rows = 0
    for old, new in sorted(changes.items(), key=lambda x: all_vals.get(x[0], 0), reverse=True):
        cnt = all_vals.get(old, 0)
        total_rows += cnt
        print(f"  {repr(old):<45} → {repr(new):<35} | {cnt}")

    print(f"\n  Total rows that will be updated: {total_rows}")
    print(f"{'='*72}\n")

    # ── Confirm before applying ──────────────────────────────────
    ans = input("Apply these changes to the database? [y/N]: ").strip().lower()
    if ans != 'y':
        print("Aborted — no changes made.")
        cur.close(); conn.close(); return

    # ── Apply inside a transaction ───────────────────────────────
    print("\nApplying normalizations...")
    updated_total = 0
    try:
        for old, new in changes.items():
            cur.execute("""
                UPDATE properties_final
                SET areaname = %s
                WHERE areaname = %s
            """, (new, old))
            updated_total += cur.rowcount
        conn.commit()
        print(f"\n✅  Done!  {updated_total} rows updated across {len(changes)} areaname variants.")
    except Exception as e:
        conn.rollback()
        print(f"\n❌  Error: {e}\n    Rolling back — no changes made.")

    # ── Final unique count ───────────────────────────────────────
    cur.execute("SELECT COUNT(DISTINCT TRIM(areaname)) FROM properties_final WHERE areaname IS NOT NULL;")
    final_count = cur.fetchone()[0]
    print(f"    Unique areaname values after cleanup: {final_count}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()

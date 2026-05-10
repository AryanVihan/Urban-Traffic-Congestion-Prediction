"""
supabase_upload.py
------------------
One-time script: uploads Metro_Interstate_Traffic_Volume.csv to Supabase.

Prerequisites
-------------
1. Run supabase_setup.sql in the Supabase SQL Editor first.
2. Create a .env file with SUPABASE_URL and SUPABASE_SERVICE_KEY.
   Use the SERVICE ROLE key here (not the anon key) — it bypasses RLS
   and allows INSERT.

Usage
-----
    python supabase_upload.py
    python supabase_upload.py --csv path/to/other.csv
    python supabase_upload.py --batch-size 500 --dry-run
"""

import argparse
import os
import sys
import time

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_CSV   = os.path.join(os.path.dirname(__file__), "Metro_Interstate_Traffic_Volume.csv")
TABLE_NAME    = "traffic_volume"
DEFAULT_BATCH = 500      # rows per upsert call (Supabase recommends ≤1000)


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_and_clean_csv(path: str) -> pd.DataFrame:
    print(f"Loading CSV: {path}")
    df = pd.read_csv(path)

    # Ensure date_time is ISO-8601 string for Supabase JSON transport
    df["date_time"] = pd.to_datetime(df["date_time"]).dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    # Fill NaN holiday (Supabase JSON does not accept NaN)
    df["holiday"] = df["holiday"].fillna("None")

    # Ensure numeric columns have no NaN
    numeric_cols = ["temp", "rain_1h", "snow_1h", "clouds_all", "traffic_volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Clip rain outlier (same as data_processing.clean)
    df["rain_1h"] = df["rain_1h"].clip(upper=50.0)

    # Drop duplicates
    df = df.drop_duplicates().reset_index(drop=True)

    print(f"  Rows after cleaning: {len(df):,}")
    return df


def upload(df: pd.DataFrame, client, batch_size: int, dry_run: bool) -> None:
    records = df.to_dict(orient="records")
    total   = len(records)
    batches = (total + batch_size - 1) // batch_size

    print(f"\nUploading {total:,} rows in {batches} batches of {batch_size}…")
    if dry_run:
        print("  DRY RUN — no data will be written.\n")

    errors = 0
    for i in range(0, total, batch_size):
        batch = records[i : i + batch_size]
        batch_num = i // batch_size + 1

        if dry_run:
            print(f"  [dry] Batch {batch_num}/{batches} ({len(batch)} rows) — skipped")
            continue

        try:
            client.table(TABLE_NAME).insert(batch).execute()
            pct = (i + len(batch)) / total * 100
            print(f"  Batch {batch_num}/{batches} — {i + len(batch):,}/{total:,} rows ({pct:.1f}%)")
        except Exception as exc:
            print(f"  ERROR on batch {batch_num}: {exc}")
            errors += 1
            if errors >= 3:
                print("Too many errors — aborting.")
                sys.exit(1)

        # Brief pause to avoid hitting Supabase rate limits
        time.sleep(0.1)

    if not dry_run:
        print(f"\nDone. {total:,} rows uploaded to '{TABLE_NAME}'.")


# ── Verify ────────────────────────────────────────────────────────────────────

def verify(client) -> None:
    print("\nVerifying row count in Supabase…")
    resp  = client.table(TABLE_NAME).select("id", count="exact").execute()
    count = resp.count
    print(f"  Rows in '{TABLE_NAME}': {count:,}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Upload traffic CSV to Supabase.")
    parser.add_argument("--csv",        default=DEFAULT_CSV, help="Path to CSV file")
    parser.add_argument("--batch-size", default=DEFAULT_BATCH, type=int)
    parser.add_argument("--dry-run",    action="store_true", help="Parse and print only — no inserts")
    args = parser.parse_args()

    # Credentials — must use SERVICE ROLE key for writes
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        sys.exit(1)

    client = create_client(url, key)

    df = load_and_clean_csv(args.csv)
    upload(df, client, args.batch_size, args.dry_run)

    if not args.dry_run:
        verify(client)


if __name__ == "__main__":
    main()

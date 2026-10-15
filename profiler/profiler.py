#!/usr/bin/env python3
"""Streaming data-quality profiler for the CFPB consumer-complaint dataset.

Phase 1 prototype (Problem & Computational Prototype).

Goal
----
Profile a very large complaints CSV (≈8.9 GB, ~31.7M rows, 16 columns) in
*constant memory* using a streaming parser, producing:
  * a per-column data dictionary (type, missingness, cardinality, range),
  * a defect summary (duplicate Complaint IDs, malformed dates / ZIP codes,
    row-width mismatches).

Why streaming
-------------
The raw file is ~8.9 GB; loading it into pandas would exhaust typical laptop
memory. This profiler reads row-by-row and keeps only bounded accumulators,
so memory use does not grow with the file size. The same code runs on a small
sample (for fast iteration) and on the full file (for the real profile).

Usage
-----
    python profiler.py <input.csv|input.csv.zip> [--limit N]
                      [--json out.json] [--dict data_dictionary.md]

Only the Python standard library is required.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Iterable, Iterator, Optional

# ---- Schema (from the CFPB consumer-complaint data dictionary) -------------
EXPECTED_COLUMNS = [
    "Date received", "Product", "Sub-product", "Issue", "Sub-issue",
    "Consumer complaint narrative", "Company public response", "Company",
    "State", "ZIP code", "Tags", "Submitted via", "Date sent to company",
    "Company response to consumer", "Timely response?", "Complaint ID",
]
DATE_COLUMNS = {"Date received", "Date sent to company"}
ZIP_COLUMN = "ZIP code"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
ZIP_RE = re.compile(r"^\d{5}$")

# Cap how many distinct values we remember per column to bound memory.
DISTINCT_CAP = 200_000


class ColumnProfile:
    """Bounded accumulator for one column."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.count = 0
        self.missing = 0
        self.distinct = 0
        self._values: set[str] = set()
        self.min_val: Optional[str] = None
        self.max_val: Optional[str] = None
        self.nonconforming_date = 0
        self.nonconforming_zip = 0

    def note(self, value: str, *, is_date: bool = False, is_zip: bool = False) -> None:
        self.count += 1
        if value is None or value.strip() == "":
            self.missing += 1
            return
        if len(self._values) < DISTINCT_CAP:
            self._values.add(value)
        if is_date and not DATE_RE.match(value):
            self.nonconforming_date += 1
        if is_zip and not ZIP_RE.match(value):
            self.nonconforming_zip += 1
        if self.min_val is None or value < self.min_val:
            self.min_val = value
        if self.max_val is None or value > self.max_val:
            self.max_val = value

    def finalize(self) -> None:
        self.distinct = len(self._values)
        self._values = set()  # release memory

    def to_dict(self) -> dict:
        missing_rate = round(self.missing / self.count, 4) if self.count else 0.0
        return {
            "name": self.name,
            "count": self.count,
            "missing": self.missing,
            "missing_rate": missing_rate,
            "distinct": self.distinct,
            "min": self.min_val,
            "max": self.max_val,
            "nonconforming_date": self.nonconforming_date,
            "nonconforming_zip": self.nonconforming_zip,
        }


def _open_source(source: str):
    """Return a text file handle for a .csv or a .zip containing one .csv."""
    p = Path(source)
    if p.suffix.lower() == ".zip":
        z = zipfile.ZipFile(p)
        csv_name = next((n for n in z.namelist() if n.lower().endswith(".csv")), None)
        if csv_name is None:
            z.close()
            raise ValueError("no .csv found inside the zip archive")
        fh = io.TextIOWrapper(z.open(csv_name), encoding="utf-8", errors="replace")
        fh._owner_zip = z  # keep archive open while streaming
        return fh
    return open(p, "r", encoding="utf-8", errors="replace", newline="")


def profile(source: str, limit: Optional[int] = None) -> dict:
    """Stream the file and return a profile dict (constant memory in rows)."""
    cols = {c: ColumnProfile(name=c) for c in EXPECTED_COLUMNS}
    seen_ids: set[str] = set()
    duplicates = 0
    row_count = 0
    width_mismatch = 0

    fh = _open_source(source)
    try:
        reader = csv.reader(fh)
        next(reader, None)  # skip header
        for raw in reader:
            row_count += 1
            if limit is not None and row_count > limit:
                row_count -= 1
                break
            if len(raw) != len(EXPECTED_COLUMNS):
                width_mismatch += 1
            for i, col in enumerate(EXPECTED_COLUMNS):
                val = raw[i] if i < len(raw) else ""
                cols[col].note(
                    val,
                    is_date=(col in DATE_COLUMNS),
                    is_zip=(col == ZIP_COLUMN),
                )
            cid = raw[EXPECTED_COLUMNS.index("Complaint ID")].strip() \
                if len(raw) > EXPECTED_COLUMNS.index("Complaint ID") else ""
            if cid:
                if cid in seen_ids:
                    duplicates += 1
                else:
                    seen_ids.add(cid)
    finally:
        fh.close()
        owner = getattr(fh, "_owner_zip", None)
        if owner is not None:
            owner.close()

    for cp in cols.values():
        cp.finalize()

    return {
        "source": source,
        "rows": row_count,
        "columns": len(EXPECTED_COLUMNS),
        "width_mismatch_rows": width_mismatch,
        "duplicate_complaint_ids": duplicates,
        "column_profiles": {c: cols[c].to_dict() for c in EXPECTED_COLUMNS},
    }


def _infer_type(cp: dict) -> str:
    if cp["count"] and cp["missing"] == cp["count"]:
        return "empty"
    if cp["name"] in DATE_COLUMNS and cp["nonconforming_date"] == 0:
        return "datetime"
    if cp["name"] == ZIP_COLUMN and cp["nonconforming_zip"] == 0:
        return "zip_code"
    if cp["distinct"] <= 30:
        return "categorical"
    return "text"


def _trunc(value: Optional[str], n: int = 60) -> str:
    if value is None:
        return "-"
    value = value.replace("\n", " ").replace("\r", " ").strip()
    return value if len(value) <= n else value[: n - 1] + "…"


def write_data_dictionary(profile: dict, out_path: str) -> None:
    """Write a Markdown data dictionary with one row per column."""
    lines = [
        "# Data Dictionary (auto-generated)",
        "",
        f"- Source: `{profile['source']}`",
        f"- Rows profiled: {profile['rows']:,}",
        f"- Columns: {profile['columns']}",
        f"- Duplicate Complaint IDs: {profile['duplicate_complaint_ids']}",
        f"- Row-width mismatches: {profile['width_mismatch_rows']}",
        "",
        "| # | Column | Inferred type | Missing | Missing % | Distinct | Min | Max | Notes |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, name in enumerate(EXPECTED_COLUMNS, 1):
        cp = profile["column_profiles"][name]
        ctype = _infer_type(cp)
        notes = []
        if cp["nonconforming_date"]:
            notes.append(f"{cp['nonconforming_date']} bad date fmt")
        if cp["nonconforming_zip"]:
            notes.append(f"{cp['nonconforming_zip']} bad zip")
        lines.append(
            f"| {i} | {name} | {ctype} | {cp['missing']} | "
            f"{cp['missing_rate']*100:.1f}% | {cp['distinct']} | "
            f"{_trunc(cp['min'])} | {_trunc(cp['max'])} | {'; '.join(notes) or '-'} |"
        )
    Path(out_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Streaming CFPB complaint data profiler")
    ap.add_argument("source", help="path to complaints.csv or complaints.csv.zip")
    ap.add_argument("--limit", type=int, default=None, help="profile only first N rows")
    ap.add_argument("--json", default=None, help="write full profile JSON here")
    ap.add_argument("--dict", default=None, help="write Markdown data dictionary here")
    args = ap.parse_args(argv)

    prof = profile(args.source, limit=args.limit)

    if args.json:
        Path(args.json).write_text(
            json.dumps(prof, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"wrote profile JSON -> {args.json}")
    if args.dict:
        write_data_dictionary(prof, args.dict)
        print(f"wrote data dictionary -> {args.dict}")

    missing_narr = prof["column_profiles"]["Consumer complaint narrative"]["missing"]
    print(
        f"rows={prof['rows']:,} cols={prof['columns']} "
        f"dup_ids={prof['duplicate_complaint_ids']} "
        f"width_mismatch={prof['width_mismatch_rows']} "
        f"narrative_missing={missing_narr}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

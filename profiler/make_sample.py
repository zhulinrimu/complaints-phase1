#!/usr/bin/env python3
"""Extract a small, reproducible sample from the full complaints archive.

The raw dataset is ~8.9 GB and cannot be committed to Git. This script
documents *how* the sample in ../data/sample_complaints.csv was produced so
anyone can regenerate it. Phase 1 work runs on the sample; the full file is
reserved for Phase 2/3 where streaming profiling is demonstrated.

Usage:
    python make_sample.py --source complaints.csv.zip --out ../data/sample_complaints.csv --limit 800
"""
import argparse
import csv
import zipfile
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="complaints.csv.zip",
                    help="path to the full complaints.csv.zip")
    ap.add_argument("--out", default="../data/sample_complaints.csv")
    ap.add_argument("--limit", type=int, default=800)
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.source) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        with z.open(name) as f, open(out, "w", encoding="utf-8", newline="") as g:
            g.write(f.readline().decode("utf-8"))  # header
            for i, line in enumerate(f):
                if i >= args.limit:
                    break
                g.write(line.decode("utf-8"))
    print(f"wrote {args.limit} data rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

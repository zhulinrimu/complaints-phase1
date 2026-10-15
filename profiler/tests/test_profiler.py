"""Unit + boundary tests for the streaming complaint profiler (Phase 1).

Run with:  pytest -q
"""
import sys
from pathlib import Path

# Make the profiler module importable when running tests from any directory.
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "profiler"))

import pytest

from profiler import (  # noqa: E402
    EXPECTED_COLUMNS,
    profile,
    write_data_dictionary,
    _open_source,
)

SAMPLE = REPO_ROOT / "data" / "sample_complaints.csv"


def _write_csv(path: Path, rows: list[list[str]]) -> None:
    import csv

    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(EXPECTED_COLUMNS)
        for r in rows:
            w.writerow(r)


GOOD = ["2024-01-25T19:56:56.000Z", "Credit reporting", "Credit reporting",
        "Incorrect information", "Account status", "some narrative text",
        "Company responded", "EQUIFAX, INC.", "TN", "38141", "", "Web",
        "2024-01-25T19:56:59.000Z", "Closed", "Yes", "8223945"]


def test_expected_columns_present_in_sample():
    prof = profile(str(SAMPLE), limit=200)
    assert prof["columns"] == 16
    assert set(prof["column_profiles"].keys()) == set(EXPECTED_COLUMNS)


def test_sample_profiles_without_error():
    prof = profile(str(SAMPLE), limit=300)
    assert prof["rows"] == 300
    # narrative column exists and is profiled
    assert "Consumer complaint narrative" in prof["column_profiles"]


def test_missing_value_detection(tmp_path):
    f = tmp_path / "miss.csv"
    _write_csv(f, [["2024-01-01T00:00:00.000Z", "Product", "Sub", "Issue", "Sub",
                    "", "resp", "Co", "NY", "10001", "", "Web",
                    "2024-01-01T00:00:00.000Z", "Closed", "Yes", "1"]])
    prof = profile(str(f))
    cp = prof["column_profiles"]["Consumer complaint narrative"]
    assert cp["missing"] == 1
    assert cp["missing_rate"] == 1.0


def test_duplicate_complaint_id_detection(tmp_path):
    f = tmp_path / "dup.csv"
    r2 = list(GOOD)
    r2[-1] = "8223945"  # same Complaint ID as GOOD
    _write_csv(f, [GOOD, r2])
    prof = profile(str(f))
    assert prof["duplicate_complaint_ids"] == 1


def test_bad_date_format_flagged(tmp_path):
    f = tmp_path / "baddate.csv"
    bad = list(GOOD)
    bad[0] = "01/25/2024"  # not ISO-8601
    _write_csv(f, [bad])
    prof = profile(str(f))
    assert prof["column_profiles"]["Date received"]["nonconforming_date"] == 1


def test_bad_zip_format_flagged(tmp_path):
    f = tmp_path / "badzip.csv"
    bad = list(GOOD)
    bad[EXPECTED_COLUMNS.index("ZIP code")] = "12"  # not 5 digits
    _write_csv(f, [bad])
    prof = profile(str(f))
    assert prof["column_profiles"]["ZIP code"]["nonconforming_zip"] == 1


def test_row_width_mismatch_detected(tmp_path):
    f = tmp_path / "width.csv"
    _write_csv(f, [GOOD[:15]])  # one column short
    prof = profile(str(f))
    assert prof["width_mismatch_rows"] == 1


def test_streaming_limit_is_constant_in_rows(tmp_path):
    f = tmp_path / "lim.csv"
    _write_csv(f, [GOOD for _ in range(50)])
    prof = profile(str(f), limit=10)
    assert prof["rows"] == 10


def test_empty_file_does_not_crash(tmp_path):
    f = tmp_path / "empty.csv"
    _write_csv(f, [])  # header only
    prof = profile(str(f))
    assert prof["rows"] == 0
    assert prof["duplicate_complaint_ids"] == 0


def test_profile_is_reproducible(tmp_path):
    f = tmp_path / "repro.csv"
    _write_csv(f, [GOOD, GOOD])
    p1 = profile(str(f))
    p2 = profile(str(f))
    assert p1 == p2


def test_data_dictionary_written(tmp_path):
    f = tmp_path / "dd.csv"
    _write_csv(f, [GOOD])
    prof = profile(str(f))
    out = tmp_path / "dd.md"
    write_data_dictionary(prof, str(out))
    text = out.read_text(encoding="utf-8")
    # one markdown table row per column + header rows
    assert text.count("|") > 0
    assert "Data Dictionary" in text

#!/usr/bin/env python3
"""Generate the missing-rate bar chart as a dependency-free SVG.

Reads data/profile_sample.json (produced by profiler.py) and writes
data/missing_rate.svg. Fully reproducible; no third-party libraries.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
prof = json.loads((ROOT / "data" / "profile_sample.json").read_text(encoding="utf-8"))

cols = prof["column_profiles"]  # ordered dict
order = [
    "Date received", "Product", "Sub-product", "Issue", "Sub-issue",
    "Consumer complaint narrative", "Company public response", "Company",
    "State", "ZIP code", "Tags", "Submitted via", "Date sent to company",
    "Company response to consumer", "Timely response?", "Complaint ID",
]
labels_cn = {
    "Date received": "收到日期", "Product": "产品", "Sub-product": "子产品",
    "Issue": "问题类型", "Sub-issue": "子问题",
    "Consumer complaint narrative": "消费者叙述", "Company public response": "公司公开回应",
    "Company": "公司", "State": "州", "ZIP code": "邮编",
    "Tags": "标签", "Submitted via": "提交渠道",
    "Date sent to company": "发往公司日期", "Company response to consumer": "公司处理结论",
    "Timely response?": "及时响应?", "Complaint ID": "投诉ID",
}

rows = [(labels_cn.get(c, c), cols[c]["missing_rate"] * 100) for c in order]
rows.sort(key=lambda x: x[1])  # ascending so highest at top after flip? keep order; we draw top->bottom

W = 820
left = 210
bar_x = left + 10
bar_w = 470
row_h = 26
top = 44
H = top + len(rows) * row_h + 36

parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" '
         f'font-family="Segoe UI, Microsoft YaHei, sans-serif" font-size="13">']
parts.append(f'<text x="10" y="26" font-size="15" font-weight="bold">'
             f'图 1. 各列缺失率（样本 {prof["rows"]} 行）</text>')
for i, (label, pct) in enumerate(rows):
    y = top + i * row_h
    bar_len = bar_w * (pct / 100.0)
    parts.append(f'<text x="10" y="{y+16}" font-size="12">{label}</text>')
    parts.append(f'<rect x="{bar_x}" y="{y+3}" width="{bar_w}" height="16" fill="#eceff1"/>')
    color = "#c62828" if pct >= 50 else ("#ef6c00" if pct >= 10 else "#2e7d32")
    parts.append(f'<rect x="{bar_x}" y="{y+3}" width="{max(bar_len,1):.1f}" height="16" fill="{color}"/>')
    parts.append(f'<text x="{bar_x+bar_w+6}" y="{y+16}" font-size="12" fill="#333">{pct:.1f}%</text>')
parts.append('</svg>')

(ROOT / "data" / "missing_rate.svg").write_text("\n".join(parts), encoding="utf-8")
print("wrote data/missing_rate.svg with", len(rows), "bars")

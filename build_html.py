#!/usr/bin/env python3
"""Convert phase1_report_draft.md -> phase1_report.html (print-ready).

Dependency-free. Set @page margins to 2cm and base font 10.5pt / line 1.15
so the user can open it and "Print -> Save as PDF" to produce the submission.
A minimal Markdown subset is supported: # headings, > quotes, | tables |,
- lists, ``` code fences, and inline **bold** / `code` / ![img](src).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "phase1_report_draft.md"
OUT = ROOT / "phase1_report.html"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(s: str) -> str:
    s = esc(s)
    def _img(m):
        alt, src = m.group(1), m.group(2)
        if src.lower().endswith(".svg"):
            p = ROOT / src
            if p.exists():
                return f'<figure style="margin:6px 0">{p.read_text(encoding="utf-8")}</figure>'
        return f'<img src="{src}" alt="{alt}">'
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _img, s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def split_row(line: str):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return cells


def table_html(header, rows):
    th = "".join(f"<th>{inline(c)}</th>" for c in header)
    body = ""
    for r in rows:
        body += "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
    return f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"


def md_to_html(text: str) -> str:
    lines = text.split("\n")
    out, i, n = [], 0, len(lines)
    in_code, code_buf = False, []
    while i < n:
        line = lines[i]
        if line.startswith("```"):
            if not in_code:
                in_code, code_buf = True, []
            else:
                in_code = False
                out.append(f"<pre><code>{esc(chr(10).join(code_buf))}</code></pre>")
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue
        if line.startswith("> "):
            q = []
            while i < n and lines[i].startswith("> "):
                q.append(lines[i][2:].strip())
                i += 1
            out.append(f"<blockquote>{inline(' '.join(q))}</blockquote>")
            continue
        if line.startswith("|") and i + 1 < n and lines[i + 1].startswith("|") \
                and set(lines[i + 1].replace("|", "").strip()) <= set("-: "):
            header = split_row(line)
            i += 2
            trows = []
            while i < n and lines[i].startswith("|"):
                trows.append(split_row(lines[i]))
                i += 1
            out.append(table_html(header, trows))
            continue
        if re.match(r"^\s*-\s+", line):
            lbuf = []
            while i < n and re.match(r"^\s*-\s+", lines[i]):
                lbuf.append(lines[i].strip()[2:].strip())
                i += 1
            items = "".join(f"<li>{inline(x)}</li>" for x in lbuf)
            out.append(f"<ul>{items}</ul>")
            continue
        if line.strip() == "":
            i += 1
            continue
        out.append(f"<p>{inline(line)}</p>")
        i += 1
    return "\n".join(out)


CSS = """
<style>
@page { size: A4; margin: 2cm; }
body { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; font-size: 10.5pt;
       line-height: 1.15; color: #222; max-width: 17cm; margin: 0 auto; }
h1 { font-size: 18pt; text-align: center; }
h2 { font-size: 14pt; border-bottom: 1px solid #ccc; padding-bottom: 2px; }
h3 { font-size: 12pt; }
table { border-collapse: collapse; width: 100%; font-size: 9.5pt; margin: 6px 0; }
th, td { border: 1px solid #999; padding: 3px 6px; text-align: left; vertical-align: top; }
th { background: #f0f0f0; }
blockquote { border-left: 3px solid #c62828; padding: 4px 10px; color: #555;
             background: #fafafa; margin: 6px 0; }
pre { background: #f5f5f5; padding: 8px; overflow: auto; font-size: 9pt;
      border: 1px solid #e0e0e0; }
code { background: #f0f0f0; padding: 1px 3px; font-family: Consolas, monospace; }
img { max-width: 100%; display: block; margin: 6px auto; }
figure { margin: 6px 0; }
figure svg { display: block; max-width: 100%; height: auto; }
ul { margin: 4px 0; }
</style>
"""

html = ("<!DOCTYPE html><html lang=\"zh\"><head><meta charset=\"utf-8\">"
        "<title>阶段1报告 - CFPB投诉数据流式质量剖析器</title>" + CSS +
        "</head><body>" + md_to_html(SRC.read_text(encoding="utf-8")) +
        "</body></html>")
OUT.write_text(html, encoding="utf-8")
print("wrote", OUT, "(", len(html), "bytes )")

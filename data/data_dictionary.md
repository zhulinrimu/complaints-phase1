# Data Dictionary (auto-generated)

- Source: `C:/Users/z3412/WorkBuddy/2026-10-15-20-19-49/complaints_phase1/data/sample_complaints.csv`
- Rows profiled: 548
- Columns: 16
- Duplicate Complaint IDs: 0
- Row-width mismatches: 0

| # | Column | Inferred type | Missing | Missing % | Distinct | Min | Max | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | Date received | datetime | 0 | 0.0% | 490 | 2024-01-25T19:36:29.000Z | 2026-02-16T22:36:49.000Z | - |
| 2 | Product | categorical | 0 | 0.0% | 11 | Checking or savings account | Vehicle loan or lease | - |
| 3 | Sub-product | categorical | 0 | 0.0% | 28 | Auto debt | Virtual currency | - |
| 4 | Issue | text | 0 | 0.0% | 40 | Applying for a mortgage or refinancing an existing mortgage | Written notification about debt | - |
| 5 | Sub-issue | text | 21 | 3.8% | 66 | Account information incorrect | You told them to stop contacting you, but they keep trying | - |
| 6 | Consumer complaint narrative | text | 487 | 88.9% | 61 | As of XX/XX/XXXX, I have reached 120 payments on my student… | was enrolled at XXXX but decided not to attend the classes.… | - |
| 7 | Company public response | categorical | 372 | 67.9% | 6 | Company believes complaint caused principally by actions of… | Company has responded to the consumer and the CFPB and choo… | - |
| 8 | Company | text | 0 | 0.0% | 162 | AMERICA FIRST FEDERAL CREDIT UNION | Your Favorite Lenders, Inc | - |
| 9 | State | text | 2 | 0.4% | 38 | AL | WY | - |
| 10 | ZIP code | text | 4 | 0.7% | 381 | 009XX | XXXXX | 55 bad zip |
| 11 | Tags | categorical | 509 | 92.9% | 3 | Older American | Servicemember | - |
| 12 | Submitted via | categorical | 0 | 0.0% | 3 | Phone | Web | - |
| 13 | Date sent to company | datetime | 2 | 0.4% | 507 | 2024-01-25T19:56:42.000Z | 2026-06-29T15:42:05.000Z | - |
| 14 | Company response to consumer | categorical | 217 | 39.6% | 4 | Closed with explanation | Untimely response | - |
| 15 | Timely response? | categorical | 0 | 0.0% | 2 | No | Yes | - |
| 16 | Complaint ID | text | 4 | 0.7% | 544 | 10143247 | 9993327 | - |

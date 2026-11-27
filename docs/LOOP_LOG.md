# Loop log

| Slice | PR | Loops | Must-fix found | Repeat issues | Status |
|---|---|---|---|---|---|
| Hard-rule fixes (city, email, Python labels, job lines, AI ops credits) | #5 | 1 | 3: "I rebuilt" wording on benefits page; city still in resume PDF; "rebuilt" on projects card | none | Merged. Resume PDF city still open |
| Home first screen (descriptions hidden, titles match, DAX KPI linked, "enterprise BI" cut) | #7 | 1 | 2: "enterprise BI" still in site-wide description in _quarto.yml; LOOP_LOG published as a site page (left by #5) | none | Merged |
| Guardrails (PR checks, pre-commit scan, gitignore, LF rules) | #8 | 1 | 0 | none | Merged |
| Benefits Power BI section (video, 3 report pages, 77 measures) | benefits-powerbi-section | 2 | Loop 1: Tie-outs exported with a month filter, Person detail with no person, Share of Impact at 100% on every row (filter not cleared on Next Step), truncated headline. Loop 2: cut-off tables on Roll-forward, Exceptions, Outstanding balances; Why this month not sorted, total vs headline mismatch | Cut-off visuals in PDF export (several pages, both loops) | In review; 4 pages held for Desktop fixes |

Totals: slices shipped 3 · average loops per slice 1.25 · repeat issues 1

## Standardize
- #5: new files under the repo root get published unless excluded. Check `_site/` for unexpected pages before every PR.
- Fix #2: when cutting a phrase, search config files (`_quarto.yml`) too, not just pages.
- #7: a rule that has to hold on every PR goes in site-checks, not in a checklist.
- Benefits Power BI: before any PDF export, clear slicers and size every table so it shows all rows and columns without scrolling.

# Loop log

| Slice | PR | Loops | Must-fix found | Repeat issues | Status |
|---|---|---|---|---|---|
| Hard-rule fixes (city, email, Python labels, job lines, AI ops credits) | #5 | 1 | 3: "I rebuilt" wording on benefits page; city still in resume PDF; "rebuilt" on projects card | none | Merged. Resume PDF city still open |
| Home first screen (descriptions hidden, titles match, DAX KPI linked, "enterprise BI" cut) | fix-home-first-screen | 1 | 2: "enterprise BI" still in site-wide description in _quarto.yml; LOOP_LOG published as a site page (left by #5) | none | In review |

Totals: slices shipped 1 · average loops per slice 1 · repeat issues 0

## Standardize
- #5: new files under the repo root get published unless excluded. Check `_site/` for unexpected pages before every PR.
- Fix #2: when cutting a phrase, search config files (`_quarto.yml`) too, not just pages.

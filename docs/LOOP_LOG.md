# Loop log

| Slice | PR | Loops | Must-fix found | Repeat issues | Status |
|---|---|---|---|---|---|
| Hard-rule fixes (city, email, Python labels, job lines, AI ops credits) | #5 | 1 | 3: "I rebuilt" wording on benefits page; city still in resume PDF; "rebuilt" on projects card | none | Merged. Resume PDF city still open |
| Home first screen (descriptions hidden, titles match, DAX KPI linked, "enterprise BI" cut) | #7 | 1 | 2: "enterprise BI" still in site-wide description in _quarto.yml; LOOP_LOG published as a site page (left by #5) | none | Merged |
| Guardrails (PR checks, pre-commit scan, gitignore, LF rules) | #8 | 1 | 0 | none | Merged |
| Benefits Power BI section (video, 3 report pages, 77 measures) | benefits-powerbi-section | 2 | Loop 1: Tie-outs exported with a month filter, Person detail with no person, Share of Impact at 100% on every row (filter not cleared on Next Step), truncated headline. Loop 2: cut-off tables on Roll-forward, Exceptions, Outstanding balances; Why this month not sorted, total vs headline mismatch | Cut-off visuals in PDF export (several pages, both loops) | Merged (#9); 4 pages held for Desktop fixes |
| What the business should do (all four projects) | business-should-do | 1 | 3: AI ops line named scans and CI the page doesn't show; benefits read as advice to a real employer (no "synthetic scenario" lead-in); "both end in refunds" not on the page | Claim beyond the page's proof (also in #5) | Merged (#11) |
| Resume request (interim) and About facts | resume-request-interim | 1 | 0 | none | Merged (#12) |
| Domain-move clean-up (site-url, static pages, old-URL test) | domain-move-cleanup | 1 | 0 | none | Merged (#13) |
| Total Rewards page refresh (Day 5 facts, CI labelled AI-built, cert path) | total-rewards-refresh | 2 | 3: "~2M rows" KPI read as done; stale "two-hour session"; Review 1 bug not tied to the study site | Claim beyond the page's proof (also in #5, #11) | Merged (#15) |
| Where I'm headed (About: target roles, cert path) | where-im-headed | 1 | 0 (2 nice-to-haves applied: "many" not "most"; AI-assisted label on the Power BI link) | none | Merged (#16) |
| AI-assisted labels (benefits, FP&A, Home and Projects cards; Total Rewards card tags) | benefits-ai-labels | 2 | 2: Projects meta description unlabelled; Home DAX KPI read as "AI did it" with his own catch left out | Label buried his own work (new) | In review |

Totals: slices shipped 9 · average loops per slice 1.3 · repeat issues 2

## Standardize
- #5: new files under the repo root get published unless excluded. Check `_site/` for unexpected pages before every PR.
- Fix #2: when cutting a phrase, search config files (`_quarto.yml`) too, not just pages.
- #7: a rule that has to hold on every PR goes in site-checks, not in a checklist.
- Benefits Power BI: before any PDF export, clear slicers and size every table so it shows all rows and columns without scrolling.
- Business sections: every recommendation quotes a figure already on its page; benefits copy always says "synthetic scenario".
- Total Rewards refresh: when a page summarizes another repo, re-read that repo's latest README and process changes first; stale details (session length, figures) are where it drifts.

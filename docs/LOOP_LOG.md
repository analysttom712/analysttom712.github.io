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
| AI-assisted labels (benefits, FP&A, Home and Projects cards; Total Rewards card tags) | benefits-ai-labels | 2 | 2: Projects meta description unlabelled; Home DAX KPI read as "AI did it" with his own catch left out | Label buried his own work (new) | Merged (#17) |
| Resume request form (posts to the resume-request AWS service) | resume-request-form | 1 | 3: linked repo empty until resume-request PR #1 merges; "every request is deleted" overstated (owner email stays in Gmail); "I built" without "directed" | Claim beyond the page's proof (also in #5, #11, #15) | Merged (#18) after resume-request #1 and SES production access |
| AI ops: Confidentiality panel (no employer tie-in) | ai-ops-wording | 2 | 3: "real report's layout copied" implied a real source; "stay away from real volumes" implied known real volumes; "employer's controls" pointed at an employer | Claim beyond the page's proof (also in #5, #11, #15, #18) | Merged (#19) |
| AI ops Credits (which ideas from which talk) | ai-ops-credits | 2 | 1: credited 8 ideas, the page shows about 4 (method read as borrowed); trimmed, the rest parked in #14 | Claim beyond the page's proof (also in #5, #11, #15, #18, #19) | Merged (#20) |
| Copy pass (unslop: "X, not Y" lines, maxims, closing coda, stray emphasis) | unslop-copy | 1 | 0 (checks only; no fresh-context recruiter or hiring-manager read run) | none | Merged (#21) |

Totals: slices shipped 14 · average loops per slice 1.4 · repeat issues 2 (claim beyond proof recurs: now 6 slices)

## Standardize
- #5: new files under the repo root get published unless excluded. Check `_site/` for unexpected pages before every PR.
- Fix #2: when cutting a phrase, search config files (`_quarto.yml`) too, not just pages.
- #7: a rule that has to hold on every PR goes in site-checks, not in a checklist.
- Benefits Power BI: before any PDF export, clear slicers and size every table so it shows all rows and columns without scrolling.
- Business sections: every recommendation quotes a figure already on its page; benefits copy always says "synthetic scenario".
- Total Rewards refresh: when a page summarizes another repo, re-read that repo's latest README and process changes first; stale details (session length, figures) are where it drifts.
- AI labels (#17): when a headline figure gets an AI-assisted label, pair it with what Thomas did himself in the same caption.
- Resume request form: a page that links to another repo as proof ships only after that repo's PR is merged; check the link target's main branch, not the feature branch.
- Claim beyond proof keeps returning: before any PR, list each claim the change adds and point to the line or artifact on the same page that proves it. Candidate for a site-checks step or a PR-template checklist.
- Copy pass (#21): run the unslop check on any copy change before the PR; at most one "X, not Y" contrast per page, and no closing maxim or realization line.

# Portfolio site agent: thomasbaynum.dev

## Role
You maintain Thomas Baynum's portfolio site. It exists to get him
hired in data management, data analytics, analytics engineering or
data engineering.

Positioning: an analyst who makes data trustworthy (reconciliation,
data quality checks, tie-outs) and is building toward analytics and
data engineering. Lead with what's proven; show engineering work as
in progress, never as experience he doesn't have yet. Keep the
tagline: "I make the numbers agree, and I show where they don't."

Map every page to the target roles:
- Data management: data quality checks, reconciliation logic, SOPs,
  governance of AI-assisted work.
- Data analytics: the benefits reconciliation and FP&A projects.
- Analytics engineering: the Total Rewards Analytics repo
  (github.com/analysttom712/total-rewards-analytics) as an
  in-progress project: pipeline, tests, CI, dbt planned.
- Data engineering: a short "where I'm headed" section with the cert
  path (GitHub Foundations, GH-900, now → PL-300 → AWS Cloud
  Practitioner → dbt Analytics Engineering; DP-600 optional), marked
  planned except the one in progress. The source of truth is
  docs/RESOURCES.md ("Cert path") in total-rewards-analytics; if they
  differ, that file wins and this line gets updated.
Every skill on the site must point to a project that uses it.

## Current state
- Quarto site in the analysttom712/analysttom712.github.io repo, on
  GitHub Pages. Moving to the custom domain thomasbaynum.dev.
- Pages: Home, Projects, About, Resume, Contact. Projects: benefits
  receivables reconciliation, AI operations and enablement, FP&A
  variance and forecast. Also /benefits-recon/, /dealer-pack/
  (/cat redirects there), and an unlisted YouTube walkthrough.

## Source of truth
Facts come only from the resume handoff files I give you
(RESUME-FACTS.md and the claim rules) and what I confirm. Never
invent numbers, skills or results. If a fact is missing, mark it
[NEED] and ask.

## Hard rules
- Public site: no employer name, member data, dollar figures or
  internal process detail. Projects are "built from scratch on
  invented data as a portfolio exercise," never "my work model
  rebuilt."
- Never mention the former side venture (see banned-terms.txt).
- Python is not a claimed skill. SQL is fundamentals/intermediate
  (DataCamp). AI-assisted work is labeled AI-assisted.
- No street address, phone or city on the site. Contact = email and
  LinkedIn.
- Every claim links to its proof (demo, file, repo, screenshot). A
  claim with no proof gets cut or softened.
- Every project ends with "What the business should do" in 2–3 lines.
- The AI operations page credits Matt Pocock's AI engineering
  workshop (https://youtu.be/-QFHIoCo-Ko) and Lydia Hallie's
  "Rethinking Claude Code Best Practices"
  (https://youtu.be/vlfCjWuv4es) for ideas I adapted.

## How we work (Lean + loops)
Value: the customer is a hiring manager for my target roles. Work
that doesn't help them see proof of my skills is waste.

Align first: before building anything new, ask me questions one at a
time, each with your recommended answer, then write a short brief:
goal, pages, out of scope, done criteria.

The board (pull, not push):
- Work lives in GitHub Issues: one slice per issue, blockers marked.
- WIP limit 1: finish and merge one slice before pulling the next.
- Only I add or reorder work. Your ideas go in a "Parking lot" issue.

Every slice runs one PDCA loop:
1. PLAN: goal, the proof it adds, and the done check, in 3 lines.
   I approve.
2. DO: build the smallest version that works end to end, on a branch.
3. CHECK (pass/fail): site renders, links work, public scan passes,
   every claim links to proof, then a fresh-session recruiter read
   (30 seconds, busy) and hiring-manager read.
4. ACT: fix must-fix items and loop back to CHECK. Stop after 3 loops,
   or if the same issue returns twice, and bring it to me. When it
   passes, I merge, and you write one line on what to standardize.

Cut the 8 wastes: overproduction (pages nobody asked for), waiting
(batch your questions), rework (fix causes; a repeated mistake
becomes a rule or check), overprocessing (stop at "proves the
skill"), inventory (merge or close half-done branches), motion (load
files only when needed), defects (unproven claims, broken links),
unused talent (my accounting and reconciliation strengths belong in
every project story).

Measure in docs/LOOP_LOG.md: slices shipped, loops per slice, repeat
issues. If loops per slice rise, slices are too big: split them.

## How I work with AI (a featured part of the site)
The AI operations and enablement project is where this lives. It
shows my method, with proof for each part:
- Align before building: question-by-question alignment, then a short
  brief with done criteria.
- Thin end-to-end slices on a kanban board, worked one at a time.
- Lean PDCA loops with pass/fail checks and a 3-loop stop rule;
  docs/LOOP_LOG.md from this repo is live proof.
- Critical rules enforced by tools, not wording: the public-repo scan,
  pre-commit hooks, CI that fails closed, branch protection. Proof:
  ADR-002/003 and the scanner in total-rewards-analytics.
- Fresh-context reviews (recruiter + hiring manager) before anything
  ships.
- Humans keep planning, review and merging; AI does the building.
- Honest labeling: AI-assisted work is called AI-assisted.

Rules for this page:
- Show, don't tell: link each part of the method to a real artifact
  (an ADR, a PR, the loop log, a review file). No artifact, no claim.
- Frame it for data roles: the same discipline that makes AI output
  trustworthy makes data trustworthy (gates, checks, reconciliation,
  audit trail).
- Credit Matt Pocock's AI engineering workshop
  (https://youtu.be/-QFHIoCo-Ko) and Lydia Hallie's "Rethinking Claude
  Code Best Practices" (https://youtu.be/vlfCjWuv4es) for the ideas I
  adapted.
- No employer data; the examples come from my public repos.

## Environment
Machine and tools
- Windows, PowerShell by default; Git Bash is fine for git.
- Quarto pinned to the version the site was built with (1.11.9 per
  page metadata). Check `quarto --version` at session start; if it
  differs, stop and ask before re-rendering.
- If a page runs Python or R, use a pinned venv/renv and Quarto's
  freeze so pages don't re-execute on every render.
- Local preview: `quarto preview` on a fixed port. Put the command
  and URL in the README.

Repo
- .gitignore: _site/, .quarto/, .venv/, *.local.*, .env.
- .gitattributes: LF line endings for scripts and hooks.
- A CNAME file containing thomasbaynum.dev in the published output.
- Check how the site deploys today (GitHub Actions vs a gh-pages
  branch) and keep one method only.

Safety
- Pre-commit hook running the public scan (secrets, home-folder
  paths, SSN-shaped numbers, AWS IDs, words in the local blocklist).
  Reuse scripts/public_scan.py from total-rewards-analytics.
- The blocklist file is gitignored; CI reads it from the
  SCAN_BLOCKLIST repository secret.
- CI on every PR: render, scan, broken-link check. Fail closed.
- main is protected (PR required, checks must pass, no force push).
  I merge. You never push to main.
- No API keys or tokens in the repo.

Permissions
- Ask before network access other than package installs and GitHub.
  Ask before deleting files.
- Never change DNS, repo settings or GitHub Pages settings yourself:
  give me the exact steps and values.

## Domain and DNS (Cloudflare)
- DNS is on Cloudflare. GitHub Pages records are "DNS only" (grey
  cloud) so GitHub can issue the HTTPS certificate. If the proxy is
  ever turned on, SSL/TLS mode must be Full (strict).
- A .dev domain only works over HTTPS: "Enforce HTTPS" must be on
  before the link is shared.
- Get the record values (apex A/AAAA records, www CNAME, the TXT
  record for domain verification) from GitHub's current Pages docs,
  not memory, and give them to me as a table.

## Keeping old links working
- Keep the site in the analysttom712.github.io repo so GitHub's
  user-site redirect sends every old URL to thomasbaynum.dev with the
  same path. Confirm this in the current GitHub Pages docs.
- Never rename or move a page without adding its old path under
  `aliases:` in its front matter. Keep /cat → /dealer-pack/.
- Before the switch, save a list of every current URL. After it, test
  each old URL and confirm it lands on the right page. Any failure
  blocks the release.
- After the switch, give me a checklist of places to update: resume
  header and base specs, LinkedIn, GitHub profile README, email
  signature, profile.md in my job hunting files.

## First session (in order, then stop)
1. Save this file as AGENTS.md (branch + PR; I merge).
2. Audit the live site:
   - The 30-second recruiter test: what you'd conclude, keep reading
     or move on, the first thing that made you doubt a claim.
   - Claims vs. proof table for every skill and number on the site.
   - The "so what" check for each project.
   - How well the site supports each of my 4 target roles (score 1–5
     each, with the reason).
   - Red flags, including: "35 DAX measures" and other headline
     claims with no evidence, Python/SQL listed on the benefits
     project, "Columbia, SC" location, the title vs og:title
     mismatch, raw metadata showing in the page, anything that
     breaks the hard rules.
3. Plan the domain move: the DNS table for Cloudflare, the CNAME
   file, HTTPS, domain verification, the old-URL test.
4. Propose the top 5 fixes ranked by impact per hour. Then wait for
   my pick.

# ERIS brain

This folder is the project's working memory. For every change it records what was built, why it was built that
way, what else was considered, what it costs, and how it was checked. It is written for the project owner, for
future contributors, and for any future work session on this repository.

## What this folder is, and what it is not

- It records **decisions, reasons, trade-offs and verification**.
- It does **not** reproduce moment-to-moment reasoning. Where a reason was never written down anywhere, the entry
  says so and gives the reason as *reconstructed* from commit messages, docs and code. Most work before 2026-10-01
  falls into that group, because the rebuild was the first time decisions were recorded alongside commits.
- Facts here were checked against the repository on 2026-10-24 (HEAD `8615f2e`, the merge of PR #32).

## Map

| File | Read it for |
|---|---|
| [01-timeline.md](01-timeline.md) | Every commit in order, grouped into eras, with what each one did |
| [02-decisions.md](02-decisions.md) | Architecture and product decisions, with reasons, alternatives and consequences |
| [03-features-and-pages.md](03-features-and-pages.md) | Every page and feature: what it does, why it exists, where the code lives |
| [04-backend.md](04-backend.md) | Routers, services, key functions and the logic inside them |
| [05-dataset.md](05-dataset.md) | The synthetic restaurant chain and how it is generated |
| [06-performance.md](06-performance.md) | Slow-page problems, their causes, the fixes and the measurements |
| [07-assistant.md](07-assistant.md) | The AI assistant: routing, grounding, caching and evaluation |
| [08-forecasting-and-analytics.md](08-forecasting-and-analytics.md) | Forecasting models, anomaly detection, driver analysis and their evaluation |
| [09-security-ci-deploy.md](09-security-ci-deploy.md) | Access control, CI hardening, Docker, hosting |
| [10-testing.md](10-testing.md) | Test suites, what each proves, and how to run them |
| [11-open-items.md](11-open-items.md) | Known gaps, doc discrepancies, and decisions waiting on the owner |
| [12-security-incident.md](12-security-incident.md) | Credentials found in repository history, their severity, and the owner actions still open |
| [13-hardening-and-pipelines.md](13-hardening-and-pipelines.md) | Dead code removed, open ports, security headers, TLS, rate limits, and the pipelines under load with measurements |
| [TEMPLATE.md](TEMPLATE.md) | The entry format for future changes |

## Standing rule for all future work

Every change requested from now on must, **in the same piece of work**:

1. Add an entry to `01-timeline.md`, using `TEMPLATE.md`.
2. Update the topic file it touches (a page in `03`, a service in `04`, a decision in `02`, and so on).
3. Record the reasoning: why this approach, what else was considered, what it costs, what it risks.
4. Record verification exactly as it was run, including anything that failed and how it was fixed.

The note is written before the commit is made, so the code and its explanation are committed together.

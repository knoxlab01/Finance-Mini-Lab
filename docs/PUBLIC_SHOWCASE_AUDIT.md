# Vexa Public Showcase / Admissions Audit

Audit date: **2026-10-16**. Source baseline: `a457e3d07cb6a86f713fbc41e00985e5eb4799ef` (`Prepare Vexa v0.4.0 release`). This report describes a local presentation refresh, not a new release, publication or certification of live availability.

## Repository and version

- At entry, `main`, `origin/main` and `v0.4-dev` pointed to the approved v0.4.0 commit; working tree clean.
- Work is isolated on `codex/vexa-public-showcase`. Stable main, repository name and URLs are unchanged. No commit/push/tag/release is part of this task.
- The local tag inventory contains only `v0.1.0`; absent local tags do not downgrade the implemented v0.4.0 code or establish remote Release status. No new version number is assigned.
- Source inventory: 142 tracked baseline files and 72 Python files parsed across application, research and tests. Key implementation paths were inspected, rather than inferring features from README.

```text
streamlit_app.py     web entry: global language, planning and portfolio tabs
app.py               independent CLI compound calculator
src/                 planning, analytics, data, simulation and presentation
src/evolance/        preserved v1 / frozen v1.1 rules
research/            offline validation, derived results and private-input loader
tests/               unit, UI, data, research and regression tests
docs/                methodology, frozen specification, reports and release history
assets/              five approved product PNGs
requirements*.txt    runtime and test dependencies
```

## Implemented capabilities and boundaries

| Area | Code evidence and actual behavior |
| --- | --- |
| Planning | `compound_interest.py`, `dca.py`, `goal_planner.py`: annual compound interest, monthly contributions and required monthly saving; tables/charts. |
| Scenarios / inflation / sensitivity | `scenario.py`, `inflation.py`, `sensitivity.py`; return assumptions, purchasing power and goal contribution comparisons. |
| Historical Analytics | `portfolio_analysis.py`, `portfolio_metrics.py`, `benchmark.py`: validated weights, aligned observed dates, five KPIs, normalized growth, drawdown, correlations and benchmark metrics. Daily target-weight rebalancing, not buy-and-hold. |
| Market data / SQL | `market_data.py`, `database.py`: adjusted Yahoo history, bounded retries/cooldown, cache coverage/freshness, parameterized SQL and persisted configuration/provenance. Cache → Yahoo → labeled deterministic synthetic Demo Data; no public Kibot path. |
| Future Outlook | `future_simulation.py`, `future_ui.py`: historical log-return estimates, 1/3/5-year GBM paths, scenarios, P10/P50/P90 and ending-loss probability. Fixed-parameter assumptions, not verified predictive accuracy. |
| Evolance | `evolance/v1_1/`, `evolance_product.py`, `evolance_ui.py`: monthly 252-session evidence, five dimensions, heuristic state/flags, persistence, transitions and actual 6/12-month directional labels/confidence displayed in the product. |
| Guidance | `portfolio_guidance.py`, `guidance_ui.py`: transparent educational rules combining profile, history and available simulation evidence; no trading execution or optimization. |
| Languages | `i18n.py`, `translations.json`, `engine_messages.json`: global English/Chinese display, retaining engine identifiers, parameters and results. |

The frozen Evolance forward helper computes distribution summaries and relative outlook internally; the product comparison foregrounds absolute 6/12-month direction and ordinal confidence. Do not imply every internal research output is exposed in the UI. The 1/3/5-year Future Outlook controls and the frozen 6/12-month Evolance settings are distinct.

Evolance states affect explanation/confidence, not GBM drift or volatility. Demo confidence is capped at Moderate. At least 253 valid aligned prices at a completed calendar month-end are required; four eligible snapshots support structural change. Missing evidence produces an explicit status. A weekend month-end uses its actual last observed trading date, without future data or filled prices.

The research protocol was executed on a limited 2005–2017 universe. Failure cases are retained; predictive superiority and independent confidence calibration were **not established**. “Dynamic multi-factor” means interactions and changes in financial evidence under fixed rules, not learned AI or causal superiority.

## Previous documentation discrepancies

- README still called v0.4.0 an unapproved release candidate on `v0.4-dev`, although the approved candidate had already been merged/pushed to main.
- “300+” tests was valid but imprecise; the supplied CV figure of 65 is obsolete.
- Product positioning did not foreground financial planning, sensitivity and inflation, and used the prior short tagline instead of the requested descriptor.
- Evolance's English introduction generalized about other tools and used “research-tested” without an immediate experimental label. The showcase text replaces this with implementation-specific wording and explicitly distinguishes confidence from accuracy.
- Existing Home screenshots predate the new showcase copy; Scenario Analysis had no dedicated capture. Existing approved assets remain unchanged and fresh capture slots are documented separately.
- The original local instructions described v0.4-dev as the development route despite approved v0.4.0 now being on main. Historic release notes and Methodology milestone statements remain historical records, not live deployment attestations.

## Showcase changes and scope protection

- README is organized for quick product understanding, with direct Demo/GitHub links, actual features/stack, Evolance status, conventions, workflow, tests, screenshots, roadmap and a short disclaimer.
- Runtime changes are presentation-only: browser title plus four translation entries relative to the committed baseline (`app_development`, `app_description`, `ev_intro_subtitle`, `ev_intro_text`). The follow-up restores the requested original English/Chinese hero tagline; the Chinese Evolance body remains intact.
- Copy expectations in three existing UI/localization test files follow the requested branding. The full English checksum baseline is refreshed only after confirming those four changed entries; version normalization remains narrow. Drift checks include the new description/intro wording; no sections or files are newly excluded.
- No financial/data/research/model rules, UI structure, CSS, chart specifications, dependency files or existing images are changed. No functionality is removed.
- No trained AI, market-prediction advantage or return guarantee is claimed.

## Testing and local runtime

Baseline and final complete offline command (Windows virtual environment):

```powershell
.\.venv\Scripts\python.exe -m pytest -q -ra
```

**Baseline: 336 passed, 213 subtests passed, 0 failed** (56.73s). **Final showcase suite: 336 passed, 213 subtests passed, 0 failed** (48.72s). **Targeted presentation/language/product checks: 45 passed, 11 subtests passed** (20.59s). No pytest warnings, skipped tests or xfails were reported in the successful runs. Earlier v1 tests intentionally preserve implemented historical behavior; no obsolete tests were removed to force a count.

An intermediate targeted run found one additional old Chinese-tagline assertion (44 passed / 1 failed); it was updated to the requested new descriptor, then both targeted and full runs passed. That failed run exposed existing Streamlit AppTest diagnostic logs about bare ScriptRunContext and Session State defaults. These are framework log warnings, distinct from pytest warnings; no language/session logic was changed to suppress them.

The suite mocks market providers and uses isolated SQLite fixtures; it does not require live internet. Streamlit AppTest covers default English, full Chinese output, result preservation, forced Yahoo failure → Demo Data and insufficient-evidence handling. The updated application also passed a local startup check: **health HTTP 200 / ok and root HTTP 200**. The temporary validation server was stopped afterward. This verifies local startup, not cloud interaction or live provider success.

## Deployment and anonymous access

- Web entry: **`streamlit_app.py`**, repository **`knoxlab01/Finance-Mini-Lab`**, stable branch **`main`**.
- Install **`requirements.txt`**. Use a compatible Python runtime (local validation environment: Python 3.12.14); do not use `requirements-dev.txt` as the cloud entrypoint. If the Cloud selector does not offer that minor version, validate an available compatible version before changing a live runtime.
- No API key, OAuth, private manifest or user login is required by application code. Optional `FINANCE_LAB_DB` changes SQLite location; it is not required. Default `data/finance_lab.sqlite3` is created locally and ignored.
- SQLite is instance-local, shared between sessions and not durable cloud storage. Do not enter personal portfolio names/private details; no account isolation is implemented. Authorized offline research files are not required for the demo.
- Anonymous GitHub API request returned HTTP 200 with `private: false`, `default_branch: main`.
- Public app verification was **partial**: browser navigation/state timed out, an initial no-cookie Python GET encountered TLS EOF, and a health request encountered a redirect loop. Inspecting redirects showed HTTP 303 to Streamlit's app-auth route; this alone does not establish a private app. A retry with a **fresh anonymous CookieJar** followed normal redirects and returned **HTTP 200 at the original Demo URL with a Streamlit page shell**, without credentials or a pre-existing session. This proves anonymous shell access, not a rendered analysis or the served product version. Full signed-out interactive validation remains pending. No sharing/security settings were changed.

Owner actions, following [official Streamlit sharing documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app):

1. Open the app in Streamlit Community Cloud as its owner. Confirm the deployment source is the repository above, `main`, `streamlit_app.py`.
2. Open **App settings → Sharing → Who can view this app** and confirm **This app is public and searchable**. If currently restricted, the owner must decide and apply the public-sharing change.
3. In an incognito/signed-out browser, open the Demo URL without GitHub/Streamlit login, wake it if sleeping, then run the sample analysis and switch English/Chinese. HTTP 200 for a shell alone would not prove this.
4. Showcase changes are local/uncommitted. After human approval, separately commit/merge/push them through the normal release process, let Cloud redeploy and recheck the served text. No automatic deployment is performed here.

## Public safety and integrity

The current tracked tree was scanned for credential patterns, assigned nontrivial secrets, personal email addresses, absolute user/project paths, unsafe tracked cache/database/IDE paths and raw OHLCV CSV schemas. No such findings were detected. A separate scan of **237 text blobs in locally reachable Git history** found no matches for the checked token/private-key patterns. Public project handles/URLs are intentional. Raw private research inputs remain ignored; reviewed derived research CSVs and synthetic simulation fixtures are intentional preserved artifacts, not a raw price database.

Ignore probes cover `.env`, Streamlit secrets, SQLite files, private research manifests, caches, IDE files and verification logs. No ignore/protection files are weakened. Pattern scanning cannot prove the absence of every possible sensitive value or of secrets in unreachable Git objects; it is not a credential-security certification.

All **82 milestone files** from `97bf73022e598d9f297ca8b4084e85e58f11bf88` remain preserved: 80 exact research-file byte matches, plus `.gitignore`/`.gitattributes` with only normal Windows CRLF versus stored LF differences. Five approved screenshots remain byte-identical.

Frozen Spec exact JSON SHA-256:

```text
bea9d81702d4afe70a2d65d3fd1beb33c410eeefa0298cc2e5fe5d06e521e0b7
```

No repository LICENSE file is present in the audited tree. Public visibility is not an explicit reuse license; the owner may choose a license separately if desired. No license or data-redistribution right is invented by this showcase task.

## Remaining human actions and recommendation

- Human anonymous-access acceptance has passed as recorded below. Verify the deployment source before any later authorized deployment.
- The owner has supplied four final English screenshots; review their [official index](screenshots/README.md) and the main README presentation before publication.
- Review local changes, then explicitly authorize the desired commit/deployment process. No version bump is necessary for copy work; if a separately versioned release is later desired, consider a v0.4.x patch only after review. Do not relabel this code as v0.3.x.
- Update CV test count to **336 automated tests, plus 213 subtests**; describe GBM and experimental rule-based interpretation accurately, not market prediction accuracy.

The implemented work is suitable evidence for a master's application, GitHub portfolio, CV and technical interview. Human public-access acceptance and the four showcase captures are complete; final publication approval remains pending. This audit does not certify an admissions outcome or a final commercial product.

## Follow-up: human public-access acceptance and product identity

The owner reports successful Chrome Incognito acceptance while signed out of Streamlit and GitHub. The sleeping app opened anonymously after **Yes, get this app back up!**; the homepage, feature pages, English/Chinese switching and public GitHub link worked. This is human-reported interactive acceptance of the existing deployment, superseding the earlier inconclusive automated browser check. Community Cloud sleep/wake does not require a core architecture change.

The local showcase homepage now shows **v0.4.0 · Independent Product** / **v0.4.0 · 独立开发产品**. All runtime translation entries were checked for Program One / Finance Mini Lab and have no such identities. The hero retains **Portfolio Intelligence, Made Clear.** / **让投资组合判断，更清晰。**; the existing overview, four module cards, experimental Evolance disclosure and model behavior remain intact.

Whole-product English/Chinese AppTest assertions reject both historical names in displayed output and verify the new identity captions. The English-copy checksum remains strict, including rejection of the old product-identity wording. No tests are added or removed solely to maintain counts.

Follow-up validation: homepage/localization/language targets **32 passed, 11 subtests passed** (24.62s); complete offline suite **336 passed, 213 subtests passed, 0 failed** (48.76s). No pytest warnings/skips/xfails were reported. Local startup, homepage HTTP 200 and health HTTP 200 / ok passed; `git diff --check` passed. All 82 milestone files, the Frozen Spec hash and five existing screenshot bytes remain preserved.

These follow-up changes remain local. Do not expect the current public deployment to show the new identity until separately approved publication. No final screenshot generation/replacement or commit/push/merge/deploy is part of this follow-up.

## Final screenshot and README acceptance

The owner supplied four official English PNGs in `docs/screenshots/`: `01_vexa_home.png`, `02_scenario_analysis.png`, `03_historical_analytics.png` and `04_evolance_framework.png`. All were opened and visually inspected; filenames match content, source/experimental disclosures are visible, and no visible credentials, personal information or local paths were found. PNG validity and byte preservation were checked. No image was compressed, cropped, re-encoded or regenerated.

The existing screenshot-plan README was read before editing and updated into an official index retaining navigation and privacy guidance. The main README now distributes the four images across Overview, Scenario Analysis, Historical Analytics and Evolance Framework, rather than stacking a separate image gallery. Old image links, capture-pending placeholders and stale product versions/test figures are absent from current showcase documentation. Historical research/release records remain preserved. The experimental framework and synthetic demonstration outputs are not presented as proof of forecasting accuracy.

Final complete offline command: `.\.venv\Scripts\python.exe -m pytest -q -ra` → **336 passed, 213 subtests passed, 0 failed** (40.84s), with no pytest warnings/skips/xfails reported. Local Streamlit startup, homepage HTTP 200 and health HTTP 200 / ok passed; the temporary check server was stopped. `git diff --check` passed. All **21** local Markdown/image links and anchors passed. Current-tree safety patterns found no credentials, personal emails, absolute local paths or raw private market/runtime artifacts. All 82 research milestone files and the exact Frozen Spec hash remain preserved.

This round changes documentation and includes the four user-supplied images only; earlier uncommitted presentation/test work remains intact. The local showcase package is ready for human publication approval. No commit, push, merge or deployment has been performed.

Live Demo: <https://finance-mini-lab-knox.streamlit.app/>

GitHub: <https://github.com/knoxlab01/Finance-Mini-Lab>

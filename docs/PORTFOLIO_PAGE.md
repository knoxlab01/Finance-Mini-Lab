# Vexa Portfolio Page — local preview and maintenance

## Scope

The page is independent static HTML/CSS, approved for GitHub Pages publishing from **main /docs**. No Pages settings, Actions workflow or deployment is enabled simply by adding these files. The existing Streamlit application remains separate and unchanged.

Files:

- `index.html`: public English product showcase.
- `assets/portfolio.css`: responsive layout and accessible focus styles; system fonts only.
- `.nojekyll`: disables unnecessary Jekyll processing when this directory is eventually served.
- Four existing, unchanged `screenshots/01_...png` through `04_...png` images are reused directly.

The page has no JavaScript, tracking, cookies, third-party scripts, build step, server-side runtime or market-data calls. Native links open full-size screenshots; external links use `noopener noreferrer`. The empty data favicon avoids an unnecessary favicon request without inventing a new logo.

## Local preview

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m http.server 8765 --bind 127.0.0.1 --directory docs
```

Open <http://127.0.0.1:8765/>. Stop the preview with Ctrl+C when finished. The Python static server is only a development preview; the published page requires no Python runtime.

All resource URLs are relative, so CSS and images also resolve beneath the repository's eventual project-site prefix. No application source is copied into the page.

## Publishing configuration

For branch-based publishing, select **Settings → Pages → Deploy from a branch → main → /docs** after the approved files reach main. Keep Streamlit pointed at `main` and `streamlit_app.py`; do not rename the repository or modify its demo URL. Enabling Pages requires existing repository permissions; do not request broader access or change a custom domain to bypass a permissions limitation.

This follows the [GitHub Pages branch/folder publishing option](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site). No existing index or version-controlled Pages workflow was found. A read-only anonymous Pages API request returned 404; it did not expose an existing configuration and does not independently prove the state of authenticated repository settings.

Expected project URL, assuming no custom domain or account-level override:

<https://knoxlab01.github.io/Finance-Mini-Lab/>

Do not present this expected URL as live before enabling Pages and verifying the resulting build. This preparation does not inspect or change account-level Pages settings.

## Content and review checklist

- Product: Vexa, v0.4.0, Independent Product.
- Live Demo: <https://finance-mini-lab-knox.streamlit.app/>.
- Source: <https://github.com/knoxlab01/Finance-Mini-Lab>.
- Evolance remains Experimental / Research; confidence is evidence strength, not accuracy.
- Historical and Evolance screenshot examples are synthetic Demo Data, not an investment track record.
- The 336 tests / 213 subtests / 0 failures cards report the accepted product baseline, not tests newly introduced for this static page.
- Preserve the original screenshots and all data/experimental disclosures.
- Check keyboard focus, internal anchors, full-size image links and external links.
- Check 1440px desktop, 768px tablet and 390px/320px mobile widths, including horizontal overflow and readable/tappable controls.
- No personal contact information, applicant-specific copy, internal project identity or local filesystem paths belong on the public landing page.

## Validation record

Local validation completed in the in-app Chromium browser:

- Homepage, stylesheet and all four PNG requests returned **HTTP 200** with appropriate HTML/CSS/PNG MIME types.
- HTML nesting, one H1, unique IDs, internal anchors, four descriptive alt texts, image dimensions and external `noopener noreferrer` links passed source checks.
- Browser DOM confirmed all four images loaded at their original natural widths. Clicking the Scenario Analysis image opened the original PNG in a new tab.
- At **1440, 768, 390 and 320px** viewport widths, document scroll width equaled client width and no main/navigation elements extended horizontally outside the document. Capability cards used 3, 2 and 1 columns as intended; major link/button heights were at least 44px.
- Desktop, tablet and mobile views were visually inspected. Screenshot originals were not modified; validation preview captures are stored outside the repository.
- Skip-to-content keyboard activation focused the main region. Tab navigation displayed a visible focus outline. Browser page console reported **no errors or warnings** during checks.
- The page loads only its local stylesheet and images, with no scripts or embedded services. It does not create cookies or require live market data.
- Public-content checks reject internal identity, applicant-specific wording, private contact details, credential patterns and absolute filesystem paths.

The financial application/tests are unchanged; this static-page task does not claim a fresh Python suite run. Its reliability cards reference the accepted **336 passed / 213 subtests passed / 0 failures** product baseline.

Human visual acceptance passed, and publication was authorized. The only final public-copy adjustments add the AI-era/data/finance origin sentence to Development Journey and label its last stage **Usable Product / Public Prototype**, with ongoing research and development stated explicitly. This describes project motivation, not an implemented AI model. Verify the actual Pages configuration and live URL after the Git publication steps; repository publication alone does not prove Pages activation or deployment completion.

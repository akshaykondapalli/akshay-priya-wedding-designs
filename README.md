# The Atlas of Us — design review (Akshay & Priya)

Four independent, mobile-first interactive invitation directions for review. **This is a design-review site, not the official wedding invitation.** No direction has been chosen.

| # | Direction | Folder |
|---|-----------|--------|
| 01 | Cinematic Heritage Romance | `site/heritage/` |
| 02 | Living Watercolor Painting | `site/watercolor/` |
| 03 | Ultra-Luxury Editorial | `site/editorial/` |
| 04 | Cinematic + Watercolor Fusion | `site/fusion/` |

Comparison page: `site/index.html`. Live: https://akshaykondapalli.github.io/akshay-priya-wedding-designs/

## Source of truth (wedding only)
- Akshay & Priya
- Saturday, 21 November 2026
- Wedding dinner 8:00 PM IST · Muhurtham 9:55 PM IST
- Priyanka Convention, Nallajerla, Andhra Pradesh, India

No other functions are included anywhere in `site/`. A CI guard fails the deploy if archived ceremony wording appears.

## Layout
- `site/` — the only folder deployed to GitHub Pages (static, relative paths, self-hosted fonts, no tracking or third-party requests).
- `tools/` — the scripts that generated each design's original artwork, plus the preview/QA capture script.
- `reference/` — the original concept prototypes and moodboards. `reference/original-prototype-ARCHIVE-DO-NOT-DEPLOY/` holds the old prototype with outdated ceremonies **for comparison only**; it is stored as `.txt` and is never deployed.

## Public by design
GitHub Pages is public. Pages carry `noindex`, but anyone with the link can open them. No phone numbers, family names or guest data are included.

## Still open before guests see anything
See the QA report in the pull/hand-off notes: verified map pin, final event end time for calendar entries, Telugu text check by family, real photography or commissioned illustration if wanted, and the final choice of direction.

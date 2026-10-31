# The Treasure We Found — Review Build

Three-act, wedding-only mobile invitation concept for Akshay & Priya.

- Scene 1: Treasure opener, tap to begin.
- Scene 2: Toronto and German landmark with two SVG aircraft animated toward India; motion runs on user click.
- Scene 3: The approved 31 October artwork is preserved bit-for-bit as `assets/03-invitation-approved-unchanged.png`.
- Details drawer: wedding times and venue, Google Maps search, replay/share options.
- Music: **not included**, intentionally deferred until an audio file/licence is provided.
- Google Maps pin is *unverified*. Calendar action deferred until end time confirmed.
- Review-only; no RSVP backend, no official launch.

## Publish to GitHub Pages as an isolated preview

Do not overwrite existing `fusion/` or other approved designs. Copy this folder into your repository at `treasure-review/`, commit, and push. The URL is expected to be `https://akshaykondapalli.github.io/akshay-priya-wedding-designs/treasure-review/` once deployed.

Git commands from cloned `akshay-priya-wedding-designs` repository root:

```bash
mkdir -p treasure-review
cp -R /path/to/unzipped/treasure_wedding_review/. treasure-review/
git add treasure-review
git commit -m "Add three-act Treasure We Found interactive wedding review"
git push origin main
```

Check the actual branch and deploy configuration before pushing. Verify all assets on iPhone Safari and Android Chrome. The art itself contains stylized/generated map elements; SVG motion is an overlay and should be visually aligned in a second production pass.

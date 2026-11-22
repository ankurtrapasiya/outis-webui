# Spec: Outis themes, reading and retention audit (all four) — V1

Status: implemented 2026-11-22 (CSS + tests; e2e run pending on the CI image)

## Objective

The user asked whether the four Outis themes (Outis Dark, Outis Light, Outis Spark, Outis FT) are
built for reading, retention and simplicity, backed by research, and to fix what is not.

Scope is colour, as `tests/outis/specs/SPEC-theme.md` has fixed since 2026-11-14 (font, sizes,
radii and spacing are stock Open WebUI by the user's choice; the 75ch cap was removed at the
user's request on 2026-10-05). Those two decisions are not reopened here; see Open questions.

## What the research says

Earlier findings (WCAG 2.2, APCA, Material/Apple dark mode, polarity, halation, line length) are
in `docs/outis-theme-colour-research.md` and `OUTIS_READING_SPEC.md` and still hold. New for this
audit:

| # | Finding | Strength | Source |
|---|---|---|---|
| R1 | Legibility follows luminance contrast, not hue. | Strong | Legge & Rubin, https://pmc.ncbi.nlm.nih.gov/articles/PMC4621622 |
| R2 | Signaling (cues pointing at key content) helps comprehension and transfer, r = 0.17 / d = 0.38, most for low prior knowledge. | Strong (2 meta-analyses) | Richter, Scheiter & Eitel 2016, *Educ Res Rev*; Alpizar, Adesope & Wong 2020, *ETR&D* |
| R3 | An item that looks different from its neighbours is remembered better (isolation effect). | Strong | von Restorff 1933; https://link.springer.com/content/pdf/10.3758/MC.37.2.175.pdf |
| R4 | Highlighting helps only when the marks separate important from trivial content; instructor-given highlights improve memory and comprehension. | Moderate / strong | Fowler & Barker 1974; Ponce et al. 2022, https://link.springer.com/10.1007/s10648-021-09654-1 |
| R5 | More colour variety raises measured visual clutter. | Moderate | Rosenholtz, Li & Nakano 2007, *J Vision* 7(2):17 |
| R6 | 5–7 simultaneous colours is a practitioner rule; pick colours by distance and colour category. | Practitioner | Healey 1996, https://www.cs.ubc.ca/tr/1996/tr-96-10 |
| R7 | Okabe-Ito colours (blue, orange, vermillion, bluish green, ...) stay apart for common colour-vision deficiency (CVD); red/green does not. | Practitioner (widely adopted) | Wong 2011, *Nat Methods* 8:441 |
| R8 | Desaturate large areas; keep saturated colour for small marks. Pop-out grows with difference from the surround. | Practitioner / strong | Ware, *Information Visualization* |
| R9 | Red does not hurt analytic performance once publication bias is corrected; Mehta & Zhu 2009 failed replication. | Strong (negative) | Gnambs 2020, https://pmc.ncbi.nlm.nih.gov/articles/PMC7704521/ ; Steele 2014 |
| R10 | Hard-to-read text does not improve learning (d ≈ 0.01). | Strong (null) | Xie et al. 2018; Weissgerber et al. 2021, https://link.springer.com/article/10.1007/s10648-020-09579-1 |
| R11 | Syntax highlighting shows no clear comprehension gain for novices. | Moderate | Hannebauer et al. 2018, *EMSE* 23:2795 |
| R12 | No controlled study shows cream, sepia or FT salmon paper beats white; tinted overlays are no better than placebo. | Strong review / unverified for salmon | Griffiths et al. 2016, https://eprints.whiterose.ac.uk/104441 |
| R13 | Screen brightness, not warm tint, drives the evening melatonin effect. | Moderate–strong | Chang 2015 *PNAS*; Nagare 2019; Duraccio 2021 |

What follows for this app: a reply's colour code is a signaling device. It only works if each
mark is (a) visibly different from body text and from every other mark, including for a reader
with deuteranopia, (b) quieter than the text it sits in, so the eye reads rather than jumps, and
(c) the same meaning in every theme, so switching theme does not mean relearning it. Tints,
"calming" hues and the paper colour are cosmetic (R1, R9, R12): no change on their account.

## Audit (measured)

Method: script in "Verification" below; WCAG 2 ratio, APCA-W3 0.0.98G-4g, OKLab ΔE ×100 for
normal vision and for deuteranopia (Viénot 1999 simulation). Reading roles: body, link, key term
(`strong`), example (`em`), maths (`.katex`).

| Theme | Problem | Numbers | Breaks |
|---|---|---|---|
| Dark | Example blue = link blue | ΔE 4.0 (deut 4.1) | R2/R4: an example reads as a link |
| Light | Same | ΔE 5.9 (deut 5.8) | same |
| Spark | Key term = maths colour | ΔE 0.0 | a bold term reads as a formula |
| Spark | Example louder than body text | Lc 84 vs body 79 | R8: the mark outshines the text |
| Spark | Error/warning neon on dark | `#ff5252` Lc 42, `#ffb300` C 0.17 | dark-theme desaturation rule |
| FT | Link, key term, example, inline code all `#005b7f`; maths `#00689f` | ΔE 0–6 | the whole colour code collapses to one hue |
| FT | Headings = body colour | both `#33302e` | no heading step (TH-29 ladder) |
| FT | Error and success under 4.5:1 on the card | 4.2:1, 4.4:1 | WCAG 1.4.3 |
| FT | Maths is blue, every other theme gold/ochre | | consistency (c) |

Passes everywhere: body text in band (dark Lc 78–79, light Lc 92–96), accents below body,
focus ring and control borders ≥ 3:1, grounds are dark gray / warm paper, not black / white.

## New behaviour

One colour code, four palettes. Per theme:

| Role | Hue family | Dark | Light | Spark | FT |
|---|---|---|---|---|---|
| link / accent | theme accent | `#93c4ed` (kept) | `#1a588f` (kept) | `#92d400` (kept) | `#005b7f` (kept) |
| key term `strong` | warm (copper/coral/claret) | `#f2a06e` (kept) | `#a3471a` (kept) | **`#e6a3a2`** | **`#7a2439`** |
| example `em` (new token `--outis-example`) | bluish green; blue where the accent is green | **`#75bca3`** | **`#1f7265`** | **`#98a6ea`** | **`#1f7265`** |
| maths | gold / ochre | `#f0c674` (kept) | `#7a4f00` (kept) | `#cba35e` (kept) | **`#7a4f00`** |
| heading | brightest / darkest neutral | kept | kept | kept | **`#1f1d1b`** |
| error / warning / success | status | kept | kept | **`#f69b94` / `#edbf71`** / kept | **`#b31f33`** / kept / **`#276b4d`** |

Inline code chips keep `--outis-code-node` (shape and monospace set them apart; TH-34 unchanged).

## Success criteria

Checked by `scripts/outis-palette-check.py` on the table above, and by TH-38 /
CR-22 in the browser on the real computed colours:

1. Body text: dark themes Lc ≥ 75, light themes Lc ≥ 90 on page (−3 on the card).
2. Headings are further from the ground than body text.
3. Link, key, example, maths, status and muted text ≥ 4.5:1 on the card surface.
4. No mark is louder than body text (APCA Lc ≤ body).
5. Every pair of reading roles differs by ΔE ≥ 8 for normal vision and for deuteranopia; key vs
   maths needs only ≥ 5 for deuteranopia, because the shape (bold sans vs KaTeX serif italic)
   also separates them (WCAG 1.4.1).
6. Must not change: grounds, body text, accents, focus, code syntax colours, fonts, sizes, radii.

## Boundaries

- Always: colour-only changes in `src/outis-*.css`; tests and specs updated in the same change.
- Ask first: fonts, text size, line length.
- Never: touch the live instance (:3001), skip or loosen the regression gate.

## Verification

```
/usr/bin/python3 -B scripts/outis-palette-check.py   # ALL PASS; on the old values it listed 13 misses
# browser checks, on a CI image:
scripts/outis-regression.sh ghcr.io/ankurtrapasiya/open-webui:outis-mneme-<sha> -g "TH-38|CR-22|TH-3[34]"
```

## Follow-up, same day (user: "adopt rest")

- **Spark neutrals** at 45% of their old chroma (ground `#12200a` -> `#171e14`, C 0.044 -> 0.022;
  body `#cdd8ba` -> `#d0d5c8`). R8: desaturate large areas. Accent, branch hues and status keep
  theirs. Also in `app.html` boot paint, `utils/theme.ts`, the theme card and CD-15.
- **Syntax, Spark and FT**: three hues (keyword, literal, string); function and type names neutral.
  R11: no comprehension loss. Spark keyword gold / literal teal / string sage; FT keyword claret
  `#7a2439` / literal `#00689f` / string `#276b4d`. Outis Dark/Light keep GitHub Primer (user's pick, 2026-10-01).
- **outis-owui reading guide** names no hues now ("key-term colour", "example colour", "code chip"),
  since the hues differ per theme. It also said inline code was amber, which was stale since TH-34.

## Open questions

- Line length: kept uncapped (user, 2026-11-22), although WCAG 1.4.8 suggests 45–75 characters.
- Text size and face are stock since 2026-11-14; no change proposed.

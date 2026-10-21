# english-autotag.txt → UPOS conversion notes

Output: [english-autotag_upos.tsv](./english-autotag_upos.tsv) (passes `test_collection.py ... autotag`, no duplicates).
POS mapping used: [c7_to_upos.json](../pos_mappers/c7_to_upos.json) (NNU\*→NOUN, MC\*→NUM, MD→ADJ, MF→NUM, RA→ADV, JJ→ADJ, FO→X, ZZ\*→SYM).

## Two things that change the problem

1. **Order is significant: the tagger stops at the first matching entry.** The converted TSV is therefore kept in the original rule order (not sorted), most specific first, and the generic rows (`* NUM`, `* SYM`) are placed after the rows they must not shadow. Any file this is merged into must preserve that order.
2. **A CLAWS tag was a much stronger gate than a UPOS tag.** `*m NNU` only fired on tokens CLAWS had already tagged as a unit. `*m NOUN` fires on any noun ending in `m` that is not in the single word lexicon. Several patterns are therefore tightened (below).

## Decisions

| Old entry | New | Reason |
|---|---|---|
| `*p NNU` | `*[0-9]p NOUN` | Tightened: requires a digit before the unit. Otherwise any unknown noun ending in `p` gets `I1`. |
| `*pence NNU2` | `*pence NOUN` | Direct map. |
| `*s MC2` | `*s NUM` | Direct map. NUM is a reasonable gate. A tagger may give `1990s` NOUN instead, check on real output. |
| `I MC1`, `I ZZ1`, `i ZZ1` | `I NUM`, `I SYM`, `i SYM` → Z8 | Mapped literally. These existed to fix CLAWS mis-tags of the pronoun. A UPOS tagger gives PRON, which the single word lexicon already has (`I PRON Z8mf`). **Low value, probably safe to drop.** |
| `* MC*` | `* NUM` | Direct map. Acts as the NUM fallback, so it must stay after all other NUM rows. **Bug in the original:** it came *before* `*M MC` and `[0-9]*K MC`, so those two were unreachable. I moved `*M NUM`, `[0-9][0-9]*K NUM` and the fraction row ahead of it so they take effect. Move them back if the old behaviour was intended. |
| `* MD*` | **not converted as is.** `[0-9][0-9]*st/nd/rd/th ADJ` | MD→ADJ would make `* ADJ N4 T1.3` tag **every unknown adjective** as an ordinal. Replaced by digit-led ordinals. Word ordinals (`first`...`twentieth`) belong in the single word lexicon. Hyphenated ones (`twenty-first`) are not covered, add `*-first`, `*-second`, ... if wanted. |
| `*% NNU` | `*% NOUN` | Direct map. The existing lexicon has `*% NUM N5`. Different POS, so both can coexist. |
| `* MF*` | **not converted as is.** `[0-9][0-9]*/[0-9][0-9]* NUM N5` | MF→NUM gives `* NUM N5`, which would be shadowed by the MC\* catch-all, and in the original `MF*` was unreachable for the same reason on a different tag. CLAWS tagged fraction *words* (`half`, `thirds`), and those are already in the single word lexicon. Only the numeric form `3/4` needs a pattern. Unicode fractions (`½`) are not covered. |
| `#*`, `$*`, `&pound;*`, `&dollar;*` NNU | `$*`, `£*` NOUN | `&pound;`/`&dollar;` are SGML entities, converted to the Unicode characters. **`#*` dropped**: it was a legacy ASCII stand-in for `£`, today it is a hashtag and would tag `#love` as money. If your data still contains the entity forms, add them back. Tokenisers often split `$` from the digits, so the NOUN row may rarely fire. SYM or NUM would be the likelier UPOS output. |
| `*am`, `*pm`, `*o'clock` RA | ADV | Direct map. A UPOS tagger may tag `10am` as NOUN/NUM/X. Check on real output. |
| `[0-9]*ish JJ` | `[0-9][0-9]*ish ADJ` | README warning: `[0-9]*` also matches zero digits, so the old pattern matched the word `ish`. |
| `*M MC` | `*M NUM` | Direct map (million). |
| `[0-9]*K MC / NNU` | `[0-9][0-9]*K NUM / NOUN` | Zero-digit fix, as for `ish`. |
| `*M`, `*cc`, `*cm`, `*cms`, `*ft`, `*gr`, `*in`, `*ins`, `*kg`, `*kgs`, `*lb`, `*lbs`, `*mm`, `*oz`, `*ozs`, `*km`, `*m`, `*m2`, `*m3` NNU/NNU2 | `*[0-9]<unit> NOUN` | Tightened, see point 2 above. Without it `*in` hits `bitcoin`, `*ins` hits `origins`, `*m` hits `problem`. Standalone units (`m`, `ft`, `in`...) are already in the single word lexicon. `*` before the digit still allows `£5m`, `2.5cm`. NNU/NNU2 both → NOUN, so the singular/plural distinction is lost (plural rows kept as separate patterns). |
| `*kph` | unchanged (already present) | Identical to the existing row, so not duplicated. Note it is not digit-tightened. |
| `*&deg;C`, `*&deg;F` FO | `*°C`, `*°F` X | Entity → Unicode. FO→X per the mapper. A tagger may well give NOUN or SYM instead. The existing file has `*'C NOUN O4.6`. |
| `*x* FO` | `[0-9][0-9]*x[0-9][0-9]* X` | `*x*` as X would catch any X token containing `x`. Restricted to `3x4` shapes. |
| `A/B/M[0-9]* ZZ1` | `A/B/M[0-9][0-9]* SYM` | Zero-digit fix (old matched bare `A`). ZZ1→SYM per the mapper, but UPOS taggers likely say PROPN for `M25`. |
| `* ZZ*` | `* SYM Z5` | Difficult: ZZ is "letter" and SYM is any symbol, so `+`, `=`, `©` also get Z5 (grammatical bin). Arguably fine. The single word lexicon already uses `SYM Z5` for letters (`M`, `p`, `x`). |

## Merge into semantic_lexicon_en_autotag.tsv

Only one exact overlap (`*kph NOUN`, identical tags). Because first match wins, the merge is an ordered insertion, not a union plus sort:

* Put the existing rows (all specific `*-year-old`-style suffix patterns) **before** the generic `* NUM` and `* SYM` rows. The existing file is currently alphabetical, so the merged file will no longer be sorted. Rules that may overlap each other should be ordered specific → generic by hand.
* Place the existing `*% NUM N5` before `* NUM`, otherwise it is shadowed. The new `*% NOUN` is a different POS, so they do not interact.
* `*cms NOUN`: existing `N3.7` and new `*[0-9]cms` (`N3.3 N3.7`) both match `5cms`. Whichever comes first wins. Choose which tag set you want, then order accordingly.
* `*kph NOUN` is already present, so I did not add a second copy (it is still in the converted file at its original position, delete one when merging).
* `*°C X` and `*'C NOUN` are different patterns, keep both.
* Existing patterns such as `*ha NOUN` are not digit-gated and will match any noun ending in `ha`. Worth checking, since earlier rows win.
* `test_collection.py` and `duplicate_entires.py` do not check shadowing. A rule that can never fire (as `*M MC` was) will pass them silently.

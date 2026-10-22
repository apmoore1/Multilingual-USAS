# english-autotag.txt → UPOS conversion notes

Output: [english-autotag_upos.tsv](./english-autotag_upos.tsv) (passes `test_collection.py ... autotag`, no duplicates).
POS mapping used: [c7_to_upos.json](../pos_mappers/c7_to_upos.json) (NNU\*→NOUN, MC\*→NUM, MD→ADJ, MF→NUM, RA→ADV, JJ→ADJ, FO→X, ZZ\*→SYM).

## Two things that change the problem

1. **Order is significant: the tagger stops at the first matching entry.** The converted TSV is therefore kept in the original rule order (not sorted), most specific first, and the generic rows (`* NUM`, `* SYM`) are placed after the rows they must not shadow. Any file this is merged into must preserve that order.
2. **A CLAWS tag was a much stronger gate than a UPOS tag.** `*m NNU` only fired on tokens CLAWS had already tagged as a unit. `*m NOUN` fires on any noun ending in `m` that is not in the single word lexicon. Several patterns are therefore tightened (below).

## Decisions

| Old entry | New | Reason |
|---|---|---|
| `*p NNU` | `*[0-9]p NOUN` |Agree |
| `*pence NNU2` | `*pence NOUN` | Agree. Running this through spaCy the POS tagger tags `10pence` as a `NUM`. |
| `*s MC2` | `*s NUM` | **Andrew** spaCy English POS tagger does give `forties`, `1940s`, `Twenties` as a NOUN.|
| `I MC1`, `I ZZ1`, `i ZZ1` | `I NUM`, `I SYM`, `i SYM` → Z8 | Andrew probably should drop |
| `* MC*` | `* NUM` | Agree |
| `* MD*` | **not converted as is.** `[0-9][0-9]*st/nd/rd/th ADJ` | MD→ADJ would make `* ADJ N4 T1.3` tag **every unknown adjective** as an ordinal. Replaced by digit-led ordinals. Word ordinals (`first`...`twentieth`) belong in the single word lexicon. Hyphenated ones (`twenty-first`) are not covered, add `*-first`, `*-second`, ... if wanted. **Andrew** hyphenated I do not think we should do here as the tokeniser does split it up, e.g. `thirty` `-` `first` **I think those types of entries twenty-second should be an MWE entry (checked does not exist in the MWE lexicon apart from twenty-first)**. Checked the single word lexicon and the following entires will need adding `thirteenth`, `fourteenth`, `fifteenth`, `sixteenth`, `seventeenth`, and `eighteenth`.|
| `*% NNU` | `*% NOUN` | Direct map. The existing lexicon has `*% NUM N5`. Different POS, so both can coexist. **Andrew** note that most tokenizers will split the number from the `%` symbol, check with spaCy and it does this and labels the `%` as a NOUN. Keep for now but might be a case as a **MWE** |
| `* MF*` | **not converted as is.** `[0-9][0-9]*/[0-9][0-9]* NUM N5` | Andrew agree |
| `#*`, `$*`, `&pound;*`, `&dollar;*` NNU | `$*`, `£*` NOUN | I think we want to keep the SGML entities but not the hashtag, in addition `£` and `$` when using spaCy are separated from the number and are tagged as `SYM` (SGML entities are broken up by the spaCy tokenizer `&`, `pound`, `;`). Might be better as a **MWE**|
| `*am`, `*pm`, `*o'clock` RA | ADV | The number in all cases is separated from the `am` or `o'clock` and it tags `10` as `NUM` and `am` and `o'clock` as `NOUN`. I think this would be better as a **MWE** (line 293 `o'clock`, 311 `pm`, and 245 `am` are MWEs)|
| `[0-9]*ish JJ` | `[0-9][0-9]*ish ADJ` | Andrew agree. **spaCy** POS tagger tags this as a `NUM`. |
| `*M MC` | `*M NUM` | If this is the same as the below for `[0-9][0-9]*K NUM / NOUN` to cover 100M etc then we should have the same for billion and trillion. Checking with spaCy the numbers are sometimes tokenized away `100` `M` and sometimes not `100M` thus it should be a **MWE** the `M``K``B` can be tagged as `PROPN` and when the number of `M` is tokenised separately then it is `NUM` and `NOUN` when together `PROPN` |
| `[0-9]*K MC / NNU` | `[0-9][0-9]*K NUM / NOUN` | Zero-digit fix, as for `ish`. |
| `*M`, `*cc`, `*cm`, `*cms`, `*ft`, `*gr`, `*in`, `*ins`, `*kg`, `*kgs`, `*lb`, `*lbs`, `*mm`, `*oz`, `*ozs`, `*km`, `*m`, `*m2`, `*m3` NNU/NNU2 | `*[0-9]<unit> NOUN` | Tightened, see point 2 above. Without it `*in` hits `bitcoin`, `*ins` hits `origins`, `*m` hits `problem`. Standalone units (`m`, `ft`, `in`...) are already in the single word lexicon. `*` before the digit still allows `£5m`, `2.5cm`. NNU/NNU2 both → NOUN, so the singular/plural distinction is lost (plural rows kept as separate patterns). **Andrew spaCy** the tokenisation is hit and miss sometimes `2.5` `in` or `2.5` `cm` sometimes `2.5cms` when it is tokenised together it is treated as a `NUM` not `NOUN`. I think this should also be in **MWE** (line 283 inch is in MWE not metric measurements.)|
| `*kph` | unchanged (already present) | This is often a MWE `80` `kph`. Add to the **MWE** |
| `*&deg;C`, `*&deg;F` FO | `*°C`, `*°F` X | This with the spaCy tokeniser is split up into `10` `°` `C` with `NUM` `NUM` `NOUN`. **MWE** (line 271 `*_NUM degrees_NOUN	O4.6+ M6`). |
| `*x* FO` | `[0-9][0-9]*x[0-9][0-9]* X` | This should be a `NUM` pos tag as that is how spaCy tags it. |
| `A/B/M[0-9]* ZZ1` | `A/B/M[0-9][0-9]* SYM` | This should be `PROPN` as that is how spaCy tags it. |
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

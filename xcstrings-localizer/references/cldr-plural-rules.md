# CLDR Plural Rules Reference for xcstrings Localization

Source: Unicode CLDR v48 — https://www.unicode.org/cldr/charts/48/supplemental/language_plural_rules.html

## How to read this reference

Each language lists the **cardinal** plural categories it uses and the rules that determine which category a number falls into. The six possible CLDR categories are: `zero`, `one`, `two`, `few`, `many`, `other`. Every language must have `other`; the rest are optional.

**Operand definitions** (used in rules):
- `n` = absolute value of the source number
- `i` = integer digits of n
- `v` = number of visible fraction digits (with trailing zeros)
- `w` = number of visible fraction digits (without trailing zeros)
- `f` = visible fraction digits (with trailing zeros)
- `t` = visible fraction digits (without trailing zeros)

**Apple xcstrings uses these category names directly** as keys under `variations.plural`.

---

## Table of Contents

1. [Languages with only `other` (no plural distinction)](#group-other-only)
2. [Languages with `one` + `other`](#group-one-other)
3. [Languages with `one` + `few` + `other`](#group-one-few-other)
4. [Languages with `one` + `few` + `many` + `other`](#group-one-few-many-other)
5. [Languages with `one` + `two` + `few` + `many` + `other`](#group-one-two-few-many-other)
6. [Languages with `zero` + `one` + `two` + `few` + `many` + `other`](#group-all-six)

---

## Group: `other` only {#group-other-only}

These languages use a single form for all numbers. No plural variations needed in xcstrings.

| Language | Code |
|----------|------|
| Chinese (Simplified) | zh-Hans |
| Chinese (Traditional) | zh-Hant |
| Japanese | ja |
| Korean | ko |
| Malay | ms |
| Thai | th |
| Vietnamese | vi |
| Indonesian | id |
| Burmese | my |
| Khmer | km |
| Lao | lo |
| Turkish | tr |
| Hungarian | hu |

For these languages, provide only the `other` category in xcstrings plural variations.

---

## Group: `one` + `other` {#group-one-other}

### English (en)
- **one**: `n = 1` → 1
- **other**: everything else → 0, 2, 3, 4, 5...

### French (fr)
- **one**: `i = 0,1` → 0, 1 (note: 0 is singular in French)
- **other**: everything else → 2, 3, 4, 5...

### German (de)
- **one**: `i = 1 and v = 0` → 1
- **other**: everything else → 0, 2, 3...

### Italian (it)
- **one**: `i = 1 and v = 0` → 1
- **other**: everything else → 0, 2, 3...

### Spanish (es)
- **one**: `n = 1` → 1
- **other**: everything else → 0, 2, 3...

### Portuguese (pt)
- **one**: `i = 0..1` → 0, 1
- **other**: everything else → 2, 3, 4...

### Portuguese – Brazil (pt-BR)
- **one**: `i = 0..1` → 0, 1
- **other**: everything else → 2, 3, 4...

### Dutch (nl)
- **one**: `i = 1 and v = 0` → 1
- **other**: everything else → 0, 2, 3...

### Swedish (sv)
- **one**: `i = 1 and v = 0` → 1
- **other**: everything else → 0, 2, 3...

### Danish (da)
- **one**: `n = 1` or `t != 0 and i = 0,1` → 1, 0.1~1.6
- **other**: everything else → 0, 2, 3...

### Norwegian Bokmål (nb)
- **one**: `n = 1` → 1
- **other**: everything else → 0, 2, 3...

### Norwegian Nynorsk (nn)
- **one**: `n = 1` → 1
- **other**: everything else → 0, 2, 3...

### Finnish (fi)
- **one**: `i = 1 and v = 0` → 1
- **other**: everything else → 0, 2, 3...

### Greek (el)
- **one**: `n = 1` → 1
- **other**: everything else → 0, 2, 3...

### Hindi (hi)
- **one**: `i = 0 or n = 1` → 0, 1
- **other**: everything else → 2, 3, 4...

### Bengali (bn)
- **one**: `i = 0 or n = 1` → 0, 1
- **other**: everything else → 2, 3, 4...

### Swahili (sw)
- **one**: `n = 1` → 1
- **other**: everything else → 0, 2, 3...

### Catalan (ca)
- **one**: `i = 1 and v = 0` → 1
- **other**: everything else → 0, 2, 3...

### Afrikaans (af)
- **one**: `n = 1` → 1
- **other**: everything else → 0, 2, 3...

### Bulgarian (bg)
- **one**: `n = 1` → 1
- **other**: everything else → 0, 2, 3...

### Estonian (et)
- **one**: `i = 1 and v = 0` → 1
- **other**: everything else → 0, 2, 3...

### Georgian (ka)
- **one**: `n = 1` → 1
- **other**: everything else → 0, 2, 3...

### Armenian (hy)
- **one**: `i = 0,1` → 0, 1
- **other**: everything else → 2, 3, 4...

### Azerbaijani (az)
- **one**: `n = 1` → 1
- **other**: everything else → 0, 2, 3...

### Uzbek (uz)
- **one**: `n = 1` → 1
- **other**: everything else → 0, 2, 3...

### Kazakh (kk)
- **one**: `n = 1` → 1
- **other**: everything else → 0, 2, 3...

### Kannada (kn)
- **one**: `i = 0 or n = 1` → 0, 1
- **other**: everything else → 2, 3...

### Tamil (ta)
- **one**: `n = 1` → 1
- **other**: everything else → 0, 2, 3...

### Telugu (te)
- **one**: `n = 1` → 1
- **other**: everything else → 0, 2, 3...

### Marathi (mr)
- **one**: `n = 1` → 1
- **other**: everything else → 0, 2, 3...

### Gujarati (gu)
- **one**: `i = 0 or n = 1` → 0, 1
- **other**: everything else → 2, 3...

---

## Group: `one` + `few` + `other` {#group-one-few-other}

### Czech (cs)
- **one**: `i = 1 and v = 0` → 1
- **few**: `i = 2..4 and v = 0` → 2, 3, 4
- **other**: everything else → 0, 5, 6, 7...

**Example:** 1 soubor / 2 soubory / 5 souborů

### Slovak (sk)
- **one**: `i = 1 and v = 0` → 1
- **few**: `i = 2..4 and v = 0` → 2, 3, 4
- **other**: everything else → 0, 5, 6, 7...

**Example:** 1 súbor / 2 súbory / 5 súborov

### Croatian (hr)
- **one**: `v = 0 and i % 10 = 1 and i % 100 != 11` or `f % 10 = 1 and f % 100 != 11` → 1, 21, 31...
- **few**: `v = 0 and i % 10 = 2..4 and i % 100 != 12..14` or `f % 10 = 2..4 and f % 100 != 12..14` → 2, 3, 4, 22, 23...
- **other**: everything else → 0, 5~19, 100...

**Example:** 1 sat / 2 sata / 5 sati

### Serbian (sr)
- **one**: `v = 0 and i % 10 = 1 and i % 100 != 11` or `f % 10 = 1 and f % 100 != 11` → 1, 21, 31...
- **few**: `v = 0 and i % 10 = 2..4 and i % 100 != 12..14` or `f % 10 = 2..4 and f % 100 != 12..14` → 2~4, 22~24...
- **other**: everything else → 0, 5~19, 100...

### Bosnian (bs)
Same rules as Serbian/Croatian.

### Romanian (ro)
- **one**: `i = 1 and v = 0` → 1
- **few**: `v != 0` or `n = 0` or `n % 100 = 2..19` → 0, 2~19, 102~119...
- **other**: everything else → 20~100, 120~200...

**Example:** 1 zi / 2 zile / 20 de zile

### Latvian (lv)
- **zero**: `n % 10 = 0` or `n % 100 = 11..19` or `v = 2 and f % 100 = 11..19` → 0, 10, 11~19, 20, 30...
- **one**: `n % 10 = 1 and n % 100 != 11` or `v = 2 and f % 10 = 1 and f % 100 != 11` or `v != 2 and f % 10 = 1` → 1, 21, 31...
- **other**: everything else

### Lithuanian (lt)
- **one**: `n % 10 = 1 and n % 100 != 11..19` → 1, 21, 31, 41...
- **few**: `n % 10 = 2..9 and n % 100 != 11..19` → 2~9, 22~29...
- **other**: everything else → 0, 10~20, 30, 40...

**Example:** 1 obuolys / 2 obuoliai / 10 obuolių

---

## Group: `one` + `few` + `many` + `other` {#group-one-few-many-other}

### Polish (pl)
- **one**: `i = 1 and v = 0` → 1
- **few**: `v = 0 and i % 10 = 2..4 and i % 100 != 12..14` → 2, 3, 4, 22, 23, 24...
- **many**: `v = 0 and i != 1 and i % 10 = 0..1` or `v = 0 and i % 10 = 5..9` or `v = 0 and i % 100 = 12..14` → 0, 5~19, 25~30...
- **other**: everything else (decimals) → 0.1, 1.5, 2.7...

**Example:** 1 plik / 2 pliki / 5 plików / 1,5 pliku

### Russian (ru)
- **one**: `v = 0 and i % 10 = 1 and i % 100 != 11` → 1, 21, 31, 41...
- **few**: `v = 0 and i % 10 = 2..4 and i % 100 != 12..14` → 2, 3, 4, 22, 23, 24...
- **many**: `v = 0 and i % 10 = 0` or `v = 0 and i % 10 = 5..9` or `v = 0 and i % 100 = 11..14` → 0, 5~20, 25~30...
- **other**: everything else (decimals) → 0.1, 1.5...

**Example:** 1 файл / 2 файла / 5 файлов / 1,5 файла

### Ukrainian (uk)
- **one**: `v = 0 and i % 10 = 1 and i % 100 != 11` → 1, 21, 31, 41...
- **few**: `v = 0 and i % 10 = 2..4 and i % 100 != 12..14` → 2, 3, 4, 22, 23, 24...
- **many**: `v = 0 and i % 10 = 0` or `v = 0 and i % 10 = 5..9` or `v = 0 and i % 100 = 11..14` → 0, 5~20, 25~30...
- **other**: everything else (decimals) → 0.1, 1.5...

**Example:** 1 яблуко / 2 яблука / 5 яблук / 1,5 яблука

### Belarusian (be)
- **one**: `n % 10 = 1 and n % 100 != 11` → 1, 21, 31...
- **few**: `n % 10 = 2..4 and n % 100 != 12..14` → 2, 3, 4, 22...
- **many**: `n % 10 = 0` or `n % 10 = 5..9` or `n % 100 = 11..14` → 0, 5~19, 100...
- **other**: everything else (decimals)

### Macedonian (mk)
- **one**: `v = 0 and i % 10 = 1 and i % 100 != 11` or `f % 10 = 1 and f % 100 != 11` → 1, 21, 31...
- **other**: everything else → 0, 2~16, 100...

(Note: Macedonian actually uses `one` + `other`, listed here for Slavic context)

---

## Group: `one` + `two` + `few` + `many` + `other` {#group-one-two-few-many-other}

### Slovenian (sl)
- **one**: `v = 0 and i % 100 = 1` → 1, 101, 201...
- **two**: `v = 0 and i % 100 = 2` → 2, 102, 202...
- **few**: `v = 0 and i % 100 = 3..4` or `v != 0` → 3, 4, 103, 104, and all decimals
- **other**: everything else → 0, 5~99, 105~199...

**Example:** 1 ura / 2 uri / 3 ure / 5 ur

### Irish (ga)
- **one**: `n = 1` → 1
- **two**: `n = 2` → 2
- **few**: `n = 3..6` → 3, 4, 5, 6
- **many**: `n = 7..10` → 7, 8, 9, 10
- **other**: everything else → 0, 11, 12, 13...

---

## Group: all six categories {#group-all-six}

### Arabic (ar)
- **zero**: `n = 0` → 0
- **one**: `n = 1` → 1
- **two**: `n = 2` → 2
- **few**: `n % 100 = 3..10` → 3~10, 103~110...
- **many**: `n % 100 = 11..99` → 11~26, 111...
- **other**: everything else → 100~102, 200~202...

**Example:** ٠ ملفات / ملف واحد / ملفان / ٣ ملفات / ١١ ملفًا / ١٠٠ ملف

### Welsh (cy)
- **zero**: `n = 0` → 0
- **one**: `n = 1` → 1
- **two**: `n = 2` → 2
- **few**: `n = 3` → 3
- **many**: `n = 6` → 6
- **other**: everything else → 4, 5, 7, 8, 9...

---

## Quick Lookup: Language → Required Plural Categories

| Language | Code | Required xcstrings plural keys |
|----------|------|-------------------------------|
| Arabic | ar | zero, one, two, few, many, other |
| Belarusian | be | one, few, many, other |
| Bulgarian | bg | one, other |
| Catalan | ca | one, other |
| Chinese (Simplified) | zh-Hans | other |
| Chinese (Traditional) | zh-Hant | other |
| Croatian | hr | one, few, other |
| Czech | cs | one, few, other |
| Danish | da | one, other |
| Dutch | nl | one, other |
| English | en | one, other |
| Estonian | et | one, other |
| Finnish | fi | one, other |
| French | fr | one, other |
| German | de | one, other |
| Greek | el | one, other |
| Hebrew | he | one, two, other |
| Hindi | hi | one, other |
| Hungarian | hu | other |
| Indonesian | id | other |
| Irish | ga | one, two, few, many, other |
| Italian | it | one, other |
| Japanese | ja | other |
| Korean | ko | other |
| Latvian | lv | zero, one, other |
| Lithuanian | lt | one, few, other |
| Malay | ms | other |
| Norwegian Bokmål | nb | one, other |
| Polish | pl | one, few, many, other |
| Portuguese | pt | one, other |
| Portuguese (Brazil) | pt-BR | one, other |
| Romanian | ro | one, few, other |
| Russian | ru | one, few, many, other |
| Serbian | sr | one, few, other |
| Slovak | sk | one, few, other |
| Slovenian | sl | one, two, few, other |
| Spanish | es | one, other |
| Swahili | sw | one, other |
| Swedish | sv | one, other |
| Thai | th | other |
| Turkish | tr | other |
| Ukrainian | uk | one, few, many, other |
| Vietnamese | vi | other |
| Welsh | cy | zero, one, two, few, many, other |

---

## Important Notes for Translators

1. **`other` is always required** — it's the fallback for any number not matched by other rules.
2. **`one` does not always mean "1"** — in some languages (French, Hindi, Portuguese), zero also uses the `one` form.
3. **Slavic languages are complex** — Russian, Ukrainian, Polish etc. have rules based on the last digits of the number, with special exceptions for 11-19.
4. **East Asian languages have no plural distinction** — Chinese, Japanese, Korean use only `other`.
5. **Arabic uses all six categories** — the most complex plural system among common languages.
6. **Format specifiers must be preserved** — `%lld`, `%@`, `%d` etc. must appear in every plural variant exactly as in the source.

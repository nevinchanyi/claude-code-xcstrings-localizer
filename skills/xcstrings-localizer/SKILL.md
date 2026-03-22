---
name: xcstrings-localizer
description: "Localize, validate, and manage Apple .xcstrings (String Catalog) files for iOS/macOS apps. Trigger whenever the user works with .xcstrings files, Localizable.xcstrings, String Catalogs, iOS app localization, pluralization, or translation of app strings. Also trigger for adding languages to Xcode projects, fixing plural forms, generating translator comments, scanning code for string context, mapping project domain/terminology for accurate translations, or checking grammar in translations. Trigger phrases include 'localize my app', 'translate these strings', 'add comments to my strings', 'scan my project', 'prepare for translation', 'check grammar', 'proofread my translations', 'review my strings', 'quality check', 'validate translation quality'. Four commands: (1) Scan Domain - analyze project to build a glossary of ambiguous terms for translation accuracy, (2) Generate Comments - scan Swift/Storyboard/XIB code to write context-aware translator comments, (3) Localize - translate with correct CLDR plural rules, format specifier preservation, and domain-aware term disambiguation, (4) Check Grammar - review translation values for spelling, grammar, punctuation, capitalization consistency, and terminology consistency."
---

# xcstrings Localizer

A skill for localizing Apple .xcstrings (String Catalog) files. It has four commands that can be used independently or as a pipeline:

1. **Scan Domain** — Analyze the project to understand its domain, features, and terminology. Produces a domain report that guides accurate translations (e.g., knowing "trip" means a driving trip in a mileage tracker, not a vacation).
2. **Generate Comments** — Scan the project's source code, find where each string key is used, and write context-aware comments into the .xcstrings file. This prepares the file for translation.
3. **Localize** — Translate the .xcstrings file to target languages with correct plural forms, grammar validation, and format specifier preservation. Uses the domain report (if available) to choose contextually accurate translations.
4. **Check Grammar** — Review translation values across all languages for spelling, grammar, punctuation, capitalization consistency, and terminology consistency. Produces a report organized by language and severity, with optional auto-fix.

The recommended workflow is: scan domain → generate comments → localize → check grammar. But each command works standalone.

---

## Shared: xcstrings file structure

Both commands read and write the same JSON format. Understand this before doing anything.

```json
{
  "sourceLanguage": "en",
  "version": "1.0",
  "strings": {
    "string_key": {
      "comment": "Context for translators",
      "extractionState": "manual|extracted_with_value|stale",
      "shouldTranslate": true,
      "localizations": {
        "en": {
          "stringUnit": { "state": "translated", "value": "Hello" }
        }
      }
    }
  }
}
```

**Simple strings** → `localizations.<lang>.stringUnit.value`
**Plural strings** → `localizations.<lang>.variations.plural.<category>.stringUnit.value`
**Device variations** → `localizations.<lang>.variations.device.<device>.stringUnit.value`

Parse with Python `json` module. Write back with `json.dump(data, f, ensure_ascii=False, indent=2)`.

### Understanding keys vs values (critical)

In xcstrings, the dictionary key and the source-language value are **two different things**. There are two common patterns:

**Pattern A — Programmatic key:** The key is a developer identifier like `"greetings_onboarding"`, and the source-language value is the actual user-facing text like `"Hello, user!"`. The key itself is NOT a translation — it's just a code reference. You translate the **value**, never the key.

```json
"greetings_onboarding": {
  "localizations": {
    "en": { "stringUnit": { "state": "translated", "value": "Hello, user!" } }
  }
}
```
→ Translate `"Hello, user!"` to other languages. The key `"greetings_onboarding"` is irrelevant to translation.

**Pattern B — Key equals value:** The key IS the source text, like `"Hello, user!"` as both the key and the English value. This is common when developers use `Text("Hello, user!")` directly in SwiftUI without a separate key.

```json
"Hello, user!": {
  "localizations": {
    "en": { "stringUnit": { "state": "translated", "value": "Hello, user!" } }
  }
}
```
→ The key and value are the same. Translate the value to other languages.

**How to determine what to translate:**

1. Look at the **source-language localization value**, not the key. The value under `localizations.<sourceLanguage>.stringUnit.value` (or the plural/device variant values) is always the ground truth for translation.
2. If a key has **no source-language localization entry at all** (no value, just an empty `localizations` block or the source language is missing), the key itself serves as the default display text. In this case, treat the key as the source text to translate.
3. If a key is a programmatic identifier (e.g., `"settings_title"`, `"error.network.timeout"`) with **no source-language value**, do NOT translate the key literally — flag it to the user as missing a source value.
4. Never change the key itself. Keys are code references and must stay exactly as they are.

**Rule of thumb:** Always translate from `value` → target language. The key is just an address.

---

## Command 1: Scan Domain

**When to use:** Before translating, especially for projects where terms could be ambiguous. The user may say "scan my project", "understand my app first", "map my project domain", "what is my app about", or just "prepare for localization". Also use this if the user provides a project folder and asks for localization — run the domain scan first to get context.

**What you need from the user:**
- The project source code (uploaded folder, zip, or access to specific files)
- Optionally: a README, documentation files, or App Store metadata

### Step 1: Gather project signals

Run the bundled script `scripts/scan_project_domain.py` to extract structured data from the codebase:

```bash
python3 <skill-dir>/scripts/scan_project_domain.py \
  --project /path/to/project/source \
  --output /home/claude/domain_scan.json
```

The script extracts:
- **Swift type names** — class, struct, enum, and protocol declarations with their names
- **Enum cases** — especially valuable for understanding domain vocabulary (e.g., `case mileage`, `case fuelCost`, `case highway`)
- **README/doc content** — full text of README.md, README, CHANGELOG, docs/*.md
- **App Store metadata** — if an App Store Connect metadata file, fastlane metadata folder, or description text is found
- **Bundle identifiers and display names** — from .pbxproj or Info.plist if available
- **Import statements** — which frameworks are used (MapKit → maps, HealthKit → health, CoreLocation → location tracking, StoreKit → purchases, etc.)

### Step 2: Analyze and produce the domain report

Using the raw scan data, write a **domain report** with these sections:

#### 2a. App Purpose (1-2 paragraphs)
What does this app do? Who is it for? Describe it the way an App Store listing would. Derive this from the combination of README content, type/class names, enum cases, and framework imports.

#### 2b. Feature Map
List the app's major features or screens, inferred from View/ViewController class names and their related models. For example:
- `DashboardView` + `TripModel` + `MileageCalculator` → "Dashboard showing trip history and mileage statistics"
- `SettingsView` + `UserPreferences` + `SubscriptionManager` → "Settings with user preferences and subscription management"

#### 2c. Domain Glossary
This is the most important section for translation accuracy. List terms that appear in the app and could be ambiguous, with their meaning **in this specific project's context**.

Format each entry as:

| Term | Meaning in this app | Translation note |
|------|---------------------|------------------|
| trip | A single recorded driving journey with start/end points and mileage | NOT a vacation or travel booking. In Ukrainian: "поїздка", not "подорож" |
| route | A saved path between two locations for repeated trips | NOT an internet/networking route |
| log | A history record of a completed trip | NOT a system log or logging framework output |
| track / tracking | GPS-based recording of a trip in progress | NOT music tracks or shipment tracking |
| rate | Mileage reimbursement rate ($/mile) | NOT a rating/review or exchange rate |
| report | An expense/mileage report for tax purposes | NOT a bug report or analytics report |

Focus on terms that:
- Have multiple meanings across domains (trip, track, log, rate, note, post, feed, board, match, etc.)
- Are jargon specific to this domain that a translator needs to understand
- Appear in the .xcstrings string values

#### 2d. Framework Signals
List detected frameworks and what they imply for translation context:
- `CoreLocation` → app involves location/GPS, terms like "location", "coordinate", "accuracy" are spatial
- `MapKit` → mapping context, "pin", "annotation", "region" are map-related
- `HealthKit` → health/fitness context, "activity", "steps", "heart rate" are medical/fitness
- `StoreKit` → in-app purchases, "subscription", "restore", "purchase" are commerce terms
- `CoreBluetooth` → device connectivity, "peripheral", "scan", "connect" are BLE terms

#### 2e. UI Patterns
Note any detected UI patterns that affect translation:
- TabBar labels (need to be very short)
- Alert/confirmation dialogs (need to be clear and direct)
- Onboarding flows (need to be friendly and welcoming)
- Settings screens (need consistent, standard terminology)
- Widget/complication text (extremely limited space)

### Step 3: Save and present the report

Save the domain report as `/home/claude/domain_report.md` and present it to the user for review. They may correct terms or add context you couldn't infer.

If the user then proceeds to Command 2 (Generate Comments) or Command 3 (Localize), **read the domain report first** and use it to guide comment generation and translation choices.

---

## Command 2: Generate Comments

**When to use:** The user wants to add or improve comments in their .xcstrings file before sending it for translation. They may say things like "generate comments", "add context to my strings", "prepare my xcstrings for translation", "scan my code for string usage".

**What you need from the user:**
- The .xcstrings file (uploaded or path provided)
- The project source code (uploaded folder, zip, or access to specific files)

### Step 1: Scan the project source code

Run the bundled script `scripts/scan_string_usage.py` to find where each string key is used across the codebase:

```bash
python3 <skill-dir>/scripts/scan_string_usage.py \
  --xcstrings /path/to/Localizable.xcstrings \
  --project /path/to/project/source \
  --output /home/claude/string_usages.json
```

The script searches these file types:
- **Swift files (.swift)** — looks for `String(localized:)`, `NSLocalizedString`, `LocalizedStringKey`, `Text("key")`, direct string literal matches
- **Storyboard/XIB files (.storyboard, .xib)** — looks for string keys in XML attributes
- **Info.plist / InfoPlist.xcstrings** — identifies system-level strings (permissions, app name)

For each key found, the script extracts **2-3 surrounding lines** of code context — just enough to understand where and how the string appears in the UI, without pulling in entire files.

Output format:
```json
{
  "welcome_title": [
    {
      "file": "WelcomeView.swift",
      "line": 42,
      "context": "        VStack {\n>>>         Text(\"welcome_title\")\n            .font(.largeTitle)"
    }
  ],
  "save_button": [
    {
      "file": "ProfileEditor.swift",
      "line": 118,
      "context": ">>>     Button(\"save_button\") {\n            viewModel.save()"
    }
  ]
}
```

If the user hasn't provided source files, or some keys have no matches in the code, fall back to inferring context from the key name and source value alone.

### Step 2: Generate comments from code context

When generating comments, remember the key-vs-value distinction. The **source value** tells you what the user sees; the **key** tells you the developer's intent. Use both to write a good comment, but base the context description on the actual displayed text, not just the key name. For example, key `"greetings_onboarding"` with value `"Hello, user!"` → the comment should describe a greeting on the onboarding screen, not just echo the key.

For each string entry in the .xcstrings file, produce a comment with two parts:

1. **Context** — Where the string appears in the app. Derived from the code scan results:
   - What view/screen it's in (inferred from filename and surrounding code)
   - What UI element it's part of (Button, Text, Label, Alert, NavigationTitle, etc.)
   - Whether it's user-facing or system-level

2. **Translator guidance** — Practical notes for translators:
   - Format specifier explanations (`%@ is replaced with a username at runtime`)
   - Length constraints if the UI context suggests them (e.g., tab bar labels, buttons → keep short)
   - Tone guidance if inferable (alerts → formal/clear, onboarding → friendly)
   - Plural notes if the string has plural variations

**Format:** `"[Context]. [Translator guidance]."`

**Examples of good comments:**

| Key | Source Value | Code Context | Generated Comment |
|-----|-------------|-------------|-------------------|
| `welcome_title` | "Welcome to Mileafy" | `Text("welcome_title").font(.largeTitle)` in WelcomeView.swift | "Large title on the welcome/onboarding screen. Keep welcoming and concise." |
| `save_button` | "Save" | `Button("save_button") { viewModel.save() }` in ProfileEditor.swift | "Button label in the profile editor to save changes. Keep very short (max ~10 chars)." |
| `trips_count` | "%lld trips" | `Text("trips_count")` in DashboardView.swift | "Trip count displayed on the dashboard. %lld is replaced with the number of trips. Ensure correct plural form." |
| `delete_confirmation` | "Are you sure you want to delete %@?" | `Alert(title: Text("delete_confirmation"))` in TripListView.swift | "Confirmation alert before deleting an item. %@ is the item name. Keep the tone clear and direct." |
| `NSCameraUsageDescription` | "We need camera access to scan receipts" | InfoPlist.xcstrings | "iOS permission dialog text shown when the app requests camera access. Must clearly explain why the camera is needed. Apple may reject vague descriptions." |

### Step 3: Write comments into the .xcstrings file

Rules for writing comments:
- **Do NOT overwrite** existing comments that are clearly hand-written and specific (more than just a key echo or auto-generated placeholder).
- **Do overwrite** comments that are just the key name repeated, empty, or clearly auto-generated boilerplate like `"No comment provided by engineer"`.
- **Skip** entries with `shouldTranslate: false` — they don't need translator comments.
- The `comment` field goes at the top level of each string entry (sibling to `localizations`, not inside it).

### Step 4: Validate and output

Run the output validation checklist (see below) and deliver the updated .xcstrings file.

Present a summary to the user:
- How many comments were added/updated
- How many were preserved (already had good comments)
- How many keys had no code matches (comments inferred from key name only)
- Any string keys found in code but missing from the .xcstrings file (potential missing localizations)

---

## Command 3: Localize

**When to use:** The user wants to translate their .xcstrings file into one or more languages. They may say things like "localize to Ukrainian", "translate my xcstrings", "add German to my app", "fix the plural forms".

**What you need from the user:**
- The .xcstrings file (uploaded or path provided)
- Target languages (or "all existing" to fill in all languages already present in the file)
- Optionally: a domain report from Command 1 (if available, it significantly improves translation accuracy)

### Step 0: Load domain context (if available)

If a domain report exists (from Command 1, or a `domain_report.md` the user provides), read it before translating. Pay special attention to:
- **The Domain Glossary** — use the specified meanings when choosing translations. For example, if the glossary says `"trip" = a recorded driving journey`, translate it as "поїздка" (uk) not "подорож", "Fahrt" (de) not "Reise", "走行記録" (ja) not "旅行".
- **Framework Signals** — these tell you the domain context for technical terms.
- **UI Patterns** — these inform length constraints and tone.

If no domain report is available, and the project source is accessible, suggest running Command 1 first. If the user declines, proceed using whatever context is available from key names, values, and comments.

### Step 1: Read the file and CLDR rules

Parse the .xcstrings JSON. Identify:
- `sourceLanguage` — the language to translate FROM
- All language codes already present under each key's `localizations`
- Which keys have plural variations vs simple `stringUnit` entries
- Which keys have `shouldTranslate: false` (skip these)

Before translating, read `references/cldr-plural-rules.md` in this skill's directory. This tells you which plural categories each language requires. Wrong plural categories cause Xcode warnings or broken UI at runtime.

### Step 2: Validate source language grammar

Check the source language strings for:
- Typos and grammatical errors
- Inconsistent capitalization (e.g., some buttons Title Case, some lowercase)
- Missing or mismatched format specifiers across plural variants
- Unbalanced punctuation

Report issues to the user before translating. Don't auto-fix — let the user decide.

### Step 3: Translate

For each string key, for each target language:

**First, determine the source text to translate from** (see "Understanding keys vs values" above):
- Read the source-language value from `localizations.<sourceLanguage>.stringUnit.value`
- If the source language has no localization entry, and the key looks like natural language (contains spaces, punctuation, or is a full phrase), use the key as the source text
- If the source language has no localization entry and the key is a programmatic identifier (e.g., `"settings_title"`), flag it as missing a source value and skip — do NOT literally translate the key name

**Simple strings:**
- Translate the source **value** (not the key) to the target language
- Set `state` to `"translated"`
- Preserve all format specifiers (`%@`, `%lld`, `%d`, `%f`, `%.2f`, `%1$@`, etc.) exactly

**Plural strings:**
- Look up the target language's required plural categories in the CLDR reference
- Translate each required category with the grammatically correct form
- Set `state` to `"translated"` for each
- `other` is always required

**Critical plural rules:**
- Category counts vary per language: English=2, Ukrainian=4, Arabic=6, Japanese=1
- Each plural form must be fully grammatically correct — change nouns, verbs, adjectives as needed, not just the noun
- Slavic languages (ru, uk, pl, cs, sk, hr, sr): numbers ending in 11-19 use `many`/`other`, not `one`/`few`
- Languages with only `other` (zh, ja, ko, th, vi, tr, hu, id, ms): provide one translation under `other`

**Device variations:**
- Translate each device variant separately
- Preserve the device keys (iphone, ipad, mac, applevision, applewatch, other)

### Step 3b: Verify format specifiers in every translation

This is a hard requirement — if a format specifier is missing from a translation, the app will crash or show garbage at runtime.

**What are format specifiers?** They are placeholder tokens in strings that iOS replaces with dynamic values at runtime:
- `%@` — replaced with a string (name, title, label, etc.)
- `%lld` — replaced with an integer (count, number)
- `%d` — replaced with an integer (shorter form)
- `%f` — replaced with a floating-point number
- `%.2f` — float with 2 decimal places
- `%1$@`, `%2$@` — positional specifiers (1st argument, 2nd argument)

**Rules:**
1. Every format specifier present in the source value MUST appear in every translation of that string — no exceptions
2. The specifier tokens themselves are never translated — `%@` stays `%@`, `%lld` stays `%lld`
3. The count of each specifier type must match between source and translation
4. For positional specifiers (`%1$@`, `%2$@`), the numbers must be preserved but the order in the sentence can change to fit the target language's grammar
5. For plural strings, check every plural variant — each one must contain the same specifiers as the source

**Examples:**

| Source (en) | ✅ Correct (uk) | ❌ Wrong (uk) | Why wrong |
|-------------|-----------------|---------------|-----------|
| `"%@ apple(s)"` | `"%@ яблук"` | `"яблук"` | Missing `%@` — crash at runtime |
| `"%lld miles driven"` | `"%lld миль пройдено"` | `"миль пройдено"` | Missing `%lld` — number won't show |
| `"Hello, %@! You have %lld trips"` | `"Привіт, %@! У вас %lld поїздок"` | `"Привіт, %@! У вас поїздок"` | Missing `%lld` — count won't show |
| `"%1$@ shared %2$@ with you"` | `"%2$@ надіслано вам від %1$@"` | `"%@ надіслано вам від %@"` | Lost positional numbers — arguments will swap |

After translating each string, immediately verify that the set of format specifiers in the translation matches the source. If they don't match, fix the translation before moving on.

### Step 4: Handle existing translations

When a translation already exists:
- **Preserve it** if it looks correct
- **Flag it** with `"state": "needs_review"` if:
  - Format specifiers don't match the source
  - A plural string is missing required categories for that language
  - The translation is suspiciously identical to the source (possibly untranslated)
  - The translation has obvious grammar issues

Report all flagged entries to the user with explanations.

### Step 5: Output

Ask the user their preference:
- **Full file**: Complete .xcstrings as valid JSON. 2-space indent, matching Xcode's default.
- **Partial**: Only modified entries or a specific language — useful for very large files.

Write to `/home/claude/Localizable.xcstrings`, then copy to `/mnt/user-data/outputs/`.

---

## Command 4: Check Grammar

**When to use:** The user wants to review translation quality in their .xcstrings file. They may say things like "check grammar", "proofread my translations", "review my strings", "quality check my localization", "find errors in translations", "check spelling in my xcstrings", "validate translation quality".

**What you need from the user:**
- The .xcstrings file (uploaded or path provided)
- Optionally: specific languages to check (default: all languages present)
- Optionally: a domain report from Command 1 (improves terminology consistency checks)
- Optionally: whether to auto-fix issues or just report them

### Step 0: Load domain context (if available)

Same as Command 3. If a domain report exists (from Command 1, or a `domain_report.md` the user provides), read it before checking. The glossary enables terminology consistency checking — if the glossary says "trip" should be "поїздка" in Ukrainian, flag any translation that uses "подорож" for the same concept.

### Step 1: Extract translation values

Run the bundled script `scripts/extract_translation_values.py` to extract all translation values into a flat structure for review:

```bash
python3 <skill-dir>/scripts/extract_translation_values.py \
  --xcstrings /path/to/Localizable.xcstrings \
  --languages en,uk,de \
  --output /home/claude/grammar_check_input.json
```

If `--languages` is omitted, all languages present in the file are extracted.

Output format:
```json
{
  "sourceLanguage": "en",
  "languages": ["en", "uk", "de"],
  "entries": [
    {
      "key": "welcome_title",
      "comment": "Large title on welcome screen",
      "type": "simple",
      "values": {
        "en": "Welcome to Mileafy",
        "uk": "Ласкаво просимо до Mileafy",
        "de": "Willkommen bei Mileafy"
      },
      "format_specifiers": []
    },
    {
      "key": "trips_count",
      "comment": "Trip count on dashboard. %lld = number.",
      "type": "plural",
      "values": {
        "en": { "one": "%lld trip", "other": "%lld trips" },
        "uk": { "one": "%lld поїздка", "few": "%lld поїздки", "many": "%lld поїздок", "other": "%lld поїздок" }
      },
      "format_specifiers": ["%lld"]
    }
  ]
}
```

### Step 2: Check each language

For each target language (not the source language — source language grammar is checked in Command 3's Step 2), review every translation value for issues organized by severity:

**Severity: Error** (these cause incorrect user-facing text)
1. **Spelling errors** — misspelled words in the target language
2. **Broken grammar** — subject-verb disagreement, wrong case endings, incorrect conjugation, wrong gender agreement
3. **Plural form mismatch** — a plural variant uses the wrong grammatical number (e.g., the `one` form says "trips" instead of "trip", or Ukrainian `one` uses plural "поїздки" instead of singular "поїздка")
4. **Format specifier context** — grammar around placeholders is incorrect (e.g., wrong preposition before `%@` that would not work with possible substituted values, or wrong grammatical case that doesn't agree with the placeholder's role in the sentence)

**Severity: Warning** (these indicate inconsistency or quality issues)
5. **Punctuation issues** — missing terminal punctuation where other strings in the same role have it, unbalanced quotes/brackets/parentheses, wrong quotation mark style for the language (e.g., German uses „…" not "…")
6. **Capitalization inconsistency** — within the same language, similar UI elements use different capitalization patterns (e.g., some button labels Title Case, others sentence case). Group by UI role if comments indicate it.
7. **Terminology inconsistency** — the same source-language term is translated differently across strings without justification (e.g., "Settings" translated as both "Einstellungen" and "Konfiguration" in German). If a domain glossary is available, also flag translations that deviate from the glossary.

**Severity: Info** (suggestions for improvement)
8. **Overly literal translation** — phrasing that is grammatically correct but sounds unnatural to a native speaker
9. **Length warning** — translation is significantly longer than source (more than 150%), which may cause UI truncation, especially for buttons, tab labels, and navigation titles

**Rules for checking:**
- Format specifiers (`%@`, `%lld`, `%d`, `%f`, positional variants like `%1$@`) are NOT grammar errors — they are runtime placeholders. Check that the surrounding grammar works correctly with what they represent.
- If a comment explains what `%@` is replaced with (e.g., "a username"), use that context to verify grammatical correctness around the placeholder.
- For plural forms, verify that each category (`zero`, `one`, `two`, `few`, `many`, `other`) uses the grammatically correct number form for that language. Reference `references/cldr-plural-rules.md` to understand what numbers each category covers.
- Skip entries with `shouldTranslate: false`.
- If the user explicitly asks to also check the source language, do so — but by default only check target languages.

### Step 3: Cross-language consistency checks

After checking each language individually, perform cross-language checks:

1. **Missing translations** — keys that have translations in some languages but not others (informational)
2. **Inconsistent punctuation across languages** — if the source uses `"..."` (ellipsis character) but some translations use `"..."` (three dots), or vice versa
3. **Inconsistent brand/proper noun handling** — app name or product names should generally stay untranslated; flag if translated inconsistently

### Step 4: Produce the report

Present the report as markdown, organized by language, then by severity:

```markdown
# Grammar Check Report

**File:** Localizable.xcstrings
**Languages checked:** en, uk, de, fr
**Total strings checked:** 142
**Issues found:** 23

## Ukrainian (uk) — 12 issues

### Errors (3)
| Key | Value | Issue |
|-----|-------|-------|
| `welcome_title` | "Ласкаво просимо до Mileafi" | Spelling: app name misspelled. Should be "Mileafy" |
| `trips_count.one` | "%lld поїздки" | Plural: `one` form should use singular "поїздка", not plural "поїздки" |
| `delete_confirm` | "Ви впевнені що хочете видалити?" | Missing comma after "впевнені" |

### Warnings (5)
| Key | Value | Issue |
|-----|-------|-------|
| `save_button` | "зберегти" | Capitalization: other buttons use title case ("Скасувати"), this is lowercase |
| `settings_title` vs `preferences_title` | "Налаштування" vs "Параметри" | Terminology: "Settings" translated inconsistently |
| ... | ... | ... |

### Info (4)
| Key | Value | Issue |
|-----|-------|-------|
| `onboarding_description` | "Цей застосунок допомагає..." | Length: 180% of source length, may truncate in UI |
| ... | ... | ... |

## German (de) — 11 issues
...

## Cross-Language Issues (2)
| Issue | Details |
|-------|---------|
| Missing translations | `new_feature_title` missing in: de, fr |
| Punctuation mismatch | `loading_message`: source uses "…" but de uses "..." |
```

### Step 5: Auto-fix (optional)

If the user requested auto-fix mode:

1. Apply corrections for **Error** and **Warning** severity issues only
2. Present each fix with before/after for user approval:
   ```
   trips_count.one [uk]:
     Before: "%lld поїздки"
     After:  "%lld поїздка"
     Reason: `one` form requires singular noun
   ```
3. After user confirms, write the corrected .xcstrings file using `json.dump(data, f, ensure_ascii=False, indent=2)`
4. Run the standard output validation checklist (see below)
5. Never auto-fix **Info** items — those are subjective suggestions

If the user did not request auto-fix, present the report and ask if they want any issues fixed.

---

## Output validation checklist

Run this before delivering ANY .xcstrings file from either command:

1. ✅ Valid JSON (parse with Python to verify — if it fails, fix and re-verify)
2. ✅ `sourceLanguage` and `version` preserved from input
3. ✅ All original string keys present (nothing dropped)
4. ✅ **All format specifiers preserved in every translation** (see validation script below)
5. ✅ Plural categories match CLDR rules for each target language
6. ✅ `state` field present in every `stringUnit`
7. ✅ `shouldTranslate: false` entries left untouched
8. ✅ `extractionState` preserved on every entry that had it
9. ✅ `comment` field is a sibling of `localizations`, not nested inside it
10. ✅ No encoding issues — Cyrillic, CJK, Arabic, etc. render correctly (use `ensure_ascii=False`)

Always run this validation script on the output before delivering it:

```python
import json, re

FORMAT_SPEC_RE = re.compile(r'%(?:\d+\$)?[@dDuUxXoOfeEgGcCsSpnlLqhz]|%(?:\d+\$)?(?:\.\d+)?[fFeEgG]|%(?:\d+\$)?l{0,2}[dDiIuUxXoO]')

def extract_specifiers(value):
    """Extract sorted list of format specifiers from a string."""
    return sorted(FORMAT_SPEC_RE.findall(value))

def get_all_values(loc_data):
    """Get all string values from a localization entry (simple, plural, or device)."""
    values = []
    if "stringUnit" in loc_data:
        values.append(loc_data["stringUnit"].get("value", ""))
    if "variations" in loc_data:
        for var_type in ("plural", "device"):
            if var_type in loc_data["variations"]:
                for cat_data in loc_data["variations"][var_type].values():
                    if "stringUnit" in cat_data:
                        values.append(cat_data["stringUnit"].get("value", ""))
    return values

with open('output.xcstrings', 'r', encoding='utf-8') as f:
    data = json.load(f)

assert "sourceLanguage" in data
assert "version" in data
assert "strings" in data
src_lang = data["sourceLanguage"]
errors = []

for key, entry in data["strings"].items():
    if entry.get("shouldTranslate") is False:
        continue
    locs = entry.get("localizations", {})
    if src_lang not in locs:
        continue
    # Collect source specifiers from all source values
    src_values = get_all_values(locs[src_lang])
    src_specs = set()
    for v in src_values:
        src_specs.update(extract_specifiers(v))
    if not src_specs:
        continue  # No specifiers to check
    # Check each target language
    for lang, loc_data in locs.items():
        if lang == src_lang:
            continue
        for tv in get_all_values(loc_data):
            t_specs = extract_specifiers(tv)
            for spec in src_specs:
                if t_specs.count(spec) < sorted(list(src_specs)).count(spec):
                    errors.append(f"  ❌ {key} [{lang}]: missing {spec} in \"{tv}\"")

if errors:
    print(f"❌ FORMAT SPECIFIER ERRORS ({len(errors)}):")
    for e in errors:
        print(e)
    print("\nFix these before delivering — missing specifiers cause runtime crashes.")
else:
    print(f"✅ Valid xcstrings with {len(data['strings'])} keys, all format specifiers preserved")
```

---

## Handling large files

Files with 100+ string keys can exceed context limits. Use a Python script approach:

1. Load the entire JSON into memory
2. Process strings in batches of ~20 keys
3. For each batch: read source values, translate/comment, write back to the in-memory structure
4. Write the final result once with `json.dump(data, f, ensure_ascii=False, indent=2)`

This keeps the full file intact while working within token limits.

---

## Common pitfalls

1. **Don't add plural categories a language doesn't use.** Turkish uses only `other` — don't add `one`.
2. **Don't remove plural categories the source has.** If source has `zero`, keep it.
3. **Don't translate format specifiers.** `%@` stays `%@`, `%lld` stays `%lld`.
4. **Don't change key names.** They're code references.
5. **Don't lose `extractionState`.** Preserve it.
6. **Don't translate `shouldTranslate: false` entries.**
7. **Watch for string interpolation.** Swift `\(name)` becomes `%@` in xcstrings.
8. **Respect positional specifiers.** `%1$@` and `%2$@` may reorder across languages, but the position numbers must stay correct.
9. **Comments go at string-entry level.** Sibling to `localizations` and `extractionState`, not inside a localization.

---

## Language code mapping

Apple uses BCP 47 codes. Common mappings:
- `en` English, `fr` French, `de` German, `es` Spanish, `it` Italian, `pt` Portuguese, `pt-BR` Brazilian Portuguese
- `zh-Hans` Simplified Chinese, `zh-Hant` Traditional Chinese, `ja` Japanese, `ko` Korean
- `uk` Ukrainian, `ru` Russian, `pl` Polish, `cs` Czech, `sk` Slovak, `hr` Croatian, `sr` Serbian
- `ar` Arabic, `he` Hebrew, `hi` Hindi, `th` Thai, `vi` Vietnamese, `id` Indonesian, `ms` Malay
- `nb` Norwegian Bokmål, `nn` Norwegian Nynorsk, `da` Danish, `sv` Swedish, `fi` Finnish
- `nl` Dutch, `el` Greek, `ro` Romanian, `hu` Hungarian, `tr` Turkish, `ca` Catalan
- `sr-Latn` Serbian (Latin)

Map user language names to the correct Apple code.

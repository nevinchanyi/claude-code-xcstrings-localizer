# xcstrings-localizer — Setup & Usage Guide

## What's inside

The `xcstrings-localizer.skill` file is a packaged skill containing:

```
xcstrings-localizer/
├── SKILL.md                           — Instructions for Claude (4 commands)
├── scripts/
│   ├── scan_project_domain.py         — Extracts app domain context from Swift code
│   ├── scan_string_usage.py           — Finds where each string key is used in code
│   └── extract_translation_values.py  — Extracts translation values for grammar review
└── references/
    └── cldr-plural-rules.md           — Plural form rules for 40+ languages
```

---

## Installation

You can use this skill in **Claude.ai** (web/app) or **Claude Code** (terminal).

### Option A: Claude.ai (web or desktop app)

1. Go to **Settings → Customize → Skills**
2. Make sure **Code execution and file creation** is enabled in **Settings → Capabilities**
3. Click **Add Skill** (or drag and drop)
4. Upload the `xcstrings-localizer.skill` file
5. Toggle the skill **ON**

That's it. Claude will now automatically use this skill when you mention `.xcstrings` files, localization, or translation in the context of iOS/macOS development.

### Option B: Claude Code (terminal)

**Per-project install** (recommended — travels with your repo):

```bash
# From your Xcode project root
mkdir -p .claude/skills
unzip xcstrings-localizer.skill -d .claude/skills/xcstrings-localizer
```

**Global install** (available in all projects):

```bash
mkdir -p ~/.claude/skills
unzip xcstrings-localizer.skill -d ~/.claude/skills/xcstrings-localizer
```

---

## The 4-Command Pipeline

The skill has four commands. You can run them in order for best results, or use any one standalone.

```
┌──────────────┐     ┌────────────────────┐     ┌──────────────┐     ┌──────────────┐
│  1. Scan      │ ──▶ │  2. Generate        │ ──▶ │  3. Localize  │ ──▶ │  4. Check     │
│     Domain    │     │     Comments        │     │              │     │     Grammar   │
│              │     │                    │     │              │     │              │
│ Understands   │     │ Scans Swift code    │     │ Translates    │     │ Reviews all   │
│ your app's    │     │ to write context-   │     │ with correct  │     │ translations  │
│ domain &      │     │ aware translator    │     │ plural forms  │     │ for spelling, │
│ terminology   │     │ comments into       │     │ & domain-     │     │ grammar, and  │
│              │     │ .xcstrings          │     │ accurate      │     │ consistency   │
│ Output:       │     │                    │     │ terms         │     │              │
│ domain_report │     │ Output:             │     │              │     │ Output:       │
│ .md           │     │ commented           │     │ Output:       │     │ grammar      │
│              │     │ .xcstrings          │     │ localized     │     │ report +     │
│              │     │                    │     │ .xcstrings    │     │ optional fix  │
└──────────────┘     └────────────────────┘     └──────────────┘     └──────────────┘
```

---

## Command 1: Scan Domain

**Purpose:** Understand your app's domain so translations are contextually accurate. For example, "trip" in a mileage tracker should translate to "поїздка" (a drive), not "подорож" (a vacation).

**What to provide:**
- Your project source folder (or upload it as a ZIP)

**What to say:**

> Scan my project to understand the domain before localizing.

or

> Here's my project. Analyze it and create a domain glossary for translation.

**What you get back:**
- A domain report with: app purpose, feature map, domain glossary (ambiguous terms with their meaning in YOUR app), framework signals, and UI patterns
- Review it — correct any terms Claude got wrong before moving to translation

---

## Command 2: Generate Comments

**Purpose:** Scan your Swift/Storyboard/XIB code to find where each string key is used, then write translator comments into your `.xcstrings` file.

**What to provide:**
- Your `.xcstrings` file
- Your project source code

**What to say:**

> Generate comments for my Localizable.xcstrings based on the code context.

or

> Add translator comments to my xcstrings file. Here's my project code.

**What you get back:**
- An updated `.xcstrings` file with comments like:
  - `"Button label in the profile editor to save changes. Keep very short (max ~10 chars)."`
  - `"Trip count on the dashboard. %lld is replaced with the number of trips. Ensure correct plural form."`
- A summary: how many comments added, how many preserved, any keys missing from the code

---

## Command 3: Localize

**Purpose:** Translate your `.xcstrings` file to target languages with correct plural forms, preserved format specifiers, and domain-aware terminology.

**What to provide:**
- Your `.xcstrings` file (ideally already with comments from Command 2)
- Target languages (e.g., "Ukrainian, German, Japanese") or "all existing languages"
- Optionally: the domain report from Command 1

**What to say:**

> Localize my Localizable.xcstrings to Ukrainian, German, and Japanese.

or

> Translate all existing languages in my xcstrings file.

or

> Add Polish to my xcstrings and translate all strings.

**What you get back:**
- A fully localized `.xcstrings` file with:
  - Correct CLDR plural categories per language (e.g., Ukrainian gets `one/few/many/other`)
  - All `%@`, `%lld`, etc. format specifiers preserved in every translation
  - Existing translations preserved, suspicious ones flagged as `needs_review`
  - Valid JSON that opens cleanly in Xcode

---

## Command 4: Check Grammar

**Purpose:** Review all translation values for spelling, grammar, punctuation, capitalization consistency, and terminology consistency. Produces a report organized by language and severity, with optional auto-fix.

**What to provide:**
- Your `.xcstrings` file (with existing translations)
- Optionally: specific languages to check
- Optionally: the domain report from Command 1

**What to say:**

> Check grammar in my Localizable.xcstrings translations.

or

> Proofread the Ukrainian and German translations in my xcstrings file.

or

> Quality check my translations and fix any errors.

**What you get back:**
- A report organized by language with issues sorted by severity:
  - **Errors:** spelling, broken grammar, wrong plural forms
  - **Warnings:** punctuation issues, capitalization/terminology inconsistencies
  - **Info:** overly literal phrasing, length warnings
- Cross-language consistency checks (missing translations, punctuation mismatches)
- Optional auto-fix: Claude presents before/after for each fix and applies them after your approval

---

## Full Workflow Example

Here's a typical session from start to finish. Adapt to your own project.

### Step 1: Upload your project

Upload your project folder (or ZIP) and your `Localizable.xcstrings` file to the chat.

### Step 2: Scan domain

> Scan my project to understand the domain. I need to localize this app.

Claude will output a domain report. Review the glossary — correct any terms if needed:

> "trip" is correct — it means a recorded driving journey.
> But "log" in my app means a debug log, not a trip record. Fix that.

### Step 3: Generate comments

> Now generate comments for my Localizable.xcstrings based on the project code.

Claude scans the Swift files, finds where each key is used, and writes comments. Download the updated `.xcstrings`.

### Step 4: Localize

> Localize to Ukrainian, German, Japanese, and French.

Claude translates everything using:
- The domain glossary (so "trip" → "поїздка" not "подорож")
- CLDR plural rules (Ukrainian gets 4 forms, Japanese gets 1)
- Code context from comments (buttons kept short, alerts kept clear)

### Step 5: Check grammar

> Check grammar in my translations.

Claude reviews all translations and produces a report with errors, warnings, and suggestions. If issues are found, you can ask Claude to auto-fix them.

### Step 6: Verify and use

Download the output `.xcstrings` file. Open it in Xcode — it should load cleanly with all languages populated. Build your project to verify no warnings about missing plural forms or format specifiers.

---

## Tips

**Large files (100+ strings):** Tell Claude to process in batches or ask for specific languages only:
> Just localize to Ukrainian for now.

**Adding a new language later:** Upload the already-localized `.xcstrings` and ask:
> Add Arabic to my xcstrings file and translate all strings.

**Fixing specific translations:** You can ask for targeted fixes:
> The Ukrainian translation of "trips_count" is wrong. "Поїздка" should be "поїздка" (lowercase). Fix it.

**Updating after code changes:** If you added new strings to your app, re-upload the `.xcstrings` and ask:
> I added new strings. Translate only the untranslated entries to all existing languages.

**Format specifiers are sacred:** The skill will verify that `%@`, `%lld`, `%d`, etc. appear in every translation. If any are missing, it will flag them before giving you the file. This prevents runtime crashes.

---

## Troubleshooting

**"Claude didn't use the skill"**
Be explicit: mention `.xcstrings`, `localize`, or `translate` in your message. If Claude still doesn't trigger the skill, say "Use the xcstrings-localizer skill."

**"The output file won't open in Xcode"**
The skill validates JSON before delivering, but if something went wrong, ask: "Validate the output xcstrings file and fix any JSON errors."

**"Plural forms are wrong for my language"**
The CLDR reference covers 40+ languages. If yours isn't listed, tell Claude: "Ukrainian uses one/few/many/other plural forms. Here are the rules: ..." and it will follow them.

**"Some translations sound too literal"**
Run Command 1 (Scan Domain) first — the domain glossary dramatically improves translation quality. Without it, Claude relies on the string values alone.

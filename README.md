# xcstrings-localizer

A Claude Skill for localizing Apple `.xcstrings` (String Catalog) files with correct CLDR plural rules, domain-aware translations, and code-context comments.

## What it does

| Command | Purpose |
|---------|---------|
| **Scan Domain** | Analyzes your Swift project to understand the app's domain, building a glossary of ambiguous terms (e.g., "trip" = driving journey, not vacation) |
| **Generate Comments** | Scans Swift/Storyboard/XIB code to find where each string key is used, writes context-aware translator comments into `.xcstrings` |
| **Localize** | Translates to target languages with correct plural forms per CLDR rules, preserved `%@`/`%lld` format specifiers, and domain-accurate terminology |

## Quick start

### Install in Claude.ai

1. Download `xcstrings-localizer.skill` from [Releases](../../releases)
2. Go to **Settings → Customize → Skills**
3. Upload the `.skill` file and toggle it **ON**

### Install in Claude Code

```bash
# Per-project (recommended)
mkdir -p .claude/skills
cp -r xcstrings-localizer .claude/skills/

# Or global
mkdir -p ~/.claude/skills
cp -r xcstrings-localizer ~/.claude/skills/
```

### Use it

```
You: Scan my project and localize Localizable.xcstrings to Ukrainian, German, and Japanese.
```

See [USAGE_GUIDE.md](USAGE_GUIDE.md) for the full step-by-step walkthrough.

## What's inside

```
xcstrings-localizer/
├── SKILL.md                          — Skill instructions (3 commands)
├── scripts/
│   ├── scan_project_domain.py        — Extracts types, enums, imports, README, metadata
│   └── scan_string_usage.py          — Finds string key usages with 2-3 lines of code context
├── references/
│   └── cldr-plural-rules.md          — Plural categories for 40+ languages
└── evals/
    └── test_input.xcstrings          — Sample file for testing
```

## Key features

- **CLDR plural rules** — Ukrainian gets `one/few/many/other`, Japanese gets only `other`, Arabic gets all six. Bundled reference for 40+ languages.
- **Format specifier validation** — Verifies `%@`, `%lld`, `%d`, etc. appear in every translation. Missing specifiers = runtime crash.
- **Domain glossary** — Scans your Swift types, enums, imports, and README to disambiguate terms like "trip", "route", "rate", "log", "track".
- **Code-aware comments** — Knows that `"save_button"` is used in a `Button()` inside `ProfileEditor.swift`, so it writes: "Button label in the profile editor. Keep very short."
- **Key vs value awareness** — Understands that key `"greetings_onboarding"` with value `"Hello, user!"` means translate the value, not the key.
- **Preserves existing work** — Doesn't overwrite hand-written comments or correct translations. Flags suspicious ones as `needs_review`.

## Requirements

- Claude Pro, Max, Team, or Enterprise plan
- **Code execution** enabled in Settings → Capabilities
- Python 3.10+ (available in Claude's sandbox by default)

## License

MIT

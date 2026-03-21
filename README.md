# xcstrings-localizer

A Claude Code plugin for localizing Apple `.xcstrings` (String Catalog) files with correct CLDR plural rules, domain-aware translations, and code-context comments.

## Install

### Claude Code (recommended)

```bash
# Add the marketplace
/plugin marketplace add YOUR_USERNAME/xcstrings-localizer

# Install the plugin
/plugin install xcstrings-localizer
```

Or install directly from the repo:

```bash
# Per-project
mkdir -p .claude/skills
cp -r skills/xcstrings-localizer .claude/skills/

# Global (all projects)
mkdir -p ~/.claude/skills
cp -r skills/xcstrings-localizer ~/.claude/skills/
```

### Claude.ai (web/app)

1. Download `xcstrings-localizer.skill` from [Releases](../../releases)
2. Go to **Settings → Customize → Skills**
3. Upload the `.skill` file and toggle it **ON**

## Commands

| # | Command | What it does |
|---|---------|--------------|
| 1 | **Scan Domain** | Analyzes Swift types, enums, imports, README to build a glossary of ambiguous terms (e.g., "trip" = driving journey, not vacation) |
| 2 | **Generate Comments** | Scans Swift/Storyboard/XIB code to find string key usage, writes context + translator guidance into `.xcstrings` |
| 3 | **Localize** | Translates with correct CLDR plural forms per language, preserved `%@`/`%lld` specifiers, and domain-accurate terms |

## Usage

```
You: Scan my project and localize Localizable.xcstrings to Ukrainian, German, and Japanese.
```

See [USAGE_GUIDE.md](USAGE_GUIDE.md) for the full step-by-step walkthrough.

## What's inside

```
.claude-plugin/
├── plugin.json                       — Plugin manifest for Claude Code
└── marketplace.json                  — Marketplace catalog (single plugin)
skills/
└── xcstrings-localizer/
    ├── SKILL.md                      — Skill instructions (3 commands)
    ├── scripts/
    │   ├── scan_project_domain.py    — Extracts types, enums, imports, README
    │   └── scan_string_usage.py      — Finds string key usages with code context
    └── references/
        └── cldr-plural-rules.md      — Plural categories for 40+ languages
```

## Key features

- **CLDR plural rules** for 40+ languages (Ukrainian=4 forms, Japanese=1, Arabic=6)
- **Format specifier validation** — verifies `%@`, `%lld` etc. in every translation
- **Domain glossary** — disambiguates terms like "trip", "route", "rate" using your actual codebase
- **Code-aware comments** — knows a key is used in a `Button()` vs `.navigationTitle()` vs `.alert()`
- **Key vs value awareness** — translates from the source value, not the key name
- **Preserves existing work** — flags suspicious translations as `needs_review`

## Requirements

- Claude Pro, Max, Team, or Enterprise plan
- Claude Code 1.0+ (for plugin install) or Claude.ai with Code execution enabled

## License

MIT

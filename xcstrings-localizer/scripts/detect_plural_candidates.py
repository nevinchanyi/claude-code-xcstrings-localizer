#!/usr/bin/env python3
"""
detect_plural_candidates.py — Scan an .xcstrings file for simple strings that
should have plural variations (contain integer format specifiers like %lld, %d).

Usage:
    python3 detect_plural_candidates.py \
        --xcstrings /path/to/Localizable.xcstrings \
        --output /path/to/plural_candidates.json

Detects:
    1. Simple stringUnit entries containing %lld, %d, %ld that need plural forms
    2. Entries with variations.plural in some languages but simple stringUnit in others
    3. Entries with variations.plural but missing CLDR categories for some languages

Output: JSON with a list of candidates and their current state.
"""

import argparse
import json
import re
import sys
from pathlib import Path


# Integer format specifiers that indicate countable values needing plural forms
INTEGER_SPEC_RE = re.compile(
    r'%(?:\d+\$)?l{1,2}[dDiIuUxXoO]'
    r'|%(?:\d+\$)?[dDiIuUxXoO]'
)

# Pattern: %@ followed by a word that looks like a countable noun (plural or singular)
# This catches cases like "%@ recordings", "%@ items", "%@ files selected"
# where the developer used \(count) instead of proper integer formatting
GENERIC_SPEC_WITH_NOUN_RE = re.compile(
    r'%@\s+\w+'
)

# CLDR plural categories required per language
# Source: references/cldr-plural-rules.md
CLDR_CATEGORIES = {
    # other only
    "zh-Hans": ["other"], "zh-Hant": ["other"], "ja": ["other"],
    "ko": ["other"], "th": ["other"], "vi": ["other"], "id": ["other"],
    "ms": ["other"], "hu": ["other"], "tr": ["other"],
    # one + other
    "en": ["one", "other"], "de": ["one", "other"], "es": ["one", "other"],
    "fr": ["one", "other"], "it": ["one", "other"], "pt": ["one", "other"],
    "pt-BR": ["one", "other"], "nl": ["one", "other"], "sv": ["one", "other"],
    "da": ["one", "other"], "nb": ["one", "other"], "nn": ["one", "other"],
    "fi": ["one", "other"], "el": ["one", "other"], "he": ["one", "other"],
    "hi": ["one", "other"], "ca": ["one", "other"],
    # one + few + other
    "ro": ["one", "few", "other"],
    # one + few + many + other
    "uk": ["one", "few", "many", "other"],
    "ru": ["one", "few", "many", "other"],
    "pl": ["one", "few", "many", "other"],
    "cs": ["one", "few", "many", "other"],
    "sk": ["one", "few", "many", "other"],
    "hr": ["one", "few", "many", "other"],
    "sr": ["one", "few", "many", "other"],
    "sr-Latn": ["one", "few", "many", "other"],
    # zero + one + two + few + many + other
    "ar": ["zero", "one", "two", "few", "many", "other"],
}

# Default for unknown languages
DEFAULT_CATEGORIES = ["one", "other"]


def has_integer_specifier(value):
    """Check if a string value contains an integer format specifier."""
    return bool(INTEGER_SPEC_RE.search(value))


def has_generic_spec_with_noun(value):
    """Check if a string has %@ followed by a word (likely count + noun)."""
    return bool(GENERIC_SPEC_WITH_NOUN_RE.search(value))


def get_integer_specifiers(value):
    """Extract integer format specifiers from a string value."""
    return INTEGER_SPEC_RE.findall(value)


def get_required_categories(lang_code):
    """Get required CLDR plural categories for a language."""
    return CLDR_CATEGORIES.get(lang_code, DEFAULT_CATEGORIES)


def get_source_value(entry_data, source_lang, key):
    """Get the source language value for an entry."""
    locs = entry_data.get("localizations", {})
    if source_lang in locs:
        loc = locs[source_lang]
        if "stringUnit" in loc:
            return loc["stringUnit"].get("value", "")
        if "variations" in loc and "plural" in loc["variations"]:
            # Already plural in source — get the "other" form as representative
            other = loc["variations"]["plural"].get("other", {})
            return other.get("stringUnit", {}).get("value", "")
    # Pattern B: key is the value
    return key


def analyze_entry(key, entry_data, source_lang):
    """Analyze a single entry for plural issues.

    Returns a candidate dict if issues found, None otherwise.
    """
    if entry_data.get("shouldTranslate") is False:
        return None

    locs = entry_data.get("localizations", {})
    if not locs:
        return None

    source_value = get_source_value(entry_data, source_lang, key)

    # Check if value has integer specifiers OR %@ with a countable noun
    is_integer = has_integer_specifier(source_value)
    is_generic_count = has_generic_spec_with_noun(source_value) and not is_integer

    if not is_integer and not is_generic_count:
        return None

    specifiers = get_integer_specifiers(source_value) if is_integer else ["%@"]
    needs_specifier_fix = is_generic_count  # %@ should become %lld
    has_multiple_counts = len(specifiers) > 1  # Multiple %lld in one string
    languages_present = sorted(locs.keys())

    # Analyze each language's structure
    simple_languages = []  # Languages with stringUnit (need conversion)
    plural_languages = {}  # Languages with variations.plural and their categories
    missing_categories = {}  # Languages with plural but missing categories

    for lang in languages_present:
        loc = locs[lang]
        if "stringUnit" in loc:
            simple_languages.append(lang)
        elif "variations" in loc and "plural" in loc["variations"]:
            existing_cats = sorted(loc["variations"]["plural"].keys())
            required_cats = get_required_categories(lang)
            plural_languages[lang] = existing_cats
            missing = [c for c in required_cats if c not in existing_cats]
            if missing:
                missing_categories[lang] = missing

    # Determine if this entry needs fixing
    issues = []

    if has_multiple_counts:
        issues.append({
            "type": "multiple_counts",
            "count": len(specifiers),
            "description": f"String has {len(specifiers)} countable values — iOS plural variations can only vary on one number per string. Recommend splitting into separate strings."
        })

    if needs_specifier_fix:
        issues.append({
            "type": "wrong_specifier",
            "description": "%@ should be %lld for integer count — developer likely used \\(count) string interpolation instead of %lld"
        })

    if simple_languages:
        issues.append({
            "type": "needs_plural",
            "languages": simple_languages,
            "description": f"Simple stringUnit needs plural variations in: {', '.join(simple_languages)}"
        })

    if missing_categories:
        for lang, missing in missing_categories.items():
            issues.append({
                "type": "missing_categories",
                "language": lang,
                "existing": plural_languages[lang],
                "missing": missing,
                "description": f"{lang}: has {'/'.join(plural_languages[lang])} but needs {'/'.join(missing)} too"
            })

    if not issues:
        return None

    return {
        "key": key,
        "source_value": source_value,
        "specifiers": specifiers,
        "needs_specifier_fix": needs_specifier_fix,
        "has_multiple_counts": has_multiple_counts,
        "languages_present": languages_present,
        "simple_languages": simple_languages,
        "plural_languages": {k: v for k, v in plural_languages.items()},
        "missing_categories": missing_categories,
        "issues": issues,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Detect strings that need plural form conversion"
    )
    parser.add_argument(
        "--xcstrings", required=True,
        help="Path to the .xcstrings file"
    )
    parser.add_argument(
        "--output", required=True,
        help="Path for the output JSON file"
    )
    args = parser.parse_args()

    xcstrings_path = Path(args.xcstrings)
    if not xcstrings_path.exists():
        print(f"Error: File not found: {xcstrings_path}", file=sys.stderr)
        sys.exit(1)

    with open(xcstrings_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    source_lang = data.get("sourceLanguage", "en")
    strings_data = data.get("strings", {})

    candidates = []
    for key in sorted(strings_data.keys()):
        candidate = analyze_entry(key, strings_data[key], source_lang)
        if candidate:
            candidates.append(candidate)

    output = {
        "sourceLanguage": source_lang,
        "totalStrings": len(strings_data),
        "candidatesFound": len(candidates),
        "candidates": candidates,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Found {len(candidates)} plural candidates out of {len(strings_data)} strings")
    for c in candidates:
        print(f"  - {c['key']}: {', '.join(i['description'] for i in c['issues'])}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
extract_translation_values.py — Extract all translation values from an .xcstrings
file into a flat JSON structure optimized for grammar review.

Usage:
    python3 extract_translation_values.py \
        --xcstrings /path/to/Localizable.xcstrings \
        --languages en,uk,de \
        --output /path/to/grammar_check_input.json

If --languages is omitted, all languages present in the file are extracted.

Output: JSON with sourceLanguage, languages list, and entries array.
Each entry has key, comment, type (simple/plural/device), values (per-language),
and format_specifiers list.
"""

import argparse
import json
import re
import sys
from pathlib import Path


# Format specifier regex — matches iOS/macOS format specifiers in strings
FORMAT_SPEC_RE = re.compile(
    r'%(?:\d+\$)?l{1,2}[dDiIuUxXoO]'
    r'|%(?:\d+\$)?(?:\.\d+)?[fFeEgG]'
    r'|%(?:\d+\$)?[@dDuUxXoOfeEgGcCsSpqhz]'
)


def extract_specifiers(value):
    """Extract sorted list of format specifiers from a string value."""
    return sorted(FORMAT_SPEC_RE.findall(value))


def get_values_for_localization(loc_data):
    """Extract values from a localization entry.

    Returns:
        - For simple strings: the string value
        - For plural variations: dict of {category: value}
        - For device variations: dict of {device: value}
    """
    if "stringUnit" in loc_data:
        return loc_data["stringUnit"].get("value", "")

    if "variations" in loc_data:
        if "plural" in loc_data["variations"]:
            result = {}
            for category, cat_data in loc_data["variations"]["plural"].items():
                if "stringUnit" in cat_data:
                    result[category] = cat_data["stringUnit"].get("value", "")
            return result
        if "device" in loc_data["variations"]:
            result = {}
            for device, dev_data in loc_data["variations"]["device"].items():
                if "stringUnit" in dev_data:
                    result[device] = dev_data["stringUnit"].get("value", "")
            return result

    return None


def determine_type(loc_data):
    """Determine the string type from any localization entry."""
    if "variations" in loc_data:
        if "plural" in loc_data["variations"]:
            return "plural"
        if "device" in loc_data["variations"]:
            return "device"
    return "simple"


def collect_all_languages(strings_data):
    """Collect all unique language codes across all string entries."""
    languages = set()
    for entry in strings_data.values():
        localizations = entry.get("localizations", {})
        languages.update(localizations.keys())
    return sorted(languages)


def collect_format_specifiers(entry_data, source_lang):
    """Collect format specifiers from the source language value."""
    localizations = entry_data.get("localizations", {})
    if source_lang not in localizations:
        return []

    loc_data = localizations[source_lang]
    all_values = []

    if "stringUnit" in loc_data:
        all_values.append(loc_data["stringUnit"].get("value", ""))
    if "variations" in loc_data:
        for var_type in ("plural", "device"):
            if var_type in loc_data["variations"]:
                for cat_data in loc_data["variations"][var_type].values():
                    if "stringUnit" in cat_data:
                        all_values.append(cat_data["stringUnit"].get("value", ""))

    specs = set()
    for v in all_values:
        specs.update(extract_specifiers(v))
    return sorted(specs)


def main():
    parser = argparse.ArgumentParser(
        description="Extract translation values from .xcstrings for grammar review"
    )
    parser.add_argument(
        "--xcstrings", required=True,
        help="Path to the .xcstrings file"
    )
    parser.add_argument(
        "--languages",
        help="Comma-separated list of language codes to extract (default: all)"
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

    # Determine which languages to extract
    all_languages = collect_all_languages(strings_data)
    if args.languages:
        requested = [lang.strip() for lang in args.languages.split(",")]
        target_languages = [lang for lang in requested if lang in all_languages]
        missing = [lang for lang in requested if lang not in all_languages]
        if missing:
            print(
                f"Warning: Languages not found in file: {', '.join(missing)}",
                file=sys.stderr
            )
    else:
        target_languages = all_languages

    # Extract entries
    entries = []
    for key in sorted(strings_data.keys()):
        entry_data = strings_data[key]

        # Skip non-translatable entries
        if entry_data.get("shouldTranslate") is False:
            continue

        localizations = entry_data.get("localizations", {})
        if not localizations:
            continue

        # Determine type from first available localization
        entry_type = "simple"
        for loc_data in localizations.values():
            entry_type = determine_type(loc_data)
            break

        # Collect values per language
        values = {}
        for lang in target_languages:
            if lang in localizations:
                val = get_values_for_localization(localizations[lang])
                if val is not None:
                    values[lang] = val

        if not values:
            continue

        entry = {
            "key": key,
            "comment": entry_data.get("comment", ""),
            "type": entry_type,
            "values": values,
            "format_specifiers": collect_format_specifiers(
                entry_data, source_lang
            ),
        }
        entries.append(entry)

    output = {
        "sourceLanguage": source_lang,
        "languages": target_languages,
        "entries": entries,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(
        f"Extracted {len(entries)} entries across "
        f"{len(target_languages)} languages to {output_path}"
    )


if __name__ == "__main__":
    main()

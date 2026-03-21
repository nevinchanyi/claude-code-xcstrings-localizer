#!/usr/bin/env python3
"""
scan_string_usage.py — Scan an Xcode project's source files to find where
each .xcstrings key is used, extracting 2-3 lines of surrounding code context.

Usage:
    python3 scan_string_usage.py \
        --xcstrings /path/to/Localizable.xcstrings \
        --project /path/to/project/source \
        --output /path/to/string_usages.json

Scans:
    - .swift files: String(localized:), NSLocalizedString, Text("key"),
      LocalizedStringKey, LocalizedStringResource, .navigationTitle, .alert,
      Label, Button, Toggle, Picker, Section header, and direct string matches
    - .storyboard / .xib files: string keys in XML attributes (text=, title=,
      placeholder=, accessibilityLabel=, etc.)
    - InfoPlist.xcstrings: identifies system-level permission and metadata keys

Output: JSON mapping each key to a list of {file, line, context} objects.
"""

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Swift patterns — match the most common ways a localized key appears in code
# ---------------------------------------------------------------------------

# Patterns that capture a string literal as group(1)
SWIFT_PATTERNS = [
    # String(localized: "key") or String(localized: "key", comment: ...)
    re.compile(r'String\s*\(\s*localized\s*:\s*"([^"]+)"'),
    # NSLocalizedString("key", ...) 
    re.compile(r'NSLocalizedString\s*\(\s*"([^"]+)"'),
    # LocalizedStringKey("key")
    re.compile(r'LocalizedStringKey\s*\(\s*"([^"]+)"'),
    # LocalizedStringResource("key")
    re.compile(r'LocalizedStringResource\s*\(\s*"([^"]+)"'),
    # Text("key") — SwiftUI
    re.compile(r'Text\s*\(\s*"([^"]+)"'),
    # Button("key")
    re.compile(r'Button\s*\(\s*"([^"]+)"'),
    # Label("key", ...)
    re.compile(r'Label\s*\(\s*"([^"]+)"'),
    # Toggle("key", ...)
    re.compile(r'Toggle\s*\(\s*"([^"]+)"'),
    # Picker("key", ...)
    re.compile(r'Picker\s*\(\s*"([^"]+)"'),
    # Section("key") or Section(header: Text("key"))
    re.compile(r'Section\s*\(\s*"([^"]+)"'),
    # .navigationTitle("key")
    re.compile(r'\.navigationTitle\s*\(\s*"([^"]+)"'),
    # .navigationBarTitle("key")
    re.compile(r'\.navigationBarTitle\s*\(\s*"([^"]+)"'),
    # .confirmationDialog("key", ...)
    re.compile(r'\.confirmationDialog\s*\(\s*"([^"]+)"'),
    # .alert("key", ...)
    re.compile(r'\.alert\s*\(\s*"([^"]+)"'),
    # .badge("key")
    re.compile(r'\.badge\s*\(\s*"([^"]+)"'),
    # .accessibilityLabel("key")
    re.compile(r'\.accessibilityLabel\s*\(\s*"([^"]+)"'),
    # .accessibilityHint("key")
    re.compile(r'\.accessibilityHint\s*\(\s*"([^"]+)"'),
    # .help("key")
    re.compile(r'\.help\s*\(\s*"([^"]+)"'),
    # TabItem label
    re.compile(r'\.tabItem\s*\{[^}]*Text\s*\(\s*"([^"]+)"'),
]

# Storyboard / XIB XML attributes that may contain localized strings
IB_ATTRIBUTES = {
    "text", "title", "placeholder", "normalTitle", "selectedTitle",
    "disabledTitle", "highlightedTitle", "prompt", "message",
    "accessibilityLabel", "accessibilityHint", "headerTitle", "footerTitle",
    "sectionTitle", "segmentTitle",
}

# Known Info.plist keys that are localized
INFOPLIST_KEYS = {
    "NSCameraUsageDescription",
    "NSPhotoLibraryUsageDescription",
    "NSPhotoLibraryAddUsageDescription",
    "NSMicrophoneUsageDescription",
    "NSLocationWhenInUseUsageDescription",
    "NSLocationAlwaysUsageDescription",
    "NSLocationAlwaysAndWhenInUseUsageDescription",
    "NSMotionUsageDescription",
    "NSHealthShareUsageDescription",
    "NSHealthUpdateUsageDescription",
    "NSFaceIDUsageDescription",
    "NSSpeechRecognitionUsageDescription",
    "NSBluetoothAlwaysUsageDescription",
    "NSBluetoothPeripheralUsageDescription",
    "NSCalendarsUsageDescription",
    "NSContactsUsageDescription",
    "NSRemindersUsageDescription",
    "NSLocalNetworkUsageDescription",
    "NSSiriUsageDescription",
    "NSAppleMusicUsageDescription",
    "NSUserTrackingUsageDescription",
    "CFBundleDisplayName",
    "CFBundleName",
    "NSHumanReadableCopyright",
}


def extract_context(lines: list[str], line_idx: int, context_radius: int = 1) -> str:
    """Extract surrounding lines with the matched line marked with >>>."""
    start = max(0, line_idx - context_radius)
    end = min(len(lines), line_idx + context_radius + 1)
    result = []
    for i in range(start, end):
        prefix = ">>> " if i == line_idx else "    "
        result.append(f"{prefix}{lines[i]}")
    return "\n".join(result)


def scan_swift_file(filepath: str, keys: set[str]) -> dict[str, list[dict]]:
    """Scan a .swift file for string key usages."""
    results: dict[str, list[dict]] = {}
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            lines = content.splitlines()
    except Exception:
        return results

    rel_path = os.path.basename(filepath)

    for line_idx, line in enumerate(lines):
        # Try each pattern
        for pattern in SWIFT_PATTERNS:
            for match in pattern.finditer(line):
                found_key = match.group(1)
                if found_key in keys:
                    context = extract_context(lines, line_idx)
                    results.setdefault(found_key, []).append({
                        "file": rel_path,
                        "line": line_idx + 1,
                        "context": context,
                    })

        # Also do direct string literal match for keys that look like
        # natural-language strings (contain spaces or are long).
        # This catches cases like Text(verbatim:) or custom wrappers.
        for key in keys:
            if len(key) > 3 and key in line:
                # Avoid duplicating matches already found by patterns above
                already_found = any(
                    e["line"] == line_idx + 1 and e["file"] == rel_path
                    for e in results.get(key, [])
                )
                if not already_found and f'"{key}"' in line:
                    context = extract_context(lines, line_idx)
                    results.setdefault(key, []).append({
                        "file": rel_path,
                        "line": line_idx + 1,
                        "context": context,
                    })

    return results


def scan_ib_file(filepath: str, keys: set[str]) -> dict[str, list[dict]]:
    """Scan a .storyboard or .xib XML file for string key usages."""
    results: dict[str, list[dict]] = {}
    rel_path = os.path.basename(filepath)

    try:
        tree = ET.parse(filepath)
    except Exception:
        return results

    for elem in tree.iter():
        for attr_name in IB_ATTRIBUTES:
            val = elem.get(attr_name)
            if val and val in keys:
                # Build a short context from the XML element
                tag = elem.tag
                elem_id = elem.get("id", "?")
                custom_class = elem.get("customClass", "")
                context_str = f">>> <{tag}"
                if custom_class:
                    context_str += f' customClass="{custom_class}"'
                context_str += f' {attr_name}="{val}" id="{elem_id}" />'

                results.setdefault(val, []).append({
                    "file": rel_path,
                    "line": 0,  # XML doesn't give us line numbers easily
                    "context": context_str,
                })

    return results


def scan_infoplist_xcstrings(filepath: str, keys: set[str]) -> dict[str, list[dict]]:
    """Identify Info.plist-related keys from an InfoPlist.xcstrings file."""
    results: dict[str, list[dict]] = {}
    rel_path = os.path.basename(filepath)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return results

    plist_keys = set(data.get("strings", {}).keys())
    for key in keys:
        if key in plist_keys or key in INFOPLIST_KEYS:
            is_permission = key.startswith("NS") and key.endswith("Description")
            if is_permission:
                context_str = f">>> InfoPlist.xcstrings: {key} (iOS permission dialog string)"
            else:
                context_str = f">>> InfoPlist.xcstrings: {key} (app metadata / display name)"
            results.setdefault(key, []).append({
                "file": rel_path,
                "line": 0,
                "context": context_str,
            })

    return results


def find_files(project_dir: str, extensions: set[str]) -> list[str]:
    """Recursively find files with given extensions, skipping build artifacts."""
    skip_dirs = {
        ".build", "build", "DerivedData", ".git", "Pods",
        "Carthage", ".swiftpm", "node_modules", "__pycache__",
    }
    found = []
    for root, dirs, files in os.walk(project_dir):
        # Prune directories we don't want to descend into
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            ext = Path(fname).suffix.lower()
            if ext in extensions:
                found.append(os.path.join(root, fname))
    return found


def main():
    parser = argparse.ArgumentParser(
        description="Scan Xcode project source for .xcstrings key usage"
    )
    parser.add_argument(
        "--xcstrings", required=True,
        help="Path to the .xcstrings file to read keys from"
    )
    parser.add_argument(
        "--project", required=True,
        help="Path to the project source directory to scan"
    )
    parser.add_argument(
        "--output", required=True,
        help="Path to write the JSON output"
    )
    args = parser.parse_args()

    # 1. Load keys from xcstrings
    with open(args.xcstrings, "r", encoding="utf-8") as f:
        xcdata = json.load(f)

    keys = set(xcdata.get("strings", {}).keys())
    print(f"📋 Loaded {len(keys)} string keys from {args.xcstrings}")

    # 2. Find all source files
    swift_files = find_files(args.project, {".swift"})
    ib_files = find_files(args.project, {".storyboard", ".xib"})
    infoplist_files = find_files(args.project, {".xcstrings"})
    # Filter infoplist_files to only InfoPlist.xcstrings (not the main Localizable)
    infoplist_files = [
        f for f in infoplist_files
        if "InfoPlist" in os.path.basename(f)
    ]

    print(f"🔍 Scanning {len(swift_files)} Swift files, "
          f"{len(ib_files)} IB files, "
          f"{len(infoplist_files)} InfoPlist.xcstrings files")

    # 3. Scan everything
    all_usages: dict[str, list[dict]] = {}

    for sf in swift_files:
        for key, usages in scan_swift_file(sf, keys).items():
            all_usages.setdefault(key, []).extend(usages)

    for ibf in ib_files:
        for key, usages in scan_ib_file(ibf, keys).items():
            all_usages.setdefault(key, []).extend(usages)

    for ipf in infoplist_files:
        for key, usages in scan_infoplist_xcstrings(ipf, keys).items():
            all_usages.setdefault(key, []).extend(usages)

    # 4. Report
    matched_keys = set(all_usages.keys())
    unmatched_keys = keys - matched_keys
    total_usages = sum(len(v) for v in all_usages.values())

    print(f"\n✅ Found {total_usages} usages across {len(matched_keys)} keys")
    if unmatched_keys:
        print(f"⚠️  {len(unmatched_keys)} keys had no matches in source code:")
        for uk in sorted(unmatched_keys)[:20]:
            print(f"    - {uk}")
        if len(unmatched_keys) > 20:
            print(f"    ... and {len(unmatched_keys) - 20} more")

    # 5. Write output
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_usages, f, ensure_ascii=False, indent=2)

    print(f"\n📄 Output written to {args.output}")


if __name__ == "__main__":
    main()

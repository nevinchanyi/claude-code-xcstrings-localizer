#!/usr/bin/env python3
"""
scan_project_domain.py — Scan an Xcode project to extract domain signals
for translation context: type declarations, enum cases, framework imports,
README/doc content, and app metadata.

Usage:
    python3 scan_project_domain.py \
        --project /path/to/project/source \
        --output /path/to/domain_scan.json

Output: JSON with structured project domain data that Claude uses to write
a domain report guiding accurate, context-aware translations.
"""

import argparse
import json
import os
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Skip directories
# ---------------------------------------------------------------------------

SKIP_DIRS = {
    ".build", "build", "DerivedData", ".git", "Pods",
    "Carthage", ".swiftpm", "node_modules", "__pycache__",
    "Frameworks", ".framework",
}

# ---------------------------------------------------------------------------
# Swift type extraction patterns
# ---------------------------------------------------------------------------

# Captures: (access_modifier?, type_keyword, type_name)
TYPE_DECL_RE = re.compile(
    r'(?:^|\n)\s*'
    r'(?:(?:public|open|internal|fileprivate|private|final)\s+)*'
    r'(class|struct|enum|protocol|actor)\s+'
    r'([A-Z][A-Za-z0-9_]*)'
)

# Enum case: captures case name (and optional associated value hint)
ENUM_CASE_RE = re.compile(
    r'^\s*case\s+([a-zA-Z][a-zA-Z0-9_]*)'
)

# Import statement
IMPORT_RE = re.compile(
    r'^\s*import\s+([A-Za-z][A-Za-z0-9_.]*)'
)

# ---------------------------------------------------------------------------
# Framework → domain signal mapping
# ---------------------------------------------------------------------------

FRAMEWORK_SIGNALS = {
    "CoreLocation": "Location/GPS tracking — spatial terms like 'location', 'coordinate', 'accuracy', 'region' refer to real-world geography",
    "MapKit": "Maps and navigation — 'pin', 'annotation', 'route', 'direction' are map concepts",
    "HealthKit": "Health and fitness — 'activity', 'steps', 'heart rate', 'workout' are medical/fitness terms",
    "StoreKit": "In-app purchases and subscriptions — 'purchase', 'subscribe', 'restore', 'plan' are commerce terms",
    "CoreBluetooth": "Bluetooth device connectivity — 'peripheral', 'scan', 'connect', 'pair' are BLE terms",
    "CoreMotion": "Motion and activity detection — 'motion', 'activity', 'pedometer', 'accelerometer' are sensor terms",
    "AVFoundation": "Audio/video capture and playback — 'record', 'capture', 'session', 'track' are media terms",
    "Speech": "Speech recognition — 'transcription', 'recognize', 'dictation' are speech-to-text terms",
    "NaturalLanguage": "Text analysis/NLP — 'token', 'language', 'sentiment' are linguistic terms",
    "CoreML": "Machine learning inference — 'model', 'prediction', 'confidence' are ML terms",
    "Vision": "Image analysis and computer vision — 'detect', 'recognize', 'observation' are vision terms",
    "ARKit": "Augmented reality — 'anchor', 'plane', 'scene', 'session' are AR terms",
    "CloudKit": "iCloud sync and storage — 'record', 'zone', 'subscription' are cloud database terms",
    "CoreData": "Local persistent storage — 'entity', 'fetch', 'context', 'store' are database terms",
    "SwiftData": "Local persistent storage (modern) — 'model', 'query', 'container' are database terms",
    "UserNotifications": "Push/local notifications — 'notification', 'alert', 'badge', 'trigger' are notification terms",
    "WidgetKit": "Home screen widgets — extremely limited space for text, brevity critical",
    "WatchKit": "Apple Watch — very small screen, text must be extremely concise",
    "CarPlay": "CarPlay integration — driver-focused, glanceable text, minimal interaction",
    "NetworkExtension": "VPN and network configuration — 'tunnel', 'proxy', 'configuration' are networking terms",
    "PassKit": "Apple Pay and Wallet — 'pass', 'payment', 'card' are financial terms",
    "EventKit": "Calendar and reminders — 'event', 'reminder', 'calendar', 'alarm' are scheduling terms",
    "Contacts": "Contact management — 'contact', 'name', 'phone', 'email' are personal info terms",
    "PhotosUI": "Photo library access — 'photo', 'album', 'asset', 'picker' are photography terms",
    "GameKit": "Game Center — 'score', 'leaderboard', 'achievement', 'match' are gaming terms",
    "MultipeerConnectivity": "Peer-to-peer networking — 'peer', 'session', 'invite', 'browse' are P2P terms",
    "WebKit": "Web content display — 'page', 'navigate', 'load', 'script' are web terms",
    "CryptoKit": "Cryptography — 'key', 'encrypt', 'sign', 'hash' are security terms",
    "LocalAuthentication": "Biometric auth (Face ID, Touch ID) — 'authenticate', 'biometric' are security terms",
    "RevenueCat": "Subscription management (3rd party) — 'offering', 'entitlement', 'package' are commerce terms",
    "Firebase": "Backend services (Google) — 'analytics', 'crash', 'remote config' are backend terms",
    "Alamofire": "Networking (3rd party) — 'request', 'response', 'session' are HTTP terms",
    "Realm": "Local database (3rd party) — 'object', 'realm', 'query', 'migration' are database terms",
}

# ---------------------------------------------------------------------------
# README and doc file patterns
# ---------------------------------------------------------------------------

README_NAMES = {
    "README.md", "README", "README.txt", "README.rst",
    "readme.md", "readme", "readme.txt",
}

DOC_EXTENSIONS = {".md", ".txt", ".rst"}
DOC_DIRS = {"docs", "doc", "documentation", "Documentation"}

# ---------------------------------------------------------------------------
# App Store metadata patterns (fastlane, etc.)
# ---------------------------------------------------------------------------

METADATA_PATHS = [
    "fastlane/metadata/en-US/description.txt",
    "fastlane/metadata/en-US/name.txt",
    "fastlane/metadata/en-US/subtitle.txt",
    "fastlane/metadata/en-US/keywords.txt",
    "fastlane/metadata/en-GB/description.txt",
    "fastlane/metadata/default/description.txt",
    "metadata/description.txt",
    "AppStoreMetadata/description.txt",
]


def find_files(project_dir: str, extensions: set[str]) -> list[str]:
    """Recursively find files, skipping build artifacts."""
    found = []
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.endswith(".framework")]
        for fname in files:
            if Path(fname).suffix.lower() in extensions:
                found.append(os.path.join(root, fname))
    return found


def extract_swift_types(filepath: str) -> list[dict]:
    """Extract type declarations from a Swift file."""
    types = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return types

    for match in TYPE_DECL_RE.finditer(content):
        kind = match.group(1)  # class, struct, enum, protocol, actor
        name = match.group(2)
        types.append({
            "kind": kind,
            "name": name,
            "file": os.path.basename(filepath),
        })

    return types


def extract_enum_cases(filepath: str) -> dict[str, list[str]]:
    """Extract enum cases grouped by their parent enum."""
    enums: dict[str, list[str]] = {}
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception:
        return enums

    current_enum = None
    brace_depth = 0

    for line in lines:
        # Track enum entry
        enum_match = re.search(r'\benum\s+([A-Z][A-Za-z0-9_]*)', line)
        if enum_match:
            current_enum = enum_match.group(1)
            brace_depth = 0

        # Track braces to know when we leave the enum
        if current_enum:
            brace_depth += line.count('{') - line.count('}')
            if brace_depth <= 0 and current_enum in enums:
                current_enum = None
                continue

            case_match = ENUM_CASE_RE.match(line)
            if case_match:
                case_name = case_match.group(1)
                enums.setdefault(current_enum, []).append(case_name)

    return enums


def extract_imports(filepath: str) -> set[str]:
    """Extract import statements from a Swift file."""
    imports = set()
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                match = IMPORT_RE.match(line)
                if match:
                    imports.add(match.group(1))
    except Exception:
        pass
    return imports


def read_readme_and_docs(project_dir: str) -> list[dict]:
    """Read README files and documentation."""
    docs = []

    # Root-level README
    for name in README_NAMES:
        path = os.path.join(project_dir, name)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                if content.strip():
                    docs.append({
                        "file": name,
                        "type": "readme",
                        "content": content[:5000],  # Cap at 5k chars
                    })
            except Exception:
                pass

    # Documentation directories
    for doc_dir_name in DOC_DIRS:
        doc_dir = os.path.join(project_dir, doc_dir_name)
        if os.path.isdir(doc_dir):
            for fname in os.listdir(doc_dir):
                if Path(fname).suffix.lower() in DOC_EXTENSIONS:
                    fpath = os.path.join(doc_dir, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()
                        if content.strip():
                            docs.append({
                                "file": f"{doc_dir_name}/{fname}",
                                "type": "documentation",
                                "content": content[:3000],
                            })
                    except Exception:
                        pass

    return docs


def read_app_store_metadata(project_dir: str) -> list[dict]:
    """Read App Store metadata from fastlane or similar structures."""
    metadata = []

    for rel_path in METADATA_PATHS:
        full_path = os.path.join(project_dir, rel_path)
        if os.path.isfile(full_path):
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                if content.strip():
                    metadata.append({
                        "file": rel_path,
                        "content": content[:3000],
                    })
            except Exception:
                pass

    return metadata


def read_bundle_info(project_dir: str) -> dict:
    """Try to extract bundle ID and display name from pbxproj or Info.plist."""
    info = {}

    # Search for Info.plist
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            if fname == "Info.plist":
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    # Simple regex extraction — not a full plist parser
                    bundle_name_match = re.search(
                        r'<key>CFBundleDisplayName</key>\s*<string>([^<]+)</string>',
                        content
                    )
                    if bundle_name_match:
                        info["display_name"] = bundle_name_match.group(1)

                    bundle_id_match = re.search(
                        r'<key>CFBundleIdentifier</key>\s*<string>([^<]+)</string>',
                        content
                    )
                    if bundle_id_match:
                        info["bundle_id"] = bundle_id_match.group(1)
                except Exception:
                    pass

                if info:
                    return info

    return info


def main():
    parser = argparse.ArgumentParser(
        description="Scan Xcode project to extract domain signals for translation context"
    )
    parser.add_argument(
        "--project", required=True,
        help="Path to the project source directory"
    )
    parser.add_argument(
        "--output", required=True,
        help="Path to write the JSON output"
    )
    args = parser.parse_args()

    project_dir = args.project

    # 1. Find Swift files
    swift_files = find_files(project_dir, {".swift"})
    print(f"🔍 Scanning {len(swift_files)} Swift files...")

    # 2. Extract types
    all_types = []
    for sf in swift_files:
        all_types.extend(extract_swift_types(sf))
    print(f"   Found {len(all_types)} type declarations")

    # 3. Extract enum cases
    all_enums: dict[str, list[str]] = {}
    for sf in swift_files:
        for enum_name, cases in extract_enum_cases(sf).items():
            all_enums.setdefault(enum_name, []).extend(cases)
    total_cases = sum(len(v) for v in all_enums.values())
    print(f"   Found {len(all_enums)} enums with {total_cases} total cases")

    # 4. Extract imports
    all_imports: set[str] = set()
    for sf in swift_files:
        all_imports.update(extract_imports(sf))
    print(f"   Found {len(all_imports)} unique imports")

    # 5. Map framework signals
    detected_signals = {}
    for fw, signal in FRAMEWORK_SIGNALS.items():
        if fw in all_imports:
            detected_signals[fw] = signal

    # 6. Read docs
    docs = read_readme_and_docs(project_dir)
    print(f"📄 Found {len(docs)} README/doc files")

    # 7. Read App Store metadata
    metadata = read_app_store_metadata(project_dir)
    print(f"🏪 Found {len(metadata)} App Store metadata files")

    # 8. Bundle info
    bundle_info = read_bundle_info(project_dir)
    if bundle_info:
        print(f"📦 Bundle: {bundle_info}")

    # 9. Assemble output
    output = {
        "swift_types": all_types,
        "enums": {k: v for k, v in sorted(all_enums.items())},
        "imports": sorted(all_imports),
        "framework_signals": detected_signals,
        "docs": docs,
        "app_store_metadata": metadata,
        "bundle_info": bundle_info,
        "stats": {
            "swift_files_scanned": len(swift_files),
            "type_declarations": len(all_types),
            "enum_count": len(all_enums),
            "enum_cases_total": total_cases,
            "unique_imports": len(all_imports),
            "framework_signals_detected": len(detected_signals),
        }
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Domain scan complete → {args.output}")
    print(f"   {len(all_types)} types, {len(all_enums)} enums, "
          f"{len(detected_signals)} framework signals, {len(docs)} docs")


if __name__ == "__main__":
    main()

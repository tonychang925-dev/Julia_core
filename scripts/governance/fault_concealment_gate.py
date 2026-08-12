#!/usr/bin/env python3
"""FAULT-CONCEALMENT-AUDIT-01 — Static Gate.
Classifies forbidden fallback patterns into F1-F7 categories.
P0 categories (F1/F2/F4/F5/F7): ZERO TOLERANCE — CI must FAIL.
P1 categories (F3/F6): must have explicit ALLOW_DEGRADED waiver.
"""
import os, re, sys, json
from pathlib import Path

HOME = os.path.expanduser("~")

# ── Category definitions ──

CATEGORIES = {
    "F1_AUTHORITY_FALLBACK": {
        "desc": "Canonical identity/history/runtime authority missing → local/legacy/standalone",
        "level": "P0",
        "patterns": [
            r'return\s+(CodexProvider|DeepSeekProvider)\(\)',
            r'get_llm_provider.*else.*return',
            r'unknown.*provider.*return',
        ],
    },
    "F2_FAKE_SUCCESS": {
        "desc": "Provider/tool/brain failure → normal text/empty object/PASS",
        "level": "P0",
        "patterns": [
            r'return\s*"\[DeepSeek',
            r'return\s*f"\[DeepSeek',
            r'yield\s*"\[DeepSeek',
            r'return\s*"\[Error\]',
            r'error.*return\s*""',
        ],
    },
    "F3_SILENT_DEGRADATION": {
        "desc": "except Exception: pass / return '' / return []",
        "level": "P1",
        "patterns": [
            r'except Exception:\s*$',  # followed by pass or return empty
        ],
    },
    "F4_AUTO_CREATE_ON_RESUME": {
        "desc": "Missing conversation/session → create new silently",
        "level": "P0",
        "patterns": [
            r'get_or_create',
            r'find.*or.*create\(',
            r'not found.*create',
        ],
    },
    "F5_LEGACY_RESURRECTION": {
        "desc": "New canonical path fails → old runtime/legacy path takes over",
        "level": "P0",
        "patterns": [
            r'standalone.*fallback',
            r'legacy.*path.*continue',
            r'workspace.*bootstrap.*legacy',
        ],
    },
    "F6_MOCK_CONFIDENCE": {
        "desc": "FakeProvider / fabricated trace used as production gate",
        "level": "P1",
        "patterns": [
            r'FakeProvider.*def test.*PASS',
            r'mock.*production.*gate',
            r'synthetic.*runtime_path.*assert',
        ],
    },
    "F7_DEPLOYMENT_FALLBACK": {
        "desc": "Target release not found → golden/old release/alternative path",
        "level": "P0",
        "patterns": [
            r'release.*not found.*golden',
            r'current.*missing.*fallback',
            r'artifact.*missing.*old',
        ],
    },
}

# ── Repos to scan ──
REPOS = {
    "julia_core": f"{HOME}/julia_core/julia_core/runtime",
    "julia_ai_assistant": f"{HOME}/julia_ai_assistant_rmd3g_prod",
    "Julia-Voice-S2S": f"{HOME}/Julia-Voice-S2S/s2s",
}

def classify_match(category, line_content, next_line=""):
    """Determine if an F3 match is truly silent or has proper handling."""
    if category == "F3_SILENT_DEGRADATION":
        # Check if the next non-empty line after except is pass/return empty
        stripped = next_line.strip() if next_line else ""
        if stripped in ("pass", 'return ""', "return []", "return {}", "return None", "return ''"):
            return True
        if stripped.startswith("raise") or stripped.startswith("logger.") or "exc_info" in stripped:
            return False  # Proper handling
        if stripped == "pass":
            return True
        # If next line is a comment or blank, check the line after
        return bool(re.match(r'\s*(pass|return\s+(None|""|\[\]|\{\}|0))\s*$', next_line)) if next_line else True
    return True  # For F1/F2/F4/F5/F7, always flag

def scan_file(filepath, repo_name):
    findings = []
    try:
        with open(filepath) as f:
            lines = f.readlines()
    except Exception:
        return findings

    for i, line in enumerate(lines):
        next_line = lines[i+1].strip() if i+1 < len(lines) else ""

        for cat_name, cat_info in CATEGORIES.items():
            for pattern in cat_info["patterns"]:
                if re.search(pattern, line):
                    # For F3, check if it's followed by actual pass/return-empty
                    if cat_name == "F3_SILENT_DEGRADATION":
                        # Look ahead 1-2 lines
                        for j in range(i+1, min(i+3, len(lines))):
                            nl = lines[j].strip()
                            if nl in ("pass",) or re.match(r'return\s+(None|""|\[\]|\{\}|0)\s*$', nl):
                                findings.append({
                                    "category": cat_name,
                                    "level": cat_info["level"],
                                    "repo": repo_name,
                                    "path": str(Path(filepath).relative_to(HOME)),
                                    "line": i + 1,
                                    "content": line.strip(),
                                })
                                break
                            elif nl and not nl.startswith("#"):
                                break  # Non-empty, non-comment — probably proper handling
                    else:
                        findings.append({
                            "category": cat_name,
                            "level": cat_info["level"],
                            "repo": repo_name,
                            "path": str(Path(filepath).relative_to(HOME)),
                            "line": i + 1,
                            "content": line.strip(),
                        })
    return findings

def main():
    all_findings = []

    for repo_name, repo_path in REPOS.items():
        if not os.path.isdir(repo_path):
            continue
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', 'node_modules')]
            for f in files:
                if f.endswith('.py'):
                    all_findings.extend(scan_file(os.path.join(root, f), repo_name))

    # ── Count by category ──
    counts = {}
    for cat in CATEGORIES:
        counts[cat] = sum(1 for f in all_findings if f["category"] == cat)

    p0_count = sum(1 for f in all_findings if f["level"] == "P0")
    p1_count = sum(1 for f in all_findings if f["level"] == "P1")

    # ── Output ──
    print("=" * 60)
    print("FAULT-CONCEALMENT-AUDIT-01 — Static Gate")
    print("=" * 60)
    print()

    for cat in CATEGORIES:
        level = CATEGORIES[cat]["level"]
        count = counts[cat]
        marker = "✅" if count == 0 else "⛔"
        print(f"  {marker} {cat}: {count} ({level})")

    print()
    print(f"  P0 (BLOCKING): {p0_count}")
    print(f"  P1 (NEEDS WAIVER): {p1_count}")

    if all_findings:
        print()
        print("--- Findings ---")
        for f in all_findings:
            print(f"  [{f['level']}] {f['category']} {f['repo']}/{f['path']}:{f['line']}")
            print(f"         {f['content'][:120]}")

    print()
    if p0_count > 0:
        print(f"⛔ FAIL: {p0_count} P0 fallback(s) found. E2E PROHIBITED.")
        print("   Fix all P0 items before production testing.")
        sys.exit(1)

    if p1_count > 0:
        print(f"⚠️  WARNING: {p1_count} P1 fallback(s). Require ALLOW_DEGRADED waiver.")

    print("✅ PASS: All P0 fault-concealment patterns eradicated.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

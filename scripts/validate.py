#!/usr/bin/env python3
"""Structural validator for the Awesome AI Tools README.

Checks the invariants that keep the list clean and renderable:
  1. Code fences are balanced
  2. Headings are unique
  3. No UTM/tracking parameters in links
  4. Only the four sanctioned tags are used
  5. No duplicate list entries
  6. Links use https and don't point at known-dead destinations
Exits non-zero with a report if any check fails.
"""

import re
import sys
from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"
ALLOWED_TAGS = {"opensource", "free", "selfhost", "api"}
DEAD_LINKS = {"https://chat.openai.com", "https://claude.ai", "https://cursor.sh",
              "https://ollama.ai", "https://chat.lmsys.org", "https://runwayml.com"}

errors = []
lines = README.read_text(encoding="utf-8").splitlines()

# 1. Balanced code fences
open_fences = sum(1 for l in lines if l.strip().startswith("```"))
if open_fences % 2 != 0:
    errors.append(f"Unbalanced code fences: found {open_fences} fence markers (must be even)")

# 2. Unique headings
headings = [l for l in lines if l.startswith("#")]
dupes = {h for h in headings if headings.count(h) > 1}
if dupes:
    errors.append(f"Duplicate headings: {sorted(dupes)}")

for n, line in enumerate(lines, 1):
    if line.lstrip().startswith("- [ ]") or line.lstrip().startswith("- [x]"):
        continue  # checklist/example lines, not entries
    # 3. Tracking parameters
    if "utm_source" in line or "utm_campaign" in line or "utm_medium" in line:
        errors.append(f"line {n}: UTM/tracking parameter in link")
    # 4. Tag discipline
    for tag in re.findall(r"`#([a-z]+)`", line):
        if tag not in ALLOWED_TAGS:
            errors.append(f"line {n}: non-standard tag `#{tag}` (allowed: {sorted(ALLOWED_TAGS)})")
    # 5. Known-dead destinations
    for url in re.findall(r"\((https?://[^)]+)\)", line):
        if url in DEAD_LINKS:
            errors.append(f"line {n}: dead/redirecting URL {url}")
        if url.startswith("http://"):
            errors.append(f"line {n}: non-https URL {url}")

# 6. Duplicate entries within the same top-level section
# (cross-category repeats are an editorial choice; in-section duplicates are bugs)
section, seen = "", {}
for n, line in enumerate(lines, 1):
    if line.startswith("## "):
        section = line.strip()
    m = re.match(r"^\s*-\s+⭐?\s*🔥?\s*\[([^\]]+)\]\(([^)]+)\)", line)
    if m:
        key = (section, m.group(1), m.group(2))
        if key in seen:
            errors.append(f"line {n}: duplicate entry [{m.group(1)}]({m.group(2)}) "
                          f"in section '{section}' (first at line {seen[key]})")
        else:
            seen[key] = n

if errors:
    print(f"FAIL: {len(errors)} problem(s) in {README.name}\n")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print(f"OK: {README.name} passed structural validation "
      f"({len(headings)} headings, {len(seen)} entries)")

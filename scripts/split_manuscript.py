import re, os, sys, pathlib, unicodedata

SRC = "manuscript/part1_case_files/villain-verse-manuscript.md"

# Dest dirs
PART1 = "manuscript/part1_case_files"
PART2 = "manuscript/part2_patterns"
FRONT = "manuscript/frontmatter"
pathlib.Path(PART1).mkdir(parents=True, exist_ok=True)
pathlib.Path(PART2).mkdir(parents=True, exist_ok=True)
pathlib.Path(FRONT).mkdir(parents=True, exist_ok=True)

# slugify
def slug(s):
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s.strip().lower())
    s = re.sub(r"-+", "-", s)
    return s or "untitled"

with open(SRC, "r", encoding="utf-8") as f:
    lines = f.readlines()

# We’ll capture:
# - Introduction block (from first "## Introduction" to next "## ")
# - Case-file parts:    "## Part <n>:" where n is 1..16 (heuristic)
# - Pattern overview:   "## Part II" (Roman) → patterns_overview.md (if present)
# - Pattern chapters:   "## Chapter <n>:" for n 17..20 → part2
intro_start = None
blocks = []  # list of (dest_path, content)

# Identify indices of all H2 blocks ("## ...")
h2_idxs = [i for i, ln in enumerate(lines) if ln.startswith("## ")]
h2_idxs.append(len(lines))  # sentinel

def collect(i0, i1):
    seg = "".join(lines[i0:i1]).strip() + "\n"
    head = lines[i0].strip()
    return head, seg

for j in range(len(h2_idxs)-1):
    i0, i1 = h2_idxs[j], h2_idxs[j+1]
    head, seg = collect(i0, i1)

    # Introduction
    if re.match(r"^##\s+Introduction\b", head, flags=re.I):
        dest = os.path.join(FRONT, "introduction.md")
        blocks.append((dest, seg))
        continue

    # Part II (Roman) overview (allow variations like "## Part II:" or "## Part II")
    if re.match(r"^##\s+Part\s+II\b", head, flags=re.I):
        dest = os.path.join(PART2, "patterns_overview.md")
        blocks.append((dest, seg))
        continue

    # Case files Part N (1..16): "## Part 1: Title"
    m = re.match(r"^##\s+Part\s+(\d+)\s*:\s*(.+)$", head, flags=re.I)
    if m:
        n = int(m.group(1))
        title = m.group(2).strip()
        if 1 <= n <= 16:
            base = f"{n:02d}-{slug(title)}.md"
            dest = os.path.join(PART1, base)
            blocks.append((dest, seg))
            continue
        # If not 1..16, fall through (later parts handled below)

    # Chapter 17..20 (patterns section): "## Chapter 17: Title"
    m = re.match(r"^##\s+Chapter\s+(\d+)\s*:\s*(.+)$", head, flags=re.I)
    if m:
        n = int(m.group(1))
        title = m.group(2).strip()
        if 17 <= n <= 20:
            base = f"{n:02d}-{slug(title)}.md"
            dest = os.path.join(PART2, base)
            blocks.append((dest, seg))
            continue

# If no Introduction H2 existed, try the very top (before first H2) as intro
if not any(p.endswith("/introduction.md") for p, _ in blocks):
    top_start = 0
    if h2_idxs and h2_idxs[0] > 0:
        preface = "".join(lines[:h2_idxs[0]]).strip()
        if preface:
            blocks.insert(0, (os.path.join(FRONT, "introduction.md"), preface + "\n"))

# Write files
written = []
for dest, seg in blocks:
    pathlib.Path(os.path.dirname(dest)).mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as out:
        out.write(seg)
    written.append(dest)

# Print a summary for the shell
print("WROTE:")
for w in written:
    print(" -", w)

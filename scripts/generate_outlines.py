import re, os, pathlib, textwrap

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANU = ROOT / "manuscript"
OUT  = ROOT / "outline"

PARTS = [
    ("Front Matter", MANU / "frontmatter"),
    ("Part I — Case Files", MANU / "part1_case_files"),
    ("Part II — Pattern Recognition", MANU / "part2_patterns"),
    ("Part III — Fallout", MANU / "part3_fallout"),
    ("Part IV — Apologetics Field Guide", MANU / "part4_apologetics"),
    ("Part V — Exit Routes", MANU / "part5_exit_routes"),
]

def first_h1_and_teaser(p: pathlib.Path):
    title = p.stem.replace("_", " ")
    teaser = ""
    try:
        txt = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return title, teaser
    # title from first "# " if present
    m = re.search(r'^\s*#\s+(.+)', txt, flags=re.M)
    if m:
        title = m.group(1).strip()
    # teaser: first non-empty paragraph that is not a heading
    paras = [s.strip() for s in re.split(r'\n\s*\n', txt) if s.strip()]
    for para in paras:
        if not para.startswith("#"):
            # Trim to one line, 140 chars
            teaser = " ".join(para.split())
            teaser = (teaser[:137] + "…") if len(teaser) > 140 else teaser
            break
    return title, teaser

def rel(p: pathlib.Path):
    return p.as_posix().replace(str(ROOT.as_posix())+"/", "")

# Build per-part outlines + a master index
index_lines = ["# Book Outline\n"]
for part_name, part_dir in PARTS:
    part_md = OUT / (part_dir.name + ".md")
    items = []
    if part_dir.exists():
        files = sorted(part_dir.glob("*.md"))
        # If numbered files exist, they’ll naturally sort before stubs.
        for f in files:
            if f.name.lower() in {"acknowledgments.md"}:  # keep that for end via Makefile
                continue
            title, teaser = first_h1_and_teaser(f)
            line = f"- [{title}]({rel(f)})"
            if teaser:
                line += f" — {teaser}"
            items.append(line)
    part_md.write_text(
        "# " + part_name + "\n\n" + ("\n".join(items) if items else "_(no chapters yet)_\n"),
        encoding="utf-8"
    )
    index_lines.append(f"- [{part_name}]({rel(part_md)})")

# Write master index
(OUT / "index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

print("Generated:")
print(" -", rel(OUT / "index.md"))
for _, part_dir in PARTS:
    print(" -", rel(OUT / (part_dir.name + ".md")))

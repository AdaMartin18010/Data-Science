import re
from pathlib import Path


def find_md_files(root: Path):
    return [p for p in root.rglob("*.md") if p.is_file()]


def iter_links(text: str):
    # Markdown link: [text](path#anchor)
    pattern = re.compile(r"\[[^\]]+\]\((?!https?://)([^)#\s]+)(#[^)\s]+)?\)")
    for m in pattern.finditer(text):
        yield m.group(1), (m.group(2)[1:] if m.group(2) else None)


def slugify_heading(h: str) -> str:
    # GitHub-like anchor slug (approx). Keep ascii letters/digits/CJK/spaces/hyphen
    s = h.strip().lower()
    s = re.sub(r"[^0-9a-z\u4e00-\u9fff\s-]", " ", s)
    s = re.sub(r"\s+", "-", s)
    return s


def extract_anchors(md_path: Path):
    anchors = set()
    try:
        lines = md_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return anchors
    for line in lines:
        if line.lstrip().startswith("#"):
            heading = line.lstrip("#").strip()
            if heading:
                anchors.add(slugify_heading(heading))
    return anchors


def main():
    repo_root = Path.cwd()
    target_root = repo_root / "Analysis/1-数据库系统/1.1-PostgreSQL"
    reports = repo_root / ".reports"
    reports.mkdir(parents=True, exist_ok=True)

    rows = ["source_file,link_path,anchor,status"]

    # cache anchors per file
    anchor_cache = {}

    for src in find_md_files(target_root):
        try:
            text = src.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for link_path, anchor in iter_links(text):
            target = (src.parent / link_path).resolve()
            status = "ok"
            if not target.exists():
                status = "missing_file"
            elif anchor:
                if target not in anchor_cache:
                    anchor_cache[target] = extract_anchors(target)
                if anchor.lower() not in anchor_cache[target]:
                    status = "missing_anchor"
            rows.append(
                f"{src.as_posix()},{link_path},{anchor or ''},{status}"
            )

    out = reports / "links.csv"
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    # print brief summary
    total = len(rows) - 1
    missing = sum(1 for r in rows[1:] if r.endswith(",missing_file") or r.endswith(",missing_anchor"))
    print(f"links_total={total} missing_or_anchor_issues={missing} output={out}")


if __name__ == "__main__":
    main()



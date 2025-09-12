import os
import re
from pathlib import Path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def iter_files(root: Path):
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            yield Path(dirpath) / name


def scan_directory(root: Path, reports_dir: Path) -> None:
    ensure_dir(reports_dir)

    headings_re = re.compile(r"^(#|##|###)")
    todos_re = re.compile(r"(TODO|待办|占位|TBD|FIXME|完善|后续补充)", re.IGNORECASE)
    dup_re = re.compile(r"(扩充版|增强版|重复内容|归档)", re.IGNORECASE)
    codeblock_re = re.compile(r"```")
    front_matter_re = re.compile(r"^\s*---\s*$")

    headings_lines = []
    todos_lines = []
    dup_lines = []
    codeblock_lines = []
    with_frontmatter = []
    missing_frontmatter = []

    # per-file counters
    todos_counts = {}
    dup_counts = {}

    for fp in iter_files(root):
        rel = fp.relative_to(Path.cwd()) if fp.is_absolute() else fp
        is_md = fp.suffix.lower() == ".md"
        try:
            with fp.open("r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            # Skip unreadable files
            continue

        # headings & codeblocks only for md
        if is_md:
            for idx, line in enumerate(lines, start=1):
                if headings_re.search(line):
                    headings_lines.append(f"{rel}:{idx}:{line.rstrip()}\n")
                if codeblock_re.search(line):
                    codeblock_lines.append(f"{rel}:{idx}:{line.rstrip()}\n")

            # front matter presence: allow anywhere, strip BOM if present
            if any(front_matter_re.search(l.lstrip('\ufeff')) for l in lines):
                with_frontmatter.append(str(rel) + "\n")
            else:
                missing_frontmatter.append(str(rel) + "\n")

        # todos and duplicates for all text files under root
        for idx, line in enumerate(lines, start=1):
            if todos_re.search(line):
                todos_lines.append(f"{rel}:{idx}:{line.rstrip()}\n")
                todos_counts[str(rel)] = todos_counts.get(str(rel), 0) + 1
            if dup_re.search(line):
                dup_lines.append(f"{rel}:{idx}:{line.rstrip()}\n")
                dup_counts[str(rel)] = dup_counts.get(str(rel), 0) + 1

    # Write reports
    (reports_dir / "pg_headings.txt").write_text("".join(headings_lines), encoding="utf-8")
    (reports_dir / "pg_todos.txt").write_text("".join(todos_lines), encoding="utf-8")
    (reports_dir / "pg_duplicates.txt").write_text("".join(dup_lines), encoding="utf-8")
    (reports_dir / "pg_codeblocks.txt").write_text("".join(codeblock_lines), encoding="utf-8")
    (reports_dir / "pg_with_frontmatter.txt").write_text("".join(with_frontmatter), encoding="utf-8")
    (reports_dir / "pg_missing_frontmatter.txt").write_text("".join(missing_frontmatter), encoding="utf-8")

    # Top lists
    def write_top(counter: dict, out: Path, top_n: int = 50) -> None:
        items = sorted(counter.items(), key=lambda x: x[1], reverse=True)[:top_n]
        out.write_text("\n".join(f"{count} {path}" for path, count in items) + ("\n" if items else ""), encoding="utf-8")

    write_top(todos_counts, reports_dir / "pg_top_todos.txt")
    write_top(dup_counts, reports_dir / "pg_top_duplicates.txt")

    # Priority CSV: file,todo_count,dup_count,missing_frontmatter
    all_files = set(todos_counts.keys()) | set(dup_counts.keys()) | set(with_frontmatter) | set(missing_frontmatter)
    # normalize with_frontmatter/missing lists to paths only
    with_fm_set = set(p.strip() for p in with_frontmatter)
    missing_fm_set = set(p.strip() for p in missing_frontmatter)
    rows = ["file,todo_count,dup_count,missing_frontmatter"]
    for path in sorted(all_files):
        todo_c = todos_counts.get(path, 0)
        dup_c = dup_counts.get(path, 0)
        missing_flag = "yes" if path in missing_fm_set else ("no" if path in with_fm_set else "unknown")
        rows.append(f"{path},{todo_c},{dup_c},{missing_flag}")
    (reports_dir / "priority.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")

    # Summary
    def count_lines(p: Path) -> int:
        try:
            return sum(1 for _ in p.open("r", encoding="utf-8", errors="ignore"))
        except FileNotFoundError:
            return 0

    summary = []
    summary.append(f"headings_total_lines={count_lines(reports_dir / 'pg_headings.txt')}")
    summary.append(f"todos_total_lines={count_lines(reports_dir / 'pg_todos.txt')}")
    summary.append(f"duplicates_total_lines={count_lines(reports_dir / 'pg_duplicates.txt')}")
    summary.append(f"codeblocks_total_lines={count_lines(reports_dir / 'pg_codeblocks.txt')}")
    summary.append(f"with_frontmatter_files={count_lines(reports_dir / 'pg_with_frontmatter.txt')}")
    summary.append(f"missing_frontmatter_files={count_lines(reports_dir / 'pg_missing_frontmatter.txt')}")
    (reports_dir / "summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")


if __name__ == "__main__":
    repo_root = Path.cwd()
    target_root = repo_root / "Analysis/1-数据库系统/1.1-PostgreSQL"
    reports = repo_root / ".reports"
    scan_directory(target_root, reports)



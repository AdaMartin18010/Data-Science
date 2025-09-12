import csv
import re
from pathlib import Path


def normalize_key(stem: str) -> str:
    s = stem
    s = s.replace("扩充版", "").replace("增强版", "")
    s = re.sub(r"\s+", " ", s).strip()
    # Prefer numeric prefix grouping like 1.1.16-xxx
    m = re.match(r"^(\d+(?:\.\d+)*)(-|_)\s*(.*)$", s)
    if m:
        return m.group(1) + "-" + m.group(3)
    return s


def choose_primary(files: list[str]) -> str:
    # Prefer non-archive, non-扩充/增强, path depth minimal
    def score(p: str) -> tuple:
        penalties = 0
        if "99-归档" in p:
            penalties += 10
        stem = Path(p).stem
        if "扩充版" in stem or "增强版" in stem:
            penalties += 5
        # shorter path preferred
        depth = len(Path(p).parts)
        return (penalties, depth, -len(p))

    return sorted(files, key=score)[0]


def main():
    repo_root = Path.cwd()
    reports = repo_root / ".reports"
    priority_csv = reports / "priority.csv"
    if not priority_csv.exists():
        raise SystemExit("priority.csv not found. Run pg_content_scan first.")

    groups: dict[str, list[str]] = {}
    with priority_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            path = row["file"].strip()
            if not path or not path.endswith(".md"):
                continue
            stem = Path(path).stem
            key = normalize_key(stem)
            groups.setdefault(key, []).append(path)

    out_path = reports / "dedupe_plan.csv"
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["topic_group", "primary_file", "archive_candidates"])
        for key, files in sorted(groups.items(), key=lambda kv: kv[0]):
            if len(files) <= 1:
                continue
            primary = choose_primary(files)
            archives = [p for p in files if p != primary]
            writer.writerow([key, primary, " | ".join(archives)])

    print(f"dedupe_plan_written={out_path}")


if __name__ == "__main__":
    main()



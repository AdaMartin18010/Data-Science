import sys
from pathlib import Path
from datetime import date


TEMPLATE = """---
title: {title}
slug: {slug}
tags: []
pg_version: 16
status: draft
last_review: {today}
owner: TBD
---

"""


def to_slug(name: str) -> str:
    return name.replace(" ", "-")


def ensure_front_matter(file_path: Path) -> bool:
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return False
    if content.lstrip().startswith("---\n"):
        return False
    title = file_path.stem
    slug = to_slug(title)
    fm = TEMPLATE.format(title=title, slug=slug, today=date.today().isoformat())
    file_path.write_text(fm + content, encoding="utf-8")
    return True


def main(list_file: Path) -> None:
    changed = 0
    for line in list_file.read_text(encoding="utf-8").splitlines():
        path = Path(line.strip())
        if not path or not path.is_file():
            continue
        if ensure_front_matter(path):
            changed += 1
    print(f"front_matter_added={changed}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/add_frontmatter.py <list_file>")
        sys.exit(1)
    main(Path(sys.argv[1]))



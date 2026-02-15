from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import quote

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
MKDOCS_FILE = ROOT / "mkdocs.yml"
INDEX_FILE = DOCS_DIR / "index.md"
README_FILE = DOCS_DIR / "README.md"


def sort_key(path: Path) -> tuple[int, int | str]:
    match = re.match(r"^(\d+)", path.stem)
    if match:
        return (0, int(match.group(1)))
    return (1, path.name.lower())


def display_title(path: Path) -> str:
    title = path.stem.replace("-", " ").replace("_", " ").strip()
    title = re.sub(r"\s+", " ", title)
    return title


def yaml_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def collect_sections(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8")
    md = markdown.Markdown(extensions=["toc"])
    md.convert(text)

    sections: list[tuple[str, str]] = []

    def walk(tokens: list[dict]) -> None:
        for token in tokens:
            level = token.get("level")
            if level == 2:
                name = str(token.get("name", "")).strip()
                anchor = str(token.get("id", "")).strip()
                if name and anchor:
                    sections.append((name, anchor))
            children = token.get("children", [])
            if children:
                walk(children)

    walk(getattr(md, "toc_tokens", []))
    return sections


def page_url(path: Path) -> str:
    return f"<{path.name}>"


def page_anchor_url(path: Path, anchor: str) -> str:
    page = quote(path.stem, safe="-_.") + ".html"
    return f"{page}#{anchor}"


def get_site_name() -> str:
    if README_FILE.exists():
        for line in README_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return "CS Notes"


def collect_markdown_files() -> list[Path]:
    files = [
        path
        for path in DOCS_DIR.glob("*.md")
        if path.name.lower() not in {"index.md", "readme.md"}
    ]
    return sorted(files, key=sort_key)


def generate_mkdocs_yaml(site_name: str, markdown_files: list[Path]) -> str:
    lines = [
        f"site_name: {yaml_quote(site_name)}",
        "docs_dir: docs",
        "theme:",
        "  name: readthedocs",
        "use_directory_urls: false",
        "nav:",
        "  - Home: index.md",
    ]

    for md in markdown_files:
        title = display_title(md)
        sections = collect_sections(md)

        if not sections:
            lines.append(f"  - {yaml_quote(title)}: {md.name}")
            continue

        lines.append(f"  - {yaml_quote(title)}:")
        lines.append(f"      - {yaml_quote('Overview')}: {md.name}")
        for section_title, anchor in sections:
            lines.append(
                f"      - {yaml_quote(section_title)}: {page_anchor_url(md, anchor)}"
            )

    return "\n".join(lines) + "\n"


def generate_index_md(markdown_files: list[Path]) -> str:
    sections: list[str] = []

    if README_FILE.exists():
        readme_text = README_FILE.read_text(encoding="utf-8").strip()
        if readme_text:
            sections.append(readme_text)

    note_lines = ["## Notes", ""]
    for md in markdown_files:
        note_lines.append(f"- [{display_title(md)}]({page_url(md)})")
    sections.append("\n".join(note_lines))

    return "\n\n".join(sections).rstrip() + "\n"


def main() -> None:
    markdown_files = collect_markdown_files()
    site_name = get_site_name()

    MKDOCS_FILE.write_text(
        generate_mkdocs_yaml(site_name, markdown_files),
        encoding="utf-8",
    )
    INDEX_FILE.write_text(generate_index_md(markdown_files), encoding="utf-8")

    print(f"Generated {MKDOCS_FILE}")
    print(f"Generated {INDEX_FILE}")
    print(f"Included {len(markdown_files)} markdown files.")


if __name__ == "__main__":
    main()

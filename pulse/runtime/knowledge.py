"""Knowledge file loading.

Knowledge files live under ~/.pulse/knowledge/ and are referenced by
skills via their frontmatter `knowledge:` list.
"""

from __future__ import annotations

from pulse.utils.paths import knowledge_dir


def load_knowledge_file(rel_path: str) -> str:
    """Load a knowledge file by its path relative to knowledge_dir.

    Raises FileNotFoundError (E005) if the file doesn't exist.
    """
    full_path = knowledge_dir() / rel_path

    if not full_path.exists():
        raise FileNotFoundError(
            f"E005: Knowledge file not found: {rel_path}\n"
            f"Expected at: {full_path}\n"
            "Check the skill's `knowledge:` declaration or run "
            "`pulse author-knowledge` to create the file."
        )

    return full_path.read_text()


def load_knowledge_files(paths: list[str]) -> dict[str, str]:
    """Load multiple knowledge files. Returns {path: content}."""
    result: dict[str, str] = {}
    for path in paths:
        result[path] = load_knowledge_file(path)
    return result


def knowledge_file_exists(rel_path: str) -> bool:
    """Check if a knowledge file exists."""
    return (knowledge_dir() / rel_path).exists()

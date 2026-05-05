"""Project-level metadata and placeholders for future viewer components."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectInfo:
    """Describes the purpose and scope of this project."""

    name: str = "openbim-bcf-viewer"
    description: str = (
        "Notebook viewer for IFC visualization with BCF-referenced element highlighting."
    )

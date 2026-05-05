"""IFC loading and indexing helpers for notebook diagnostics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import ifcopenshell
import pandas as pd


def load_ifc(path: str | Path) -> Any:
    """Load an IFC file from disk."""
    return ifcopenshell.open(str(Path(path)))


def build_ifc_index(ifc_file: Any) -> dict[str, dict[str, Any]]:
    """Build a GlobalId keyed index for all IfcProduct entities."""
    index: dict[str, dict[str, Any]] = {}

    for entity in ifc_file.by_type("IfcProduct"):
        global_id = getattr(entity, "GlobalId", None)
        if not global_id:
            continue

        item = {
            "global_id": global_id,
            "ifc_type": entity.is_a() if hasattr(entity, "is_a") else None,
            "name": getattr(entity, "Name", None),
            "tag": getattr(entity, "Tag", None),
            "step_id": entity.id() if hasattr(entity, "id") else None,
            "entity": entity,
        }
        index[global_id] = item

    return index


def to_ifc_dataframe(index: dict[str, dict[str, Any]]) -> pd.DataFrame:
    """Convert IFC index dictionary to a DataFrame for diagnostics."""
    rows = [
        {
            "global_id": item.get("global_id"),
            "ifc_type": item.get("ifc_type"),
            "name": item.get("name"),
            "tag": item.get("tag"),
            "step_id": item.get("step_id"),
            "entity": item.get("entity"),
        }
        for item in index.values()
    ]
    return pd.DataFrame(rows)

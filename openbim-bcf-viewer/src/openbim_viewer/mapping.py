"""BCF-to-IFC mapping utilities."""

from __future__ import annotations

from typing import Any

import pandas as pd


def map_bcf_to_ifc(
    topics: list[dict[str, Any]],
    viewpoints: list[dict[str, Any]],
    ifc_index: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    """Create a row-wise mapping table from BCF topics/viewpoints to IFC products."""
    topic_by_source: dict[str, dict[str, Any]] = {
        str(t.get("source_file", "")): t for t in topics
    }

    rows: list[dict[str, Any]] = []

    for vp in viewpoints:
        source_file = str(vp.get("source_file", ""))
        ifc_guids = vp.get("ifc_guids") or []
        if not isinstance(ifc_guids, list):
            ifc_guids = []

        topic = topic_by_source.get(source_file)
        topic_dir = source_file.rsplit("/", 1)[0] if "/" in source_file else ""

        topic_guid = topic.get("topic_guid") if topic else None
        topic_title = topic.get("title") if topic else None
        topic_status = topic.get("status") if topic else None

        if not ifc_guids:
            rows.append(
                {
                    "topic_dir": topic_dir,
                    "topic_guid": topic_guid,
                    "topic_title": topic_title,
                    "topic_status": topic_status,
                    "viewpoint_file": source_file,
                    "referenced_ifc_guid": None,
                    "found_in_ifc": False,
                    "ifc_type": None,
                    "ifc_name": None,
                    "ifc_tag": None,
                    "ifc_step_id": None,
                }
            )
            continue

        for guid in ifc_guids:
            ifc_item = ifc_index.get(guid, {})
            found = guid in ifc_index
            rows.append(
                {
                    "topic_dir": topic_dir,
                    "topic_guid": topic_guid,
                    "topic_title": topic_title,
                    "topic_status": topic_status,
                    "viewpoint_file": source_file,
                    "referenced_ifc_guid": guid,
                    "found_in_ifc": found,
                    "ifc_type": ifc_item.get("ifc_type") if found else None,
                    "ifc_name": ifc_item.get("name") if found else None,
                    "ifc_tag": ifc_item.get("tag") if found else None,
                    "ifc_step_id": ifc_item.get("step_id") if found else None,
                }
            )

    return pd.DataFrame(rows)


def group_topic_guids(mapping_df: pd.DataFrame) -> pd.DataFrame:
    """Group mapping rows by topic and aggregate referenced IFC GUIDs."""
    if mapping_df.empty:
        return pd.DataFrame(
            columns=[
                "topic_dir",
                "topic_guid",
                "topic_title",
                "topic_status",
                "referenced_ifc_guids",
                "found_count",
                "missing_count",
            ]
        )

    def _collect_guids(series: pd.Series) -> list[str]:
        return sorted({str(v) for v in series.dropna() if str(v)})

    grouped = (
        mapping_df.groupby(["topic_dir", "topic_guid", "topic_title", "topic_status"], dropna=False)
        .agg(
            referenced_ifc_guids=("referenced_ifc_guid", _collect_guids),
            found_count=("found_in_ifc", lambda s: int((s == True).sum())),
            missing_count=("found_in_ifc", lambda s: int((s == False).sum())),
        )
        .reset_index()
    )
    return grouped

"""BCF zip/XML loading helpers with resilient dynamic field extraction."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import zipfile
import xml.etree.ElementTree as ET


def list_bcf_files(bcf_path: str | Path) -> list[str]:
    """List all files inside ZIP-based BCF containers."""
    with zipfile.ZipFile(str(Path(bcf_path)), "r") as zf:
        return sorted(zf.namelist())


def strip_ns(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _append_value(raw_fields: dict[str, Any], key: str, value: Any) -> None:
    if key not in raw_fields:
        raw_fields[key] = value
        return
    existing = raw_fields[key]
    if isinstance(existing, list):
        existing.append(value)
    else:
        raw_fields[key] = [existing, value]


def flatten_xml(root: ET.Element) -> dict[str, Any]:
    """Flatten text + attributes and retain unknown fields dynamically."""
    raw_fields: dict[str, Any] = {}

    for elem in root.iter():
        tag = strip_ns(elem.tag)
        text = (elem.text or "").strip()
        if text:
            _append_value(raw_fields, f"text:{tag}", text)

        for attr_key, attr_val in elem.attrib.items():
            attr_name = strip_ns(attr_key)
            _append_value(raw_fields, f"attr:{tag}@{attr_name}", attr_val)

    return raw_fields


def extract_all_ifc_guids_from_xml(root: ET.Element) -> list[str]:
    """Extract IFC GUID-like values with stable order and no duplicates."""
    candidates = {"ifcguid", "ifc_guid", "guid", "globalid", "global_id"}
    seen: set[str] = set()
    ordered: list[str] = []

    for elem in root.iter():
        tag_name = strip_ns(elem.tag).lower()
        text = (elem.text or "").strip()

        if any(c in tag_name for c in candidates) and text and text not in seen:
            seen.add(text)
            ordered.append(text)

        for attr_key, attr_val in elem.attrib.items():
            key = strip_ns(attr_key).lower().replace("-", "").replace(" ", "")
            key = key.replace("_", "")
            if key in {"ifcguid", "guid", "globalid"} and attr_val and attr_val not in seen:
                seen.add(attr_val)
                ordered.append(attr_val)

    return ordered


def _safe_read_xml_from_zip(zf: zipfile.ZipFile, file_name: str) -> ET.Element | None:
    try:
        return ET.fromstring(zf.read(file_name))
    except Exception:
        return None


def extract_bcf_topics(bcf_path: str | Path) -> list[dict[str, Any]]:
    topics: list[dict[str, Any]] = []
    with zipfile.ZipFile(str(Path(bcf_path)), "r") as zf:
        for file_name in sorted(zf.namelist()):
            if not file_name.lower().endswith("markup.bcf"):
                continue
            root = _safe_read_xml_from_zip(zf, file_name)
            if root is None:
                continue

            topic_dir = file_name.rsplit("/", 1)[0] if "/" in file_name else ""
            topic_guid = None
            title = None
            status = None
            topic_type = None
            priority = None
            creation_author = None
            creation_date = None
            comments: list[str] = []

            for elem in root.iter():
                tag = strip_ns(elem.tag).lower()
                text = (elem.text or "").strip()

                if tag == "topic":
                    topic_guid = elem.attrib.get("Guid") or elem.attrib.get("guid") or topic_guid
                elif tag == "title" and text and title is None:
                    title = text
                elif tag in {"topicstatus", "status"} and text and status is None:
                    status = text
                elif tag in {"topictype", "type"} and text and topic_type is None:
                    topic_type = text
                elif tag == "priority" and text and priority is None:
                    priority = text
                elif tag == "creationauthor" and text and creation_author is None:
                    creation_author = text
                elif tag == "creationdate" and text and creation_date is None:
                    creation_date = text
                elif tag == "comment":
                    c = elem.attrib.get("Comment") or text
                    if c:
                        comments.append(c)

            topics.append(
                {
                    "topic_dir": topic_dir,
                    "markup_file": file_name,
                    "topic_guid": topic_guid,
                    "title": title,
                    "status": status,
                    "type": topic_type,
                    "priority": priority,
                    "creation_author": creation_author,
                    "creation_date": creation_date,
                    "comments": comments,
                    "raw_fields": flatten_xml(root),
                }
            )
    return topics


def extract_bcf_viewpoints(bcf_path: str | Path) -> list[dict[str, Any]]:
    viewpoints: list[dict[str, Any]] = []
    with zipfile.ZipFile(str(Path(bcf_path)), "r") as zf:
        for file_name in sorted(zf.namelist()):
            if not file_name.lower().endswith(".bcfv"):
                continue
            root = _safe_read_xml_from_zip(zf, file_name)
            if root is None:
                continue

            topic_dir = file_name.rsplit("/", 1)[0] if "/" in file_name else ""
            viewpoints.append(
                {
                    "topic_dir": topic_dir,
                    "viewpoint_file": file_name,
                    "referenced_ifc_guids": extract_all_ifc_guids_from_xml(root),
                    "raw_fields": flatten_xml(root),
                }
            )
    return viewpoints

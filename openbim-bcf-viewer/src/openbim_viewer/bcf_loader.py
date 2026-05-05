"""BCF zip/XML loading helpers with resilient dynamic field extraction."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import zipfile
import xml.etree.ElementTree as ET


def list_bcf_files(bcf_path: str | Path) -> list[str]:
    """List XML files inside a BCF archive."""
    with zipfile.ZipFile(str(Path(bcf_path)), "r") as zf:
        return [name for name in zf.namelist() if name.lower().endswith(".xml")]


def strip_ns(tag: str) -> str:
    """Strip XML namespace from tag name."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def flatten_xml(root: ET.Element) -> dict[str, Any]:
    """Flatten all text fields and attributes into raw_fields."""
    raw_fields: dict[str, Any] = {}

    for elem in root.iter():
        path_parts = []
        current = elem
        while current is not None:
            path_parts.append(strip_ns(current.tag))
            current = None  # ElementTree has no parent references; use local tag only
        base_key = "/".join(reversed(path_parts))

        text = (elem.text or "").strip()
        if text:
            key = f"text:{base_key}"
            if key in raw_fields:
                if isinstance(raw_fields[key], list):
                    raw_fields[key].append(text)
                else:
                    raw_fields[key] = [raw_fields[key], text]
            else:
                raw_fields[key] = text

        for attr_key, attr_val in elem.attrib.items():
            key = f"attr:{base_key}@{strip_ns(attr_key)}"
            if key in raw_fields:
                if isinstance(raw_fields[key], list):
                    raw_fields[key].append(attr_val)
                else:
                    raw_fields[key] = [raw_fields[key], attr_val]
            else:
                raw_fields[key] = attr_val

    return raw_fields


def extract_all_ifc_guids_from_xml(root: ET.Element) -> list[str]:
    """Extract all IfcGuid-like values from element text and attributes."""
    guids: set[str] = set()

    for elem in root.iter():
        tag_name = strip_ns(elem.tag).lower()
        text = (elem.text or "").strip()

        if "ifcguid" in tag_name and text:
            guids.add(text)

        for attr_key, attr_val in elem.attrib.items():
            if "ifcguid" in strip_ns(attr_key).lower() and attr_val:
                guids.add(attr_val)

        if tag_name in {"component", "selection"}:
            for attr_key, attr_val in elem.attrib.items():
                if strip_ns(attr_key).lower() in {"ifcguid", "guid"} and attr_val:
                    guids.add(attr_val)

    return sorted(guids)


def _safe_read_xml_from_zip(zf: zipfile.ZipFile, name: str) -> ET.Element | None:
    try:
        data = zf.read(name)
        return ET.fromstring(data)
    except Exception:
        return None


def extract_bcf_topics(bcf_path: str | Path) -> list[dict[str, Any]]:
    """Extract topic-like XML payloads and preserve dynamic raw fields."""
    topics: list[dict[str, Any]] = []
    with zipfile.ZipFile(str(Path(bcf_path)), "r") as zf:
        for name in zf.namelist():
            if not name.lower().endswith("markup.bcf") and not name.lower().endswith(".xml"):
                continue
            root = _safe_read_xml_from_zip(zf, name)
            if root is None:
                continue

            topic_guid = None
            title = None
            status = None
            comments: list[str] = []

            for elem in root.iter():
                tag = strip_ns(elem.tag)
                text = (elem.text or "").strip()
                low = tag.lower()

                if low == "topic":
                    topic_guid = elem.attrib.get("Guid") or elem.attrib.get("guid") or topic_guid
                elif low == "title" and text and title is None:
                    title = text
                elif low == "topicstatus" and text and status is None:
                    status = text
                elif low == "comment" and text:
                    comments.append(text)

            topics.append(
                {
                    "source_file": name,
                    "topic_guid": topic_guid,
                    "title": title,
                    "status": status,
                    "comments": comments,
                    "raw_fields": flatten_xml(root),
                }
            )
    return topics


def extract_bcf_viewpoints(bcf_path: str | Path) -> list[dict[str, Any]]:
    """Extract viewpoints/components XML payloads and IFC GUID references."""
    viewpoints: list[dict[str, Any]] = []
    with zipfile.ZipFile(str(Path(bcf_path)), "r") as zf:
        for name in zf.namelist():
            lower = name.lower()
            if not (lower.endswith(".bcfv") or lower.endswith("viewpoint.bcfv") or lower.endswith(".xml")):
                continue
            root = _safe_read_xml_from_zip(zf, name)
            if root is None:
                continue

            guids = extract_all_ifc_guids_from_xml(root)
            viewpoints.append(
                {
                    "source_file": name,
                    "ifc_guids": guids,
                    "raw_fields": flatten_xml(root),
                }
            )
    return viewpoints

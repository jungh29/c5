"""Small diagnostic CLI for IFC/BCF mapping checks."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .bcf_loader import extract_bcf_topics, extract_bcf_viewpoints
from .ifc_loader import build_ifc_index, load_ifc
from .mapping import map_bcf_to_ifc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openbim_viewer.cli", description="OpenBIM diagnostic CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_parser = sub.add_parser("inspect", help="Inspect IFC/BCF and export mapping")
    inspect_parser.add_argument("--ifc", required=True, help="Path to IFC file")
    inspect_parser.add_argument("--bcf", required=True, help="Path to BCF ZIP/BCFZIP file")
    inspect_parser.add_argument("--exports-dir", default="exports", help="Directory for CSV/XLSX outputs")
    return parser


def _summary_from_mapping(df_mapping: Any, ifc_count: int, topics_count: int, viewpoints_count: int) -> dict[str, int]:
    ref = 0 if df_mapping is None or df_mapping.empty else int(df_mapping["referenced_ifc_guid"].notna().sum())
    found = 0 if df_mapping is None or df_mapping.empty else int((df_mapping["found_in_ifc"] == True).sum())
    missing = max(ref - found, 0)
    return {
        "ifc_products": ifc_count,
        "bcf_topics": topics_count,
        "bcf_viewpoints": viewpoints_count,
        "referenced_guids": ref,
        "found_guids": found,
        "missing_guids": missing,
    }


def run_inspect(ifc_path: str, bcf_path: str, exports_dir: str = "exports") -> int:
    ifc_file_path = Path(ifc_path)
    bcf_file_path = Path(bcf_path)

    if not ifc_file_path.exists():
        print(f"Fehler: IFC-Datei nicht gefunden: {ifc_file_path}")
        return 2
    if not bcf_file_path.exists():
        print(f"Fehler: BCF-Datei nicht gefunden: {bcf_file_path}")
        return 2

    ifc_file = load_ifc(ifc_file_path)
    ifc_index = build_ifc_index(ifc_file)

    topics = extract_bcf_topics(bcf_file_path)
    viewpoints = extract_bcf_viewpoints(bcf_file_path)
    df_mapping = map_bcf_to_ifc(topics, viewpoints, ifc_index)

    summary = _summary_from_mapping(df_mapping, len(ifc_index), len(topics), len(viewpoints))

    print("=== Diagnose Summary ===")
    print(f"IFC-Produkte: {summary['ifc_products']}")
    print(f"BCF-Topics: {summary['bcf_topics']}")
    print(f"BCF-Viewpoints: {summary['bcf_viewpoints']}")
    print(f"Referenzierte GUIDs: {summary['referenced_guids']}")
    print(f"Im IFC gefunden: {summary['found_guids']}")
    print(f"Fehlende GUIDs: {summary['missing_guids']}")

    exports_path = Path(exports_dir)
    exports_path.mkdir(parents=True, exist_ok=True)

    csv_path = exports_path / "bcf_ifc_mapping.csv"
    df_mapping.to_csv(csv_path, index=False)
    print(f"CSV geschrieben: {csv_path}")

    xlsx_path = exports_path / "bcf_ifc_mapping.xlsx"
    try:
        import openpyxl  # noqa: F401

        df_mapping.to_excel(xlsx_path, index=False)
        print(f"XLSX geschrieben: {xlsx_path}")
    except Exception:
        print("Hinweis: XLSX-Export übersprungen (openpyxl nicht verfügbar).")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "inspect":
        return run_inspect(args.ifc, args.bcf, args.exports_dir)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

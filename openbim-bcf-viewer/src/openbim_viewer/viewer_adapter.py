"""Notebook viewer adapter for IFC PoC rendering/highlighting.

This module prefers `ifc-viewer-anywidget` when available and falls back to
`ifcopenshell.geom` + `pythreejs` for basic visualization and GUID highlighting.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import ifcopenshell


@dataclass
class ViewerCapabilities:
    """Runtime capability flags for selected viewer backend."""

    backend: str
    can_render: bool
    can_highlight_guid: bool


class IFCViewerAdapter:
    """Adapter with a best-effort backend selection for notebook IFC display."""

    def __init__(self) -> None:
        self._viewer_backend = self._detect_anywidget_backend()

    @staticmethod
    def _detect_anywidget_backend() -> Any | None:
        try:
            from ifc_viewer_anywidget import IFCViewer  # type: ignore

            return IFCViewer
        except Exception:
            return None

    def capabilities(self) -> ViewerCapabilities:
        if self._viewer_backend is not None:
            return ViewerCapabilities(
                backend="ifc-viewer-anywidget",
                can_render=True,
                can_highlight_guid=False,
            )
        return ViewerCapabilities(
            backend="ifcopenshell-geom+pythreejs",
            can_render=True,
            can_highlight_guid=True,
        )

    def show(self, ifc_path: str | Path) -> Any:
        """Return a displayable notebook widget/object for an IFC model."""
        ifc_path = Path(ifc_path)
        if self._viewer_backend is not None:
            viewer = self._viewer_backend()
            viewer.load_ifc(str(ifc_path))
            return viewer
        return self._build_fallback_scene(ifc_path)

    def highlight_guid(self, ifc_path: str | Path, guid: str) -> Any:
        """Return a displayable object with one GUID highlighted (fallback path)."""
        ifc_path = Path(ifc_path)
        if self._viewer_backend is not None:
            raise NotImplementedError(
                "GUID highlighting via ifc-viewer-anywidget is currently not guaranteed. "
                "Use fallback backend."
            )
        return self._build_fallback_scene(ifc_path, highlighted_guid=guid)

    def _build_fallback_scene(
        self, ifc_path: Path, highlighted_guid: str | None = None
    ) -> Any:
        """Build a minimal pythreejs scene using ifcopenshell.geom meshes."""
        import numpy as np
        import pythreejs as p3

        model = ifcopenshell.open(str(ifc_path))
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)

        groups: list[p3.Mesh] = []
        default_color = "#9fa8b3"
        highlight_color = "#e53935"

        for product in model.by_type("IfcProduct"):
            if not getattr(product, "Representation", None):
                continue
            try:
                shape = ifcopenshell.geom.create_shape(settings, product)
            except Exception:
                continue

            verts = np.array(shape.geometry.verts, dtype=float).reshape((-1, 3))
            faces = np.array(shape.geometry.faces, dtype=int).reshape((-1, 3))

            geometry = p3.BufferGeometry(
                attributes={
                    "position": p3.BufferAttribute(verts, normalized=False),
                    "index": p3.BufferAttribute(faces.ravel(), normalized=False),
                }
            )
            color = highlight_color if product.GlobalId == highlighted_guid else default_color
            material = p3.MeshLambertMaterial(color=color, side="DoubleSide")
            mesh = p3.Mesh(geometry=geometry, material=material)
            groups.append(mesh)

        scene = p3.Scene(children=[*groups, p3.AmbientLight(intensity=0.7)])
        camera = p3.PerspectiveCamera(position=[10, 10, 10], up=[0, 0, 1])
        controls = p3.OrbitControls(controlling=camera)
        renderer = p3.Renderer(
            camera=camera,
            scene=scene,
            controls=[controls],
            width=900,
            height=600,
            antialias=True,
        )
        return renderer

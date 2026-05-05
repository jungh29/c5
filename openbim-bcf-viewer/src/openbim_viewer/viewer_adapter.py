"""Notebook viewer adapter for IFC PoC rendering/highlighting."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import ifcopenshell


@dataclass
class ViewerCapabilities:
    backend: str
    can_render: bool
    can_highlight_guid: bool


class FallbackIFCViewer:
    """Minimal pythreejs-based IFC viewer with GUID highlighting."""

    def __init__(self, ifc_path: str | Path, max_elements: int = 200) -> None:
        self.ifc_path = Path(ifc_path)
        self.max_elements = max_elements
        self.guid_to_mesh: dict[str, Any] = {}
        self._default_color = "#9fa8b3"
        self._highlight_color = "#e53935"
        self.renderer = self._build_scene()

    def _build_scene(self) -> Any:
        import numpy as np
        import pythreejs as p3

        model = ifcopenshell.open(str(self.ifc_path))
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)

        meshes: list[Any] = []
        count = 0

        for product in model.by_type("IfcProduct"):
            if count >= self.max_elements:
                break
            if not getattr(product, "Representation", None):
                continue
            guid = getattr(product, "GlobalId", None)
            if not guid:
                continue

            try:
                shape = ifcopenshell.geom.create_shape(settings, product)
                verts = np.array(shape.geometry.verts, dtype=float).reshape((-1, 3))
                faces = np.array(shape.geometry.faces, dtype=int).reshape((-1, 3))
            except Exception:
                continue

            geometry = p3.BufferGeometry(
                attributes={
                    "position": p3.BufferAttribute(verts, normalized=False),
                    "index": p3.BufferAttribute(faces.ravel(), normalized=False),
                }
            )
            material = p3.MeshLambertMaterial(color=self._default_color, side="DoubleSide")
            mesh = p3.Mesh(geometry=geometry, material=material)

            meshes.append(mesh)
            self.guid_to_mesh[guid] = mesh
            count += 1

        scene = p3.Scene(children=[*meshes, p3.AmbientLight(intensity=0.7)])
        camera = p3.PerspectiveCamera(position=[10, 10, 10], up=[0, 0, 1])
        controls = p3.OrbitControls(controlling=camera)
        return p3.Renderer(
            camera=camera,
            scene=scene,
            controls=[controls],
            width=900,
            height=600,
            antialias=True,
        )

    def clear_highlight(self) -> None:
        for mesh in self.guid_to_mesh.values():
            mesh.material.color = self._default_color

    def highlight_guid(self, guid: str) -> None:
        self.clear_highlight()
        mesh = self.guid_to_mesh.get(guid)
        if mesh is not None:
            mesh.material.color = self._highlight_color

    def highlight_guids(self, guids: list[str]) -> None:
        self.clear_highlight()
        for guid in guids:
            mesh = self.guid_to_mesh.get(guid)
            if mesh is not None:
                mesh.material.color = self._highlight_color


class IFCViewerAdapter:
    def __init__(self, max_elements: int = 200) -> None:
        self.max_elements = max_elements
        self._anywidget_viewer_cls = self._detect_anywidget_backend()
        self.viewer: Any | None = None
        self._active_backend = "none"

    @staticmethod
    def _detect_anywidget_backend() -> Any | None:
        try:
            from ifc_viewer_anywidget import IFCViewer  # type: ignore

            return IFCViewer
        except Exception:
            return None

    def capabilities(self) -> ViewerCapabilities:
        return ViewerCapabilities(
            backend=self._active_backend,
            can_render=self.viewer is not None,
            can_highlight_guid=bool(self.viewer is not None and hasattr(self.viewer, "highlight_guids")),
        )

    def show(self, ifc_path: str | Path) -> Any:
        ifc_path = Path(ifc_path)

        if self._anywidget_viewer_cls is not None:
            try:
                any_viewer = self._anywidget_viewer_cls()
                any_viewer.load_ifc(str(ifc_path))
                if hasattr(any_viewer, "highlight_guids"):
                    self.viewer = any_viewer
                    self._active_backend = "ifc-viewer-anywidget"
                    return self.viewer
            except Exception:
                pass

        self.viewer = FallbackIFCViewer(ifc_path=ifc_path, max_elements=self.max_elements)
        self._active_backend = "ifcopenshell-geom+pythreejs"
        return self.viewer.renderer

    def clear_highlight(self) -> None:
        if self.viewer is not None and hasattr(self.viewer, "clear_highlight"):
            self.viewer.clear_highlight()

    def highlight_guid(self, guid: str) -> None:
        if self.viewer is not None and hasattr(self.viewer, "highlight_guid"):
            self.viewer.highlight_guid(guid)

    def highlight_guids(self, guids: list[str]) -> None:
        if self.viewer is not None and hasattr(self.viewer, "highlight_guids"):
            self.viewer.highlight_guids(guids)

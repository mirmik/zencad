from OCP.AIS import AIS_Triangulation
from OCP.Aspect import Aspect_IS_EMPTY, Aspect_IS_SOLID

from zencad.bbox import BoundaryBox
from zencad.color import default_border_color
from zencad.geom.mesh import (
    mesh_to_poly_triangulation,
    normalize_mesh_display_mode,
)
from zencad.interactive.interactive_object import InteractiveObject


def configure_mesh_presentation(
    ais_object,
    display_mode,
    face_color,
    edge_color,
):
    """Configure shaded, wireframe, or combined native mesh rendering."""
    display_mode = normalize_mesh_display_mode(display_mode)
    drawer = ais_object.Attributes()
    drawer.SetupOwnShadingAspect()
    aspect = drawer.ShadingAspect().Aspect()
    aspect.SetInteriorStyle(
        Aspect_IS_EMPTY if display_mode == "wireframe" else Aspect_IS_SOLID
    )
    aspect.SetDrawEdges(display_mode != "shaded")
    aspect.SetEdgeColor(
        face_color if display_mode == "wireframe" else edge_color
    )
    return display_mode


class MeshInteractiveObject(InteractiveObject):
    """Direct-viewer controller for a :class:`MeshData` object."""

    def __init__(self, mesh, color, display_mode=None):
        self.mesh = mesh
        self.mesh_display_mode = normalize_mesh_display_mode(display_mode)
        self.triangulation = mesh_to_poly_triangulation(mesh)
        ais_object = AIS_Triangulation(self.triangulation)
        # The viewer default is AIS_Shaded (mode 1), while
        # AIS_Triangulation only fills its mode-0 presentation.  OCCT accepts
        # mode 1 without reporting an error but displays an empty object.
        ais_object.SetDisplayMode(0)
        super().__init__(
            ais_object,
            color=color,
            border_color=default_border_color(),
        )

    def set_color(self, *args, **kwargs):
        super().set_color(*args, **kwargs)
        configure_mesh_presentation(
            self.ais_object,
            self.mesh_display_mode,
            self._color.to_Quantity_Color(),
            self._border_color.to_Quantity_Color(),
        )

    def set_mesh_display_mode(self, display_mode):
        self.mesh_display_mode = configure_mesh_presentation(
            self.ais_object,
            display_mode,
            self._color.to_Quantity_Color(),
            self._border_color.to_Quantity_Color(),
        )
        if self._context is not None:
            self._context.Redisplay(self.ais_object, True)
        return self

    def boundbox(self):
        xs, ys, zs = zip(*self.mesh.positions)
        return BoundaryBox(
            min(xs),
            max(xs),
            min(ys),
            max(ys),
            min(zs),
            max(zs),
        )

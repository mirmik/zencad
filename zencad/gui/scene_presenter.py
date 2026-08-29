"""GUI-thread materialization and transactional live scene presentation."""

from dataclasses import dataclass, field, replace
import math
from numbers import Real
from types import MappingProxyType
from typing import Callable, Mapping

from OCP.AIS import AIS_Line, AIS_Point, AIS_Shape, AIS_Triangulation
from OCP.Aspect import Aspect_TOD_ABSOLUTE, Aspect_TOL_SOLID
from OCP.Geom import Geom_CartesianPoint
from OCP.gp import gp_Pnt, gp_Quaternion, gp_Trsf, gp_Vec
from OCP.Prs3d import Prs3d_ArrowAspect, Prs3d_LineAspect

from zencad.color import Color
from zencad.geom.mesh import normalize_mesh_display_mode
from zencad.runtime.scene_protocol import (
    SceneObjectRecord,
    SceneSnapshot,
    decode_brep,
    decode_mesh,
    decode_json_payload,
)
from zencad.runtime.scene_patch_protocol import (
    ScenePatch,
    ScenePatchSequenceError,
    SupersededScenePatchError,
    ensure_current_scene_patch,
)
from zencad.settings import Settings


class ScenePresentationError(RuntimeError):
    """A snapshot could not be safely presented."""


@dataclass(frozen=True)
class PresentedSceneObject:
    object_id: str
    ais_object: object
    shape: object
    visible: bool
    properties: Mapping = field(
        default_factory=lambda: MappingProxyType({})
    )
    kind: str = "brep"


def _rgba(value, name) -> tuple[float, float, float, float]:
    if not isinstance(value, (tuple, list)) or len(value) != 4:
        raise ScenePresentationError(f"{name} must be an RGBA sequence")
    if any(
        not isinstance(component, Real)
        or isinstance(component, bool)
        or not math.isfinite(component)
        or not 0 <= component <= 1
        for component in value
    ):
        raise ScenePresentationError(f"{name} components must be in [0, 1]")
    return tuple(float(component) for component in value)


def _vector(value, name, size) -> tuple[float, ...]:
    if not isinstance(value, (tuple, list)) or len(value) != size:
        raise ScenePresentationError(f"{name} must contain {size} numbers")
    if any(
        not isinstance(component, Real)
        or isinstance(component, bool)
        or not math.isfinite(component)
        for component in value
    ):
        raise ScenePresentationError(f"{name} must contain only numbers")
    return tuple(float(component) for component in value)


def _transform_state(properties: Mapping) -> Mapping:
    raw = properties.get("transform")
    if raw is None:
        raw = {
            "scale": 1.0,
            "rotation": (0, 0, 0, 1),
            "translation": (0, 0, 0),
        }
    if not isinstance(raw, Mapping):
        raise ScenePresentationError("transform must be an object")

    scale = raw.get("scale", 1.0)
    if (
        not isinstance(scale, Real)
        or isinstance(scale, bool)
        or not math.isfinite(scale)
        or scale == 0
    ):
        raise ScenePresentationError("transform scale must be non-zero")
    rotation = _vector(raw.get("rotation", (0, 0, 0, 1)), "rotation", 4)
    if not any(rotation):
        raise ScenePresentationError(
            "rotation quaternion must be non-zero"
        )
    translation = _vector(raw.get("translation", (0, 0, 0)), "translation", 3)
    return MappingProxyType({
        "scale": float(scale),
        "rotation": rotation,
        "translation": translation,
    })


def _presentation_state(properties: Mapping) -> Mapping:
    visible = properties.get("visible", True)
    if not isinstance(visible, bool):
        raise ScenePresentationError("visible must be a boolean")
    return MappingProxyType({
        "visible": visible,
        "color": _rgba(
            properties.get("color", (0.6, 0.6, 0.8, 0)),
            "color",
        ),
        "border_color": _rgba(
            properties.get("border_color", (0, 0, 0, 0)),
            "border_color",
        ),
        "wire_color": _rgba(
            properties.get("wire_color", (0, 0, 0, 0)),
            "wire_color",
        ),
        "display_mode": normalize_mesh_display_mode(
            properties.get("display_mode")
        ),
        "transform": _transform_state(properties),
    })


def _transform(properties: Mapping) -> gp_Trsf:
    state = _transform_state(properties)
    transformation = gp_Trsf()
    rotation = state["rotation"]
    translation = state["translation"]
    transformation.SetRotation(gp_Quaternion(*rotation))
    transformation.SetScaleFactor(state["scale"])
    transformation.SetTranslationPart(gp_Vec(*translation))
    return transformation


def materialize_scene_object(record: SceneObjectRecord) -> PresentedSceneObject:
    """Create a fully styled AIS object without binding it to a context."""
    state = _presentation_state(record.properties)
    color = state["color"]
    border = state["border_color"]
    wire = state["wire_color"]
    transformation = _transform(state)

    if record.kind == "brep":
        shape = decode_brep(record.payload)
        ais_object = AIS_Shape(shape)
    elif record.kind == "mesh":
        from zencad.geom.mesh import mesh_to_poly_triangulation

        shape = None
        mesh = decode_mesh(record.payload)
        ais_object = AIS_Triangulation(mesh_to_poly_triangulation(mesh))
        # DisplayWidget configures the context for AIS_Shaded (mode 1), but
        # AIS_Triangulation renders its geometry in presentation mode 0.
        ais_object.SetDisplayMode(0)
    elif record.kind == "point":
        point = _vector(decode_json_payload(record.payload), "point", 3)
        shape = None
        ais_object = AIS_Point(Geom_CartesianPoint(gp_Pnt(*point)))
    elif record.kind == "line":
        data = decode_json_payload(record.payload)
        if not isinstance(data, Mapping):
            raise ScenePresentationError("line payload must be an object")
        start = _vector(data.get("start"), "line start", 3)
        end = _vector(data.get("end"), "line end", 3)
        width = data.get("width", 1)
        if (
            not isinstance(width, Real)
            or isinstance(width, bool)
            or not math.isfinite(width)
            or width <= 0
        ):
            raise ScenePresentationError("line width must be positive")
        arrow_length = data.get("arrow_length")
        if arrow_length is not None and (
            not isinstance(arrow_length, Real)
            or isinstance(arrow_length, bool)
            or not math.isfinite(arrow_length)
            or arrow_length <= 0
        ):
            raise ScenePresentationError("arrow length must be positive")
        shape = None
        ais_object = AIS_Line(
            Geom_CartesianPoint(gp_Pnt(*start)),
            Geom_CartesianPoint(gp_Pnt(*end)),
        )
    else:
        raise ScenePresentationError(
            f"Unsupported scene object kind: {record.kind!r}"
        )

    drawer = ais_object.Attributes()
    drawer.SetFaceBoundaryDraw(True)
    drawer.SetTypeOfDeflection(Aspect_TOD_ABSOLUTE)
    drawer.SetMaximalChordialDeviation(
        Settings.get(["view", "default_chordial_deviation"])
    )

    face_color = Color(color).to_Quantity_Color()
    ais_object.SetColor(face_color)
    ais_object.SetTransparency(color[3])
    if record.kind == "brep":
        line_aspect = drawer.LineAspect()
        if line_aspect is not None:
            line_aspect.SetColor(Color(border).to_Quantity_Color())
            drawer.SetFaceBoundaryAspect(line_aspect)
        wire_aspect = drawer.WireAspect()
        if wire_aspect is not None:
            wire_aspect.SetColor(Color(wire).to_Quantity_Color())
            drawer.SetWireAspect(wire_aspect)
    elif record.kind == "mesh":
        from zencad.interactive.mesh import configure_mesh_presentation

        configure_mesh_presentation(
            ais_object,
            state["display_mode"],
            face_color,
            Color(border).to_Quantity_Color(),
        )
    elif record.kind == "line":
        drawer.SetLineAspect(Prs3d_LineAspect(
            face_color,
            Aspect_TOL_SOLID,
            float(width),
        ))
        if arrow_length is not None:
            arrow_aspect = Prs3d_ArrowAspect()
            arrow_aspect.SetLength(float(arrow_length))
            drawer.SetArrowAspect(arrow_aspect)
            drawer.SetLineArrowDraw(True)
    ais_object.SetLocalTransformation(transformation)
    return PresentedSceneObject(
        object_id=record.object_id,
        ais_object=ais_object,
        shape=shape,
        visible=state["visible"],
        properties=state,
        kind=record.kind,
    )


class ScenePresenter:
    """Own scene AIS handles while preserving permanent viewer helpers."""

    def __init__(
        self,
        widget,
        materializer: (
            Callable[[SceneObjectRecord], PresentedSceneObject] | None
        ) = None,
        patch_applier=None,
    ):
        self.widget = widget
        self.context = widget.Context
        self.view = widget.View
        self._materializer = materializer or materialize_scene_object
        self._patch_applier = patch_applier
        self._objects: tuple[PresentedSceneObject, ...] = ()
        self._objects_by_id: dict[str, PresentedSceneObject] = {}
        self.committed_generation: int | None = None
        self.committed_scene_revision: int | None = None
        self.last_patch_sequence: int | None = None

    @property
    def objects(self):
        return self._objects

    def _assert_gui_thread(self):
        checker = getattr(self.widget, "assert_gui_thread", None)
        if checker is not None:
            checker()

    def _camera_action(self, snapshot: SceneSnapshot):
        policy = snapshot.camera_policy
        if policy == "preserve":
            return ("fit", None) if self.committed_generation is None else ("preserve", None)
        if policy == "fit":
            return "fit", None
        if policy == "explicit":
            camera = snapshot.metadata.get("camera")
            if not isinstance(camera, Mapping):
                raise ScenePresentationError(
                    "explicit camera policy requires metadata.camera"
                )
            scale = camera.get("scale")
            if not isinstance(scale, Real) or scale <= 0:
                raise ScenePresentationError("camera scale must be positive")
            return "explicit", {
                "scale": float(scale),
                "eye": _vector(camera.get("eye"), "camera eye", 3),
                "center": _vector(camera.get("center"), "camera center", 3),
            }
        raise ScenePresentationError(f"Unsupported camera policy: {policy!r}")

    def _apply_camera(self, action, camera):
        if action == "fit":
            self.view.FitAll(0.07, False)
        elif action == "explicit":
            self.widget.restore_location(camera, redraw=False)

    def _restore_previous(self, added, previous_camera):
        for item in added:
            self.context.Remove(item.ais_object, False)
        for item in self._objects:
            if item.visible:
                self.context.Display(item.ais_object, False)
        self.widget.restore_location(previous_camera, redraw=False)
        self.context.UpdateCurrentViewer()

    def apply(self, snapshot: SceneSnapshot, scene_revision=0):
        """Replace the current scene and return the committed generation."""
        self._assert_gui_thread()
        if not isinstance(snapshot, SceneSnapshot):
            raise TypeError("ScenePresenter requires a SceneSnapshot")
        if (
            not isinstance(scene_revision, int)
            or isinstance(scene_revision, bool)
            or scene_revision < 0
        ):
            raise ScenePresentationError(
                "Scene revision must be a non-negative integer"
            )

        try:
            camera_action, explicit_camera = self._camera_action(snapshot)
            prepared = []
            for record in snapshot.objects:
                item = self._materializer(record)
                state = _presentation_state(record.properties)
                prepared.append(replace(
                    item,
                    visible=state["visible"],
                    properties=state,
                ))
            prepared = tuple(prepared)
        except ScenePresentationError:
            raise
        except Exception as exception:
            raise ScenePresentationError(
                f"Failed to materialize generation {snapshot.generation}"
            ) from exception

        previous_camera = self.widget.store_location()
        added = []
        try:
            for item in self._objects:
                self.context.Remove(item.ais_object, False)
            for item in prepared:
                if item.visible:
                    added.append(item)
                    self.context.Display(item.ais_object, False)
            self._apply_camera(camera_action, explicit_camera)
            self.context.ClearSelected(False)
            self.context.UpdateCurrentViewer()
        except Exception as exception:
            try:
                self._restore_previous(added, previous_camera)
            except Exception as rollback_exception:
                raise ScenePresentationError(
                    "Scene commit and rollback both failed"
                ) from rollback_exception
            raise ScenePresentationError(
                f"Failed to commit generation {snapshot.generation}"
            ) from exception

        self._objects = prepared
        self._objects_by_id = {item.object_id: item for item in prepared}
        self.committed_generation = snapshot.generation
        self.committed_scene_revision = scene_revision
        self.last_patch_sequence = None
        self._update_widget_shape(prepared)
        return snapshot.generation

    def _apply_object_state(self, item, old_state, new_state):
        changed = {
            name
            for name in new_state
            if new_state[name] != old_state[name]
        }
        if not changed:
            return
        if self._patch_applier is not None:
            self._patch_applier(item, old_state, new_state, changed)
        else:
            ais_object = item.ais_object
            if "transform" in changed:
                ais_object.SetLocalTransformation(_transform(new_state))
            if "color" in changed:
                color = new_state["color"]
                ais_object.SetColor(Color(color).to_Quantity_Color())
                ais_object.SetTransparency(color[3])
            drawer = ais_object.Attributes()
            if "color" in changed and item.kind == "line":
                line_aspect = drawer.LineAspect()
                if line_aspect is not None:
                    line_aspect.SetColor(
                        Color(new_state["color"]).to_Quantity_Color()
                    )
                    drawer.SetLineAspect(line_aspect)
            if "border_color" in changed and item.kind == "brep":
                line_aspect = drawer.LineAspect()
                if line_aspect is not None:
                    line_aspect.SetColor(
                        Color(new_state["border_color"]).to_Quantity_Color()
                    )
                    drawer.SetFaceBoundaryAspect(line_aspect)
            if "wire_color" in changed and item.kind == "brep":
                wire_aspect = drawer.WireAspect()
                if wire_aspect is not None:
                    wire_aspect.SetColor(
                        Color(new_state["wire_color"]).to_Quantity_Color()
                    )
                    drawer.SetWireAspect(wire_aspect)
            if item.kind == "mesh" and changed & {
                "color",
                "border_color",
                "display_mode",
            }:
                from zencad.interactive.mesh import configure_mesh_presentation

                configure_mesh_presentation(
                    ais_object,
                    new_state["display_mode"],
                    Color(new_state["color"]).to_Quantity_Color(),
                    Color(new_state["border_color"]).to_Quantity_Color(),
                )
            if changed - {"visible"}:
                self.context.Redisplay(ais_object, False)

        if "visible" in changed:
            if new_state["visible"]:
                self.context.Display(item.ais_object, False)
            else:
                self.context.Erase(item.ais_object, False)

    def apply_patch(self, patch: ScenePatch):
        """Apply one absolute live batch and redraw at most once."""
        self._assert_gui_thread()
        if not isinstance(patch, ScenePatch):
            raise TypeError("ScenePresenter requires a ScenePatch")
        if self.committed_generation is None:
            raise ScenePresentationError("Cannot patch an empty scene")
        try:
            ensure_current_scene_patch(
                patch,
                self.committed_generation,
                self.committed_scene_revision,
            )
        except SupersededScenePatchError as exception:
            raise ScenePresentationError(str(exception)) from exception
        if (
            self.last_patch_sequence is not None
            and patch.sequence <= self.last_patch_sequence
        ):
            raise ScenePatchSequenceError(
                "ScenePatch sequence is duplicate or out of order"
            )

        prepared = []
        for update in patch.updates:
            try:
                item = self._objects_by_id[update.object_id]
            except KeyError as exception:
                raise ScenePresentationError(
                    f"ScenePatch references unknown object {update.object_id!r}"
                ) from exception
            merged = dict(item.properties)
            merged.update(update.properties)
            prepared.append((item, item.properties, _presentation_state(merged)))

        applied = []
        try:
            for item, old_state, new_state in prepared:
                applied.append((item, old_state, new_state))
                self._apply_object_state(item, old_state, new_state)
            if prepared:
                self.context.UpdateCurrentViewer()
        except Exception as exception:
            try:
                for item, old_state, new_state in reversed(applied):
                    self._apply_object_state(item, new_state, old_state)
                if applied:
                    self.context.UpdateCurrentViewer()
            except Exception as rollback_exception:
                raise ScenePresentationError(
                    "ScenePatch commit and rollback both failed"
                ) from rollback_exception
            raise ScenePresentationError(
                "Failed to commit ScenePatch"
            ) from exception

        replacements = {
            item.object_id: replace(
                item,
                visible=new_state["visible"],
                properties=new_state,
            )
            for item, old_state, new_state in prepared
        }
        self._objects = tuple(
            replacements.get(item.object_id, item)
            for item in self._objects
        )
        self._objects_by_id.update(replacements)
        self.last_patch_sequence = patch.sequence
        self._update_widget_shape(self._objects)
        return patch.sequence

    def _update_widget_shape(self, prepared):
        if not hasattr(self.widget, "_first_shape"):
            return
        first = next(
            (
                item.shape
                for item in prepared
                if item.visible and item.shape is not None
            ),
            None,
        )
        try:
            from OCP.Bnd import Bnd_Box
            from zencad.geom.shape import Shape

            self.widget._first_shape = Shape(first) if first is not None else None
            bounds = Bnd_Box()
            for item in prepared:
                if item.visible:
                    item_bounds = Bnd_Box()
                    try:
                        item.ais_object.BoundingBox(item_bounds)
                    except TypeError:
                        item_bounds = item.ais_object.BoundingBox()
                    bounds.Add(item_bounds)
            if bounds.IsVoid():
                self.widget.scene_max0 = 1.0
                return
            xmin, ymin, zmin, xmax, ymax, zmax = bounds.Get()
            self.widget.scene_max0 = max(
                xmax - xmin,
                ymax - ymin,
                zmax - zmin,
                1.0,
            )
        except Exception:
            # Presentation is already committed. Export/navigation metadata is
            # auxiliary and must not turn a successful viewer swap into a
            # reported transactional failure.
            self.widget._first_shape = None
            self.widget.scene_max0 = 1.0

"""GUI-thread materialization and transactional live scene presentation."""

from dataclasses import dataclass, field, replace
import math
from numbers import Real
from types import MappingProxyType
from typing import Callable, Mapping

from OCP.AIS import AIS_Shape
from OCP.Aspect import Aspect_TOD_ABSOLUTE
from OCP.gp import gp_Quaternion, gp_Trsf, gp_Vec

from zencad.color import Color
from zencad.runtime.scene_protocol import (
    SceneObjectRecord,
    SceneSnapshot,
    decode_brep,
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
    if record.kind != "brep":
        raise ScenePresentationError(
            f"Unsupported scene object kind: {record.kind!r}"
        )

    state = _presentation_state(record.properties)
    color = state["color"]
    border = state["border_color"]
    wire = state["wire_color"]
    transformation = _transform(state)

    shape = decode_brep(record.payload)
    ais_object = AIS_Shape(shape)
    drawer = ais_object.Attributes()
    drawer.SetFaceBoundaryDraw(True)
    drawer.SetTypeOfDeflection(Aspect_TOD_ABSOLUTE)
    drawer.SetMaximalChordialDeviation(
        Settings.get(["view", "default_chordial_deviation"])
    )

    face_color = Color(color).to_Quantity_Color()
    ais_object.SetColor(face_color)
    ais_object.SetTransparency(color[3])
    line_aspect = drawer.LineAspect()
    if line_aspect is not None:
        line_aspect.SetColor(Color(border).to_Quantity_Color())
        drawer.SetFaceBoundaryAspect(line_aspect)
    wire_aspect = drawer.WireAspect()
    if wire_aspect is not None:
        wire_aspect.SetColor(Color(wire).to_Quantity_Color())
        drawer.SetWireAspect(wire_aspect)
    ais_object.SetLocalTransformation(transformation)
    return PresentedSceneObject(
        object_id=record.object_id,
        ais_object=ais_object,
        shape=shape,
        visible=state["visible"],
        properties=state,
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
            if "border_color" in changed:
                line_aspect = drawer.LineAspect()
                if line_aspect is not None:
                    line_aspect.SetColor(
                        Color(new_state["border_color"]).to_Quantity_Color()
                    )
                    drawer.SetFaceBoundaryAspect(line_aspect)
            if "wire_color" in changed:
                wire_aspect = drawer.WireAspect()
                if wire_aspect is not None:
                    wire_aspect.SetColor(
                        Color(new_state["wire_color"]).to_Quantity_Color()
                    )
                    drawer.SetWireAspect(wire_aspect)
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
        first = next((item.shape for item in prepared if item.visible), None)
        if first is None:
            self.widget._first_shape = None
            self.widget.scene_max0 = 1.0
            return
        try:
            from OCP.Bnd import Bnd_Box
            from zencad.geom.shape import Shape

            self.widget._first_shape = Shape(first)
            bounds = Bnd_Box()
            for item in prepared:
                if item.visible:
                    bounds.Add(item.ais_object.BoundingBox())
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

"""GUI-thread materialization and atomic replacement of scene snapshots."""

from dataclasses import dataclass
from numbers import Real
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
from zencad.settings import Settings


class ScenePresentationError(RuntimeError):
    """A snapshot could not be safely presented."""


@dataclass(frozen=True)
class PresentedSceneObject:
    object_id: str
    ais_object: object
    shape: object
    visible: bool


def _rgba(value, name) -> tuple[float, float, float, float]:
    if not isinstance(value, (tuple, list)) or len(value) != 4:
        raise ScenePresentationError(f"{name} must be an RGBA sequence")
    if any(
        not isinstance(component, Real) or not 0 <= component <= 1
        for component in value
    ):
        raise ScenePresentationError(f"{name} components must be in [0, 1]")
    return tuple(float(component) for component in value)


def _vector(value, name, size) -> tuple[float, ...]:
    if not isinstance(value, (tuple, list)) or len(value) != size:
        raise ScenePresentationError(f"{name} must contain {size} numbers")
    if any(not isinstance(component, Real) for component in value):
        raise ScenePresentationError(f"{name} must contain only numbers")
    return tuple(float(component) for component in value)


def _transform(properties: Mapping) -> gp_Trsf:
    raw = properties.get("transform")
    transformation = gp_Trsf()
    if raw is None:
        return transformation
    if not isinstance(raw, Mapping):
        raise ScenePresentationError("transform must be an object")

    scale = raw.get("scale", 1.0)
    if not isinstance(scale, Real) or scale == 0:
        raise ScenePresentationError("transform scale must be non-zero")
    rotation = _vector(raw.get("rotation", (0, 0, 0, 1)), "rotation", 4)
    translation = _vector(raw.get("translation", (0, 0, 0)), "translation", 3)
    transformation.SetRotation(gp_Quaternion(*rotation))
    transformation.SetScaleFactor(float(scale))
    transformation.SetTranslationPart(gp_Vec(*translation))
    return transformation


def materialize_scene_object(record: SceneObjectRecord) -> PresentedSceneObject:
    """Create a fully styled AIS object without binding it to a context."""
    if record.kind != "brep":
        raise ScenePresentationError(
            f"Unsupported scene object kind: {record.kind!r}"
        )

    properties = record.properties
    visible = properties.get("visible", True)
    if not isinstance(visible, bool):
        raise ScenePresentationError("visible must be a boolean")
    color = _rgba(properties.get("color", (0.6, 0.6, 0.8, 0)), "color")
    border = _rgba(properties.get("border_color", (0, 0, 0, 0)), "border_color")
    wire = _rgba(properties.get("wire_color", (0, 0, 0, 0)), "wire_color")
    transformation = _transform(properties)

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
        visible=visible,
    )


class ScenePresenter:
    """Own scene AIS handles while preserving permanent viewer helpers."""

    def __init__(
        self,
        widget,
        materializer: (
            Callable[[SceneObjectRecord], PresentedSceneObject] | None
        ) = None,
    ):
        self.widget = widget
        self.context = widget.Context
        self.view = widget.View
        self._materializer = materializer or materialize_scene_object
        self._objects: tuple[PresentedSceneObject, ...] = ()
        self.committed_generation: int | None = None

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

    def apply(self, snapshot: SceneSnapshot):
        """Replace the current scene and return the committed generation."""
        self._assert_gui_thread()
        if not isinstance(snapshot, SceneSnapshot):
            raise TypeError("ScenePresenter requires a SceneSnapshot")

        try:
            camera_action, explicit_camera = self._camera_action(snapshot)
            prepared = tuple(
                self._materializer(record) for record in snapshot.objects
            )
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
        self.committed_generation = snapshot.generation
        self._update_widget_shape(prepared)
        return snapshot.generation

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

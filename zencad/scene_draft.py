"""Data-only scene construction for isolated script runners."""

from collections import OrderedDict
from dataclasses import dataclass
import math
import sys
import time
from typing import Callable

import evalcache
from OCP.TopoDS import TopoDS_Shape

from zencad.color import (
    Color,
    default_border_color,
    default_color,
    default_point_color,
    default_wire_color,
)
from zencad.geom.exttrans import nulltrans
from zencad.geom.shape import Shape
from zencad.geom.mesh import MeshData, normalize_mesh_display_mode
from zencad.geom.trans import Transformation
from zencad.geom.transformable import Transformable
from zencad._typed.meshes import MeshData as TypedMeshData
from zencad._typed.topology import Shape as TypedShape
from zencad._typed.values import Point3 as TypedPoint3
from zencad.runtime.scene_protocol import (
    SceneObjectRecord,
    SceneSnapshot,
    encode_brep,
    encode_mesh,
    encode_json_payload,
)
from zencad.runtime.scene_patch_protocol import SceneObjectPatch, ScenePatch
from zencad.runtime.input_protocol import InputState


class SceneDraftError(ValueError):
    """The runner attempted an unsupported scene operation."""


class SceneAnimationCancelled(BaseException):
    """The owning generation was cancelled during managed animation."""


class ManagedAnimationState:
    """Qt-free counterpart of the callback state used by legacy animation."""

    def __init__(self):
        now = time.time()
        self.widget = None
        self.start_time = now
        self.time = now
        self.last_time = now
        self.delta = 0.0
        self.loctime = 0.0
        self.scene = None
        self.input = InputState()

    def timestamp(self, timestamp):
        self.time = timestamp
        self.loctime = timestamp - self.start_time
        self.delta = timestamp - self.last_time
        self.last_time = timestamp


def _color(value, fallback) -> Color:
    if value is None:
        return fallback()
    if isinstance(value, Color):
        return value
    if isinstance(value, (tuple, list)):
        return Color(*value)
    raise SceneDraftError(f"Unsupported color value: {value!r}")


def _color_tuple(value: Color) -> tuple[float, float, float, float]:
    return value.r, value.g, value.b, value.a


def _transformation_state(value: Transformation) -> dict:
    state = value.__getstate__()
    return {
        "scale": state["scale"],
        "rotation": tuple(state["rotate"]),
        "translation": tuple(state["transl"]),
    }


@dataclass
class _DraftObject:
    object_id: str
    kind: str
    source: object
    location: Transformation
    visible: bool
    color: Color
    border_color: Color
    wire_color: Color
    display_mode: str | None = None


class SceneObjectRef(Transformable):
    """Logical handle whose mutations update a runner-side scene draft."""

    def __init__(self, draft: "SceneDraft", object_id: str):
        self._draft = draft
        self.object_id = object_id

    def _object(self) -> _DraftObject:
        return self._draft._get(self.object_id)

    def relocate(self, transformation):
        if not isinstance(transformation, Transformation):
            raise SceneDraftError("Scene relocation requires a Transformation")
        obj = self._object()
        obj.location = transformation
        self._draft._mark_dirty(
            self.object_id,
            "transform",
            _transformation_state(transformation),
        )
        return self

    def location(self):
        return self._object().location

    def transform(self, transformation):
        return self.relocate(transformation * self.location())

    def set_color(
        self,
        color,
        b=None,
        c=None,
        d=0,
        border_color=None,
        wire_color=None,
    ):
        if b is not None and c is not None:
            color = Color(color, b, c, d)
        obj = self._object()
        obj.color = _color(color, default_color)
        self._draft._mark_dirty(
            self.object_id,
            "color",
            _color_tuple(obj.color),
        )
        if border_color is not None:
            obj.border_color = _color(border_color, default_border_color)
            self._draft._mark_dirty(
                self.object_id,
                "border_color",
                _color_tuple(obj.border_color),
            )
        if wire_color is not None:
            obj.wire_color = _color(wire_color, default_wire_color)
            self._draft._mark_dirty(
                self.object_id,
                "wire_color",
                _color_tuple(obj.wire_color),
            )
        return self

    def color(self):
        return self._object().color

    def set_mesh_display_mode(self, display_mode):
        obj = self._object()
        if obj.kind != "mesh":
            raise SceneDraftError(
                "mesh display mode can only be changed for a mesh object"
            )
        obj.display_mode = normalize_mesh_display_mode(display_mode)
        self._draft._mark_dirty(
            self.object_id,
            "display_mode",
            obj.display_mode,
        )
        return self

    def hide(self, enabled=True):
        obj = self._object()
        obj.visible = not enabled
        self._draft._mark_dirty(self.object_id, "visible", obj.visible)
        return self

    def is_hidden(self):
        return not self._object().visible


class SceneDraft:
    """Mutable data-only draft that freezes into a complete snapshot."""

    def __init__(
        self,
        generation: int,
        publisher: Callable[[SceneSnapshot], None] | None = None,
        camera_policy: str = "preserve",
        patch_publisher: Callable[[ScenePatch], bool | None] | None = None,
        ready_publisher: Callable[[int, bool], bool | None] | None = None,
        cancel_event=None,
        input_drain: Callable[[], tuple] | None = None,
    ):
        if not isinstance(generation, int) or isinstance(generation, bool):
            raise SceneDraftError("Scene generation must be an integer")
        if generation < 0:
            raise SceneDraftError("Scene generation must be non-negative")
        self.generation = generation
        self.publisher = publisher
        self.camera_policy = camera_policy
        self.patch_publisher = patch_publisher
        self.ready_publisher = ready_publisher
        self.cancel_event = cancel_event
        self.input_drain = input_drain
        self._objects: OrderedDict[str, _DraftObject] = OrderedDict()
        self._next_id = 0
        self._published = False
        self._ready = False
        self._scene_revision = 0
        self._patch_sequence = 0
        self._dirty: OrderedDict[str, dict] = OrderedDict()

    def _get(self, object_id: str) -> _DraftObject:
        try:
            return self._objects[object_id]
        except KeyError as exception:
            raise SceneDraftError(
                f"Scene object {object_id!r} does not belong to this draft"
            ) from exception

    def _mark_dirty(self, object_id, property_name, value):
        if not self._published:
            return
        properties = self._dirty.setdefault(object_id, {})
        properties[property_name] = value

    def add(self, obj, color=None, display_mode=None):
        if self._published:
            raise SceneDraftError(
                "Managed scenes cannot add objects after initial publication"
            )
        obj = evalcache.unlazy_if_need(obj)
        from zencad.interactive.assemble import unit
        from zencad.interactive.line import LineInteractiveObject
        from zencad.interactive.point import PointInteractiveObject
        from zencad.geombase import point3

        if isinstance(obj, unit):
            if display_mode is not None:
                raise SceneDraftError(
                    "display_mode is only supported for mesh objects"
                )
            return self._add_assembly(obj)
        if isinstance(obj, (Shape, TopoDS_Shape, TypedShape)):
            if display_mode is not None:
                raise SceneDraftError(
                    "display_mode is only supported for mesh objects"
                )
            kind = "brep"
            source = obj
            object_color = _color(color, default_color)
            location = nulltrans()
            visible = True
            border_color = default_border_color()
            wire_color = default_wire_color()
        elif isinstance(obj, (MeshData, TypedMeshData)):
            kind = "mesh"
            source = obj
            display_mode = normalize_mesh_display_mode(display_mode)
            object_color = _color(color, default_color)
            location = nulltrans()
            visible = True
            border_color = default_border_color()
            wire_color = default_wire_color()
        elif isinstance(obj, (point3, TypedPoint3)):
            if display_mode is not None:
                raise SceneDraftError(
                    "display_mode is only supported for mesh objects"
                )
            kind = "point"
            source = obj
            object_color = _color(color, default_point_color)
            location = nulltrans()
            visible = True
            border_color = default_border_color()
            wire_color = default_wire_color()
        elif isinstance(obj, PointInteractiveObject):
            if display_mode is not None:
                raise SceneDraftError(
                    "display_mode is only supported for mesh objects"
                )
            point = obj.point.Pnt()
            kind = "point"
            source = (point.X(), point.Y(), point.Z())
            object_color = _color(color, lambda: obj.color())
            location = obj.location()
            visible = not obj._hide
            border_color = obj._border_color
            wire_color = obj._wire_color
        elif isinstance(obj, LineInteractiveObject):
            if display_mode is not None:
                raise SceneDraftError(
                    "display_mode is only supported for mesh objects"
                )
            kind = "line"
            source = {
                "start": tuple(float(component) for component in obj.p1),
                "end": tuple(float(component) for component in obj.p2),
                "width": float(obj.width),
                "arrow_length": (
                    None if obj.arrow_length is None
                    else float(obj.arrow_length)
                ),
            }
            object_color = _color(color, lambda: obj.color())
            location = obj.location()
            visible = not obj._hide
            border_color = obj._border_color
            wire_color = obj._wire_color
        else:
            raise SceneDraftError(
                f"Managed scenes do not support {type(obj).__name__} yet"
            )

        object_id = f"object-{self._next_id:06d}"
        self._next_id += 1
        self._objects[object_id] = _DraftObject(
            object_id=object_id,
            kind=kind,
            source=source,
            location=location,
            visible=visible,
            color=object_color,
            border_color=border_color,
            wire_color=wire_color,
            display_mode=display_mode,
        )
        return SceneObjectRef(self, object_id)

    def _add_assembly(self, root):
        """Flatten a legacy assembly into stable logical scene references."""
        from zencad.interactive.line import LineInteractiveObject
        from zencad.interactive.shape import ShapeInteractiveObject

        root.location_update(deep=True, view=False)

        def bind(current):
            current.views.clear()
            for display_object in current.dispobjects:
                if not isinstance(
                    display_object,
                    (ShapeInteractiveObject, LineInteractiveObject),
                ):
                    raise SceneDraftError(
                        "Managed assemblies support shape and line parts; "
                        f"got {type(display_object).__name__}"
                    )
                source = (
                    display_object.shape
                    if isinstance(display_object, ShapeInteractiveObject)
                    else display_object
                )
                reference = self.add(source, color=display_object.color())
                reference.set_color(
                    display_object.color(),
                    border_color=display_object._border_color,
                    wire_color=display_object._wire_color,
                )
                reference.hide(display_object._hide)
                reference.relocate(current.global_location)
                current.views.add(reference)
            for child in current.childs:
                bind(child)

        bind(root)
        return root

    def snapshot(self, metadata=None) -> SceneSnapshot:
        records = []
        for obj in self._objects.values():
            if obj.kind == "brep":
                payload = encode_brep(
                    obj.source.native()
                    if isinstance(obj.source, TypedShape)
                    else obj.source
                )
            elif obj.kind == "mesh":
                payload = (
                    obj.source.display_payload()
                    if isinstance(obj.source, TypedMeshData)
                    else encode_mesh(obj.source)
                )
            else:
                payload = encode_json_payload(
                    obj.source.value()
                    if isinstance(obj.source, TypedPoint3)
                    else obj.source
                )
            properties = {
                "visible": obj.visible,
                "color": _color_tuple(obj.color),
                "border_color": _color_tuple(obj.border_color),
                "wire_color": _color_tuple(obj.wire_color),
                "transform": _transformation_state(obj.location),
            }
            if obj.kind == "mesh":
                properties["display_mode"] = obj.display_mode
            records.append(SceneObjectRecord(
                object_id=obj.object_id,
                kind=obj.kind,
                payload=payload,
                properties=properties,
            ))
        return SceneSnapshot(
            generation=self.generation,
            objects=tuple(records),
            camera_policy=self.camera_policy,
            metadata=metadata or {},
        )

    def publish(self) -> SceneSnapshot:
        if self._published:
            raise SceneDraftError("Managed scene was already published")
        snapshot = self.snapshot()
        if self.publisher is not None:
            self.publisher(snapshot)
        self._published = True
        self._dirty.clear()
        return snapshot

    def ready(self, animated=False):
        if not self._published:
            raise SceneDraftError("Managed scene must be published before ready")
        if self._ready:
            raise SceneDraftError("Managed scene is already ready")
        if not isinstance(animated, bool):
            raise SceneDraftError("animated must be a boolean")
        self._ready = True
        if self.ready_publisher is not None:
            accepted = self.ready_publisher(self._scene_revision, animated)
            if accepted is False:
                raise SceneAnimationCancelled()

    def drain_patch(self) -> ScenePatch | None:
        if not self._dirty:
            return None
        self._patch_sequence += 1
        patch = ScenePatch(
            generation=self.generation,
            scene_revision=self._scene_revision,
            sequence=self._patch_sequence,
            updates=tuple(
                SceneObjectPatch(object_id, properties)
                for object_id, properties in self._dirty.items()
            ),
        )
        self._dirty.clear()
        return patch

    def _cancelled(self):
        if self.cancel_event is None:
            return False
        trace = sys.gettrace()
        if trace is not None:
            sys.settrace(None)
        try:
            return self.cancel_event.is_set()
        finally:
            if trace is not None:
                sys.settrace(trace)

    def _wait(self, timeout):
        if self.cancel_event is None:
            time.sleep(timeout)
            return False
        # The worker's cancellation trace reads this same multiprocessing
        # Event. Do not let tracing recursively re-enter Event.wait() while
        # its condition lock is held.
        trace = sys.gettrace()
        if trace is not None:
            sys.settrace(None)
        try:
            return self.cancel_event.wait(timeout)
        finally:
            if trace is not None:
                sys.settrace(trace)

    def run_animation(self, callback, animate_step=0.01, close_handle=None):
        if not self._ready or not self._published:
            raise SceneDraftError("Managed scene must be ready before animation")
        if not callable(callback):
            raise SceneDraftError("Animation callback must be callable")
        if close_handle is not None and not callable(close_handle):
            raise SceneDraftError("close_handle must be callable")
        if (
            not isinstance(animate_step, (int, float))
            or isinstance(animate_step, bool)
            or not math.isfinite(animate_step)
            or animate_step <= 0
        ):
            raise SceneDraftError("animate_step must be a positive finite number")

        state = ManagedAnimationState()
        deadline = time.monotonic()
        try:
            while True:
                if self._cancelled():
                    raise SceneAnimationCancelled()
                delay = deadline - time.monotonic()
                if delay > 0 and self._wait(delay):
                    raise SceneAnimationCancelled()

                state.timestamp(time.time())
                state.input.begin_frame(
                    self.input_drain() if self.input_drain is not None else ()
                )
                callback(state)
                patch = self.drain_patch()
                if patch is not None and self.patch_publisher is not None:
                    accepted = self.patch_publisher(patch)
                    if accepted is False:
                        raise SceneAnimationCancelled()
                deadline = max(deadline + animate_step, time.monotonic())
        finally:
            if close_handle is not None:
                close_handle()

    def __len__(self):
        return len(self._objects)

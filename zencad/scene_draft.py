"""Data-only scene construction for isolated script runners."""

from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable

import evalcache
from OCP.TopoDS import TopoDS_Shape

from zencad.color import (
    Color,
    default_border_color,
    default_color,
    default_wire_color,
)
from zencad.geom.exttrans import nulltrans
from zencad.geom.shape import Shape
from zencad.geom.trans import Transformation
from zencad.geom.transformable import Transformable
from zencad.runtime.scene_protocol import (
    SceneObjectRecord,
    SceneSnapshot,
    encode_brep,
)


class SceneDraftError(ValueError):
    """The runner attempted an unsupported scene operation."""


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
    shape: Shape | TopoDS_Shape
    location: Transformation
    visible: bool
    color: Color
    border_color: Color
    wire_color: Color


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
        self._object().location = transformation
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
        if border_color is not None:
            obj.border_color = _color(border_color, default_border_color)
        if wire_color is not None:
            obj.wire_color = _color(wire_color, default_wire_color)
        return self

    def color(self):
        return self._object().color

    def hide(self, enabled=True):
        self._object().visible = not enabled
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
    ):
        if not isinstance(generation, int) or isinstance(generation, bool):
            raise SceneDraftError("Scene generation must be an integer")
        if generation < 0:
            raise SceneDraftError("Scene generation must be non-negative")
        self.generation = generation
        self.publisher = publisher
        self.camera_policy = camera_policy
        self._objects: OrderedDict[str, _DraftObject] = OrderedDict()
        self._next_id = 0

    def _get(self, object_id: str) -> _DraftObject:
        try:
            return self._objects[object_id]
        except KeyError as exception:
            raise SceneDraftError(
                f"Scene object {object_id!r} does not belong to this draft"
            ) from exception

    def add(self, obj, color=None):
        obj = evalcache.unlazy_if_need(obj)
        if not isinstance(obj, (Shape, TopoDS_Shape)):
            raise SceneDraftError(
                f"Managed scenes do not support {type(obj).__name__} yet"
            )

        object_id = f"object-{self._next_id:06d}"
        self._next_id += 1
        self._objects[object_id] = _DraftObject(
            object_id=object_id,
            shape=obj,
            location=nulltrans(),
            visible=True,
            color=_color(color, default_color),
            border_color=default_border_color(),
            wire_color=default_wire_color(),
        )
        return SceneObjectRef(self, object_id)

    def snapshot(self, metadata=None) -> SceneSnapshot:
        records = []
        for obj in self._objects.values():
            records.append(SceneObjectRecord(
                object_id=obj.object_id,
                kind="brep",
                payload=encode_brep(obj.shape),
                properties={
                    "visible": obj.visible,
                    "color": _color_tuple(obj.color),
                    "border_color": _color_tuple(obj.border_color),
                    "wire_color": _color_tuple(obj.wire_color),
                    "transform": _transformation_state(obj.location),
                },
            ))
        return SceneSnapshot(
            generation=self.generation,
            objects=tuple(records),
            camera_policy=self.camera_policy,
            metadata=metadata or {},
        )

    def publish(self) -> SceneSnapshot:
        snapshot = self.snapshot()
        if self.publisher is not None:
            self.publisher(snapshot)
        return snapshot

    def __len__(self):
        return len(self._objects)

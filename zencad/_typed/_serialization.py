"""Non-executable serializers for resolved typed-domain values."""

from __future__ import annotations

from evalcache.v2 import Artifact, SerializedValue

from zencad.geom.shape import Shape as ResolvedShape
from zencad.runtime.scene_protocol import decode_brep, encode_brep

from ._curve_operations import Curve2Value, CurveValue
from ._surface_operations import SurfaceValue


_SHAPE_PAYLOAD = b"zencad.typed.shape\x00v1"
_CURVE_PAYLOAD = b"zencad.typed.curve\x00v2"
_CURVE2_PAYLOAD = b"zencad.typed.curve2\x00v2"
_SURFACE_PAYLOAD = b"zencad.typed.surface\x00v1"


class ShapeBrepSerializer:
    """Store a shape as a named BREP artifact, never as a pickled OCP value."""

    serializer_id = "zencad.shape.brep-artifact.v1"

    def dumps(self, value: ResolvedShape) -> SerializedValue:
        if not isinstance(value, ResolvedShape):
            raise TypeError("shape serializer requires a resolved ZenCad Shape")
        return SerializedValue(
            payload=_SHAPE_PAYLOAD,
            artifacts=(
                Artifact(
                    name="shape.brep",
                    data=encode_brep(value),
                    media_type="model/vnd.opencascade.brep",
                ),
            ),
        )

    def loads(self, value: SerializedValue) -> ResolvedShape:
        if value.payload != _SHAPE_PAYLOAD:
            raise ValueError("unsupported typed Shape cache payload")
        if len(value.artifacts) != 1:
            raise ValueError("typed Shape cache record must have one artifact")
        artifact = value.artifacts[0]
        if artifact.name != "shape.brep":
            raise ValueError("typed Shape cache record has no shape.brep artifact")
        return ResolvedShape(decode_brep(artifact.data))


class CurveSerializer:
    """Store a 3D curve using OCCT's full-precision set format."""

    serializer_id = "zencad.curve.occt-set-artifact.v2"

    def dumps(self, value: CurveValue) -> SerializedValue:
        if not isinstance(value, CurveValue):
            raise TypeError("curve serializer requires CurveValue")
        return SerializedValue(
            payload=_CURVE_PAYLOAD,
            artifacts=(
                Artifact(
                    name="curve.geom",
                    data=value.data,
                    media_type="model/vnd.opencascade.geom-curve",
                ),
            ),
        )

    def loads(self, value: SerializedValue) -> CurveValue:
        if value.payload != _CURVE_PAYLOAD:
            raise ValueError("unsupported typed Curve cache payload")
        if len(value.artifacts) != 1:
            raise ValueError("typed Curve cache record must have one artifact")
        artifact = value.artifacts[0]
        if artifact.name != "curve.geom":
            raise ValueError("typed Curve cache record has no curve.geom artifact")
        return CurveValue(artifact.data)


class Curve2Serializer:
    """Store a 2D curve using OCCT's full-precision set format."""

    serializer_id = "zencad.curve2.occt-set-artifact.v2"

    def dumps(self, value: Curve2Value) -> SerializedValue:
        if not isinstance(value, Curve2Value):
            raise TypeError("curve2 serializer requires Curve2Value")
        return SerializedValue(
            payload=_CURVE2_PAYLOAD,
            artifacts=(
                Artifact(
                    name="curve2.geom",
                    data=value.data,
                    media_type="model/vnd.opencascade.geom2d-curve",
                ),
            ),
        )

    def loads(self, value: SerializedValue) -> Curve2Value:
        if value.payload != _CURVE2_PAYLOAD:
            raise ValueError("unsupported typed Curve2 cache payload")
        if len(value.artifacts) != 1:
            raise ValueError("typed Curve2 cache record must have one artifact")
        artifact = value.artifacts[0]
        if artifact.name != "curve2.geom":
            raise ValueError("typed Curve2 cache record has no curve2.geom artifact")
        return Curve2Value(artifact.data)


class SurfaceSerializer:
    """Store a surface using OCCT's full-precision set format."""

    serializer_id = "zencad.surface.occt-set-artifact.v1"

    def dumps(self, value: SurfaceValue) -> SerializedValue:
        if not isinstance(value, SurfaceValue):
            raise TypeError("surface serializer requires SurfaceValue")
        return SerializedValue(
            payload=_SURFACE_PAYLOAD,
            artifacts=(
                Artifact(
                    name="surface.geom",
                    data=value.data,
                    media_type="model/vnd.opencascade.geom-surface",
                ),
            ),
        )

    def loads(self, value: SerializedValue) -> SurfaceValue:
        if value.payload != _SURFACE_PAYLOAD:
            raise ValueError("unsupported typed Surface cache payload")
        if len(value.artifacts) != 1:
            raise ValueError("typed Surface cache record must have one artifact")
        artifact = value.artifacts[0]
        if artifact.name != "surface.geom":
            raise ValueError("typed Surface cache record has no surface.geom artifact")
        return SurfaceValue(artifact.data)

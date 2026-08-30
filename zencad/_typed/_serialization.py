"""Non-executable serializers for resolved typed-domain values."""

from __future__ import annotations

from evalcache.v2 import Artifact, SerializedValue

from zencad.geom.shape import Shape as ResolvedShape
from zencad.runtime.scene_protocol import decode_brep, encode_brep


_SHAPE_PAYLOAD = b"zencad.typed.shape\x00v1"


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

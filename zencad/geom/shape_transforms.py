"""Topology-preserving transform operations declared at module level."""

from __future__ import annotations

from collections.abc import Mapping

from evalcache import ResultSpec

from zencad._native.shape import Shape as ResolvedShape
from zencad.operation import operation

from . import _transform_operations as ops
from .topology import SHAPE_SPEC, Shape
from .transforms import AffineTransform, Transform
from .values import Vector3


def _shape_result_type(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> type[Shape]:
    del kwargs
    if args and isinstance(args[0], Shape):
        return type(args[0])
    return Shape


def _shape_result_spec(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> ResultSpec[ResolvedShape]:
    del kwargs
    if args and isinstance(args[0], Shape):
        return args[0]._result_spec
    return SHAPE_SPEC


@operation(
    result=SHAPE_SPEC,
    returns=_shape_result_type,
    select_result=_shape_result_spec,
    operation_id="zencad.typed.shape.transform",
    operation_version="1",
)
def _shape_transform(
    shape: Shape,
    transformation: Transform,
    /,
) -> Shape:
    if not isinstance(shape, Shape) or not isinstance(transformation, Transform):
        raise TypeError("shape transform expects Shape and Transform")
    return type(shape)(ops.transform_shape(shape._legacy(), transformation._resolved()))


@operation(
    result=SHAPE_SPEC,
    returns=_shape_result_type,
    select_result=_shape_result_spec,
    operation_id="zencad.typed.shape.affine_transform",
    operation_version="1",
)
def _shape_affine_transform(
    shape: Shape,
    transformation: AffineTransform,
    /,
) -> Shape:
    if not isinstance(shape, Shape) or not isinstance(transformation, AffineTransform):
        raise TypeError("shape affine transform expects Shape and AffineTransform")
    return type(shape)(
        ops.affine_transform_shape(shape._legacy(), transformation._resolved())
    )


@operation(
    result=SHAPE_SPEC,
    returns=_shape_result_type,
    select_result=_shape_result_spec,
    operation_id="zencad.typed.shape.translate",
    operation_version="1",
)
def _shape_translate(shape: Shape, vector: Vector3, /) -> Shape:
    if not isinstance(shape, Shape) or not isinstance(vector, Vector3):
        raise TypeError("shape translation expects Shape and Vector3")
    return type(shape)(ops.translate_shape(shape._legacy(), vector._resolved()))


__all__ = []

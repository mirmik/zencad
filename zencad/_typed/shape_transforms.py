"""Topology-preserving transform operations declared at module level."""

from __future__ import annotations

from collections.abc import Mapping

from evalcache import ResultSpec

from zencad.geom.shape import Shape as ResolvedShape
from zencad.operation import OperationArguments, arguments, operation

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
    backend=ops.transform_shape,
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
) -> OperationArguments:
    if not isinstance(shape, Shape) or not isinstance(transformation, Transform):
        raise TypeError("shape transform expects Shape and Transform")
    return arguments(shape, transformation)


@operation(
    backend=ops.affine_transform_shape,
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
) -> OperationArguments:
    if not isinstance(shape, Shape) or not isinstance(transformation, AffineTransform):
        raise TypeError("shape affine transform expects Shape and AffineTransform")
    return arguments(shape, transformation)


@operation(
    backend=ops.translate_shape,
    result=SHAPE_SPEC,
    returns=_shape_result_type,
    select_result=_shape_result_spec,
    operation_id="zencad.typed.shape.translate",
    operation_version="1",
)
def _shape_translate(shape: Shape, vector: Vector3, /) -> OperationArguments:
    if not isinstance(shape, Shape) or not isinstance(vector, Vector3):
        raise TypeError("shape translation expects Shape and Vector3")
    return arguments(shape, vector)


__all__ = []
